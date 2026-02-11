> ⚠️ **LEGACY**: This document describes the **Tiered mode** integration flow. Production uses **Combo mode** — see [Combo Architecture](../../../../docs/combo/ARCHITECTURE.md) and [Combo PRD](../../../../docs/combo/PRD.md).
>
> **Combo mode summary**: 352 persistent alerts monitor ~1,054 symbols (3 per alert). Single combo screener (NWE + OB/FVG + Divergence) fires webhooks to `POST /api/tte/combo`. No batch rotation, no hot list, no alert create/delete cycles. Alerts run continuously with 5-minute maintenance checks.

# Integration Flow Reference

Complete reference for the TTE → Stock Buddy integration workflow.

## Table of Contents

- [Overview](#overview)
- [System Components](#system-components)
- [Complete Workflow](#complete-workflow)
- [Phase 1: NWE Batch Processing](#phase-1-nwe-batch-processing)
- [Phase 2: OBDIV Confirmation](#phase-2-obdiv-confirmation)
- [Timing and Delays](#timing-and-delays)
- [Error Handling](#error-handling)
- [Orchestrator State Machine](#orchestrator-state-machine)
- [Webhook Processing](#webhook-processing)

## Overview

The TTE → Stock Buddy integration uses a two-tier workflow to filter 900+ symbols down to high-confidence trading signals:

```
900+ Symbols (Stock Buddy DB)
         ↓
    Tier 1: NWE Screening (batches of 20)
         ↓
   Hot Symbols (5-20 symbols)
         ↓
    Tier 2: OBDIV Confirmation (batches of 8)
         ↓
   Confirmed Signals (levels 1/2/3)
```

**Key Principle**: Minimize browser automation time by using webhooks for data transfer instead of scraping.

## System Components

| Component | Technology | Role |
|-----------|------------|------|
| **TradingView** | Pine Script | Runs screeners, sends webhooks |
| **TTE Orchestrator** | Python (Selenium) | Automates browser, coordinates workflow |
| **Stock Buddy API** | Next.js (API routes) | Receives webhooks, manages data |
| **Stock Buddy Frontend** | React | Displays signals to user |
| **MongoDB** | Database | Stores symbols, hot list, signals |

## Complete Workflow

### High-Level Flow

1. **Startup**
   - TTE orchestrator starts
   - API health check
   - Delete expired hot symbols
   - Load NWE layout in TradingView

2. **Phase 1: NWE Batch** (20 symbols)
   - Fetch next batch from Stock Buddy API
   - Input symbols into NWE screener
   - Create webhook alert (URL: `/api/tte/nwe`)
   - Wait for alert to trigger
   - Delete alert
   - Mark symbols as scanned

3. **Phase 2: OBDIV Processing** (hot symbols)
   - Fetch hot symbols from Stock Buddy API
   - Switch to OBDIV layout
   - Process hot symbols in batches of 8:
     - Input symbols into OBDIV screener
     - Create webhook alert (URL: `/api/tte/obdiv`)
     - Wait for alert to trigger
     - Delete alert
   - Repeat until hot list is empty
   - Switch back to NWE layout

4. **Cycle Complete**
   - Wait for cycle interval (5 minutes)
   - Return to step 2 (next NWE batch)

### Timing Overview

| Operation | Duration | Notes |
|-----------|----------|-------|
| NWE batch processing | 60-90 seconds | Includes input, alert creation, webhook wait |
| OBDIV batch processing | 60-90 seconds | Per batch of 8 symbols |
| Cycle interval | 5 minutes | Wait between complete cycles |
| Hot symbol expiration | 5m - 24h | Based on NWE timeframe |

## Phase 1: NWE Batch Processing

### Detailed Steps

**Step 1: Fetch Batch from API**

```python
# TTE orchestrator (api_client.py)
batch_response = api.get_next_symbol_batch(size=20)
symbols = [s["symbol"] for s in batch_response["batch"]]
```

**API Request**:
```http
GET /api/tte/symbols/next-batch?size=20
```

**API Response**:
```json
{
  "success": true,
  "batch": [
    {"symbol": "EURUSD", "exchange": "FX", "priority": "A"},
    {"symbol": "GBPUSD", "exchange": "FX", "priority": "A"}
  ],
  "count": 20,
  "rotation": {
    "batch_number": 6,
    "rotation_number": 1,
    "total_symbols": 941,
    "symbols_scanned_this_rotation": 120
  }
}
```

**Step 2: Input Symbols into NWE Screener**

```python
# TTE orchestrator
browser.input_symbols_to_screener(symbols, NWE_SCREENER_NAME)
```

**Browser Actions**:
1. Click screener indicator on chart
2. Open settings panel
3. For each of 20 symbol inputs:
   - Clear existing value
   - Enter new symbol
4. Save settings

**Duration**: ~10-15 seconds

**Step 3: Create Webhook Alert**

```python
# TTE orchestrator
browser.create_webhook_alert(
    indicator_name=NWE_SCREENER_NAME,
    webhook_url=self.nwe_webhook_url,
    alert_name=f"NWE Batch {batch_number}"
)
```

**Browser Actions**:
1. Click "Create Alert" button
2. Select NWE screener as condition
3. Set alert name
4. Set webhook URL: `https://stock-buddy-app.vercel.app/api/tte/nwe`
5. Configure alert to trigger "Once Per Bar Close"
6. Save alert

**Duration**: ~5-10 seconds

**Step 4: Wait for Webhook to Fire**

```python
# TTE orchestrator (config.py)
time.sleep(config.nwe_batch_wait)  # Default: 60 seconds
```

**What Happens**:
1. TradingView evaluates NWE screener on each bar close
2. If symbols are in NWE zones, screener sends webhook
3. Webhook payload includes all symbols currently in zones
4. Stock Buddy API receives webhook, creates hot list entries

**Webhook Payload** (sent by TradingView):
```json
{
  "tier": "nwe",
  "symbols": [
    {"symbol": "GBPAUD", "direction": "bullish", "timeframes": ["5m", "15m"]},
    {"symbol": "EURUSD", "direction": "bearish", "timeframes": ["5m"]}
  ],
  "timestamp": 1705312800,
  "count": 2
}
```

**Note**: Webhook may send empty `symbols: []` array if no symbols are in zones (valid).

**Step 5: Delete Alert**

```python
# TTE orchestrator
browser.delete_alert(alert_name=f"NWE Batch {batch_number}")
```

**Browser Actions**:
1. Open alerts panel
2. Find alert by name
3. Click delete button
4. Confirm deletion

**Duration**: ~2-5 seconds

**Step 6: Mark Symbols as Scanned**

```python
# TTE orchestrator
api.mark_symbols_scanned(symbols)
```

**API Request**:
```http
POST /api/tte/symbols/mark-scanned
Content-Type: application/json

{
  "symbols": ["EURUSD", "GBPUSD", "USDJPY"]
}
```

**API Response**:
```json
{
  "success": true,
  "marked_count": 20,
  "rotation_complete": false
}
```

**Database Updates** (Stock Buddy):
1. Update `last_scanned` timestamp for each symbol
2. Increment `scan_count` for each symbol
3. Update rotation state:
   - Increment `batch_number`
   - Increment `symbols_scanned_this_rotation` by 20
   - Check if rotation complete (all symbols scanned)

### Phase 1 Total Duration

**Best Case**: 60 seconds
**Typical**: 75 seconds
**Worst Case**: 90 seconds

## Phase 2: OBDIV Confirmation

### Detailed Steps

**Step 1: Fetch Hot Symbols**

```python
# TTE orchestrator
hot_symbols = api.get_hot_symbols(limit=8)
```

**API Request**:
```http
GET /api/tte/hot-symbols?limit=8&status=pending_tier2
```

**API Response**:
```json
{
  "success": true,
  "symbols": [
    {
      "_id": "65a5b2c1d4e5f6a7b8c9d0e1",
      "symbol": "GBPAUD",
      "direction": "bullish",
      "nwe_timeframe": "5m",
      "nwe_timestamp": 1705312800,
      "status": "pending_tier2",
      "created_at": "2024-01-15T10:30:00Z",
      "expires_at": "2024-01-15T10:35:00Z"
    }
  ],
  "count": 5
}
```

**Step 2: Switch to OBDIV Layout**

```python
# TTE orchestrator
browser.switch_layout(OBDIV_LAYOUT_NAME)
```

**Browser Actions**:
1. Click layouts dropdown
2. Select "OBDIV" layout
3. Wait for layout to load

**Duration**: ~5-10 seconds (first time), ~2-3 seconds (cached)

**Step 3: Process Hot Symbols in Batches of 8**

```python
# TTE orchestrator
for batch in chunks(hot_symbols, 8):
    # Input symbols
    browser.input_symbols_to_screener(batch, OBDIV_SCREENER_NAME)

    # Create webhook alert
    browser.create_webhook_alert(
        indicator_name=OBDIV_SCREENER_NAME,
        webhook_url=self.obdiv_webhook_url,
        alert_name=f"OBDIV Batch {batch_number}"
    )

    # Wait for webhook
    time.sleep(config.obdiv_batch_wait)  # Default: 60 seconds

    # Delete alert
    browser.delete_alert(alert_name=f"OBDIV Batch {batch_number}")
```

**OBDIV Webhook Payload** (sent by TradingView):
```json
{
  "tier": "obdiv",
  "symbol": "EURUSD",
  "bull_ob": {
    "found": true,
    "tf": "1H",
    "type": "OB",
    "high": 1.1050,
    "low": 1.1000
  },
  "bull_div": {
    "found": true,
    "tf": "5m",
    "type": "Logic2"
  },
  "bear_ob": {
    "found": false
  },
  "bear_div": {
    "found": false
  },
  "timestamp": 1705316400
}
```

**Stock Buddy Processing** (OBDIV webhook):
1. Validate webhook payload (Zod schema)
2. Check for bullish signal (if `bull_ob.found` OR `bull_div.found`):
   - Look up hot list entry for symbol + bullish
   - Calculate level: 3 (OB+DIV), 2 (OB OR DIV), 1 (neither)
   - Create signal document in `tte_signals` collection
   - Mark hot list entry as `tier2_complete`
   - Increment symbol's `signal_count`
3. Repeat for bearish signal
4. Return response with signals created

**Step 4: Switch Back to NWE Layout**

```python
# TTE orchestrator
browser.switch_layout(NWE_LAYOUT_NAME)
```

### Phase 2 Total Duration

**Per Batch**: 60-90 seconds
**Total**: 60-90 seconds × (number of batches)

Example: 16 hot symbols = 2 batches = 120-180 seconds

## Timing and Delays

### Configuration

All timing values are configurable in `config.py`:

```python
@dataclass
class Config:
    # Alert wait times
    nwe_batch_wait: int = 60        # Wait after NWE alert creation (seconds)
    obdiv_batch_wait: int = 60      # Wait after OBDIV alert creation (seconds)

    # Cycle timing
    cycle_interval: int = 300       # Wait between complete cycles (5 minutes)

    # API settings
    api_timeout: int = 30           # Request timeout (seconds)
    max_retries: int = 3            # Maximum API retry attempts
    retry_delay: int = 5            # Delay between retries (seconds)
```

### Why These Delays?

**NWE Batch Wait (60s)**:
- TradingView needs time to evaluate screener on bar close
- 5m timeframe → max wait is 5 minutes, but alert typically fires within 60s
- If no symbols in zones, webhook fires immediately with empty array

**OBDIV Batch Wait (60s)**:
- OBDIV screener evaluates OB/DIV logic on each symbol
- More complex calculations than NWE
- Alert typically fires within 30-60 seconds

**Cycle Interval (5 minutes)**:
- Prevents overwhelming TradingView with constant requests
- Allows time for market conditions to change
- Reduces risk of rate limiting

### Adjusting Delays

**For Faster Testing** (not recommended for production):
```python
nwe_batch_wait: int = 30
obdiv_batch_wait: int = 30
cycle_interval: int = 60
```

**For Higher Reliability** (slower but more robust):
```python
nwe_batch_wait: int = 90
obdiv_batch_wait: int = 90
cycle_interval: int = 600  # 10 minutes
```

## Error Handling

### API Connection Errors

```python
# TTE orchestrator
try:
    batch = api.get_next_symbol_batch(20)
except requests.exceptions.ConnectionError:
    logger.error("API connection failed, retrying in 30 seconds")
    time.sleep(30)
    # Retry logic...
```

**Retry Strategy**:
1. Connection error → retry up to 3 times with 5s delay
2. 5xx error → retry with exponential backoff
3. 4xx error → log and skip (client error)

### Webhook Processing Errors

**NWE Webhook**:
- Validation error → return 400 with error message
- Empty `symbols: []` array → valid, return 200 with `created: 0`
- Duplicate symbol+timeframe → skip, increment `skipped` count

**OBDIV Webhook**:
- Validation error → return 400 with error message
- No matching hot list entry → return 200 with `signals_created: []`
- Hot list entry expired → skip silently

### Browser Automation Errors

```python
# TTE orchestrator
try:
    browser.input_symbols_to_screener(symbols, NWE_SCREENER_NAME)
except selenium.common.exceptions.TimeoutException:
    logger.error("Timeout while inputting symbols, refreshing page")
    browser.refresh()
    # Retry...
```

**Common Issues**:
- Element not found → wait and retry
- Timeout → refresh page and retry
- Alert creation failed → delete existing alert and retry

## Orchestrator State Machine

### States

```python
class OrchestratorState:
    STARTING = "starting"           # Initial startup
    NWE_FETCHING = "nwe_fetching"   # Fetching next batch
    NWE_INPUTTING = "nwe_inputting" # Inputting symbols to screener
    NWE_CREATING_ALERT = "nwe_creating_alert"
    NWE_WAITING = "nwe_waiting"     # Waiting for webhook
    NWE_CLEANUP = "nwe_cleanup"     # Deleting alert, marking scanned
    OBDIV_FETCHING = "obdiv_fetching"
    OBDIV_SWITCHING = "obdiv_switching"  # Switching to OBDIV layout
    OBDIV_PROCESSING = "obdiv_processing"
    OBDIV_CLEANUP = "obdiv_cleanup"
    CYCLE_WAITING = "cycle_waiting"  # Waiting between cycles
    ERROR = "error"
    STOPPED = "stopped"
```

### State Transitions

```
STARTING
  ↓
NWE_FETCHING
  ↓
NWE_INPUTTING
  ↓
NWE_CREATING_ALERT
  ↓
NWE_WAITING (60s)
  ↓
NWE_CLEANUP
  ↓
OBDIV_FETCHING
  ↓ (if hot symbols exist)
OBDIV_SWITCHING
  ↓
OBDIV_PROCESSING (per batch)
  ↓ (repeat for each batch)
OBDIV_CLEANUP
  ↓
CYCLE_WAITING (5 minutes)
  ↓
NWE_FETCHING (loop)
```

### State Logging

```python
# TTE orchestrator (orchestrator.py)
logger.info(f"State: {self.state}")
logger.info(f"Batch #{batch_number} | Rotation #{rotation_number}")
logger.info(f"Symbols scanned this rotation: {scanned}/{total}")
```

## Webhook Processing

### NWE Webhook Processing

**Endpoint**: `POST /api/tte/nwe`

**Processing Steps**:
1. Parse JSON body
2. Validate with Zod schema (`nweBatchWebhookSchema`)
3. Extract symbols array
4. For each symbol:
   - For each timeframe:
     - Check if hot list entry exists (symbol + direction + timeframe)
     - If exists, skip (no refresh)
     - If not exists, create new entry with expiration
5. Return response with `created` and `skipped` counts

**Database Operations**:
```typescript
// For each symbol+timeframe combination
await collection.insertOne({
  symbol,
  direction,
  nwe_timeframe: timeframe,
  nwe_timestamp: timestamp,
  status: "pending_tier2",
  created_at: new Date(),
  expires_at: getExpirationDate(timestamp, timeframe)
});
```

### OBDIV Webhook Processing

**Endpoint**: `POST /api/tte/obdiv`

**Processing Steps**:
1. Parse JSON body
2. Validate with Zod schema (`obdivWebhookSchema`)
3. Check for bullish signal:
   - If `bull_ob.found` OR `bull_div.found`:
     - Look up hot list entry (symbol + bullish)
     - Calculate level (1/2/3)
     - Create signal document
     - Mark hot list entry as `tier2_complete`
     - Increment symbol's `signal_count`
4. Repeat for bearish signal
5. Return response with signals created

**Signal Level Calculation**:
```typescript
function calculateSignalLevel(hasOB: boolean, hasDiv: boolean): 1 | 2 | 3 {
  if (hasOB && hasDiv) return 3;
  if (hasOB || hasDiv) return 2;
  return 1;
}
```

---

**Related**:
- [API Endpoints](api_endpoints.md) - API endpoint details and schemas
- [Database Schema](database_schema.md) - Hot list and signal document structures
- [Symbol Management](symbol_management.md) - Batch selection algorithm
