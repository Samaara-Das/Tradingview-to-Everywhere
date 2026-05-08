"""
Backfill reversed-strategy snapshots.

Re-renders every setup in Stock Buddy's `setup_messages` collection so the
visual TP/SL match the reversed strategy. Designed to run as a long-running
job alongside (not on) tte-1's `--maintain-only` instance — point it at a
SEPARATE TradingView profile/Chrome user-data dir.

Idempotency
-----------
Manager rule (Q2, 2026-05-08): write a NEW image asset with a versioned
suffix (`REV_SUFFIX` below); update the doc image-URL to the new asset.
Skip any doc whose image-URL already ends with `REV_SUFFIX`.

Checkpointing
-------------
Progress (last processed _id, counts, failures) persisted to
`backfill_snapshots_progress.json` after each doc. Crash-resume reads this
file and continues from `last_id`.

Progress reporting
------------------
Every 30 minutes (`PROGRESS_LOG_INTERVAL`) appends one line to
`.claude/team-bus-C.md` as `[BACKFILL] processed N / M`.

Status: SCAFFOLD — `SnapshotWorker._take_snapshot(setup)` and
`StockBuddyClient.update_snapshot()` are already the callables we need.
Remaining blocker is SB-side only: an enumeration endpoint
`GET /api/tte/snapshots/all?after_id=<id>&limit=<n>` so we can iterate
every doc in `setup_messages` with crash-resumable cursor pagination.
The `_rev2` suffix / originals-preservation strategy may resolve to a
metadata field on the doc rather than a literal URL suffix — awaiting
manager clarification (queued in team-bus-C 2026-05-08 12:28 IST).
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

REV_SUFFIX = "_rev2"
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


def already_reversed(image_url: str) -> bool:
    """Idempotency check — manager Q2 rule."""
    if not image_url:
        return False
    base = image_url.rsplit(".", 1)[0]
    return base.endswith(REV_SUFFIX)


def iter_setup_messages(client) -> Iterator[dict]:
    """Yield every doc in `setup_messages`, oldest-first, via cursor pagination.

    BLOCKER: needs SB endpoint `GET /api/tte/snapshots/all?after_id=<id>&limit=<n>`.
    Resumes from `progress.last_id` after a crash.
    """
    raise NotImplementedError("Pending Stock Buddy endpoint /snapshots/all")


def run(worker, client) -> None:
    """Drive the existing `SnapshotWorker._take_snapshot()` over every historical setup.

    Must be invoked with a `worker` whose browser is a SEPARATE TV profile from
    tte-1's `--maintain-only` instance (manager Q3 rule, 2026-05-08).
    `config.reversed_strategy_snapshots` should be True (default) so each
    re-rendered snapshot uses the swapped TP/SL coordinates.
    """
    progress = BackfillProgress.load()
    logger.info(f"Backfill resuming from last_id={progress.last_id!r}")

    for setup in iter_setup_messages(client):
        if already_reversed(setup.get("image", "") or setup.get("snapshotUrl", "")):
            progress.skipped += 1
            progress.last_id = setup.get("_id") or setup.get("setupMessageId")
            progress.save()
            continue
        try:
            ok = worker._take_snapshot(setup)  # writes new URL back via update_snapshot
            if ok:
                progress.processed += 1
            else:
                progress.failed += 1
                progress.failed_ids.append(str(setup.get("setupMessageId")))
        except Exception:
            logger.exception("Backfill error on %s", setup.get("setupMessageId"))
            progress.failed += 1
            progress.failed_ids.append(str(setup.get("setupMessageId")))
        progress.last_id = setup.get("_id") or setup.get("setupMessageId")
        progress.save()
        progress.maybe_log()

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
        "Backfill entrypoint requires (worker, client) — wire from a separate-profile launcher."
    )
