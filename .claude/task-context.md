# Task Context Tracker

**Last Updated**: 2026-02-23
**Current Task**: Snapshot quality improvements + GUI defaults exposure
**Active Branch**: `feat/snapshot-quality-gui-defaults`
**Latest Commit (TTE)**: `0c9690b` — Add Snapshot config to GUI, pre-commit hooks, and codebase formatting
**Latest Commit (Stock Buddy)**: `bc0b810` — Add snapshot backfill endpoint

---

## Task Progress Summary

| # | Task | Status |
|---|------|--------|
| 131–144 | Chart snapshots feature + backfill | completed |
| 145 | Understand snapshot processing timing and batch size | completed |
| 146 | Get remaining 20 symbols into alerts on TradingView | pending |
| 147 | Decide on testing strategy (TDD / test coverage) | pending |
| 148 | Set up pre-commit hooks for linting, type checking, and formatting | completed |
| 149 | Rebuild and redeploy TTE.exe | pending |

---

## Session History

### Session: 2026-02-23 (Snapshot Quality + GUI Defaults)

**Goal**: Improve snapshot quality and expose snapshot settings in the GUI.

**Branch**: `feat/snapshot-quality-gui-defaults`

#### Snapshot Quality Improvements (already committed)
Recent commits on branch improved snapshot quality:
- `7190735` — Improve snapshot quality and GUI defaults
- `526d88e` — Fix: move `_set_bars_to_right()` after layout switch
- `7d750df` — Use Snapshot layout for entire maintenance loop
- `471685a` — Fix: initialize browser on Snapshot layout for `--maintain-only`
- `516db09` — Fix: change Alt+R auto-fit log from debug to info

#### Add Snapshot Config Section to GUI
Added Snapshot settings section to `tte_gui.py` between Alerts and Maintenance:
- **Row 1**: Enabled checkbox, Layout entry, Bar Style dropdown
- **Row 2**: Batch Size (1-20), Poll Interval (30-600s), Bars Right (10-200)
- Load/save from `combo_settings.yaml` `snapshot:` section
- Defaults: enabled=True, layout="Snapshot", bar_style="candle", batch_size=5, poll_interval=60, bars_to_right=60

**TTE.exe rebuilt** after GUI changes (20 MB, all validations passed).

#### Pre-commit Hooks & Codebase Formatting (Task #148)
Set up pre-commit hooks with ruff + pyright:
- Added `.pre-commit-config.yaml` — trim whitespace, EOF fix, YAML check, merge conflicts, large files, debug statements, ruff, ruff-format, pyright
- Added `pyproject.toml` with ruff/pyright config
- Applied ruff formatting across entire codebase (whitespace, imports, quotes)
- Added `ruff` and `pre-commit` to Pipfile dev dependencies
- Added PRD-generator and update-docs skills

**Commit**: `0c9690b` — all 9 pre-commit hooks passed, pushed to `feat/snapshot-quality-gui-defaults`

---

### Session: 2026-02-21 (Snapshot Reliability + Backfill)

**Goal**: Fix indicator loading race condition in snapshot worker, then backfill snapshots for all pre-feature setup messages.

#### Bug Fix: Wait for Indicator to Load Before Filling Settings

**Problem**: TTE was double-clicking the Trade Drawer indicator to open settings before it had finished loading after a symbol/timeframe change. The legend-source-item shows `data-status="loading"` while loading.

**Fix**: Added `_wait_for_indicator_ready()` to `SnapshotWorker` in `tte/snapshot_worker.py`:
- Polls `data-status` on the `div[data-qa-id="legend-source-item"]` every 200ms
- Waits up to 3.5 seconds for `data-status != "loading"`
- Re-fetches element on `StaleElementReferenceException`
- Proceeds with a warning if timeout exceeded (non-blocking)
- Called in `_set_trade_drawer()` after `get_indicator()`, before double-click

**Also fixed**: `setup_tv()` in `tradingview.py` — Screener-not-found was a hard failure preventing `--maintain-only` from starting if indicator had a transient load issue. Changed to a warning (maintenance + snapshots don't need the Screener to be on chart).

**Commit**: `0c61633`

#### Testing the Fix

Manually marked one setup (`EHC HTF H4`) as `snapshotStatus: "pending"` in MongoDB, ran `python combo_main.py --maintain-only`. Confirmed:
- Trade Drawer found and loaded before settings filled
- JLL, GEHC, TLN snapshots all succeeded in the same run
- Logs: `"Snapshot completed for {SYMBOL}: https://www.tradingview.com/x/..."`
- Browser runs headless (no visible window) — expected

**Key finding from DB check**: `setup_messages` collection is in `tte` database (not `stock-buddy`). Already had 1,385 pending + 288 completed snapshots before backfill endpoint was built.

#### Backfill Endpoint (Task #144)

**Problem**: Setup messages created before the snapshot feature was deployed have no `snapshotStatus` field — the worker only picks up `pending`/`failed` docs, so old setups are invisible to it.

**Solution**: `POST /api/tte/snapshots/backfill` on Stock Buddy
- Finds all setup messages from last 30 days where `snapshotStatus` doesn't exist
- Bulk-sets them to `snapshotStatus: "pending"`, `snapshotAttempts: 0`
- Returns `{ queued: N, setupMessageIds: [...] }`
- Idempotent — second call returns `queued: 0`

**Files added/modified (Stock Buddy)**:
- `src/lib/tte/collections.ts` — `backfillPendingSnapshots(days=30)` function
- `src/app/api/tte/snapshots/backfill/route.ts` — NEW endpoint

**Mini PRD**: `docs/prds/backfill-snapshots.md` (TTE repo)

**Stock Buddy commit**: `bc0b810`, pushed to main. **TTE.exe rebuilt** `293f971` — includes all snapshot fixes.

**To trigger backfill**:
```bash
curl -X POST https://stock-buddy-app.vercel.app/api/tte/snapshots/backfill
```

---

### Session: 2026-02-20 (Chart Snapshots Feature — Full Implementation)

**Goal**: Add TradingView chart snapshots to Stock Buddy setup messages.

**Architecture**: Async polling — Stock Buddy stores `snapshotStatus: "pending"` on setup messages. TTE polls every 60s, takes screenshots (Alt+S → clipboard), reports URLs back. Stale recovery resets "processing" >10min back to "pending".

**TTE files created/modified**:
- `tte/snapshot_worker.py` — NEW: `StockBuddyClient` + `SnapshotWorker`
- `tte/config.py` — 6 `snapshot_*` fields
- `combo_settings.yaml` — `snapshot:` section
- `tte/main.py` — Dual-timer maintenance loop
- `tte/browser/chart.py` — Fixed selectors, JS-based timeframe change + indicator title
- `tte/browser/tradingview.py` — JS-based indicator title lookup
- `Pine Script Code/Trade Drawer.txt` — NEW: Trade Drawer v6
- `docs/combo/ARCHITECTURE.md` — Sections 3.7, 3.8, Phase 4

**Stock Buddy files**:
- Schema: `snapshotStatus`, `snapshotUrl`, `snapshotTvUrl`, `snapshotAttempts`, `snapshotUpdatedAt`
- APIs: `GET /api/tte/snapshots/pending`, `POST /api/tte/snapshots/update`
- UI: `SetupMessageBubble.tsx` renders chart images

**Key bugs fixed during implementation**:
1. `legend-source-item` selector: `data-name` → `data-qa-id`
2. `nweTf` values: Added "1H"/"4H"/"H1"/"H4" to TF_MAP
3. `alertTimestamp`: Already ms, removed `* 1000`
4. Trade Drawer input selector: `.cell-tBgV1m0B` → `data-qa-id="ui-lib-Input-input"`
5. Snapshot method: Camera icon → Alt+S clipboard
6. Legend toggle: Use `aria-label` to distinguish state
7. Bar style: `"bar"` → `"candle"`
8. Trade Drawer: Fill only 4 inputs (skip TP2/TP3)
9. Hashed CSS `title-l31H9iuA` → JS `querySelectorAll('div[class*="title-"]')`
10. Headless clipboard: CDP `Browser.grantPermissions` for `clipboardReadWrite`
11. PNG URL: `snapshots/{first_char_lowercase}/{id}.png`
12. `pystray` missing from exe: Added `--hidden-import pystray` to PyInstaller

**PR #6**: Squash-merged → `a9680f0`. Post-merge: `b4960c0`, `27a12ff`

---

### Previous Sessions (Summary)
- **2026-02-20**: Branch cleanup — reset main to combo-architecture
- **2026-02-13**: Codebase reorganization into `tte/` package (PR #4)
- **2026-02-12**: Codebase cleanup, Pine Script screener v2, entry setups, divergence fix, GUI stop button
- **2026-02-10–11**: Single browser optimization, maintenance loop, docs, Stock Buddy combo API

---

## Important Decisions Made

1. **Snapshot architecture**: Async polling (not webhook-triggered). TTE polls Stock Buddy every 60s.
2. **Single browser**: Reuses existing browser. TradingView allows max 2 sessions.
3. **Dual-timer maintenance**: Snapshots 60s, maintenance 300s. Maintenance has priority.
4. **Alt+S for snapshots**: Clipboard via `navigator.clipboard.readText()` + CDP permission for headless.
5. **Trade Drawer v6**: Draws on `barstate.islast` only. Orange SL / Blue TP (distinct from NWE red/green).
6. **Legend hide/show**: Hide before screenshot, show before Trade Drawer settings.
7. **JS-based selectors**: Replace hashed CSS classes with `querySelectorAll('div[class*="title-"]')`.
8. **No layout switch-back**: Maintenance can run on any layout.
9. **PNG URL prefix**: TradingView S3 CDN uses `snapshots/{first_char_lowercase}/{id}.png`.
10. **Screener check non-fatal**: `setup_tv()` Screener-not-found → warning only (not exit).
11. **Indicator load wait**: 3.5s polling wait on `data-status != "loading"` before settings dialog.
12. **Backfill scope**: Last 30 days only. Older setups assumed stale/irrelevant.
13. **MongoDB DB name**: `setup_messages` collection is in `tte` database (not `stock-buddy`).
14. **Pre-commit hooks**: ruff (lint + format) + pyright (type check). Config in `.pre-commit-config.yaml` + `pyproject.toml`.
15. **GUI snapshot settings**: Exposed 6 snapshot config fields (enabled, layout_name, bar_style, batch_size, poll_interval, bars_to_right) in GUI between Alerts and Maintenance sections.

---

## Key Reference Files

### TTE Project
| File | Purpose |
|------|---------|
| `tte/snapshot_worker.py` | Snapshot polling + browser orchestration (incl. `_wait_for_indicator_ready`) |
| `tte/main.py` | Entry point with dual-timer maintenance loop |
| `tte/config.py` | Config dataclass (includes snapshot settings) |
| `combo_settings.yaml` | All settings (chart, screener, alerts, snapshot) |
| `tte/browser/tradingview.py` | Browser automation (Screener check now warning-only) |
| `tte/browser/chart.py` | Chart symbol/timeframe/indicator/snapshot |
| `Pine Script Code/Trade Drawer.txt` | Trade Drawer v6 Pine Script |
| `Pine Script Code/TTE Screener.txt` | Production screener |
| `docs/combo/ARCHITECTURE.md` | Full system architecture (incl. snapshots) |
| `docs/prds/backfill-snapshots.md` | Mini PRD for backfill feature |
| `tte_gui.py` | GUI with snapshot config section |
| `.pre-commit-config.yaml` | Pre-commit hooks (ruff, pyright, etc.) |
| `pyproject.toml` | Ruff + pyright config |

### Stock Buddy App (`C:/Users/dassa/Work/Stock-Buddy-App`)
| File | Purpose |
|------|---------|
| `src/lib/tte/schemas.ts` | SetupMessage with snapshot fields |
| `src/lib/tte/collections.ts` | getPendingSnapshots, updateSetupSnapshot, backfillPendingSnapshots |
| `src/app/api/tte/snapshots/pending/route.ts` | GET pending snapshots |
| `src/app/api/tte/snapshots/update/route.ts` | POST snapshot result |
| `src/app/api/tte/snapshots/backfill/route.ts` | POST backfill old snapshots |
| `src/components/chat/SetupMessageBubble.tsx` | Renders snapshot image |

---

## Verified Patterns

### Snapshot API Contract
```
GET  /api/tte/snapshots/pending?limit=5
  → { snapshots: [{ setupMessageId, symbol, direction, label, entryPrice, stopLoss, takeProfit, nweTf, alertTimestamp }] }

POST /api/tte/snapshots/update
  Success: { setupMessageId, snapshotUrl, snapshotTvUrl }
  Failure: { setupMessageId, error }
  → { success: true }

POST /api/tte/snapshots/backfill
  → { success: true, queued: N, setupMessageIds: [...] }
```

### Working TradingView Selectors
```
Legend items:      div[data-qa-id="legend-source-item"]  (data-status="loading" while loading)
Legend toggler:    button[data-qa-id="legend-toggler"] (use aria-label to distinguish)
Indicator inputs:  input[data-qa-id="ui-lib-Input-input"]
Indicator title:   JS: querySelectorAll('div[class*="title-"]')[0].textContent
Settings dialog:   div[data-name="indicator-properties-dialog"]
Inputs tab:        button[id="inputs"]
Submit button:     button[name="submit"]
Chart area:        div.chart-markup-table
Timeframe dropdown: div[data-qa-id="menu-inner"] (use JS click for stale-element safety)
```

### Timeframe Mapping
```python
TF_MAP = {"LTF": "1 hour", "HTF": "4 hours", "1H": "1 hour", "4H": "4 hours", "H1": "1 hour", "H4": "4 hours"}
```

### PNG URL Construction
```python
snapshot_id = tv_url.rstrip("/").split("/")[-1]
prefix = snapshot_id[0].lower()
png_url = f"https://s3.tradingview.com/snapshots/{prefix}/{snapshot_id}.png"
```

### MongoDB — Mark One Setup Pending (for testing)
```bash
python /tmp/mark_pending.py   # see script below
# or from pipenv:
pipenv run python - << 'EOF'
import sys; sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv(dotenv_path='.env')
import pymongo, os
col = pymongo.MongoClient(os.getenv('MONGODB_URI'))['tte']['setup_messages']
r = col.find_one_and_update({'snapshotStatus': 'completed'}, {'$set': {'snapshotStatus': 'pending', 'snapshotAttempts': 0}, '$unset': {'snapshotUrl': '', 'snapshotTvUrl': ''}}, sort=[('timestamp', -1)], return_document=pymongo.ReturnDocument.AFTER)
print(r['_id'], r['symbol'])
EOF
```

---

## Test Commands

```bash
# TTE
python combo_main.py --maintain-only    # Run maintenance + snapshots (headless)
python combo_main.py --validate         # Validate config
python combo_main.py --fresh            # Delete alerts & recreate
dist/TTE.exe                            # GUI (requires pystray)

# Trigger backfill (after Stock Buddy deployed)
curl -X POST https://stock-buddy-app.vercel.app/api/tte/snapshots/backfill

# Stock Buddy
cd "C:/Users/dassa/Work/Stock-Buddy-App"
npm run dev
npx tsc --project tsconfig.json --noEmit

# MongoDB snapshot status check
pipenv run python -c "
import pymongo, os; from dotenv import load_dotenv; load_dotenv('.env')
col = pymongo.MongoClient(os.getenv('MONGODB_URI'))['tte']['setup_messages']
print('completed:', col.count_documents({'snapshotStatus': 'completed'}))
print('pending:', col.count_documents({'snapshotStatus': 'pending'}))
print('failed:', col.count_documents({'snapshotStatus': 'failed'}))
print('no status:', col.count_documents({'snapshotStatus': {'\$exists': False}}))
"
```
