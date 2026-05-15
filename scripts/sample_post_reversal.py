"""Pick 10 snapshots that were RENDERED after the reversed Pine upload
(2026-05-08 12:00 UTC), across symbol categories. We then visually inspect
each PNG to confirm the Trade Drawer V2 indicator drew TP and SL swapped.
"""

from __future__ import annotations

import os
from collections import defaultdict

from pymongo import MongoClient


def main() -> None:
    c = MongoClient(os.environ["MONGODB_URI"])
    coll = c.tte.setup_messages

    # snapshotUpdatedAt is a string like "2026-05-08 13:47:49.382000"
    # use lexical comparison to filter
    cutoff = "2026-05-08 12:00:00"

    q = {
        "snapshotUrl": {"$exists": True, "$ne": None},
        "snapshotUpdatedAt": {"$gte": cutoff},
        "reversedSnapshot": {"$ne": True},  # don't pull the reverted backfill batch
    }
    total = coll.count_documents(q)
    print(f"Docs rendered AFTER {cutoff} (excluding reverted backfill): {total}")

    # Get newest 50 across symbols
    docs = list(
        coll.find(
            q,
            {
                "_id": 1,
                "symbol": 1,
                "direction": 1,
                "entryPrice": 1,
                "takeProfit": 1,
                "stopLoss": 1,
                "snapshotUrl": 1,
                "snapshotUpdatedAt": 1,
            },
        )
        .sort("snapshotUpdatedAt", -1)
        .limit(80)
    )

    # Balance: try to get a mix of Buy and Sell
    by_dir: dict[str, list] = defaultdict(list)
    for d in docs:
        by_dir[d.get("direction", "?")].append(d)

    picked: list = []
    # take up to 5 newest Buy + 5 newest Sell, fill from whichever has more if short
    for dir_label in ("Buy", "Sell"):
        for d in by_dir.get(dir_label, [])[:5]:
            picked.append(d)
    if len(picked) < 10:
        for d in docs:
            if d not in picked:
                picked.append(d)
            if len(picked) >= 10:
                break

    picked = picked[:10]
    print("\n=== 10 picks (post-reversal renders) ===")
    for d in picked:
        print(
            f"  ts={d.get('snapshotUpdatedAt')}  "
            f"sym={d.get('symbol'):14}  "
            f"dir={d.get('direction'):6}  "
            f"entry={d.get('entryPrice')}  "
            f"tp={d.get('takeProfit')}  "
            f"sl={d.get('stopLoss')}  "
            f"snap={d.get('snapshotUrl')}"
        )


if __name__ == "__main__":
    main()
