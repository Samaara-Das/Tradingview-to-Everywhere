# Selenium Automation Infrastructure Audit Report

**Date**: 2026-01-30
**Project**: TradingView to Everywhere (TTE)
**Branch**: multi-alert
**Auditor**: Claude Code

---

## Executive Summary

The TTE project contains **two parallel Selenium automation systems**:

| System | File(s) | Purpose | Status |
|--------|---------|---------|--------|
| **Modern** | `selenium_manager.py` | Tiered screener orchestration | Active/Primary |
| **Legacy** | `open_tv.py`, `handle_alerts.py` | Alert-based scraping | Secondary/Reference |

### Key Findings

| Capability | Status | Notes |
|------------|--------|-------|
| Browser initialization | **TESTED** | Profile management, version detection |
| Chart navigation | **TESTED** | URL-based (modern), UI-based (legacy) |
| Indicator legend access | **TESTED** | CSS selector `[data-name="legend-source-item"]` |
| Open indicator settings | **UNTESTED** | Double-click implemented but never run in production |
| Update symbol inputs | **UNTESTED** | Generic approach, heuristic-based input detection |
| Create alerts | **PARTIAL** | Basic creation works, webhook config missing |
| Configure webhooks | **NOT IMPLEMENTED** | Critical gap for tiered architecture |
| Take screenshots | **TESTED** | Alt+S snapshot with fallback to local PNG |

### Critical Gaps for Orchestrator

1. **Webhook alert creation** - No code exists to configure webhook URLs when creating alerts
2. **Alert message format** - Cannot set `{{alert.message}}` template programmatically
3. **Indicator settings validation** - Double-click approach untested, may need selectors
4. **Symbol input detection** - Heuristic approach may fail on OBDIV screener's input structure

---

## 1. Current Capabilities Documentation

### 1.1 selenium_manager.py (Modern System)

**Architecture**: Clean, modular, configurable
**Lines of Code**: ~500
**Exception Handling**: Custom `SeleniumError` class
**Context Manager**: Yes (`__enter__`/`__exit__`)

#### Class: SeleniumManager

| Method | Purpose | Tested? |
|--------|---------|---------|
| `get_driver()` | Initialize Chrome with profile | Yes |
| `navigate_to_chart(url, wait_time)` | Navigate and wait for chart | Yes |
| `_check_login_required()` | Detect login redirect | Yes |
| `open_indicator_settings(name)` | Double-click indicator | **No** |
| `set_symbol_inputs(symbols, max)` | Update symbol fields | **No** |
| `click_ok_button()` | Submit settings dialog | **No** |
| `update_nwe_symbols(symbols)` | High-level NWE update | **No** |
| `update_obdiv_symbols(symbols)` | High-level OBDIV update | **No** |
| `capture_chart_screenshot(symbol, tf)` | TradingView snapshot | Partial |
| `close()` / `restart()` | Lifecycle management | Yes |

#### Selectors Used

```python
# Chart container (presence wait)
".chart-container"

# Legend items
'div[data-name="legend-source-item"]'

# Legend title (indicator name)
'div[class*="title"]'

# Settings dialog (multiple fallbacks)
'[data-dialog-name="indicatorSettings"]'
'.tv-dialog--indicator-properties'

# Symbol inputs in dialog
'input[type="text"]'
'input.tv-symbol-input'

# OK/Apply buttons (priority order)
'button[data-name="submit"]'
'button[data-name="apply"]'
"//button[contains(text(), 'OK')]"
"//button[contains(text(), 'Apply')]"
'.tv-dialog__submit-button'

# Snapshot URL input
'input[type="text"][readonly]'
'.tv-snapshot-url input'
```

#### Wait Strategies

```python
# Implicit wait (global)
driver.implicitly_wait(10)  # SELENIUM_IMPLICIT_WAIT

# Page load timeout
driver.set_page_load_timeout(60)  # PAGE_LOAD_TIMEOUT

# Explicit waits (WebDriverWait)
- Chart container: 30s presence
- Settings dialog: 30s presence
- OK button: 30s clickable
- Snapshot URL: 30s presence
```

#### Error Handling

```python
# Custom exception with helpful messages
class SeleniumError(Exception):
    pass

# Chrome already running detection
if "DevToolsActivePort" in error_msg:
    raise SeleniumError(
        "Chrome driver initialization failed.\n"
        "Please close ALL Chrome windows and try again."
    )

# Login detection
if self._check_login_required():
    raise SeleniumError("TradingView login required. Please log in manually.")

# Stale element recovery
except StaleElementReferenceException:
    continue  # Skip stale, move to next input
```

---

### 1.2 open_tv.py (Legacy System)

**Architecture**: Monolithic, tightly coupled
**Lines of Code**: ~1,350
**Exception Handling**: Generic `except Exception`
**Context Manager**: No

#### Class: Browser

| Method | Purpose | Tested? |
|--------|---------|---------|
| `sign_in()` | Automated TradingView login | Yes |
| `setup_tv()` | Configure layout, indicators | Yes |
| `change_layout(name)` | Switch TradingView layouts | Yes |
| `get_indicator(shorttitle)` | Find indicator in legend | Yes |
| `click_create_alert(shorttitle)` | Create basic alert | Partial |
| `delete_all_alerts()` | Bulk delete alerts | Yes |
| `set_alerts(symbols)` | Create alerts for screener | Partial |
| `change_settings(symbols)` | Update indicator settings | Yes |
| `indicator_visibility(visible, name)` | Toggle indicator eye | Yes |
| `reupload_indicator(ind, name, short)` | Delete and re-add | Yes |

#### Selectors Used (Selected Critical)

```python
# Login detection
'a[data-main-menu-root-track-id="products"]'

# Login form
By.NAME, "id_username"  # Email
By.NAME, "id_password"  # Password
'button[data-overflow-tooltip-text="Sign in"]'

# Layout switching (FRAGILE - hardcoded XPath!)
"/html/body/div[2]/div/div[3]/div/div/div[3]/div[1]/div/div/div/div/div[14]/div/div/div/button"

# Indicator legend
'div[data-name="legend-source-item"]'
'div[class="title-l31H9iuA"]'  # Obfuscated, may change

# Settings dialog
'.content-tBgV1m0B'  # Obfuscated
'.inlineRow-tBgV1m0B div[data-name="edit-button"]'

# Alert creation
'div[data-name="set-alert-button"]'
'div[data-name="alerts-create-edit-dialog"]'
'span[data-qa-id="ui-kit-disclosure-control main-series-select"]'
'input[id="alert-name"]'
'button[data-name="submit"]'

# Alert deletion
'div[data-name="alerts-settings-button"]'
'div[data-name="menu-inner"]'
```

#### Critical Anti-Patterns

1. **Hardcoded XPath for layout switching** - Will break on any TradingView UI update
2. **Print statements for timing** - Comment says "Don't remove - code only works with prints"
3. **Obfuscated CSS classes** - `title-l31H9iuA`, `content-tBgV1m0B` change frequently
4. **Silent failures** - Many methods return `True` even when operation partially fails

---

### 1.3 handle_alerts.py

**Purpose**: Read and process TradingView alert messages
**Alert Creation**: Not implemented (only reading)

#### Class: Alerts

| Method | Purpose | Status |
|--------|---------|--------|
| `post_entries()` | Read all unread alerts | Working |
| `get_alert()` | Read single alert, delete it | Working |
| `get_alert_box_and_msg()` | Extract alert DOM element | Working |
| `remove_alert()` | Delete alert from UI | Working |
| `restart_inactive_alerts()` | Reactivate stopped alerts | Working |
| `send_everywhere()` | Distribute to socials | Working |

#### Alert Message Parsing

```python
# Expected format (from Pine Script)
{
    "GBPUSD": {
        "timeframe": "1H",
        "entryTime": "1,672,531,200,000",
        "entryPrice": 1.0500,
        "slPrice": 1.0400,
        "tp1Price": 1.0600,
        "tp2Price": 1.0700,
        "tp3Price": 1.0800,
        "direction": "bullish",
        "type": "entry"
    }
}
```

#### Selectors Used

```python
# Alert log items
'div[data-name="alert-log-item"]'

# Alert message content
'div[class="message-PQUvhamm"]'

# Alert name
'div[class="name-PQUvhamm"]'

# Delete button (on hover)
'div[data-name="event-delete-button"]'
```

---

## 2. Specific Capability Assessment

### 2.1 Capability Matrix

| Capability | selenium_manager | open_tv | Notes |
|------------|-----------------|---------|-------|
| Open TradingView | Yes (URL) | Yes (URL) | Both work |
| Login automation | No (manual) | Yes (env vars) | Manual is safer |
| Navigate to chart | Yes | Yes | Different approaches |
| Find indicators | Yes | Yes | Same selector |
| Open settings | Yes (untested) | Yes (tested) | Double-click vs button |
| Update symbol inputs | Yes (untested) | Yes (partial) | Heuristic detection |
| Create alerts | No | Yes (partial) | Missing webhook config |
| Configure webhooks | **No** | **No** | **CRITICAL GAP** |
| Set alert message | **No** | **No** | **CRITICAL GAP** |
| Take screenshots | Yes | No | Alt+S approach |
| Delete alerts | No | Yes | Bulk delete |
| Restart alerts | No | Yes | Reactivate inactive |

### 2.2 Detailed Capability Analysis

#### Opening Indicator Settings

**selenium_manager.py approach:**
```python
def open_indicator_settings(self, indicator_name):
    # Find indicator in legend
    indicators = wait.until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')
    ))

    # Match by name
    for ind in indicators:
        title = ind.find_element(By.CSS_SELECTOR, 'div[class*="title"]').text
        if indicator_name in title:
            # Double-click to open settings
            ActionChains(driver).double_click(ind).perform()
            break

    # Wait for dialog
    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, '[data-dialog-name="indicatorSettings"]')
    ))
```

**Assessment**: Logic is sound but **never tested in production**. May need:
- Different dialog selector for Pine Script indicators
- Click on settings gear icon instead of double-click
- Handling indicator name variations

#### Updating Symbol Inputs

**selenium_manager.py approach:**
```python
def set_symbol_inputs(self, symbols, max_inputs=20):
    dialog = driver.find_element(By.CSS_SELECTOR, '[data-dialog-name="indicatorSettings"]')
    inputs = dialog.find_elements(By.CSS_SELECTOR, 'input[type="text"]')

    symbol_inputs = []
    for inp in inputs:
        # Heuristic: check for ':' in value (e.g., "EURUSD:FX")
        # Or placeholder/data-name containing "symbol"
        value = inp.get_attribute('value') or ''
        placeholder = inp.get_attribute('placeholder') or ''
        data_name = inp.get_attribute('data-name') or ''

        if ':' in value or 'symbol' in placeholder.lower() or 'symbol' in data_name.lower():
            symbol_inputs.append(inp)

    # Fill inputs
    for i, inp in enumerate(symbol_inputs[:max_inputs]):
        if i < len(symbols):
            inp.clear()
            inp.send_keys(symbols[i])
```

**Assessment**: Heuristic approach is **risky**. May fail if:
- Symbol inputs don't contain ':' or 'symbol' identifier
- Other text inputs match the heuristic (e.g., notes field)
- Pine Script input structure differs from expected

**Recommendation**: Read the actual Pine Script indicator settings to understand exact input structure, then use explicit selectors.

---

## 3. Gap Analysis

### 3.1 Critical Gaps (Must Fix)

| Gap | Impact | Effort |
|-----|--------|--------|
| **Webhook URL configuration** | Cannot create alerts that POST to API | High |
| **Alert message format** | Cannot set `{{alert.message}}` template | High |
| **Indicator settings validation** | May fail silently if dialog structure differs | Medium |
| **Symbol input detection** | May update wrong fields | Medium |

### 3.2 Webhook Alert Creation (Not Implemented)

**What's needed:**
1. Navigate to "Notifications" tab in alert creation dialog
2. Find webhook URL input field
3. Enter Stock Buddy API URL
4. Find message format input
5. Enter `{{alert.message}}`
6. Enable webhook notification type

**Current state:**
- Alert creation stops after selecting indicator and clicking "Create"
- No code navigates to Notifications tab
- No selectors for webhook URL input
- No selectors for message format input

### 3.3 Medium Priority Gaps

| Gap | Impact | Effort |
|-----|--------|--------|
| Settings dialog close button | May leave dialogs open | Low |
| Symbol validation | No check if symbol is valid | Low |
| Progress indication | No feedback during long operations | Low |
| Rate limit handling | May trigger TradingView restrictions | Medium |

### 3.4 Low Priority Gaps

| Gap | Impact | Effort |
|-----|--------|--------|
| Screenshot cleanup | Old files accumulate | Low |
| Metrics/observability | Hard to debug production issues | Medium |
| Browser recovery | May need manual intervention | Medium |

---

## 4. Code Quality Review

### 4.1 selenium_manager.py (Modern)

| Aspect | Grade | Notes |
|--------|-------|-------|
| **Architecture** | A | Clean separation, single responsibility |
| **Error handling** | A | Custom exceptions, helpful messages |
| **Wait strategies** | A | Configurable, explicit waits |
| **Selectors** | B+ | Good data-* attributes, few obfuscated |
| **Logging** | A | Structured, module-based |
| **Testability** | B | No DI, but simple design |
| **Documentation** | B | Docstrings present, could be better |

**Strengths:**
- Context manager for cleanup
- Configurable timeouts via Config class
- Multiple selector fallbacks for robustness
- Clear error messages with recovery instructions

**Areas for improvement:**
- Add retry decorator to key methods
- Add typing hints consistently
- Add validation for symbols before sending

### 4.2 open_tv.py (Legacy)

| Aspect | Grade | Notes |
|--------|-------|-------|
| **Architecture** | D | Monolithic, 1300+ lines |
| **Error handling** | D | Generic `except Exception`, silent failures |
| **Wait strategies** | C | Hardcoded, inconsistent |
| **Selectors** | D | Hardcoded XPath, obfuscated classes |
| **Logging** | C | Print statements for debugging |
| **Testability** | F | Tightly coupled, no mocking possible |
| **Documentation** | C | Some docstrings, outdated |

**Critical issues:**
- Hardcoded layout XPath will break on TradingView updates
- Print statements indicate timing issues being masked
- Obfuscated CSS classes (`-l31H9iuA`) are unstable
- No context manager, potential resource leaks

### 4.3 Selector Robustness Analysis

**Good selectors (stable):**
```css
div[data-name="legend-source-item"]     /* Data attribute */
button[data-name="submit"]              /* Data attribute */
div[data-name="alerts-create-edit-dialog"]  /* Data attribute */
```

**Risky selectors (may change):**
```css
div[class="title-l31H9iuA"]             /* Obfuscated hash */
.content-tBgV1m0B                       /* Obfuscated hash */
div[class="message-PQUvhamm"]           /* Obfuscated hash */
```

**Extremely fragile:**
```xpath
/html/body/div[2]/div/div[3]/...       /* Hardcoded DOM path */
```

**Recommendation**: Replace all obfuscated class selectors with data-* attributes where available, or use partial class matching (`[class*="title"]`).

---

## 5. Reusability Recommendations

### 5.1 Reuse As-Is

| Component | File | Notes |
|-----------|------|-------|
| Browser initialization | `selenium_manager.py:get_driver()` | Well-implemented |
| Chart navigation | `selenium_manager.py:navigate_to_chart()` | URL-based, simple |
| Login detection | `selenium_manager.py:_check_login_required()` | Multiple patterns |
| Screenshot capture | `selenium_manager.py:capture_chart_screenshot()` | Works with fallback |
| Lifecycle management | `selenium_manager.py:close/restart()` | Context manager |

### 5.2 Reuse with Modifications

| Component | File | Required Changes |
|-----------|------|------------------|
| Indicator settings | `selenium_manager.py:open_indicator_settings()` | Add gear button click as fallback |
| Symbol inputs | `selenium_manager.py:set_symbol_inputs()` | Add explicit selector option |
| OK button click | `selenium_manager.py:click_ok_button()` | Add dialog close verification |
| Alert creation | `open_tv.py:click_create_alert()` | Add webhook configuration steps |
| Alert deletion | `open_tv.py:delete_all_alerts()` | Port to selenium_manager.py |

### 5.3 Needs Complete Rewrite

| Component | Reason |
|-----------|--------|
| Layout switching | Hardcoded XPath in open_tv.py |
| Webhook configuration | Does not exist |
| Alert message format | Does not exist |
| Symbol input validation | Heuristic approach unreliable |

---

## 6. Implementation Recommendations

### 6.1 Phase 1: Validate Existing Code (Before Production)

```python
# Test indicator settings flow manually
with SeleniumManager() as browser:
    driver = browser.get_driver()
    browser.navigate_to_chart(NWE_CHART_URL)

    # Validate these work:
    browser.open_indicator_settings("TTE NWE Screener")
    browser.set_symbol_inputs(["EURUSD", "GBPUSD"], max_inputs=2)
    browser.click_ok_button()
```

### 6.2 Phase 2: Add Webhook Alert Creation

```python
# New method needed in selenium_manager.py
def create_webhook_alert(self, indicator_name: str, webhook_url: str, alert_name: str = ""):
    """Create alert with webhook configuration."""

    # 1. Open alert creation dialog
    set_alert_btn = self.wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="set-alert-button"]'))
    )
    set_alert_btn.click()

    # 2. Wait for dialog
    dialog = self.wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"]'))
    )

    # 3. Select indicator as source
    source_dropdown = dialog.find_element(
        By.CSS_SELECTOR, 'span[data-qa-id="ui-kit-disclosure-control main-series-select"]'
    )
    source_dropdown.click()

    options = self.driver.find_elements(
        By.CSS_SELECTOR, 'div[data-name="menu-inner"] div[role="option"]'
    )
    for opt in options:
        if indicator_name in opt.text:
            opt.click()
            break

    # 4. Navigate to Notifications tab (NEW)
    # TODO: Identify correct selector for Notifications tab
    notifications_tab = dialog.find_element(By.CSS_SELECTOR, '???')  # Need to identify
    notifications_tab.click()

    # 5. Enable webhook notification (NEW)
    # TODO: Find webhook toggle/checkbox
    webhook_toggle = dialog.find_element(By.CSS_SELECTOR, '???')  # Need to identify
    if not webhook_toggle.is_selected():
        webhook_toggle.click()

    # 6. Enter webhook URL (NEW)
    webhook_url_input = dialog.find_element(By.CSS_SELECTOR, '???')  # Need to identify
    webhook_url_input.clear()
    webhook_url_input.send_keys(webhook_url)

    # 7. Set message format (NEW)
    message_format_input = dialog.find_element(By.CSS_SELECTOR, '???')  # Need to identify
    message_format_input.clear()
    message_format_input.send_keys('{{alert.message}}')

    # 8. Set alert name
    if alert_name:
        name_input = dialog.find_element(By.CSS_SELECTOR, 'input[id="alert-name"]')
        name_input.clear()
        name_input.send_keys(alert_name)

    # 9. Create alert
    submit_btn = dialog.find_element(By.CSS_SELECTOR, 'button[data-name="submit"]')
    submit_btn.click()

    # 10. Wait for success
    time.sleep(2)
    return True
```

### 6.3 Phase 3: Improve Symbol Input Detection

```python
# Enhanced version with explicit Pine Script support
def set_symbol_inputs_explicit(self, symbols: List[str], input_prefix: str = "Symbol"):
    """
    Update symbol inputs using explicit label matching.

    Args:
        symbols: List of symbols to set
        input_prefix: Label prefix (e.g., "Symbol" for Symbol1, Symbol2, etc.)
    """
    dialog = self.driver.find_element(
        By.CSS_SELECTOR, '[data-dialog-name="indicatorSettings"]'
    )

    # Find input rows by label text
    rows = dialog.find_elements(By.CSS_SELECTOR, '.inputRow, [class*="inputRow"]')

    symbol_index = 0
    for row in rows:
        try:
            label = row.find_element(By.CSS_SELECTOR, '.label, [class*="label"]').text
            if label.startswith(input_prefix):
                if symbol_index < len(symbols):
                    input_field = row.find_element(By.CSS_SELECTOR, 'input')
                    input_field.clear()
                    input_field.send_keys(symbols[symbol_index])
                    symbol_index += 1
        except NoSuchElementException:
            continue

    return symbol_index  # Number of symbols successfully set
```

---

## 7. Test Plan

### 7.1 Manual Validation Tests

Before production use, manually verify:

1. **Indicator Settings Test**
   ```
   - Navigate to NWE chart URL
   - Double-click "TTE NWE Screener" indicator
   - Verify settings dialog opens
   - Update 2 symbol inputs
   - Click OK
   - Verify chart updates with new symbols
   ```

2. **Alert Creation Test**
   ```
   - Navigate to OBDIV chart URL
   - Click "+ Set Alert" button
   - Select "TTE OBDIV Screener" as source
   - Navigate to Notifications tab
   - Configure webhook URL
   - Set message format
   - Create alert
   - Verify alert appears in Alerts list
   ```

3. **Screenshot Test**
   ```
   - Navigate to any chart
   - Press Alt+S
   - Verify snapshot dialog appears
   - Extract URL from readonly input
   - Verify URL is valid TradingView snapshot
   ```

### 7.2 Automated Test Suite

```python
# tests/test_selenium_manager.py

def test_browser_initialization():
    """Verify Chrome starts with correct profile."""
    with SeleniumManager() as browser:
        driver = browser.get_driver()
        assert driver is not None
        assert "TTE" in driver.capabilities.get('chrome', {}).get('userDataDir', '')

def test_chart_navigation():
    """Verify navigation to TradingView chart."""
    with SeleniumManager() as browser:
        browser.navigate_to_chart("https://www.tradingview.com/chart/?symbol=EURUSD")
        assert "tradingview.com" in browser.driver.current_url

def test_indicator_settings_open():
    """Verify indicator settings dialog opens."""
    # This test requires NWE_CHART_URL configured
    pass

def test_symbol_input_update():
    """Verify symbols can be updated."""
    # This test requires indicator settings dialog open
    pass
```

---

## 8. Risk Assessment

### 8.1 High Risk Items

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Indicator settings selectors incorrect | High | Critical | Manual testing before deployment |
| Webhook config selectors unknown | Certain | Critical | Browser inspection, find selectors |
| TradingView UI change | Medium | High | Use data-* attributes, avoid obfuscated |
| Rate limiting by TradingView | Medium | Medium | Add delays, respect robot.txt |

### 8.2 Medium Risk Items

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Chrome profile corruption | Low | High | Backup profiles, recovery script |
| Session timeout | Medium | Medium | Login detection, auto-retry |
| Screenshot URL expiration | High | Low | Save local backup |

---

## 9. Next Steps

### COMPLETED (2026-01-30)

1. **Added `create_webhook_alert()` method** to `selenium_manager.py`
   - Full alert creation workflow with webhook configuration
   - Retry decorator for robustness
   - Multiple selector fallbacks for TradingView UI changes

2. **Added retry decorator** to critical selenium operations
   - `@retry_on_failure` with exponential backoff
   - Configurable retries and delay

3. **Added `TVSelectors` class** for centralized selector management
   - All selectors in one place for easy updates
   - Organized by function (legend, alert, buttons, etc.)

4. **Added `set_symbol_inputs_by_label()` method**
   - Label-based input detection (more reliable)
   - Falls back to heuristic method if labels not found

5. **Added utility methods**
   - `delete_all_alerts()` - Bulk alert deletion
   - `verify_indicator_loaded()` - Verify indicator state
   - `_close_alert_dialog()` - Safe dialog closure

6. **Created `test_browser_quick.py`** validation script
   - Individual test modes: browser, navigation, indicator, alert
   - `--inspect-alert` mode for manual selector discovery
   - Comprehensive test suite with `--test all`

### Immediate (Before Production)

1. **Run inspection mode** to discover webhook selectors:
   ```bash
   python test_browser_quick.py --inspect-alert
   ```

2. **Update selectors** in `TVSelectors` class:
   - `NOTIFICATIONS_TAB`
   - `WEBHOOK_URL_TOGGLE`
   - `WEBHOOK_URL_INPUT`
   - `ALERT_MESSAGE_INPUT`

3. **Run full test suite**:
   ```bash
   python test_browser_quick.py --test all
   ```

### Short Term (First Week)

1. **Test full orchestration cycle** with 2-3 symbols
2. **Set up local test environment** with mock API
3. **Configure NWE_CHART_URL and OBDIV_CHART_URL** in `.env`

### Medium Term (First Month)

1. **Monitor selector stability** after TradingView updates
2. **Add metrics/logging** for production debugging
3. **Create recovery scripts** for common failure modes

---

## Appendix A: Environment Configuration

```bash
# Required for selenium_manager.py
CHROME_PROFILES_PATH=/path/to/chrome/profiles
NWE_CHART_URL=https://www.tradingview.com/chart/YOUR_NWE_CHART/
OBDIV_CHART_URL=https://www.tradingview.com/chart/YOUR_OBDIV_CHART/
STOCK_BUDDY_API_URL=https://stock-buddy-app.vercel.app/api/tte

# Optional overrides
SELENIUM_IMPLICIT_WAIT=10
SELENIUM_EXPLICIT_WAIT=30
PAGE_LOAD_TIMEOUT=60
NWE_BATCH_SIZE=20
OBDIV_BATCH_SIZE=8
```

## Appendix B: Selector Reference Quick Sheet

```python
# Stable selectors (data-* attributes)
LEGEND_ITEM = 'div[data-name="legend-source-item"]'
SET_ALERT_BTN = 'div[data-name="set-alert-button"]'
ALERT_DIALOG = 'div[data-name="alerts-create-edit-dialog"]'
SUBMIT_BTN = 'button[data-name="submit"]'
CANCEL_BTN = 'button[data-name="cancel"]'
CLOSE_BTN = 'button[data-name="close"]'
ALERT_LOG_ITEM = 'div[data-name="alert-log-item"]'
SETTINGS_BTN = 'button[data-name="legend-settings-action"]'
DELETE_BTN = 'div[data-name="event-delete-button"]'

# Semi-stable selectors (may need updates)
INDICATOR_SETTINGS_DIALOG = '[data-dialog-name="indicatorSettings"]'
SOURCE_DROPDOWN = 'span[data-qa-id="ui-kit-disclosure-control main-series-select"]'
MENU_OPTIONS = 'div[data-name="menu-inner"] div[role="option"]'
ALERT_NAME_INPUT = 'input[id="alert-name"]'
```

---

**Report Complete**

This audit provides the foundation for implementing the orchestrator's Selenium automation. The critical next step is browser inspection to find webhook configuration selectors, then implementing the `create_webhook_alert()` method.
