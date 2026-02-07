# Architecture 1: Combo Screener — Complete Design Document

## Table of Contents

1. [Context & Why This Architecture](#1-context--why-this-architecture)
2. [System Overview](#2-system-overview)
3. [Component Details](#3-component-details)
4. [Data Flow — End to End](#4-data-flow--end-to-end)
5. [TTE Combo Screener (Pine Script)](#5-tte-combo-screener-pine-script)
6. [TTE Orchestrator (Python)](#6-tte-orchestrator-python)
7. [TradingView Alert Lifecycle](#7-tradingview-alert-lifecycle)
8. [Webhook & Stock Buddy API Integration](#8-webhook--stock-buddy-api-integration)
9. [Live Signal State Model](#9-live-signal-state-model)
10. [Symbol Rotation](#10-symbol-rotation)
11. [Error Handling & Resilience](#11-error-handling--resilience)
12. [Infrastructure & Costs](#12-infrastructure--costs)
13. [Constraints & Limitations](#13-constraints--limitations)
14. [Open Questions](#14-open-questions)

---

## 1. Context & Why This Architecture

### Problem
TTE needs to monitor ~1,054 trading symbols across multiple timeframes for NWE, Order Block/FVG, and Divergence signals, then display those signals in real-time on the Stock Buddy dashboard.

### Why Combo Screener (Architecture 1) Over Separate Screeners (Architecture 2)

Two architectures were evaluated:

- **Architecture 1 (Combo)**: Single Pine Script indicator combining NWE + OB/FVG + Divergence. 4 symbols per batch, 1 alert per batch.
- **Architecture 2 (Separate)**: 3 separate Pine Script indicators (NWE, OB, Divergence). 4 symbols per batch, 3 alerts per batch.

Architecture 1 was chosen because:

| Factor | Arch 1 (Combo) | Arch 2 (Separate) |
|--------|---------------|-------------------|
| Alert cycles for 1,054 symbols | **264** | **792** (3x more) |
| Browser automation interactions | 264 create + 264 delete | 792 create + 792 delete |
| Full rotation time | **~6.6 hours** | **~19.8 hours** |
| Signal merging needed | No — single payload has all data | Yes — 3 payloads must be correlated per batch |
| Pine Script already built | Yes | No — would need 3 new scripts |
| Selenium failure surface | Lower | 3x higher |

The 4-symbol hard limit (more causes memory/runtime errors in TradingView) eliminates Architecture 2's main advantage (larger batch sizes per screener).

---

## 2. System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    ONE-TIME SETUP PHASE                         │
│                                                                 │
│  TTE Orchestrator (Python + Selenium)                          │
│  ├── Fetches ~1,054 symbols                                    │
│  ├── Takes batch of 4 symbols                                  │
│  ├── Opens TradingView, inputs symbols into combo screener     │
│  ├── Creates webhook alert → points to Stock Buddy API         │
│  ├── Repeats for all 264 batches                               │
│  └── Result: 264 alerts live on TradingView                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CONTINUOUS OPERATION                          │
│                                                                 │
│  TradingView (Server-Side)                                     │
│  ├── 264 alerts running continuously                           │
│  ├── Each alert monitors 4 symbols via combo screener          │
│  ├── On every tick: evaluates all signals                      │
│  ├── Fires webhook with JSON payload when signals exist        │
│  └── Alerts persist even when browser is closed                │
│           │                                                     │
│           ▼                                                     │
│  Stock Buddy API (Vercel / Next.js)                            │
│  ├── POST /api/tte/signal — receives webhook                   │
│  ├── Validates payload (Zod)                                   │
│  ├── Upserts signal state into MongoDB                         │
│  └── Frontend polls for latest state                           │
│           │                                                     │
│           ▼                                                     │
│  Stock Buddy Frontend (React)                                  │
│  ├── RTK Query polls signals endpoint                          │
│  ├── Displays live signal grid                                 │
│  └── Shows current signal state for all symbols                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MAINTENANCE (Periodic)                        │
│                                                                 │
│  TTE Orchestrator                                              │
│  ├── Periodically checks TradingView for stopped alerts        │
│  ├── Restarts any alerts that stopped due to runtime errors    │
│  └── Runs on a schedule (e.g., every 30-60 minutes)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Details

### 3.1 TTE Combo Screener (Pine Script)

- **File**: `Pine Script Code/TTE Screener.txt`
- **Version**: Pine Script v6
- **Indicator name**: "TTE Screener" (short title: "Screener")
- **Symbols**: 4 per instance (hard limit — more causes memory/runtime errors)
- **Timeframes scanned**: H4, D1 (NWE + OB + Divergence), W1 (OB only)
- **`request.security()` calls**: 12 of 40 max (4×H4 + 4×D1 + 4×W1)
- **Signal types detected**:
  - **NWE (Nadaraya-Watson Envelope)**: Price in lower/upper envelope zones on H4/D1
  - **OB/FVG (Order Block / Fair Value Gap)**: Unmitigated OBs, breaker zones, unfilled FVGs on H4/D1/W1
  - **Divergence (Kernel AO)**: Logic 2 divergence on H4/D1
- **Alert behavior**: Fires on every tick (`alert.freq_all`) when at least 1 signal exists across any of its 4 symbols
- **No signal hierarchy**: All raw signals are sent; Stock Buddy calculates levels
- **Continuous webhook delivery**: Fires on every evaluation when signals are present, providing real-time updates
- **Payload**: Rich nested JSON with all signal details (see Section 8)

### 3.2 TTE Orchestrator (Python)

- **File**: `orchestrator.py`, `tiered_main.py`
- **Purpose**: One-time setup of all 264 alerts, plus periodic maintenance
- **Technology**: Python + Selenium (Chrome browser automation)
- **Responsibilities**:
  1. Fetch symbol list (~1,054 symbols)
  2. Batch into groups of 4
  3. For each batch: open TradingView → input symbols → create webhook alert
  4. Periodically check for stopped alerts and restart them

### 3.3 TradingView Platform

- **Subscription**: Premium (required for webhooks)
- **264 alerts**: All running simultaneously as server-side alerts
- **Each alert**: Monitors 4 symbols via the combo screener indicator
- **Server-side execution**: Alerts continue running after browser is closed
- **Alert snapshots**: When an alert is created, TradingView captures a snapshot of the indicator. Editing the script does NOT update existing alerts — they must be deleted and recreated.

### 3.4 Stock Buddy API (Next.js / Vercel)

- **Repository**: `C:\Users\dassa\Work\Stock-Buddy-App`
- **New endpoint needed**: `POST /api/tte/signal`
- **Responsibilities**:
  - Receive webhook payload from TradingView
  - Validate with Zod schema
  - Upsert signal state into MongoDB (replace, not accumulate)
  - Serve signal state to frontend via existing query endpoints

### 3.5 MongoDB Atlas

- **Collections**:
  - `tte_live_signals` (NEW): Current signal state per symbol — upserted on every webhook
  - `tte_symbols`: Symbol list with priority and rotation metadata
  - `tte_rotation_state`: Tracks orchestrator progress through symbol batches
- **Tier**: M2 recommended ($9/mo) — 2GB storage, better connection pool

### 3.6 Stock Buddy Frontend (React)

- **Technology**: Next.js 14, React 18, RTK Query, Tailwind CSS
- **Signal display**: Grid showing all symbols with their current signal state
- **Polling**: RTK Query polls the signals endpoint at regular intervals
- **Staleness detection**: If `last_updated` for a symbol is too old, show as "stale"

---

## 4. Data Flow — End to End

### Phase 1: Alert Setup (One-Time)

```
Step 1: TTE Orchestrator starts
Step 2: Fetches symbol list from Stock Buddy API or local config
        → Returns ~1,054 symbols
Step 3: Divides into 264 batches of 4 symbols each
Step 4: For batch #1 (e.g., GBPAUD, AUDJPY, EURCAD, EURGBP):
        a. Opens TradingView in Chrome via Selenium
        b. Loads the "Screener" layout (has TTE Screener indicator)
        c. Opens indicator settings panel
        d. Inputs 4 symbols into s01-s04 fields
        e. Clicks the indicator on chart to select it
        f. Opens alert dialog
        g. Selects "Any alert() function call" as condition
        h. Goes to Notifications tab
        i. Enables webhook checkbox
        j. Enters webhook URL: https://stock-buddy-app.vercel.app/api/tte/signal
        k. Clicks Create
Step 5: Repeats Step 4 for all 264 batches
Step 6: All 264 alerts are now live on TradingView's servers
```

### Phase 2: Continuous Signal Flow

```
Step 1: TradingView server evaluates alert #47 (symbols: GBPAUD, AUDJPY, EURCAD, EURGBP)
Step 2: Combo screener runs on current tick
        → GBPAUD has bullish NWE on 1H + bullish OB on H4
        → AUDJPY has no signals
        → EURCAD has bearish NWE on H4
        → EURGBP has no signals
Step 3: Screener builds JSON payload:
        - GBPAUD included with NWE + OB data
        - AUDJPY excluded (no signals)
        - EURCAD included with NWE data
        - EURGBP excluded (no signals)
Step 4: alert() fires → TradingView sends POST to Stock Buddy webhook URL
Step 5: Stock Buddy receives payload
        a. Zod validates the JSON structure
        b. For GBPAUD: upserts signal state (NWE + OB active, last_updated = now)
        c. For EURCAD: upserts signal state (NWE active, last_updated = now)
        d. AUDJPY/EURGBP: not in payload, their existing state (if any) is untouched
        e. Returns 200 OK
Step 6: Frontend polls signals endpoint
        → Shows GBPAUD with NWE + OB signals (last updated: just now)
        → Shows EURCAD with NWE signal (last updated: just now)
        → AUDJPY/EURGBP: if they had old signals, those persist with old last_updated
        → User sees timestamps and judges freshness
```

### Phase 3: Maintenance (Periodic)

```
Step 1: TTE Orchestrator runs maintenance check (every 30-60 minutes)
Step 2: Opens TradingView alerts panel via Selenium
Step 3: Scans for stopped/errored alerts
Step 4: For each stopped alert:
        a. Identifies which 4 symbols it covered
        b. Deletes the stopped alert
        c. Recreates it with the same symbols and webhook URL
Step 5: Alert is now running again on TradingView's servers
```

---

## 5. TTE Combo Screener (Pine Script)

### Signal Detection Logic

**A. NWE (Nadaraya-Watson Envelope)**

- Uses kernel regression to create support/resistance envelope bands
- Bullish signal: Price overlaps lower envelope zones (lower_avg or lower_far)
- Bearish signal: Price overlaps upper envelope zones (upper_avg or upper_far)
- Checked on: H4 and D1 timeframes

**B. OB/FVG (Order Block / Fair Value Gap)**

- Detects institutional supply/demand zones
- Bullish signals: Unmitigated bullish OB, breaker support, unfilled bullish FVG
- Bearish signals: Unmitigated bearish OB, breaker resistance, unfilled bearish FVG
- Checks if current price overlaps these zones
- Checked on: H4, D1, and W1 timeframes

**C. Divergence (Kernel AO — Logic 2)**

- Detects price/oscillator divergence suggesting momentum weakening
- Bullish: Price makes lower low but AO makes higher low
- Bearish: Price makes higher high but AO makes lower high
- Checked on: H4 and D1 timeframes

### Alert Behavior

- **Current**: `alert.freq_all` — fires on every tick while signals exist
- **Continuous updates**: Every evaluation with signals fires a webhook, providing real-time signal state updates
- **No `barstate.isconfirmed` guard**: Fires on realtime bars (not just confirmed bars)
- **Only fires when at least 1 symbol has at least 1 signal** (line 967)
- **Production timeframes** (1H, H4, D1): Signal state changes infrequently between bar closes, resulting in manageable webhook volume

### `request.security()` Budget

| Timeframe | Calls | What's Scanned |
|-----------|-------|----------------|
| H4 | 4 (one per symbol) | NWE + OB/FVG + Divergence combined |
| D1 | 4 (one per symbol) | NWE + OB/FVG + Divergence combined |
| W1 | 4 (one per symbol) | OB/FVG only (no NWE or Divergence) |
| **Total** | **12 of 40 max** | 28 calls remaining for future use |

### Timeframe Configuration (Testing vs Production)

**Important**: The variable names (`TF_H4`, `TF_D1`, `TF_W1`) are misleading — they are legacy names. The actual production timeframes are 1H, H4, and D1.

| Variable | Testing Value | Production Value | Actual Meaning |
|----------|--------------|-----------------|----------------|
| `TF_H4` | `"1"` (1 minute) | `"60"` (1 hour) | **1H timeframe** |
| `TF_D1` | `"5"` (5 minutes) | `"240"` (4 hour) | **H4 timeframe** |
| `TF_W1` | `"15"` (15 minutes) | `"D"` (daily) | **D1 timeframe** |

**Indicator coverage per timeframe**:
- **1H** (via `TF_H4`): NWE + OB/FVG + Divergence
- **H4** (via `TF_D1`): NWE + OB/FVG + Divergence
- **D1** (via `TF_W1`): OB/FVG only (no NWE or Divergence)

---

## 6. TTE Orchestrator (Python)

### Setup Phase Workflow

```python
# Pseudocode for the setup phase
def setup_all_alerts(symbols: list[str]):
    batches = chunk(symbols, size=4)  # 264 batches

    browser = Browser()  # Selenium Chrome
    browser.open_tradingview()
    browser.load_layout("Screener")  # Layout with TTE Screener indicator

    for batch in batches:
        # Input symbols into screener
        browser.open_indicator_settings()
        for i, symbol in enumerate(batch):
            browser.set_symbol_input(f"s{i+1:02d}", symbol)
        browser.close_indicator_settings()

        # Create webhook alert
        browser.click_indicator()  # Select it
        browser.create_webhook_alert(
            webhook_url="https://stock-buddy-app.vercel.app/api/tte/signal",
            condition="Any alert() function call"
        )

        # Track progress
        mark_batch_created(batch)

    print(f"Created {len(batches)} alerts covering {len(symbols)} symbols")
```

### Maintenance Phase Workflow

```python
# Pseudocode for periodic maintenance
def maintain_alerts():
    browser = Browser()
    browser.open_tradingview()
    browser.open_alerts_panel()

    stopped_alerts = browser.find_stopped_alerts()

    for alert in stopped_alerts:
        symbols = get_symbols_for_alert(alert)
        browser.delete_alert(alert)

        # Recreate
        browser.load_layout("Screener")
        browser.input_symbols(symbols)
        browser.create_webhook_alert(webhook_url=WEBHOOK_URL)

    print(f"Restarted {len(stopped_alerts)} stopped alerts")
```

### Key Orchestrator Files

| File | Purpose |
|------|---------|
| `tiered_main.py` | CLI entry point |
| `orchestrator.py` | TieredOrchestrator class |
| `open_tv.py` | Browser automation (Selenium) |
| `api_client.py` | Stock Buddy API client |
| `config.py` | Configuration and validation |

---

## 7. TradingView Alert Lifecycle

### Creation
1. TTE Orchestrator opens alert dialog via Selenium
2. Selects the TTE Screener indicator as the condition
3. Sets "Any alert() function call" as the trigger
4. Enables webhook and enters Stock Buddy URL
5. Clicks Create → TradingView creates a server-side alert

### Running
- Alert runs on TradingView's cloud servers
- Persists even when user closes browser
- Evaluates the screener on every tick (with `alert.freq_all`)
- When signals exist → fires webhook to Stock Buddy
- When no signals exist → does not fire (current behavior)

### Alert Snapshot Behavior
- TradingView captures a **snapshot** of the indicator code when the alert is created
- Editing the Pine Script code does NOT update existing alerts
- To apply script changes: must delete all alerts and recreate them
- This is why the orchestrator has a "setup phase" — it's a one-time batch creation

### Runtime Errors
- If the Pine Script encounters a runtime error (e.g., `na` value arithmetic, array out of bounds), the alert **stops silently**
- No notification is sent to the user
- The alert appears as "stopped" in the TradingView alerts panel
- TTE Orchestrator's maintenance phase detects and restarts these

### Stopped Alert Detection
- TTE opens the alerts panel via Selenium
- Scans for alerts with a "stopped" or "error" status indicator
- Identifies which batch of symbols the stopped alert covered
- Deletes and recreates the alert

---

## 8. Webhook & Stock Buddy API Integration

### Webhook URL

```
https://stock-buddy-app.vercel.app/api/tte/signal
```

### JSON Payload Structure (from the screener)

```json
{
  "timestamp": 1707264000000,
  "signals": [
    {
      "symbol": "GBPAUD",
      "nwe": [
        {
          "zone": "lower_avg",
          "type": "bullish",
          "overlapTimestamp": 1707264000000,
          "timeframe": "H4"
        }
      ],
      "ob_fvg": [
        {
          "zonetype": "OB",
          "subtype": "unmitigated",
          "type": "bullish",
          "zoneTimestamp": 1707260400000,
          "overlapTimestamp": 1707264000000,
          "timeframe": "H4"
        }
      ],
      "divergence": [
        {
          "divType": "Logic 2",
          "type": "bullish",
          "timestamp": 1707264000000,
          "timeframe": "H4"
        }
      ]
    },
    {
      "symbol": "EURCAD",
      "nwe": [
        {
          "zone": "upper_avg",
          "type": "bearish",
          "overlapTimestamp": 1707264000000,
          "timeframe": "D1"
        }
      ],
      "ob_fvg": [],
      "divergence": []
    }
  ]
}
```

**Key rules**:
- Only symbols WITH at least one signal are included (current behavior)
- All signal types are independent — bullish AND bearish can coexist
- Empty arrays mean no signal of that type for that symbol
- `timestamp` is the bar's opening time in milliseconds

### Stock Buddy Endpoint Design: `POST /api/tte/signal`

**Receives**: Webhook payload from TradingView
**Action**: Upserts signal state for each symbol in the payload
**Returns**: `200 OK` with `{ success: true, updated: N }`

```typescript
// Pseudocode for the endpoint
export async function POST(request: Request) {
  const body = await request.json();
  const validated = signalWebhookSchema.parse(body);

  for (const signal of validated.signals) {
    // Upsert: replace entire signal state for this symbol
    await db.collection("tte_live_signals").updateOne(
      { symbol: signal.symbol },
      {
        $set: {
          symbol: signal.symbol,
          nwe: signal.nwe,
          ob_fvg: signal.ob_fvg,
          divergence: signal.divergence,
          last_updated: new Date(),
          // Stock Buddy calculates level from raw signals:
          level: calculateLevel(signal),
        }
      },
      { upsert: true }
    );
  }

  return Response.json({ success: true, updated: validated.signals.length });
}

function calculateLevel(signal) {
  const hasNwe = signal.nwe.length > 0;
  const hasOb = signal.ob_fvg.length > 0;
  const hasDiv = signal.divergence.length > 0;

  if (hasNwe && hasOb && hasDiv) return 3;
  if (hasNwe && (hasOb || hasDiv)) return 2;
  if (hasNwe) return 1;
  return 0;  // shouldn't happen — symbol wouldn't be in payload
}
```

---

## 9. Live Signal State Model

### Decisions Made

- **Payload**: Only symbols WITH active signals are included in the webhook payload. Symbols with no signals are absent.
- **Signal levels**: Not calculated. Raw NWE, OB/FVG, and Divergence signals are displayed independently.
- **Signal disappearance**: Signals are **never auto-removed**. They persist in the database with a `last_updated` timestamp. Users judge freshness by looking at the timestamp.

### How Signals Appear

When a webhook arrives with a symbol's signal data, Stock Buddy **upserts** that symbol's signal state in `tte_live_signals`. Each signal type (NWE, OB, Divergence) for each timeframe is stored independently.

### How Signals "Disappear"

They don't — not automatically. When a signal was active but stops appearing in webhooks:
- The signal remains in the database with its `last_updated` timestamp
- The dashboard shows `last_updated` next to each signal
- Users decide whether a signal is still relevant based on how old it is
- Example: A 1H NWE signal with `last_updated: 3 hours ago` — user knows it may no longer be valid

If the same symbol sends a **new** webhook with **different** signals (e.g., NWE gone but OB still present), the upsert replaces the old state. So signals do get cleared when the screener sends updated data for that symbol — they just don't get cleared when the screener goes silent about that symbol.

### Volume Estimate (Production Timeframes)

With production timeframes (1H, H4, D1) and `alert.freq_all`:
- 1H bars close every hour, H4 every 4 hours, D1 once per day
- Between bar closes, signal state changes are rare (OB/FVG zones are stable, NWE zones shift slowly)
- Alerts fire continuously when signals are present, providing real-time state updates
- **Rough estimate**: ~5,000-50,000 webhooks/day depending on market conditions
- This volume is well within Vercel Pro capacity and has been tested without issues

### MongoDB Document Structure

```json
// tte_live_signals collection — one document per symbol
{
  "_id": "GBPAUD",
  "symbol": "GBPAUD",
  "nwe": [
    {"zone": "lower_avg", "type": "bullish", "overlapTimestamp": 1707264000000, "timeframe": "1H"}
  ],
  "ob_fvg": [
    {"zonetype": "OB", "subtype": "unmitigated", "type": "bullish", "zoneTimestamp": 1707260400000, "overlapTimestamp": 1707264000000, "timeframe": "H4"}
  ],
  "divergence": [],
  "last_updated": "2026-02-06T12:00:00Z"
}
```

### Frontend Display

- Grid with one row per symbol that has signals
- Columns: Symbol | NWE signals | OB/FVG signals | Divergence signals | Last Updated
- Each signal shows its type (bullish/bearish) and timeframe
- `last_updated` shown as relative time ("2 min ago", "1 hour ago")
- No color-coding by level (since levels aren't calculated)
- Filtering by signal type, direction, timeframe available

---

## 10. Symbol Rotation

### Overview

- **Total symbols**: ~1,054
- **Batch size**: 4 symbols per alert
- **Total batches**: ~264 alerts
- **Full rotation**: All 1,054 symbols covered by 264 simultaneously running alerts

### Priority System

| Priority | Description | Scan Frequency | Count |
|----------|-------------|----------------|-------|
| **A** | Major pairs (EURUSD, GBPUSD, etc.) | Every rotation | ~28 |
| **B** | Secondary symbols | Every 3rd rotation | ~150 |
| **C** | Exotic/low-volume | Every 10th rotation | ~763 |

### Rotation Tracking

Stored in MongoDB `tte_rotation_state`:

```json
{
  "_id": "current",
  "batch_number": 264,
  "rotation_number": 1,
  "symbols_scanned_this_rotation": 1054,
  "total_symbols": 1054,
  "last_batch_at": "2026-02-06T12:00:00Z"
}
```

### Important Note

In this architecture, "rotation" is really about the **initial setup**. Once all 264 alerts are created and running, they continuously monitor their 4 symbols. The rotation concept applies to:
1. **Initial setup**: Creating all 264 alerts (takes ~6.6 hours at ~90s per batch)
2. **Re-setup**: If all alerts need to be recreated (e.g., after script update)
3. **Symbol list changes**: If the symbol list changes, alerts need to be recreated for affected batches

---

## 11. Error Handling & Resilience

### Pine Script Runtime Errors

- **Problem**: Runtime errors (na arithmetic, array bounds, etc.) silently stop individual alerts
- **Mitigation**:
  - Defensive coding in Pine Script (na checks, validation)
  - TTE Orchestrator periodically detects and restarts stopped alerts
- **Impact**: 4 symbols go unmonitored until alert is restarted

### TradingView Platform Issues

- **Problem**: TradingView may have outages, slow evaluations, or connectivity issues
- **Mitigation**: Alerts resume automatically when TradingView recovers (server-side)
- **Impact**: Temporary gap in signal updates; `last_updated` timestamps reveal staleness

### Network Failures (Webhook Delivery)

- **Problem**: Webhook POST to Stock Buddy may fail (network issue, Vercel cold start timeout)
- **Mitigation**: TradingView retries failed webhooks (built-in behavior)
- **Impact**: Brief delay in signal updates

### Stock Buddy API Errors

- **Problem**: Zod validation failure, MongoDB write failure
- **Mitigation**: Return appropriate HTTP error codes; TradingView may retry
- **Impact**: Signal state not updated for that tick; next tick will retry

### Stale Data on Dashboard

- **Problem**: If an alert stops and isn't restarted, its 4 symbols show stale data
- **Mitigation**: Frontend checks `last_updated` timestamp and visually indicates staleness
- **Threshold**: If `last_updated` > 60 seconds old, show as stale

---

## 12. Infrastructure & Costs

| Service | Tier | Cost | Purpose |
|---------|------|------|---------|
| TradingView | Premium | ~$14.95/mo | Webhook alerts, server-side execution |
| Vercel | Pro | $20/mo | Stock Buddy API hosting |
| MongoDB Atlas | M2 | $9/mo | Signal storage, 2GB, better connection pool |
| **Total** | | **~$44/mo** | |

### Vercel Capacity Assessment

With production timeframes (1H, H4, D1) and `alert.freq_all`:
- Alerts fire on every tick when signals are present
- 1H bars close every hour, H4 every 4 hours — signal state changes infrequently between bar closes
- **Estimated**: ~5,000-50,000 webhooks/day depending on market activity
- **Monthly**: ~150K-1.5M invocations/month
- Vercel Pro includes 1M/month — this volume is well within limits
- Overage if needed: $0.60 per additional 1M = negligible
- **Verdict**: Tested and confirmed working without capacity issues

---

## 13. Constraints & Limitations

| Constraint | Value | Impact |
|------------|-------|--------|
| Symbols per batch | 4 (hard limit) | More causes memory/runtime errors |
| `request.security()` per indicator | 40 max (12 used) | 28 calls available for future expansion |
| Total alerts needed | 264 | One-time setup takes ~6.6 hours |
| Alert snapshot behavior | Code frozen at creation time | Must delete & recreate after script edits |
| Webhook payload size | ~500 bytes - 2 KB | Well within TradingView's limits |
| Continuous webhook delivery | Every tick when signals present | Requires efficient backend (tested and working) |
| Pine Script v6 | Current version | Uses v6 syntax throughout |

---

## 14. Resolved Decisions & Remaining Questions

### Resolved

| # | Question | Decision |
|---|----------|----------|
| Q1 | Always-send vs only-when-signals payload | **Only symbols with signals**. Dashboard shows `last_updated` timestamp for users to judge freshness. |
| Q2 | Infrastructure | **Vercel Pro + MongoDB M2**. Production timeframes (1H/H4/D1) keep volume manageable (~5K-50K/day). |
| Q3 | Signal level calculation | **No levels**. Raw NWE, OB/FVG, and Divergence signals displayed independently. |
| Q4 | Dashboard display | Grid with raw signals. Columns: Symbol, NWE, OB/FVG, Divergence, Last Updated. No level color-coding. |
| Q6 | Production timeframes | **1H, H4, D1** (mapped to `TF_H4="60"`, `TF_D1="240"`, `TF_W1="D"`). |
| Q7 | Signal disappearance | **Never auto-remove**. Signals persist with `last_updated`. Users judge freshness. |

### Additionally Resolved

| # | Question | Decision |
|---|----------|----------|
| Q8 | Payload timeframe labels | **Update to match reality**: `"1H"`, `"H4"`, `"D1"` in the JSON payload. Requires screener code update. |
| Q10 | Symbol list source | **Stock Buddy API as primary** (fetches from MongoDB), **MongoDB direct as fallback** if API is down. |

### Additionally Resolved (Q5 & Q9)

| # | Question | Decision |
|---|----------|----------|
| Q5 | Alert maintenance frequency | **Every 5 minutes**. Orchestrator runs continuously and calls `restart_inactive_alerts()` (existing method in `handle_alerts.py:240-303`) on each cycle. This method opens the TradingView alerts settings menu → selects "All" → clicks "Restart all inactive" → confirms. Logs each restart event. |
| Q9 | Alert creation approach | **Parallelize with multiple browser tabs/windows**. Each tab handles a separate batch of 4 symbols. Selenium manages multiple tabs via `driver.window_handles` and `driver.switch_to.window()` (pattern already used in `open_entry_chart.py:277-318`). This reduces the ~6.6 hour sequential setup time proportionally to the number of parallel tabs. |

### Q5 Detail: Alert Maintenance

- **Frequency**: Every 5 minutes (configurable via `MAINTENANCE_INTERVAL` env var)
- **Method**: Reuse `restart_inactive_alerts()` from `handle_alerts.py` (lines 240-303)
- **How it works**:
  1. Opens the Alerts tab via `open_alert_tab()`
  2. Clicks the 3-dot settings button (`alerts-settings-button`)
  3. Expands "Show Alerts" section if collapsed
  4. Selects "All" filter to show all alerts
  5. Clicks "Restart all inactive" button
  6. Confirms via the popup dialog ("Yes")
- **Logging**: Each restart cycle logs whether inactive alerts were found and restarted
- **Runs continuously**: The orchestrator's maintenance loop sleeps 5 minutes between checks (not cron-based)

### Q9 Detail: Parallel Alert Creation

- **Approach**: Multiple browser tabs, each creating alerts for different batches
- **Selenium tab management**: Uses existing patterns from the codebase:
  - `driver.execute_script("window.open('about:blank')")` to open new tabs
  - `driver.window_handles` to list all tabs
  - `driver.switch_to.window(handle)` to switch between tabs
- **Workflow**:
  1. Open N tabs (e.g., 4 tabs), each loading TradingView with the "Screener" layout
  2. Assign each tab a subset of the 264 batches (e.g., tab 1 gets batches 1-66, tab 2 gets 67-132, etc.)
  3. Round-robin through tabs: input symbols → create alert → move to next tab
  4. While one tab waits for alert creation confirmation, the orchestrator works on the next tab
- **Estimated speedup**: With 4 parallel tabs, setup drops from ~6.6 hours to ~1.6 hours
- **Constraint**: All tabs share the same TradingView session/account, so alert creation is still serialized on TradingView's side — but the browser automation steps (inputting symbols, navigating UI) overlap with TradingView's server-side processing
