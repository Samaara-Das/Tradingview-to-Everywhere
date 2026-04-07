# Task Context Tracker

**Last Updated**: 2026-04-07 (continued session)
**Current Task**: Run `--fresh` via TTE.exe to recreate all 340 alerts (Task 25 — unblocked)
**Active Branch**: `main` (uncommitted changes in `tte/browser/chart.py`, `tte/browser/tradingview.py`, `tte/main.py`)
**Latest Commit**: `c0d7695` — Merge pull request #23

---

## Task Progress Summary

| # | Task | Status |
|---|------|--------|
| 1-16 | Previous tasks (alerts, signals, snapshots, cleanup) | **done** |
| 17 | Fix TradingView layout selector bug (dynamic class names changed) | **done** (2026-04-06) |
| 18 | Update webhook URL to new Stock Buddy deployment | **done** (2026-04-06) |
| 19 | Update webhook URL to stockbuddy.co custom domain | **done** (2026-04-07) |
| 20 | Fix delete_all_alerts dropdown bug (index-based to XPath text matching) | **done** (2026-04-07) |
| 21 | Auto-retry failed alert batches after creation | **done** (2026-04-07) |
| 22 | Fix layout dropdown selector (scoped XPath + navigate via href) | **done** (2026-04-07) |
| 23 | Fix timeframe dropdown (collapsible sections redesign) | **done** (2026-04-07) |
| 24 | Fix alert creation hang (two root causes found and fixed) | **done** (2026-04-07) |
| 25 | Run `--fresh` via TTE.exe to recreate 340 alerts | **READY** — unblocked |

---

## Session History

### Session: 2026-04-07 (TradingView UI Redesign Fixes — ALL FIXED)

**User request**: Run `--fresh` to recreate all 340 alerts with new `stockbuddy.co` webhook URL. Hit multiple TradingView UI breakages.

#### Bug 1 — Layout dropdown XPath too broad (FIXED)

**Root cause**: XPath `//*[normalize-space(text())="Screener"]` matched the chart legend instead of the dropdown item.
**Fix** (`tte/browser/tradingview.py` `change_layout()`):
1. Scoped XPath to `data-qa-id="save-load-menu-item-recent"` items only
2. Non-current layouts are `<a target="_blank">` links — extract `href` and navigate via `driver.get(url)` instead of clicking

#### Bug 2 — Timeframe dropdown completely redesigned (FIXED)

**Root cause**: Dropdown changed from flat list to collapsible sections (Ticks/Seconds/Minutes/Hours/Days/Ranges).
**Fix** (`tte/browser/chart.py`): Three new helpers (`_get_timeframe_section()`, `_open_timeframe_dropdown()`, `_expand_timeframe_section()`) + rewrote `change_tframe()` and `force_change_tframe()`.

#### Bug 3 — Legend items not found (TRANSIENT)

**Root cause**: Corrupted Chrome profile state from force-killed runs. Resolved by killing all Chrome processes and running fresh.
- The selector `data-qa-id="legend-source-item"` IS STILL VALID
- Added debug logging to `get_indicator()` (screenshot + page_source check on failure)

#### Bug 4 — Alert creation hang (FIXED — two root causes)

**Root Cause 1: Screener V2 indicator missing from chart layout**
- Previous force-kills of Chrome corrupted the TradingView layout state
- The Screener V2 indicator was completely removed from the "Screener" layout at URL 3Bcyo3gz
- `_safe_indicator_access()` timed out repeatedly (15s x retries) creating the appearance of an infinite hang
- **Fix**: User manually re-added the indicator to the chart and saved the layout

**Root Cause 2: TradingView alert dialog redesign — no more tabs**
- OLD: Single alert dialog with Settings tab + Notifications tab
- NEW: Main dialog with a "Webhook >" button that opens a separate notifications sub-dialog
- The old code tried to click `button[id="alert-dialog-tabs__notifications"]` which no longer exists
- This caused `create_webhook_alert()` to fail, which triggered `reupload_indicator()` (removes indicator from chart)

**Fix** (`tradingview.py` `create_webhook_alert()`):
1. Click `button[data-qa-id="alert-notifications-button"]` to navigate to notifications sub-dialog
2. Wait for `div[data-qa-id="alerts-notifications-edit-dialog"]`
3. Find webhook checkbox via `label[data-qa-id="webhook"]` then `input[type="checkbox"]`
4. Fill `input#webhook-url` with webhook URL
5. Click "Apply" (`button[data-qa-id="submit"]` inside sub-dialog) to return to main dialog
6. Click "Create" (`button[data-qa-id="submit"]` in main dialog) to submit

**Other fixes applied:**
- `_validate_alert_condition()` — Added contains-match selector `[data-qa-id*="main-series-select"]` + text-based fallback
- `is_no_error()` — Replaced dynamic class selectors (`statusesWrapper-l31H9iuA`, `dataProblemLow-Lgtz1OtS`) with stable `[data-qa-id="legend-statuses-wrapper"] [class*="dataProblem"]`
- Diagnostic logging added to `main.py` alert creation loop and `create_webhook_alert()`

**False lead investigated and reverted:**
- Initially renamed `legend-source-item` to `legend-series-item` thinking TradingView renamed it
- Actually: `legend-series-item` = main chart series, `legend-source-item` = added indicators/studies (BOTH exist, different purposes)
- Reverted all legend-source-item changes

#### Verified Working (15:49:16)
- Full alert creation flow: change_symbol -> change_settings -> is_no_error -> click indicator -> create_webhook_alert -> SUCCESS
- 1 test alert created for FX:NZDCHF, FX:NZDJPY with stockbuddy.co webhook in 19.7s

---

## Uncommitted Changes (3 files)

### `tte/browser/chart.py` (+136 -86 lines)
- New: `_get_timeframe_section()`, `_open_timeframe_dropdown()`, `_expand_timeframe_section()`
- Rewritten: `change_tframe()` — collapsible section support
- Rewritten: `force_change_tframe()` — uses shared helpers
- Removed: All dynamic class name selectors (`menuItem-RmqZNwwp`, `label-jFqVJoPk`)

### `tte/browser/tradingview.py` (major changes)
- Rewritten: `change_layout()` — scoped XPath, navigate via href for `<a>` links
- Rewritten: `current_chart_tframe()` — uses `button[aria-checked="true"]`
- Rewritten: `create_webhook_alert()` — new two-dialog flow (main + notifications sub-dialog)
- Fixed: `_validate_alert_condition()` — contains-match selector + text-based fallback
- Fixed: `is_no_error()` — stable `data-qa-id` selectors instead of dynamic class names
- Added: Debug logging in `get_indicator()` and `create_webhook_alert()`

### `tte/main.py`
- Added: Diagnostic logging in alert creation loop

---

## Important Decisions Made

### Layout Navigation via href (2026-04-07)
Non-current layouts in TradingView's dropdown are `<a target="_blank">` links. Clicking them via Selenium opens a new tab. **Solution**: Extract `href` from the `<a>` element and navigate via `driver.get(url)`. This reloads the page with the correct layout.

### Timeframe Dropdown Section Expansion (2026-04-07)
TradingView now groups timeframes into collapsible sections. TTE must: (1) identify the section from the timeframe label, (2) expand it if `aria-expanded="false"`, (3) then find the item.

### Alert Dialog Two-Step Flow (2026-04-07)
TradingView removed the tabbed alert dialog. Webhook settings are now behind a "Webhook >" button that opens a separate sub-dialog. TTE must: (1) configure alert conditions in main dialog, (2) click webhook button, (3) configure webhook in sub-dialog, (4) apply sub-dialog, (5) create alert in main dialog.

### legend-source-item vs legend-series-item (2026-04-07)
Both selectors exist in TradingView with different purposes:
- `legend-series-item` = main chart series (e.g., OHLC bars)
- `legend-source-item` = added indicators/studies (e.g., Screener V2)
TTE must continue using `legend-source-item` for indicator access.

### Chrome Version Mismatch (2026-04-07)
Chrome auto-updated to **146.0.7680.178** but cached chromedriver is **145.0.7632.117**. The `_find_chromedriver()` function falls back to the best-available cached driver. This mismatch did NOT prevent Chrome from launching. Should be fixed eventually.

---

## Key Reference Files

| File | Purpose |
|------|---------|
| `tte/main.py` | Entry point (orchestrator, alert creation loop lines 160-330, auto-retry) |
| `tte/browser/tradingview.py` | Browser automation (layout switch, indicator access, alert creation, `is_no_error`) |
| `tte/browser/chart.py` | Chart navigation (timeframe with collapsible sections, symbol search) |
| `tte/config.py` | Config dataclass (`recalc_wait=2.0`, `headless=true`) |
| `combo_settings.yaml` | Settings (batch_size=2, 45 seconds, screener "Screener V2") |
| `.env` | `COMBO_WEBHOOK_URL=https://stockbuddy.co/api/tte/combo` |

---

## Verified Patterns (Updated 2026-04-07)

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
Quick-access btns:  #header-toolbar-intervals button (5m, 15m, 1h, 4h, D, W, 45s)
Active timeframe:   #header-toolbar-intervals button[aria-checked="true"]
Dropdown chevron:   #header-toolbar-intervals > button[aria-label="Chart interval"]
Dropdown menu:      div[data-qa-id="menu-inner"]
Section headers:    button[data-qa-id="ui-lib-title-list-item"][aria-label="Seconds"]
  Expanded:         aria-expanded="true"
  Collapsed:        aria-expanded="false", children aria-hidden="true"
Timeframe items:    div[data-qa-id="interval-menu-item"][aria-label="45 seconds"]
  Selected:         aria-selected="true"
  Value attr:       data-value="45S"
```

### Legend/Indicator Selectors
```
Legend items:       div[data-qa-id="legend-source-item"]   (indicators/studies)
Chart series:       div[data-qa-id="legend-series-item"]   (main chart bars — NOT for indicators)
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
  Dialog container:  div[data-qa-id="alerts-notifications-edit-dialog"]
  Back button:       button[data-qa-id="back"]
  Webhook checkbox:  label[data-qa-id="webhook"] input[type="checkbox"]
  Webhook URL input: input#webhook-url
  Apply button:      button[data-qa-id="submit"] (inside sub-dialog context)
```

### Alerts Settings Dropdown
```
3-dots button:      div[data-name="alerts-settings-button"]
Menu items (text):  XPath: //div[@data-qa-id="menu-inner"]/div[.//span[normalize-space(text())="Label"]]
Confirm dialog:     div[data-name="confirm-dialog"]
Confirm yes:        button[name="yes"]
```

---

## Debug Files Created This Session

- `debug_headless.png` — Screenshot of headless Chrome with default profile
- `debug_tte_profile.png` — Screenshot of headless Chrome with TTE profile
- `debug_flow.png` — Screenshot of TTE flow replication test
- `debug_get_indicator_fail.png` — Saved by debug logging when get_indicator fails

**Clean up**: Delete these debug PNG files after confirming full `--fresh` run works.

---

## Test Commands

```bash
# TTE
pipenv run python combo_main.py --fresh            # Delete alerts & recreate (~340 alerts)
pipenv run python combo_main.py --setup-only        # Setup only (stop after browser init)
pipenv run python combo_main.py --maintain-only     # Maintenance + snapshots (headless)
pipenv run python combo_main.py --validate          # Validate config
dist/TTE.exe                                        # GUI (requires rebuild after code changes)

# Verification
pipenv run pyright tte/                             # Type checking
pipenv run ruff check tte/                          # Linting
```

## Remaining Tasks (Priority Order)

1. [ ] **Run `--fresh` via TTE.exe** to recreate all 340 alerts with stockbuddy.co webhook (Task 25)
2. [ ] Remove diagnostic logging from `main.py` and `tradingview.py` after confirming full run works
3. [ ] Delete debug PNG files
4. [ ] Commit & PR all selector fixes (layout, timeframe, alert dialog, is_no_error)
5. [ ] Rebuild `dist/TTE.exe` after final cleanup
6. [ ] Restart maintenance loop
7. [ ] Verify alerts fire — check Stock Buddy webhook logs
