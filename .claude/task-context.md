# Task Context Tracker

**Last Updated**: 2026-03-03
**Current Task**: Task 4 (Exit checker architecture) — Phase 3 complete. Pine Script rewritten to stateless. Needs TradingView upload + alert recreation.
**Active Branch**: `feature/stateless-screener` (to be created)
**Latest Commit (TTE)**: `72237e1` — Fix save_layout: remove stale class selector and wrong log level
**Latest Commit (Stock Buddy)**: PR #64 deployed — exit checker cron + webhook handler update

---

## Task Progress Summary

| # | Task | Status |
|---|------|--------|
| 1 | Get alerts to trigger for Indian stocks | **done** (PR #11) |
| 2 | Check signal detection for US stocks and Indian stocks | **done** (PR #12 merged) |
| 3 | Figure out why only 262 alerts got created instead of 314 | **deferred** (will resolve after Task 4 finalizes symbol list) |
| 4 | Make new API polling architecture (exit checker) | **in-progress** — Phase 3 done (Pine Script stateless). Needs TV upload + `--fresh` alert recreation |
| 5 | Test signals, setups, exits for the user | pending (blocked by #4) |
| 6 | Verify Indian stock alerts trigger after exchange prefix fix | **pending** (test during next NSE hours) |
| 7 | Post-deployment: verify signal timing & timestamps (forex/crypto/stocks) | **pending** (blocked by deployment) |

### Exit Checker Implementation Status

| Phase | Scope | Owner | Status |
|-------|-------|-------|--------|
| Phase 1 | DB reset (wipe collections, verify indexes) | Stock Buddy | **Done** |
| Phase 2 | Webhook handler update + exit checker cron | Stock Buddy | **Done** (PR #64 deployed) |
| Phase 3 | Strip exit tracking from Pine Script V2 | TTE | **Done** (code complete, needs TV upload) |
| Phase 4 | End-to-end verification | Both | **Next** — upload to TV, recreate alerts, verify |

---

## Session History

### Session: 2026-03-03 (Exit Checker Spec, Symbol Validation, Agent Comms)

**Goal**: Finalize exit checker architecture spec, validate all symbols against price APIs, communicate tasks to Stock Buddy agent.

**Chronological flow**:

1. **Gathered context**: Read task-context.md, git log, task-master list. Corrected task 4 status (in-progress, not done — spec written but not implemented).

2. **Read exit-checker-architecture.md** (written in previous session): Full spec covering Pine Script stateless rewrite, webhook handler dedup changes, Vercel cron for TP/SL detection via Binance/Yahoo candles.

3. **Identified spec discrepancy**: Spec said to keep `stale01`/`stale02` staleness checks, but PR #11 already removed them. **Updated spec** to remove all staleness references.

4. **Symbol validation script** (`scripts/validate_symbols.py`):
   - Created script to check all 626 MongoDB symbols against Binance (crypto) and Yahoo Finance (stocks/forex)
   - First run: **614 valid, 12 invalid**
   - **Fixed 8 mapping issues**:
     - Indian stocks: `_` → `-` (`BAJAJ_AUTO` → `BAJAJ-AUTO.NS`)
     - US stocks: `.`/`/` → `-` (`BRK.A` → `BRK-A`, `C/PR` → `C-PR`)
     - Commodities: `XAUUSD` → `GC=F`, `XAGUSD` → `SI=F` (futures tickers, not forex `=X`)
     - Exchange prefix: `NSE:HAL` → `HAL` (strip prefix)
   - Second run: **622 valid, 4 invalid** (GVTD, KRT, M_M, M_MFIN — delisted Indian stocks)
   - **Removed 4 invalid symbols** from MongoDB with `--remove` flag
   - **622 symbols remain**, all validated

5. **Updated exit-checker-architecture.md** Section 5 (Symbol Mapping):
   - Added pre-processing step (strip exchange prefix)
   - Updated transform table with correct mappings for US/Indian stocks
   - Added commodities special case (XAUUSD/XAGUSD)
   - Added Yahoo 5m data limit note (~60 days, no pagination needed)
   - Added validation note referencing the script

6. **Removed auto-expire feature** from spec per user request:
   - Deleted Force-Expire Threshold subsection (30-day TTL)
   - Removed `"expired"` from outcome enum
   - Removed all force-expire references across sections 4, 5, 6, 7, 8, 9
   - Setups stay "running" until TP or SL is actually hit

7. **Wrote agent-comms.md** to Stock Buddy agent:
   - Cleared old content, explained new architecture
   - Listed all Stock Buddy tasks (Phase 1 DB reset + Phase 2 code changes)
   - Asked 5 specific questions about existing code

8. **Stock Buddy agent replied** with detailed answers:
   - `resolveSetupExit()` exists at `src/lib/tte/collections.ts:197-246` — takes PositionState, calls `updateSetupOutcome()`
   - `insertSetupMessage()` exists at `src/lib/tte/collections.ts:141-190` — already uses insert-and-catch with E11000
   - `yahoo-finance2` already installed (`^3.13.1`)
   - Current Zod schema shown — `n`, `xt`, `xp`, `xts` fields identified for removal
   - 6 files need updating (schemas.ts, collections.ts, route.ts, 3 test files)
   - **Design decisions by Stock Buddy**:
     - **Dedup**: Keep Option B (insert-and-catch) — already in place, atomic, race-free
     - **Cron function**: New `resolveSetupByCron(setupId, outcome, exitPrice, exitTimestamp)` — calls `updateSetupOutcome()` directly, adds `exitSource: "cron"`
     - **Position nulling**: New `nullifyLiveSignalPosition(symbol, direction, slotIndex)`
     - **Transition**: Option A — make `n`/`xt`/`xp`/`xts` optional during transition, then cleanup after TTE Phase 3

9. **TTE confirmed all Stock Buddy decisions**:
   - Option A transition (optional fields) — approved
   - Option B dedup (insert-and-catch) — approved
   - All new functions — approved
   - Clarified cron algorithm: walk candles chronologically, per-candle TP-first priority, stop at first hit
   - Gave green light to start building

**Key files created/modified this session**:
- `scripts/validate_symbols.py` — symbol validation script (new)
- `.claude/exit-checker-architecture.md` — spec updates (staleness, symbol mapping, auto-expire removal)
- `.claude/agent-comms.md` — rewritten for exit checker communication

**Status**: Waiting for Stock Buddy to build and deploy Phase 1+2. TTE Phase 3 starts after.

---

### Session: 2026-03-03 (Phase 3: Stateless Pine Script Rewrite)

**Goal**: Rewrite TTE Screener V2 Pine Script to remove all position tracking and exit detection (Phase 3 of exit checker architecture).

**Chronological flow**:

1. **Stock Buddy confirmed Phase 2 complete** via agent-comms.md — all tasks done, PR #64 deployed to production.
2. **Planned the rewrite**: Explored Pine Script file (943 lines), mapped all 104 `var` declarations, exit detection, position clearing, isNew reset, exitSent flags.
3. **Applied 9 edits bottom-up** (preserving line numbers):
   - Deleted exitSent flag setting (lines 917-933)
   - Replaced buildPosV2() calls with simple setup variable assignments (lines 893-901)
   - Rewrote `buildPosV2()` → `buildSetupV2()` (12 params → 7 params, no exit fields)
   - Deleted EXIT DETECTION section (lines 746-797)
   - Rewrote setup detection to stateless (lines 672-744) — removed `na(pos_entry)` guard, local string vars
   - Deleted isNew reset logic (lines 654-670)
   - Deleted position clearing logic (lines 616-652)
   - Deleted all 104 var declarations (lines 498-614)
   - Updated description comment
4. **Moved `buildSetupV2()` definition** above its first call (Pine Script requires top-down order)
5. **Verified**: Grep for `pos_s`, `isNew`, `exited`, `exitSent`, `exitType`, `exitPrice`, `exitTime`, `buildPosV2` — all zero results
6. **File reduced**: 943 → 695 lines
7. **Updated docs**: agent-comms.md (Phase 3 complete notice), ARCHITECTURE.md (stateless design), task-context.md

**Key files modified**:
- `Pine Script Code/TTE Screener V2.txt` — stateless rewrite (sole code change)
- `.claude/agent-comms.md` — Phase 3 complete notice to Stock Buddy
- `docs/combo/ARCHITECTURE.md` — updated V2 sections for stateless design
- `.claude/task-context.md` — this file

**Next steps**:
1. Upload modified Pine Script to TradingView Pine Editor
2. Verify it compiles and loads on chart without errors
3. Run `python combo_main.py --fresh` to recreate all alerts
4. Monitor Stock Buddy logs for correct payload format
5. Confirm to Stock Buddy agent → triggers cleanup pass

---

### Session: 2026-03-03 (PR Review, Merge, save_layout Fix, Smoke Test)

**Goal**: Review and merge signal detection guards PR, fix save_layout bug, smoke test `ensure_regular_hours()`.

1. **Opened & merged PR #12** (`fix/signal-detection-guards` → `main`, `7c5ebd9`):
   - `session.ismarket` guard in Pine Script V2
   - `ensure_regular_hours()` in `tte/browser/chart.py`
   - `agent-comms.md` doc fix (ots/zts are milliseconds, not seconds)

2. **Smoke test** confirmed `ensure_regular_hours()` works.

3. **Fixed save_layout() bug** (`72237e1`):
   - `logger.exception()` → `logger.info()` (was logging ERROR for success)
   - Removed stale class selector check, just click save directly

---

### Session: 2026-03-03 (Task 2: Debug Wrong Signal Detection)

**Goal**: Investigate wrong NWE/OB signals in Stock Buddy DB.

**Root causes found**:
- PPL off-hours anomaly (1/368 US stocks): Alert created when extended hours was ON
- "Wrong signals": Mostly user checking wrong dates + HTF candle semantics confusion
- **Fix**: `session.ismarket` guard + `ensure_regular_hours()` (PR #12)

---

### Session: 2026-03-03 (Fix Indian Stock Alerts)

**Goal**: Fix Indian stock alerts never firing. Task #1.

**Root causes**: `change_settings()` stripped exchange prefixes + redundant staleness check.
**Fix**: Keep full `EXCHANGE:SYMBOL` format, remove staleness detection. PR #11 merged (`e77888e`).

---

### Previous Sessions (Summary)
- **2026-02-27**: V2 debug testing + cleanup, maintenance TimeoutException fix, docs update + git cleanup
- **2026-02-26**: Stale CSS selectors fix, V2 webhook confirmed, graceful shutdown, delete_all_alerts race condition, LTF/HTF independent positions refactor, V2 testing/compilation fix, V2 implementation (Pine Script + Python + PR), V2 architecture planning + MongoDB
- **2026-02-23**: Snapshot quality + GUI defaults (PR #7)
- **2026-02-21**: Snapshot reliability
- **2026-02-20**: Chart snapshots feature (PR #6), Trade Drawer v6, dual-timer maintenance
- **2026-02-13**: Codebase reorganization into `tte/` package (PR #4)
- **2026-02-12**: Pine Script screener, entry setups, divergence fix, GUI stop button
- **2026-02-10–11**: Single browser optimization, maintenance loop, Stock Buddy combo API

---

## Important Decisions Made

### Exit Checker Architecture (2026-03-03)
1. **Decouple exit detection from TradingView**: Pine Script `var` state is unreliable (wiped on alert restart). Move exit detection to server-side cron.
2. **Pine Script becomes stateless**: Only sends signals + setup data. No position tracking, no exit detection.
3. **DB-level dedup**: Stock Buddy uses insert-and-catch with partial unique index (atomic, race-free) instead of `n: true` flag.
4. **Vercel cron every 5 min**: Fetches running setups, gets 5-min OHLC candles from Binance/Yahoo, scans for TP/SL hits.
5. **No auto-expire**: Setups stay "running" until TP or SL is actually hit. No 30-day TTL.
6. **Symbol mapping validated**: 622 symbols confirmed. Special handling for Indian stocks (underscore→hyphen), US stocks (dot/slash→hyphen), commodities (XAUUSD→GC=F, XAGUSD→SI=F).
7. **Transition strategy**: Stock Buddy makes `n`/`xt`/`xp`/`xts` optional first, then removes after TTE Phase 3 completes.
8. **TP-first on same candle**: When both TP and SL hit in same 5-min candle, TP wins (matches Pine Script behavior).

### V2 Architecture Decisions (2026-02-26)
1. **Indicator over Strategy**: `strategy.entry/exit` only works for chart symbol.
2. **45-second chart**: `alert.freq_once_per_bar_close`.
3. **Compact JSON keys**: Abbreviated for TradingView's ~2KB limit.
4. **Category-aware pairing**: Same asset class for matching market hours.
5. **Staleness detection REMOVED** (PR #11).
6. **Independent LTF/HTF**: 4 positions per symbol max. No cross-restrictions.
7. **Array payload**: `"b":[ltfPos, htfPos]`, `"se":[ltfPos, htfPos]`.

### Other Decisions
- **Graceful shutdown**: `threading.Event` + force-kill ChromeDriver on Ctrl+C.
- **Snapshot architecture**: Async polling (TTE polls Stock Buddy every 60s).
- **Pre-commit hooks**: ruff + pyright.

---

## Key Reference Files

### TTE Project
| File | Purpose |
|------|---------|
| `.claude/exit-checker-architecture.md` | **Exit checker spec** — full design for cron-based exit detection |
| `Pine Script Code/TTE Screener V2.txt` | V2 screener (will be simplified to stateless in Phase 3) |
| `.claude/agent-comms.md` | Communication with Stock Buddy agent |
| `scripts/validate_symbols.py` | Symbol validation against Binance/Yahoo APIs |
| `tte/main.py` | Entry point — `fetch_symbols_by_category()` for category pairing |
| `tte/config.py` | Config dataclass |
| `combo_settings.yaml` | Settings (45s, batch_size=2, 150s maintenance) |
| `tte/browser/tradingview.py` | Browser automation |

### Stock Buddy App
| File | Purpose |
|------|---------|
| `src/lib/tte/schemas.ts` | Zod schemas + PositionState interface (being updated) |
| `src/lib/tte/collections.ts` | `insertSetupMessage()`, `resolveSetupExit()`, `updateSetupOutcome()` |
| `src/app/api/tte/combo/route.ts` | Webhook handler (being updated) |
| `src/app/api/cron/check-exits/route.ts` | **New** — exit checker cron (being built) |

---

## Verified Patterns

### Symbol Mapping (TradingView → Price API)
| Category | API | Transform |
|----------|-----|-----------|
| Crypto | Binance | Direct (`BTCUSDT`) |
| US Stocks | Yahoo | `.`/`/` → `-` (`BRK.A` → `BRK-A`) |
| Indian Stocks | Yahoo | `_` → `-`, append `.NS` (`BAJAJ_AUTO` → `BAJAJ-AUTO.NS`) |
| Currencies | Yahoo | Append `=X` (`EURUSD` → `EURUSD=X`) |
| Commodities | Yahoo | `XAUUSD` → `GC=F`, `XAGUSD` → `SI=F` |

### Working TradingView Selectors
```
Alert items:       div[data-name="alert-item-name"]
Alert settings:    div[data-name="alerts-settings-button"]
Dropdown menu:     div[data-qa-id="menu-inner"] > div
Legend items:      div[data-qa-id="legend-source-item"]
Indicator inputs:  input[data-qa-id="ui-lib-Input-input"]
Settings dialog:   div[data-name="indicator-properties-dialog"]
```

**WARNING**: Never use TradingView's dynamically generated class names. Always prefer `data-name` and `data-qa-id` selectors.

### MongoDB — 622 Symbols
Categories: `Currencies` (29), `Crypto` (20), `US Stocks` (376), `Indian Stocks` (197)

---

## Test Commands

```bash
# TTE
pipenv run python combo_main.py --maintain-only    # Run maintenance + snapshots (headless)
pipenv run python combo_main.py --validate         # Validate config
pipenv run python combo_main.py --fresh            # Delete alerts & recreate
dist/TTE.exe                                       # GUI (requires pystray)

# Symbol validation
.venv/Scripts/python.exe -u scripts/validate_symbols.py          # Dry-run report
.venv/Scripts/python.exe -u scripts/validate_symbols.py --remove # Remove invalid from DB
```
