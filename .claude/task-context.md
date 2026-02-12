# Task Context Tracker

**Last Updated**: 2026-02-12
**Current Task**: Fixed divergence detection in TTE Pine Script screener — confirmed working via debug table test.
**Last Session**: Pine Script divergence fix (3 production changes + 5 debug helper fixes)
**Active Branch**: `combo-architecture`

---

## Task Progress Summary

**Completed Count**: 97 tasks | **In Progress**: 0 | **Pending**: 0

All tasks complete. Documentation fully synced with production state.

---

## Session History

### Session: 2026-02-12 (Fix Divergence Detection in Pine Script Screener)

**Goal**: Fix divergence detection that was always empty (`divergence: []`) in all 950 symbols in `tte_live_signals`.

**Root cause**: Two issues working together in `Pine Script Code/TTE Screener.txt`:
1. `buildDivEntry()` (line 792) checked `divTime == currTime` — comparing HTF bar timestamp vs 1-minute chart timestamp (virtually never match)
2. `detectBullishDiv()`/`detectBearishDiv()` scanned 300 bars back with no recency gate — relaxing #1 alone would flood stale divergences

**Production changes (3 edits, atomic set)**:
1. **Line 289**: `if inDownleg and lowerLow` → `if inDownleg and lowerLow and currLowShift <= 1` — gate bullish div to shift 0/1 on HTF
2. **Line 316**: `if inUpleg and higherHigh` → `if inUpleg and higherHigh and currHighShift <= 1` — gate bearish div to shift 0/1 on HTF
3. **Line 792**: `divTime == currTime` → `divTime > 0` — replace impossible timestamp match with non-zero check
4. **Line 790**: Updated stale comment to match new logic

**Debug helper functions fixed (5 edits, same `== currTime` → `> 0` pattern)**:
- `buildDivDetailTable` (line 860) — table cell text
- `buildDivTooltip` (line 922) — hover tooltip
- `formatSingleDivSignal` (line 969) — B/S/- display
- `getSingleDivColor` (line 982) — green/red/gray coloring
- `hasAnySignal` (line 995) — signal presence check

**Testing**: Uncommented debug table for 1 symbol (s01) on 1H + H4 timeframes. User confirmed divergence detection working correctly on shift 0 and 1. Table re-commented for production.

**Note**: D1 timeframe uses `checkOBOnly()` (no divergence detection). Only 1H and H4 divergences appear. Adding D1 divergence would require additional `request.security()` calls — separate scope.

---

### Session: 2026-02-12 (Documentation Update — 6 Outdated Files)

**Goal**: Update 6 documentation files that were outdated after the Feb 2026 single-browser/headless/GUI changes.

**Production numbers used**: ~1,028 symbols (MongoDB), 338 alerts (338 × 3 = 1,014 covered), targets 343 for full coverage.

**Files updated (by priority)**:

1. **`README.md`** (HIGH): Updated alert count (352→338), symbol count (~1,054→~1,028), `gui.py`→`tte_gui.py`, added `dist/TTE.exe`, removed `COMBO_NUM_BROWSERS`, added headless note.

2. **`docs/combo/PRD.md`** (HIGH): Updated all counts, changed "Browser instances: 2" → "Browser mode: Single (sequential)", updated YAML example to match actual `combo_settings.yaml`, removed `COMBO_NUM_BROWSERS` env var, split "Future Enhancements" into Completed (headless, GUI) + remaining, updated production metrics (task count 89→97).

3. **`docs/combo/ARCHITECTURE.md`** (MEDIUM — largest, 745 lines): Systematic replacement of 264→338, 4 symbols→3 symbols, ~1,054→~1,028 throughout all 14 sections. Changed `/api/tte/signal`→`/api/tte/combo` (4 locations). Updated orchestrator files (`orchestrator.py`→`combo_main.py`), setup diagram, maintenance pseudocode (added page refresh + alert log clearing), data flow examples, Q9 parallel→single browser.

4. **`docs/SETUP.md`** (MEDIUM): Updated YAML example (added headless, screener, progress sections; removed num_browsers; fixed creation_delay), removed `COMBO_NUM_BROWSERS`, added GUI subsection.

5. **`docs/TROUBLESHOOTING.md`** (LOW): Rewrote "Browser Session Limits" for single browser, added GUI/exe troubleshooting section, added headless mode issues section.

6. **`docs/CONTRIBUTING.md`** (LOW): Added combo test commands, added combo docs to update table and key files reference.

**Verification** (all passed):
- `num_browsers` → 0 matches in docs + README
- `gui.py` (without `tte_` prefix) → 0 matches
- `264` in combo docs → only in JSON timestamp values (correct)
- `/api/tte/signal` in combo docs → only in archived `IMPLEMENTATION.md` (out of scope)

---

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
- **Production alerts**: 338 alerts, batch_size=3, 1-min chart, graceful shutdown
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
