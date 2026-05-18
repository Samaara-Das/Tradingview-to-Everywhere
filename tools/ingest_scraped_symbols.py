"""
Ingest scraped TradingView screener rows into MongoDB `tte.symbols`.

Usage:
    pipenv run python tools/ingest_scraped_symbols.py path/to/scraped.json [--commit]

Input JSON shape (per row):
    {
      "symbol": "AAPL",
      "full_symbol": "NASDAQ:AAPL",
      "exchange": "NASDAQ",
      "category": "US Stocks",
      "companyName": "Apple Inc."
    }

Behavior:
- Reads input JSON + current `db.symbols` content.
- Per category: union of scraped + existing symbols, sorted alphabetically, then
  assign `assigned_instance` round-robin (`tte-1` to even indices, `tte-2` to
  odd). This is deterministic across runs — re-ingest is idempotent.
- Bulk upsert by `full_symbol`: `companyName` is always set (backfill on
  existing rows); `assigned_instance` is always set (re-balance is OK because
  alerts are only created/deleted at the next `--fresh`).
- Defaults to DRY-RUN; pass `--commit` to actually write.

The multi-tte-instance contracts spec (§2.1) lists `assigned_instance` as
TTE-owned bookkeeping; SB does not filter on it.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

load_dotenv()

INSTANCES = ("tte-1", "tte-2")


def load_scraped(path: Path) -> list[dict[str, Any]]:
    with path.open() as f:
        rows = json.load(f)
    if not isinstance(rows, list):
        raise SystemExit(f"Expected a JSON array in {path}, got {type(rows).__name__}")
    required = {"symbol", "full_symbol", "exchange", "category", "companyName"}
    for i, r in enumerate(rows):
        missing = required - set(r)
        if missing:
            raise SystemExit(f"Row {i} missing keys {missing}: {r}")
    return rows


def assign_instances(
    scraped: list[dict[str, Any]],
    existing: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Return {full_symbol: {assigned_instance, companyName?, ...}}.

    Combines scraped + existing per category, sorts by symbol, then
    round-robins `tte-1`/`tte-2`. companyName from scraped takes precedence;
    missing companyName falls back to existing doc's value (or stays absent).
    """
    by_category: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)

    for row in existing:
        cat = row["category"]
        fs = row.get("full_symbol") or row["symbol"]
        by_category[cat][fs] = {
            "symbol": row["symbol"],
            "full_symbol": fs,
            "category": cat,
            "exchange": row.get("exchange"),
            "companyName": row.get("companyName"),
        }

    for row in scraped:
        cat = row["category"]
        fs = row["full_symbol"]
        existing_row = by_category[cat].get(fs, {})
        by_category[cat][fs] = {
            "symbol": row["symbol"],
            "full_symbol": fs,
            "category": cat,
            "exchange": row["exchange"],
            # scraped companyName wins; fall back to existing if scraped is empty
            "companyName": row.get("companyName") or existing_row.get("companyName"),
        }

    out: dict[str, dict[str, Any]] = {}
    for _cat, rows_map in by_category.items():
        ordered = sorted(rows_map.values(), key=lambda r: r["symbol"])
        for i, r in enumerate(ordered):
            r["assigned_instance"] = INSTANCES[i % len(INSTANCES)]
            out[r["full_symbol"]] = r
    return out


def build_bulk_ops(merged: dict[str, dict[str, Any]]) -> list[UpdateOne]:
    ops = []
    for fs, doc in merged.items():
        update: dict[str, Any] = {
            "symbol": doc["symbol"],
            "full_symbol": fs,
            "category": doc["category"],
            "exchange": doc["exchange"],
            "assigned_instance": doc["assigned_instance"],
        }
        if doc.get("companyName"):
            update["companyName"] = doc["companyName"]
        ops.append(UpdateOne({"full_symbol": fs}, {"$set": update}, upsert=True))
    return ops


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ingest scraped TV screener rows into MongoDB.")
    p.add_argument("input", type=Path, help="Path to scraped JSON file")
    p.add_argument(
        "--commit", action="store_true", help="Actually write to MongoDB (default: dry-run)"
    )
    p.add_argument("--db", default=os.getenv("MONGODB_DATABASE", "tte"))
    args = p.parse_args(argv)

    if not args.input.exists():
        print(f"[ERROR] {args.input} not found", file=sys.stderr)
        return 2

    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        print("[ERROR] MONGODB_URI not set", file=sys.stderr)
        return 2

    scraped = load_scraped(args.input)
    print(f"[INFO] Loaded {len(scraped)} scraped rows from {args.input}")

    client = MongoClient(mongo_uri)
    coll = client[args.db].symbols
    existing = list(coll.find({}, {"_id": 0}))
    print(f"[INFO] Loaded {len(existing)} existing rows from {args.db}.symbols")

    merged = assign_instances(scraped, existing)
    print(f"[INFO] Merged universe: {len(merged)} symbols")

    # Reporting
    by_cat: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for doc in merged.values():
        by_cat[doc["category"]]["total"] += 1
        by_cat[doc["category"]][doc["assigned_instance"]] += 1
        if doc.get("companyName"):
            by_cat[doc["category"]]["with_companyName"] += 1

    print("\n[INFO] Per-category breakdown (merged):")
    for cat, stats in sorted(by_cat.items()):
        print(
            f"  {cat:<16} total={stats['total']:>5}  "
            f"tte-1={stats['tte-1']:>4}  tte-2={stats['tte-2']:>4}  "
            f"named={stats['with_companyName']:>5}"
        )

    ops = build_bulk_ops(merged)
    print(f"\n[INFO] Built {len(ops)} bulk-upsert ops")

    if not args.commit:
        print("[DRY-RUN] Pass --commit to write. No changes made.")
        return 0

    print("[COMMIT] Executing bulk write...")
    result = coll.bulk_write(ops, ordered=False)
    print(
        f"[COMMIT] matched={result.matched_count} modified={result.modified_count} "
        f"upserted={len(result.upserted_ids)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
