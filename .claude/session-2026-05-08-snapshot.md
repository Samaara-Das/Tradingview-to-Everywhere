# Session 2026-05-08 — TTE Goal 2 (reversed-snapshot backfill) deploy + halt

## Outcome
Deployed `tte-backfill` sibling container on KVM8 with new TV Ultimate account `Kingsdxb2025@gmail.com`. Got the backfill running end-to-end (146 docs marked `reversedSnapshot:true`, 0 failures). Sammy then spotted the rendered visuals were unusable — Trade Drawer V2 lines anchor to historical entry timestamps so the lines render off-screen for setups older than the chart's default visible window. Container halted; resuming Monday after a design discussion.

## PRs shipped
- **#36** (squash `3d05e78`) — `fix(backfill)`: DB default `stock_buddy_app` → `tte`, `REVERSED_STRATEGY_SNAPSHOTS` launcher default `true` → `false` (Pine handles reversal).
- **#37** (squash `74dc8e0`) — `feat(backfill)`: pre-flight `count_documents`, atomic `originalSnapshotUrl` preservation, end-of-run `.claude/backfill-failed.json` dump, dropped dead `_rev2` URL-suffix fallback, launcher cred routing (`*_BACKFILL` → `TRADINGVIEW_EMAIL/PASSWORD`).
- **#38** (squash `ff00eaf`) — `fix(backfill)`: synthesize `setupMessageId` from `_id` for direct-Mongo docs (caught by local dry-run; production would have failed on doc 1).

## On-host patches NOT yet upstreamed (apply before Monday resume)
1. `scripts/run_reversed_backfill.py:31` — `sys.path.insert(0, repo_root)` so `from tte import ...` works when launched as `python scripts/...`.
2. Same launcher — `browser.sign_in() → open_page("/chart") → change_layout(snapshot_layout_name)` injected after `Browser(...)` ctor (ctor doesn't auto-login).
3. `tte/snapshot_worker.py:_take_snapshot` — timeframe-change call disabled. The chevron selector `#header-toolbar-intervals > button[aria-label="Chart interval"]` times out (~18s) on the new account's UI variant. Root cause not investigated; resume task.
4. Same file: `sleep(4)` after settings-apply tightened to `sleep(2)` for backfill speed.
5. `tte/backfill_reversed_snapshots.maybe_log()` — bus-file write wrapped in `try/except + mkdir(parents=True)` so missing in-container `/app/.claude` dir doesn't crash the run.

## Speedups achieved (38.5s → 17.5s/doc, 55% faster)
- Skip the doomed timeframe-change call: -~18s/doc.
- Tighten post-render `sleep(4)` → `sleep(2)`: -~2s/doc.

## Key bug discovered (HALT reason)
Trade Drawer V2 anchors `entryLine`, `slLine`, `tp1Line` to `dateTime = startTime` (the setup's entry epoch) and `endTime = startTime + 15 * dt`. For setups days/weeks old, these timestamps fall far to the LEFT of the chart's auto-fit visible region, so the drawn lines render off-screen. The live tte-1 path doesn't hit this because it snaps the setup as it fires (entry ≈ now). Backfill needs a `chart_scroll_to_date(setup.entryTime)` step before fill_inputs to anchor the visible bar window around the entry time.

## Other root causes to address Monday
- `combo_settings.yaml: snapshot.bars_to_right=60` is tuned for live entries. Historical entries need ~15-30 bars on EITHER side of the entry bar — possibly redesign Trade Drawer V2 to draw bidirectionally.
- Layout aesthetic mismatch: Sammy wants the look of `dassamaara@gmail.com`'s Snapshot layout, but we're rendering under `Kingsdxb2025@gmail.com`'s freshly-built Snapshot layout. Either export-and-import the layout, or pause tte-1 during backfill and run it under dassamaara directly.
- Disabled timeframe-change worsens bar alignment for old setups — the chart stays on whatever timeframe the layout opens in. Need a working chevron selector for this account's UI variant.

## Mongo state to clean before resume
- `db.setup_messages.countDocuments({reversedSnapshot: true})` = 146 (visually unusable).
- Reset path before resuming: `db.setup_messages.updateMany({reversedSnapshot: true}, [{$set: {snapshotUrl: "$originalSnapshotUrl", snapshotTvUrl: "$originalSnapshotTvUrl"}, $unset: ["reversedSnapshot", "originalSnapshotUrl", "originalSnapshotTvUrl"]}])`.
- 0 failures in `failed_ids` so no retry list to triage.

## Infra deployed (intact, ready for Monday)
- Container `tte-backfill` on KVM8 (`srv1591208.hstgr.cloud` / `168.231.103.163`) — currently `Stopped`.
- Compose service appended to `/opt/stockbuddy/docker-compose.yml` (under existing `stockbuddy` project).
- Secrets at `/opt/stockbuddy/secrets/.env.tte-backfill` (mode 600).
- Named volume `stockbuddy_tte-backfill-userdata` holds the logged-in BackfillProfile + saved Snapshot layout under `Kingsdxb2025@gmail.com`.
- SSH key on this Windows machine at `~/.ssh/kvm8-claude_ed25519` (port 2222, user `root`).
- 3rd TV Ultimate account is unused — Sammy can spare it for a parallel `tte-backfill-2` container later.
- Health-monitor cron `134de544` cancelled (was every 30 min via CronCreate).

## What's next (Monday)
1. Patch `_take_snapshot` to call `chart_scroll_to_date(setup.entryTime)` BEFORE filling Trade Drawer inputs.
2. Either export `dassamaara@gmail.com`'s Snapshot layout JSON and import on `Kingsdxb2025@gmail.com`, or stop tte-1 for the backfill window and run under `dassamaara`.
3. Reset the 146 bad docs (Mongo updateMany above).
4. Optionally: tweak `Trade Drawer V2.txt` Pine to draw lines bidirectionally `[startTime - N*dt, startTime + N*dt]` so off-by-anchor-time still produces a visible chart.
5. Resume `tte-backfill` container; restart 30-min health-monitor cron.
6. After 1-2 docs, manually verify the rendered image matches the dassamaara aesthetic and the lines are on-screen, before letting it run unattended for ~30h.

## Branch state
- HEAD = `06dd155` on local main (stale; behind `origin/main` at `74dc8e0` after the 3 squash-merges of #36, #37, #38).
- Nothing uncommitted that's worth saving in source control. The `dry_run_one.py` smoke script was deleted before commit. Patches on KVM8 are not in source control yet — Monday's first task is to upstream them.
