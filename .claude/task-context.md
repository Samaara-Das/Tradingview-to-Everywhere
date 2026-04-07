# Task Context Tracker

**Last Updated**: 2026-04-07
**Current Task**: Webhook URL updated to `https://stockbuddy.co/api/tte/combo`, TTE.exe rebuilt. Ready for `--fresh` run.
**Active Branch**: `main`
**Latest Commit (TTE)**: `585aca5` — Merge pull request #22

---

## Task Progress Summary

| # | Task | Status |
|---|------|--------|
| 1 | Get alerts to trigger for Indian stocks | **done** (PR #11) |
| 2 | Check signal detection for US stocks and Indian stocks | **done** (PR #12) |
| 3 | Figure out why only 262 alerts got created instead of 314 | **resolved** |
| 4 | Make new API polling architecture (exit checker) | **done** (PR #13, Stock Buddy PR #64) |
| 5 | Test signals, setups, exits for the user | **pending** (user-side, needs market hours) |
| 6 | Verify Indian stock alerts trigger after exchange prefix fix | **pending** (user-side, needs NSE hours) |
| 7 | Post-deployment: verify signal timing & timestamps | **pending** (user-side, needs market hours) |
| 8 | Fix snapshot Trade Drawer not rendering on chart | **done** (PR #14) |
| 9 | Remove delisted EOSUSDT/EOSBTC from MongoDB | **done** (PR #15) |
| 10 | Fix bugs, remove dead code, sync docs | **done** (PR #16) |
| 11 | Remove webdriver-manager dependency | **done** (PR #17) |
| 12 | Bypass SeleniumManager network calls with explicit chromedriver path | **done** (PR #19) |
| 13 | Fix snapshot pipeline — backfill, dialog cleanup, throughput | **done** (PR #20, merged) |
| 14 | Symbol universe update (620 → 677) — snapshot fix + fresh run | **done** (PR #21, merged) |
| 15 | Fix 41 failed symbols — overlay retry, --symbols flag, TV UI adaptation | **done** (PR #22, merged) |
| 16 | Verify alert-symbol alignment (orchestrator mission) | **done** — PASS |
| 17 | Fix TradingView layout selector bug (dynamic class names changed) | **done** (2026-04-06) |
| 18 | Update webhook URL to new Stock Buddy deployment | **done** (2026-04-06) |
| 19 | Update webhook URL to stockbuddy.co custom domain | **done** (2026-04-07) |

---

## Session History

### Session: 2026-04-07 (Webhook URL Update to stockbuddy.co)

**User request**: Update webhook URL to `https://stockbuddy.co/api/tte/combo` (custom domain) and rebuild exe.

**What was done**:
1. Switched to `main` branch (PR #22 already merged at `585aca5`)
2. Updated `.env`: `COMBO_WEBHOOK_URL` changed from `stock-buddy-app-nine.vercel.app` to `stockbuddy.co`
3. Rebuilt `dist/TTE.exe` (19 MB) — all validations passed
4. No git commit needed (`.env` is gitignored)

**Next step**: User needs to run TTE.exe with "Fresh (delete all)" to recreate all 340 alerts with new webhook URL.

### Session: 2026-04-06 (Layout Selector Fix + Webhook URL Update)

**User request**: Update webhook URL in all 340 alerts to `https://stock-buddy-app-nine.vercel.app/api/tte/combo`, and fix TTE startup error.

**Bug 1 — Layout selector crash** (`NoSuchElementException: .text-yyMUOAN9`):
- **Root cause**: TradingView redesigned the layout toolbar. `#header-toolbar-save-load` changed from a `div` containing buttons to a single `button` element. Dynamic class names no longer exist.
- **Fix** (`tte/browser/tradingview.py`):
  - `change_layout()`: Click `button[data-name="save-load-menu"]` via ActionChains, find layout item by XPath `normalize-space(text())`
  - `current_layout()`: Get text directly from `#header-toolbar-save-load` button
  - Removed all dynamic class selectors
- **Tested**: Layout switched successfully, alert creation began

**Bug 2 — Webhook URL update**: Updated `.env` with new URL.

**Exe rebuild**: `dist/TTE.exe` rebuilt, all validations passed.

### Session: 2026-03-23 (Alert-Symbol Alignment Verification)

**Orchestrator mission**: Verify `--fresh` and retry runs used correct 677-symbol DB.
- Sampled 28 symbols from logs — **28/28 match**
- Searched for 6 removed symbols — **zero matches**
- Retry run: 21/21 alerts (100% success)
- **Verdict**: PASS

### Session: 2026-03-23 (Fix 41 Failed Symbols + TradingView UI Adaptation)

- Overlay retry fix: 3-attempt retry loop (wait for overlay → ESC → JS click)
- `--symbols` CLI flag for targeted alert creation
- Timeframe toolbar CSS selector fix (`#header-toolbar-intervals`)
- Alert dialog Notifications sub-page adaptation
- Result: 319 + 21 = **340 alerts covering all 677 symbols**
- PR #22 created

### Previous Sessions (Summary)
- **2026-03-20**: Snapshot pipeline fix (PR #20, #21) — backfill, dialog cleanup, multi-batch
- **2026-03-07**: ChromeDriver fix (PRs #17, #19)
- **2026-03-06**: Codebase audit, bug fixes, dead code removal (PR #16)
- **2026-03-05**: Trade Drawer V2, EOS removal (PRs #14, #15)
- **2026-03-03**: Signal guards, stateless screener (PRs #12, #13)
- **2026-02-26**: V2 implementation (Pine Script + Python)
- **2026-02-20-23**: Snapshots feature (PRs #6, #7)
- **2026-02-10-13**: Codebase reorg (PR #4), Pine Script screener

---

## Important Decisions Made

### Layout Selector Fix (2026-04-06)
1. **XPath text matching over CSS selectors**: TradingView dropdown items render in unidentified containers. `normalize-space(text())` XPath is the most reliable approach.
2. **`button[data-name="save-load-menu"]` is stable**: Survived the TV redesign.
3. **ActionChains click over JS click**: Produces proper mouse events for TradingView's React handlers.
4. **`#header-toolbar-save-load` is now a button**: Get layout name via `.text.strip()` directly.

### Previous Decisions (Summary)
- **Overlay retry (2026-03-23)**: 3 attempts — wait for overlay, ESC, then JS click
- **CSS selectors over XPath for timeframe toolbar (2026-03-23)**
- **Alert dialog Notifications sub-page (2026-03-23)**: New flow replaces old tab-based approach
- **Snapshot pipeline (2026-03-20)**: Targeted dialog cleanup, multi-batch, backfill
- **ChromeDriver (2026-03-07)**: Bypass SeleniumManager with explicit `~/.wdm` cache path
- **Exit checker (2026-03-03)**: Server-side cron, Pine Script stateless
- **V2 architecture (2026-02-26)**: 45s chart, compact JSON keys, category-aware pairing

---

## Key Reference Files

| File | Purpose |
|------|---------|
| `tte/main.py` | Entry point (orchestrator, maintenance loop, `--symbols` flag) |
| `tte/snapshot_worker.py` | Snapshot worker (multi-batch, dialog cleanup, backfill) |
| `tte/config.py` | Config dataclass |
| `tte/browser/tradingview.py` | Browser automation (layout switch, overlay retry, Notifications sub-page) |
| `tte/browser/chart.py` | Chart navigation (timeframe with CSS selectors, symbol search) |
| `tte/data/symbols.py` | MongoDB symbol fetching (returns `full_symbol` with exchange prefix) |
| `combo_settings.yaml` | Settings (batch_size=2, snapshot batch_size=10, 150s maintenance) |
| `Pine Script Code/TTE Screener V2.txt` | V2 screener (stateless setup detection) |
| `Pine Script Code/Trade Drawer V2.txt` | NWE bands + trade level drawings for snapshots |

---

## Verified Patterns

### Layout Toolbar Selectors (Updated 2026-04-06)
```
Save button:        button#header-toolbar-save-load
Layout name:        button#header-toolbar-save-load .text (use .text.strip())
Dropdown trigger:   button[data-name="save-load-menu"] (aria-label="Manage layouts")
Layout items:       XPath: //*[normalize-space(text())="LayoutName"]
```

### Alert Dialog Selectors (Updated 2026-03-23)
```
Webhook button:     button[data-qa-id="alert-notifications-button"]
Notifications page: div[data-qa-id="alerts-notifications-edit-dialog"]
Webhook checkbox:   label[data-qa-id="webhook"] input[type="checkbox"]
Webhook URL input:  input#webhook-url
Apply/Submit:       button[data-qa-id="submit"]
Create dialog:      div[data-qa-id="alerts-create-edit-dialog"]
Condition dropdown: span[data-qa-id="ui-kit-disclosure-control main-series-select"]
```

### Timeframe Toolbar Selectors (Updated 2026-03-23)
```
Dropdown arrow:     #header-toolbar-intervals > button[aria-label="Chart interval"]
Active timeframe:   #header-toolbar-intervals button[aria-checked="true"]
Dropdown menu:      div[data-qa-id="menu-inner"]
Menu items:         div.menuItem-RmqZNwwp
Menu labels:        span.label-jFqVJoPk
```

### Other TradingView Selectors
```
Alert items:       div[data-name="alert-item-name"]
Alert settings:    div[data-name="alerts-settings-button"]
Legend items:      div[data-qa-id="legend-source-item"]
Settings dialog:   div[data-name="indicator-properties-dialog"]
Overlay (blocker): div.screen-otjoFNF2.fade-otjoFNF2
```

**WARNING**: Never use TradingView's dynamically generated class names. Always prefer `data-name`, `data-qa-id`, `aria-label`, and XPath text matching.

### MongoDB — 677 Symbols
Categories: `Currencies` (29), `Crypto` (18), `US Stocks` (243), `Indian Stocks` (387)
Exchanges: NSE (300), BSE (87), NASDAQ (122), NYSE (118), AMEX (1), CBOE (2), BINANCE (18), FX (29)

### Alert Math
- 340 alerts total: 337 with 2 symbols + 3 with 1 symbol
- 337 x 2 + 3 x 1 = 677 symbols (no duplicates)

---

## Test Commands

```bash
# TTE
pipenv run python combo_main.py --maintain-only    # Run maintenance + snapshots (headless)
pipenv run python combo_main.py --validate         # Validate config
pipenv run python combo_main.py --fresh            # Delete alerts & recreate (~340 alerts)
pipenv run python combo_main.py --setup-only --symbols SYM1,SYM2  # Specific symbols only
dist/TTE.exe                                       # GUI (requires pystray)

# Verification
pipenv run pyright tte/                            # Type checking
pipenv run ruff check tte/                         # Linting
```

## Remaining Tasks

- [ ] Run `--fresh` via TTE.exe to recreate 340 alerts with new webhook URL (`stockbuddy.co`)
- [ ] Restart maintenance loop via TTE.exe GUI
- [ ] **Task 5**: Verify alerts are firing — check Stock Buddy webhook logs
- [ ] **Task 6**: Verify Indian stock (BSE) alerts trigger during NSE hours
- [ ] **Task 7**: Verify signal timing & timestamps
