# Current Mission: Snapshot Pipeline — Debug & Fix Missing Snapshots
Date: 2026-03-20
From: Orchestrator

## Context

There are 400+ setup messages on Stock Buddy without chart snapshots. The user wants to understand why and fix it. There may also be recurring errors in the snapshot worker.

**Important:** The symbol list is about to grow from 620 → 677 symbols (~339 alerts). A fresh TTE run with the updated list is coming soon. Fix the snapshot pipeline BEFORE that happens so the new setups don't pile onto the backlog.

**How the snapshot pipeline works:**
1. SB webhook inserts new setups with `snapshotStatus: "pending"`, `snapshotAttempts: 0`
2. TTE's snapshot worker (in the maintenance loop) polls `GET /api/tte/snapshots/pending?limit=5` every 60s
3. SB atomically marks returned docs as `"processing"` and returns setup metadata
4. TTE takes snapshot via Selenium (symbol → timeframe → Trade Drawer settings → Alt+S → clipboard → PNG/TV URLs)
5. TTE reports result via `POST /api/tte/snapshots/update` (success: snapshotUrl+snapshotTvUrl, failure: error string)
6. SB updates the doc: `"completed"` on success, `"failed"` + increment `snapshotAttempts` on failure
7. Failed setups with `snapshotAttempts < 3` get retried. At 3+ attempts → permanently stuck as `"failed"`
8. Stale `"processing"` docs (>10 min) are auto-recovered back to `"pending"`

**Key files:**
- `tte/snapshot_worker.py` — SnapshotWorker class, StockBuddyClient HTTP client
- `tte/main.py` — `run_maintenance()` integrates snapshot worker (line ~496)
- `tte/config.py` — snapshot config (batch_size=5, poll_interval=60s)
- `combo_settings.yaml` — YAML config

**SB-side snapshot code (READ-ONLY — don't modify, just understand):**
- `GET /api/tte/snapshots/pending` → calls `getPendingSnapshots(limit)` in `src/lib/tte/collections.ts:1099`
- `POST /api/tte/snapshots/update` → calls `updateSetupSnapshot()` in `src/lib/tte/collections.ts:1309`
- `POST /api/tte/snapshots/backfill` → calls `backfillPendingSnapshots(days=30)` in `src/lib/tte/collections.ts:1155`

## Tasks (in order):

### 1. Investigate recurring snapshot errors
- Read through `tte/snapshot_worker.py` carefully — understand each failure mode
- Check for fragile CSS selectors, timing issues, or silent failures
- Common failure points to check:
  - `change_symbol()` failing for certain symbol formats (e.g., `NSE:` prefix symbols, crypto pairs)
  - `force_change_tframe()` failing
  - Trade Drawer settings dialog not opening (double-click timing, stale elements)
  - Alt+S clipboard read failing (clipboard permission, race condition, retry exhaustion)
  - Legend show/hide failing
- Check if there's any logging that would show error patterns when TTE.exe is running
- Fix any bugs you find that could cause recurring failures

### 2. Investigate why 400+ setups have no snapshots
There are two likely categories of missing snapshots. Investigate both:

**Category A — Setups with NO `snapshotStatus` field at all:**
These are setups created BEFORE the snapshot feature was added, OR setups where `insertSetupMessage()` somehow didn't set the field. The worker's `getPendingSnapshots()` query only matches `snapshotStatus: "pending"` or `snapshotStatus: "failed"` — docs with no field are INVISIBLE.

SB has a backfill function (`backfillPendingSnapshots()`) and endpoint (`POST /api/tte/snapshots/backfill`) that marks old docs as `"pending"`. But it needs to be called. Check if TTE should call this at startup or periodically.

**Category B — Setups permanently stuck as `"failed"` (attempts >= 3):**
These exhausted their 3 retries and will never be picked up again. Need to understand WHY they failed 3 times (recurring error?) and potentially reset them.

**What to do:**
- Add a startup or periodic call from TTE to trigger the backfill endpoint, so old setups get queued automatically
- Consider increasing `SNAPSHOT_MAX_ATTEMPTS` handling — if an error is transient (e.g., chart didn't load), 3 attempts may not be enough
- Consider increasing `snapshot_batch_size` from 5 to something higher to chew through backlog faster — but test that the browser remains stable

### 3. Optimize throughput for clearing the backlog
With 400+ pending snapshots, at 5 per minute it would take over an hour. Consider:
- Increasing `snapshot_batch_size` (currently 5) — what's realistic before browser instability?
- Reducing unnecessary `sleep()` calls in the pipeline (each snapshot has ~6s of hardcoded waits)
- Reducing `snapshot_poll_interval` (currently 60s) — can poll faster while there's a backlog
- Any other throughput improvements you see

### 4. Verify no regressions
- Run Pyright type checking — ensure 0 errors
- Make sure maintenance loop (alert restart, log clear) is unaffected
- Review all changes for correctness

## Cross-Project Dependencies
- SB has the backfill endpoint ready (`POST /api/tte/snapshots/backfill`) — TTE just needs to call it
- SB has a separate mission to update UI fallback text. No coordination needed.
- Do NOT modify any Stock Buddy code. If you find SB-side issues, document them in the report.

## Report Results
Write completion report to: C:/Users/dassa/Work/TTE-SB-Orchestrator/agent-comms.md
Format: [Date] [Project: TTE] — what was investigated, root causes found, what was fixed, any SB-side issues to address.
