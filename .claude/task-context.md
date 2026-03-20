# Task Context Tracker

**Last Updated**: 2026-03-20
**Current Task**: Snapshot pipeline fix — PR #20 (branch `fix/snapshot-pipeline`), live-tested, pending merge + TTE.exe rebuild
**Active Branch**: `fix/snapshot-pipeline`
**Latest Commit (TTE)**: PR #20 open — Fix: Snapshot pipeline (backfill, dialog cleanup, multi-batch, throughput)
**Latest Commit (Stock Buddy)**: Snapshot fallback text updated (commit `2253bcb`)

---

## Task Progress Summary

| # | Task | Status |
|---|------|--------|
| 1 | Get alerts to trigger for Indian stocks | **done** (PR #11) |
| 2 | Check signal detection for US stocks and Indian stocks | **done** (PR #12) |
| 3 | Figure out why only 262 alerts got created instead of 314 | **deferred** (resolves on next `--fresh` run) |
| 4 | Make new API polling architecture (exit checker) | **done** — Pine Script stateless (PR #13), Stock Buddy cron (PR #64) |
| 5 | Test signals, setups, exits for the user | **pending** (user-side, needs market hours) |
| 6 | Verify Indian stock alerts trigger after exchange prefix fix | **pending** (user-side, needs NSE hours) |
| 7 | Post-deployment: verify signal timing & timestamps | **pending** (user-side, needs `--fresh` + market hours) |
| 8 | Fix snapshot Trade Drawer not rendering on chart | **done** (PR #14) |
| 9 | Remove delisted EOSUSDT/EOSBTC from MongoDB | **done** (PR #15) |
| 10 | Fix bugs, remove dead code, sync docs | **done** (PR #16) |
| 11 | Remove webdriver-manager dependency | **done** (PR #17) |
| 12 | Bypass SeleniumManager network calls with explicit chromedriver path | **done** (PR #19) |
| 13 | Fix snapshot pipeline — backfill, dialog cleanup, throughput | **in progress** (PR #20, live-tested, needs merge + TTE.exe rebuild) |

---

## Session History

### Session: 2026-03-20 (Snapshot Pipeline Fix — PR #20)

**Mission**: From orchestrator (`.claude/current-mission.md`) — 400+ setup messages on Stock Buddy have no chart snapshots. Fix before symbol list grows 620 → 677.

**Root causes identified**:
1. **Category A (invisible setups)**: Old setups lack `snapshotStatus` field. Worker only queries `"pending"` or `"failed"`. TTE never called SB's backfill endpoint.
2. **Category B (cascading failures)**: Failed snapshot leaves dialog open → subsequent snapshots in same batch fail → exhausts 3 retries quickly.
3. **Low throughput**: batch_size=5, single-round, snapshots skipped during maintenance ticks.

**Fixes implemented** (committed `c8b2a81`):
1. **Backfill endpoint call**: Added `trigger_backfill()` to `StockBuddyClient`. Called at startup + hourly via `last_backfill` timer.
2. **Targeted dialog cleanup**: Added `_dismiss_dialogs()` — checks for `indicator-properties-dialog` and `series-properties-dialog`, clicks cancel. Called before each snapshot + after failures.
3. **Multi-batch loop**: `process_pending_snapshots()` now processes up to 2 rounds per cycle (20 snapshots max).
4. **Removed `not maintenance_due` guard**: Snapshots now run after maintenance with 3s stabilization wait. Reset `_bars_right_last_set` after refresh.
5. **Sleep reductions**: ~2s saved per snapshot (legend 0.3→0.1s, auto-fit 0.3→0.1s, Alt+R 1.0→0.7s, chart click 0.5→0.2s, clipboard retry 1.0→0.7s, dialog waits 0.5→0.3s).
6. **batch_size**: 5 → 10 in `combo_settings.yaml`.

**Additional fixes during live testing**:
- **Timeframe error in `--maintain-only`**: `create_browser()` passed `chart_timeframe="45 seconds"` for Snapshot layout, which failed. Fixed: use `"1 hour"` when `layout_override` is set.
- **Shutdown not responsive**: Snapshot batch loop had no shutdown check — Ctrl+C waited for entire batch (10 snapshots × 20-30s each). Fixed: passed `_shutdown_event` to `SnapshotWorker`, check between each snapshot.
- **Progressive slowness observed**: Each snapshot takes longer (23s → 58s over 8 snapshots). Cause: TradingView DOM accumulation with each symbol/timeframe change. Not fixable without periodic browser restarts.

**Live test results** (non-headless, `--maintain-only`):
- Backfill call: "Backfill: no setups needed queuing" (all already have snapshotStatus)
- 8/10 snapshots completed successfully before user Ctrl+C
- Maintenance cycle (alert restart + log clear) worked normally
- Snapshot URLs verified (e.g., `https://www.tradingview.com/x/hLEZGaUV/`)

**Status**: PR #20 open. Needs: commit shutdown fix → merge → flip `headless: true` → rebuild TTE.exe.

### Previous Sessions (Summary)
- **2026-03-07**: PRs #17, #19 — ChromeDriver fix (bypass SeleniumManager, explicit path)
- **2026-03-06**: PR #16 — Codebase audit, 2 bug fixes, 6 dead functions removed
- **2026-03-05**: PRs #14, #15 — Trade Drawer V2 simplification, EOS removal
- **2026-03-03**: PRs #12, #13 — Signal guards, stateless screener, exit checker spec
- **2026-02-26**: V2 implementation (Pine Script + Python), stale CSS fix
- **2026-02-20-23**: Snapshots feature (PR #6, #7), Trade Drawer, dual-timer
- **2026-02-10-13**: Codebase reorg (PR #4), Pine Script screener, maintenance loop

---

## Important Decisions Made

### Snapshot Pipeline Fix (2026-03-20)
1. **Targeted dialog cleanup over blind ESC**: Check for specific dialog selectors (`indicator-properties-dialog`, `series-properties-dialog`) and click cancel. Avoids accidentally closing alerts sidebar.
2. **Multi-batch with max_rounds=2**: Balances throughput vs maintenance starvation. 2 rounds of 10 = 20 snapshots/cycle max.
3. **Backfill at startup + hourly**: Fire-and-forget. Queues old setups that lack `snapshotStatus` field.
4. **Snapshot layout uses "1 hour" timeframe**: Not "45 seconds" (screener timeframe). Snapshot worker overrides per-setup anyway.

### Previous Decisions (Summary)
- **ChromeDriver (2026-03-07)**: Bypass SeleniumManager with explicit `~/.wdm` cache path. Graceful fallback.
- **Hashed selectors (2026-03-06)**: Leave `.text-yyMUOAN9` etc. as-is — risky to change without inspecting live HTML.
- **Exit checker (2026-03-03)**: Server-side cron (every 5 min), Pine Script stateless, DB-level dedup.
- **V2 architecture (2026-02-26)**: 45s chart, compact JSON keys, category-aware pairing.

---

## Key Reference Files

| File | Purpose |
|------|---------|
| `tte/main.py` | Entry point (orchestrator, maintenance loop, backfill timer) |
| `tte/snapshot_worker.py` | Snapshot worker (multi-batch, dialog cleanup, backfill client) |
| `tte/config.py` | Config dataclass |
| `tte/browser/tradingview.py` | Browser automation (Selenium) |
| `tte/browser/chart.py` | Chart navigation (symbol, timeframe, indicators) |
| `combo_settings.yaml` | Settings (batch_size=10, poll_interval=60, 150s maintenance) |
| `.claude/current-mission.md` | Orchestrator mission: snapshot pipeline fix |
| `Pine Script Code/TTE Screener V2.txt` | V2 screener (stateless setup detection) |
| `Pine Script Code/Trade Drawer V2.txt` | NWE bands + trade level drawings for snapshots |

---

## Verified Patterns

### Snapshot Worker Selectors
```
Dialog cleanup:     div[data-name="indicator-properties-dialog"], div[data-name="series-properties-dialog"]
Cancel button:      button[name="cancel"]
Legend toggler:     button[data-qa-id="legend-toggler"] (aria-label="Show/Hide indicators legend")
Chart area:         div.chart-markup-table
```

### Working TradingView Selectors
```
Alert items:       div[data-name="alert-item-name"]
Alert settings:    div[data-name="alerts-settings-button"]
Dropdown menu:     div[data-qa-id="menu-inner"] > div
Legend items:      div[data-qa-id="legend-source-item"]
Indicator inputs:  input[data-qa-id="ui-lib-Input-input"]
Settings dialog:   div[data-name="indicator-properties-dialog"]
Chart settings:    div[data-name="series-properties-dialog"]
Right margin:      input[data-name="paneRightMargin"]
```

**WARNING**: Never use TradingView's dynamically generated class names. Always prefer `data-name` and `data-qa-id` selectors.

### MongoDB — 620 Symbols (growing to 677 soon)
Categories: `Currencies` (29), `Crypto` (18), `US Stocks` (376), `Indian Stocks` (197)

---

## Test Commands

```bash
# TTE
pipenv run python combo_main.py --maintain-only    # Run maintenance + snapshots (headless)
pipenv run python combo_main.py --validate         # Validate config
pipenv run python combo_main.py --fresh            # Delete alerts & recreate
dist/TTE.exe                                       # GUI (requires pystray)

# Verification
pipenv run pyright tte/                            # Type checking (0 errors expected)
pipenv run ruff check tte/                         # Linting
```
