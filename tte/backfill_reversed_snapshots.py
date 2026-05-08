"""
Backfill REVERSED-STRATEGY snapshots.

NOTE: distinct from `docs/prds/backfill-snapshots.md`, which describes a
ONE-SHOT Stock Buddy endpoint that flips `snapshotStatus`-missing setups
to `pending` so the existing TTE worker renders them for the first time.
THIS module is the reversed-strategy RE-RENDER backfill (Goal 2): every
already-snapshotted setup gets a fresh chart drawn with TP/SL swapped.

Re-renders every setup in Stock Buddy's `setup_messages` collection so the
visual TP/SL match the reversed strategy. Designed to run as a long-running
job alongside (not on) tte-1's `--maintain-only` instance — point it at a
SEPARATE TradingView profile/Chrome user-data dir.

Idempotency
-----------
Manager rule (Q2, 2026-05-08, refined): each doc is stamped with
`reversedSnapshot: true` after a successful re-render. Subsequent passes
skip docs that already carry the marker. The earlier `_rev2` URL-suffix
idea was unreachable in practice — TradingView's Alt+S generates an
immutable S3 filename (`s3.tradingview.com/snapshots/{prefix}/{id}.png`)
that we cannot suffix. Originals are preserved instead by copying the
existing `snapshotUrl`/`snapshotTvUrl` into `originalSnapshotUrl` /
`originalSnapshotTvUrl` BEFORE overwrite (atomic with the marker).

Checkpointing
-------------
Progress (last processed _id, counts, failures) persisted to
`backfill_snapshots_progress.json` after each doc. Crash-resume reads this
file and continues from `last_id`.

Progress reporting
------------------
Every 30 minutes (`PROGRESS_LOG_INTERVAL`) appends one line to
`.claude/team-bus-C.md` as `[BACKFILL] processed N / M`.
End-of-run failed-id list dumped to `.claude/backfill-failed.json`.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

PROGRESS_FILE = Path("backfill_snapshots_progress.json")
TEAM_BUS_FILE = Path(".claude/team-bus-C.md")
PROGRESS_LOG_INTERVAL = 30 * 60  # seconds


@dataclass
class BackfillProgress:
    last_id: str | None = None
    processed: int = 0
    skipped: int = 0
    failed: int = 0
    failed_ids: list[str] = field(default_factory=list)
    total: int | None = None
    started_at: float | None = None
    last_progress_log_at: float = 0.0

    @classmethod
    def load(cls) -> BackfillProgress:
        if PROGRESS_FILE.exists():
            data = json.loads(PROGRESS_FILE.read_text())
            return cls(**data)
        return cls(started_at=time.time())

    def save(self) -> None:
        PROGRESS_FILE.write_text(json.dumps(self.__dict__, indent=2))

    def maybe_log(self) -> None:
        now = time.time()
        if now - self.last_progress_log_at < PROGRESS_LOG_INTERVAL:
            return
        line = (
            f"- {time.strftime('%Y-%m-%d %H:%M IST')} "
            f"[BACKFILL] processed {self.processed} / {self.total or '?'} "
            f"(skipped={self.skipped}, failed={self.failed})\n"
        )
        with TEAM_BUS_FILE.open("a", encoding="utf-8") as f:
            f.write(line)
        self.last_progress_log_at = now
        self.save()


REVERSED_MARKER_FIELD = "reversedSnapshot"
ORIGINAL_PNG_FIELD = "originalSnapshotUrl"
ORIGINAL_TV_FIELD = "originalSnapshotTvUrl"
FAILED_LIST_FILE = Path(".claude/backfill-failed.json")
PAGE_SIZE = 100


def already_reversed(doc: dict) -> bool:
    """Idempotency check via the `reversedSnapshot: true` marker.

    The earlier `_rev2` URL-suffix fallback was unreachable (TradingView
    controls S3 filenames; we cannot suffix the snapshot URL). Manager
    Q2 spec was clarified 2026-05-08: marker field is the sole signal.
    """
    return doc.get(REVERSED_MARKER_FIELD) is True


def _get_setup_messages_collection():
    """Return the `setup_messages` collection on the shared Atlas cluster.

    Uses the same `MONGODB_URI` env var the rest of TTE reads, plus
    `STOCK_BUDDY_DATABASE` (defaults to `stock_buddy_app`) for the DB name.
    Manager directive 2026-05-08 12:31 IST: backfill goes direct-Mongo —
    both repos share Atlas.
    """
    import os

    from pymongo import MongoClient

    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError(
            "MONGODB_URI not set. Direct-Mongo backfill requires the shared "
            "Atlas connection string."
        )
    db_name = os.getenv("STOCK_BUDDY_DATABASE", "stock_buddy_app")
    client = MongoClient(uri)
    client.admin.command("ping")  # fail fast on misconfig
    return client[db_name]["setup_messages"]


def iter_setup_messages(after_id: str | None) -> Iterator[dict]:
    """Yield every doc in `setup_messages`, oldest-first, via _id cursor.

    Cursor pagination keyed on `_id` so a crash mid-run can resume from
    `progress.last_id`. PAGE_SIZE limits memory + Atlas round-trip latency.
    """
    from bson import ObjectId

    coll = _get_setup_messages_collection()
    last_id = ObjectId(after_id) if after_id else None
    while True:
        query = {"_id": {"$gt": last_id}} if last_id else {}
        page = list(coll.find(query).sort("_id", 1).limit(PAGE_SIZE))
        if not page:
            return
        for doc in page:
            yield doc
            last_id = doc["_id"]


def _mark_reversed(
    doc_id, original_png_url: str | None = None, original_tv_url: str | None = None
) -> None:
    """Stamp the doc with the idempotency marker after a successful re-render.

    Atomically also preserves the original `snapshotUrl` / `snapshotTvUrl` into
    `originalSnapshotUrl` / `originalSnapshotTvUrl` so a future rollback can
    restore the original-strategy image without a re-render. We `$set` the
    originals only when they are non-empty AND not already preserved (the
    `$exists: false` guard makes this safe to call repeatedly).
    """
    set_fields: dict = {REVERSED_MARKER_FIELD: True}
    update: dict = {"$set": set_fields}
    coll = _get_setup_messages_collection()

    if original_png_url and not coll.count_documents(
        {"_id": doc_id, ORIGINAL_PNG_FIELD: {"$exists": True}}, limit=1
    ):
        set_fields[ORIGINAL_PNG_FIELD] = original_png_url
    if original_tv_url and not coll.count_documents(
        {"_id": doc_id, ORIGINAL_TV_FIELD: {"$exists": True}}, limit=1
    ):
        set_fields[ORIGINAL_TV_FIELD] = original_tv_url

    coll.update_one({"_id": doc_id}, update)


def _dump_failed_list(failed_ids: list[str]) -> None:
    """Persist the list of setupMessageIds that failed re-render so an operator
    can target them for retry. Written at end-of-run only (small file)."""
    if not failed_ids:
        return
    FAILED_LIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    FAILED_LIST_FILE.write_text(json.dumps({"failed_ids": failed_ids}, indent=2))
    logger.info("Wrote %d failed ids to %s", len(failed_ids), FAILED_LIST_FILE)


def run(worker) -> None:
    """Drive the existing `SnapshotWorker._take_snapshot()` over every historical setup.

    Must be invoked with a `worker` whose browser is a SEPARATE TV profile from
    tte-1's `--maintain-only` instance (manager Q3 rule, 2026-05-08).
    `config.reversed_strategy_snapshots` should be True (default) so each
    re-rendered snapshot uses the swapped TP/SL coordinates.

    `worker._take_snapshot(setup)` already POSTs the new TV URL back to
    Stock Buddy via `update_snapshot`; we only add the `reversedSnapshot`
    marker to the doc for our own idempotency.
    """
    progress = BackfillProgress.load()
    logger.info(f"Backfill resuming from last_id={progress.last_id!r}")

    if progress.total is None:
        coll = _get_setup_messages_collection()
        progress.total = coll.count_documents({REVERSED_MARKER_FIELD: {"$ne": True}})
        progress.save()
    logger.info(f"Backfill total pending: {progress.total}")

    for doc in iter_setup_messages(progress.last_id):
        doc_id = doc["_id"]
        if already_reversed(doc):
            progress.skipped += 1
            progress.last_id = str(doc_id)
            progress.save()
            continue
        original_png = doc.get("snapshotUrl")
        original_tv = doc.get("snapshotTvUrl")
        try:
            ok = worker._take_snapshot(doc)
            if ok:
                _mark_reversed(doc_id, original_png, original_tv)
                progress.processed += 1
            else:
                progress.failed += 1
                progress.failed_ids.append(str(doc.get("setupMessageId")))
        except Exception:
            logger.exception("Backfill error on %s", doc.get("setupMessageId"))
            progress.failed += 1
            progress.failed_ids.append(str(doc.get("setupMessageId")))
        progress.last_id = str(doc_id)
        progress.save()
        progress.maybe_log()

    _dump_failed_list(progress.failed_ids)
    progress.save()
    logger.info(
        "Backfill done: processed=%d skipped=%d failed=%d",
        progress.processed,
        progress.skipped,
        progress.failed,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(
        "Backfill entrypoint requires a configured `worker` — wire from a "
        "separate-profile launcher."
    )
