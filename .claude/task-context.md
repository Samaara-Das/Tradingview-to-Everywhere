# Task Context Tracker

**Last Updated**: 2026-02-10
**Current Task**: Production run in progress — 258 batches across 2 parallel browsers (Task #84)
**Last Session**: Fixed parallel browser mode (5 test runs), removed dry run limit, launched production
**Active Branch**: `combo-architecture`

---

## Task Progress Summary

**Parallel Browser Mode - COMPLETE** ✅:
| ID | Task | Status |
|----|------|--------|
| 80 | Test parallel browser mode | **completed** ✅ (2 browsers, TV limits to 2) |
| 82 | Update combo_settings.yaml to use multiple browsers | **completed** ✅ |
| 83 | Run dry run with 12 symbols (3 batches) | **completed** ✅ |
| 84 | **Run full production test with 258 batches** | **IN PROGRESS** 🔄 |
| 85 | Analyze results and document findings | pending |

**Combo Implementation - COMPLETE** ✅:
| ID | Task | Status |
|----|------|--------|
| 55-59 | Core combo mode (open_tv.py, combo_config, combo_main, api_client, env) | **completed** ✅ |
| 63-66 | Multi-browser architecture + symbol change fix | **completed** ✅ |
| 68-72 | Error recovery (is_no_error, reupload_indicator, retries) | **completed** ✅ |
| 73-79 | Error handling tests + bug fixes | **completed** ✅ |

**Screener Work - COMPLETE** ✅:
| ID | Task | Status |
|----|------|--------|
| 44-54 | All screener validation, testing, variable renaming | **completed** ✅ |

**Deferred / Future**:
| ID | Task | Status | Notes |
|----|------|--------|-------|
| 22 | Test webhook payload and trigger frequency | pending | After combo live |
| 24-31 | Orchestrator rewrite tasks | pending | May not be needed (combo_main.py works) |
| 32-38 | Stock Buddy API tasks | pending | Next major milestone |
| 60-62 | Dashboard and live testing | pending | After API built |
| 67 | Failed batch retry logic | pending | Phase 2 enhancement |
| 81 | Headless Chrome mode | pending | Future optimization |

**Completed Count**: 39 tasks | **In Progress**: 1 | **Pending**: 15

---

## Session History

### Session: 2026-02-10 (Parallel Browser Mode — 5 Test Runs to Production)

**Goal**: Get parallel browser mode working for combo alert creation (reduce setup from ~6.6h to ~3.3h)

**Test Run 1** (pre-session): All browsers shared same Chrome profile. `taskkill /F /IM chrome.exe` in `Browser.__init__()` killed previously-opened browsers.

**Test Run 2** (pre-session): Added separate `user_data_dir` per browser, but:
- All 3 browsers got remote debugging port 9226 (derived from profile name "Profile 4")
- Browser 0's window closed when Browser 1 initialized
- Overlay dialog blocked clicks on Browser 1

**Test Run 3** — Fixed port collisions:
- Added `browser_id` param to `Browser.__init__()`
- Remote debugging port: `9222 + browser_id` (not profile number)
- ChromeDriver service port: `9515 + browser_id`
- Added ESC key press after `setup_tv()` to dismiss overlays
- Added session copy (`shutil.copytree`) from primary TTE profile
- **Result**: Browser 0 worked, Browser 1 failed (session copy didn't preserve login, needed 2FA), Browser 2 crashed (`WinError 32` — files locked by Browser 0)

**Test Run 4** — Fixed session copy timing + 2FA:
- Moved `shutil.copytree` to before any browser launches (no file locks)
- Always fresh copy (delete existing stale dirs first)
- Increased `sign_in()` timeout from 7s to 60s for manual 2FA
- Wrapped automated login in try/except (falls through to 60s manual wait)
- **Result**: Browsers 1&2 still needed sign-in but crashed because `sign_in()` threw unhandled exception when email form wasn't found (2FA page shown instead)

**Test Run 5** — Fixed sign_in crash + reduced to 2 browsers:
- Wrapped entire email/password/submit block in try/except
- If automated login fails, falls through to 60s wait for manual sign-in
- Reduced `num_browsers: 3` → `2` (TradingView limits simultaneous sessions to 2)
- Removed session copy logic entirely (doesn't preserve login anyway)
- **Result**: SUCCESS! Both browsers logged in automatically, created alerts in parallel. 2/3 batches completed before user hit Ctrl+C.

**Production Launch** — Removed dry run limit:
- Added targeted Chrome process kill (PowerShell `Get-CimInstance` to find Chrome with "TTE" in command line)
- Initial attempt used `wmic` which doesn't exist on user's system → switched to PowerShell
- Removed 12-symbol dry run limit
- **Result**: 258 batches, 2 browsers, production run started successfully

**Files Modified**:
- `open_tv.py` — `Browser.__init__()`: added `browser_id` param, unique debug/service ports, targeted TTE Chrome kill, ESC dismiss overlays, `sign_in()` 60s timeout with try/except
- `combo_main.py` — Removed session copy, removed dry run limit
- `combo_settings.yaml` — `num_browsers: 2`

**Key Bugs Fixed This Session**:
1. ChromeDriver port collision (all browsers fought for default port)
2. Remote debugging port collision (all derived from "Profile 4" = 9226)
3. `shutil.copytree` WinError 32 (Chrome locks profile files while running)
4. `sign_in()` crash on 2FA page (unhandled exception finding email form)
5. TradingView 2-session limit (reduced from 3 to 2 browsers)
6. `wmic` not found on system (replaced with PowerShell `Get-CimInstance`)

---

### Session: 2026-02-10 (reupload_indicator() Selector Fixes)

**Goal**: Fix `reupload_indicator()` with updated TradingView selectors

**Fixes**:
- Delete button: `data-name="legend-delete-action"` → `data-qa-id="legend-delete-action"`
- Menu container: `data-name="menu-inner"` → `data-qa-id="menu-inner"`
- Indicator reload wait: Replaced manual selector with `_safe_indicator_access()`
- **Commit**: `43f94f4`

---

### Session: 2026-02-09 (Screener Cleanup & Timeframe Renaming)

- Commented out debug table for production (Task #52)
- Created `combo-architecture` branch (Task #53)
- Renamed legacy timeframe variables: `TF_H4`→`TF_1H`, `TF_D1`→`TF_H4`, `TF_W1`→`TF_D1` (Task #54)
- Uploaded screener versions to Google Drive (Task #23)
- Fixed OB/FVG gap conditions and divergence thresholds

---

### Earlier Sessions (2026-02-03 to 2026-02-09)

See git history for details. Key milestones:
- Pine Script screener consolidated (NWE + OB/FVG + DIV)
- NWE signal detection bugs fixed (timestamps, disappearing signals, chart symbol dependency)
- Divergence detection verified working
- Tiered orchestrator built and tested (Phase 1 NWE working, Phase 2 OBDIV timeout)
- Hot symbol expiration system implemented
- Browser login and webhook creation automation working

---

## Important Decisions Made

1. **Architecture**: Combo screener (single indicator) over separate screeners — fewer alert cycles, simpler
2. **Webhook destination**: Stock Buddy API (Vercel) — existing pipeline
3. **4 symbol hard limit**: More causes TradingView memory/runtime errors
4. **2 parallel browsers**: TradingView limits to 2 simultaneous sessions (not 3)
5. **No session copying**: Chrome invalidates cookies across user-data-dirs. Manual 2FA needed for secondary browsers on fresh runs, but sessions persist after first login
6. **Signal levels calculated server-side**: Screener sends raw signals, Stock Buddy calculates levels
7. **Targeted Chrome kill**: Only kill Chrome processes using TTE user-data-dirs, preserve regular Chrome

---

## Key Reference Files

| File | Purpose |
|------|---------|
| `combo_main.py` | Combo mode entry point — parallel browser alert creation |
| `combo_config.py` | Combo configuration from YAML |
| `combo_settings.yaml` | All combo settings (batch_size=4, num_browsers=2, etc.) |
| `open_tv.py` | Browser class — Selenium automation, sign_in, setup_tv, create_webhook_alert |
| `Pine Script Code/TTE Screener.txt` | Production combo screener |
| `docs/ARCHITECTURE v2.md` | Combo architecture docs |
| `docs/COMBO_IMPLEMENTATION.md` | Implementation details |

---

## Verified Patterns

### Parallel Browser Port Mapping
| Browser | Debug Port | ChromeDriver Port | User Data Dir |
|---------|-----------|-------------------|---------------|
| 0 | 9222 | 9515 | `TTE/` |
| 1 | 9223 | 9516 | `TTE_browser1/` |

### Targeted TTE Chrome Kill (PowerShell)
```python
ps_cmd = (
    "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
    "Where-Object { $_.CommandLine -match 'TTE' } | "
    "Select-Object -ExpandProperty ProcessId"
)
```

### Sign-in with 2FA Fallback
```python
try:
    # Automated email/password login
    WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.NAME, "Email"))).click()
    # ... fill credentials, click sign in ...
except Exception:
    logger.warning("Automated login failed. Waiting for manual sign-in...")

# Always wait 60s for sign-in (handles 2FA, manual login, etc.)
WebDriverWait(self.driver, 60).until(EC.presence_of_element_located(products_menu))
```

### TradingView Webhook Alert Creation
```
1. Click indicator on chart to select it
2. Click + button to open alert dialog
3. Click Notifications tab: button[id="alert-dialog-tabs__notifications"]
4. Wait for webhook checkbox: input[data-qa-id="webhook"]
5. Ensure checkbox is checked
6. Fill webhook URL: input#webhook-url (Ctrl+A, Backspace, type URL)
7. Click Create: button[data-qa-id="submit"]
```

### Combo Mode Settings
```yaml
batch_size: 4          # Hard limit
num_browsers: 2        # TradingView limit
creation_delay: 3.0
maintenance_interval: 200
```

---

## Test Commands

```bash
# Run combo mode (production)
python combo_main.py

# Run with fresh start (delete existing alerts)
python combo_main.py --fresh

# Validate config only
python combo_main.py --validate

# Setup only (no maintenance)
python combo_main.py --setup-only

# Maintenance only (skip setup)
python combo_main.py --maintain-only
```

---

## Next Steps

1. **Wait for production run to complete** — 258 batches across 2 browsers (~3.3h)
2. **Analyze results** (Task #85) — Check success rate, timing, errors
3. **Build Stock Buddy API** (Tasks #32-38) — Webhook endpoint, signal storage, symbol management
4. **Test end-to-end flow** — TradingView alerts → Stock Buddy API → MongoDB → Dashboard
