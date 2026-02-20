# Task Context Tracker

**Last Updated**: 2026-02-20
**Current Task**: Chart Snapshots feature — TTE working end-to-end, user verifying remaining cases
**Active Branch**: `feature/chart-snapshots`
**PR**: https://github.com/Samaara-Das/Tradingview-to-Everywhere/pull/6

---

## Task Progress Summary

**Completed**: 6 | **In Progress**: 0 | **Pending**: 2

| # | Task | Status |
|---|------|--------|
| 131 | Add snapshot config to combo_settings.yaml and config.py | completed |
| 132 | Create tte/snapshot_worker.py with StockBuddyClient and SnapshotWorker | completed |
| 133 | Integrate snapshot worker into maintenance loop with dual timers | completed |
| 134 | Stock Buddy: Add snapshot schema fields and collection functions | completed |
| 135 | Stock Buddy: Create snapshot API endpoints | completed |
| 136 | Stock Buddy: Update SetupMessageBubble to display snapshot images | completed |
| 137 | Manual verification: End-to-end snapshot workflow testing | pending |
| 138 | Verify snapshot images render in Stock Buddy UI | pending |

---

## Session History

### Session: 2026-02-20 (Chart Snapshots Feature)

**Goal**: Add TradingView chart snapshots to Stock Buddy setup messages. TTE takes screenshots of the chart with correct symbol/timeframe/Trade Drawer levels and reports URLs back to Stock Buddy.

**Architecture**: Async polling — Stock Buddy stores `snapshotStatus: "pending"` on setup messages. TTE polls every 60s, takes screenshots, reports URLs back. Stale recovery resets "processing" snapshots >10min back to "pending".

**Files created/modified (TTE side)**:
- `tte/snapshot_worker.py` — NEW: `StockBuddyClient` (HTTP client) + `SnapshotWorker` (orchestrator)
- `tte/config.py` — Added 6 `snapshot_*` fields to `ComboConfig`
- `combo_settings.yaml` — Added `snapshot:` section
- `tte/main.py` — Dual-timer maintenance loop (snapshots 60s, maintenance 300s)
- `tte/browser/chart.py` — Fixed `legend-source-item` selector (`data-name` → `data-qa-id`)
- `.claude/agent-comms.md` — API contract + inter-agent communication
- `Pine Script Code/Trade Drawer.txt` — NEW: Rewritten Trade Drawer v2 with proper colors

**Stock Buddy side** (separate repo, `feature/chart-snapshots` merged to main):
- Schema: `snapshotStatus`, `snapshotUrl`, `snapshotTvUrl`, `snapshotAttempts`, `snapshotUpdatedAt`
- Collection functions: `getPendingSnapshots()`, `updateSetupSnapshot()`, `resetStaleSnapshots()`
- APIs: `GET /api/tte/snapshots/pending`, `POST /api/tte/snapshots/update`
- UI: `SetupMessageBubble.tsx` shows image (completed), loading placeholder (pending), or "unavailable" (failed)
- Chat API: pass-through of snapshot fields

**Bugs fixed during testing**:

1. **`legend-source-item` selector stale**: `data-name="legend-source-item"` → `data-qa-id="legend-source-item"` in `chart.py:376`

2. **`nweTf` values mismatch**: Stock Buddy sends `"1H"`/`"4H"`/`"H1"`/`"H4"`, not `"LTF"`/`"HTF"`. Added all variants to `TF_MAP`.

3. **`alertTimestamp` already milliseconds**: Stock Buddy agent initially said Unix seconds, but actual data was ms (e.g., `1771591380000`). Removed `* 1000` multiplication.

4. **Trade Drawer input selector stale**: `.cell-tBgV1m0B input` found 0 elements. Changed to `input[data-qa-id="ui-lib-Input-input"]` (stable data-qa-id selector).

5. **Snapshot method**: Camera icon approach (`save_chart_img()`) replaced with Alt+S shortcut. Click chart → Alt+S → read clipboard via `navigator.clipboard.readText()` (browser JS, isolated from desktop clipboard).

6. **Legend toggle selector**: `data-qa-id="legend-toggler"` is same in both states. Must use `aria-label` to distinguish ("Hide indicators legend" vs "Show indicators legend").

7. **Bar style**: Changed from `"bar"` to `"candle"` per user preference.

8. **Trade Drawer fills only 4 inputs**: Skips TP2/TP3 (redundant). Only fills entry_time, entry_price, sl, tp1.

9. **Trade Drawer Pine Script rewrite**: Original drew lines/fills on every tick (hundreds of overlapping objects). Brownish color from green+red overlap. Rewritten to draw on `barstate.islast` only, delete old drawings before redrawing, use orange (SL) + blue (TP) colors distinct from NWE's red/green.

10. **Trade Drawer bar 0 bug**: Drawing on bar 0 (when inputs change and script reloads) caused `time[1] = na`, making `dt = na` and `endTime = na` — lines stretched to chart origin with broken coordinates. Fixed by drawing only on `barstate.islast`.

11. **Maintenance/snapshot collision**: Both timers could fire simultaneously (e.g., at 300s). Fixed: maintenance has priority; snapshots skip that tick to avoid browser contention.

12. **Legend ensure visible at batch start**: Added `_show_legend()` after switching to Snapshot layout, before processing any setups — ensures first setup's Trade Drawer double-click works.

**Working snapshot flow** (verified in logs, 50+ pending processed successfully):
```
Fetched 5 pending snapshots → Switch to Snapshot layout → Change candles to candle →
Show legend → For each: change_symbol → force_change_tframe → show_legend →
set Trade Drawer (4 inputs) → hide_legend → Alt+S snapshot → show_legend →
report URL → Switch back to Screener layout
```

**Inter-agent communication**: `.claude/agent-comms.md` used for TTE ↔ Stock Buddy agent coordination. Documented API contract, field format clarifications, deployment status.

---

### Session: 2026-02-20 (Branch Cleanup)
Reset `main` to `combo-architecture` HEAD. Force-pushed. Closed stale PRs. Final state: `main` = `4d08793`.

### Session: 2026-02-13 (Codebase Reorganization into `tte/` Package)
Moved flat Python files into `tte/` package. PR #4.

### Earlier Sessions (2026-02-10 — 2026-02-12)
Codebase cleanup, Pine Script screener v2, entry setups, divergence detection fix, GUI stop button fix, exe rebuild, Stock Buddy combo API.

---

## Important Decisions Made

1. **Snapshot architecture**: Async polling (not webhook-triggered). TTE polls Stock Buddy every 60s.
2. **Single browser for snapshots**: Reuses existing browser. TradingView allows max 2 sessions.
3. **Dual-timer maintenance loop**: Snapshots every 60s, alert maintenance every 300s (configurable).
4. **Trade Drawer v2 (6 inputs)**: entry_time, entry_price, sl, tp1, tp2, tp3. Only 4 filled by TTE.
5. **Alt+S for snapshots**: More reliable than camera icon + new tab approach. Reads clipboard via browser JS.
6. **Legend hide/show per snapshot**: Hide before screenshot (clean chart), show before Trade Drawer settings (needs double-click on indicator).
7. **Orange/Blue colors for Trade Drawer**: Distinct from NWE's red/green. Orange `#FF6D00` for SL, Blue `#2962FF` for TP.
8. **Draw on barstate.islast**: Trade Drawer draws only on last bar (valid `time[1]`). Deletes old drawings before redrawing.
9. **Stable selectors**: `data-qa-id` attributes preferred over CSS class names (TradingView rehashes classes).
10. **Maintenance priority over snapshots**: When both timers fire, maintenance runs first, snapshots skip that tick.

---

## Key Reference Files

### TTE Project
| File | Purpose |
|------|---------|
| `tte/snapshot_worker.py` | Snapshot polling + browser orchestration |
| `tte/main.py` | Entry point with dual-timer maintenance loop |
| `tte/config.py` | Config dataclass (includes snapshot settings) |
| `combo_settings.yaml` | All settings (chart, screener, alerts, snapshot) |
| `tte/browser/tradingview.py` | Browser automation (Selenium) |
| `tte/browser/chart.py` | Chart symbol/timeframe/indicator/snapshot |
| `.claude/agent-comms.md` | Inter-agent communication file |
| `Pine Script Code/Trade Drawer.txt` | Trade Drawer v2 Pine Script |
| `Pine Script Code/TTE Screener.txt` | Production screener |

### Stock Buddy App
| File | Purpose |
|------|---------|
| `src/lib/tte/schemas.ts` | SetupMessage with snapshot fields |
| `src/lib/tte/collections.ts` | getPendingSnapshots, updateSetupSnapshot |
| `src/app/api/tte/snapshots/pending/route.ts` | GET pending snapshots |
| `src/app/api/tte/snapshots/update/route.ts` | POST snapshot result |
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
```

### Working TradingView Selectors
```
Legend items:     div[data-qa-id="legend-source-item"]
Legend toggler:   button[data-qa-id="legend-toggler"] (use aria-label to distinguish state)
Indicator inputs: input[data-qa-id="ui-lib-Input-input"]
Settings dialog:  div[data-name="indicator-properties-dialog"]
Inputs tab:       button[id="inputs"]
Submit button:    button[name="submit"]
Chart area:       div.chart-markup-table
```

### Timeframe Mapping (nweTf → TradingView dropdown)
```python
TF_MAP = {"LTF": "1 hour", "HTF": "4 hours", "1H": "1 hour", "4H": "4 hours", "H1": "1 hour", "H4": "4 hours"}
```

---

## Test Commands

```bash
# TTE
python combo_main.py --maintain-only    # Run maintenance + snapshots
python combo_main.py --validate         # Validate config
python combo_main.py --fresh            # Delete alerts & recreate

# Test API connectivity
python -c "from tte.config import ComboConfig; from tte.snapshot_worker import StockBuddyClient; c = ComboConfig(); cl = StockBuddyClient(c); print(cl.get_pending_snapshots(5))"

# Stock Buddy
cd "C:/Users/dassa/Work/Stock-Buddy-App"
npm run dev
npx tsc --project tsconfig.json --noEmit
```
