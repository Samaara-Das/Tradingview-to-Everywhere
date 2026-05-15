"""One-shot revert of the cancelled reversed-strategy snapshot backfill.

Reverts every doc in `tte.setup_messages` with `reversedSnapshot: true`:
- If `originalSnapshotUrl` / `originalSnapshotTvUrl` were preserved by the
  backfill, restore `snapshotUrl` / `snapshotTvUrl` from them.
- If no originals preserved, just clear the `reversedSnapshot` marker so the
  doc returns to Stock Buddy's snapshot pending queue.
- Unsets `reversedSnapshot`, `originalSnapshotUrl`, `originalSnapshotTvUrl`.

Run via:
    docker exec tte-1 python /tmp/revert_reversed_snapshots.py
"""

from __future__ import annotations

import os

from pymongo import MongoClient


def main() -> None:
    uri = os.environ["MONGODB_URI"]
    client = MongoClient(uri)
    coll = client.tte.setup_messages

    total = coll.count_documents({"reversedSnapshot": True})
    print(f"Pre-revert total reversedSnapshot:true = {total}")

    restored = 0
    for doc in coll.find(
        {"reversedSnapshot": True, "originalSnapshotUrl": {"$exists": True, "$ne": None}}
    ):
        set_fields = {"snapshotUrl": doc["originalSnapshotUrl"]}
        if doc.get("originalSnapshotTvUrl"):
            set_fields["snapshotTvUrl"] = doc["originalSnapshotTvUrl"]
        coll.update_one(
            {"_id": doc["_id"]},
            {
                "$set": set_fields,
                "$unset": {
                    "reversedSnapshot": "",
                    "originalSnapshotUrl": "",
                    "originalSnapshotTvUrl": "",
                },
            },
        )
        restored += 1
    print(f"Restored from originals: {restored}")

    cleared = coll.update_many(
        {"reversedSnapshot": True},
        {
            "$unset": {
                "reversedSnapshot": "",
                "originalSnapshotUrl": "",
                "originalSnapshotTvUrl": "",
            }
        },
    )
    print(f"Cleared marker only (no originals): {cleared.modified_count}")

    remaining_marker = coll.count_documents({"reversedSnapshot": True})
    remaining_orig_png = coll.count_documents({"originalSnapshotUrl": {"$exists": True}})
    remaining_orig_tv = coll.count_documents({"originalSnapshotTvUrl": {"$exists": True}})
    print(f"Remaining reversedSnapshot:true (expect 0): {remaining_marker}")
    print(f"Remaining originalSnapshotUrl (expect 0):   {remaining_orig_png}")
    print(f"Remaining originalSnapshotTvUrl (expect 0): {remaining_orig_tv}")


if __name__ == "__main__":
    main()
