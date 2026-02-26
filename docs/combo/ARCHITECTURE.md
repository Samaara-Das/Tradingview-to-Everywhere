> **Status**: V2 in development (Feb 2026). V1 sections below are being superseded by V2.

---

# Architecture 1: Combo Screener — Complete Design Document

## V2 Architecture Changes (Feb 2026)

V2 moves setup detection, position tracking, and exit detection **into Pine Script**. Stock Buddy receives pre-computed trade positions instead of raw signals.

### What Changed

| Aspect | V1 | V2 |
|--------|----|----|
| Symbols per alert | 3 | **2** |
| Chart timeframe | 1 minute | **30 seconds** |
| Alert frequency | `alert.freq_all` (every tick) | **`alert.freq_once_per_bar_close`** (every 30s) |
| Divergence | Included | **Removed** |
| Setup detection | Stock Buddy (from raw signals) | **Pine Script** (NWE + OB/FVG alignment) |
| Exit detection | Stock Buddy cron (price API) | **Pine Script** (candle high/low vs TP/SL) |
| Payload format | Verbose keys | **Compact keys** (for 2KB limit) |
| Payload content | Raw signals only | **Signals + positions + exits** |
| `request.security()` calls | 12 (4 symbols × 3 TFs) | **8** (2 symbols × 4 call types) |
| Maintenance interval | 300s (5 min) | **150s** (2.5 min) |
| Total symbols | ~1,028 | **626** (expandable to 800) |
| Total alerts | ~338 | **~314** (expandable to 400) |

### V2 Pine Script Indicator

- **File**: `Pine Script Code/TTE Screener V2.txt`
- **Indicator**: "TTE Screener V2" (short title: "Screener V2")
- **`max_bars_back`**: 5000 (for 30s chart `var` history)
- **Position tracking**: `var` state variables (12 per position × 8 positions = 96 vars)
- **Setup types**: LTF (1H NWE + H4/D1 OB) and HTF (H4 NWE + D1 OB), tracked independently
- **Max positions**: 1 LTF buy + 1 HTF buy + 1 LTF sell + 1 HTF sell per symbol (up to 4 concurrent)
- **SL**: MIN(confirming OB zoneLow) for buys, MAX(zoneHigh) for sells
- **TP**: 1:2 risk-reward from entry
- **Exit detection**: Candle high/low vs TP/SL, TP checked before SL
- **Staleness**: `timenow - symTime > 120000` excludes stale symbols from payload

### V2 Category-Aware Symbol Pairing

Symbols are paired within the same asset class (forex with forex, crypto with crypto, etc.) for matching market hours. This is handled by `fetch_symbols_by_category()` in `tte/main.py`.

| Category | Symbols | Alerts |
|----------|---------|--------|
| Currencies | 29 | 15 |
| Crypto | 20 | 10 |
| US Stocks | 376 | 188 |
| Indian Stocks | 201 | 101 |
| **Total** | **626** | **~314** |

### V2 Compact Payload Format

```json
{
  "ts": 1707264000000,
  "s": [{
    "sym": "GBPAUD", "c": 1.985,
    "nwe": [{"z": "la", "t": "bull", "tf": "1H", "ots": 1707264000}],
    "ob": [{"zt": "OB", "st": "un", "t": "bull", "zh": 1.99, "zl": 1.97, "tf": "H4", "zts": 1707260400, "ots": 1707264000}],
    "b": [{"e": 1.98, "sl": 1.975, "tp": 1.99, "et": 1707260000, "l": "LTF", "ntf": "1H", "otf": "H4", "n": true}, null],
    "se": [null, null]
  }]
}
```

Key legend: `ts`=timestamp, `s`=symbols, `sym`=symbol, `c`=close, `nwe`=NWE signals, `ob`=OB/FVG signals, `b`=buy positions [LTF, HTF], `se`=sell positions [LTF, HTF], `e`=entry, `sl`=stopLoss, `tp`=takeProfit, `et`=entryTime, `l`=label(LTF/HTF), `ntf`=nweTf, `otf`=obTf, `n`=isNew, `xt`=exitType(tp/sl), `xp`=exitPrice, `xts`=exitTime

### V2 Position Lifecycle

Tracked per array slot (index 0 = LTF, index 1 = HTF). LTF and HTF are independent:

1. No position: `"b": [null, null]`
2. New LTF setup: `"b": [{"e":1.98, ..., "n": true}, null]` (one bar only)
3. Both running: `"b": [{"e":1.98, ..., "n": false}, {"e":1.97, ..., "n": false}]`
4. LTF exit: `"b": [{"e":1.98, ..., "xt": "tp", "xp": 1.99, "xts": 123}, {"e":1.97, ..., "n": false}]`
5. LTF cleared: `"b": [null, {"e":1.97, ..., "n": false}]` (next bar after exit)

### V2 Files

| File | Change |
|------|--------|
| `Pine Script Code/TTE Screener V2.txt` | **New** — forked from V1 with setup/exit tracking |
| `combo_settings.yaml` | Updated: 30s timeframe, batch_size=2, 150s maintenance |
| `tte/main.py` | Updated: `fetch_symbols_by_category()` for category-aware pairing |

---

> **V1 documentation follows below** for reference. V1 is no longer in active use.

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
TTE needs to monitor ~1,028 trading symbols across multiple timeframes for NWE, Order Block/FVG, and Divergence signals, then display those signals in real-time on the Stock Buddy dashboard.

### Why Combo Screener (Architecture 1) Over Separate Screeners (Architecture 2)

Two architectures were evaluated:

- **Architecture 1 (Combo)**: Single Pine Script indicator combining NWE + OB/FVG + Divergence. 3 symbols per batch, 1 alert per batch.
- **Architecture 2 (Separate)**: 3 separate Pine Script indicators (NWE, OB, Divergence). 3 symbols per batch, 3 alerts per batch.

Architecture 1 was chosen because:

| Factor | Arch 1 (Combo) | Arch 2 (Separate) |
|--------|---------------|-------------------|
| Alert cycles for 1,028 symbols | **338** | **1,014** (3x more) |
| Browser automation interactions | 338 create | 1,014 create |
| Setup approach | Single browser, sequential | Single browser, sequential |
| Signal merging needed | No — single payload has all data | Yes — 3 payloads must be correlated per batch |
| Pine Script already built | Yes | No — would need 3 new scripts |
| Selenium failure surface | Lower | 3x higher |

The 4-symbol hard limit (more causes memory/runtime errors in TradingView) eliminates Architecture 2's main advantage (larger batch sizes per screener). Production uses 3 symbols per batch for optimal 1-minute chart performance.

---

## 2. System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    ONE-TIME SETUP PHASE                         │
│                                                                 │
│  TTE Orchestrator (Python + Selenium, headless Chrome)          │
│  ├── Fetches ~1,028 symbols                                    │
│  ├── Takes batch of 3 symbols                                  │
│  ├── Opens TradingView, inputs symbols into combo screener     │
│  ├── Creates webhook alert → points to Stock Buddy API         │
│  ├── Repeats for all 338 batches (single browser, sequential)  │
│  └── Result: 338 alerts live on TradingView                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CONTINUOUS OPERATION                          │
│                                                                 │
│  TradingView (Server-Side)                                     │
│  ├── 338 alerts running continuously                           │
│  ├── Each alert monitors 3 symbols via combo screener          │
│  ├── On every tick: evaluates all signals                      │
│  ├── Fires webhook with JSON payload when signals exist        │
│  └── Alerts persist even when browser is closed                │
│           │                                                     │
│           ▼                                                     │
│  Stock Buddy API (Vercel / Next.js)                            │
│  ├── POST /api/tte/combo — receives webhook                    │
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
│                   MAINTENANCE (Every 5 min)                     │
│                                                                 │
│  TTE Orchestrator                                              │
│  ├── Refreshes page to prevent stale browser state             │
│  ├── Clears alert log to reduce memory usage                   │
│  ├── Restarts any alerts that stopped due to runtime errors    │
│  └── Has priority over snapshots (same browser)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CHART SNAPSHOTS (Every 60s)                   │
│                                                                 │
│  TTE Snapshot Worker (async polling, same browser)             │
│  ├── Polls Stock Buddy for pending setup snapshots             │
│  ├── Switches to "Snapshot" layout (NWE + Trade Drawer)        │
│  ├── For each: symbol → timeframe → Trade Drawer inputs        │
│  ├── Takes screenshot via Alt+S → gets PNG/TV URLs             │
│  ├── Reports URLs back to Stock Buddy API                      │
│  └── Setup messages display chart images in Stock Buddy UI     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Details

### 3.1 TTE Combo Screener (Pine Script)

- **File**: `Pine Script Code/TTE Screener.txt`
- **Version**: Pine Script v6
- **Indicator name**: "TTE Screener" (short title: "Screener")
- **Symbols**: 3 per instance in production (4-symbol hard limit — more causes memory/runtime errors)
- **Timeframes scanned**: H4, D1 (NWE + OB + Divergence), W1 (OB only)
- **`request.security()` calls**: 12 of 40 max (4×H4 + 4×D1 + 4×W1) — uses 4-symbol capacity
- **Signal types detected**:
  - **NWE (Nadaraya-Watson Envelope)**: Price in lower/upper envelope zones on H4/D1
  - **OB/FVG (Order Block / Fair Value Gap)**: Unmitigated OBs, breaker zones, unfilled FVGs on H4/D1/W1
  - **Divergence (Kernel AO)**: Logic 2 divergence on H4/D1
- **Alert behavior**: Fires on every tick (`alert.freq_all`) when at least 1 signal exists across any of its symbols
- **No signal hierarchy**: All raw signals are sent; Stock Buddy calculates levels
- **Continuous webhook delivery**: Fires on every evaluation when signals are present, providing real-time updates
- **Payload**: Rich nested JSON with all signal details (see Section 8)

### 3.2 TTE Orchestrator (Python)

- **File**: `tte/main.py`, `tte/config.py`
- **Purpose**: One-time setup of all 338 alerts, plus periodic maintenance
- **Technology**: Python + Selenium (single headless Chrome browser)
- **GUI**: `tte_gui.py` (or standalone `dist/TTE.exe`) provides a desktop interface for settings and execution
- **Responsibilities**:
  1. Fetch symbol list (~1,028 symbols)
  2. Batch into groups of 3
  3. For each batch: open TradingView → input symbols → create webhook alert (sequential, single browser)
  4. Periodically: refresh page, clear alert log, restart stopped alerts

### 3.3 TradingView Platform

- **Subscription**: Premium (required for webhooks)
- **338 alerts**: All running simultaneously as server-side alerts
- **Each alert**: Monitors 3 symbols via the combo screener indicator
- **Server-side execution**: Alerts continue running after browser is closed
- **Alert snapshots**: When an alert is created, TradingView captures a snapshot of the indicator. Editing the script does NOT update existing alerts — they must be deleted and recreated.

### 3.4 Stock Buddy API (Next.js / Vercel)

- **Repository**: `C:\Users\dassa\Work\Stock-Buddy-App`
- **Endpoint**: `POST /api/tte/combo`
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

### 3.7 Chart Snapshot Worker

- **File**: `tte/snapshot_worker.py`
- **Purpose**: Asynchronously captures TradingView chart screenshots for setup messages
- **Technology**: Same Selenium browser as orchestrator, polls Stock Buddy API
- **Components**:
  - `StockBuddyClient`: HTTP client for `GET /api/tte/snapshots/pending` and `POST /api/tte/snapshots/update`
  - `SnapshotWorker`: Orchestrates chart screenshots using existing browser automation
- **TradingView layout**: "Snapshot" (separate from "Screener") with NWE + Trade Drawer v2 indicators. The maintenance loop switches to this layout at startup and stays on it for the entire session.
- **Trade Drawer v2**: Pine Script indicator (`Pine Script Code/Trade Drawer.txt`, v6) that draws entry/SL/TP levels on the chart. Controlled via 4 input fields: entry_time, entry_price, sl, tp1.
- **Chart defaults**: Bar style `candle`, with "Bars to right" margin set to 60 via chart settings (applied once at startup, then refreshed every 24h).
- **Dual-timer integration**: Runs every 60s in the maintenance loop. Maintenance (every 5 min) has priority — if both timers fire simultaneously, snapshots skip that tick.
- **Snapshot method**: Alt+R (auto-fit/reset scale) → Alt+S (snapshot) → reads clipboard URL via `navigator.clipboard.readText()` (CDP clipboard permission granted for headless Chrome)
- **Workflow per setup**: change_symbol → force_change_tframe → show legend → set Trade Drawer inputs → hide legend → Alt+R auto-fit → Alt+S snapshot → show legend → report URL
- **Initialization**: `_set_bars_to_right()` sets the right margin (60 bars) via the chart settings dialog (Canvas tab → `paneRightMargin` input). Runs once at startup, then every 24 hours.
- **Error handling**: Each setup processed independently; failures reported to Stock Buddy (max 3 retries). "Processing" snapshots older than 10 min auto-reset to "pending" by Stock Buddy.
- **GUI config**: Snapshot settings (enabled, layout name, bar style, batch size, poll interval, bars to right) are exposed in the GUI settings card.

### 3.8 Trade Drawer Indicator (Pine Script)

- **File**: `Pine Script Code/Trade Drawer.txt`
- **Version**: Pine Script v6
- **Purpose**: Draws entry/SL/TP levels on chart for snapshot screenshots
- **Inputs**: entry_time (Unix ms), entry_price, sl_price, tp1_price, tp2_price, tp3_price + 20 symbol inputs (for TTE to find the indicator)
- **Drawing behavior**: Only draws on `barstate.islast` (avoids broken coordinates from bar 0). Deletes old drawings before redrawing.
- **Colors**: Orange `#FF6D00` for SL zone, Blue `#2962FF` for TP zone (distinct from NWE's red/green)

---

## 4. Data Flow — End to End

### Phase 1: Alert Setup (One-Time)

```
Step 1: TTE Orchestrator starts
Step 2: Fetches symbol list from Stock Buddy API or local config
        → Returns ~1,028 symbols
Step 3: Divides into 338 batches of 3 symbols each
Step 4: For batch #1 (e.g., GBPAUD, AUDJPY, EURCAD):
        a. Opens TradingView in headless Chrome via Selenium
        b. Loads the "Screener" layout (has TTE Screener indicator)
        c. Opens indicator settings panel
        d. Inputs 3 symbols into s01-s03 fields
        e. Clicks the indicator on chart to select it
        f. Opens alert dialog
        g. Selects "Any alert() function call" as condition
        h. Goes to Notifications tab
        i. Enables webhook checkbox
        j. Enters webhook URL: https://stock-buddy-app.vercel.app/api/tte/combo
        k. Clicks Create
Step 5: Repeats Step 4 for all 338 batches (sequential, single browser)
Step 6: All 338 alerts are now live on TradingView's servers
```

### Phase 2: Continuous Signal Flow

```
Step 1: TradingView server evaluates alert #47 (symbols: GBPAUD, AUDJPY, EURCAD)
Step 2: Combo screener runs on current tick
        → GBPAUD has bullish NWE on 1H + bullish OB on H4
        → AUDJPY has no signals
        → EURCAD has bearish NWE on H4
Step 3: Screener builds JSON payload:
        - GBPAUD included with NWE + OB data
        - AUDJPY excluded (no signals)
        - EURCAD included with NWE data
Step 4: alert() fires → TradingView sends POST to Stock Buddy webhook URL
Step 5: Stock Buddy receives payload
        a. Zod validates the JSON structure
        b. For GBPAUD: upserts signal state (NWE + OB active, last_updated = now)
        c. For EURCAD: upserts signal state (NWE active, last_updated = now)
        d. AUDJPY: not in payload, its existing state (if any) is untouched
        e. Returns 200 OK
Step 6: Frontend polls signals endpoint
        → Shows GBPAUD with NWE + OB signals (last updated: just now)
        → Shows EURCAD with NWE signal (last updated: just now)
        → AUDJPY: if it had old signals, those persist with old last_updated
        → User sees timestamps and judges freshness
```

### Phase 3: Maintenance (Every 5 min)

```
Step 1: TTE Orchestrator runs maintenance check (every 5 minutes)
Step 2: Refreshes the TradingView page to prevent stale browser state
Step 3: Clears the alert log to reduce memory usage
Step 4: Opens TradingView alerts panel via Selenium
Step 5: Clicks "Restart all inactive" to restart any stopped alerts
Step 6: All alerts are running again on TradingView's servers
```

### Phase 4: Chart Snapshots (Every 60s)

```
Step 1: TTE Snapshot Worker polls Stock Buddy: GET /api/tte/snapshots/pending
Step 2: If pending setups exist (up to 5 per batch):
        a. Switches to "Snapshot" layout (NWE + Trade Drawer indicators)
        b. Sets bar style to candle
        c. Ensures legend is visible
Step 3: For each pending setup:
        a. Changes chart symbol (e.g., GBPCAD)
        b. Changes timeframe (1H or 4H based on nweTf)
        c. Shows legend, opens Trade Drawer settings, fills entry_time/entry_price/sl/tp1
        d. Hides indicator legend (clean screenshot)
        e. Alt+R → auto-fit/reset chart scale
        f. Alt+S → captures snapshot URL from clipboard
        g. Shows legend again
        h. Reports PNG/TV URLs back: POST /api/tte/snapshots/update
Step 4: Setup message in Stock Buddy now displays the chart image
        (pending → completed, with clickable snapshot)
```

**Timing**: Setup text appears instantly in Stock Buddy. Chart image appears
within ~1-2 minutes (60-second polling interval). Similar to how messaging
apps load link previews asynchronously.

**Browser contention**: Maintenance has priority. If both timers fire at the
same time (e.g., at 300s), maintenance runs and snapshots skip that tick.
The same browser instance is shared — they never run concurrently.

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
    batches = chunk(symbols, size=3)  # 338 batches

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
            webhook_url="https://stock-buddy-app.vercel.app/api/tte/combo",
            condition="Any alert() function call"
        )

        # Track progress
        mark_batch_created(batch)

    print(f"Created {len(batches)} alerts covering {len(symbols)} symbols")
```

### Maintenance Loop (Dual Timers)

```python
# Pseudocode for the dual-timer maintenance loop
def run_maintenance(browser, config):
    snapshot_worker = SnapshotWorker(browser, config) if config.snapshot_enabled else None

    while not shutdown_requested:
        maintenance_due = (now - last_maintenance) >= 300  # 5 minutes

        # Maintenance has priority (same browser, can't run concurrently)
        if maintenance_due:
            browser.refresh_page()
            browser.restart_inactive_alerts()
            browser.clear_alert_log()

        # Snapshots run only when maintenance isn't running
        if snapshot_worker and (now - last_snapshot) >= 60 and not maintenance_due:
            snapshot_worker.process_pending_snapshots()

        sleep(60)  # Tick interval = min(snapshot_interval, maintenance_interval)
```

### Key Orchestrator Files

| File | Purpose |
|------|---------|
| `combo_main.py` | Backward-compatible entry point (shim for `tte/main.py`) |
| `tte/main.py` | CLI entry point (orchestrator + dual-timer maintenance) |
| `tte/config.py` | ComboConfig dataclass (loads combo_settings.yaml) |
| `tte/snapshot_worker.py` | Chart snapshot polling + browser orchestration |
| `combo_settings.yaml` | All combo mode settings (incl. snapshot config) |
| `tte_gui.py` | GUI interface (also `dist/TTE.exe`) |
| `tte/browser/tradingview.py` | Browser automation (Selenium) |
| `Pine Script Code/Trade Drawer.txt` | Trade Drawer v6 indicator for chart snapshots |

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
https://stock-buddy-app.vercel.app/api/tte/combo
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

### Stock Buddy Endpoint Design: `POST /api/tte/combo`

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

- **Total symbols**: ~1,028
- **Batch size**: 3 symbols per alert
- **Total batches**: 338 alerts (targets 343 for full coverage)
- **Full rotation**: All 1,028 symbols covered by 338+ simultaneously running alerts

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
  "batch_number": 338,
  "rotation_number": 1,
  "symbols_scanned_this_rotation": 1028,
  "total_symbols": 1028,
  "last_batch_at": "2026-02-06T12:00:00Z"
}
```

### Important Note

In this architecture, "rotation" is really about the **initial setup**. Once all 338 alerts are created and running, they continuously monitor their 3 symbols. The rotation concept applies to:
1. **Initial setup**: Creating all 338 alerts (sequential, single browser)
2. **Re-setup**: If all alerts need to be recreated (e.g., after script update)
3. **Symbol list changes**: If the symbol list changes, alerts need to be recreated for affected batches

---

## 11. Error Handling & Resilience

### Pine Script Runtime Errors

- **Problem**: Runtime errors (na arithmetic, array bounds, etc.) silently stop individual alerts
- **Mitigation**:
  - Defensive coding in Pine Script (na checks, validation)
  - TTE Orchestrator periodically detects and restarts stopped alerts
- **Impact**: 3 symbols go unmonitored until alert is restarted

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

- **Problem**: If an alert stops and isn't restarted, its 3 symbols show stale data
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
| Symbols per batch | 3 in production (4 hard limit) | More causes memory/runtime errors |
| `request.security()` per indicator | 40 max (12 used) | 28 calls available for future expansion |
| Total alerts needed | 338 | One-time setup, single browser sequential |
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
| Q9 | Alert creation approach | **Single browser, sequential**. Each batch of 3 symbols is processed one at a time in a single headless Chrome instance. Parallel tab approach was evaluated but abandoned in favor of simplicity and reliability. |

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

### Q9 Detail: Single Browser Sequential Creation

- **Approach**: Single headless Chrome browser, processing batches sequentially
- **Why not parallel**: Parallel tab approach was evaluated but abandoned — single browser is simpler, more reliable, and avoids TradingView session limit issues
- **Workflow**:
  1. Open one headless Chrome instance with the "Screener" layout
  2. For each of the 338 batches: input 3 symbols → create webhook alert → next batch
  3. Progress tracked in `combo_progress.json` for resume capability
- **Headless mode**: Runs without visible browser window (`headless: true` in combo_settings.yaml)
- **GUI**: `tte_gui.py` (or `dist/TTE.exe`) provides a desktop interface for configuration and execution
