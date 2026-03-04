"""
Validate all symbols in MongoDB against price APIs (Binance / Yahoo Finance).

Reports which symbols have market data available and which don't.
Optionally removes invalid symbols from the database.

Usage:
    pipenv run python scripts/validate_symbols.py            # dry-run report
    pipenv run python scripts/validate_symbols.py --remove   # remove invalid from DB
"""

import argparse
import os
import sys
import time
from collections import defaultdict

import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart"

YAHOO_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

YAHOO_DELAY = 0.5  # seconds between Yahoo requests (conservative)

# Commodities that Yahoo lists as futures, not forex
COMMODITY_YAHOO_MAP = {
    "XAUUSD": "GC=F",  # Gold
    "XAGUSD": "SI=F",  # Silver
}


def normalize_symbol(symbol: str) -> str:
    """Clean up symbol data issues (e.g. exchange prefix left in symbol field)."""
    # Strip exchange prefix if present (e.g. "NSE:HAL" → "HAL")
    if ":" in symbol:
        symbol = symbol.split(":", 1)[1]
    return symbol


def connect_db():
    uri = os.getenv("MONGODB_URI")
    if not uri:
        print("ERROR: MONGODB_URI not set in .env")
        sys.exit(1)
    client = MongoClient(uri)
    client.admin.command("ping")
    db_name = os.getenv("MONGODB_DATABASE", "tte")
    return client[db_name]


def fetch_symbols(db):
    docs = list(db.symbols.find({}, {"symbol": 1, "full_symbol": 1, "category": 1}))
    print(f"Fetched {len(docs)} symbols from MongoDB\n")
    return docs


def check_binance(symbol: str) -> bool:
    try:
        resp = requests.get(
            BINANCE_KLINES_URL,
            params={"symbol": symbol, "interval": "5m", "limit": 1},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return isinstance(data, list) and len(data) > 0
        return False
    except requests.RequestException:
        return False


def check_yahoo(symbol: str) -> bool:
    try:
        resp = requests.get(
            f"{YAHOO_CHART_URL}/{symbol}",
            params={"interval": "1d", "range": "5d"},
            headers=YAHOO_HEADERS,
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            result = data.get("chart", {}).get("result")
            return result is not None and len(result) > 0
        return False
    except requests.RequestException:
        return False


def yahoo_symbol(symbol: str, category: str) -> str:
    # Commodities mapped to futures tickers
    if symbol in COMMODITY_YAHOO_MAP:
        return COMMODITY_YAHOO_MAP[symbol]
    if category == "Indian Stocks":
        # Underscores → hyphens (BAJAJ_AUTO → BAJAJ-AUTO.NS)
        return f"{symbol.replace('_', '-')}.NS"
    if category == "Currencies":
        return f"{symbol}=X"
    # US Stocks: dots/slashes → hyphens (BRK.A → BRK-A, C/PR → C-PR)
    if category == "US Stocks":
        return symbol.replace(".", "-").replace("/", "-")
    return symbol


def validate_all(symbols: list[dict]) -> dict[str, dict]:
    by_category: dict[str, list[dict]] = defaultdict(list)
    for doc in symbols:
        cat = doc.get("category", "Unknown")
        by_category[cat].append(doc)

    results: dict[str, dict] = {}

    for category in sorted(by_category.keys()):
        cat_symbols = by_category[category]
        valid = []
        invalid = []

        print(f"Checking {category} ({len(cat_symbols)} symbols)...")

        for i, doc in enumerate(cat_symbols):
            raw_sym = doc.get("symbol", "")
            sym = normalize_symbol(raw_sym)

            if category == "Crypto":
                ok = check_binance(sym)
            else:
                api_sym = yahoo_symbol(sym, category)
                ok = check_yahoo(api_sym)
                time.sleep(YAHOO_DELAY)

            if ok:
                valid.append(raw_sym)
            else:
                invalid.append(raw_sym)

            # Progress indicator every 50 symbols
            checked = i + 1
            if checked % 50 == 0 or checked == len(cat_symbols):
                print(f"  ... {checked}/{len(cat_symbols)}")

        results[category] = {
            "valid": valid,
            "invalid": invalid,
            "total": len(cat_symbols),
        }

    return results


def print_report(results: dict[str, dict]):
    print("\n" + "=" * 50)
    print("  Symbol Validation Report")
    print("=" * 50 + "\n")

    total_checked = 0
    total_valid = 0
    total_invalid = 0

    for category in sorted(results.keys()):
        r = results[category]
        n_valid = len(r["valid"])
        n_invalid = len(r["invalid"])
        total_checked += r["total"]
        total_valid += n_valid
        total_invalid += n_invalid

        print(f"{category} ({r['total']} symbols)")
        print(f"  Valid: {n_valid}  |  Invalid: {n_invalid}")
        if r["invalid"]:
            print(f"  Invalid: {', '.join(sorted(r['invalid']))}")
        print()

    print("-" * 50)
    print(f"TOTAL: {total_checked} checked, {total_valid} valid, {total_invalid} invalid")
    print()


def remove_invalid(db, results: dict[str, dict]):
    all_invalid = []
    for r in results.values():
        all_invalid.extend(r["invalid"])

    if not all_invalid:
        print("No invalid symbols to remove.")
        return

    print(f"Removing {len(all_invalid)} invalid symbols from MongoDB...")
    result = db.symbols.delete_many({"symbol": {"$in": all_invalid}})
    print(f"Deleted {result.deleted_count} documents.")


def main():
    parser = argparse.ArgumentParser(description="Validate symbols against price APIs")
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove invalid symbols from MongoDB",
    )
    args = parser.parse_args()

    db = connect_db()
    symbols = fetch_symbols(db)
    results = validate_all(symbols)
    print_report(results)

    if args.remove:
        remove_invalid(db, results)
    elif any(r["invalid"] for r in results.values()):
        print("Run with --remove to delete invalid symbols from MongoDB.")


if __name__ == "__main__":
    main()
