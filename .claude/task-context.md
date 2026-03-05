# Task Context Tracker

**Last Updated**: 2026-03-05
**Current Task**: EOSUSDT/EOSBTC removal done. User will run `--setup-only --symbols BCHUSDT` to restore BCHUSDT coverage.
**Active Branch**: `main`
**Latest Commit (TTE)**: `dab4b33` — Simplify Trade Drawer V2 (PR #14 squash-merged)
**Latest Commit (Stock Buddy)**: PR #67 deployed — exit cron bug fixes (yahoo-finance2 v3, entry candle skip)

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
| 8 | Fix snapshot Trade Drawer not rendering on chart | **done** — PR #14 merged. V2 simplified (NWE + trade levels). TTE.exe rebuilt. |
| 9 | Remove delisted EOSUSDT/EOSBTC from MongoDB | **done** — Both deleted. User running `--setup-only --symbols BCHUSDT` to restore coverage. |

### Exit Checker Implementation Status

| Phase | Scope | Owner | Status |
|-------|-------|-------|--------|
| Phase 1 | DB reset (wipe collections, verify indexes) | Stock Buddy | **Done** |
| Phase 2 | Webhook handler update + exit checker cron | Stock Buddy | **Done** (PR #64 deployed) |
| Phase 3 | Strip exit tracking from Pine Script V2 | TTE | **Done** (code complete, needs TV upload) |
| Phase 4 | End-to-end verification | Both | **Next** — upload to TV, recreate alerts, verify |

---

## Session History

### Session: 2026-03-05 (EOSUSDT/EOSBTC Removal — Orchestrator Mission)

**Goal**: Remove delisted EOS symbols from MongoDB per orchestrator mission in `.claude/current-mission.md`.

**Chronological flow**:

1. **Queried MongoDB**: Found EOSUSDT and EOSBTC in `tte.symbols` (Crypto category). No live_signals or setup_messages existed for either.
2. **Deleted both symbols** from `tte.symbols` by ObjectId (bulk `$in` delete failed silently — used direct `delete_one` per ObjectId).
3. **Verified counts**: 620 total symbols, 18 Crypto (was 622/20).
4. **Pairing analysis**: Initially thought EOSBTC+EOSUSDT were paired together (alphabetical sort). User corrected: the actual TradingView alert paired **EOSUSDT + BCHUSDT**. After deleting that alert, BCHUSDT has no coverage.
5. **Resolution**: User will run `python combo_main.py --setup-only --symbols BCHUSDT` to create a single alert for BCHUSDT. On next `--fresh` run, BCHUSDT will auto-pair with BCHBTC (new alphabetical order).
6. **Updated docs**: ARCHITECTURE.md (Crypto 20→18, totals), task-context.md, exit-checker-architecture.md, symbols.py docstring, MEMORY.md.
7. **Wrote completion report** to `C:/Users/dassa/Work/TTE-SB-Orchestrator/agent-comms.md`.

**Key learning**: TradingView alert pairing may not match the alphabetical sort order assumed in code — the actual pairing depends on when `--fresh` was run and with what symbol list.

---

### Session: 2026-03-05 (Trade Drawer V2 — Simplification)

**Goal**: Simplify Trade Drawer V2 — keep NWE bands + trade levels, remove candle drawing & bar hiding (overcomplicated). Native chart bars stay visible.

**Chronological flow**:

1. **Rewrote `Pine Script Code/Trade Drawer V2.txt`**:
   - **Kept**: NWE band calculation (kernel functions, 7 plots, 4 fills) using built-in `close`/`high`/`low`
   - **Removed**: All candle drawing (box/line arrays, `ticker.standard()` OHLC, `request.security()`, 60-bar candle loop)
   - **Reverted**: Trade level anchoring back to `dateTime` (original behavior from Trade Drawer.txt)
   - **Reverted**: `max_lines_count=10, max_labels_count=10` (no boxes needed)
2. **Fixed seconds→milliseconds bug**: `alertTimestamp` from Stock Buddy is Unix seconds, TradingView `time` is milliseconds. Fixed: `startTime = dateTime > 0 ? dateTime * 1000 : time`
3. **Shortened trade level lines**: 30 bars → 15 bars (`endTime = startTime + 15 * dt`)
4. **Cleaned up `tte/snapshot_worker.py`**:
   - Deleted `_bars_hidden: bool = False` field
   - Deleted `if not self._bars_hidden: self._hide_chart_bars()` block
   - Deleted entire `_hide_chart_bars()` method (~65 lines)
   - Reverted module docstring (removed bar-hiding references)
   - Kept `sleep(2)` render wait (NWE calculation needs time)
5. **Tested with real Stock Buddy data**: SCCO Buy setup (Entry 199.13, SL 197.5, TP1 202.39, nweTf 1H). User confirmed setup draws correctly on chart.
6. **Committed** `42ffba3`, pushed, PR #14 squash-merged → `dab4b33` on main.
7. **Rebuilt TTE.exe** — `dist/TTE.exe` (PyInstaller onefile, ~19MB).
8. **User completed TradingView setup**: Pasted Trade Drawer V2 on Snapshot layout, removed separate NWE indicator.

**Key files modified**:
- `Pine Script Code/Trade Drawer V2.txt` — Simplified: NWE bands + dateTime-anchored trade levels
- `tte/snapshot_worker.py` — Removed `_hide_chart_bars()`, `_bars_hidden`

### Previous Session: 2026-03-05 (Trade Drawer V2 — Initial Attempt)

**Summary**: Created self-contained Trade Drawer V2 with NWE bands + plotcandle + bar hiding. Committed as `42bbd92`→`d987d35`. This approach was overcomplicated — simplified in the session above.

---

### Session: 2026-03-03 (Exit Checker Spec, Symbol Validation, Agent Comms)

**Summary**: Finalized exit checker architecture spec, validated 622 symbols against Binance/Yahoo APIs (removed 4 invalid Indian stocks), wrote agent-comms to Stock Buddy, confirmed all design decisions.

### Session: 2026-03-03 (Phase 3: Stateless Pine Script Rewrite)

**Summary**: Rewrote TTE Screener V2 Pine Script to stateless (943 → 695 lines). Deleted all 104 `var` declarations, exit detection, position clearing, isNew reset, exitSent flags. `buildPosV2()` → `buildSetupV2()`. Needs TV upload.

### Session: 2026-03-03 (PR Review, Merge, save_layout Fix)

**Summary**: Merged PR #12 (signal detection guards), fixed save_layout() bug (`72237e1`).

### Previous Sessions (Summary)
- **2026-03-03**: Task 2 debug (wrong signal detection), Task 1 fix (Indian stock alerts, PR #11)
- **2026-02-27**: V2 debug testing + cleanup, maintenance TimeoutException fix
- **2026-02-26**: V2 implementation cycle (Pine Script + Python + PR), stale CSS selectors fix
- **2026-02-23**: Snapshot quality + GUI defaults (PR #7)
- **2026-02-20–21**: Chart snapshots feature (PR #6), Trade Drawer, dual-timer maintenance
- **2026-02-13**: Codebase reorganization into `tte/` package (PR #4)
- **2026-02-10–12**: Pine Script screener, maintenance loop, Stock Buddy combo API

---

## Important Decisions Made

### Trade Drawer V2 (2026-03-05)
1. **NWE bands + trade levels only**: No candle drawing, no bar hiding. Native chart bars stay visible on Snapshot layout.
2. **dateTime anchoring with ms conversion**: `startTime = dateTime > 0 ? dateTime * 1000 : time` (Stock Buddy sends Unix seconds, TV uses milliseconds).
3. **15-bar trade level span**: `endTime = startTime + 15 * dt`.
4. **Replaces old Trade Drawer + NWE combo**: Single indicator handles both NWE envelope and trade level drawings.

### Exit Checker Architecture (2026-03-03)
1. **Decouple exit detection from TradingView**: Move to server-side cron (every 5 min).
2. **Pine Script becomes stateless**: Only sends signals + setup data.
3. **DB-level dedup**: Insert-and-catch with partial unique index.
4. **No auto-expire**: Setups stay "running" until TP or SL hit.
5. **TP-first on same candle**: When both hit in same 5-min candle, TP wins.

### V2 Architecture Decisions (2026-02-26)
1. **45-second chart** with `alert.freq_once_per_bar_close`.
2. **Compact JSON keys** for TradingView's ~2KB limit.
3. **Category-aware pairing**: Same asset class for matching market hours.

---

## Key Reference Files

### TTE Project
| File | Purpose |
|------|---------|
| `Pine Script Code/Trade Drawer V2.txt` | NWE bands + trade level drawings (simplified, no candles/bar hiding) |
| `Pine Script Code/Trade Drawer.txt` | Old Trade Drawer (replaced by V2) |
| `.claude/exit-checker-architecture.md` | Exit checker spec — full design for cron-based exit detection |
| `Pine Script Code/TTE Screener V2.txt` | V2 screener (stateless) |
| `tte/snapshot_worker.py` | Snapshot worker — `_set_trade_drawer()`, `_take_snapshot()` (no more `_hide_chart_bars()`) |
| `tte/main.py` | Entry point |
| `tte/config.py` | Config dataclass |
| `combo_settings.yaml` | Settings (45s, batch_size=2, 150s maintenance) |
| `tte/browser/tradingview.py` | Browser automation |

---

## Verified Patterns

### Chart Settings Selectors
```
Settings dialog:    div[data-name="series-properties-dialog"]
Canvas tab:         button[data-name="canvas"]
Submit:             button[name="submit"]
Right margin:       input[data-name="paneRightMargin"]
```

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

### Symbol Mapping (TradingView → Price API)
| Category | API | Transform |
|----------|-----|-----------|
| Crypto | Binance | Direct (`BTCUSDT`) |
| US Stocks | Yahoo | `.`/`/` → `-` (`BRK.A` → `BRK-A`) |
| Indian Stocks | Yahoo | `_` → `-`, append `.NS` |
| Currencies | Yahoo | Append `=X` (`EURUSD` → `EURUSD=X`) |
| Commodities | Yahoo | `XAUUSD` → `GC=F`, `XAGUSD` → `SI=F` |

### MongoDB — 620 Symbols
Categories: `Currencies` (29), `Crypto` (18), `US Stocks` (376), `Indian Stocks` (197)

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
