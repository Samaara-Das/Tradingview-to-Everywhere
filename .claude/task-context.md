# Task Context Tracker

**Last Updated**: 2026-03-07
**Current Task**: All TTE work complete. TTE.exe running and working perfectly.
**Active Branch**: `main`
**Latest Commit (TTE)**: PR #19 merged — Fix: Bypass SeleniumManager network calls with explicit chromedriver path
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
| 11 | Remove webdriver-manager dependency | **done** (PR #17) |
| 12 | Bypass SeleniumManager network calls with explicit chromedriver path | **done** (PR #19) |

### Exit Checker Implementation Status

| Phase | Scope | Owner | Status |
|-------|-------|-------|--------|
| Phase 1 | DB reset (wipe collections, verify indexes) | Stock Buddy | **Done** |
| Phase 2 | Webhook handler update + exit checker cron | Stock Buddy | **Done** (PR #64) |
| Phase 3 | Strip exit tracking from Pine Script V2 | TTE | **Done** (PR #13) |
| Phase 4 | End-to-end verification | Both | **Pending** (user-side: upload to TV, `--fresh`, verify) |

---

## Session History

### Session: 2026-03-07 (ChromeDriver Fix — PRs #17, #18/#19)

**Goal**: Fix ChromeDriver initialization failures caused by SeleniumManager network errors after removing `webdriver-manager`.

**Chronological flow**:

1. **PR #17 (from previous session)**: Removed `webdriver-manager` dependency, switched to Selenium 4 built-in driver management. But SeleniumManager also failed with network errors (`code: 65, error decoding response body`).

2. **PR #19**: Added `_find_chromedriver()` + `_get_chrome_major_version()` helpers to `tte/browser/tradingview.py`:
   - Fallback chain: `CHROMEDRIVER_PATH` env var → `~/.wdm` cache (version-matched to Chrome major version) → Selenium auto-discovery
   - `_get_chrome_major_version()` runs local PowerShell to get Chrome version (no network)
   - When explicit path found, passes `ChromeService(executable_path=...)` which skips SeleniumManager entirely
   - Also moved `import subprocess` from local (inside `__init__`) to module-level, added `from pathlib import Path`

3. **Verification**:
   - `--validate` passed
   - `_find_chromedriver()` correctly found `~/.wdm/drivers/chromedriver/win64/145.0.7632.117/.../chromedriver.exe`
   - Pre-commit hooks passed (ruff, pyright, ruff-format)
   - `dist/TTE.exe` rebuilt successfully

4. **PR workflow**: Branch created from `fix/remove-webdriver-manager` (PR #17). After merging #17, rebased onto main. PR #18 was auto-closed (base branch deleted), so created PR #19 which was squash-merged.

5. **TTE.exe confirmed working** — running perfectly in production.

### Session: 2026-03-06 (Codebase Audit & Cleanup — PR #16)

**Summary**: Comprehensive audit — 2 bug fixes (ActionChains wrong arg, fragile `.label-*` selector), 6 dead functions removed (~160 lines), ~40 doc corrections across 5 files.

### Session: 2026-03-05 (EOSUSDT/EOSBTC Removal — PR #15)

**Summary**: Removed delisted EOS symbols from MongoDB (620 total, 18 Crypto).

### Session: 2026-03-05 (Trade Drawer V2 Simplification — PR #14)

**Summary**: Simplified Trade Drawer V2 to NWE bands + trade levels only. Fixed seconds-to-ms bug. TTE.exe rebuilt.

### Session: 2026-03-03 (Exit Checker Spec + Phase 3 — PR #13)

**Summary**: Finalized exit checker architecture spec. Rewrote TTE Screener V2 to stateless (943 to 695 lines, removed 104 `var` declarations). Validated 622 symbols against APIs (removed 4 invalid Indian stocks).

### Previous Sessions (Summary)
- **2026-03-03**: PR #12 merged (signal detection guards), save_layout() fix, Task 1/2 debug
- **2026-02-27**: V2 debug testing + cleanup, maintenance TimeoutException fix
- **2026-02-26**: V2 implementation cycle (Pine Script + Python + PR), stale CSS selectors fix
- **2026-02-23**: Snapshot quality + GUI defaults (PR #7)
- **2026-02-20-21**: Chart snapshots feature (PR #6), Trade Drawer, dual-timer maintenance
- **2026-02-13**: Codebase reorganization into `tte/` package (PR #4)
- **2026-02-10-12**: Pine Script screener, maintenance loop, Stock Buddy combo API

---

## Important Decisions Made

### ChromeDriver Fix (2026-03-07)
1. **Bypass SeleniumManager with explicit path**: Pass `executable_path` to `ChromeService` when cached driver found — avoids all network calls.
2. **Version matching**: Match chromedriver to Chrome's major version from `~/.wdm` cache. Fallback to newest available if no match.
3. **Graceful degradation**: If no cached driver found, fall back to Selenium auto-discovery (works when network available).

### Cleanup PR #16 (2026-03-06)
1. **Leave fragile hashed selectors as-is**: `.text-yyMUOAN9`, `.layoutTitle-yyMUOAN9`, `.content-tBgV1m0B` are risky to change without inspecting current TradingView HTML.
2. **Use `condition_dropdown.text`** instead of finding child `.label-*` element.

### Exit Checker Architecture (2026-03-03)
1. **Decouple exit detection from TradingView**: Server-side cron (every 5 min).
2. **Pine Script becomes stateless**: Only sends signals + setup data.
3. **DB-level dedup**: Partial unique index on `{ symbol, dedupKey }` where `outcome: "running"`.

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

### ChromeDriver Discovery
```
Env var override:  CHROMEDRIVER_PATH
WDM cache path:    ~/.wdm/drivers/chromedriver/win64/<version>/chromedriver-win32/chromedriver.exe
Chrome exe path:   C:\Program Files\Google\Chrome\Application\chrome.exe
Current versions:  Chrome 145.0.7632.160, chromedriver 145.0.7632.117
```

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

### Symbol Mapping (TradingView to Price API)
| Category | API | Transform |
|----------|-----|-----------|
| Crypto | Binance | Direct (`BTCUSDT`) |
| US Stocks | Yahoo | `.`/`/` to `-` (`BRK.A` to `BRK-A`) |
| Indian Stocks | Yahoo | `_` to `-`, append `.NS` |
| Currencies | Yahoo | Append `=X` (`EURUSD` to `EURUSD=X`) |
| Commodities | Yahoo | `XAUUSD` to `GC=F`, `XAGUSD` to `SI=F` |

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
