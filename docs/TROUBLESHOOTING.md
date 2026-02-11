# Troubleshooting Guide

Common issues and solutions for TTE.

## Table of Contents

1. [Browser Automation Issues](#browser-automation-issues)
2. [API and Webhook Issues](#api-and-webhook-issues)
3. [MongoDB Issues](#mongodb-issues)
4. [Alert Issues](#alert-issues)
5. [Log Analysis Guide](#log-analysis-guide)
6. [Debug Techniques](#debug-techniques)

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
2. If persistent, increase wait times in `config.py`:
   ```python
   nwe_batch_wait: int = 90  # Increase from 60
   ```
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
   del %USERPROFILE%\.wdm\drivers\chromedriver\*
   ```
3. TTE uses webdriver-manager which should auto-download matching version
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
3. Check indicator short title matches exactly:
   - NWE: `TTE NWE Screener`
   - OBDIV: `TTE OBDIV Screener`
4. Increase page load wait time
5. Save the layout after adding indicators

---

### Layout Switch Failed

**Symptoms**:
- Error: `Cannot change layout to <name>`
- Wrong layout active after switch

**Cause**: Layout doesn't exist or timing issue.

**Solutions**:
1. Verify layout exists with exact name:
   - Tiered mode: `NWE` and `OBDIV`
   - Legacy mode: `Screener` and `Exits`
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
   - `"5 minutes"`, `"15 minutes"`, `"1 hour"`, `"4 hours"`, `"1 day"`
2. Ensure timeframe button is visible and clickable
3. Check for popup dialogs blocking interaction

---

## API and Webhook Issues

### API Health Check Failed

**Symptoms**:
- Error: `API health check failed`
- Error: `Failed to connect to API`

**Solutions**:
1. Check API URL in config:
   ```bash
   STOCK_BUDDY_API_URL=https://stock-buddy-app.vercel.app/api/tte
   ```
2. Test manually:
   ```bash
   curl https://stock-buddy-app.vercel.app/api/health
   ```
3. Check if Vercel deployment is active
4. Verify network connectivity

---

### Batch Fetch Failed

**Symptoms**:
- Error: `Failed to get symbol batch`
- Empty batch returned

**Solutions**:
1. Check API stats: `python tiered_main.py --stats`
2. If rotation complete, symbols may need reset on API side
3. Verify API endpoint is returning valid JSON
4. Check `api_timeout` setting (default 30s)

---

### Webhook Not Firing

**Symptoms**:
- Alert created but no webhook received
- Hot symbols queue stays empty

**Cause**: Alert misconfigured, webhook URL wrong, or indicator not triggering.

**Solutions**:
1. Verify webhook URL is correct:
   ```
   https://stock-buddy-app.vercel.app/api/tte/nwe
   https://stock-buddy-app.vercel.app/api/tte/obdiv
   ```
2. Check alert was created successfully in TradingView
3. Verify indicator is calculating (no errors shown)
4. Increase wait time: `nwe_batch_wait` or `obdiv_batch_wait`
5. Check TradingView's webhook limit (may be rate limited)

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
   python -c "from database.local_db import Database; db = Database(); print('OK')"
   ```
4. For local MongoDB, ensure service is running

---

### Symbols Collection Empty

**Symptoms**:
- Error: `Symbols collection is empty or does not exist`
- Error: `Cannot load symbols from MongoDB`

**Solutions**:
1. Populate the `symbols` collection with symbol data
2. For tiered mode, set `SKIP_MONGODB_SYMBOLS=true` (uses API instead)
3. Verify collection name in database

---

## Alert Issues

### Failed to Create Alert

**Symptoms**:
- Error: `Failed to create webhook alert`
- Error: `Alert failed to get saved`

**Cause**: Rate limit, invalid indicator, or dialog blocked.

**Solutions**:
1. Check TradingView alert limit (varies by subscription)
2. Delete existing alerts: ensure `delete_all_alerts()` succeeds
3. Verify indicator is selected before creating alert
4. Check for error messages in alert dialog
5. Look for popup blocking the dialog

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

### Alert Duplicated

**Symptoms**:
- Two alerts created for same symbols

**Cause**: Known issue - sometimes TradingView creates duplicate alerts.

**Solutions**:
1. This is non-critical and doesn't affect functionality
2. The `delete_all_alerts()` function cleans up duplicates between cycles

---

## Combo Mode Issues

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

### Browser Session Limits

**Symptoms**:
- Error: `Session limit exceeded`
- Second browser fails to start
- TradingView shows "Maximum number of connections" warning

**Cause**: TradingView Premium allows only 2 simultaneous sessions.

**Solutions**:
1. Set `num_browsers: 2` in `combo_settings.yaml` (not higher)
2. Close any other TradingView tabs/windows
3. Ensure no other TTE instance is running

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

### Combo Webhook Not Received

**Symptoms**:
- Alerts are active but Stock Buddy shows no signals
- `tte_live_signals` collection empty

**Solutions**:
1. Verify webhook URL: `https://stock-buddy-app.vercel.app/api/tte/combo`
2. Check `COMBO_WEBHOOK_URL` in `.env`
3. Test webhook manually with curl (see API.md)
4. Check Vercel function logs for errors
5. Verify the combo indicator has active signals (check TradingView)

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
INFO - Fetched batch #6 with 20 symbols
INFO - Webhook alert created successfully for TTE NWE Screener
INFO - Marked 20 symbols as scanned
```

**Warning Signs**:
```
WARNING - API health check failed - proceeding anyway
WARNING - Failed to delete alerts, continuing anyway...
WARNING - Could not save layout
```

**Error Indicators**:
```
ERROR - Failed to sign in to TradingView
ERROR - Could not switch to NWE layout
ERROR - Failed to create webhook alert
EXCEPTION - Error occurred when...
```

### Debug Output

TTE uses both logging and print statements for debugging:

```python
print("[DEBUG] Starting phase 1...", flush=True)  # Immediate output
logger.info("Phase 1 complete")  # Written to log file
```

Look for `[DEBUG]` prefixed lines in console output for real-time debugging.

---

## Debug Techniques

### Test Individual Components

```bash
# Test configuration
python tiered_main.py --validate

# Test API
python tiered_main.py --test-api

# Test browser
python tiered_main.py --test-browser

# Test Phase 2 with mock data
python tiered_main.py --test-phase2

# Run single cycle
python tiered_main.py --single-cycle
```

### View Current Stats

```bash
python tiered_main.py --stats
```

### Clear Log File

```bash
echo "" > app_log.log
```

### Inspect Browser State

When running `--test-browser`, the browser stays open for inspection:
1. Check if correct layout is loaded
2. Verify indicators are visible
3. Check alerts sidebar
4. Inspect any error messages on indicators

### Add Debug Logging

When troubleshooting, add print statements:

```python
print(f"[DEBUG] variable_name = {variable_name}", flush=True)
```

The `flush=True` ensures immediate output.

### Check Selenium Waits

If elements aren't being found, the wait timeout may be too short:

```python
# Default is usually 10 seconds
WebDriverWait(self.driver, 15).until(...)  # Increase to 15
```

### Capture Screenshots

For debugging browser issues, add screenshot capture:

```python
self.driver.save_screenshot("debug_screenshot.png")
```

---

## Quick Fixes Checklist

- [ ] Close all Chrome windows
- [ ] Verify `.env` file has correct credentials
- [ ] Check TradingView 2FA is disabled
- [ ] Verify layouts exist with correct names
- [ ] Confirm indicators are starred/favorited
- [ ] Test MongoDB connection
- [ ] Test API connection
- [ ] Clear and check log file
- [ ] Run `--validate` to check configuration
- [ ] Try `--single-cycle` for isolated testing

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
- [Architecture](legacy/ARCHITECTURE.md) - System internals
- [API Reference](API.md) - API troubleshooting
