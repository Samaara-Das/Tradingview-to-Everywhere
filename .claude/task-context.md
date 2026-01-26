# Task Context Tracker

This file is automatically updated by Claude Code hooks to maintain context across sessions.

**Last Updated**: 2026-01-26 20:45:00

**Current Task Master Task**: Get the TTE Screener working

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

### In Progress
- None

### Pending Subtasks (in order)
- 1.8: Add Kernel AO regular divergences Logic 1 to screener and test

---

## This Session's Work (2026-01-26)

### Internal Divergence Detection - WORKING ✅

**Problem**: USDCHF Daily had a bullish internal divergence visible in Multi Oscillator indicator, but screener didn't detect it.

**Root Causes Found & Fixed**:

1. **`log.info()` in `request.security()` shows wrong symbol** - Created test script to debug directly on chart symbol

2. **Array index -1 out of bounds error** - When `deepestIdx` (or `highestIdx`) was 0, the loop `for i = 0 to deepestIdx - 1` became `for i = 0 to -1`, causing Pine Script to iterate to -1 and crash on `array.get(pinkAos, -1)`

**Fixes Applied**:

1. Created `TTE Internal Div Debug.txt` test script for single-symbol debugging
2. Added `if deepestIdx > 0` guard in `detectBullishIntDiv()` (both test script and main screener)
3. Added `if highestIdx > 0` guard in `detectBearishIntDiv()` (main screener)

**Result**: Internal divergences now working on H4 and D1 timeframes. USDCHF bullish internal divergence successfully detected on 2025-04-03.

---

## Previous Session's Work (2026-01-25)

### Internal (Same-Side) Divergence Added to Screener ✅

Implemented Internal/Same-Side divergence detection for the screener based on the Multi Oscillator indicator.

**What is Internal Divergence?**
Unlike Logic 2 divergence which compares swing points across different AO ranges, Internal divergence compares swing points within the SAME oscillator range:
- **Bullish Internal**: Within a negative AO range, compare pink sub-ranges (AO falling). If previous pink had deeper AO but higher price, and current pink has shallower AO but lower price → bullish divergence (momentum improving despite lower price)
- **Bearish Internal**: Within a positive AO range, compare purple sub-ranges (AO rising). If previous purple had higher AO but lower price, and current purple has lower AO but higher price → bearish divergence (momentum weakening despite higher price)

**Changes Made:**

1. **Added helper functions:**
   - `findLowestPriceInRange(startShift, endShift)` - Returns [lowest price, shift of lowest]
   - `findHighestPriceInRange(startShift, endShift)` - Returns [highest price, shift of highest]

2. **Added detection functions:**
   - `detectBullishIntDiv(osc, maxLookback)` - Detects bullish internal divergence within current negative AO range
   - `detectBearishIntDiv(osc, maxLookback)` - Detects bearish internal divergence within current positive AO range

3. **Updated `checkSignalWithOB()`:**
   - Now returns 14 values (was 12): 2 NWE + 8 OB + 2 Logic 2 div + 2 Internal div timestamps

4. **Updated all 20 request.security() calls:**
   - H4 (10 symbols) and D1 (10 symbols) now receive 14 values each
   - Added `intBullTm*` and `intBearTm*` variables for internal divergence timestamps

5. **Updated debug table:**
   - Changed from Logic 2 columns to Internal divergence columns
   - Headers: Symbol | H4 IntBull | H4 IntBear | D1 IntBull | D1 IntBear
   - Uses lime/red colors to distinguish from Logic 2 (which was aqua/fuchsia)

**Logic Details:**

For Bullish Internal Div:
1. Must be in negative AO range (osc < 0)
2. Must be in a pink sub-range (AO falling, `osc <= osc[1]`)
3. Find the deepest (most negative) pink sub-range in this negative range
4. Compare current pink to deepest pink:
   - Current AO higher (less negative): `currPinkLowestAo > deepestPinkAo`
   - Current price lower: `currPinkPriceLowest < deepestPinkPriceLowest`
5. Return timestamp of current pink's lowest price

For Bearish Internal Div:
1. Must be in positive AO range (osc > 0)
2. Must be in a purple sub-range (AO rising, `osc > osc[1]`)
3. Find the highest purple sub-range in this positive range
4. Compare current purple to highest purple:
   - Current AO lower: `currPurpleHighestAo < highestPurpleAo`
   - Current price higher: `currPurplePriceHighest > highestPurplePriceHighest`
5. Return timestamp of current purple's highest price

---

## Previous Session's Work (2026-01-17)

### Swing Point Detection - WORKING CORRECTLY ✅

Fixed swing point overwrite bug where previous swing high/low was detected at wrong bars.

---

## Bugs Fixed (All Sessions)

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

1. **Subtask 1.8** - Add Kernel AO Logic 1 divergence to screener and test
2. **Clean up debug logs** - Remove verbose logging from screener once all divergences are working
3. **Complete Task 1** - Get the screener fully working with all indicators

---

## Files Referenced
- `Pine Script Code/TTE Screener.txt` - Main screener with NWE + OB/FVG + Internal Divergence Debug Table
- `Pine Script Code/TTE Internal Div Debug.txt` - **NEW** Single-symbol test script for debugging internal divergence
- `Pine Script Code/Kernel AO Divergence.txt` - Original indicator reference
- `Pine Script Code/aoDiv library.txt` - Divergence library
- `Pine Script Code/Multi Oscillator_swing high low.txt` - Reference for same side divergence
- `Pine Script Code/logic/Regime 1 Reversal logic for SB.md` - Signal requirements

---

## Current Debug Table Columns
| Symbol | H4 IntBull | H4 IntBear | D1 IntBull | D1 IntBear |
|--------|------------|------------|------------|------------|
| Shows timestamps of Internal divergences on H4 and D1 timeframes |
