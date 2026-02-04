# Task Context Tracker

**Last Updated**: 2026-02-04
**Current Task**: Task 5 - E2E Testing (Phase 1 and Phase 2)
**Last Session**: Hot Symbol Expiration System Implementation

---

## Task Progress Summary (Task Master)

| ID | Task | Status | Priority | Dependencies |
|----|------|--------|----------|--------------|
| 1 | Create TTE NWE Screener v2 Pine Script | **done** | high | - |
| 2 | Create TTE OBDIV Screener v2 Pine Script | **done** | high | - |
| 3 | Implement TieredOrchestrator class | **done** | high | 1, 2 |
| 4 | Fix screener webhooks to fire instantly | **done** | high | 1, 2 |
| 5 | Test orchestrator E2E - Phase 1 and Phase 2 | pending | high | 3, 4 |
| 6 | Test signals display on Stock Buddy grid | pending | medium | 5 |
| 7 | Analyze architecture impact on signal delay | **done** | high | - |
| 8 | Verify TradingView screener signal accuracy | pending | high | - |
| 9 | Send signal screenshots to Stock Buddy | pending | medium | - |

**Stats**: 9 tasks, 56% complete (5 done, 4 pending)

### Task 5 Subtasks
- 5.1: Prevent price-crossing alerts instead of screener alerts (pending)
- 5.2: Reduce webhook wait time with alert log monitoring (pending)
- 5.3: Handle data subscription error in Create Alert dialog (pending)

### Task 6 Subtasks
- 6.1: Verify Stock Buddy grid displays correct signal info (pending)

---

## Session History

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
| `screeners on TV/TTE NWE Screener v2.txt` | Pine Script for Tier 1 NWE screening |
| `screeners on TV/TTE OBDIV Screener v2.txt` | Pine Script for Tier 2 OBDIV screening |

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

1. **Test E2E** (Task 5): Run `--single-cycle` and verify:
   - Phase 1 webhook fires and sends hot symbols to API
   - Phase 2 receives hot symbols and processes through OBDIV
2. **Fix Task 5 Subtasks**:
   - 5.1: Prevent price-crossing alerts
   - 5.2: Reduce webhook wait time with alert log monitoring
   - 5.3: Handle data subscription error
3. **Test Stock Buddy Grid** (Task 6): Verify signals appear correctly on the grid UI
4. **Verify Screener Accuracy** (Task 8): Verify TradingView screeners produce correct signals
5. **Screenshot Integration** (Task 9): Send signal screenshots to Stock Buddy

---

## Bugs Fixed

1. **"session not created from chrome not reachable"**:
   - Cause: Chrome background processes locking profile
   - Fix: Added `taskkill` before starting Chrome, removed `--remote-debugging-port`

2. **Webhook not firing instantly**:
   - Cause: `barstate.isconfirmed` waits for bar close, `alreadyFired` set on historical bars
   - Fix: Changed to `barstate.isrealtime` and `alert.freq_once_per_bar`

3. **`change_settings()` importing from main.py in tiered mode**:
   - Cause: Timeframe logic always ran, importing constants from main.py
   - Fix: Wrapped in `if screener_shorttitle is None:` to skip for tiered mode

4. **Condition dropdown selector timeout** (2026-02-04):
   - Cause: TradingView UI changed, old `data-qa-id` selector no longer matched
   - Fix: Added alternative selector `span[data-qa-id="ui-kit-disclosure-control main-series-select"]`
   - File: `open_tv.py` lines 1175-1198

5. **`open_log_tab()` timeout on empty log** (2026-02-04):
   - Cause: Waited for `div[data-name="alert-log-item"]` which doesn't exist when log is empty
   - Fix: Changed to wait for `aria-selected="true"` on Log tab button
   - File: `resources/utils.py` lines 135-144

6. **`_close_alert_dialog()` silent failure** (2026-02-04):
   - Cause: Caught all exceptions with `except: pass`, no logging
   - Fix: Added Cancel button as primary method, proper error logging
   - File: `open_tv.py` lines 1130-1159

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
