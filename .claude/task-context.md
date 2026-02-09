# Task Context Tracker

**Last Updated**: 2026-02-09
**Current Task**: Screener validation complete ✅ - Ready to begin Combo architecture implementation
**Last Session**: Cleaned up screener for production, renamed timeframe variables, uploaded to Google Drive
**Active Branch**: `combo-architecture` (created for Combo mode implementation)

---

## Task Progress Summary (Built-in Tasks)

**Screener Work - COMPLETE** ✅:
| ID | Task | Status |
|----|------|--------|
| 44 | Validate TTE Screener signal accuracy | **completed** ✅ |
| 49 | Test NWE signal detection on all timeframes | **completed** ✅ |
| 50 | Test DIV signal detection on all timeframes | **completed** ✅ |
| 51 | Test OB/FVG signal detection on all timeframes | **completed** ✅ |
| 52 | Comment out debug table in TTE Screener | **completed** ✅ |
| 53 | Create new git branch for Architecture 1 (Combo mode) | **completed** ✅ |
| 54 | Rename legacy timeframe variables to actual values | **completed** ✅ |
| 23 | Upload all screener versions to Google Drive | **completed** ✅ |

**Testing - DEFERRED** (Will be done after combo system is live):
| ID | Task | Status | Notes |
|----|------|--------|-------|
| 22 | Test webhook alert payload and trigger frequency | pending | Requires live combo system |
| 37 | Test end-to-end webhook flow | pending | Requires API endpoints built |

**Combo Implementation - READY TO START** 🚀:
| ID | Task | Status | Dependencies |
|----|------|--------|--------------|
| 24 | Rewrite config.py for Combo architecture | **READY** | None |
| 25 | Rewrite api_client.py for Combo architecture | **READY** | None |
| 26-31 | Python orchestrator implementation | pending | Tasks #24, #25 |
| 32-38 | Stock Buddy API implementation | **READY** | None (except #33 needs #32) |

**Completed Count**: 27 tasks
**Pending Count**: 17 tasks (7 ready to start)

---

## Session History

### Session: 2026-02-09 (Screener Production Cleanup & Timeframe Variable Renaming)

**Goal**: Finalize screener for production by cleaning up debug code, renaming confusing legacy variables, and preparing for Combo architecture implementation

**Tasks Completed**:

1. **Task #52 - Comment Out Debug Table** ✅
   - Commented out table declaration (line 1095)
   - Commented out helper functions (lines 836-1002)
   - Commented out table rendering for all 4 symbols (lines 1175-1254)
   - Kept `plot(na)` statement for valid Pine Script indicator
   - **Result**: Production-ready screener with no debug UI clutter
   - **Commit**: `807845c` - "Comment out debug table in TTE Screener for production"

2. **Task #53 - Create Combo Architecture Branch** ✅
   - Created new branch: `combo-architecture`
   - Pushed to remote with tracking
   - **Result**: Ready for Combo mode implementation
   - **Branch**: Now working on `combo-architecture` (diverged from `tiered-orchestrator`)

3. **Task #54 - Rename Legacy Timeframe Variables** ✅
   - **Problem**: Variable names contradicted their actual values
     - `TF_H4 = '60'` (actually 1 hour, not 4 hour)
     - `TF_D1 = '240'` (actually 4 hour, not daily)
     - `TF_W1 = 'D'` (actually daily, not weekly)

   - **Changes Made** (82+ occurrences):
     - Constants: `TF_H4` → `TF_1H`, `TF_D1` → `TF_H4`, `TF_W1` → `TF_D1`
     - All variable suffixes: `_h4` → `_1h`, `_d1` → `_h4`, `_w1` → `_d1`
     - Updated all comments and documentation
     - Preserved JSON payload strings (already correct)

   - **Strategy**: Used three-step sed replacement with temporary placeholders to avoid naming collisions
   - **Result**: Code is now self-documenting - variable names match actual timeframe values
   - **Commit**: `d7e0b6b` - "Rename legacy timeframe variables to match actual values"

4. **Task #23 - Upload Screener Versions to Google Drive** ✅
   - Uploaded TTE Screener.txt (production combo screener)
   - Uploaded TTE NWE Screener v2.txt (deprecated Tier 1)
   - Uploaded TTE OBDIV Screener v2.txt (deprecated Tier 2)
   - **Result**: All screener versions backed up to Google Drive

**User Questions Answered**:
- Clarified screener configuration: 4 symbols, 3 timeframes (1H, H4, D1)
- Explained actual timeframes vs legacy variable names
- Confirmed all screener/testing tasks are complete

**Screener Configuration (Final)**:
- **Symbols**: 4 active (GBPAUD, AUDJPY, EURCAD, EURGBP) - configurable up to 20
- **Timeframes**:
  - 1H (`TF_1H = '60'`) - NWE, OB/FVG, Divergence
  - H4 (`TF_H4 = '240'`) - NWE, OB/FVG, Divergence
  - D1 (`TF_D1 = 'D'`) - OB/FVG only
- **Status**: Production-ready, validated, uploaded

**Next Steps Identified**:
- Task #22 (webhook testing) will be done AFTER combo system is live
- Ready to begin Combo architecture implementation:
  - Tasks #24-25 (config.py, api_client.py) - Ready to start
  - Tasks #26-31 (orchestrator) - Blocked by #24-25
  - Tasks #32-38 (Stock Buddy API) - Ready to start (7 tasks available)

**Files Modified**:
- `Pine Script Code/TTE Screener.txt` - Debug table commented out, timeframe variables renamed
- `.claude/task-context.md` - Updated with session progress

**Commits** (on `combo-architecture` branch):
- `807845c` - Comment out debug table in TTE Screener for production
- `cc90253` - Update task context with OB/FVG gap condition alignment session notes
- `d7e0b6b` - Rename legacy timeframe variables to match actual values

**Result**:
✅ **All screener work complete** - validated, cleaned, uploaded, production-ready
🚀 **Ready to begin Combo architecture implementation** - 7 tasks unblocked and ready to start

---

### Session: 2026-02-09 (OB/FVG Gap Condition Alignment with Standalone Indicator)

**Goal**: Ensure TTE Screener's OB/FVG detection uses the exact same logic as the standalone `OB & FVG.txt` indicator

**Investigation Process**:

1. **Thorough analysis of both indicators** using parallel Explore agents:
   - Analyzed standalone `OB & FVG.txt`: `isBullishOB()` (lines 127-148), `isBearishOB()` (lines 103-124), `addOB()` (lines 194-217), `updateOBStates()` (lines 220-304)
   - Analyzed screener `TTE Screener.txt`: `scanOBRange()` (lines 351-657), bullish detection (lines 400-506), bearish detection (lines 508-657)

2. **Detailed logic comparison findings**:

   | Aspect | Standalone | Screener | Match? |
   |--------|-----------|----------|--------|
   | Sweep condition | Local extremum check | Same formula | ✅ Identical |
   | Gap condition | 2 conditions (redundant second) | 1 condition | ⚠️ Subset |
   | gapLevel/FVG zone | bar[0]'s price at detection | bar[i-2]/[i-3] (equivalent) | ✅ Equivalent |
   | Lifecycle (tested/broken/reversed) | Same logic | Same logic | ✅ Identical |
   | FVG fill check | `low[1]`/`high[1]` (prev bar) | `low[j]`/`high[j]` (each bar) | ✅ Screener more thorough |

3. **Key finding**: Gap conditions are mathematically equivalent:
   - Standalone bearish: `low[idx] > high[0] AND low[idx] > low[0]` — second condition redundant (if `low[idx] > high[0]` and `high[0] >= low[0]`, then `low[idx] > low[0]` is always true)
   - Screener bearish: `low[i] > high[i-2]` — same relative check, just missing the redundant second condition
   - Same applies to bullish gap

4. **Deep trace confirmed equivalence**: The standalone checks bar[2]/bar[3] vs bar[0] on every new bar. The screener loops backward checking the same relative bar offsets (bar[i] vs bar[i-2]/bar[i-3]). Both access the same historical price data.

**Changes Made** (`Pine Script Code/TTE Screener.txt`):

1. **Bullish gap condition** (lines 404-405, done by another Claude Code chat):
   ```pinescript
   // Before:
   bool bullGap2 = high[i] < low[i - 2]
   bool bullGap3 = high[i] < low[i - 3]
   // After (matches OB & FVG.txt line 131):
   bool bullGap2 = high[i] < low[i - 2] and high[i] < high[i - 2]
   bool bullGap3 = high[i] < low[i - 3] and high[i] < high[i - 3]
   ```

2. **Bearish gap condition** (lines 512-513):
   ```pinescript
   // Before:
   bool bearGap2 = low[i] > high[i - 2]
   bool bearGap3 = low[i] > high[i - 3]
   // After (matches OB & FVG.txt line 107):
   bool bearGap2 = low[i] > high[i - 2] and low[i] > low[i - 2]
   bool bearGap3 = low[i] > high[i - 3] and low[i] > low[i - 3]
   ```

**Other changes from parallel Claude Code chat** (preserved during revert+reapply):
- Divergence threshold fix (lines 293, 320) — removed `±0.0001` thresholds
- OB & FVG indicator name fix (`OB & FVG Indicator` → `Order Block Indicator`)
- Timeframe references in logic docs updated (H4/Daily/Weekly → H1/H4/Daily)

**Approach**: Reverted file to git HEAD (removing all debug logs/symbol isolation from previous debug session), then applied only the gap condition changes. This cleanly removed ~30 debug log lines and restored all 4 symbols + all timeframes.

**Commit**: `fd9102d` - Align screener OB/FVG gap conditions and divergence thresholds with original indicators

**Result**:
✅ Gap conditions now exactly match standalone OB & FVG indicator
✅ All debug logs from previous investigation removed
✅ All symbols and timeframes restored
⏳ Awaiting user verification on TradingView

---

### Session: 2026-02-09 (Logic 2 Divergence Threshold Fix)

**Goal**: Fix divergence detection in TTE Screener to match the original `Kernel AO Divergence` indicator exactly

**Problem Identified**:
The TTE Screener had extra threshold checks in divergence detection that the original indicator did not have:
- **Bullish** (line 293): `if prevDownlegAO < -0.0001 and currDownlegAO > prevDownlegAO` — extra `-0.0001` threshold
- **Bearish** (line 320): `if prevUplegAO > 0.0001 and currUplegAO < prevUplegAO` — extra `0.0001` threshold

The original `Kernel AO Divergence` indicator uses simple comparisons with no threshold:
- Bullish: `if lowest1 < lowest2`
- Bearish: `if highest1 > highest2`

**Changes Made** (`Pine Script Code/TTE Screener.txt`):
1. **Line 293** (bullish divergence): `if prevDownlegAO < -0.0001 and currDownlegAO > prevDownlegAO` → `if prevDownlegAO < currDownlegAO`
2. **Line 320** (bearish divergence): `if prevUplegAO > 0.0001 and currUplegAO < prevUplegAO` → `if prevUplegAO > currUplegAO`

**Impact Assessment**:
- Slightly more divergences may be detected (cases where prev AO was between 0 and ±0.0001)
- In practice, negligible — `0.0001` is extremely small, and the scan functions already start from `0.0` filtering values that never cross zero
- Main purpose: **correctness** — matching the original indicator exactly

**Analysis verified no changes needed for**:
- Oscillator calculation (`calcKernelOsc`) — identical kernel parameters
- AO range search functions — same logic as aoDiv library
- Swing point tracking — correctly maps shifts
- Leg direction checks — equivalent to original's bar_index comparisons
- AO scan boundaries — match the original

**Result**:
✅ Divergence detection now matches original `Kernel AO Divergence` indicator exactly
⏳ Awaiting user verification on TradingView

---

### Session: 2026-02-09 (Divergence Detection Debug & Verification)

**Goal**: Add debug logs to understand divergence detection behavior and verify it works correctly across all symbols and timeframes

**Process**:

1. **Added comprehensive debug logs** to divergence detection functions:
   - Modified `detectBullishDiv()` to accept `debugLabel` parameter (lines ~272-297)
   - Modified `detectBearishDiv()` to accept `debugLabel` parameter (lines ~299-337)
   - Added logs showing:
     - Swing point conditions (`inDownleg`, `inUpleg`, `lowerLow`, `higherHigh`)
     - Shift values and price comparisons
     - AO (Awesome Oscillator) validation checks
     - Warning logs when divergence detected
   - Updated `checkSignalWithOB()` to create debug label: `syminfo.ticker + " TF=" + tf`
   - Added result logging when divergence found

2. **Initial Problem Discovered**:
   - Debug logs only appeared for 4th symbol (XRPUSD), not for all 4 symbols
   - Root cause: Using `syminfo.ticker` in global scope only shows chart's symbol
   - Solution: Pass `debugLabel` parameter through functions so it works inside `request.security()` context

3. **User Testing Results**:
   - User confirmed: "the divergence is being detected correctly across the 1h/4h timeframes and all 4 symbols"
   - Verified divergence detection working as expected

4. **Cleanup**:
   - Removed all debug logs after verification
   - Reverted functions to original signatures (removed `debugLabel` parameters)
   - File: `Pine Script Code/TTE Screener.txt`

**Key Learning**:
- Inside `request.security()` context, `syminfo.ticker` refers to the **requested symbol**, not the chart symbol
- This is why passing debug labels through functions was necessary during testing
- Divergence detection works correctly - no bugs found

**Result**:
✅ Task #50 completed - DIV signal detection verified working on all timeframes (1H, H4) and all 4 symbols
✅ Code cleaned up - all debug logs removed
✅ Divergence detection confirmed accurate

**Files Modified**:
- `Pine Script Code/TTE Screener.txt` - Added debug logs, then removed them after verification

---

### Session: 2026-02-09 (NWE Bug Fix Implementation & Timezone Uniformity)

**Goal**: Fix NWE signal detection to work across all symbols and ensure timezone uniformity

**Issues Addressed**:

**1. Bug #11 - NWE Chart Symbol Dependency (FIXED)**:
- **Problem**: NWE signals only detected for the chart's active symbol, not all 4 monitored symbols
- **Root Cause**: NWE detection used chart's builtin `low`/`high` variables, which always reference the active chart symbol
- **Solution**: Moved NWE detection INSIDE `checkSignalWithOB()` function
  - Detection now happens in `request.security()` context where `low`/`high` refer to the correct symbol
  - Each symbol's signals are detected using that symbol's own price data

**2. Timezone Uniformity Issue (FIXED)**:
- **Problem**: Tooltips used `syminfo.timezone` (exchange timezone) causing inconsistent display
- **Impact**: Different symbols could show different timezones, confusing users
- **Solution**: Changed all tooltip functions to use `"UTC"` explicitly
  - Added " UTC" suffix to clarify timezone
  - Ensures uniform display regardless of chart symbol or exchange

**Implementation Details**:

**File Modified**: `Pine Script Code/TTE Screener.txt`

**Change 1 - NWE Detection Logic** (lines 649-691):
```pinescript
checkSignalWithOB(simple string tf) =>
    // Calculate NWE envelope
    [yhat, upper_near, upper_far, upper_avg, lower_near, lower_far, lower_avg] = calcNWE(...)

    // NWE overlap detection using symbol's own low/high (in request.security context)
    bool bullZone1 = low <= lower_near and high >= lower_avg
    bool bullZone2 = low <= lower_avg and high >= lower_far
    bool nweBull = bullZone1 or bullZone2

    bool bearZone1 = high >= upper_near and low <= upper_avg
    bool bearZone2 = high >= upper_avg and low <= upper_far
    bool nweBear = bearZone1 or bearZone2

    // Calculate zone names
    string bullZone = getNweZoneName(true, low, high, ...)
    string bearZone = getNweZoneName(false, low, high, ...)

    // Return 24 values (was 20): added nweBull, bullZone, nweBear, bearZone
```

**Change 2 - request.security() Calls** (lines 724-734):
```pinescript
// H4 timeframe - now receives 24 values including NWE signals
[lnNear01_h4, lnAvg01_h4, unNear01_h4, unFar01_h4,
 nweBull01_h4, bullZone01_h4, nweBear01_h4, bearZone01_h4,
 bullF01_h4, ...] = request.security(s01, TF_H4, checkSignalWithOB(TF_H4))
```

**Change 3 - Timezone Uniformity** (lines 883-935):
```pinescript
// Before
str.format_time(timestamp, 'yyyy-MM-dd HH:mm', syminfo.timezone)

// After
str.format_time(timestamp, 'yyyy-MM-dd HH:mm', "UTC") + ' UTC'
```

**Functions Updated**:
- `buildNweTooltip()` - line 883
- `buildObTooltip()` - line 907
- `buildDivTooltip()` - line 923

**Change 4 - Removed Chart-TF Detection** (lines 747-806):
- Deleted entire obsolete section that detected signals on chart timeframe
- No longer needed since detection happens inside `request.security()` context

**Verification**:
✅ User confirmed: "the NWE signals are being detected across timeframes and symbols!"

**Result**:
- All 4 symbols now show independent NWE signals regardless of active chart
- Tooltips display uniform UTC timestamps with " UTC" suffix
- Bug #11 resolved
- Timezone consistency achieved

**Commits**:
- Commit 1 (2026-02-09): Fix NWE signal detection to use correct symbol prices and overlap logic
- Commit 2 (pending): Add timezone uniformity to all tooltip displays

---

### Session: 2026-02-07 (Signal Accuracy Testing - Additional NWE Bugs Found)

**Goal**: Test TTE Screener signal accuracy across all timeframes and signal types

**Task Setup**:
Created three sequential testing subtasks:
1. Task #49: Test NWE signal detection (in_progress)
2. Task #50: Test DIV signal detection (pending, blocked by #49)
3. Task #51: Test OB/FVG signal detection (pending, blocked by #50)

**New Bugs Discovered During NWE Testing**:

**Bug #11 - NWE signals only display for chart's current symbol**:
- **Symptom**: NWE signals only appear in the debug table for the symbol that matches the current chart
- **Example**: If chart is on GBPAUD, only GBPAUD row shows NWE signals; other symbols (AUDJPY, EURCAD, EURGBP) show no NWE signals
- **Expected**: All 4 symbols should show NWE signals if price is in NWE zones, regardless of chart symbol
- **Impact**: Critical - screener cannot detect signals for symbols other than the active chart symbol
- **Status**: Not fixed yet
- **Related**: This is different from the previously fixed bugs (timestamp and disappearing signals)

**Bug #12 - No DIV signals displayed**:
- **Symptom**: DIV column in debug table has not shown any signals during testing
- **Status**: Needs investigation - could be legitimate (no divergences present) or a detection bug
- **Related**: Previous session (2026-02-05) confirmed divergence detection was working correctly, but required OB overlap to reach Level 3

**Previous Bugs Fixed (Last Session)**:
1. ✅ Bug #1: Incorrect timestamps (HTF bar time instead of current bar time)
2. ✅ Bug #2: Disappearing signals (vanished when price still in zone)
3. ✅ Bug #3: Missing tooltips (empty tooltips not displayed)

**Testing Status**:
- ❌ NWE signals: Bugs found (#11 - chart symbol dependency)
- ⏳ DIV signals: No signals observed yet (needs investigation - Bug #12)
- ✅ OB/FVG signals: Previously confirmed correct (2026-02-07 tooltip session)

**Next Steps**:
1. Fix Bug #11 (NWE chart symbol dependency)
2. Investigate Bug #12 (missing DIV signals)
3. Complete NWE testing (Task #49)
4. Begin DIV testing (Task #50)
5. Begin OB/FVG testing (Task #51)

---

### Session: 2026-02-07 (NWE Signal Detection Bug Fixes)

**Goal**: Fix two critical NWE signal detection bugs in TTE Screener

**Problems Identified**:
1. **Bug 1 - Incorrect Timestamps**: NWE signals showed HTF bar timestamps (e.g., 5 hours old) instead of current bar time
   - Example: On BTCUSD 1H chart at 19:30, bearish NWE signal showed timestamp 14:00 (5 hours stale)
   - Root cause: `request.security()` returned data from previous closed H4 bar, not current 1H bar

2. **Bug 2 - Disappearing Signals**: Signals vanished even when price remained in NWE zone
   - Signal display required BOTH `nweBull/nweBear` boolean AND non-empty zone name string
   - When HTF bar data changed, zone name calculation failed, causing signals to disappear

**Solution Implemented**: Chart-timeframe signal detection pattern

**Key Changes**:

1. **Modified `checkSignalWithOB()` function** (lines 649-682):
   - Removed NWE signal detection logic (nweBull, nweBear booleans and zone names)
   - Now returns only NWE band levels (lower_near, lower_avg, upper_near, upper_avg)
   - Return values reduced from 22 to 20
   - Rationale: Detecting signals inside `request.security()` meant detection occurred in HTF context

2. **Updated `request.security()` calls** (lines 715-725):
   - Updated all 8 calls (4 symbols × 2 timeframes: H4, D1)
   - Changed destructuring to receive 20 values instead of 22
   - Removed `nweBull`, `nweBear`, `bullZone`, `bearZone` from assignments

3. **Added chart-timeframe NWE signal detection** (new section after line 729):
   - Created comprehensive section detecting signals on chart timeframe (shift 0)
   - For each symbol/timeframe (8 total combinations):
     - Calculates `nweBull`/`nweBear` booleans using chart's `low`/`high` with HTF band levels
     - Calculates `lower_far` and `upper_far` as: `lowerFar = lowerAvg - (lowerNear - lowerAvg)`
     - Calls `getNweZoneName()` with chart's price data
   - Benefits:
     - Timestamps always reflect current bar (shift 0), not HTF bar
     - Signals persist correctly while price remains in zone
     - No more "disappearing signals" bug

**Signal Detection Flow Change**:

Before (buggy):
```
request.security(symbol, H4, checkSignalWithOB(H4))
  ↓ checkSignalWithOB() executes in H4 context
  ↓ Uses H4 bar's low/high (previous closed bar - 5 hours old)
  ↓ Returns nweBull, nweBear, zone names from H4 context
  ↓ Debug table shows H4 timestamp (stale data)
```

After (fixed):
```
request.security(symbol, H4, checkSignalWithOB(H4))
  ↓ Returns only NWE band levels from H4
  ↓
Chart timeframe logic (shift 0):
  ↓ Uses current bar's low[0]/high[0]
  ↓ Compares with HTF band levels
  ↓ Detects signals on current bar
  ↓ Debug table shows current bar timestamp
```

**What Was Fixed**:
✅ Timestamps now always reflect current bar (shift 0) on chart timeframe
✅ Signals persist correctly as long as price remains in NWE zone
✅ Signal accuracy improved - uses actual current bar data instead of stale HTF data
✅ Debug table tooltip always shows current bar timestamp

**What Stayed the Same**:
✅ NWE band calculations (unchanged - still calculated in HTF for stability)
✅ OB/FVG detection (unchanged)
✅ Divergence detection (unchanged)
✅ Debug table layout (unchanged)
✅ JSON payload structure (timestamps update, format stays same)
✅ Alert firing frequency (`alert.freq_all` - already implemented)

**Files Modified**:
- `Pine Script Code/TTE Screener.txt`:
  - Lines 649-682: Modified `checkSignalWithOB()` function
  - Lines 715-725: Updated `request.security()` calls
  - Lines 730-790 (new): Added chart-timeframe NWE signal detection section
  - Total: ~100 lines modified/added

**Important Memory Created**:
- Documented that there is NO rate limit for TradingView alerts (previous "15 alerts per 3 minutes" documentation was incorrect)
- Documented chart-timeframe detection pattern as best practice for HTF signal detection
- File: `C:\Users\dassa\.claude\projects\C--Users-dassa-Work-For-Poolsifi-tradingview-to-everywhere\memory\MEMORY.md`

**Tasks Completed**:
- Task #45: Modify checkSignalWithOB() to return only band levels
- Task #46: Update request.security() calls for 20-value returns
- Task #47: Add chart-timeframe NWE signal detection
- Task #48: Verify debug table uses current timestamp

**Verification Steps** (for user testing):
1. Compilation check - verify script loads in TradingView
2. Timestamp accuracy - check tooltip shows current bar time, not past HTF bar time
3. Signal persistence - verify signals don't disappear while price in zone
4. Zone name accuracy - verify tooltip shows correct zone (lower_avg, lower_far, upper_avg, upper_far)

---

### Session: 2026-02-07 (TTE Screener Tooltip Bug Fix)

**Goal**: Fix missing tooltips in TTE Screener debug table for specific NWE cells

**Problem Identified**:
Two specific cells in the TTE Screener debug table were not showing tooltips on hover:
1. ETHUSD row → NWE-1H column (no tooltip)
2. BTCUSD row → NWE-H4 column (no tooltip)

All other cells showed tooltips correctly, indicating a specific data/logic issue rather than a systemic display problem.

**Root Cause**:
The `buildNweTooltip()` function (lines 866-875) was returning empty strings when:
- No signal exists (bullish=false AND bearish=false), OR
- Signal exists BUT zone string is empty (str.length(zone) == 0)

TradingView does not display empty tooltip strings, so these cells appeared to have no tooltip.

**Fix Implemented** (`Pine Script Code/TTE Screener.txt` lines 866-887):

1. **Removed zone length requirement** from signal checks
   - Before: `if bullish and str.length(bullZone) > 0`
   - After: `if bullish` (zone length checked separately)

2. **Added zone fallback handling**
   - If zone is empty, displays "Unknown" instead of omitting tooltip
   - Pattern: `string zone = str.length(bullZone) > 0 ? bullZone : 'Unknown'`

3. **Added "No Signal" fallback**
   - When neither bullish nor bearish signals exist, tooltip shows "No Signal"
   - Prevents TradingView from hiding empty tooltips

4. **Improved code structure**
   - Added clear section comments (bullish/bearish/no signal sections)
   - Better readability for future maintenance

**Impact**:
✅ All NWE cells now always display tooltips (never empty)
✅ Users get clear feedback: signal details or "No Signal"
✅ Unknown zones handled gracefully ("Zone: Unknown")
✅ Easier debugging (can see what indicator is calculating)

**Testing Status**:
- Code modified and verified in Pine Script file
- User is currently testing signal accuracy on TradingView:
  - ✅ OB/FVG signals confirmed correct
  - ⏳ NWE signals testing in progress
  - ⏳ Divergence signals testing in progress

**Files Modified**:
- `Pine Script Code/TTE Screener.txt` - Updated `buildNweTooltip()` function (9 lines changed)

---

### Session: 2026-02-06 (Architecture Analysis & Webhook Decision)

**Goal**: Evaluate two architectures (combo screener vs separate screeners) and decide webhook destination

**Architecture Decision: Combo Screener (Architecture 1) Chosen**

Two architectures analyzed:
- **Arch 1 (Combo)**: Single TTE Screener with NWE + OB + DIV combined, 4 symbols/batch, 1 alert/batch
- **Arch 2 (Separate)**: 3 separate screeners (NWE, OB, DIV), 4 symbols/batch, 3 alerts/batch

Key factors favoring Arch 1:
- 264 alert cycles vs 792 (3x less browser automation)
- ~6.6 hour full rotation vs ~19.8 hours
- No signal merging complexity — single webhook contains complete signal with level
- Combo screener already built and tested
- 4 symbols is the hard limit (more causes memory/runtime errors), eliminating Arch 2's batch size advantage
- Runtime errors handled by TTE periodically restarting stopped alerts via TV UI

**Webhook Destination Decision: Stock Buddy API**

Considered: Stock Buddy API (Vercel), MongoDB Atlas directly, custom webhook server

Stock Buddy chosen because:
- Existing endpoint pipeline: webhook → Zod validation → MongoDB → RTK Query → React grid
- Vercel Pro ($20/mo) handles the traffic easily
- MongoDB Atlas M2 ($9/mo) provides comfortable storage
- MongoDB directly not viable (can't set auth headers from TV webhooks)

**Screener Updated Mid-Session** — old version had signal change detection, new version does NOT:

Old version (was in codebase at start of session):
- `var int prevBuyLvl01-08` state tracking
- `buyLvl != prevBuyLvl` comparison before `alert()`
- `barstate.isconfirmed` guard
- `alert.freq_once_per_bar_close` frequency
- Flat JSON: `{"symbol":"XXX","signal":"BUY","level":3,"details":"NWE:H4,D1 OB:W1 DIV:H4"}`
- Signal levels 0/1/2/3 calculated in Pine Script

Updated version (replaced mid-session by user from another chat):
- **NO signal change detection** — fires on every bar if any signal exists
- `alert.freq_once_per_bar` — fires on first tick of each bar (not bar close)
- **NO barstate.isconfirmed guard** — fires on realtime bars before close
- Rich nested JSON payload:
  ```json
  {"timestamp":<ms>,"signals":[{"symbol":"XXX","nwe":[...],"ob_fvg":[...],"divergence":[...]}]}
  ```
- **NO signal hierarchy** — all raw signals sent, Stock Buddy must calculate levels
- Symbols with NO signals excluded from payload entirely

**Traffic Impact of Updated Screener**:
- Estimated ~500-5,000 webhooks/day (depending on how many symbols in zones)
- Bursts of 20-50 at bar boundaries
- Stock Buddy endpoint MUST deduplicate server-side (upsert by symbol, only update if signals changed)

**Combo Screener `request.security()` Usage**: 24 of 40 max
- 8 x H4 (NWE+OB+DIV combined) = 8 calls
- 8 x D1 (NWE+OB+DIV combined) = 8 calls
- 8 x W1 (OB only) = 8 calls

**New Endpoint Needed**: `/api/tte/signal` on Stock Buddy to receive combo screener's rich JSON format (replaces two-phase NWE + OBDIV pattern). Must handle deduplication since screener fires every bar.

**Skills Used**: /pinescript, /mongodb, /stock-buddy — all loaded for domain expertise

---

### Session: 2026-02-05 (TTE Screener Consolidation & Divergence Debugging)

**Goal**: Consolidate NWE and OBDIV screeners into single TTE Screener, debug divergence detection

**Changes Implemented**:

1. **Consolidated Screener** (`screeners on TV/TTE Screener.txt`):
   - Combined NWE + OB/FVG + Divergence detection into single indicator
   - Signal levels: Level 1 (NWE only) → Level 2 (NWE + OB) → Level 3 (NWE + OB + DIV)
   - Hierarchical signal logic: `buyLvl = nweBull ? (obBull ? (divBull ? 3 : 2) : 1) : 0`
   - Timeframes: H4, D1 for NWE/Divergence; H4, D1, W1 for OB/FVG

2. **Divergence Debugging Session**:
   - Added `getBullDivDebug()` function to return intermediate values
   - Added debug `request.security` call for EURCAD H4
   - Created expanded debug table showing: BullTm, CurrTm, cLowS, inDL, LL, prevAO, currAO
   - **Finding**: Divergence detection IS working correctly
   - **Root Cause of "missing" Level 3**: Signal requires OB overlap (Level 2) before divergence can boost to Level 3
   - This is intended behavior - removed debug code after verification

3. **Symbol Count Adjustments**:
   - Started with 8 symbols, reduced to 4 for testing
   - Temporarily reduced to 3 for debugging
   - Final: 4 symbols (GBPAUD, AUDJPY, EURCAD, EURGBP)

**Key Files Modified**:
- `screeners on TV/TTE Screener.txt` - Main consolidated screener (1000+ lines)

**Next Step**: Test if signal table displays correct NWE, OB, and Divergence signals

---

### Session: 2026-02-04 (Data Subscription Error Handling - Task 5.3)

**Goal**: Handle TradingView "data subscription" error in Create Alert dialog when screener contains symbols the user's plan doesn't support

**Problem Identified**:
1. Wrong CSS selector: Code used `div[data-name="error-hint"]` but actual HTML uses `div[data-qa-id="error-hint"]`
2. No error differentiation: Code detected errors but didn't distinguish data subscription errors
3. Phase 1 stops entirely: Returned on failure instead of continuing to next batch

**Changes Implemented**:

1. **`open_tv.py` - Fixed CSS selector** (line 972):
   - Changed `div[data-name="error-hint"]` → `div[data-qa-id="error-hint"]`

2. **`open_tv.py` - Updated `create_webhook_alert()` return type** (lines 1007-1147):
   - Changed from `bool` to `tuple[bool, str | None]`
   - Return values:
     - `(True, None)` - Success
     - `(False, None)` - Generic error
     - `(False, "data_subscription")` - Data subscription error
     - `(False, "condition_invalid")` - Screener not in dropdown
   - Added error text extraction: `error_text = error_element.text.lower()`
   - Added data subscription detection: `if "data subscription" in error_text`

3. **`orchestrator.py` - Phase 1 handling** (lines 273-288):
   - Unpacks tuple: `success, error_type = self.browser.create_webhook_alert(...)`
   - On data subscription error: Logs warning, marks symbols as scanned, returns
   - On other errors: Logs error and returns

4. **`orchestrator.py` - Phase 2 handling** (lines 457-469):
   - Unpacks tuple: `success, error_type = self.browser.create_webhook_alert(...)`
   - On data subscription error: Logs warning, continues to next batch
   - On other errors: Logs error, continues to next batch

**Behavior Change**:
- Before: Any alert creation error would stop Phase 1 entirely
- After: Data subscription errors mark symbols as scanned and skip to next batch/cycle

**Error Detection**: Looks for `"data subscription"` in error text (case-insensitive), robust to minor TradingView wording changes

---

### Session: 2026-02-04 (Hot Symbol Expiration System Implementation)

**Goal**: Implement timeframe-based hot symbol expiration with separate documents per timeframe

**Changes Implemented**:

#### Stock Buddy API (`C:\Users\dassa\Work\Stock-Buddy-App`)

1. **`src/lib/tte/schemas.ts`**:
   - Changed `HotListDocument.nwe_timeframes` (array) → `nwe_timeframe` (single string)
   - Removed `updated_at` field (no refresh logic needed)
   - Added `TIMEFRAME_SECONDS` mapping: `{5m: 300, 15m: 900, 1H: 3600, H4: 14400, D1: 86400}`
   - Added `getExpirationDate(timestamp, timeframe)` helper function
   - Added `nweBatchWebhookSchema` for batch webhook format

2. **`src/app/api/tte/nwe/route.ts`** - Complete rewrite:
   - Handles batch format: `{tier: "nwe", symbols: [{symbol, direction, timeframes}, ...], timestamp}`
   - Creates separate documents for each symbol+timeframe combination
   - No-refresh logic: skips if document already exists for symbol+direction+timeframe
   - Uses `getExpirationDate()` to calculate `expires_at`

3. **`src/app/api/tte/hot-symbols/expired/route.ts`** (NEW):
   - DELETE endpoint removes all documents where `expires_at < now`
   - Returns `{success: true, deleted_count: N}`

4. **`src/app/api/tte/hot-symbols/route.ts`**:
   - Added `include_expired` query parameter (default: false)
   - Filters out expired symbols by default: `expires_at: { $gt: now }`

5. **`src/lib/tte/collections.ts`**:
   - Updated `getPendingHotSymbols()` to filter expired by default
   - Updated `getHotListEntry()` with optional `timeframe` parameter
   - Updated `markHotListComplete()` with optional `timeframe` parameter
   - Marked `upsertHotListEntry()` as deprecated
   - Added `deleteExpiredHotSymbols()` helper function

6. **`src/app/api/tte/obdiv/route.ts`**:
   - Fixed to use new `nwe_timeframe` field (singular) instead of `nwe_timeframes`

#### TTE Orchestrator (`C:\Users\dassa\Work\For Poolsifi\tradingview to everywhere`)

1. **`api_client.py`**:
   - Updated `get_hot_symbols()` docstring for new schema
   - Added `delete_expired_hot_symbols()` method

2. **`orchestrator.py`**:
   - Added call to `api_client.delete_expired_hot_symbols()` at startup in `create_orchestrator()`

**Commits**:
- Stock Buddy: `83cf092` - Implement timeframe-based hot symbol expiration system

**Verification Tests (All Passed)**:
1. ✅ NWE batch webhook - Creates separate documents per timeframe
2. ✅ Timeframe-based expiration - 5m entry expired after 5 minutes, 15m/1H still valid
3. ✅ No-refresh logic - `Created 0 hot list entries (3 skipped)` when re-sending
4. ✅ Filter expired by default - Without param: 3 docs, with `include_expired=true`: 4 docs
5. ✅ DELETE expired endpoint - `Deleted 40 expired hot symbols`
6. ✅ New document schema - `nwe_timeframe` (string), no `updated_at`, correct `expires_at`

---

### Session: 2026-02-04 (Orchestrator Bug Fixes & Hot Symbol Expiration Design)

**Goal**: Fix orchestrator bugs found during E2E testing and design hot symbol expiration logic

#### Chronological Tasks & Discussions

**1. Implemented Plan: Alert Dialog Close & Save Layout Fixes**

From previous plan file, implemented two fixes:

- **Fix 1: `_close_alert_dialog()` in `open_tv.py`** (lines 1130-1159)
  - Added Cancel button as primary close method (`button[name="cancel"][data-qa-id="cancel"]`)
  - Falls back to close (X) button if Cancel not found
  - Added proper logging instead of silent `except: pass`

- **Fix 2: Save layout before switching in `orchestrator.py`** (lines 151-154)
  - Added `self.browser.save_layout()` before `change_layout()`
  - Added 1-second pause to ensure save completes

**2. Bug Fix: Condition Dropdown Selector Timeout**

- **Problem**: Alert creation failed with "Timeout waiting for condition dropdown or options menu"
- **Cause**: TradingView UI changed, old selector `span[data-qa-id="ui-lib-Input main-series-select"]` no longer worked
- **Fix**: Added alternative selector `span[data-qa-id="ui-kit-disclosure-control main-series-select"]` in `_validate_alert_condition()` (open_tv.py lines 1175-1198)
- **Result**: Logs now show "Found condition dropdown with selector: span[data-qa-id="ui-kit-disclosure-control main-series-select"]"

**3. Bug Fix: `open_log_tab()` Timeout on Empty Log**

- **Problem**: When switching to Log tab for webhook monitoring, it timed out waiting for `div[data-name="alert-log-item"]` which doesn't exist when log is empty
- **Location**: `resources/utils.py` lines 135-144
- **Fix**: Changed verification from waiting for log item to waiting for tab selection (`aria-selected="true"`), matching pattern used in `open_alert_tab()`
- **Result**: Log tab opens successfully even when empty

**4. E2E Test Run - Phase 1 Success, Phase 2 Timeout**

Test run showed:
- Phase 1 (NWE): Webhook created and detected after 7.6s ✓
- Alert deleted successfully ✓
- API marked 20 symbols as scanned ✓
- Phase 2 (OBDIV): Layout switch worked, symbols input worked, alert created
- Phase 2: Webhook wait timed out after 60.6s (no OBDIV signal)

**5. Discussion: Hot Symbol Expiration Logic**

User raised concern about stale hot symbols being processed in OBDIV.

**API Response Fields Explained**:
| Field | Format | Description |
|-------|--------|-------------|
| `_id` | String | MongoDB document ID |
| `symbol` | String | Trading symbol (e.g., "EURUSD") |
| `direction` | String | `"bullish"` or `"bearish"` |
| `nwe_timeframes` | Array | Timeframes where NWE triggered (e.g., `["H4", "D1"]`) |
| `nwe_timestamp` | Unix epoch (seconds) | When NWE signal was detected |
| `created_at` | ISO 8601 UTC | When added to database |
| `updated_at` | ISO 8601 UTC | Last modification time |
| `expires_at` | ISO 8601 UTC | When signal becomes invalid |
| `status` | String | `"pending_tier2"`, `"tier2_complete"`, or `"expired"` |

**Current behavior** (per `docs/DATABASE.md`): `expires_at = updated_at + 24h` (refreshed on each NWE appearance)

**6. Design Discussion: New Expiration Logic (In Progress)**

User requirements for new expiration system:
1. **`expires_at` = `nwe_timestamp` + timeframe duration** (not 24h after update)
2. **No refresh** - once set, expiration is fixed
3. **Separate documents per timeframe** - if signal has `["5m", "15m"]`, create 2 hot symbol documents
4. **Delete expired at orchestrator startup**

Expiration durations:
| Timeframe | Expiration |
|-----------|------------|
| 5m | +5 minutes |
| 15m | +15 minutes |
| 1H | +1 hour |
| H4 | +4 hours |
| D1 | +1 day |

**Scope**: Requires Stock Buddy API schema changes (separate documents per timeframe) + orchestrator changes (delete expired at startup)

**Status**: Plan in progress - awaiting final specification before implementation

---

### Session: 2026-02-04 (Signal Freshness Documentation)

**Goal**: Create comprehensive documentation explaining how TTE tiered architecture affects signal delay and dashboard freshness

**File Created**:
- `docs/SIGNAL-FRESHNESS.md` - 597 lines of comprehensive documentation

**Sections Included**:
1. **Executive Summary** - Key metrics (941 symbols, batch sizes, rotation timing)
2. **Scanning Architecture** - Two-tier workflow diagram, batch timing breakdown
3. **Timeframe Staleness Rules** - Bar-close based staleness with examples:
   - 5m signal → stale after next 5m bar closes (max 5 minutes)
   - 15m signal → stale after next 15m bar closes (max 15 minutes)
   - 1H signal → stale after next 1H bar closes (max 60 minutes)
4. **Dashboard Freshness Interpretation** - Python algorithm, UI recommendations
5. **Full Rotation Timing Analysis** - Best/average/worst case scenarios
6. **Priority Rotation System** - A/B/C scan frequencies
7. **Current System Limitations** - Known gaps and future improvements
8. **API Reference** - Useful curl commands for freshness queries
9. **Quick Reference Card** - Condensed cheat sheet

**Key Findings Documented**:
- Full rotation: ~55 min (best) to ~6+ hours (worst)
- Priority A (28 symbols): Scanned every batch
- Priority B (150 symbols): Every 3rd rotation
- Priority C (763 symbols): Every 10th rotation

**Completes Task 7**: Analyze architecture impact on signal delay

---

### Session: 2026-02-04 (Screener Timeframe Updates)

**Goal**: Update screener timeframes from misleading H4/D1/W1 labels to actual 5m/15m/1H values

**Changes Made**:

1. **NWE Screener v2** (`screeners on TV/TTE NWE Screener v2.txt`):
   - Renamed `TF_H4` → `TF_5M`, `TF_D1` → `TF_15M`
   - Updated all variable suffixes: `_h4` → `_5m`, `_d1` → `_15m`
   - Updated comments to reference correct timeframes
   - JSON payload already used correct strings ("5m", "15m")

2. **OBDIV Screener v2** (`screeners on TV/TTE OBDIV Screener v2.txt`):
   - Renamed `TF_H4` → `TF_5M`, `TF_D1` → `TF_15M`, `TF_W1` → `TF_1H`
   - Updated all variable suffixes: `_h4` → `_5m`, `_d1` → `_15m`, `_w1` → `_1h`
   - Updated JSON payload strings: "W1" → "1H", "D1" → "15m", "H4" → "5m"
   - Updated comments to reference correct timeframes

3. **Documentation Updates** (all webhook format corrections):
   - `docs/API.md` - Corrected NWE to batch format, updated all timeframe references
   - `docs/PRD.md` - Updated all webhook payload examples and timeframe references
   - `.claude/task-context.md` - Updated webhook format in Verified Patterns
   - Stock Buddy `TTE-Integration.md` - Updated webhook formats and added clarity

**Key Format Corrections**:
- NWE webhook sends **batch** format (symbols array), not individual symbols
- OBDIV webhook sends **individual** format (one alert per symbol)
- Timeframes: 5m, 15m for NWE; 5m, 15m, 1H for OBDIV OB; 5m, 15m for OBDIV Divergence

---

### Session: 2026-02-04 (Documentation Correction)

**Goal**: Correct Stock Buddy API documentation in TTE to match actual implementation

**Problem Identified**:
After exploring the Stock Buddy App codebase, found significant discrepancies between TTE documentation and actual Stock Buddy API implementation:
1. Wrong/missing endpoints
2. Incorrect webhook payload formats
3. Missing signal levels documentation
4. Missing database collection schemas

**Files Modified (TTE Repo)**:
- `docs/API.md` - Complete rewrite with correct endpoints and schemas
- `docs/DATABASE.md` - Added Stock Buddy database collections section

**Files Created (Stock Buddy Repo)**:
- `src/lib/knowledge-base/TTE-Integration.md` - New comprehensive TTE integration doc
- Updated `src/lib/knowledge-base/README.md` to reference new file

**Key Corrections Made**:
1. **Webhook Payloads**:
   - NWE: `{ tier: "nwe", symbol, direction, timeframes, timestamp }` (not `{ screener, symbols[] }`)
   - OBDIV: `{ tier: "obdiv", symbol, bull_ob, bull_div, bear_ob, bear_div }` with nested schemas
2. **New Endpoints Documented**:
   - `GET/POST /api/tte/init` - Initialization
   - `GET /api/tte/signals` - Query signals with filtering
   - `PATCH /api/tte/signals/[id]` - Update signal
   - `POST /api/tte/symbols/import` - Bulk import
3. **Stats Response Format**: Corrected to use nested structure (signals, hot_list, rotation, symbols)
4. **Signal Levels**: Documented Level 1/2/3 system with criteria
5. **Priority Rotation**: Documented A/B/C priority system
6. **Stock Buddy Collections**: `tte_symbols`, `tte_hot_list`, `tte_signals`, `tte_rotation_state`

**Commits**:
- TTE: `bcc247d` - Correct Stock Buddy API documentation with actual endpoint schemas
- Stock Buddy: `91d220b` - Add TTE integration documentation to knowledge base

---

### Session: 2026-02-03 (Webhook Fix - COMPLETED)

**Goal**: Fix NWE and OBDIV screeners to fire alerts instantly instead of waiting for bar close

**Problem Identified**:
1. `var bool alreadyFired = false` was being set on historical bars
2. `barstate.isconfirmed` waits for bar close, not instant

**Solution Applied**:
1. Changed `barstate.isconfirmed` to `barstate.isrealtime` - Only fires on realtime bars
2. Changed `alert.freq_once_per_bar_close` to `alert.freq_once_per_bar` - Fires on first tick

**Files Modified**:
- `screeners on TV/TTE NWE Screener v2.txt` - Line 236 and 404
- `screeners on TV/TTE OBDIV Screener v2.txt` - Same changes (done in parallel chat)

**Testing Result**: User confirmed alerts fire almost instantly after creation

**Commit**: `09ec618` - Fix screener webhooks to fire instantly on first realtime tick

---

### Session: 2026-02-03 (Single-Cycle Test - Phase 1 Working)

**Goal**: Fix tiered orchestrator for single-cycle testing

**Issues Fixed**:

1. **`change_settings()` importing from `main.py`**:
   - Problem: Lines 598-604 imported `SCREENER_TIMEFRAME_1/2/3` and `TIMEFRAME_INPUT_MAP` from main.py, causing issues in tiered mode
   - Fix: Wrapped timeframe logic in `if screener_shorttitle is None:` to skip for tiered mode

2. **No robust layout switching**:
   - Problem: Orchestrator didn't retry on layout switch failure or verify success
   - Fix: Added `_switch_to_layout_with_setup()` helper method with retry logic, timeframe change (5 minutes), and layout save on first switch

3. **Webhook alert creation flow**:
   - Problem: `create_webhook_alert()` had incorrect steps for TradingView UI
   - Fix: Simplified to follow correct workflow:
     1. Click Notifications tab (`button[id="alert-dialog-tabs__notifications"]`)
     2. Wait for webhook checkbox (`input[data-qa-id="webhook"]`)
     3. Ensure checkbox is checked
     4. Clear and fill webhook URL (Ctrl+A, Backspace, type) (`input#webhook-url`)
     5. Click Create (`button[data-qa-id="submit"]`)

4. **Indicator not selected before alert creation**:
   - Problem: Alert dialog didn't have correct indicator pre-selected
   - Fix: Added indicator click before `create_webhook_alert()` in both phases

**Single-Cycle Test Results**:
- Browser opens and logs in
- NWE chart loads
- Alerts sidebar opens
- Layout switching works (timeframe already set)
- 20 symbols input to NWE screener successfully
- Webhook alert created successfully for TTE NWE Screener
- Waited 60 seconds for webhook
- Alert deleted
- Phase 2 (OBDIV) didn't run - likely no hot symbols returned from API

**Commit**: `488815a` - Add robust layout switching and fix webhook alert creation

---

### Session: 2026-02-03 (Browser Login Fix - RESOLVED)

**Issue Fixed**: "session not created from chrome not reachable" error

**Root Cause**: Chrome background processes were locking the profile even after closing browser windows.

**Solution Applied** (by user):
- Fixed the Chrome session issue
- Browser can now login to TradingView
- Sign in works when needed

**Changes Made**:

1. **Added debug logging** to track execution flow
2. **Added Chrome process killer** in `Browser.__init__()`
3. **Removed problematic Chrome argument**: `--remote-debugging-port=9224`
4. **Configuration updates**:
   - `env.py`: PROFILE = "Profile 4"
   - `.env`: Added TRADINGVIEW_EMAIL and TRADINGVIEW_PASSWORD
   - `open_tv.py`: Fixed Chrome user-data-dir path

---

### Session: 2026-02-03 (initial setup)

**Accomplishments**:
1. Created comprehensive PRD (`docs/PRD.md`) - 1900+ lines
2. Added TradingView screener source files (`screeners on TV/`)
3. Updated `config.py` batch sizes to match screener limits
4. Created implementation tasks in task-master-ai

**Commits**:
- `68b7e7c` - Add comprehensive PRD and update for v2 screeners
- `968993b` - Update tiered orchestrator code and clean up config files
- `3c217d9` - Update environment and Claude Code settings
- `261fc6a` - Fix orchestrator workflow documentation

---

## Important Decisions Made

1. **Batch Sizes**: NWE screener handles 20 symbols max, OBDIV handles 8 symbols max

2. **Workflow Design**: Single cycle processes one 20-symbol batch completely through both tiers

3. **Chrome Profile**: Use "Profile 4" at `C:\Users\dassa\AppData\Local\Google\Chrome\User Data`

4. **Instant Alert Firing**: Use `barstate.isrealtime` + `alert.freq_once_per_bar` for immediate webhook triggers

5. **Chrome Process Management**: Kill existing Chrome processes before starting Selenium to avoid profile lock issues

6. **Signal Levels**: Level 1 (NWE only), Level 2 (NWE + OB or DIV), Level 3 (NWE + OB + DIV)

7. **Hot Symbol Expiration**: `expires_at = nwe_timestamp + timeframe_duration` (no refresh, separate docs per timeframe)

8. **Architecture Choice (2026-02-06)**: Combo screener (Arch 1) over separate screeners (Arch 2) — fewer alert cycles, simpler orchestrator, no signal merging

9. **Webhook Destination (2026-02-06)**: Stock Buddy API — existing pipeline, signal change detection limits traffic to manageable levels, Vercel Pro + MongoDB M2 recommended ($29/mo)

10. **4 Symbol Hard Limit (2026-02-06)**: More than 4 symbols causes memory/runtime errors in the combo screener. This eliminates Arch 2's batch size advantage

11. **Updated Screener Design (2026-02-06)**: Screener sends ALL raw signals (no levels, no change detection) on every bar. Stock Buddy calculates levels server-side. Uses `alert.freq_once_per_bar` for immediate firing. Deduplication must happen in Stock Buddy API endpoint

---

## Key Reference Files

| File | Purpose |
|------|---------|
| `docs/PRD.md` | Complete technical specification (1900+ lines) |
| `docs/API.md` | **Updated** - Stock Buddy API reference with correct schemas |
| `docs/DATABASE.md` | **Updated** - TTE and Stock Buddy database documentation |
| `docs/SIGNAL-FRESHNESS.md` | **New** - Signal timing, freshness, and staleness documentation |
| `orchestrator.py` | TieredOrchestrator class with two-phase workflow |
| `open_tv.py` | Browser class with all Selenium automation methods |
| `api_client.py` | Stock Buddy API client |
| `config.py` | Configuration with validation |
| `tiered_main.py` | CLI entry point |
| `env.py` | Environment configuration (PROFILE = "Profile 4") |
| `screeners on TV/TTE Screener.txt` | **Consolidated** Pine Script screener (NWE + OB + DIV) |
| `screeners on TV/TTE NWE Screener v2.txt` | (Deprecated) Tier 1 NWE screening |
| `screeners on TV/TTE OBDIV Screener v2.txt` | (Deprecated) Tier 2 OBDIV screening |

---

## Test Commands

```bash
# Validate configuration
python tiered_main.py --validate

# Test API connection
python tiered_main.py --test-api

# Test browser automation
python tiered_main.py --test-browser

# Run single cycle (MAIN TEST)
python tiered_main.py --single-cycle

# Run continuously
python tiered_main.py
```

---

## Next Steps

1. **Build new orchestrator for Arch 1**: Implement the combo screener rotation (264 batches of 4 symbols, create alert per batch, webhook to Stock Buddy)
2. **Create `/api/tte/signal` endpoint on Stock Buddy**: Unified webhook receiver for combo screener JSON format (replaces two-phase NWE+OBDIV endpoints)
3. **Implement alert restart logic**: TTE periodically checks for stopped alerts and restarts them via TradingView UI
4. **Verify Screener Accuracy** (Task 8): Test TTE Screener signal table correctness
5. **Test Stock Buddy Grid** (Task 6): Verify signals appear correctly on the grid UI
6. **Screenshot Integration** (Task 9): Send signal screenshots to Stock Buddy

---

## Bugs Fixed

### Active Bugs (Not Fixed Yet)

None currently.

### Fixed Bugs

16. **Bug #16 - OB/FVG gap condition missing second check** (2026-02-09 - FIXED):
   - Symptom: Screener's OB gap condition was a subset of standalone indicator's (missing redundant second condition)
   - Root cause: Screener only checked `low[i] > high[i-2]` while standalone checks `low[idx] > high[0] AND low[idx] > low[0]`
   - Analysis: Second condition is mathematically redundant (`a > b` and `b >= c` implies `a > c`), but added for exact parity
   - Fix: Added `and low[i] > low[i-2]` (bearish) and `and high[i] < high[i-2]` (bullish) to gap conditions
   - File: `Pine Script Code/TTE Screener.txt` lines 404-405, 512-513
   - Commit: `fd9102d`

15. **Bug #15 - Extra threshold in divergence detection** (2026-02-09 - FIXED):
   - Symptom: TTE Screener divergence detection could miss weak divergences near AO zero
   - Root cause: Extra `-0.0001`/`0.0001` threshold checks not present in original indicator
   - Fix: Removed thresholds — `if prevDownlegAO < currDownlegAO` (bullish) and `if prevUplegAO > currUplegAO` (bearish)
   - File: `Pine Script Code/TTE Screener.txt` lines 293, 320
   - Impact: Negligible in practice (threshold was very small), but ensures exact match with original

14. **Bug #12 - No DIV signals displayed in debug table** (2026-02-09 - VERIFIED NOT A BUG):
   - Initial symptom: DIV column showed no signals during early testing
   - Investigation: Added comprehensive debug logs to divergence detection
   - Result: Divergence detection working correctly - signals appear when market conditions are met
   - User confirmed: "divergence is being detected correctly across the 1h/4h timeframes and all 4 symbols"
   - Resolution: No actual bug - divergences are simply rare market conditions that don't always occur

11. **NWE signals only display for chart's current symbol** (2026-02-09 - FIXED):
   - Symptom: NWE signals only appeared for the symbol matching the current chart
   - Example: Chart on GBPAUD → only GBPAUD row showed NWE signals, other symbols blank
   - Root cause: Chart-timeframe detection used builtin `low`/`high` (always chart symbol)
   - Fix: Moved detection inside `checkSignalWithOB()` so `low`/`high` refer to each symbol in request.security() context
   - Files: `Pine Script Code/TTE Screener.txt` lines 649-734
   - Result: All 4 symbols now show independent NWE signals ✅

**NEW** 13. **Timezone inconsistency in tooltips** (2026-02-09 - FIXED):
   - Symptom: Tooltips displayed timestamps in exchange timezone (varied by symbol/exchange)
   - Impact: Different symbols could show different timezones, causing confusion
   - Fix: Changed `syminfo.timezone` → `"UTC"` in all tooltip functions, added " UTC" suffix
   - Files: `Pine Script Code/TTE Screener.txt` lines 883-935 (buildNweTooltip, buildObTooltip, buildDivTooltip)
   - Result: All tooltips now display uniform UTC timestamps ✅

1. **NWE signal timestamps showing HTF bar time instead of current bar time** (2026-02-07 - FIXED):
   - Cause: NWE signal detection occurred inside `request.security()` in HTF context
   - Symptom: On BTCUSD 1H chart at 19:30, bearish NWE signal showed 14:00 timestamp (5 hours old)
   - Fix: Moved signal detection to chart timeframe (shift 0) using HTF band levels
   - Files: `Pine Script Code/TTE Screener.txt` lines 649-790
   - Pattern: Fetch HTF band levels via `request.security()`, detect signals on chart TF with current bar's low/high

2. **NWE signals disappearing while price still in zone** (2026-02-07):
   - Cause: Signal detection in HTF context caused zone names to become empty when HTF bar data changed
   - Symptom: Signal displayed in debug table, then suddenly vanished even though price still in bearish zone
   - Fix: Chart-timeframe detection ensures signals persist as long as price remains in zone
   - Files: `Pine Script Code/TTE Screener.txt` lines 649-790
   - Same fix as Bug #1 above

3. **Missing NWE tooltips in debug table** (2026-02-07):
   - Cause: `buildNweTooltip()` returned empty strings when no signal or zone was empty
   - Symptom: ETHUSD NWE-1H and BTCUSD NWE-H4 cells showed no tooltip on hover
   - Fix: Always return non-empty tooltip (signal details, "Zone: Unknown", or "No Signal")
   - File: `Pine Script Code/TTE Screener.txt` lines 866-887

4. **"session not created from chrome not reachable"**:
   - Cause: Chrome background processes locking profile
   - Fix: Added `taskkill` before starting Chrome, removed `--remote-debugging-port`

5. **Webhook not firing instantly**:
   - Cause: `barstate.isconfirmed` waits for bar close, `alreadyFired` set on historical bars
   - Fix: Changed to `barstate.isrealtime` and `alert.freq_once_per_bar`

6. **`change_settings()` importing from main.py in tiered mode**:
   - Cause: Timeframe logic always ran, importing constants from main.py
   - Fix: Wrapped in `if screener_shorttitle is None:` to skip for tiered mode

7. **Condition dropdown selector timeout** (2026-02-04):
   - Cause: TradingView UI changed, old `data-qa-id` selector no longer matched
   - Fix: Added alternative selector `span[data-qa-id="ui-kit-disclosure-control main-series-select"]`
   - File: `open_tv.py` lines 1175-1198

8. **`open_log_tab()` timeout on empty log** (2026-02-04):
   - Cause: Waited for `div[data-name="alert-log-item"]` which doesn't exist when log is empty
   - Fix: Changed to wait for `aria-selected="true"` on Log tab button
   - File: `resources/utils.py` lines 135-144

9. **`_close_alert_dialog()` silent failure** (2026-02-04):
   - Cause: Caught all exceptions with `except: pass`, no logging
   - Fix: Added Cancel button as primary method, proper error logging
   - File: `open_tv.py` lines 1130-1159

10. **Wrong error-hint CSS selector** (2026-02-04):
   - Cause: Used `div[data-name="error-hint"]` but TradingView HTML uses `div[data-qa-id="error-hint"]`
   - Fix: Changed to correct `data-qa-id` selector
   - File: `open_tv.py` lines 972, 1116

---

## Verified Patterns

### Pine Script Instant Alert Pattern (Working)
```pinescript
var bool alreadyFired = false

if barstate.isrealtime and not alreadyFired
    // Build payload...
    alert(payload, alert.freq_once_per_bar)
    alreadyFired := true
```

### TradingView Webhook Alert Creation (Working)
```
1. Click indicator on chart to select it
2. Click + button to open alert dialog
3. Click Notifications tab: button[id="alert-dialog-tabs__notifications"]
4. Wait for webhook checkbox: input[data-qa-id="webhook"]
5. Ensure checkbox is checked (click parent label if not)
6. Fill webhook URL: input#webhook-url (Ctrl+A, Backspace, type URL)
7. Click Create: button[data-qa-id="submit"]
```

### Layout Switching with Setup (Working)
```python
def _switch_to_layout_with_setup(layout_name, is_first_switch):
    # Try layout switch with retry
    # On first switch: set timeframe to "5 minutes", save layout
    # Track initialization with _nwe_layout_initialized, _obdiv_layout_initialized
```

### Stock Buddy Webhook Payload Formats (Correct)
```json
// NWE (Tier 1) - BATCH format with symbols array
{
  "tier": "nwe",
  "symbols": [
    {"symbol": "GBPAUD", "direction": "bullish", "timeframes": ["5m", "15m"]},
    {"symbol": "EURUSD", "direction": "bearish", "timeframes": ["5m"]}
  ],
  "timestamp": 1705312800,
  "count": 2
}

// OBDIV (Tier 2) - Individual symbol format
{ "tier": "obdiv", "symbol": "EURUSD", "bull_ob": { "found": true, "tf": "1H", "type": "OB" }, "bull_div": { "found": true, "tf": "5m", "type": "Logic2" }, ... }
```

### Condition Dropdown Selectors (Working - 2026-02-04)
```python
# Try both selectors - TradingView UI may vary
selectors = [
    'span[data-qa-id="ui-lib-Input main-series-select"]',  # Old
    'span[data-qa-id="ui-kit-disclosure-control main-series-select"]',  # New (current)
]
```

### Alert Dialog Close Buttons (Working - 2026-02-04)
```python
# Cancel button (primary)
'button[name="cancel"][data-qa-id="cancel"]'
# Close (X) button (fallback)
'button[data-name="close"]'
```

### Alert Dialog Error Detection (Working - 2026-02-04)
```python
# Error hint selector (note: data-qa-id, NOT data-name)
'div[data-qa-id="alerts-create-edit-dialog"] div[data-qa-id="error-hint"]'

# Data subscription error detection
error_text = error_element.text.lower()
if "data subscription" in error_text:
    # Symbol not available in user's TradingView plan
    return (False, "data_subscription")
```

### Hot Symbol Expiration API Tests (Working - 2026-02-04)
```bash
# Test NWE webhook (batch format)
curl -X POST "https://stock-buddy-app.vercel.app/api/tte/nwe" \
  -H "Content-Type: application/json" \
  -d '{"tier":"nwe","symbols":[{"symbol":"GBPUSD","direction":"bullish","timeframes":["5m","15m","1H"]}],"timestamp":'$(date +%s)',"count":1}'

# Check hot symbols (excludes expired by default)
curl "https://stock-buddy-app.vercel.app/api/tte/hot-symbols?limit=10"

# Check hot symbols (includes expired)
curl "https://stock-buddy-app.vercel.app/api/tte/hot-symbols?limit=10&include_expired=true"

# Delete expired hot symbols
curl -X DELETE "https://stock-buddy-app.vercel.app/api/tte/hot-symbols/expired"
```

### New HotListDocument Schema (2026-02-04)
```typescript
interface HotListDocument {
  _id?: string;
  symbol: string;
  direction: "bullish" | "bearish";
  nwe_timeframe: string;      // Single string (NOT array)
  nwe_timestamp: number;
  status: "pending_tier2" | "tier2_complete" | "expired";
  created_at: Date;
  expires_at: Date;           // NO updated_at field
}
```

### TTE Screener Signal Levels (2026-02-05, updated 2026-02-06)
```
Levels are NO LONGER calculated in Pine Script (as of updated screener).
Stock Buddy must calculate levels from raw signals:
- Level 1: NWE zone only
- Level 2: NWE + (OB/FVG OR Divergence)
- Level 3: NWE + OB/FVG + Divergence

Old Pine Script logic (removed): buyLvl = nweBull ? (obBull ? (divBull ? 3 : 2) : 1) : 0
```

### TTE Screener Updated Alert Pattern (2026-02-06)
```pinescript
// Fires on EVERY bar when any signal exists (no change detection)
if str.length(allSignals) > 0
    string payload = '{"timestamp":' + str.tostring(time) + ',"signals":[' + allSignals + ']}'
    alert(payload, alert.freq_once_per_bar)
```

### TTE Screener Updated JSON Payload (2026-02-06)
```json
{
  "timestamp": 1707264000000,
  "signals": [
    {
      "symbol": "GBPAUD",
      "nwe": [
        {"zone": "lower_avg", "type": "bullish", "overlapTimestamp": 1707264000000, "timeframe": "H4"}
      ],
      "ob_fvg": [
        {"zonetype": "OB", "subtype": "unmitigated", "type": "bullish", "zoneTimestamp": 1707260400000, "overlapTimestamp": 1707264000000, "timeframe": "H4"}
      ],
      "divergence": [
        {"divType": "Logic 2", "type": "bullish", "timestamp": 1707264000000, "timeframe": "H4"}
      ]
    }
  ]
}
```
Note: Symbols with NO signals are excluded from payload entirely.

### TTE Screener Configuration (Updated 2026-02-09)
```
Symbols: 4 active (GBPAUD, AUDJPY, EURCAD, EURGBP) - configurable up to 20
Timeframes:
  - 1H (TF_1H = '60') - NWE, OB/FVG, Divergence
  - H4 (TF_H4 = '240') - NWE, OB/FVG, Divergence
  - D1 (TF_D1 = 'D') - OB/FVG only
Signal Table: Commented out for production (lines 1095-1254)
request.security() calls: 12 total (8 for 1H+H4 combined, 4 for D1 OB-only)
Variable names: Now match actual timeframes (legacy naming removed)
Status: Production-ready, validated, uploaded to Google Drive
```

### Chart-Timeframe NWE Signal Detection Pattern (Fixed - 2026-02-07)
```pinescript
// Step 1: Fetch HTF band levels only (not signals) via request.security()
[lnNear_h4, lnAvg_h4, unNear_h4, unAvg_h4, ...] = request.security(symbol, "240", checkSignalWithOB("240"))

// Step 2: Calculate lower_far and upper_far from band levels
// lower_far = lowerAvg - (lowerNear - lowerAvg) [double the distance from avg]
// upper_far = upperAvg + (upperAvg - upperNear)

// Step 3: Detect signals on chart timeframe (shift 0) using current bar's low/high
bool nweBull_h4 = low <= lnNear_h4 and high >= lnAvg_h4 or low <= lnAvg_h4 and high >= (lnAvg_h4 - (lnNear_h4 - lnAvg_h4))
bool nweBear_h4 = high >= unNear_h4 and low <= unAvg_h4 or high >= unAvg_h4 and low <= (unAvg_h4 + (unAvg_h4 - unNear_h4))

// Step 4: Calculate zone names using chart's price data
string bullZone_h4 = getNweZoneName(true, low, high, lnNear_h4, lnAvg_h4, lnAvg_h4 - (lnNear_h4 - lnAvg_h4), unNear_h4, unAvg_h4, unAvg_h4 + (unAvg_h4 - unNear_h4))
string bearZone_h4 = getNweZoneName(false, low, high, lnNear_h4, lnAvg_h4, lnAvg_h4 - (lnNear_h4 - lnAvg_h4), unNear_h4, unAvg_h4, unAvg_h4 + (unAvg_h4 - unNear_h4))

// Step 5: Use current bar's timestamp for display/alerts
string tooltip = 'Time: ' + str.format_time(time, 'yyyy-MM-dd HH:mm', syminfo.timezone)
```
**Benefits**:
- Timestamps always reflect current bar (shift 0), not HTF bar
- Signals persist correctly while price remains in zone
- No more "disappearing signals" bug
- Fixes both incorrect timestamps and signal persistence issues

**File**: `Pine Script Code/TTE Screener.txt` lines 649-790

### NWE Tooltip Pattern (Fixed - 2026-02-07)
```pinescript
// Always returns non-empty tooltip for TradingView to display
buildNweTooltip(bool bullish, bool bearish, string bullZone, string bearZone, int timestamp) =>
    string tooltip = ''

    // Build bullish section
    if bullish
        string zone = str.length(bullZone) > 0 ? bullZone : 'Unknown'
        tooltip := 'BULLISH\nZone: ' + zone + '\nTime: ' + str.format_time(timestamp, ...)

    // Build bearish section
    if bearish
        string zone = str.length(bearZone) > 0 ? bearZone : 'Unknown'
        string bearInfo = 'BEARISH\nZone: ' + zone + '\nTime: ' + str.format_time(timestamp, ...)
        tooltip := tooltip + (str.length(tooltip) > 0 ? '\n\n' : '') + bearInfo

    // If no signal at all, show "No Signal"
    if not bullish and not bearish
        tooltip := 'No Signal'

    tooltip  // Never returns empty string
```
Key principles:
- Always return non-empty strings (TradingView hides empty tooltips)
- Show "Unknown" for missing zone data instead of omitting
- Show "No Signal" when no signals exist
- Defensive programming prevents silent failures
