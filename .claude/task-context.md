# Task Context Tracker

This file is automatically updated by Claude Code hooks to maintain context across sessions.

**Last Updated**: 2026-01-28 20:52:13

**Current Task Master Task**: Build Tiered Screener Architecture (Option C)

---

## Architecture Decision (2026-01-28)

### The Problem

On 28th Jan 2026, while building the TTE Screener with all 3 indicators (NWE, OB & FVG, Divergence) running on 10 symbols, we hit a **memory limit problem**. Pine Script has a hard limit of **40 `request.security()` calls** per script (64 with Ultimate plan).

The full screener was using ~24 calls for just 8 symbols (8 × 3 timeframes). Scaling to 40+ symbols and adding more indicators to the chain was impossible with a single script.

After discussing with Papa, we evaluated 3 architecture options and decided **Option C (Tiered Architecture)** works best for our scaling goals.

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

### Option C: Tiered Architecture ✅ CHOSEN

```
┌─────────────────────────────────────────────────────┐
│  TIER 1: NWE Screeners (always running)             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ NWE Scan #1 │  │ NWE Scan #2 │  │ NWE Scan #3 │  │
│  │ Sym 1-20    │  │ Sym 21-40   │  │ Sym 41-60   │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │
└─────────┼────────────────┼────────────────┼─────────┘
          │                │                │
          └────────────────┴────────────────┘
                           │ NWE alerts (JSON)
                           ▼
┌─────────────────────────────────────────────────────┐
│  PYTHON ORCHESTRATOR (tiered_orchestrator.py)       │
│  - Receives: {"symbol":"GBPAUD","nwe":"bullish"}    │
│  - Adds GBPAUD to "hot list"                        │
│  - Maintains hot list with expiry (24hr)            │
│  - Periodically processes hot symbols               │
└─────────────────────┬───────────────────────────────┘
                      │ For each hot symbol
                      ▼
┌─────────────────────────────────────────────────────┐
│  TIER 2: Detailed Checks (on-demand via Selenium)   │
│                                                     │
│  For each hot symbol:                               │
│  1. Open chart → Load OB indicator → Read output    │
│  2. If OB found → Load DIV indicator → Read output  │
│  3. If DIV found → FIRE FULL SIGNAL (Level 3)       │
│                                                     │
│  Signal Levels:                                     │
│  - Level 1: NWE only                                │
│  - Level 2: NWE + OB                                │
│  - Level 3: NWE + OB + DIV (full signal)            │
└─────────────────────────────────────────────────────┘
```

**How it works:**
- **Tier 1**: Lightweight NWE-only screeners run continuously in TradingView
  - Each screener watches 20 symbols (uses 40 request.security calls for H4+D1)
  - Fires JSON alerts: `{"symbol":"GBPAUD","nwe":"bullish","tf":"H4,D1"}`
  - Only alerts when NWE state CHANGES (not every bar)

- **Hot List**: Python orchestrator maintains a list of "hot" symbols
  - Symbols with active NWE signals go on the hot list
  - Hot list entries expire after 24 hours
  - Symbols removed when NWE signal ends

- **Tier 2**: Python uses Selenium to check OB and Divergence
  - Only checks symbols on the hot list (~5-10% of total)
  - Opens chart, loads OB & FVG indicator, reads output
  - If OB found, loads Divergence indicator, reads output
  - Fires full trading signal if all conditions met

**Pros:**
- Scales to **unlimited symbols** (just add more NWE screeners)
- **Efficient** - only checks OB/DIV for symbols that have NWE (~5-10%)
- Can **add unlimited indicators** to the chain (loaded sequentially)
- Hot list **persists** - rechecks symbols periodically
- Clean separation of concerns (Pine for screening, Python for orchestration)

**Cons:**
- Most complex architecture
- Requires Python orchestrator code
- Selenium checks take time (but only for hot symbols)

**Why We Chose Option C:**
1. We want to scale to 40+ symbols - Option A can't handle this efficiently
2. We want to add more indicators in future - Option C allows unlimited indicators
3. NWE triggers only ~5-10% of the time - no need to check OB/DIV for all symbols always
4. Hot list concept allows periodic rechecks while NWE signal persists

---

### Files Created for Option C

1. **`Pine Script Code/TTE NWE Screener.txt`** - Tier 1 NWE-only screener
   - Watches 20 symbols on H4 and D1 timeframes
   - Uses 40 request.security() calls
   - Fires JSON alerts on NWE state changes
   - Pre-configured with 20 currency pairs

2. **`tiered_orchestrator.py`** - Python orchestrator module
   - `HotSymbol` dataclass - tracks symbols with active NWE signals
   - `Tier2Result` dataclass - captures OB/DIV findings
   - `TieredOrchestrator` class with methods:
     - `on_nwe_alert()` - receives NWE alerts from TradingView
     - `process_hot_symbols()` - checks pending symbols for OB/DIV
     - `_check_tier2()` - performs Selenium-based OB/DIV checks
   - **TODO**: Implement `_check_ob_indicator()` and `_check_divergence_indicator()` based on indicator output format

---

## Task Progress Summary

### Completed Subtasks
- 1.1: Increased symbols from 5 to 20 in the screener
- 1.2: Added NWE indicator to screener (H4 + Daily timeframes, 10 symbols)
- 1.3: Added OB & FVG indicator to screener (H4, Daily, Weekly timeframes) ✅ **COMPLETE**
- 1.4: Add Kernel AO regular divergences (original task) ✅ **DONE** (covered by 1.6)
- 1.6: Add Kernel AO regular divergences Logic 2 to screener ✅ **COMPLETE**
- 1.7: Test Logic 2 divergence matches original Kernel AO Divergence indicator ✅ **COMPLETE**
- 1.5: Add Multi Oscillator same side divergence to screener ✅ **COMPLETE** (tested & working on H4/D1)
- 1.9: Implement Regime 1 Reversal signal logic ✅ **COMPLETE** (debug table shows BUY/SELL signals)
- **NWE Zone Overlap Fix** ✅ **COMPLETE** - Fixed zone detection to use middle lines (upper_avg/lower_avg)
- **Real-Time Signal Updates** ✅ **COMPLETE** - Alert functionality with JSON format, state tracking
- **Pine Script Compilation Fixes** ✅ **COMPLETE** - Fixed function ordering and scope warnings

### In Progress
- **Option C Architecture Implementation** - Building tiered screener system
  - ✅ Created TTE NWE Screener (Tier 1)
  - ✅ Created tiered_orchestrator.py skeleton
  - 🔲 Implement `_check_ob_indicator()` method
  - 🔲 Implement `_check_divergence_indicator()` method
  - 🔲 Integrate orchestrator with existing alert handling

### Pending Subtasks (in order)
- Complete Tier 2 indicator check methods (OB & DIV)
- Test end-to-end flow: NWE alert → hot list → Tier 2 check → signal
- Deploy multiple NWE screeners for full symbol coverage

### Recently Completed (2026-01-28)
- **Architecture Decision** ✅ - Evaluated 3 options, chose Option C (Tiered Architecture)
- **TTE NWE Screener** ✅ - Created lightweight Tier 1 screener for 20 symbols
- **tiered_orchestrator.py** ✅ - Created Python orchestrator skeleton with hot list management
- **Conditional Execution Test** ✅ - Proved that conditional indicator execution inside functions causes 41% mismatch rate (history buffer fragmentation)

### Recently Completed (2026-01-27)
- **Real-Time Signal Updates Implementation** ✅ **COMPLETE** - Added alert() calls with JSON format, state tracking for change detection
- **Pine Script Compilation Fixes** ✅ **COMPLETE** - Fixed "function not found" errors and scope warnings

---

## This Session's Work (2026-01-28)

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

## Next Steps

1. **Complete Tier 2 methods** - Implement `_check_ob_indicator()` and `_check_divergence_indicator()` in tiered_orchestrator.py
2. **Integrate with alert handling** - Connect TieredOrchestrator to existing handle_alerts.py
3. **Test NWE Screener** - Deploy TTE NWE Screener in TradingView and verify alerts fire correctly
4. **Deploy multiple screeners** - Create additional NWE screener instances for full symbol coverage
5. **End-to-end testing** - Test complete flow from NWE alert through Tier 2 checks to final signal

---

## Files Referenced

### Option C Architecture Files (NEW)
- `Pine Script Code/TTE NWE Screener.txt` - **Tier 1** lightweight NWE-only screener (20 symbols)
- `tiered_orchestrator.py` - **Python orchestrator** for hot list management and Tier 2 checks
- `Pine Script Code/TTE Conditional Test.txt` - Test script that proved conditional execution doesn't work (41% mismatch)

### Original Screener Files
- `Pine Script Code/TTE Screener.txt` - Original full screener with all 3 indicators (limited to 8 symbols)
- `Pine Script Code/TTE Internal Div Debug.txt` - Single-symbol test script for debugging internal divergence

### Reference Indicators
- `Pine Script Code/Kernel AO Divergence.txt` - Original Kernel AO Divergence indicator
- `Pine Script Code/aoDiv library.txt` - Divergence library
- `Pine Script Code/Multi Oscillator_swing high low.txt` - Reference for same side divergence
- `Pine Script Code/Nadaraya Watson Envelope.txt` - Original NWE indicator
- `Pine Script Code/OB & FVG.txt` - Original Order Block & FVG indicator

### Documentation
- `Pine Script Code/logic/Regime 1 Reversal logic for SB.md` - Signal requirements

---

## Current Signal Table Columns
| Symbol | Signal | Lvl | Details |
|--------|--------|-----|---------|
| Shows BUY/SELL signals with level (1-3) and which TFs triggered conditions |

**Example Details:** `NWE:H4,D1 OB:W1 DIV:H4` means NWE triggered on H4 and D1, OB on W1, DIV on H4

**Tooltip on Hover:** Shows NWE band prices and OB/FVG type + formation timestamp
