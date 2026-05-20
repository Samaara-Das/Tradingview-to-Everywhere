# Troubleshooting Guide

Common issues and solutions for TTE.

## Table of Contents

1. [Browser Automation Issues](#browser-automation-issues)
2. [Webhook Issues](#webhook-issues)
3. [MongoDB Issues](#mongodb-issues)
4. [Alert Issues](#alert-issues)
5. [Alert Persistence Failures (PR #48)](#alert-persistence-failures-pr-48)
6. [Multi-Instance Issues](#multi-instance-issues)
7. [Snapshot Worker Issues](#snapshot-worker-issues)
8. [GUI / Executable Issues](#gui--executable-issues)
9. [Headless Mode Issues](#headless-mode-issues)
10. [Log Analysis Guide](#log-analysis-guide)
11. [Debug Techniques](#debug-techniques)

---

## Alert Persistence Failures (PR #48)

### "Alert NOT persisted on TV: sidebar top unchanged"

**Symptoms**:
- Log: `Alert NOT persisted on TV for Screener V2: sidebar top unchanged ...`
- `create_webhook_alert` returns `(False, "not_persisted")`
- Selenium's Create click APPEARED to succeed (no error popup in alert dialog)
- But the new alert isn't on the chart sidebar

**Cause**: TV's backend silently dropped the alert. Triggered by:
1. **1000-Technicals cap hit** — most common (see next section).
2. **2FA not enabled on the account** — TV blocks webhook creation with a "Protect your data" modal that the alert dialog doesn't surface as an error.
3. **Symbol not on the account's data plan** — TV rejects with no visible message.
4. **Session glitch / chart in recovery state**.

**Solutions**:
1. Run `tools/investigate_alert_cap.py` (read-only) to see TV's own counters via the alerts-settings menu.
2. Verify the TV account has 2FA enabled — every TV account TTE drives MUST have 2FA (`TRADINGVIEW_TOTP_SECRET` in `.env.tte.<N>`).
3. If only 1-3 batches `not_persisted` out of hundreds, it's noise — maintenance loop will retry. If 100% of batches fail, halt and investigate.
4. Code-side fix already in place: `tte/main.py` SKIPS the reupload retry path on `not_persisted` (would otherwise destroy the chart by removing the indicator then failing to re-add).

### "Error in alert dialog: error! alert saving failed. please, try again"

**Symptoms**:
- `create_webhook_alert` reports the dialog error text
- Every supplementary `--symbols` batch rejected

**Cause**: TV's Technicals alert cap is exactly 1000 active alerts per account. Inactive/stopped alerts ALSO count toward the cap.

**Solutions**:
1. Check via `tools/investigate_alert_cap.py` — dumps alerts-settings menu values like `Active 1000 / Inactive N` and `Technicals X/1000`.
2. Delete unwanted alerts (typically `Stopped — Calculation error` ones on illiquid OTC symbols).
3. When planning instance partitions, budget at most ~990 alerts per TV account.

See `memory/decision_tv_alert_cap_is_hard_1000.md` for full discovery details.

---

## Multi-Instance Issues

### Chart legend shows wrong `tte-N` instance label

**Symptoms**:
- Alerts being created with wrong `"instance"` value in payload
- Chart legend reads `Screener V2 (tte-1, ...)` on what should be `tte-2`'s chart

**Cause**: The Pine `Instance ID` input defaults to `tte-1`. After a `reupload_indicator` event the fresh copy from Favorites uses that default. As of PR #49, `_set_indicator_instance_id` self-detects mismatches: it polls the legend after submit and returns False if the rendered legend doesn't contain the target instance ID OR if any legend item still shows the stale `tte-1` default. On failure, `reupload_indicator` returns False so the caller halts rather than continuing to silently mis-tag alerts. The old silent-failure mode (PR #48-era code) was the root cause of the 2026-05-20 regression on tte-2.

**Solutions**:
1. **Programmatic**: stop the affected container, run `tools/fix_instance_id.py` (uses `Browser._set_indicator_instance_id` against the running chart and `Ctrl+S` to persist), then `--fresh` restart to recreate alerts with the correct tag.
2. **Manual**: open the TV chart in a real browser, double-click `Screener V2` → Instance group → set Instance ID → click the layout-save icon (not just Ctrl+S — the floppy in the top toolbar). Refresh and confirm the legend persists.

Existing alerts created with the wrong instance value cannot be re-tagged — Pine inputs are snapshotted at alert creation. Delete + recreate via `--fresh` to fix.

### Stale `--fresh` flag wiped alerts

**Symptoms**: `docker compose up -d tte-N` deletes all alerts on that account and starts a 1000-batch setup from scratch when you expected maintain-only.

**Cause**: A previous `--fresh` run left the compose `command:` line stuck on `--fresh`. The next `up -d` re-runs setup.

**Solution**: ALWAYS `grep 'command:' /opt/stockbuddy/docker-compose.yml` before `docker compose up -d`. If you see `--fresh` and you didn't intend a fresh run, `sed`-flip it to `--maintain-only` first. See `memory/feedback_check_compose_command_before_restart.md`.

---

## Snapshot Worker Issues

### "Trade Drawer 'Trade Drawer V2' not found on chart"

**Symptoms**:
- Snapshot worker logs `Failed to set Trade Drawer settings` on every setup
- Snapshots in Stock Buddy show no TP/SL drawing or fail to render

**Cause**: The `Trade Drawer V2` Pine source isn't saved + favorited + on the Snapshot layout for this TV account.

**Solutions**:
1. On the TV account in question: Pine Editor → New blank → paste `Pine Script Code/Trade Drawer V2.txt` → Ctrl+S → name `Trade Drawer V2` → Indicators → My Scripts → ⭐ favorite it.
2. Run `tools/add_trade_drawer.py` (with the right `TTE_INSTANCE` env) to switch to Snapshot layout, click Trade Drawer V2 from Favorites, and save the layout.
3. Verify via `tools/favorite_trade_drawer.py` that `Trade Drawer V2` appears in the favorites dropdown.

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

**Cause**: Invalid credentials, 2FA blocking with no TOTP secret configured, or CAPTCHA required.

**Solutions**:
1. Verify credentials in `.env`:
   ```bash
   TRADINGVIEW_EMAIL=correct@email.com
   TRADINGVIEW_PASSWORD=correct_password
   ```
2. If TradingView is forcing 2FA, set `TRADINGVIEW_TOTP_SECRET` (base32) in `.env`. PR #40's `_maybe_auto_submit_totp()` will submit codes automatically. If the secret is empty, the function no-ops and you'll need to enter the code manually inside the Selenium-driven Chrome window.
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

### Snapshot Renderer Stalls (Resolved — WS-0, 2026-05-18)

**Symptoms** (chronic since at least 2026-05-15, possibly earlier):
- `tte/snapshot_worker - ERROR - Failed to change symbol to <SYMBOL>` in `app_log.log`, with the underlying exception `HTTPConnectionPool(host='localhost', port=41623): Read timed out. (read timeout=120)`.
- Not specific to any exchange — hit on NSE (TATAELXSI, HUDCO, INFY) and NYSE/NASDAQ (BRO, ALB, AJG, CME) symbols.
- ~30% per-poll failure rate on the snapshot pipeline. Webhook + maintenance unaffected.

**Root cause**: chrome's headless renderer sustains ~93-140% CPU on the production `tte:phase4` image even right after a fresh chrome restart — not a memory leak, but a steady-state load from TV's WebSocket data streaming + Trade Drawer V2 recompute + headless software rasterization. Devtools queries respond in 1ms (V8 worker threads) but Selenium clicks queue against TV's saturated main thread. Occasionally a chain of Selenium ops in `_take_snapshot` accumulates enough wait time to exceed chromedriver's default 120s urllib3 read timeout, surfacing as the `Read timed out` error. Memory: 300 MB JS heap of 4 GB limit — fine.

**Fix** (WS-0): four small, additive changes:

1. **Lower chromedriver read timeout 120s → 45s** in `tte/browser/tradingview.py` Browser.__init__ (via `command_executor._client_config.timeout = 45`). Fails fast on stalls; recovers 75s of wall-time per stall.
2. **Retry-on-`Read timed out` in `change_symbol`** (`tte/browser/chart.py`). On stall: `driver.refresh()`, sleep 3s, retry once. Recursion capped at 2 attempts.
3. **Distinguish renderer stalls from other failures** in `tte/snapshot_worker.py` `_take_snapshot`. Time the `change_symbol` call; if it returns False after ≥ 30s, POST `error="renderer_stall"` (vs. `"Failed to change symbol"` for fast failures like unknown symbol). Per-symbol consecutive failure counter; skip to next snapshot after 2 in a row on the same name.
4. **Periodic chart recycle** every 30 snapshots in `process_pending_snapshots`. Calls `driver.refresh()` + 5s sleep, then re-runs per-cycle setup (bar style, bars-to-right, legend). Flushes accumulated DOM/tooltip state cheaply.

Diagnostic patch from WS-0 (added `--remote-allow-origins=*` to chrome args) is included in the same commit so future rebuilds keep it — required by chrome 111+ for external WebSocket DevTools attach, used by future health probes.

---

### TradingView Session Disconnected Mid-Run (Resolved — PR #39, 2026-05-14)

**Symptoms**:
- Snapshot worker or maintenance loop logs page-not-found or chart-missing errors.
- The TradingView tab shows the sign-in page or a "session disconnected" notice instead of the chart.

**Cause**: A parallel login on another device or IP invalidated the VPS-side session. Before PR #39, the maintenance loop continued operating against the logged-out page and the snapshot pipeline silently 100%-failed (2026-05-08 → 2026-05-14 blackout).

**Fix** (PR #39, commit `40311f7`): `tte/browser/tradingview.py` adds `is_chart_layout_loaded()` and `ensure_chart_layout_loaded()`. Each maintenance round calls `ensure_chart_layout_loaded()` first; if the chart is missing it re-runs `setup_tv()` (full login + layout restore) before touching alerts. No user action is required unless `TRADINGVIEW_TOTP_SECRET` is unset and TV is asking for a code — in that case see the "TradingView Login Failed" section above.

---

### TOTP Code Rejected (PR #40, 2026-05-15)

**Symptoms**:
- Log line `Auto-submitted TOTP code` appears, but the next selector wait times out.
- Login page still showing the 6-digit input after submit.

**Cause**: Container clock skew, wrong base32 secret, or TV silently rotated the secret.

**Solutions**:
1. Verify the container clock matches a public NTP source within a few seconds (`docker exec tte-1 date`).
2. Re-scan the QR code in TV's 2FA setup and confirm the base32 secret in `.env` is byte-identical (no surrounding quotes, no whitespace).
3. If the secret was added long ago, regenerate it via TV Settings → Security → 2FA → reset.
4. Inert path: clear `TRADINGVIEW_TOTP_SECRET` and rely on backup codes (see `.claude/credentials-and-2fa.md`).

---

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
- [ ] If TV forces 2FA, confirm `TRADINGVIEW_TOTP_SECRET` is set (or 2FA is off)
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
