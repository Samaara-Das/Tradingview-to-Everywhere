# Task Context Tracker

This file is automatically updated by Claude Code hooks to maintain context across sessions.

**Last Updated**: 2026-01-30 18:06:55

**Current Task Master Task**: Build Tiered Screener Architecture (Option C) - Webhook-based with Stock Buddy Dashboard

---

## Architecture Evolution

### Phase 1: Initial Problem (2026-01-28)

On 28th Jan 2026, while building the TTE Screener with all 3 indicators (NWE, OB & FVG, Divergence) running on 10 symbols, we hit a **memory limit problem**. Pine Script has a hard limit of **40 `request.security()` calls** per script (64 with Ultimate plan).

The full screener was using ~24 calls for just 8 symbols (8 × 3 timeframes). Scaling to 40+ symbols and adding more indicators to the chain was impossible with a single script.

After discussing with Papa, we evaluated 3 architecture options and decided **Option C (Tiered Architecture)** works best for our scaling goals.

### Phase 2: Architecture Refinement (2026-01-29)

After further analysis, we refined Option C into a **webhook-based architecture** with these key changes:

1. **Webhooks instead of Alert Scraping**: TradingView webhooks deliver alerts directly to Stock Buddy API (faster, more reliable than Selenium scraping)

2. **OBDIV Screener Optimization**: Removed NWE calculation from Tier 2 screener (redundant since Tier 1 already confirmed NWE) and removed table display (signals go to webhook)

3. **Stock Buddy Dashboard**: Signals displayed on web dashboard instead of Pine Script table (scales to 1000+ symbols)

4. **Screenshot-only Selenium**: Python/Selenium now only handles screenshot capture (TradingView webhooks cannot include chart snapshots)

5. **Dynamic Symbol Input**: Python changes OBDIV Screener symbols via Selenium to process hot list in batches of 8

---

### Option A: Pure Pine Script (Multiple Full Screeners)

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Full Screener #1 │  │ Full Screener #2 │  │ Full Screener #3 │
│ Symbols 1-8      │  │ Symbols 9-16     │  │ Symbols 17-24    │
│ NWE + OB + DIV   │  │ NWE + OB + DIV   │  │ NWE + OB + DIV   │
└──────────────────┘  └──────────────────┘  └──────────────────┘
         │                    │                     │
         └────────────────────┴─────────────────────┘
                              │
                       Alerts to Python
```

**How it works:**
- Copy the full screener multiple times
- Each copy watches ~8 symbols (due to request.security limits)
- All indicators run simultaneously for all symbols

**Pros:**
- Simple - just duplicate the screener
- Everything stays in Pine Script

**Cons:**
- Need ~5 screeners for 40 symbols
- Each screener calculates ALL indicators even when NWE doesn't trigger
- Wasteful - 90% of the time, OB/DIV checks are unnecessary
- Hard to add more indicators (already at the limit)

---

### Option B: Lightweight Screeners + Manual Selenium Checks

```
┌──────────────────┐  ┌──────────────────┐
│ NWE Screener #1  │  │ NWE Screener #2  │
│ Symbols 1-20     │  │ Symbols 21-40    │
│ NWE only         │  │ NWE only         │
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         └──────────┬──────────┘
                    │ "GBPAUD has NWE bullish"
                    ▼
┌─────────────────────────────────────────┐
│ Python receives alert                   │
│ Opens chart for GBPAUD                  │
│ Manually loads OB indicator → checks    │
│ Manually loads DIV indicator → checks   │
└─────────────────────────────────────────┘
```

**How it works:**
- NWE-only screeners watch 20 symbols each (lightweight)
- When NWE triggers, Python opens that specific symbol's chart
- Python loads OB indicator, reads output, checks for overlap
- If OB found, Python loads DIV indicator, reads output
- Sequential, one symbol at a time

**Pros:**
- Can watch 40+ symbols with just 2 NWE screeners
- Only does detailed checks when needed
- Can add unlimited indicators (loaded one at a time)

**Cons:**
- Slower - Selenium navigation takes time per symbol
- Sequential processing - checks one symbol at a time
- More complex Python code

---

### Option C: Tiered Architecture ✅ CHOSEN (Refined)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      REFINED WEBHOOK-BASED ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 1: TTE NWE Screener (TradingView)                             │   │
│  │  - 20 symbols, H4 + D1 timeframes                                   │   │
│  │  - Webhook: POST to Stock Buddy /api/nwe                            │   │
│  │  - Payload: {"tier":"nwe","symbol":"X","direction":"bullish",...}   │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STOCK BUDDY API (Vercel + MongoDB)                                 │   │
│  │  - /api/nwe → Adds to hot_list collection                           │   │
│  │  - /api/obdiv → Combines with NWE → final signal                    │   │
│  │  - /api/signals → Dashboard fetches signals                         │   │
│  │  - /api/hot-symbols → Python fetches symbols for Tier 2             │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PYTHON ORCHESTRATOR (Local)                                        │   │
│  │  - Polls /api/hot-symbols for pending Tier 2 checks                 │   │
│  │  - Changes OBDIV Screener symbol inputs (Selenium)                  │   │
│  │  - Takes screenshots for final signals                              │   │
│  │  - Updates /api/signals with screenshot URLs                        │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 2: TTE OBDIV Screener (TradingView)                           │   │
│  │  - 8 symbols (dynamically set by Python)                            │   │
│  │  - Checks OB + Divergence ONLY (NWE removed for efficiency)         │   │
│  │  - NO table display (signals go to webhook)                         │   │
│  │  - Webhook: POST to Stock Buddy /api/obdiv                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STOCK BUDDY DASHBOARD (https://stock-buddy-app.vercel.app)         │   │
│  │  - Real-time signals table with sorting/filtering                   │   │
│  │  - Statistics cards (today, level 3, bullish/bearish)               │   │
│  │  - Screenshot modal for viewing chart snapshots                     │   │
│  │  - Push notifications for new signals                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**How it works (Refined):**

- **Tier 1 (TTE NWE Screener)**: Lightweight NWE-only screener in TradingView
  - Watches 20 symbols on H4 + D1 (40 request.security calls)
  - Fires **webhook** to Stock Buddy `/api/nwe` on NWE zone entry
  - Payload: `{"tier":"nwe","symbol":"GBPAUD","direction":"bullish","timeframes":["H4","D1"]}`

- **Hot List (MongoDB)**: Stock Buddy API maintains hot list in database
  - `hot_list` collection with status: pending_tier2 / tier2_complete / expired
  - Python polls `/api/hot-symbols` to get symbols needing Tier 2 check

- **Tier 2 (TTE OBDIV Screener)**: Focused OB+DIV check screener
  - **NWE removed** (redundant - Tier 1 already confirmed NWE)
  - **Table removed** (signals go to webhook, not display)
  - 8 symbols dynamically set by Python via Selenium
  - Reports **both** bullish and bearish findings (Python matches direction from hot list)
  - Fires **webhook** to Stock Buddy `/api/obdiv`

- **Signal Creation**: Stock Buddy API combines NWE + OBDIV
  - Looks up hot_list to get NWE direction
  - Matches direction with OBDIV findings
  - Calculates level (1=NWE, 2=NWE+OB, 3=NWE+OB+DIV)
  - Creates signal in `signals` collection

- **Screenshot Capture**: Python/Selenium captures chart snapshots
  - Polls `/api/signals?status=pending_screenshot`
  - Navigates to chart, takes screenshot
  - Updates signal with screenshot URL via `/api/signals/{id}`

- **Dashboard**: Stock Buddy web app displays all signals
  - Real-time table with sorting, filtering, search
  - Statistics cards (today, level 3, bullish/bearish)
  - Screenshot modal, notifications, distribution chart

**Key Advantages of Refined Architecture:**
1. **Instant delivery** - Webhooks are faster than alert scraping
2. **Efficient Tier 2** - No redundant NWE calculation
3. **Scalable display** - Dashboard scales to 1000+ symbols
4. **Proof of signals** - Screenshots preserved in database
5. **Direction matching** - OBDIV reports both sides, Python matches correctly

---

### Files for Webhook-Based Architecture

**Pine Script Files (To Create/Modify):**
1. **`Pine Script Code/TTE NWE Screener v2.txt`** - Tier 1 webhook-based screener
   - Watches 20 symbols on H4 + D1
   - Fires webhook with JSON payload on NWE zone entry
   - No table display needed

2. **`Pine Script Code/TTE OBDIV Screener.txt`** - Tier 2 focused screener
   - 8 symbols (dynamically changed by Python)
   - OB + Divergence detection ONLY (no NWE)
   - Reports both bullish and bearish findings
   - Fires webhook with JSON payload

**Stock Buddy API (To Create):**
3. **`pages/api/nwe.js`** - Receives Tier 1 webhooks, adds to hot_list
4. **`pages/api/obdiv.js`** - Receives Tier 2 webhooks, creates signals
5. **`pages/api/signals/index.js`** - GET signals for dashboard
6. **`pages/api/signals/[id].js`** - PATCH signal with screenshot
7. **`pages/api/hot-symbols.js`** - GET pending symbols for Python

**Stock Buddy Dashboard (To Create):**
8. **`app/dashboard/page.jsx`** - Main dashboard page
9. **`components/dashboard/StatsGrid.jsx`** - Statistics cards
10. **`components/dashboard/FilterBar.jsx`** - Filtering controls
11. **`components/dashboard/SignalsTable.jsx`** - Signals table (desktop)
12. **`components/dashboard/CardGrid.jsx`** - Signal cards (mobile)
13. **`components/dashboard/ScreenshotModal.jsx`** - Screenshot viewer

**Python Files (To Update):**
14. **`tiered_orchestrator.py`** - Refactor for webhook-based flow
    - Poll `/api/hot-symbols` instead of maintaining local hot list
    - Change OBDIV Screener symbols via Selenium
    - Capture screenshots and update via `/api/signals/{id}`

**Documentation:**
15. **`.claude/TIERED_ARCHITECTURE_IMPLEMENTATION_PLAN.md`** ✅ Created
    - Complete 9-phase implementation plan
    - API endpoint code, MongoDB schema, component tree

---

## Task Progress Summary

### Historical Progress (TTE Screener Development)
- 1.1: Increased symbols from 5 to 20 ✅
- 1.2: Added NWE indicator (H4 + Daily) ✅
- 1.3: Added OB & FVG indicator (H4, Daily, Weekly) ✅
- 1.4: Add Kernel AO regular divergences ✅ (covered by 1.6)
- 1.5: Add Multi Oscillator same side divergence ✅
- 1.6: Add Kernel AO regular divergences Logic 2 ✅
- 1.7: Test Logic 2 divergence matches original indicator ✅
- 1.9: Implement Regime 1 Reversal signal logic ✅
- NWE Zone Overlap Fix ✅
- Real-Time Signal Updates ✅
- Pine Script Compilation Fixes ✅

### Current Implementation Plan (9 Phases, 17 Tasks)

See full plan: `.claude/TIERED_ARCHITECTURE_IMPLEMENTATION_PLAN.md`

| Phase | Task# | Description | Status | Blocked By |
|-------|-------|-------------|--------|------------|
| 1 | #1 | Select 20 symbols for deployment | pending | - |
| 2 | #2 | Create TTE NWE Screener (Tier 1) | pending | #1 |
| 3 | #3 | Create TTE OBDIV Screener (Tier 2) | pending | #1 |
| 4 | #4 | Create Stock Buddy API endpoints | pending | - |
| 5 | #5 | Set up MongoDB collections | pending | - |
| 6 | #6 | Update Python orchestrator | pending | #4, #5 |
| 7 | #7 | Dashboard - Statistics Cards | pending | #4 |
| 7 | #8 | Dashboard - Filter Bar | pending | - |
| 7 | #9 | Dashboard - Signals Table | pending | - |
| 7 | #10 | Dashboard - Mobile Cards | pending | - |
| 7 | #11 | Dashboard - Screenshot Modal | pending | - |
| 7 | #12 | Dashboard - Notifications | pending | - |
| 7 | #13 | Dashboard - Real-time Updates | pending | - |
| 7 | #14 | Dashboard - Distribution Chart | pending | - |
| 7 | #15 | Dashboard - Main Page Assembly | pending | - |
| 8 | #16 | End-to-end integration testing | pending | #2, #3, #6, #15 |
| 9 | #17 | Production deployment | pending | #16 |

### Selected 20 Symbols (Phase 1)

```
Batch 1 (1-10):        Batch 2 (11-20):
1.  EURUSD             11. GBPAUD
2.  GBPUSD             12. EURAUD
3.  USDJPY             13. EURGBP
4.  USDCHF             14. EURCAD
5.  AUDUSD             15. GBPCAD
6.  NZDUSD             16. AUDCAD
7.  USDCAD             17. NZDJPY
8.  GBPJPY             18. CADJPY
9.  EURJPY             19. CHFJPY
10. AUDJPY             20. AUDNZD
```

### Key Decisions (2026-01-29)
1. **Webhooks over Alert Scraping**: Instant delivery, more reliable
2. **OBDIV without NWE**: Avoids redundant calculation
3. **No Table in Screener**: Dashboard scales better
4. **Both Directions in OBDIV**: Python matches with hot list direction
5. **Screenshot-only Selenium**: TradingView webhooks can't include images
6. **Batch Processing**: 8 symbols per OBDIV batch (hot list may have more)

---

## This Session's Work (2026-01-29)

### Architecture Refinement and Task Planning ✅

**Goal**: Create comprehensive implementation plan for webhook-based tiered architecture.

**Research Completed:**

1. **Point-Capital Branch Analysis**
   - Reviewed alert scraping pattern via Selenium
   - Reviewed MongoDB integration (`local_db.py`)
   - Understood `send_everywhere()` flow for storing alerts

2. **TradingView Webhook Limitations**
   - Confirmed: Webhooks can only send JSON data (no images)
   - Decision: Use webhooks for data, Selenium only for screenshots

3. **Architecture Decisions Made:**
   - Webhooks replace alert scraping (faster, more reliable)
   - NWE removed from OBDIV screener (redundant calculation)
   - Table removed from OBDIV screener (dashboard scales better)
   - OBDIV reports both directions (Python matches with hot list)
   - Batch processing for hot symbols (8 per screener run)

**Artifacts Created:**

1. **Implementation Plan Document** ✅
   - File: `.claude/TIERED_ARCHITECTURE_IMPLEMENTATION_PLAN.md`
   - 9 phases with detailed specifications
   - API endpoint code, MongoDB schema
   - Component tree for dashboard
   - Signal flow timeline
   - Deployment and testing checklists

2. **Task Management** ✅
   - Created 17 tasks across 9 phases
   - Set up task dependencies
   - Tasks tracked in Claude Code task system

3. **Task Context Update** ✅
   - This file updated with new architecture details
   - Added selected 20 symbols
   - Added webhook payload formats
   - Added MongoDB schema
   - Added dashboard layout

**Session Summary:**
Successfully transitioned from original tiered architecture concept to refined webhook-based architecture with Stock Buddy dashboard. All planning artifacts created and ready for implementation.

---

## Previous Session's Work (2026-01-28)

### Conditional Execution Test - FAILED ❌

Before deciding on Option C, we tested whether we could conditionally execute indicator calculations inside Pine Script functions to save request.security() calls.

**Test Setup** (`TTE Conditional Test.txt`):
- Created two versions: `checkSignalUNCOND()` (always calculates all indicators) and `checkSignalCOND()` (only calculates OB if NWE triggers, only calculates DIV if OB triggers)
- Ran both side-by-side and compared outputs

**Results:**
- **Mismatches: 8383 of 20312 bars (41.27%)**
- Many red X markers on chart showing where outputs differed

**Root Cause**: Pine Script **history buffer fragmentation**
- When functions using `[]` operators are called conditionally inside `if` blocks, they don't maintain consistent history buffers
- The function's internal history references (`close[1]`, `ta.sma()`, etc.) get fragmented when the function isn't called every bar
- This causes the function to return different values compared to when it's called unconditionally

**Conclusion**: Cannot optimize by conditionally skipping indicator calculations in Pine Script. Must use external orchestration (Option C) to achieve conditional execution.

---

## Previous Session's Work (2026-01-27)

### Real-Time Signal Updates Implementation ✅

**Goal**: Make the screener give fresh, real-time signals that update every tick for alert generation.

**Changes Made:**

1. **Reduced symbols from 10 to 8**
   - Removed AUDUSD (s09) and NZDUSD (s10)
   - Kept: GBPAUD, AUDJPY, EURCAD, EURGBP, USDCHF, GBPUSD, EURUSD, USDJPY
   - New request.security count: 24 calls (8×3 TFs) - 60% utilization

2. **Added state tracking variables**
   - `var int prevBuyLvl01..08` and `var int prevSellLvl01..08`
   - Persist across bars to track previous signal state

3. **Added alert message builder function**
   - `buildAlertMsg(sym, signal, level, details)` returns JSON string
   - Format: `{"symbol":"XXX","signal":"BUY","level":3,"details":"NWE:H4,D1 OB:W1 DIV:H4"}`

4. **Added change detection and alert() calls**
   - Runs on `barstate.isconfirmed` for non-repainting behavior
   - Compares current buyLvl/sellLvl to previous values
   - Fires `alert()` with `alert.freq_once_per_bar_close` when signal changes
   - Updates prev state variables after firing

5. **Updated table size from 12 to 10 rows** (header + 8 symbols + buffer)

**Alert Behavior:**
- Non-repainting: fires once when bar closes with signal change
- JSON format for easy parsing by Python backend
- Only fires when signal level changes (not every bar)

### Pine Script Compilation Fixes ✅

Fixed errors and warnings that occurred after adding alert functionality:

**Errors Fixed (Function Not Found):**
- `buildNweDetail`, `buildObDetail`, `buildDivDetail`, `buildAlertMsg`, `getSymbolName` were being called before they were defined
- **Fix**: Moved the alert logic block to AFTER all helper function definitions
- Pine Script requires functions to be defined BEFORE they are called

**Warnings Fixed (Scope Issues):**
- `findLowestAoInRange` and `findHighestAoInRange` were called inside conditional `if` blocks
- **Fix**: Extracted function calls to the function level (outside `if` blocks) in both `detectBullishDiv` and `detectBearishDiv`
- Pine Script recommends calling functions unconditionally for consistency

**Screener Status:** Working fine - compiles without errors or warnings

---

### Previous Session's Work

### NWE Zone Overlap Fix ✅

**Problem**: The screener was missing the middle lines (`upper_avg` and `lower_avg`) that exist in the original NWE indicator, causing incorrect zone detection.

**Root Cause**: The original NWE has 6 boundary lines (3 upper + 3 lower), but the screener only had 4. The zone detection was incorrectly using `yhat` (regression line) as a boundary instead of the actual zone boundaries.

**Correct Zone Structure:**
```
upper_far   ─────  (highest red line)
              UPPER FAR ZONE
upper_avg   ─────  (middle red line) ← WAS MISSING
              UPPER AVG ZONE
upper_near  ─────  (bottom red line)
yhat        ═════  (regression line - NOT a zone boundary)
lower_near  ─────  (top green line)
              LOWER AVG ZONE
lower_avg   ─────  (middle green line) ← WAS MISSING
              LOWER FAR ZONE
lower_far   ─────  (lowest green line)
```

**Fixes Applied:**

1. **Updated `calcNWE()` function:**
   - Added `upper_avg = (upper_far + upper_near) / 2`
   - Added `lower_avg = (lower_far + lower_near) / 2`
   - Now returns 7 values instead of 5

2. **Fixed zone overlap logic in `checkSignalWithOB()`:**
   - Bullish: `(low <= lower_near and high >= lower_avg) or (low <= lower_avg and high >= lower_far)`
   - Bearish: `(high >= upper_near and low <= upper_avg) or (high >= upper_avg and low <= upper_far)`

### Added Tooltips to Signal Table ✅

**Feature**: Hover over Details cell to see expanded info about NWE zones and OB/FVG overlap.

**Changes Made:**

1. **Modified `checkSignalWithOB()` return values (14 → 18 values):**
   - Added 4 NWE band prices: `lower_near`, `lower_avg`, `upper_near`, `upper_avg`

2. **Updated all 20 H4/D1 request.security() calls:**
   - Added new variables: `lnNear##_h4/d1`, `lnAvg##_h4/d1`, `unNear##_h4/d1`, `unAvg##_h4/d1`

3. **Added tooltip helper functions:**
   - `buildNweTooltip()` - Shows NWE band prices for each TF that triggered
   - `buildObTooltip()` - Shows OB/FVG type and formation timestamp for each TF
   - `buildDetailsTooltip()` - Combines NWE and OB info

4. **Added tooltips to all 10 table rows:**
   - Details cell now shows tooltip on hover

**Tooltip Format:**
```
NWE Zone:
H4: 1.23456 - 1.23789
D1: 1.23123 - 1.23567

OB/FVG Zone:
H4: Unmit OB @ 01-15 08:00
W1: Bull FVG @ 01-10 00:00
```

### Removed Debug Logs ✅
- Cleaned up all `log.info()` debug statements from the screener

---

## Previous Session's Work (2026-01-26)

### Regime 1 Reversal Signal Logic - IMPLEMENTED ✅

Implemented Task 1.9: Signal detection logic that checks conditions in order (NWE → OB/FVG → Divergence).

**Signal Logic (Sequential Check):**

1. **Level 1 - NWE Zone Check** (H4 or D1)
   - Bullish: bar overlaps lower_avg zone (lower_near to lower_avg) OR lower_far zone (lower_avg to lower_far)
   - Bearish: bar overlaps upper_avg zone (upper_near to upper_avg) OR upper_far zone (upper_avg to upper_far)

2. **Level 2 - OB/FVG Overlap** (H4 or D1 or W1) - only checked if NWE passes
   - Bullish: bullish OB, bullish FVG, or breaker support
   - Bearish: bearish OB, bearish FVG, or breaker resistance

3. **Level 3 - Divergence on Current Bar** (H4 or D1) - only checked if OB passes
   - Bullish: Logic 2 or Internal bullish divergence with timestamp == current time
   - Bearish: Logic 2 or Internal bearish divergence with timestamp == current time

**Priority Rule:** If both BUY and SELL conditions exist, show the one with higher level. If tied, show BUY.

---

## Bugs Fixed (All Sessions)

### NWE Zone Detection Bug (2026-01-27)
- **Error**: NWE zone overlap detected incorrectly (was using yhat instead of zone boundaries)
- **Cause**: Missing `upper_avg` and `lower_avg` middle lines from `calcNWE()`
- **Fix**: Added middle line calculations and fixed zone overlap logic to check between the 3 boundary lines

### Array Index -1 Out of Bounds (2026-01-26)
- **Error**: `Runtime error: Error on bar 5948: In 'array.get()' function. Index -1 is out of bounds, array size is 10.`
- **Cause**: When `deepestIdx=0` (first pink is deepest), loop `for i = 0 to deepestIdx - 1` becomes `for i = 0 to -1`, and Pine Script iterates downward to -1
- **Fix**: Added `if deepestIdx > 0` guard before loop in `detectBullishIntDiv()`, and `if highestIdx > 0` guard in `detectBearishIntDiv()`

### Swing Point Overwrite Bug (2026-01-17)
- **Error**: Previous swing high/low detected at wrong shift (e.g., 89 instead of 25)
- **Cause**: After finding 2 ranges, code kept updating range1 values while scanning for the other polarity
- **Fix**: Added guards `negRangesFound < 2` and `posRangesFound < 2` to stop tracking after finding 2 ranges

### NaN Kernel AO Values (2026-01-16)
- **Error**: All oscillator values were NaN, causing "No negative/positive range found"
- **Cause**: `rationalQuadratic()` with `x0=120` + SMA(40) needs ~160 bars of history
- **Fix**: Find first valid bar before scanning, start from that offset

### Reversed OB Detection (2026-01-15)
- **Error**: Screener detected overlap with reversed OB on EURCAD 4H
- **Cause**: Lifecycle depth limit prevented checking for reversals that happened after the window
- **Fix**: Added continuation loop to check reversal all the way to shift 0 when breaker detected

### False Overlap on Formation Bar (2026-01-14)
- **Error**: FVG detected as overlapping on the bar where it formed
- **Cause**: At i=2/3, gap uses high[0]/low[0], so current bar is part of zone
- **Fix**: Added `i >= 4` guard to all overlap checks

### Pine Script Runtime Error (2026-01-13)
- **Error**: Negative historical reference (-1 bars back)
- **Cause**: Loop at i=2 accessing low[i-3] = low[-1]
- **Fix**: Handle i=2 separately, start main loop at i=3

---

## Kernel AO Divergence Reference

**Oscillator**: `kernelFast - kernelSlow`
- Fast: `rationalQuadratic(close, h=5, alpha=8, x0=25)` with SMA(4) smoothing
- Slow: `rationalQuadratic(close, h=34, alpha=3, x0=120)` with SMA(40) smoothing

**Color Terminology:**
- **Purple** = AO is rising (`osc > osc[1]`, i.e., `diff > 0`)
- **Pink** = AO is falling (`osc <= osc[1]`, i.e., `diff <= 0`)

**Divergence Types:**
1. **Logic 2** - Compares across 2 separate AO ranges (negative to negative, positive to positive)
2. **Internal** - Compares within 1 AO range (pink sub-ranges in negative, purple sub-ranges in positive)

---

## Next Steps (Recommended Order)

### Phase 1-3: Pine Script Screeners
1. **Finalize 20 symbols** (Task #1) - Confirm the forex pairs list
2. **Create TTE NWE Screener v2** (Task #2) - Webhook-based, 20 symbols, H4+D1
3. **Create TTE OBDIV Screener** (Task #3) - OB+DIV only, 8 symbols, webhook

### Phase 4-5: Backend Infrastructure
4. **Create Stock Buddy API endpoints** (Task #4) - 5 endpoints for webhooks + dashboard
5. **Set up MongoDB collections** (Task #5) - hot_list and signals with indexes

### Phase 6: Python Integration
6. **Update Python orchestrator** (Task #6) - Poll API, change symbols via Selenium, take screenshots

### Phase 7: Dashboard (Can parallel with Phase 6)
7. **Build dashboard components** (Tasks #7-15) - Stats, filters, table, mobile, modal, notifications

### Phase 8-9: Testing & Deployment
8. **End-to-end integration testing** (Task #16) - Full signal flow test
9. **Production deployment** (Task #17) - Deploy all components

### Quick Start Recommendation
Begin with Tasks #1, #4, #5 in parallel (no dependencies), then proceed to #2, #3, then #6.

---

## Files Referenced

### Architecture Documentation
- `.claude/TIERED_ARCHITECTURE_IMPLEMENTATION_PLAN.md` - **Complete 9-phase implementation plan** with code, schemas, and diagrams

### Pine Script Files
- `Pine Script Code/TTE NWE Screener.txt` - **Tier 1** lightweight NWE screener (to be refactored for webhooks)
- `Pine Script Code/TTE Screener.txt` - Original full screener (reference for OBDIV logic)
- `Pine Script Code/TTE Conditional Test.txt` - Test proving conditional execution doesn't work

### Reference Indicators
- `Pine Script Code/Kernel AO Divergence.txt` - Original divergence indicator
- `Pine Script Code/aoDiv library.txt` - Divergence library
- `Pine Script Code/Nadaraya Watson Envelope.txt` - Original NWE indicator
- `Pine Script Code/OB & FVG.txt` - Original Order Block & FVG indicator

### Python Files
- `tiered_orchestrator.py` - **Orchestrator** (to be updated for webhook-based flow)
- `main.py` - Main entry point
- `handle_alerts.py` - Alert handling (reference for point-capital pattern)
- `database/local_db.py` - MongoDB connection (reference)

### Stock Buddy (External Repository)
- URL: https://stock-buddy-app.vercel.app/
- API endpoints to create: /api/nwe, /api/obdiv, /api/signals, /api/hot-symbols

### Point-Capital Branch (Reference)
- Contains MongoDB + alert scraping pattern
- `Alert message for screeners.md` - JSON formats for OB, NW, SB screeners

---

## Stock Buddy Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  HEADER: Logo | Notifications Badge | Profile                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  STATS GRID                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ TODAY    │  │ LEVEL 3  │  │ LEVEL 2  │  │ BULLISH  │  │ BEARISH  │      │
│  │   12     │  │    3     │  │    5     │  │    8     │  │    4     │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
├─────────────────────────────────────────────────────────────────────────────┤
│  FILTER BAR                                                                 │
│  Level: [All ▼] Direction: [All ▼] Symbol: [Search...] Period: [24h ▼]     │
│  Sort: [Time ▼] [↑↓]    [ ] Screenshots only    [🔴 Live]                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  SIGNALS TABLE (Desktop) / CARD GRID (Mobile)                               │
│  ┌───────┬────────┬───────┬───────┬────────┬──────┬───────┬──────────┐     │
│  │ Time  │ Symbol │ Dir   │ Level │ NWE    │ OB   │ DIV   │ Actions  │     │
│  ├───────┼────────┼───────┼───────┼────────┼──────┼───────┼──────────┤     │
│  │ 14:30 │ GBPAUD │ 🟢BUY │ ⭐⭐⭐│ H4,D1  │ W1   │ H4    │ 📸 📈 🔗 │     │
│  │ 14:15 │ EURUSD │ 🔴SELL│ ⭐⭐  │ D1     │ H4   │ -     │ 📸 📈 🔗 │     │
│  └───────┴────────┴───────┴───────┴────────┴──────┴───────┴──────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Webhook Payload Formats

### Tier 1 (NWE Screener → /api/nwe)
```json
{
  "tier": "nwe",
  "symbol": "GBPAUD",
  "direction": "bullish",
  "timeframes": ["H4", "D1"],
  "timestamp": 1672531200
}
```

### Tier 2 (OBDIV Screener → /api/obdiv)
```json
{
  "tier": "obdiv",
  "symbol": "GBPAUD",
  "bull_ob": {"found": true, "tf": "W1", "type": "OB"},
  "bull_div": {"found": true, "tf": "H4", "type": "Logic2"},
  "bear_ob": {"found": false},
  "bear_div": {"found": false},
  "timestamp": 1672531200
}
```

## MongoDB Collections

### hot_list
```javascript
{
  symbol: "GBPAUD",
  direction: "bullish",
  nwe_timeframes: ["H4", "D1"],
  status: "pending_tier2",  // pending_tier2 | tier2_complete | expired
  updated_at: Date
}
```

### signals
```javascript
{
  symbol: "GBPAUD",
  direction: "bullish",
  level: 3,
  nwe_tf: ["H4", "D1"],
  ob_tf: "W1",
  div_tf: "H4",
  screenshot_url: "https://...",
  status: "complete",  // pending_screenshot | complete
  created_at: Date
}
```
