# Task Context Tracker

This file is automatically updated by Claude Code hooks to maintain context across sessions.

**Last Updated**: 2026-01-27 22:14:24

**Current Task Master Task**: Get the TTE Screener working ✅ **WORKING**

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
- None

### Pending Subtasks (in order)
- Integrate alerts with Python backend (when ready)

### Recently Completed (2026-01-27)
- **Real-Time Signal Updates Implementation** ✅ **COMPLETE** - Added alert() calls with JSON format, state tracking for change detection
- **Pine Script Compilation Fixes** ✅ **COMPLETE** - Fixed "function not found" errors and scope warnings

---

## This Session's Work (2026-01-27)

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

1. **Integrate with Python backend** - Connect TradingView alerts to the Python application
2. **Monitor alerts in production** - Verify alerts fire correctly in real-time
3. **Fine-tune as needed** - Adjust signal logic based on real-world results

---

## Files Referenced
- `Pine Script Code/TTE Screener.txt` - Main screener with Regime 1 Reversal Signal Table + tooltips
- `Pine Script Code/TTE Internal Div Debug.txt` - Single-symbol test script for debugging internal divergence
- `Pine Script Code/Kernel AO Divergence.txt` - Original indicator reference
- `Pine Script Code/aoDiv library.txt` - Divergence library
- `Pine Script Code/Multi Oscillator_swing high low.txt` - Reference for same side divergence
- `Pine Script Code/logic/Regime 1 Reversal logic for SB.md` - Signal requirements
- `Pine Script Code/Nadaraya Watson Envelope.txt` - Original NWE indicator reference

---

## Current Signal Table Columns
| Symbol | Signal | Lvl | Details |
|--------|--------|-----|---------|
| Shows BUY/SELL signals with level (1-3) and which TFs triggered conditions |

**Example Details:** `NWE:H4,D1 OB:W1 DIV:H4` means NWE triggered on H4 and D1, OB on W1, DIV on H4

**Tooltip on Hover:** Shows NWE band prices and OB/FVG type + formation timestamp
