# Task Context Tracker

**Last Updated**: 2026-02-11
**Current Task**: GUI redesigned, single browser mode. Next: Run TTE fresh (#109).
**Last Session**: Switched to single browser, reduced sleeps, added headless mode, built GUI exe
**Active Branch**: `combo-architecture`

---

## Task Progress Summary

**Completed Count**: 96 tasks | **In Progress**: 0 | **Pending**: 1 task

**Pending Tasks**:
| ID | Task | Status | Notes |
|----|------|--------|-------|
| 109 | Run TTE fresh to create alerts for all 1,032 symbols | pending | Manual step — `python combo_main.py --setup-only --fresh` |

---

## Session History

### Session: 2026-02-11 (Single Browser + Sleep Optimization + GUI — Tasks #81, #86, #90)

**Goal**: Optimize browser performance, add headless mode, build GUI executable

**Chronological changes**:

1. **Added debug logs to `delete_all_alerts()`** (`open_tv.py`) and `click_yes_in_confirm_popup()` (`resources/utils.py`) to diagnose alert deletion issues. Included `dump_dropdown_items()` to log all menu items with indices, `find_menu_item()` for text-based lookup (instead of hardcoded indices), `count_alerts()` for verification at each step, and popup result checking.

2. **Removed debug logs** — Alert deletion was working fine, user confirmed. Reverted both files to clean state. Also cleaned up debug prints from `setup_tv()`.

3. **Switched from parallel to single browser** — Parallel browsers were still slow despite optimizations. Rewrote `combo_main.py`:
   - Removed `ThreadPoolExecutor`, `concurrent.futures`, `assign_batches_to_browsers()`
   - Replaced `create_browser_instance(browser_id, ...)` with simpler `create_browser(config, args)`
   - `run_alert_creation()` runs sequentially on one browser (no `browser_id` param)
   - `main()` simplified: no batch splitting, no parallel init, no result aggregation
   - Maintenance reuses the same browser instead of creating a new one
   - Removed `num_browsers` from `combo_config.py`, `combo_settings.yaml`, `tte_gui.py`, `.env`, `CLAUDE.md`

4. **Sleep optimizations** (from earlier plan, applied in this session):
   - `get_indicator()` sleep: 3s → 0.5s (`open_tv.py:1948`) — WebDriverWait already handles waiting
   - `change_settings()` post-submit sleep: 2s → 0.5s (`open_tv.py:864`)
   - `change_symbol()` sleep: 2s → 1s (`open_entry_chart.py:187`)
   - Added Chrome anti-throttling flags: `--disable-background-timer-throttling`, `--disable-renderer-backgrounding`, `--disable-backgrounding-occluded-windows`

5. **Headless Chrome mode** (#81):
   - Added `headless: bool` to `combo_config.py` and `combo_settings.yaml`
   - Added `headless: bool = False` param to `Browser.__init__()` in `open_tv.py`
   - Chrome flags: `--headless=new`, `--window-size=1920,1080`
   - Guarded `maximize_window()` in `open_page()` and `sign_in()`

6. **Built TTE GUI** (#86):
   - Created `tte_gui.py` — tkinter GUI with settings editor, Start/Stop, real-time log streaming
   - Built `dist/TTE.exe` via `pyinstaller --name TTE --onefile --windowed tte_gui.py`
   - Initial design: dark theme, all settings editable, subprocess management with CTRL_BREAK_EVENT

7. **Redesigned GUI** — Modern look with:
   - Deep navy color scheme (`#1a1b2e`) with blue-purple accent (`#6c7bff`)
   - Card-based settings layout with separators, labels above inputs
   - Status dot indicator in header with color-coded states
   - Hover effects on buttons, styled combobox dropdowns
   - "Clear" link for log output
   - Rebuilt exe successfully

**Commits**:
- `4b9b246` — Switch to single browser, reduce sleeps, add headless mode and GUI

**Key decision**: Abandoned parallel browsers — single browser is simpler and TradingView throttles parallel sessions regardless of Chrome flags.

---

### Session: 2026-02-11 (Maintenance Loop Improvements — Tasks #106, #107)

**Goal**: Add alert log clearing and improve the maintenance loop in combo_main.py

**Changes to `combo_main.py`**:
1. Added `clear_alert_log(driver)` — opens log tab, clicks clear button, confirms dialog
2. Updated `run_maintenance()` — now does: page refresh → restart inactive alerts → clear alert log
3. Fixed `restart_inactive_alerts()` — handle disabled "Restart all inactive" button gracefully

**Commit**: `75036c9`

---

### Session: 2026-02-11 (Documentation Update — Task #108)

Updated all TTE and Stock Buddy documentation (16 files) to reflect combo mode in production.

**Commit**: `0c89589`

---

### Earlier Sessions (2026-02-10 — 2026-02-11)

- **Combo Signal Grid** (#99-104, #60): Replaced /tte dashboard with paginated signal grid in Stock Buddy
- **Stock Buddy Combo API** (#32-38, #91-98): Built webhook endpoints + dashboard UI
- **Production alerts**: 352 alerts, batch_size=3, 1-min chart, graceful shutdown
- **Pine Script**: Screener development, NWE signal detection, timeframe fixes
- **Error recovery**: is_no_error(), reupload_indicator(), batch retry logic

---

## Important Decisions Made

1. **Architecture**: Combo screener (single indicator) over separate screeners
2. **Webhook destination**: Stock Buddy API (Vercel) at `/api/tte/combo`
3. **tte_live_signals collection**: One document per symbol (`_id = symbol`), upserted on each webhook
4. **3 symbol batch limit**: Reduced from 4 for 1-min chart performance
5. **1-minute chart timeframe**: Fires once per minute (rate limit safe)
6. **Single browser**: Parallel browsers abandoned — slower due to TradingView throttling
7. **Paginated grid over basic table**: Better UX for 483+ symbols
8. **Main page integration**: Signals as third nav tab (not separate route)
9. **Server-side pagination & filtering**: Better performance for large datasets
10. **Doc renames**: PRD.md → legacy/PRD.md, ARCHITECTURE v2.md → combo/ARCHITECTURE.md

---

## Key Reference Files

### TTE Project
| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project instructions (updated for single browser) |
| `combo_main.py` | Combo mode entry point (single browser) |
| `combo_config.py` | Combo configuration dataclass |
| `combo_settings.yaml` | All combo settings (no num_browsers) |
| `tte_gui.py` | Tkinter GUI for combo mode |
| `tte_gui.spec` | PyInstaller spec (legacy, use CLI instead) |
| `dist/TTE.exe` | Built GUI executable |
| `open_tv.py` | Browser automation (sleep-optimized, headless support) |
| `open_entry_chart.py` | Chart symbol/timeframe changes |
| `docs/combo/PRD.md` | Combo mode PRD |
| `Pine Script Code/TTE Screener.txt` | Production screener |

### Stock Buddy App
| File | Purpose |
|------|---------|
| `src/components/tte/ComboSignalGrid.tsx` | Main paginated signal grid |
| `src/store/api/comboSignalsApi.ts` | RTK Query API for combo signals |
| `src/lib/tte/schemas.ts` | All Zod schemas |
| `src/lib/tte/collections.ts` | All DB functions |

---

## Verified Patterns

### Stock Buddy API Endpoints
```
POST /api/tte/combo          — Webhook: {timestamp, signals: [{symbol, nwe, ob_fvg, divergence}]}
GET  /api/tte/combo/signals  — Query: ?limit=20&offset=0&sort=signal_count&order=desc&direction=bullish&signalType=nwe&symbol=GBP
GET  /api/tte/stats           — Returns combo stats in "combo" field
```

### Combo Settings (production)
```yaml
batch_size: 3
chart_timeframe: "1 minute"
bar_style: "line"
recalc_wait: 1.5
creation_delay: 1.5
maintenance_interval: 300
headless: false
```

### Building the GUI Exe
```bash
pyinstaller --name TTE --onefile --windowed tte_gui.py
# Output: dist/TTE.exe
# Delete build/ and TTE.spec after
```

---

## Test Commands

```bash
# TTE
cd "C:/Users/dassa/Work/For Poolsifi/tradingview to everywhere"
python combo_main.py                # Run combo mode (setup + maintenance)
python combo_main.py --fresh        # Delete alerts & recreate
python combo_main.py --setup-only   # Create alerts, no maintenance
python combo_main.py --validate     # Validate config only
python tte_gui.py                   # Run GUI directly (no exe needed)

# Stock Buddy
cd "C:/Users/dassa/Work/Stock-Buddy-App"
npm run dev                                  # Dev server
npx tsc --project tsconfig.json --noEmit     # Type check
```

---

## Next Steps

1. **Run TTE fresh** (Task #109) — `python combo_main.py --setup-only --fresh` to create all 352 alerts
