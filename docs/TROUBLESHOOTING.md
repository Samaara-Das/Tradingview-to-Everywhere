# Troubleshooting Guide

Common issues and solutions for TTE.

## Table of Contents

1. [Browser Automation Issues](#browser-automation-issues)
2. [Webhook Issues](#webhook-issues)
3. [MongoDB Issues](#mongodb-issues)
4. [Alert Issues](#alert-issues)
5. [GUI / Executable Issues](#gui--executable-issues)
6. [Headless Mode Issues](#headless-mode-issues)
7. [Log Analysis Guide](#log-analysis-guide)
8. [Debug Techniques](#debug-techniques)

---

## Browser Automation Issues

### Chrome Profile Locked

**Symptoms**:
- Error: `Chrome is being controlled by automated test software`
- Error: `Failed to create Chrome webdriver`
- Error: `User data directory is already in use`

**Cause**: Another Chrome process is using the profile.

**Solutions**:
1. Close all Chrome windows manually
2. TTE auto-kills Chrome on startup, but if that fails:
   ```bash
   # Windows
   taskkill /F /IM chrome.exe
   ```
3. Wait a few seconds and retry

---

### Stale Element Reference Exception

**Symptoms**:
- Error: `StaleElementReferenceException`
- Error: `Element is no longer attached to the DOM`

**Cause**: Page content changed while accessing an element.

**Solutions**:
1. TTE has built-in retry logic via `_safe_indicator_access()`
2. If persistent, increase wait times in `combo_settings.yaml`
3. Check if TradingView updated their UI

---

### ChromeDriver Version Mismatch

**Symptoms**:
- Error: `This version of ChromeDriver only supports Chrome version X`
- Error: `SessionNotCreatedException`

**Cause**: Chrome updated but cached ChromeDriver is outdated.

**Solutions**:
1. Since PR #29 (commit `675e5b9`, 2026-05-05), `_find_chromedriver()` returns `None` when Chrome's major version is known and no major-match exists in the `~/.wdm/drivers/chromedriver/win64/` cache — Selenium 4's built-in `SeleniumManager` then auto-fetches a matching driver. Most cases now self-heal on the next run.
2. If `_get_chrome_major_version()` fails (PowerShell unable to read `chrome.exe` version) the function falls back to the newest cached driver — verify Chrome is installed at the standard path `C:\Program Files\Google\Chrome\Application\chrome.exe`.
3. To force a specific driver, set `CHROMEDRIVER_PATH` env var to the absolute path of the matching `chromedriver.exe`.
4. To pre-populate the cache for the current Chrome major, the chrome-for-testing API works: `https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json` → find the latest `<MAJOR>.x` entry → unzip the `chromedriver` win64 download to `~/.wdm/drivers/chromedriver/win64/<version>/`.

---

### TradingView Login Failed

**Symptoms**:
- Error: `Failed to sign in to TradingView`
- Error: `Products menu not found`
- Stuck on login page

**Cause**: Invalid credentials, 2FA enabled, or CAPTCHA required.

**Solutions**:
1. Verify credentials in `.env`:
   ```bash
   TRADINGVIEW_EMAIL=correct@email.com
   TRADINGVIEW_PASSWORD=correct_password
   ```
2. Ensure 2FA is disabled in TradingView settings
3. Unlink any social accounts (Google, Facebook, Apple)
4. Try logging in manually to check for CAPTCHA
5. If CAPTCHA appears:
   - Log in manually in the TTE Chrome profile
   - Run TTE again (it will use the saved session)

---

### Indicator Not Found

**Symptoms**:
- Error: `Failed to find indicator <name>`
- Error: `Could not find <screener> indicator`

**Cause**: Indicator not added to layout, wrong name, or page not loaded.

**Solutions**:
1. Verify indicator is added to the correct layout
2. Verify indicator is starred/favorited
3. Check indicator short title matches `screener.shorttitle` in `combo_settings.yaml`
4. Increase page load wait time
5. Save the layout after adding indicators

---

### Layout Switch Failed

**Symptoms**:
- Error: `Cannot change layout to <name>`
- Wrong layout active after switch

**Cause**: Layout doesn't exist or timing issue.

**Solutions**:
1. Verify layout exists with exact name matching `chart.layout_name` in `combo_settings.yaml`
2. Names are case-sensitive
3. Save layouts in TradingView before running TTE
4. Check if layout dropdown is accessible

---

### Timeframe Change Failed

**Symptoms**:
- Error: `Cannot change timeframe`
- Chart shows wrong timeframe

**Solutions**:
1. Valid timeframe values include:
   - `"1 minute"`, `"5 minutes"`, `"15 minutes"`, `"1 hour"`, `"4 hours"`, `"1 day"`
2. Ensure timeframe button is visible and clickable
3. Check for popup dialogs blocking interaction

---

## Webhook Issues

### Combo Webhook Not Received

**Symptoms**:
- Alerts are active but Stock Buddy shows no signals
- `tte_live_signals` collection empty

**Solutions**:
1. Verify webhook URL: `https://stockbuddy.co/api/tte/combo`
2. Check `COMBO_WEBHOOK_URL` in `.env`
3. Test webhook manually with curl (see API.md)
4. Check Vercel function logs for errors
5. Verify the combo indicator has active signals (check TradingView)

---

## MongoDB Issues

### Connection Failed

**Symptoms**:
- Error: `Failed to connect to MongoDB`
- Error: `Authentication failed`

**Solutions**:
1. Check credentials:
   ```bash
   MONGODB_PWD=correct_password
   # OR
   MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true
   ```
2. Verify IP is whitelisted in MongoDB Atlas
3. Test connection:
   ```bash
   python -c "from tte.data.symbols import get_symbols; print('OK')"
   ```
4. For local MongoDB, ensure service is running

---

### Symbols Collection Empty

**Symptoms**:
- Error: `Symbols collection is empty or does not exist`
- Error: `Cannot load symbols from MongoDB`

**Solutions**:
1. Populate the `symbols` collection with symbol data
2. Verify collection name in database

---

## Alert Issues

### Alert Creation Failures

**Symptoms**:
- Error: `Failed to create webhook alert`
- Alert count lower than expected after setup

**Solutions**:
1. Check TradingView alert limit (Premium allows up to 400)
2. Use `--fresh` flag to delete existing alerts before setup
3. Check for TradingView screener runtime errors (red indicator)
4. Verify `combo_settings.yaml` has correct settings
5. Check `combo_progress.json` for resume capability

---

### Failed to Delete Alerts

**Symptoms**:
- Error: `Failed to delete all alerts`
- Old alerts remain active

**Solutions**:
1. Ensure alerts sidebar is open
2. Check if "Stop All" and "Delete All Inactive" buttons are accessible
3. Look for confirmation popup that needs to be clicked
4. Try manual deletion in TradingView

---

### Maintenance Restart Failures

**Symptoms**:
- Inactive alerts not being restarted
- Alert count decreasing over time

**Solutions**:
1. Verify maintenance is running (`--maintain-only` mode)
2. Check if alerts sidebar is accessible
3. Look for "Restart all inactive" option in alerts settings
4. If alerts are erroring repeatedly, check Pine Script for runtime issues

---

### Browser Issues

**Symptoms**:
- Browser fails to start
- TradingView shows "Maximum number of connections" warning
- Headless mode not working

**Cause**: Another Chrome/TTE instance may be running, or headless mode incompatibility.

**Solutions**:
1. Close any other TradingView tabs/windows
2. Ensure no other TTE instance is running
3. If headless mode fails, set `headless: false` in `combo_settings.yaml` to debug visually
4. TTE uses a single browser instance -- no session limit concerns

---

## GUI / Executable Issues

### TTE.exe Won't Start

**Symptoms**:
- Double-click `dist/TTE.exe` but nothing happens
- Error about missing DLL or module

**Solutions**:
1. Run from command line to see error output: `dist\TTE.exe`
2. Ensure `combo_settings.yaml` is in the project root (not inside `dist/`)
3. Check Windows Defender hasn't quarantined the exe
4. Try running `python tte_gui.py` directly instead

### GUI Can't Find Settings File

**Symptoms**:
- GUI shows default/empty settings
- Changes don't persist

**Solutions**:
1. Ensure `combo_settings.yaml` exists in the project root
2. Check file permissions
3. The GUI reads/writes `combo_settings.yaml` relative to the working directory

---

## Headless Mode Issues

### Headless Chrome Crashes

**Symptoms**:
- Error: `Chrome failed to start` in headless mode
- Process exits silently

**Solutions**:
1. Set `headless: false` in `combo_settings.yaml` to debug visually
2. Ensure Chrome is updated to latest version
3. Check available system memory (headless still requires ~500MB)
4. Try running `python combo_main.py` from CLI instead of GUI

### Elements Not Found in Headless Mode

**Symptoms**:
- Errors about elements not clickable or not found
- Works in visible mode but fails headless

**Solutions**:
1. Headless Chrome uses a default viewport -- some elements may be off-screen
2. Set `headless: false` temporarily to identify the issue
3. Report the specific element/step that fails

---

## Log Analysis Guide

### Log File Location

```
app_log.log
```

### Log Levels

| Level | Usage |
|-------|-------|
| DEBUG | Detailed debugging info |
| INFO | Normal operation messages |
| WARNING | Non-critical issues |
| ERROR | Failures that affect operation |
| EXCEPTION | Errors with stack traces |

### Key Log Patterns

**Successful Operations**:
```
INFO - Successfully signed in to TradingView
INFO - Webhook alert created successfully
INFO - Restarting inactive alerts...
```

**Warning Signs**:
```
WARNING - Could not save layout
WARNING - Indicator loading timeout
```

**Error Indicators**:
```
ERROR - Failed to sign in to TradingView
ERROR - Failed to create webhook alert
EXCEPTION - Error occurred when...
```

---

## Debug Techniques

### Test Individual Components

```bash
# Validate configuration
python combo_main.py --validate

# Run setup only (create alerts, then exit)
python combo_main.py --setup-only

# Run maintenance only
python combo_main.py --maintain-only
```

### Inspect Browser State

When running with `headless: false`, the browser stays visible for inspection:
1. Check if correct layout is loaded
2. Verify indicators are visible
3. Check alerts sidebar
4. Inspect any error messages on indicators

### Capture Screenshots

For debugging browser issues, the driver can capture screenshots:

```python
self.driver.save_screenshot("debug_screenshot.png")
```

### Check Selenium Waits

If elements aren't being found, the wait timeout may be too short:

```python
# Default is usually 10 seconds
WebDriverWait(self.driver, 15).until(...)  # Increase to 15
```

---

## TradingView UI Changes

### Alert Dialog Redesign

**Symptoms**:
- Error: `Failed to create webhook alert`
- Alert creation hangs or times out

**Cause**: TradingView periodically redesigns their UI, breaking Selenium selectors.

**Solutions**:
1. Check if TradingView updated their alert dialog (tabs vs sub-dialogs)
2. Verify selectors in `tte/browser/tradingview.py` `create_webhook_alert()` match current UI
3. Run with `headless: false` to visually inspect the dialog
4. Check `.claude/task-context.md` for the latest verified selector patterns

### Timeframe Dropdown Redesign

**Symptoms**:
- Timeframe change fails or selects wrong timeframe
- Error about timeframe section not found

**Cause**: TradingView changed from flat dropdown to collapsible sections.

**Solutions**:
1. Check `tte/browser/chart.py` for `_expand_timeframe_section()` logic
2. Verify section headers match (Ticks/Seconds/Minutes/Hours/Days/Ranges)
3. Run with `headless: false` to debug visually

---

## Known Issues

### Screener Gear Click Intercepted (Resolved — PR #28, 2026-05-05)

**Symptoms** (identical on Windows AND Linux/Docker):
- `change_settings()` in `tte/browser/tradingview.py:599` timed out waiting for the screener legend's gear icon `button[data-qa-id="legend-settings-action"]`.
- Hit on every fresh-Chrome run; intermittent on warm sessions.

**Root cause**: `WebDriverWait(screener, 15)` was constructed with the screener WebElement (returned by `_safe_indicator_access`) instead of `self.driver`. `WebDriverWait` scopes its locator search to its first argument, so the search was restricted to the legend container's DOM subtree — but `legend-settings-action` renders elsewhere in the DOM after the legend opens. The wait could never resolve.

**Fix** (PR #28, commit `7e5cf20`): one-line change to `WebDriverWait(self.driver, 15)`. Validated end-to-end on Windows on 2026-05-05: `change_settings()` succeeds, alerts created cleanly.

**Why prior overlay-retry fix didn't catch this**: commit `60cad59` added the lines 576-598 retry block (native click ×3 → overlay-dismiss → JS click) which improved the *legend click* step but left line 599's wrong-reference WebDriverWait untouched.

---

## Quick Fixes Checklist

- [ ] Close all Chrome windows
- [ ] Verify `.env` file has correct credentials
- [ ] Check TradingView 2FA is disabled
- [ ] Verify "Screener" layout exists with correct name
- [ ] Confirm TTE Screener indicator is starred/favorited
- [ ] Test MongoDB connection
- [ ] Clear and check log file
- [ ] Run `--validate` to check configuration

---

## Getting Help

If issues persist:

1. Collect relevant log output
2. Note the exact error message
3. Record steps to reproduce
4. Check if TradingView UI has changed
5. Create an issue with full details

---

## See Also

- [Setup Guide](SETUP.md) - Configuration reference
- [Combo Architecture](combo/ARCHITECTURE.md) - System internals
- [API Reference](API.md) - API troubleshooting
