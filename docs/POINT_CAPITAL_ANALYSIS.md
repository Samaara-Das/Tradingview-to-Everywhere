# Point-Capital Branch Deep Dive Analysis

**Last Updated**: 2026-01-31
**Branch**: `point-capital`
**Purpose**: Comprehensive analysis for Stock Buddy tiered architecture migration

---

## Executive Summary

### What This Branch Does

The point-capital branch implements a **poll-based** TradingView automation system:

- **Selenium-based automation** for TradingView interaction
- **3 screeners**: Order Block, Nadaraya Watson, Structure Break
- **5 symbols per batch** processing
- **Alert log scraping** (not webhooks)
- **Multi-platform distribution**: Discord, Facebook, Twitter, MongoDB

### Key Differences from Tiered Architecture Needs

| Aspect | Point-Capital (Current) | Tiered Architecture (Target) |
|--------|------------------------|------------------------------|
| Alert Method | Poll-based (scrape alert log) | Webhook-based (POST to API) |
| Symbols/Batch | 5 symbols | 40 (NWE) / 8 (OBDIV) |
| Architecture | Single-tier | Tiered (NWE rotation + OBDIV hot list) |
| API Integration | None | GET /api/tte/symbols/next-batch |
| Indicator Focus | 3 screeners | NWE + OBDIV only |

### Recommendation: EXTRACT AND ADAPT

- **70%+ of Selenium patterns are directly reusable**
- Existing `docs/EXISTING_SELENIUM_FLOW.md` provides 50+ documented selectors
- Build new tiered orchestrator using proven, battle-tested components

---

## Section 1: File Inventory

| File | Lines | Purpose | Reuse Value | Notes |
|------|-------|---------|-------------|-------|
| `main.py` | 181 | Entry point, main loop | LOW | Legacy workflow-specific |
| `open_tv.py` | 1397 | Core Selenium automation | **HIGH** | Browser setup, indicator management, alerts |
| `handle_alerts.py` | 402 | Alert log scraping | LOW | Replaced by webhooks |
| `open_entry_chart.py` | 294 | Chart navigation, screenshots | **HIGH** | Direct reuse |
| `resources/symbol_settings.py` | 191 | Symbol batching, MongoDB | MEDIUM | Adapt batch sizes |
| `resources/utils.py` | 159 | Tab switching, dialogs | **HIGH** | Direct reuse |
| `database/local_db.py` | ~100 | MongoDB CRUD | MEDIUM | Different schema needed |
| `env.py` | 46 | Configuration | **HIGH** | Extend for API endpoints |
| `logger_setup.py` | ~50 | Logging infrastructure | **HIGH** | Direct reuse |

---

## Section 2: Complete Workflow Documentation

### Startup Sequence

```
main.py: run_trading_view()
├── Logger initialization (start_continuous_trim)
├── Browser() constructor with screener configs
│   ├── Chrome options setup
│   ├── WebDriver initialization
│   ├── OpenChart instance creation
│   └── fill_symbol_set() if START_FRESH
└── browser.setup_tv()
```

### Setup Phase (`Browser.setup_tv()` - open_tv.py:195-330)

```
1. sign_in()                          → Check products menu, login if needed
   ├── Navigate to signin page
   ├── Check for products menu (indicates logged in)
   └── If not logged in: email → password → submit

2. open_page('tradingview.com/chart') → Open chart page
   └── Maximize window

3. change_layout('PointCapital')      → Switch to correct layout
   ├── Get current layout from #header-toolbar-save-load
   ├── If different, click dropdown arrow
   └── Select target layout from list

4. change_tframe('4 hours')           → Set chart timeframe
   ├── Get current timeframe from button aria-label
   └── If different, select from dropdown

5. open_alerts_sidebar()              → Open alerts panel
   ├── Find button[aria-label="Alerts"]
   └── Click if aria-pressed="false"

6. delete_all_alerts() [if START_FRESH]
   ├── Open 3-dots menu
   ├── Click "Stop All" → Confirm
   └── Click "Delete All Inactive" → Confirm

7. get_indicator() × 4                → Find screener & drawer indicators
   ├── Query div[data-name="legend-source-item"]
   └── Match by shorttitle in div.title-l31H9iuA

8. indicator_visibility(True)         → Make indicators visible
   └── Toggle via button[data-name="legend-show-hide-action"]
```

### Alert Creation Phase (`Browser.set_bulk_alerts()` - open_tv.py:332-385)

```
FOR each symbol_sublist (5 symbols):
├── change_symbol(symbols[0])         → Navigate to first symbol
│   ├── Click #header-toolbar-symbol-search
│   ├── Enter symbol → ENTER
│   └── Wait 1.5s for chart load

├── change_settings(symbols, screener) × 3 screeners
│   ├── Click screener indicator
│   ├── Click legend-settings-action button
│   ├── Find .content-tBgV1m0B settings panel
│   ├── For each symbol input:
│   │   ├── Click edit button
│   │   ├── Enter symbol → ENTER
│   └── Click submit button

├── sleep(3)                          → Wait for indicator recalculation

└── set_alerts(symbols, screener) × 3 screeners
    ├── Check is_no_error() for screener
    ├── If error: reupload_indicator() → change_settings() → retry
    ├── Click div[data-name="set-alert-button"]
    ├── Wait for alerts-create-edit-dialog
    └── Click submit button
```

### Main Monitoring Loop (`post_entries` - handle_alerts.py:215-238)

```
WHILE True:
├── Every 10 min: restart_inactive_alerts()
│   ├── Open alerts-settings-button dropdown
│   ├── Expand "Show Alerts" section
│   ├── Select "All" option
│   └── Click "Restart all inactive" → Confirm

└── Continuously: alerts.post_entries()
    ├── open_log_tab()                → Switch to Logs tab
    ├── Get all div[data-name="alert-log-item"]
    │
    WHILE alert_boxes exist:
    ├── get_alert_box_and_msg()       → Get last alert
    │   └── Extract message from div.message-PQUvhamm
    │
    ├── remove_alert()                → Delete processed alert
    │   └── Click div[data-name="event-delete-button"]
    │
    ├── FOR each entry in alert_msg:
    │   ├── change_symbol(entry.symbol)
    │   ├── change_tframe(entry.timeframe)
    │   ├── change_indicator_settings() → Trade Drawer
    │   │   ├── Double-click indicator
    │   │   ├── Open indicator-properties-dialog
    │   │   ├── Fill inputs with Ctrl+A/Delete/send_keys
    │   │   └── Submit and wait for load
    │   │
    │   ├── save_chart_img()
    │   │   ├── Click camera button
    │   │   ├── Click "Open in new tab"
    │   │   ├── Switch to new window
    │   │   ├── Get PNG and TV links
    │   │   └── Close tab, switch back
    │   │
    │   └── send_everywhere()
    │       ├── Facebook: post(png_link, message)
    │       └── MongoDB: add_doc(entry_data)
```

---

## Section 3: Reusable Selenium Patterns

### Pattern 1: Browser Initialization

**Location**: `open_tv.py:82-96`

```python
chrome_options = Options()
chrome_options.add_experimental_option("detach", keep_open)
chrome_options.add_argument(f"--profile-directory={PROFILE}")
chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILES_PATH}/TTE")
chrome_options.add_argument("--remote-debugging-port=9224")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Version-matched ChromeDriver
cmd = "powershell -command \"&{(Get-Item 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe').VersionInfo.ProductVersion}\""
version = read_version_from_cmd(cmd, PATTERN["google-chrome"])
service = ChromeDriverManager(driver_version=version).install()
self.driver = webdriver.Chrome(service=ChromeService(service), options=chrome_options)
```

**Reuse**: Direct copy for any TradingView automation project.

---

### Pattern 2: Symbol Change

**Location**: `open_entry_chart.py:103-151`

```python
def change_symbol(self, symbol):
    # Strip exchange prefix (e.g., "OANDA:EURUSD" → "EURUSD")
    no_exchange_symbol = symbol.split(":")[-1] if ":" in symbol else symbol

    symbol_search = WebDriverWait(self.driver, 15).until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[id="header-toolbar-symbol-search"]')
        )
    )

    # Only change if current symbol is different
    if not symbol_search.find_element(By.CSS_SELECTOR, "div").text == no_exchange_symbol:
        symbol_search.click()
        search_input = self.driver.find_element(
            By.XPATH,
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div/div[2]/div[1]/input',
        )
        # Clear and enter symbol
        ActionChains(self.driver).key_down(Keys.CONTROL, search_input).send_keys("a").perform()
        search_input.send_keys(Keys.DELETE)
        search_input.send_keys(symbol)
        search_input.send_keys(Keys.ENTER)

        # Wait for symbol to appear
        WebDriverWait(self.driver, 5).until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, 'button[id="header-toolbar-symbol-search"] div'),
                no_exchange_symbol,
            )
        )
        sleep(1.5)  # Wait for chart to load
```

**Reuse**: Direct copy - handles exchange prefix stripping and chart load wait.

---

### Pattern 3: Input Field Clearing (CRITICAL)

**Location**: Multiple files

```python
# WRONG - .clear() doesn't work reliably on TradingView
input_field.clear()
input_field.send_keys(value)

# CORRECT - Use Ctrl+A + Delete
ActionChains(self.driver).key_down(Keys.CONTROL, input_field).send_keys("a").perform()
input_field.send_keys(Keys.DELETE)
input_field.send_keys(value)
```

**Reuse**: Must use this pattern for ALL TradingView input fields.

---

### Pattern 4: Indicator Settings Dialog

**Location**: `open_tv.py:483-659`

```python
def change_settings(self, symbols_list, screener_shorttitle=None):
    # Get indicator reference
    indicator = self._safe_indicator_access(screener_shorttitle)

    # Open settings
    indicator.click()
    WebDriverWait(indicator, 15).until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[data-name="legend-settings-action"]')
        )
    ).click()

    # Wait for settings dialog
    settings = WebDriverWait(self.driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".content-tBgV1m0B"))
    )

    # Find symbol input edit buttons
    symbol_inputs = settings.find_elements(
        By.CSS_SELECTOR,
        '.inlineRow-tBgV1m0B div[data-name="edit-button"]',
    )

    # Fill each symbol
    for i, symbol in enumerate(symbols_list):
        symbol_inputs[i].click()
        search_input = self.driver.find_element(
            By.XPATH,
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div/div/div[2]/div/div[2]/div/input',
        )
        search_input.send_keys(symbol)
        search_input.send_keys(Keys.ENTER)

    # Submit
    self.driver.find_element(By.CSS_SELECTOR, 'button[name="submit"]').click()
```

---

### Pattern 5: Screenshot Capture

**Location**: `open_entry_chart.py:204-266`

```python
def save_chart_img(self):
    """Capture chart screenshot and return PNG/TV links"""
    # Click camera button
    camera = WebDriverWait(self.driver, 20).until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//button[@aria-label='Take a snapshot']/div[@id='header-toolbar-screenshot']",
        ))
    )
    camera.click()

    # Click "Open in new tab"
    open_in_new_tab = self.driver.find_element(
        By.XPATH,
        '//*[@id="overlap-manager-root"]/div/span/div[1]/div/div/div[5]',
    )
    open_in_new_tab.click()

    # Switch to new tab
    self.driver.switch_to.window(self.driver.window_handles[-1])

    # Wait for image
    img_element = WebDriverWait(self.driver, 12).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "img.tv-snapshot-image"))
    )

    # Get links
    tv_link = self.driver.current_url
    png_link = img_element.get_attribute("src")

    # Clean up
    self.driver.close()
    self.driver.switch_to.window(self.driver.window_handles[0])

    return {"png": png_link, "tv": tv_link}
```

---

### Pattern 6: Tab Switching Utilities

**Location**: `resources/utils.py:74-139`

```python
def open_alert_tab(self, driver):
    """Switch to Alerts tab in sidebar"""
    alert_tab_selector = '''
        div[class="widget-X9EuSe_t widgetbar-widget widgetbar-widget-alerts"]
        div[class="widgetHeader-X9EuSe_t"]
        div[id="AlertsHeaderTabs"]
        button[data-name="light-tab-0"]
    '''
    tab = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, alert_tab_selector))
    )
    if tab.get_attribute("aria-selected") != "true":
        WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, alert_tab_selector))
        ).click()
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, "AlertsHeaderTabs"))
    )

def open_log_tab(self, driver):
    """Switch to Logs tab in sidebar"""
    # Same pattern with button[data-name="light-tab-1"]
```

---

### Pattern 7: Confirmation Dialog Handling

**Location**: `resources/utils.py:141-158`

```python
def click_yes_in_confirm_popup(self, driver):
    """Handle TradingView confirmation dialogs"""
    dialog = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'div[data-name="confirm-dialog"]')
        )
    )
    WebDriverWait(dialog, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="yes"]'))
    ).click()
    sleep(2)  # Wait for action to complete
```

---

### Pattern 8: Stale Element Recovery

**Location**: `open_tv.py:1313-1332`

```python
def _safe_indicator_access(self, shorttitle: str, max_retries: int = 2):
    """Safely access an indicator with retry logic for stale element exceptions"""
    for attempt in range(max_retries):
        try:
            indicator = self._get_fresh_indicator(shorttitle)
            if indicator:
                # Test if element is still valid
                _ = indicator.get_attribute("class")
                return indicator
        except StaleElementReferenceException:
            if attempt < max_retries - 1:
                sleep(1)
            else:
                return None
    return None
```

---

## Section 4: Gaps Analysis

### Missing for Tiered Architecture

| Gap | Effort | Priority | Notes |
|-----|--------|----------|-------|
| Webhook URL in alert dialog | 3-4h | HIGH | Navigate to Notifications tab, enable webhook, enter URL |
| API client for Stock Buddy | 2-3h | HIGH | GET /api/tte/symbols/next-batch |
| Batch size configuration | 1h | MEDIUM | Modify `fill_symbol_set()` for 40/8 symbols |
| Tiered orchestration logic | 4-5h | HIGH | NWE rotation + OBDIV hot list |
| Single-alert deletion | 1-2h | MEDIUM | Delete specific alert after webhook processing |
| Symbol rotation state tracking | 2-3h | HIGH | Track which symbols have been processed |
| Webhook alert message format | 1h | MEDIUM | JSON payload structure for screener data |

**TOTAL ESTIMATED EFFORT: 15-20 hours**

### Webhook Alert Creation Gap

The current codebase creates alerts without webhooks. New code needed:

```python
# PSEUDOCODE - Webhook alert creation
def create_webhook_alert(indicator_name, webhook_url):
    # 1. Click SET_ALERT_BUTTON
    driver.find_element(By.CSS_SELECTOR, 'div[data-name="set-alert-button"]').click()

    # 2. Wait for dialog
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'div[data-qa-id="alerts-create-edit-dialog"]')
        )
    )

    # 3. Navigate to Notifications tab
    driver.find_element(By.CSS_SELECTOR, '#alert-dialog-tabs__notifications').click()

    # 4. Enable webhook checkbox
    webhook_checkbox = driver.find_element(By.CSS_SELECTOR, 'input[data-qa-id="webhook"]')
    if not webhook_checkbox.is_selected():
        webhook_checkbox.click()

    # 5. Enter webhook URL
    webhook_input = driver.find_element(By.CSS_SELECTOR, '#webhook-url')
    webhook_input.clear()
    webhook_input.send_keys(webhook_url)

    # 6. Submit
    driver.find_element(By.CSS_SELECTOR, 'button[data-qa-id="submit"]').click()
```

---

## Section 5: Recommendations

### Option A: Adapt This Branch

| Pros | Cons |
|------|------|
| Working codebase | 60% legacy code (alert scraping, multi-screener) |
| Tested patterns | Entanglement with legacy workflow |
| Familiar structure | Significant rewrite needed |

**Effort**: 30+ hours
**Risk**: High (legacy code may interfere)

### Option B: Extract Working Code (RECOMMENDED)

| Pros | Cons |
|------|------|
| Cherry-pick proven patterns | Need to rebuild orchestration |
| Clean architecture | Requires careful extraction |
| Well-documented selectors | |

**Effort**: 15-20 hours
**Risk**: Low (well-documented patterns)

### Option C: Start Fresh

| Pros | Cons |
|------|------|
| Clean slate | Lose battle-tested patterns |
| No legacy baggage | Repeat past debugging |
| | Undocumented edge cases |

**Effort**: 40+ hours
**Risk**: High (unknown unknowns)

---

### Recommended Extraction List

**Copy Directly:**
1. Browser initialization (`open_tv.py:82-96`)
2. `change_symbol()` (`open_entry_chart.py:103-151`)
3. `change_tframe()` (`open_entry_chart.py:153-202`)
4. `save_chart_img()` (`open_entry_chart.py:204-266`)
5. `open_alert_tab()` / `open_log_tab()` (`resources/utils.py`)
6. `click_yes_in_confirm_popup()` (`resources/utils.py`)
7. `_safe_indicator_access()` (`open_tv.py:1313-1332`)
8. Logging infrastructure (`logger_setup.py`)
9. Environment configuration (`env.py`)

**Modify for Reuse:**
1. `fill_symbol_set()` - change batch size from 5 to 40/8
2. `change_settings()` - adapt for NWE/OBDIV indicators
3. `delete_all_alerts()` - keep logic, update selectors if needed

**Do Not Reuse:**
1. `get_alert()` / `post_entries()` - replaced by webhooks
2. `set_bulk_alerts()` - legacy 3-screener workflow
3. Multi-screener logic - tiered architecture uses NWE + OBDIV only

---

## Section 6: Execution Guide

### Prerequisites

```bash
# Required
- Python 3.11
- Chrome browser (any recent version)
- MongoDB accessible (local or Atlas)
- TradingView Premium account (no 2FA)

# Python dependencies
pipenv install
```

### Environment Configuration

Create `.env` file with:

```bash
# Chrome
CHROME_PROFILES_PATH=C:\Users\<User>\AppData\Local\Google\Chrome\User Data

# TradingView
TRADINGVIEW_EMAIL=your_email@example.com
TRADINGVIEW_PASSWORD=your_password

# MongoDB
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DATABASE=tte
# OR
MONGODB_PWD=your_password  # Falls back to default URI

# Discord Webhooks
CURRENCIES_WEBHOOK_NAME=Currencies
US_STOCKS_WEBHOOK_NAME=US Stocks
INDIAN_STOCKS_WEBHOOK_NAME=Indian Stocks
CRYPTO_WEBHOOK_NAME=Crypto

CURRENCIES_ENTRY_WEBHOOK_LINK=https://discord.com/api/webhooks/...
# ... other webhook links
```

### Pre-Run Checklist

1. **Close ALL Chrome windows**
   - Check Task Manager for any `chrome.exe` processes
   - End all Chrome processes

2. **Verify TradingView Layout**
   - Log into TradingView manually
   - Create layout named "PointCapital" with:
     - Order Block Screener indicator
     - Nadaraya Watson Screener indicator
     - Structure break Screener indicator
     - Trade Drawer 2 indicator
   - Save the layout

3. **Star Required Indicators**
   - All 4 indicators must be starred/favorited in TradingView
   - This allows the reupload function to find them

4. **Disable 2FA on TradingView**
   - No linked social accounts
   - Email/password login only

### Running the Application

```bash
# Activate virtual environment
pipenv shell

# Console mode
python main.py

# GUI mode
python gui.py
```

### Expected Output Sequence

1. Chrome opens to TradingView
2. Login check (auto-login if needed)
3. Layout switches to "PointCapital"
4. Alerts panel opens
5. If `START_FRESH=True`:
   - Existing alerts deleted
   - New alerts created for all symbol batches
6. Main loop starts monitoring alert log

### Success Indicators

- No errors in `app_log.log`
- Alerts appear in TradingView sidebar
- Screenshots captured (check temp folder)
- Data appears in MongoDB collection
- Facebook posts visible (if configured)

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Chrome session not created" | Chrome already running | Close all Chrome, end chrome.exe in Task Manager |
| "Products menu not found" | Not logged in | Check credentials in .env |
| "Layout not found" | Missing layout | Create "PointCapital" layout manually |
| "Indicator not found" | Not starred | Star all 4 indicators in TradingView |
| "MongoDB connection failed" | Invalid credentials | Verify MONGODB_URI or MONGODB_PWD |
| "Timeout waiting for element" | UI changed | Check selectors in EXISTING_SELENIUM_FLOW.md |

### Log Files

- `app_log.log` - Main application log
- Log is continuously trimmed to prevent overflow
- Set `REMOVE_LOG = True` in `main.py` to clear on startup

---

## Appendix: Key Constants Reference

### main.py Constants

```python
SCREENER_SHORT = "Screener"
DRAWER_SHORT = "Trade Drawer 2"
SCREENER_OB_SHORT = "Order Block Screener"
SCREENER_NW_SHORT = "Nadaraya Watson Screener"
SCREENER_SB_SHORT = "Structure break Screener"

CHART_TIMEFRAME = "4 hours"  # Default chart timeframe
INTERVAL_MINUTES = 10        # Alert restart interval
START_FRESH = False          # Delete and recreate alerts

# Screener timeframes
SCREENER_TIMEFRAME_1 = "240"  # 4 hours
SCREENER_TIMEFRAME_2 = "D"    # Daily
SCREENER_TIMEFRAME_3 = "W"    # Weekly
```

### open_tv.py Constants

```python
SYMBOL_INPUTS = 5                    # Symbols per screener batch
LAYOUT_NAME = "PointCapital"         # Required layout name
SCREENER_REUPLOAD_TIMEOUT = 15       # Seconds to wait for indicator reupload
CHROME_PROFILES_PATH = getenv("CHROME_PROFILES_PATH")
```

### env.py Constants

```python
PROFILE = "Profile 2"                          # Chrome profile directory
COLLECTION = "Point Capitalis signals"         # MongoDB collection name
```

---

## Related Documentation

- [EXISTING_SELENIUM_FLOW.md](./EXISTING_SELENIUM_FLOW.md) - Comprehensive selector inventory (50+ selectors)
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Stock Buddy technical architecture
- [CLAUDE.md](../CLAUDE.md) - Project development guidelines
