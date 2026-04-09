# Task Context Tracker

**Last Updated**: 2026-04-09
**Current Task**: Maintenance loop + snapshots running via TTE.exe (all alerts active)
**Active Branch**: `main`
**Latest Commit**: `7f344ab` — Merge pull request #24 (TradingView UI redesign fixes)

---

## Task Progress Summary

| # | Task | Status |
|---|------|--------|
| 1-16 | Previous tasks (alerts, signals, snapshots, cleanup) | **done** |
| 17 | Fix TradingView layout selector bug | **done** (2026-04-06) |
| 18 | Update webhook URL to new Stock Buddy deployment | **done** (2026-04-06) |
| 19 | Update webhook URL to stockbuddy.co custom domain | **done** (2026-04-07) |
| 20 | Fix delete_all_alerts dropdown bug | **done** (2026-04-07) |
| 21 | Auto-retry failed alert batches after creation | **done** (2026-04-07) |
| 22 | Fix layout dropdown selector (scoped XPath + navigate via href) | **done** (2026-04-07) |
| 23 | Fix timeframe dropdown (collapsible sections redesign) | **done** (2026-04-07) |
| 24 | Fix alert creation hang (two root causes) | **done** (2026-04-07) |
| 25 | Run `--fresh` via TTE.exe to recreate 340 alerts | **done** (2026-04-07, 280/340) |
| 26 | Retry 60 failed alert batches (119 symbols) | **done** (2026-04-09, 60/60) |
| 27 | Fix `STOCK_BUDDY_API_URL` in `.env` (old Vercel → stockbuddy.co) | **done** (2026-04-09) |
| 28 | Sync all docs after PRs #19-#24 (webhook URLs, batch sizes, counts) | **done** (2026-04-09) |
| 29 | Create TTE-specific /update-docs skill | **done** (2026-04-09) |
| 30 | Rebuild TTE.exe (post-PR #24 UI fixes) | **done** (2026-04-09, 19.43 MB) |

---

## Session History

### Session: 2026-04-09

**User request**: Retry 60 failed alert batches, fix maintenance loop, fix snapshot worker, update docs, rebuild exe.

#### 1. Retried 60 failed alert batches (119 symbols)

**Root cause of original failure**: Screener V2 indicator had been removed from the "Screener" layout after force-kills corrupted Chrome profile state. `get_indicator()` timed out on `legend-source-item`.

**How**: User manually re-added the indicator to the layout. Then we ran `--symbols` with all 119 symbols via Python directly (bash line-length limit prevented `--symbols` CLI with that many symbols).

**Result**: 60/60 alerts created successfully. Total alert count: ~340.

#### 2. Fixed snapshot worker (402 errors)

**Root cause**: `STOCK_BUDDY_API_URL` in `.env` still pointed to old Vercel deployment: `https://stock-buddy-app.vercel.app/api/tte`. That deployment is paused/over quota, returning 402.

**Fix**: Updated `.env` line 34: `STOCK_BUDDY_API_URL="https://stockbuddy.co/api/tte"`

**Verified**: Snapshot worker fetched 10 pending snapshots, took screenshots, submitted to Stock Buddy with no errors. Log line: `Fetched 10 pending snapshots` + multiple `Snapshot completed for NSE:*` with no `Failed to update snapshot` errors.

#### 3. Fixed maintenance loop (zombie process)

**Root cause**: Previous `--symbols` runs left 3 stale Python processes (PIDs 17640, 9376, 16704) with dead browser sessions. Killed them all, started fresh `--maintain-only`.

**Confirmed working**: First cycle: `No inactive alerts to restart (button is disabled)` + `Alert log cleared!`

#### 4. Documentation sync (after PRs #19-#24)

Updated 8 doc files and the /update-docs skill itself:

| File | Changes |
|------|---------|
| `CLAUDE.md` | Added `snapshot_worker.py`, `--symbols` flag, `STOCK_BUDDY_API_URL`/`API_TIMEOUT` env vars, fixed `snapshot.batch_size` (5→10), removed stale AGENTS.md reference |
| `README.md` | Updated webhook URL, added `--symbols` flag, added `snapshot_worker.py` to structure |
| `docs/combo/ARCHITECTURE.md` | Updated webhook URL, fixed `handle_alerts.py` ref → `tte/main.py` |
| `docs/combo/PRD.md` | Moved failed-batch-retry/UI-fixes to Completed; fixed `snapshot.batch_size` (5→10) |
| `docs/API.md` | Updated base URL and all curl examples |
| `docs/SETUP.md` | Updated webhook URL, fixed `snapshot.batch_size` (5→10) |
| `docs/TROUBLESHOOTING.md` | Updated ChromeDriver section (Selenium 4 built-in); added TradingView UI Changes section |
| `docs/DATABASE.md` | Updated symbol counts (us_stocks ~719→~376, indian_stocks ~268→~197), updated webhook URL |
| `.claude/skills/update-docs/SKILL.md` | Full rewrite: TTE-specific (was Stock Buddy) |
| `.claude/skills/update-docs/references/doc-inventory.md` | Updated to April 2026; added Trade Drawer V2 |

#### 5. Rebuilt TTE.exe

Previous exe (built 15:38 Apr 7) was missing PR #24 UI fixes (merged 16:08 Apr 7).

**Result**: New `dist/TTE.exe` — 19.43 MB, PyInstaller 6.18.0, all validations passed. User launched it successfully.

---

### Session: 2026-04-07 (TradingView UI Redesign Fixes)

**User request**: Run `--fresh` to recreate all 340 alerts. Hit multiple TradingView UI breakages.

#### Bug 1 — Layout dropdown XPath too broad (FIXED)
**Root cause**: XPath `//*[normalize-space(text())="Screener"]` matched chart legend instead of dropdown item.
**Fix** (`tte/browser/tradingview.py` `change_layout()`): Scoped to `data-qa-id="save-load-menu-item-recent"`. Non-current layouts are `<a target="_blank">` links — extract `href`, navigate via `driver.get(url)`.

#### Bug 2 — Timeframe dropdown redesigned (FIXED)
**Root cause**: Changed from flat list to collapsible sections (Ticks/Seconds/Minutes/Hours/Days/Ranges).
**Fix** (`tte/browser/chart.py`): New helpers `_get_timeframe_section()`, `_open_timeframe_dropdown()`, `_expand_timeframe_section()`. Rewrote `change_tframe()` and `force_change_tframe()`.

#### Bug 3 — Alert creation hang (FIXED — two root causes)
**Root Cause 1**: Screener V2 missing from chart layout (Chrome profile corruption from force-kills).
**Root Cause 2**: TradingView alert dialog redesigned — removed tabs, now uses "Webhook >" button opening a separate sub-dialog.
**Fix** (`tradingview.py` `create_webhook_alert()`): Two-dialog flow (see Alert Dialog Selectors below).

**Other fixes**: `_validate_alert_condition()` contains-match selector; `is_no_error()` stable `data-qa-id` selectors.

---

## Important Decisions Made

### STOCK_BUDDY_API_URL base path (2026-04-09)
`https://stockbuddy.co/api/tte` is correct. The snapshot worker appends sub-paths (`/snapshots/pending`, `/snapshots/update`). The base URL itself returns 404 — that's expected, only sub-routes exist.

### Layout Navigation via href (2026-04-07)
Non-current layouts in TradingView's dropdown are `<a target="_blank">` links. Clicking them opens a new tab. **Solution**: Extract `href` and navigate via `driver.get(url)`.

### Timeframe Dropdown Section Expansion (2026-04-07)
TradingView now groups timeframes into collapsible sections. TTE must: (1) identify section, (2) expand if `aria-expanded="false"`, (3) find item.

### Alert Dialog Two-Step Flow (2026-04-07)
Webhook settings are now behind a "Webhook >" button that opens a separate sub-dialog. TTE must: (1) configure conditions in main dialog, (2) click webhook button, (3) configure webhook in sub-dialog, (4) apply, (5) create in main dialog.

### legend-source-item vs legend-series-item (2026-04-07)
- `legend-series-item` = main chart series (OHLC bars)
- `legend-source-item` = added indicators/studies (Screener V2) — use this for indicator access

---

## Key Reference Files

| File | Purpose |
|------|---------|
| `tte/main.py` | Entry point (orchestrator, alert creation loop, auto-retry) |
| `tte/browser/tradingview.py` | Browser automation (layout, indicator, alert creation, `is_no_error`) |
| `tte/browser/chart.py` | Chart navigation (timeframe collapsible sections, symbol search) |
| `tte/snapshot_worker.py` | Chart snapshot polling & browser orchestration |
| `tte/config.py` | Config dataclass (`recalc_wait=2.0`, `headless=true`) |
| `combo_settings.yaml` | Settings (batch_size=2, 45 seconds, screener "Screener V2", snapshot.batch_size=10) |
| `.env` | `COMBO_WEBHOOK_URL=https://stockbuddy.co/api/tte/combo`, `STOCK_BUDDY_API_URL=https://stockbuddy.co/api/tte` |

---

## Verified Patterns (Updated 2026-04-09)

### Layout Toolbar Selectors
```
Save button:        button#header-toolbar-save-load
Layout name:        button#header-toolbar-save-load .text (use .text.strip())
Dropdown trigger:   button[data-name="save-load-menu"]
Dropdown menu:      div[data-qa-id="menu-inner"]
Layout items:       *[@data-qa-id="save-load-menu-item-recent"]
  Current layout:   <div> element (no href)
  Other layouts:    <a href="/chart/{id}" target="_blank"> element
Layout name span:   .//span[normalize-space(text())="LayoutName"]
```

### Timeframe Toolbar Selectors
```
Quick-access btns:  #header-toolbar-intervals button
Active timeframe:   #header-toolbar-intervals button[aria-checked="true"]
Dropdown chevron:   #header-toolbar-intervals > button[aria-label="Chart interval"]
Dropdown menu:      div[data-qa-id="menu-inner"]
Section headers:    button[data-qa-id="ui-lib-title-list-item"][aria-label="Seconds"]
  Expanded:         aria-expanded="true"
  Collapsed:        aria-expanded="false"
Timeframe items:    div[data-qa-id="interval-menu-item"][aria-label="45 seconds"]
  Selected:         aria-selected="true"
```

### Legend/Indicator Selectors
```
Legend items:       div[data-qa-id="legend-source-item"]   (indicators/studies)
Chart series:       div[data-qa-id="legend-series-item"]   (main chart bars)
Indicator title:    [data-qa-id*="legend-source-title"]
Settings button:    button[data-qa-id="legend-settings-action"]
Statuses wrapper:   div[data-qa-id="legend-statuses-wrapper"]
Error detection:    [data-qa-id="legend-statuses-wrapper"] [class*="dataProblem"]
```

### Alert Dialog Selectors (VERIFIED WORKING 2026-04-07)
```
+ button:           div[data-name="set-alert-button"]
Main dialog:        div[data-qa-id="alerts-create-edit-dialog"]
Condition dropdown: [data-qa-id*="main-series-select"]
Operator dropdown:  button[data-qa-id="operator-dropdown"]
Webhook nav button: button[data-qa-id="alert-notifications-button"]
Submit/Create:      button[data-qa-id="submit"]
Cancel:             button[name="cancel"][data-qa-id="cancel"]
Close (X):          button[data-qa-id="close"]

Notifications sub-dialog:
  Dialog container: div[data-qa-id="alerts-notifications-edit-dialog"]
  Back button:      button[data-qa-id="back"]
  Webhook checkbox: label[data-qa-id="webhook"] input[type="checkbox"]
  Webhook URL input: input#webhook-url
  Apply button:     button[data-qa-id="submit"] (inside sub-dialog context)
```

### Alerts Settings Dropdown
```
3-dots button:      div[data-name="alerts-settings-button"]
Menu items (text):  XPath: //div[@data-qa-id="menu-inner"]/div[.//span[normalize-space(text())="Label"]]
Confirm dialog:     div[data-name="confirm-dialog"]
Confirm yes:        button[name="yes"]
```

---

## Test Commands

```bash
# TTE
pipenv run python combo_main.py --fresh             # Delete alerts & recreate (~340 alerts)
pipenv run python combo_main.py --setup-only         # Setup only
pipenv run python combo_main.py --maintain-only      # Maintenance + snapshots (headless)
pipenv run python combo_main.py --validate           # Validate config
pipenv run python combo_main.py --symbols A,B,C      # Create alerts for specific symbols only
dist/TTE.exe                                         # GUI (requires rebuild after code changes)

# Verification
pipenv run pyright tte/                              # Type checking
pipenv run ruff check tte/                           # Linting
python -c "from tte.data.symbols import get_symbols; s=get_symbols(); print(sum(len(v) for v in s.values()))"
```

## Remaining Tasks

1. [ ] Delete debug PNG files (`debug_headless.png`, `debug_tte_profile.png`, `debug_flow.png`, `debug_get_indicator_fail.png`)
2. [ ] Monitor alerts — verify webhooks fire to Stock Buddy after next signal cycle
3. [ ] Fix Chrome/ChromeDriver version mismatch (Chrome 146, cached driver 145) when convenient
