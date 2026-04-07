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
1. Update Chrome to latest version
2. Delete cached ChromeDriver:
   ```bash
   # Windows - find and delete
   del %USERPROFILE%\.wdm\drivers\chromedriver\win64\*
   ```
3. TTE uses Selenium 4's built-in driver management (`_find_chromedriver()` in `tradingview.py`) which checks `~/.wdm/drivers/chromedriver/` for cached drivers and falls back to Selenium's auto-discovery
4. Restart TTE

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
- New tab opens instead of switching layout

**Cause**: Layout doesn't exist, timing issue, or TradingView UI changed.

**Solutions**:
1. Verify layout exists with exact name matching `chart.layout_name` in `combo_settings.yaml`
2. Names are case-sensitive
3. Save layouts in TradingView before running TTE
4. Check if layout dropdown is accessible
5. Non-current layouts in TradingView's dropdown are `<a target="_blank">` links — TTE navigates via `driver.get(href)` instead of clicking (since clicking opens a new tab). If this fails, the layout item XPath selector may need updating.
6. Layout items use `data-qa-id="save-load-menu-item-recent"` — the XPath is scoped to these items only

---

### Timeframe Change Failed

**Symptoms**:
- Error: `Cannot change timeframe`
- Chart shows wrong timeframe
- Timeframe item not found in dropdown

**Cause**: TradingView's timeframe dropdown uses collapsible sections (Ticks/Seconds/Minutes/Hours/Days/Ranges). The target section must be expanded before clicking the item.

**Solutions**:
1. Valid timeframe values include:
   - `"45 seconds"`, `"1 minute"`, `"5 minutes"`, `"15 minutes"`, `"1 hour"`, `"4 hours"`, `"1 day"`
2. Ensure timeframe button is visible and clickable
3. Check for popup dialogs blocking interaction
4. TTE auto-expands the correct section (e.g., "Seconds" for "45 seconds") via `_expand_timeframe_section()` in `chart.py`
5. If a section is collapsed (`aria-expanded="false"`), items inside it have `aria-hidden="true"` and won't be found

---

### Alert Creation Hangs / Webhook Tab Not Found

**Symptoms**:
- Alert creation hangs indefinitely
- Error: `alert-dialog-tabs__notifications` not found
- Webhook checkbox not found

**Cause**: TradingView redesigned the alert dialog (2026-04). The old tabbed layout (Settings tab + Notifications tab) was replaced with a main dialog + a separate notifications sub-dialog accessed via a "Webhook >" button.

**Solutions**:
1. TTE uses the new two-dialog flow:
   - Click `button[data-qa-id="alert-notifications-button"]` to open notifications sub-dialog
   - Wait for `div[data-qa-id="alerts-notifications-edit-dialog"]`
   - Configure webhook in sub-dialog, click Apply
   - Return to main dialog, click Create
2. If selectors have changed again, inspect the alert dialog in Chrome DevTools
3. Key selectors (verified 2026-04-07):
   - Main dialog: `div[data-qa-id="alerts-create-edit-dialog"]`
   - Webhook button: `button[data-qa-id="alert-notifications-button"]`
   - Notifications sub-dialog: `div[data-qa-id="alerts-notifications-edit-dialog"]`
   - Webhook checkbox: `label[data-qa-id="webhook"] input[type="checkbox"]`
   - Webhook URL input: `input#webhook-url`

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
