"""Verify that recent setup_messages snapshots use the reversed-strategy Pine.

The reversed Trade Drawer V2 Pine indicator was uploaded to TV on 2026-05-08.
All snapshots rendered AFTER that date should show TP and SL swapped relative
to the original-strategy snapshots.

This script only READS Mongo. It prints the 20 newest snapshotUrls so an
operator can open a few and visually confirm the reversal.
"""

from __future__ import annotations

import datetime as dt
import os

from pymongo import MongoClient


def main() -> None:
    client = MongoClient(os.environ["MONGODB_URI"])
    coll = client.tte.setup_messages

    print("=== Top 20 newest setups with snapshotUrl (by _id) ===")
    for d in coll.find({"snapshotUrl": {"$exists": True, "$ne": None}}).sort("_id", -1).limit(20):
        sym = d.get("symbol", "?")
        snap = d.get("snapshotUrl")
        created = d.get("createdAt") or d.get("entryTime") or "?"
        print(f"  {created} | {sym:14} | {snap}")

    print()
    print("=== Sample distinct createdAt buckets (last 5 days) ===")
    since = dt.datetime.utcnow() - dt.timedelta(days=5)
    pipeline = [
        {"$match": {"createdAt": {"$gte": since}, "snapshotUrl": {"$exists": True, "$ne": None}}},
        {"$sort": {"createdAt": -1}},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d %H:00", "date": "$createdAt"}},
                "count": {"$sum": 1},
                "sample": {"$first": "$$ROOT"},
            }
        },
        {"$sort": {"_id": -1}},
        {"$limit": 10},
    ]
    for row in coll.aggregate(pipeline):
        s = row["sample"]
        print(
            f"  {row['_id']}  count={row['count']:3}  sample {s.get('symbol'):12} {s.get('snapshotUrl')}"
        )

    print()
    print("=== Counts ===")
    total = coll.count_documents({})
    with_snap = coll.count_documents({"snapshotUrl": {"$exists": True, "$ne": None}})
    last_24h = coll.count_documents(
        {"createdAt": {"$gte": dt.datetime.utcnow() - dt.timedelta(hours=24)}}
    )
    pending = coll.count_documents({"snapshotUrl": {"$in": [None, ""]}})
    print(f"  total docs:                 {total}")
    print(f"  with snapshotUrl:           {with_snap}")
    print(f"  created in last 24h:        {last_24h}")
    print(f"  pending (no snapshotUrl):   {pending}")


if __name__ == "__main__":
    main()
