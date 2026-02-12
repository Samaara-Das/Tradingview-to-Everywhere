# Task Context Tracker

**Last Updated**: 2026-02-11
**Current Task**: GUI exe working end-to-end. TTE ran successfully via exe (headless, no terminal).
**Last Session**: Fixed GUI exe path resolution, headless default, terminal suppression, missing dependency
**Active Branch**: `combo-architecture`

---

## Task Progress Summary

**Completed Count**: 97 tasks | **In Progress**: 0 | **Pending**: 0

All tasks complete. TTE GUI exe is functional and alert creation ran successfully.

---

## Session History

### Session: 2026-02-11 (GUI Exe Fixes — Multiple Bugs)

**Goal**: Get `dist/TTE.exe` to correctly launch `combo_main.py` headlessly without extra windows

**Bugs fixed chronologically**:

1. **GUI defaults updated** (`tte_gui.py`):
   - Set `headless` default to `True` (line 557)
   - Set `fresh` checkbox default to `True` (line 572)
   - Set webhook URL fallback to `https://stock-buddy-app.vercel.app/api/tte/combo` (line 568-570)

2. **Exe spawning itself recursively** — Clicking Start opened another GUI window instead of running TTE.
   - **Root cause**: `sys.executable` points to `TTE.exe` when frozen, not Python
   - **Fix**: Added `getattr(sys, 'frozen', False)` detection; use `"python"` from PATH when frozen (line 689-694)

3. **`combo_main.py` not found** — `python: can't open file 'C:\...\dist\combo_main.py'`
   - **Root cause**: `Path(sys.executable).parent` = `dist/`, but `combo_main.py` is in project root
   - **Fix**: Added `_get_project_dir()` helper that goes up one level from exe dir (lines 20-26)
   - Also fixed `SETTINGS_FILE` (line 80) — was using `__file__` which points to PyInstaller temp dir when frozen
   - Also fixed `cwd` for subprocess (line 727) to use project root

4. **Missing `facebook-sdk` package** — `ModuleNotFoundError: No module named 'facebook'`
   - **Fix**: `pip install facebook-sdk` (required by `send_to_socials/_facebook.py`, imported transitively via `handle_alerts.py` → `open_tv.py` → `combo_main.py`)

5. **Terminal window opening** — Python console appeared when subprocess launched
   - **Fix**: Added `subprocess.CREATE_NO_WINDOW` flag alongside `CREATE_NEW_PROCESS_GROUP` (line 718-720)

6. **Headless not applying** — Browser still opened visibly
   - **Root cause**: `combo_settings.yaml` had `headless: false` which overrode GUI default
   - **Fix**: Set `headless: true` in `combo_settings.yaml`

**Commits**:
- `86e4b02` — Set GUI defaults: headless on, fresh mode enabled
- `ffe74b5` — Updated exe
- `8d62486` — Fix GUI exe: resolve path issues, hide terminal, enable headless by default

**Key pattern — PyInstaller frozen exe path resolution**:
```python
def _get_project_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent.parent  # exe in dist/, project is parent
    return Path(__file__).parent
```

---

### Session: 2026-02-11 (Single Browser + Sleep Optimization + GUI — Tasks #81, #86, #90)

**Goal**: Optimize browser performance, add headless mode, build GUI executable

**Key changes**:
1. Switched from parallel to single browser (`combo_main.py` rewrite)
2. Sleep optimizations: `get_indicator()` 3s→0.5s, `change_settings()` 2s→0.5s, `change_symbol()` 2s→1s
3. Chrome anti-throttling flags added
4. Headless Chrome mode (`--headless=new`, guarded `maximize_window()`)
5. Built TTE GUI (`tte_gui.py`) with modern dark theme, rebuilt as `dist/TTE.exe`

**Commit**: `4b9b246`

---

### Session: 2026-02-11 (Maintenance Loop — Tasks #106, #107)

Added `clear_alert_log()`, improved `run_maintenance()`, fixed `restart_inactive_alerts()`.

**Commit**: `75036c9`

---

### Session: 2026-02-11 (Documentation — Task #108)

Updated 16 doc files for combo mode in production.

**Commit**: `0c89589`

---

### Earlier Sessions (2026-02-10 — 2026-02-11)

- **Combo Signal Grid** (#99-104, #60): Paginated signal grid in Stock Buddy
- **Stock Buddy Combo API** (#32-38, #91-98): Webhook endpoints + dashboard UI
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
11. **GUI exe uses `python` from PATH**: When frozen, subprocess calls `python combo_main.py` (not bundled)

---

## Key Reference Files

### TTE Project
| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project instructions (updated for single browser) |
| `combo_main.py` | Combo mode entry point (single browser) |
| `combo_config.py` | Combo configuration dataclass |
| `combo_settings.yaml` | All combo settings (headless: true) |
| `tte_gui.py` | Tkinter GUI for combo mode (frozen exe path handling) |
| `dist/TTE.exe` | Built GUI executable (working) |
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
headless: true
```

### Building the GUI Exe
```bash
# Kill existing TTE.exe first: taskkill //F //IM TTE.exe
pyinstaller --name TTE --onefile --windowed tte_gui.py
# Output: dist/TTE.exe
# Delete build/ and TTE.spec after
```

### PyInstaller Gotchas (tte_gui.py)
- `sys.executable` → points to the exe, not Python. Use `getattr(sys, 'frozen', False)` to detect.
- `__file__` → points to temp extraction dir (`_MEI*`). Use `Path(sys.executable).parent.parent` for project root.
- `SETTINGS_FILE` must use `_get_project_dir()`, not `Path(__file__).parent`.
- Subprocess needs `CREATE_NO_WINDOW` flag to hide terminal on Windows.
- Missing pip packages (e.g. `facebook-sdk`) won't be caught until runtime — test imports after fresh install.

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
dist/TTE.exe                        # Run GUI exe

# Stock Buddy
cd "C:/Users/dassa/Work/Stock-Buddy-App"
npm run dev                                  # Dev server
npx tsc --project tsconfig.json --noEmit     # Type check
```
