# TTE Selenium Automation Documentation

This document provides comprehensive documentation of all Selenium automation patterns used in the TradingView to Everywhere (TTE) project.

**Last Updated**: 2026-01-30

---

## Table of Contents

1. [High-Level Workflows](#high-level-workflows)
2. [File Overview](#file-overview)
3. [Critical Functions Reference](#critical-functions-reference)
4. [Selector Inventory](#selector-inventory)
5. [Wait Strategies](#wait-strategies)
6. [Edge Cases & Gotchas](#edge-cases--gotchas)
7. [Error Handling Patterns](#error-handling-patterns)
8. [Implementation Comparison](#implementation-comparison)
9. [Reuse Recommendations](#reuse-recommendations)

---

## High-Level Workflows

### Legacy Mode Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LEGACY MODE WORKFLOW                               │
│                                                                             │
│  1. SETUP PHASE (setup_tv)                                                  │
│     ├─► sign_in() → TradingView login if needed                            │
│     ├─► open_page() → Navigate to chart                                    │
│     ├─► change_layout() → Switch to "Screener" layout                      │
│     ├─► save_layout() → Save current layout                                │
│     ├─► change_tframe() → Set to 1H timeframe                              │
│     ├─► open_alerts_sidebar() → Open alerts panel                          │
│     ├─► delete_all_alerts() → Clear existing alerts (if START_FRESH)       │
│     ├─► get_indicator() → Find screener & drawer indicators                │
│     └─► indicator_visibility() → Hide screener, show drawer                │
│                                                                             │
│  2. ALERT CREATION PHASE (set_bulk_alerts)                                  │
│     FOR each symbol_sublist:                                                │
│     ├─► change_symbol() → Navigate to symbol chart                         │
│     ├─► change_settings() → Fill screener inputs                           │
│     ├─► sleep(3) → Wait for indicator recalculation                        │
│     └─► set_alerts() → Create alert for screener                           │
│                                                                             │
│  3. MONITORING PHASE (post_entries)                                         │
│     LOOP:                                                                   │
│     ├─► open_log_tab() → Switch to alert logs                              │
│     ├─► get_alert() → Read alert message                                   │
│     ├─► remove_alert() → Delete processed alert                            │
│     ├─► change_symbol() → Navigate to entry symbol                         │
│     ├─► change_indicator_settings() → Set Trade Drawer values              │
│     ├─► save_chart_img() → Capture screenshot                              │
│     └─► send_everywhere() → Distribute to Discord/DB                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tiered Mode Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TIERED MODE WORKFLOW                               │
│                                                                             │
│  1. INITIALIZATION                                                          │
│     ├─► get_driver() → Initialize Chrome with TTE profile                  │
│     └─► navigate_to_chart() → Load NWE/OBDIV screener chart                │
│                                                                             │
│  2. NWE BATCH ROTATION                                                      │
│     ├─► navigate_to_chart(NWE_CHART_URL)                                   │
│     ├─► open_indicator_settings("TTE NWE Screener")                        │
│     ├─► set_symbol_inputs(batch_symbols)                                   │
│     └─► click_ok_button() → Wait 10s for recalculation                     │
│                                                                             │
│  3. OBDIV PROCESSING                                                        │
│     ├─► navigate_to_chart(OBDIV_CHART_URL)                                 │
│     ├─► open_indicator_settings("TTE OBDIV Screener")                      │
│     ├─► set_symbol_inputs(hot_symbols)                                     │
│     └─► click_ok_button()                                                  │
│                                                                             │
│  4. WEBHOOK ALERT CREATION (create_webhook_alert)                           │
│     ├─► Click SET_ALERT_BUTTON (+)                                         │
│     ├─► Wait for ALERT_DIALOG                                              │
│     ├─► Select indicator from CONDITION_DROPDOWN                           │
│     ├─► Click NOTIFICATIONS_TAB                                            │
│     ├─► Enable WEBHOOK_CHECKBOX                                            │
│     ├─► Enter webhook URL in WEBHOOK_URL_INPUT                             │
│     └─► Click SUBMIT_BUTTON (Create)                                       │
│                                                                             │
│  5. SCREENSHOT CAPTURE                                                      │
│     ├─► Navigate to symbol chart                                           │
│     ├─► capture_chart_screenshot() → Alt+S for native snapshot             │
│     └─► Fallback: driver.save_screenshot() for local file                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## File Overview

| File | Purpose | Lines | Key Patterns |
|------|---------|-------|--------------|
| `selenium_manager.py` | Tiered orchestrator browser automation | ~987 | Webhook alerts, symbol input, retry decorator |
| `open_tv.py` | Legacy browser automation | ~1347 | Alert scraping, layout management, indicator visibility |
| `handle_alerts.py` | Alert processing & distribution | ~485 | Alert log reading, message parsing, multi-platform posting |
| `open_entry_chart.py` | Chart manipulation | ~424 | Symbol/timeframe changes, indicator settings, screenshots |
| `resources/utils.py` | Utility functions | ~159 | Tab switching, confirmation dialogs |

---

## Critical Functions Reference

### Browser Initialization

| Function | File | Line | Purpose |
|----------|------|------|---------|
| `get_driver()` | selenium_manager.py | 148 | Initialize Chrome with TTE profile (tiered mode) |
| `Browser.__init__()` | open_tv.py | 64 | Initialize Chrome with TTE profile (legacy mode) |

**Key Configuration:**
```python
# Chrome Options (both files use identical settings)
chrome_options.add_argument(f"--profile-directory={PROFILE}")
chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILES_PATH}/TTE")
chrome_options.add_argument("--remote-debugging-port=9224")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_experimental_option("detach", True)

# Chrome version detection via PowerShell
cmd = 'powershell -command "&{(Get-Item \'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\').VersionInfo.ProductVersion}"'
version = read_version_from_cmd(cmd, PATTERN["google-chrome"])
```

### Navigation Functions

| Function | File | Line | Purpose | Reusable? |
|----------|------|------|---------|-----------|
| `navigate_to_chart(url)` | selenium_manager.py | 289 | Navigate to chart with login check | YES |
| `open_page(url)` | open_tv.py | 108 | Simple page navigation | YES |
| `change_symbol(symbol)` | open_entry_chart.py | 207 | Change chart symbol via search | YES |
| `change_tframe(timeframe)` | open_entry_chart.py | 257 | Change chart timeframe | YES |
| `change_layout(name)` | open_tv.py | 399 | Switch TradingView layout | YES |

### Indicator Management

| Function | File | Line | Purpose | Reusable? |
|----------|------|------|---------|-----------|
| `open_indicator_settings(name)` | selenium_manager.py | 327 | Double-click to open settings | YES |
| `set_symbol_inputs(symbols)` | selenium_manager.py | 382 | Set symbol input fields | YES |
| `click_ok_button()` | selenium_manager.py | 437 | Submit indicator settings | YES |
| `get_indicator(shorttitle)` | open_tv.py | 1256 | Find indicator by shorttitle | YES |
| `change_settings(symbols)` | open_tv.py | 485 | Full settings change for legacy screener | PARTIAL |
| `change_indicator_settings()` | open_entry_chart.py | 23 | Change Trade Drawer settings | YES |
| `indicator_visibility(visible, shorttitle)` | open_tv.py | 968 | Toggle indicator visibility | YES |
| `is_no_error(shorttitle)` | open_tv.py | 1051 | Check indicator for errors | YES |
| `reupload_indicator()` | open_tv.py | 1160 | Remove and re-add indicator | MAYBE |

### Alert Functions

| Function | File | Line | Purpose | Reusable? |
|----------|------|------|---------|-----------|
| `create_webhook_alert()` | selenium_manager.py | 611 | Create alert with webhook | YES |
| `delete_all_alerts()` | selenium_manager.py | 812 | Delete all alerts (tiered) | YES |
| `delete_all_alerts()` | open_tv.py | 1084 | Delete all alerts (legacy) | YES |
| `click_create_alert(shorttitle)` | open_tv.py | 842 | Create indicator alert | PARTIAL |
| `set_alerts(symbols)` | open_tv.py | 791 | Create alert with error recovery | NO |
| `open_alerts_sidebar()` | open_tv.py | 719 | Open alerts panel | YES |

### Alert Reading Functions

| Function | File | Line | Purpose | Reusable? |
|----------|------|------|---------|-----------|
| `get_alert()` | handle_alerts.py | 345 | Get and remove alert from log | NO (legacy) |
| `get_alert_box_and_msg()` | handle_alerts.py | 426 | Get alert element and message | NO (legacy) |
| `remove_alert(alert_box)` | handle_alerts.py | 461 | Remove alert from log | NO (legacy) |
| `restart_inactive_alerts()` | handle_alerts.py | 280 | Restart stopped alerts | YES |

### Screenshot Functions

| Function | File | Line | Purpose | Reusable? |
|----------|------|------|---------|-----------|
| `capture_chart_screenshot()` | selenium_manager.py | 922 | Alt+S native snapshot with fallback | YES |
| `save_chart_img()` | open_entry_chart.py | 334 | Camera icon → open in new tab | YES |

### Utility Functions

| Function | File | Line | Purpose | Reusable? |
|----------|------|------|---------|-----------|
| `open_alert_tab(driver)` | resources/utils.py | 74 | Switch to Alerts tab | YES |
| `open_log_tab(driver)` | resources/utils.py | 111 | Switch to Logs tab | YES |
| `click_yes_in_confirm_popup(driver)` | resources/utils.py | 141 | Confirm dialog handler | YES |

---

## Selector Inventory

### Stability Legend
- **STABLE**: Uses `data-*` attributes (unlikely to change)
- **MODERATE**: Uses semantic IDs or names
- **FRAGILE**: Uses class names (may change with UI updates)
- **VERY FRAGILE**: Uses XPath with position indices

### Alert Dialog Selectors

| Selector | Stability | Location | Purpose |
|----------|-----------|----------|---------|
| `div[data-name="set-alert-button"]` | STABLE | selenium_manager.py:90, open_tv.py:851 | "+" button to create alert |
| `div[data-qa-id="alerts-create-edit-dialog"]` | STABLE | selenium_manager.py:91 | Alert creation dialog |
| `div[data-name="alerts-create-edit-dialog"]` | STABLE | open_tv.py:860 | Alert creation dialog (alternative) |
| `input[id="alert-name"]` | STABLE | selenium_manager.py:92 | Alert name input |
| `div[data-name="error-hint"]` | STABLE | selenium_manager.py:93 | Error message in dialog |
| `span[data-qa-id="ui-kit-disclosure-control main-series-select"]` | STABLE | selenium_manager.py:96 | Condition dropdown |
| `div[data-qa-id="ui-kit-disclosure-popup popup-menu-container main-series-select"]` | STABLE | selenium_manager.py:97 | Dropdown menu |
| `div[role="option"]` | STABLE | selenium_manager.py:98 | Dropdown menu items |
| `#alert-dialog-tabs__settings` | MODERATE | selenium_manager.py:101 | Settings tab |
| `#alert-dialog-tabs__notifications` | MODERATE | selenium_manager.py:102 | Notifications tab |
| `#alert-dialog-tabs__message` | MODERATE | selenium_manager.py:103 | Message tab |
| `input[data-qa-id="webhook"]` | STABLE | selenium_manager.py:106 | Webhook checkbox |
| `#webhook-url` | MODERATE | selenium_manager.py:107 | Webhook URL input |
| `button[data-qa-id="submit"]` | STABLE | selenium_manager.py:115 | Create/Submit button |
| `button[data-name="submit"]` | STABLE | open_tv.py:922 | Submit button (alternative) |
| `button[data-name="close"]` | STABLE | selenium_manager.py:118, open_tv.py:905 | Close button |
| `button[data-name="cancel"]` | STABLE | open_tv.py:946 | Cancel button |

### Indicator/Legend Selectors

| Selector | Stability | Location | Purpose |
|----------|-----------|----------|---------|
| `div[data-name="legend-source-item"]` | STABLE | selenium_manager.py:85, open_tv.py:1228 | Indicator item in legend |
| `div[class*="title"]` | FRAGILE | selenium_manager.py:86 | Indicator title (flexible) |
| `div[class="title-l31H9iuA"]` | FRAGILE | open_tv.py:1234 | Indicator title (exact class) |
| `[data-dialog-name='indicatorSettings']` | STABLE | selenium_manager.py:87 | Indicator settings dialog |
| `.tv-dialog--indicator-properties` | FRAGILE | selenium_manager.py:87 | Settings dialog (fallback) |
| `div[data-name="indicator-properties-dialog"]` | STABLE | open_entry_chart.py:47 | Indicator properties dialog |
| `button[data-name="legend-settings-action"]` | STABLE | open_tv.py:502 | Settings button in legend |
| `button[data-name="legend-show-hide-action"]` | STABLE | open_tv.py:983 | Eye button for visibility |
| `div[data-name="legend-delete-action"]` | STABLE | open_tv.py:1174 | Delete button in legend |
| `.statusItem-Lgtz1OtS.small-Lgtz1OtS.dataProblemLow-Lgtz1OtS` | VERY FRAGILE | open_tv.py:1068 | Error indicator status |

### Settings Dialog Selectors

| Selector | Stability | Location | Purpose |
|----------|-----------|----------|---------|
| `.content-tBgV1m0B` | FRAGILE | open_tv.py:506 | Settings content area |
| `.inlineRow-tBgV1m0B div[data-name="edit-button"]` | FRAGILE | open_tv.py:509 | Symbol edit buttons |
| `div[class="cell-tBgV1m0B first-tBgV1m0B"]` | FRAGILE | open_tv.py:514 | Input label cells |
| `.cell-tBgV1m0B input` | FRAGILE | open_entry_chart.py:69 | Input fields in settings |
| `div[class="tabs-vwgPOHG8"] button[id="inputs"]` | FRAGILE | open_entry_chart.py:65 | Inputs tab button |
| `button[name="submit"]` | MODERATE | open_tv.py:542 | Submit button |

### Alerts Sidebar Selectors

| Selector | Stability | Location | Purpose |
|----------|-----------|----------|---------|
| `div[data-name="right-toolbar"] button[aria-label="Alerts"]` | STABLE | open_tv.py:726 | Alerts sidebar button |
| `div[data-name="alerts-settings-button"]` | STABLE | open_tv.py:1095 | Alert settings (3 dots) |
| `div[data-name="menu-inner"]` | STABLE | open_tv.py:1100 | Dropdown menu |
| `div.item-jFqVJoPk` | FRAGILE | open_tv.py:1086 | Dropdown menu items |
| `div.list-G90Hl2iS div.itemBody-ucBqatk5` | FRAGILE | open_tv.py:1112 | Alert items in list |
| `div[data-name="confirm-dialog"]` | STABLE | handle_alerts.py:330 | Confirmation popup |
| `button[name="yes"]` | MODERATE | handle_alerts.py:334 | Yes button |
| `button[data-name="confirm-yes"]` | STABLE | selenium_manager.py:848 | Yes button (alternative) |

### Alert Log Selectors

| Selector | Stability | Location | Purpose |
|----------|-----------|----------|---------|
| `div[data-name="alert-log-item"]` | STABLE | handle_alerts.py:261 | Alert log item |
| `div[class="name-PQUvhamm"]` | FRAGILE | handle_alerts.py:404 | Alert name in log |
| `div[class="message-PQUvhamm"]` | FRAGILE | handle_alerts.py:406 | Alert message in log |
| `span[class="attribute-PQUvhamm ticker-PQUvhamm"]` | FRAGILE | handle_alerts.py:410 | Symbol attribute |
| `div[data-name="event-delete-button"]` | STABLE | handle_alerts.py:467 | Delete button on log item |

### Tab Navigation Selectors

| Selector | Stability | Location | Purpose |
|----------|-----------|----------|---------|
| `button[data-name="light-tab-0"]` | STABLE | resources/utils.py:52 | Alerts tab |
| `button[data-name="light-tab-1"]` | STABLE | resources/utils.py:24 | Logs tab |
| `div[id="AlertsHeaderTabs"]` | MODERATE | resources/utils.py:104 | Tab container |
| `div[class="widgetbar-page active"]` | FRAGILE | handle_alerts.py:401 | Active sidebar page |

### Header/Toolbar Selectors

| Selector | Stability | Location | Purpose |
|----------|-----------|----------|---------|
| `button[id="header-toolbar-symbol-search"]` | STABLE | open_entry_chart.py:215 | Symbol search button |
| `//*[@id="header-toolbar-intervals"]/button` | VERY FRAGILE | open_entry_chart.py:263 | Timeframe button |
| `//*[@id="header-toolbar-save-load"]` | VERY FRAGILE | open_tv.py:405 | Layout save/load button |
| `div[id="header-toolbar-chart-styles"] button` | MODERATE | open_tv.py:756 | Candle type button |
| `div[id="header-toolbar-indicators"]` | MODERATE | open_tv.py:1183 | Indicators toolbar |
| `button[data-name="show-favorite-indicators"]` | STABLE | open_tv.py:1185 | Favorites dropdown |

### Screenshot Selectors

| Selector | Stability | Location | Purpose |
|----------|-----------|----------|---------|
| `button[@aria-label='Take a snapshot']` | STABLE | open_entry_chart.py:347 | Camera button |
| `div[@id='header-toolbar-screenshot']` | MODERATE | open_entry_chart.py:348 | Screenshot toolbar |
| `img.tv-snapshot-image` | FRAGILE | open_entry_chart.py:365 | Snapshot image element |
| `input[type='text'][readonly]` | FRAGILE | selenium_manager.py:125 | Snapshot URL input |

### Miscellaneous Selectors

| Selector | Stability | Location | Purpose |
|----------|-----------|----------|---------|
| `.chart-container` | FRAGILE | selenium_manager.py:122 | Chart container |
| `a[data-main-menu-root-track-id="products"]` | STABLE | open_tv.py:127 | Products menu (login check) |
| `button[data-overflow-tooltip-text="Sign in"]` | STABLE | open_tv.py:164 | Sign in button |
| `.text-yyMUOAN9` | VERY FRAGILE | open_tv.py:409 | Layout name text |
| `.layoutTitle-yyMUOAN9` | VERY FRAGILE | open_tv.py:436 | Layout title in dropdown |
| `div[class="dropdown-S_1OCXUK"]` | FRAGILE | open_entry_chart.py:274 | Timeframe dropdown |

---

## Wait Strategies

### Implicit Wait
- **Default**: 10 seconds (configured in `get_driver()`)
- **Usage**: Fallback for all `find_element` calls
- **Location**: `selenium_manager.py:199`

### Explicit Waits

| Type | Timeout | Usage | Example |
|------|---------|-------|---------|
| `presence_of_element_located` | 10-15s | Wait for element in DOM | Dialog appearance |
| `visibility_of_element_located` | 5s | Wait for element visible | Popup display |
| `element_to_be_clickable` | 10-15s | Wait for clickable state | Buttons |
| `presence_of_all_elements_located` | 10-15s | Wait for multiple elements | Dropdown items |
| `text_to_be_present_in_element` | 5s | Wait for text change | Symbol confirmation |
| `invisibility_of_element_located` | 5s | Wait for element to disappear | Dialog close |

### Fixed Delays

| Delay | Purpose | Location |
|-------|---------|----------|
| `sleep(0.3-0.5)` | UI animation completion | Throughout |
| `sleep(1)` | Dialog animation | selenium_manager.py:376 |
| `sleep(1.5)` | Chart symbol load | open_entry_chart.py:244 |
| `sleep(2)` | General UI stabilization | Multiple |
| `sleep(3)` | Symbol sublist processing | open_tv.py:381 |
| `sleep(5)` | Alert creation completion | open_tv.py:392 |
| `sleep(10)` | Indicator recalculation after symbol change | selenium_manager.py:481 |
| `sleep(15)` (timeout loop) | Indicator load verification | open_entry_chart.py:100 |

---

## Edge Cases & Gotchas

### 1. Print Statements Required in `reupload_indicator()`

**Location**: `open_tv.py:1160-1254`

**Issue**: The `reupload_indicator()` function mysteriously fails without print statements.

**Comment from code**:
> "Don't remove the print statements. It seems like the code will only run with the print statements."

**Recommendation**: Keep print statements; this may be a timing/execution order issue.

### 2. Use Ctrl+A/Delete Instead of `.clear()`

**Location**: Multiple files

**Issue**: The Selenium `.clear()` method doesn't work reliably on TradingView inputs.

**Pattern**:
```python
# WRONG
input_field.clear()
input_field.send_keys(value)

# CORRECT
ActionChains(driver).key_down(Keys.CONTROL, input_field).send_keys("a").perform()
input_field.send_keys(Keys.DELETE)
input_field.send_keys(value)
```

**Locations**:
- `selenium_manager.py:736-739`
- `open_entry_chart.py:85-89`
- `open_entry_chart.py:228-232`

### 3. ActionChains Required for Double-Click

**Location**: `selenium_manager.py:364-365`, `open_entry_chart.py:39-42`

**Issue**: Regular `.click()` doesn't open indicator settings; must use double-click.

**Pattern**:
```python
actions = ActionChains(driver)
actions.move_to_element(indicator_element).perform()
actions.double_click(indicator_element).perform()
```

### 4. 10-Second Wait After Symbol Change

**Location**: `selenium_manager.py:478-481`

**Issue**: Indicators need time to recalculate after symbol changes.

**Code**:
```python
if wait_for_recalc:
    # Wait 10 seconds for indicator to recalculate after symbol changes
    logger.info("Waiting 10 seconds for indicator to recalculate...")
    time.sleep(10)
```

### 5. Strip Exchange Prefix from Symbols

**Location**: `open_entry_chart.py:210-211`

**Issue**: Symbols may include exchange prefix (e.g., `OANDA:EURUSD`), but UI displays without it.

**Pattern**:
```python
no_exchange_symbol = symbol.split(":")[-1] if ":" in symbol else symbol
```

### 6. Window Handle Switching for Screenshots

**Location**: `open_entry_chart.py:362-378`

**Issue**: Snapshot opens in new tab; must switch handles and return.

**Pattern**:
```python
# Switch to new tab
driver.switch_to.window(driver.window_handles[-1])
# ... get data ...
# Close new tab
driver.close()
# Switch back
driver.switch_to.window(driver.window_handles[0])
```

### 7. Alert Dialog Popup May Not Appear

**Location**: `open_tv.py:858-878`

**Issue**: Alert creation popup may fail to show within timeout.

**Recovery Pattern**:
```python
try:
    popup = WebDriverWait(driver, 5).until(...)
except TimeoutException:
    driver.get(driver.current_url)  # Refresh (not .refresh() to avoid Chrome dialog)
    sleep(3)
    # Retry
```

### 8. Check `aria-pressed` for Toggle State

**Location**: `open_tv.py:730-731`

**Issue**: Sidebar buttons use `aria-pressed` attribute, not class or visibility.

**Pattern**:
```python
if alert_button.get_attribute("aria-pressed") == "false":
    alert_button.click()
```

### 9. Dropdown "isDisabled" Class Check

**Location**: `open_tv.py:1129, 1145`

**Issue**: Dropdown items may be disabled; check before clicking.

**Pattern**:
```python
if "isDisabled" in button.get_attribute("class"):
    # Skip - option is disabled
else:
    button.click()
```

### 10. Legend Item Visibility via "disabled" Class

**Location**: `open_tv.py:1038`

**Issue**: Hidden indicators have "disabled" in class attribute.

**Pattern**:
```python
status = "Hidden" if "disabled" in indicator.get_attribute("class") else "Shown"
```

---

## Error Handling Patterns

### StaleElementReferenceException Handling

**Location**: `handle_alerts.py:355-364`

**Pattern**: Retry with fresh element lookup.

```python
try:
    # Use element
except StaleElementReferenceException:
    logger.error("StaleElementReferenceException, trying again...")
    # Re-find element and retry
    element = driver.find_element(...)
    # Retry operation
```

### TimeoutException Handling

**Location**: Multiple files

**Pattern**: Return None/empty, log warning, continue.

```python
try:
    element = WebDriverWait(driver, 10).until(...)
except TimeoutException:
    logger.warning("Timeout waiting for element")
    return None  # or continue to next item
```

### Retry Decorator

**Location**: `selenium_manager.py:46-72`

**Pattern**: Exponential backoff with configurable retries.

```python
@retry_on_failure(max_retries=3, delay=2.0,
                  exceptions=(TimeoutException, StaleElementReferenceException))
def some_function():
    # Function that may fail
```

### Chrome Already Running Error

**Location**: `selenium_manager.py:212-223`

**Pattern**: Provide helpful error message with recovery steps.

```python
if "DevToolsActivePort" in error_msg or "session not created" in error_msg:
    raise SeleniumError(
        "Chrome driver initialization failed.\n\n"
        "Please:\n"
        "  1. Close ALL Chrome windows completely\n"
        "  2. Check Task Manager and end any chrome.exe processes\n"
        "  3. Try again"
    )
```

### Login Required Detection

**Location**: `selenium_manager.py:252-287`

**Pattern**: Check for login indicators and fail gracefully.

```python
def _check_login_required(self) -> bool:
    login_indicators = [
        "//button[contains(text(), 'Sign in')]",
        "//a[contains(@href, '/signin')]",
    ]
    for indicator in login_indicators:
        try:
            if driver.find_element(By.XPATH, indicator).is_displayed():
                return True
        except NoSuchElementException:
            continue
    return False
```

### Alert Dialog Cleanup

**Location**: `selenium_manager.py:791-810`

**Pattern**: Always close dialog on error.

```python
def _close_alert_dialog(self, dialog):
    try:
        close_selectors = [CLOSE_BUTTON, CANCEL_BUTTON]
        for selector in close_selectors:
            try:
                btn = dialog.find_element(By.CSS_SELECTOR, selector)
                if btn.is_displayed():
                    btn.click()
                    return
            except NoSuchElementException:
                continue
        # Fallback: press Escape
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
    except Exception:
        pass
```

---

## Implementation Comparison

### delete_all_alerts() Comparison

| Aspect | selenium_manager.py | open_tv.py |
|--------|---------------------|------------|
| **Approach** | Menu → "Delete all alerts" | Stop all → Delete inactive |
| **Steps** | 1. Click settings → Find delete all | 1. Open dropdown → Stop all → Confirm → Delete inactive → Confirm |
| **Error Handling** | Basic timeout handling | Comprehensive with retry |
| **Confirmation** | Multiple button selectors | Yes/No dialog handling |
| **Lines** | 812-872 (60 lines) | 1084-1158 (74 lines) |

**Recommendation**: Use `selenium_manager.py` approach for simplicity; use `open_tv.py` for reliability.

### Indicator Settings Comparison

| Aspect | selenium_manager.py | open_tv.py |
|--------|---------------------|------------|
| **Open Settings** | Double-click legend item | Click item → Click settings button |
| **Find Inputs** | Heuristic (placeholder, value contains `:`) | CSS selectors for known structure |
| **Set Values** | Simple clear + send_keys | Ctrl+A → Delete → send_keys |
| **Wait for Recalc** | 10 second fixed delay | Loop checking "Loading" class |

**Recommendation**:
- Use `selenium_manager.py` `open_indicator_settings()` for opening
- Use Ctrl+A pattern from `open_tv.py` for input clearing
- Use loading check from `open_entry_chart.py` for verification

### Screenshot Comparison

| Aspect | selenium_manager.py | open_entry_chart.py |
|--------|---------------------|---------------------|
| **Method** | Alt+S keyboard shortcut | Click camera → Open in new tab |
| **Output** | Snapshot URL from dialog | PNG + TV link from new tab |
| **Fallback** | Local screenshot file | Close tab on error |
| **Complexity** | Medium | Higher (window switching) |

**Recommendation**: Use `selenium_manager.py` for URL-only needs; use `open_entry_chart.py` for dual URLs.

---

## Reuse Recommendations

### Recommended for Reuse (Copy As-Is)

| Function | File | Why |
|----------|------|-----|
| `navigate_to_chart()` | selenium_manager.py | Clean login check, configurable wait |
| `open_indicator_settings()` | selenium_manager.py | Reliable double-click pattern |
| `click_ok_button()` | selenium_manager.py | Multiple button selector fallbacks |
| `verify_indicator_loaded()` | selenium_manager.py | Error state detection |
| `change_symbol()` | open_entry_chart.py | Exchange prefix handling |
| `change_tframe()` | open_entry_chart.py | Conditional change |
| `open_alert_tab()` | resources/utils.py | Tab switching utility |
| `open_log_tab()` | resources/utils.py | Tab switching utility |
| `click_yes_in_confirm_popup()` | resources/utils.py | Dialog handling |

### Recommended with Modifications

| Function | File | Modifications Needed |
|----------|------|---------------------|
| `set_symbol_inputs()` | selenium_manager.py | Add Ctrl+A pattern for reliable input clearing |
| `delete_all_alerts()` | selenium_manager.py | Add confirmation dialog handling from open_tv.py |
| `save_chart_img()` | open_entry_chart.py | Add timeout and better error recovery |
| `reupload_indicator()` | open_tv.py | Investigate print statement dependency |

### Not Recommended for Reuse

| Function | File | Why |
|----------|------|-----|
| `get_alert()` | handle_alerts.py | Legacy alert scraping, replaced by webhooks |
| `post_entries()` | handle_alerts.py | Legacy workflow |
| `set_bulk_alerts()` | open_tv.py | Legacy workflow |
| `change_settings()` | open_tv.py | Legacy screener-specific |

---

## Quick Reference Card

### Essential Selectors (Most Stable)

```python
# Alert Dialog
SET_ALERT_BUTTON = 'div[data-name="set-alert-button"]'
ALERT_DIALOG = 'div[data-qa-id="alerts-create-edit-dialog"]'
CONDITION_DROPDOWN = 'span[data-qa-id="ui-kit-disclosure-control main-series-select"]'
WEBHOOK_CHECKBOX = 'input[data-qa-id="webhook"]'
SUBMIT_BUTTON = 'button[data-qa-id="submit"]'

# Indicators
LEGEND_ITEM = 'div[data-name="legend-source-item"]'
SETTINGS_DIALOG = '[data-dialog-name="indicatorSettings"]'

# Alerts Panel
ALERTS_BUTTON = 'button[aria-label="Alerts"]'
ALERTS_SETTINGS = 'div[data-name="alerts-settings-button"]'
ALERT_LOG_ITEM = 'div[data-name="alert-log-item"]'
CONFIRM_DIALOG = 'div[data-name="confirm-dialog"]'
```

### Essential Wait Times

```python
IMPLICIT_WAIT = 10          # Default for all finds
EXPLICIT_WAIT = 15          # Dialog/element appearance
CHART_LOAD_WAIT = 5         # After navigation
RECALC_WAIT = 10            # After symbol/settings change
ANIMATION_WAIT = 0.5        # UI animations
```

### Essential Patterns

```python
# Clear input reliably
ActionChains(driver).key_down(Keys.CONTROL, input).send_keys("a").perform()
input.send_keys(Keys.DELETE)
input.send_keys(new_value)

# Double-click for settings
ActionChains(driver).double_click(element).perform()

# Strip exchange from symbol
symbol = "OANDA:EURUSD".split(":")[-1]  # "EURUSD"

# Check toggle state
is_on = button.get_attribute("aria-pressed") == "true"

# Check if disabled
is_disabled = "isDisabled" in element.get_attribute("class")
```
