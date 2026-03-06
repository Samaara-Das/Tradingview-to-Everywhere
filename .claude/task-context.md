# Task Context Tracker

**Last Updated**: 2026-03-06
**Current Task**: All TTE work complete. No pending tasks.
**Active Branch**: `main`
**Latest Commit (TTE)**: `cbd5481` — Chore: Fix bugs, remove dead code, sync docs (PR #16 squash-merged)
**Latest Commit (Stock Buddy)**: PR #67 deployed — exit cron bug fixes (yahoo-finance2 v3, entry candle skip)

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

### Exit Checker Implementation Status

| Phase | Scope | Owner | Status |
|-------|-------|-------|--------|
| Phase 1 | DB reset (wipe collections, verify indexes) | Stock Buddy | **Done** |
| Phase 2 | Webhook handler update + exit checker cron | Stock Buddy | **Done** (PR #64) |
| Phase 3 | Strip exit tracking from Pine Script V2 | TTE | **Done** (PR #13) |
| Phase 4 | End-to-end verification | Both | **Pending** (user-side: upload to TV, `--fresh`, verify) |

---

## Session History

### Session: 2026-03-06 (Codebase Audit & Cleanup — PR #16)

**Goal**: Comprehensive audit of TTE for remaining bugs, dead code, and doc inaccuracies. Fix everything in one PR.

**Chronological flow**:

1. **Ran 4 parallel audit agents**:
   - TODO/FIXME scan → no active markers in production code
   - Doc accuracy audit → found ~40 discrepancies across 5 doc files
   - QA audit (Pyright, dead code, Selenium patterns) → found 2 bugs, 6 dead functions, fragile selectors
   - Pending tasks scan → confirmed remaining items are user-side only

2. **Bug fixes** (2):
   - `tte/browser/tradingview.py:1244`: `ActionChains(menu)` passed `WebElement` instead of `WebDriver` → fixed to `ActionChains(self.driver)`. Would crash on scroll fallback in `reupload_indicator()`.
   - `tte/browser/tradingview.py:847`: Replaced fragile `.label-LM2kIa9B` hashed CSS selector with `condition_dropdown.text` in `_validate_alert_condition()`.

3. **Dead code removal** (6 functions, 2 test files, ~160 lines):
   - `chunk_symbols()` from `tte/main.py` — never called (replaced by `fetch_symbols_by_category()`)
   - `_reinitialize_screener_indicator()` from `tradingview.py` — never called, would crash (references unset attributes)
   - `is_log_tab_open()`, `is_alert_tab_open()` from `helpers.py` — never called
   - `trim_file()`, `continuous_trim()`, `start_continuous_trim()` from `log.py` — never called
   - Removed `threading`, `time`, `os` imports from `log.py` (only used by dead code)
   - Deleted `tests/test_log.py` and `tests/test_main.py` (tested deleted functions)

4. **Doc updates** (~40 corrections across 5 files):
   - `README.md`: "30 seconds" → "45 seconds" (3 places), 626→620, "setup/exit tracking" → "stateless"
   - `CLAUDE.md`: "all in Pine Script" → clarified exit detection is server-side
   - `docs/combo/ARCHITECTURE.md`: Fixed ~25 stale references (626→620, ~314→~310, "position tracking in Pine Script" → stateless, Trade Drawer V1→V2 refs, maintenance "5 min" → "2.5 min", Q9 "338 batches of 3" → "~310 batches of 2")
   - `docs/combo/PRD.md`: Fixed ~10 stale references (same patterns as above)
   - `.claude/exit-checker-architecture.md`: Status "pending implementation" → "Implemented (PR #13, PR #64)"

5. **Cleanup**: Deleted `.claude/current-mission.md` (EOSUSDT mission completed)

6. **Committed** `8c293d0`, pushed, PR #16 squash-merged → `cbd5481` on main. Pre-commit hooks passed (Pyright, ruff, ruff-format).

**Known risks left as-is** (fragile hashed selectors, currently working):
- `.text-yyMUOAN9` / `.layoutTitle-yyMUOAN9` in `change_layout()` (lines 369, 394, 409)
- `.content-tBgV1m0B` in `_close_dropdown_by_clicking_settings()` (line 433)

---

### Session: 2026-03-05 (EOSUSDT/EOSBTC Removal — PR #15)

**Summary**: Removed delisted EOS symbols from MongoDB (620 total, 18 Crypto). BCHUSDT needs `--setup-only --symbols BCHUSDT` to restore coverage.

### Session: 2026-03-05 (Trade Drawer V2 Simplification — PR #14)

**Summary**: Simplified Trade Drawer V2 to NWE bands + trade levels only (removed candle drawing & bar hiding). Fixed seconds→ms bug. TTE.exe rebuilt.

### Session: 2026-03-03 (Exit Checker Spec + Phase 3 — PR #13)

**Summary**: Finalized exit checker architecture spec. Rewrote TTE Screener V2 to stateless (943→695 lines, removed 104 `var` declarations). Validated 622 symbols against APIs (removed 4 invalid Indian stocks).

### Previous Sessions (Summary)
- **2026-03-03**: PR #12 merged (signal detection guards), save_layout() fix, Task 1/2 debug
- **2026-02-27**: V2 debug testing + cleanup, maintenance TimeoutException fix
- **2026-02-26**: V2 implementation cycle (Pine Script + Python + PR), stale CSS selectors fix
- **2026-02-23**: Snapshot quality + GUI defaults (PR #7)
- **2026-02-20–21**: Chart snapshots feature (PR #6), Trade Drawer, dual-timer maintenance
- **2026-02-13**: Codebase reorganization into `tte/` package (PR #4)
- **2026-02-10–12**: Pine Script screener, maintenance loop, Stock Buddy combo API

---

## Important Decisions Made

### Cleanup PR #16 (2026-03-06)
1. **Leave fragile hashed selectors as-is**: `.text-yyMUOAN9`, `.layoutTitle-yyMUOAN9`, `.content-tBgV1m0B` are risky to change without inspecting current TradingView HTML. They work today.
2. **Use `condition_dropdown.text`** instead of finding child `.label-*` element — simpler and selector-agnostic.

### Trade Drawer V2 (2026-03-05)
1. **NWE bands + trade levels only**: No candle drawing, no bar hiding.
2. **dateTime anchoring with ms conversion**: `startTime = dateTime > 0 ? dateTime * 1000 : time`.
3. **15-bar trade level span**: `endTime = startTime + 15 * dt`.

### Exit Checker Architecture (2026-03-03)
1. **Decouple exit detection from TradingView**: Server-side cron (every 5 min).
2. **Pine Script becomes stateless**: Only sends signals + setup data.
3. **DB-level dedup**: Partial unique index on `{ symbol, dedupKey }` where `outcome: "running"`.
4. **TP-first on same candle**: When both hit in same 5-min candle, TP wins.

### V2 Architecture (2026-02-26)
1. **45-second chart** with `alert.freq_once_per_bar_close`.
2. **Compact JSON keys** for TradingView's ~2KB limit.
3. **Category-aware pairing**: Same asset class for matching market hours.

---

## Key Reference Files

| File | Purpose |
|------|---------|
| `Pine Script Code/TTE Screener V2.txt` | V2 screener (stateless setup detection) |
| `Pine Script Code/Trade Drawer V2.txt` | NWE bands + trade level drawings for snapshots |
| `.claude/exit-checker-architecture.md` | Exit checker spec (implemented) |
| `tte/main.py` | Entry point (orchestrator) |
| `tte/config.py` | Config dataclass |
| `tte/browser/tradingview.py` | Browser automation (Selenium) |
| `tte/snapshot_worker.py` | Snapshot worker |
| `combo_settings.yaml` | Settings (45s, batch_size=2, 150s maintenance) |

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
