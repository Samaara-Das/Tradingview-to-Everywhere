"""Pick 10 newest setup_messages with snapshots, spread across symbol categories
and across the last few days. Print direction/side so we can judge whether the
snapshot layout (TP above vs below entry) matches the reversed strategy.
"""

from __future__ import annotations

import json
import os

from pymongo import MongoClient


def main() -> None:
    c = MongoClient(os.environ["MONGODB_URI"])
    coll = c.tte.setup_messages

    # Inspect schema first
    sample = coll.find_one({"snapshotUrl": {"$exists": True, "$ne": None}})
    print("=== SAMPLE DOC KEYS ===")
    print(sorted(sample.keys()))
    print("=== SAMPLE DOC ===")
    print(json.dumps({k: str(v) for k, v in sample.items()}, indent=2, default=str)[:2000])
    print()

    # Pull recent across distinct symbols (newest snapshot per symbol)
    pipeline = [
        {"$match": {"snapshotUrl": {"$exists": True, "$ne": None}}},
        {"$sort": {"_id": -1}},
        {"$group": {"_id": "$symbol", "doc": {"$first": "$$ROOT"}}},
        {"$replaceRoot": {"newRoot": "$doc"}},
        {"$sort": {"_id": -1}},
        {"$limit": 30},
    ]
    print("=== 30 newest setups (one per symbol) ===")
    for d in coll.aggregate(pipeline):
        ts = d.get("createdAt")
        print(
            f"  ts={ts}  sym={d.get('symbol'):14}  "
            f"cat={d.get('category', '?'):10}  "
            f"dir={d.get('direction') or d.get('side') or d.get('tradeType') or '?':6}  "
            f"entry={d.get('entryPrice') or d.get('entry') or '?'}  "
            f"tp={d.get('tp') or d.get('takeProfit') or '?'}  "
            f"sl={d.get('sl') or d.get('stopLoss') or '?'}  "
            f"snap={d.get('snapshotUrl')}"
        )


if __name__ == "__main__":
    main()
