# Task Context Tracker

**Last Updated**: 2026-02-13
**Current Task**: Codebase reorganization into `tte/` package complete. PR #4 open. Pending: alert recreation via exe/fresh after Stock Buddy deploy.
**Last Session**: Codebase reorganization — move all Python files into `tte/` package structure
**Active Branch**: `codebase-reorg` (PR #4)

---

## Task Progress Summary

**Completed Count**: 104+ tasks | **In Progress**: 0 | **Pending**: 1 (alert recreation via exe/fresh)

Codebase reorganization complete (8 files moved, imports updated, docs updated). Entry setup feature complete. Stock Buddy needs commit + Vercel deploy, then run `dist/TTE.exe` (Fresh mode) to recreate alerts with v2 payload.

---

## Session History

### Session: 2026-02-13 (Codebase Reorganization into `tte/` Package)

**Goal**: Reorganize flat root Python files into a proper `tte/` package with `browser/` and `data/` sub-packages.

**Branch**: `codebase-reorg` | **PR**: #4 (https://github.com/Samaara-Das/Tradingview-to-Everywhere/pull/4)

**Files moved (git mv)**:
| From | To |
|------|-----|
| `logger_setup.py` | `tte/log.py` |
| `resources/utils.py` | `tte/browser/helpers.py` |
| `open_entry_chart.py` | `tte/browser/chart.py` |
| `resources/symbol_settings.py` | `tte/data/symbols.py` |
| `open_tv.py` | `tte/browser/tradingview.py` |
| `combo_config.py` | `tte/config.py` |
| `combo_main.py` | `tte/main.py` |
| `resources/STOCK_BUDDY_TECHNICAL_ARCHITECTURE.md` | `docs/` |

**Files created**:
- `tte/__init__.py` — re-exports `ComboConfig`, `Browser`
- `tte/browser/__init__.py` — re-exports `Browser`, `OpenChart`, `Utils`
- `tte/data/__init__.py` — re-exports `get_symbols`, `get_symbol_categories`
- Root `combo_main.py` — 3-line backward-compat shim delegating to `tte.main`

**Files deleted**: `env.py` (absorbed into `tte/config.py`), `resources/` directory

**Import updates** (6 files): All `import logger_setup` → `from tte import log`, all cross-module imports updated to `tte.` prefix.

**Key changes in `tte/config.py`**:
- Added `PROFILE = "Profile 4"` (from deleted `env.py`)
- Changed `SETTINGS_FILE` path: `Path(__file__).parent` → `Path(__file__).parent.parent` (file moved one level deeper)

**Documentation updated** (~13 files): CLAUDE.md, README.md, docs/combo/ARCHITECTURE.md, docs/SETUP.md, docs/TROUBLESHOOTING.md, docs/CONTRIBUTING.md, docs/DATABASE.md, .claude/agents/ (4 agent files), .claude/skills/mongodb/SKILL.md, .vscode/launch.json

**Verification** (all passed):
- `py_compile` on all .py files
- `python combo_main.py --validate` (shim works)
- `python -m tte.main --validate` (direct module works)
- All import chain tests pass

**Commits**:
- `9c87d44` — Reorganize codebase into tte/ package (Phases 1-3)
- `d38293b` — Update documentation for tte/ package structure (Phase 4)

---

### Session: 2026-02-12 (Codebase Cleanup — Phases 1-6 on `codebase-cleanup` branch)

**Goal**: Clean up legacy/dead code, unused deps, and improve code quality.

**Completed phases**:
1. Delete legacy/tiered files (Tasks #124)
2. Clean dead code from open_tv.py (#125)
3. Clean env.py and symbol_settings.py (#126)
4. Code quality fixes (#127)
5. Remove unused dependencies (#128)
6. Update documentation (#129)
7. Verification & testing (#130)

**Commits**:
- `5fa9578` — Replace debug prints with proper logging
- `762800a` — Remove unused dependencies, add pyyaml
- `3b18d38` — Update documentation for combo-only codebase
- `80d713a` — Add auto-start on boot, maintain-only default, and 3-hour log auto-clear
- `02e3127` — Move setup_startup.ps1 to dist/ and remove unused tte_gui.spec

---

### Session: 2026-02-12 (Entry Setups — Pine Script Payload v2 + OB Timestamp Fix)

**Goal**: Add `zoneHigh`/`zoneLow` to OB entries + `close` price per symbol in webhook payload. Fix D1 OB timestamps showing 1 day earlier than the chart candle.

**Pine Script changes** (`Pine Script Code/TTE Screener.txt`):
- `buildObEntry()`: Added `zoneHigh`/`zoneLow` params
- `buildObArray()`: Added 12 new float params for zone high/low
- Close price: 3 new `request.security()` calls (15 total, within 40 limit)
- `buildSymbolJson()`: Added `closePrice` param

**OB timestamp bug fix**: `tf == 'D' ? time_close[i - timeShift] : time[i - timeShift]` at 6 locations

**Stock Buddy UAT**: 3 rounds, 41 tests passing. Entry setup feature complete end-to-end.

---

### Session: 2026-02-12 (Debug Table + GUI Stop Button Fix + Exe Rebuild)

Pine Script debug table commented for production. GUI stop button fixed (`taskkill /F /T /PID` replaces unreliable `os.kill`). Exe rebuilt.

---

### Session: 2026-02-12 (Fix Divergence Detection in Pine Script Screener)

Root cause: `buildDivEntry()` compared HTF bar timestamp vs 1-min chart timestamp (never match). Fix: `divTime > 0` + recency gate `currLowShift <= 1` / `currHighShift <= 1`.

---

### Earlier Sessions (2026-02-10 — 2026-02-11)

- Single browser + sleep optimization + GUI exe build
- Maintenance loop improvements
- Documentation updates (16 files)
- Combo Signal Grid in Stock Buddy
- Stock Buddy Combo API endpoints
- Pine Script screener development
- Error recovery patterns

---

## Important Decisions Made

1. **Architecture**: Combo screener (single indicator) over separate screeners
2. **Webhook destination**: Stock Buddy API (Vercel) at `/api/tte/combo`
3. **tte_live_signals collection**: One document per symbol (`_id = symbol`), upserted on each webhook
4. **3 symbol batch limit**: Reduced from 4 for 1-min chart performance
5. **1-minute chart timeframe**: Fires once per minute (rate limit safe)
6. **Single browser**: Parallel browsers abandoned — slower due to TradingView throttling
7. **GUI exe uses `python` from PATH**: When frozen, subprocess calls `python combo_main.py` (not bundled)
8. **Entry setups stored in TWO places**: `tte_live_signals` (overwritten per webhook) + `tte_entry_setups` (append-only)
9. **D1 OB timestamps use `time_close`**: Conditional for daily bars only
10. **GUI stop uses `taskkill`**: Replaces unreliable `os.kill(CTRL_BREAK_EVENT)` on Windows
11. **Deployment order**: Stock Buddy deploy first → then TTE alert recreation
12. **`tte/` package structure**: All Python modules organized under `tte/` with `browser/` and `data/` sub-packages
13. **Root `combo_main.py` shim**: 3-line backward-compat wrapper so CLI, GUI subprocess, .vscode/launch.json all still work
14. **`tte/log.py` not `tte/logging.py`**: Avoids shadowing Python's stdlib `logging` module
15. **`combo_settings.yaml` stays at root**: Both `tte/config.py` and `tte_gui.py` expect it there; exe build expects it there

---

## Key Reference Files

### TTE Project
| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project instructions |
| `combo_main.py` | Backward-compatible entry point (shim → `tte.main`) |
| `tte/main.py` | Actual entry point (orchestrator) |
| `tte/config.py` | Config dataclass + PROFILE constant |
| `combo_settings.yaml` | All combo settings (headless: true) |
| `tte_gui.py` | Tkinter GUI (frozen exe path handling) |
| `dist/TTE.exe` | Built GUI executable |
| `tte/browser/tradingview.py` | Browser automation (Selenium) |
| `tte/browser/chart.py` | Chart symbol/timeframe changes |
| `tte/browser/helpers.py` | Selenium utility functions |
| `tte/data/symbols.py` | MongoDB symbol loading |
| `tte/log.py` | Logger setup |
| `Pine Script Code/TTE Screener.txt` | Production screener (v2 payload) |

### Stock Buddy App
| File | Purpose |
|------|---------|
| `src/components/tte/ComboSignalGrid.tsx` | Main paginated signal grid |
| `src/lib/tte/schemas.ts` | All Zod schemas |
| `src/lib/tte/collections.ts` | All DB functions |
| `src/lib/tte/entry-setup.ts` | Entry setup detection |
| `src/app/api/tte/combo/route.ts` | Webhook handler (dual writes) |

---

## Verified Patterns

### Stock Buddy API Endpoints
```
POST /api/tte/combo          — Webhook v2: {timestamp, signals: [{symbol, close, nwe, ob_fvg, divergence}]}
GET  /api/tte/combo/signals  — Query with pagination, sorting, filtering
GET  /api/tte/stats           — Returns combo stats
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

### Package Import Patterns
```python
from tte.config import ComboConfig, PROFILE
from tte.browser.tradingview import Browser
from tte.browser.chart import OpenChart
from tte.browser.helpers import Utils
from tte.data.symbols import get_symbols
from tte import log
logger = log.setup_logger(__name__, log.INFO)
```

---

## Test Commands

```bash
# TTE
cd "C:/Users/dassa/Work/For Poolsifi/tradingview to everywhere"
python combo_main.py                # Run via shim (setup + maintenance)
python -m tte.main                  # Run directly as module
python combo_main.py --fresh        # Delete alerts & recreate
python combo_main.py --setup-only   # Create alerts, no maintenance
python combo_main.py --validate     # Validate config only
python tte_gui.py                   # Run GUI directly
dist/TTE.exe                        # Run GUI exe

# Stock Buddy
cd "C:/Users/dassa/Work/Stock-Buddy-App"
npm run dev                                  # Dev server
npx tsc --project tsconfig.json --noEmit     # Type check
```
