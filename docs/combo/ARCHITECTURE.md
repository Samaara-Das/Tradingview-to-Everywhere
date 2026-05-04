> **Status**: V2 in production (Feb 2026). V1 sections below are archived for reference.

---

# Architecture 1: Combo Screener — Complete Design Document

## V2 Architecture Changes (Feb 2026)

V2 uses stateless setup detection in Pine Script. On every bar, if NWE + OB/FVG conditions align, setup data is sent to Stock Buddy, which handles deduplication (DB-level partial unique index) and exit detection (server-side cron every 5 min via Binance/Yahoo candle data).

### What Changed

| Aspect | V1 | V2 |
|--------|----|----|
| Symbols per alert | 3 | **2** |
| Chart timeframe | 1 minute | **45 seconds** |
| Alert frequency | `alert.freq_all` (every tick) | **`alert.freq_once_per_bar_close`** (every 45s) |
| Divergence | Included | **Removed** |
| Setup detection | Stock Buddy (from raw signals) | **Pine Script** (stateless NWE + OB/FVG alignment) |
| Exit detection | Pine Script (candle high/low) | **Stock Buddy cron** (every 5 min via Binance/Yahoo candles) |
| Payload format | Verbose keys | **Compact keys** (for 2KB limit) |
| Payload content | Raw signals only | **Signals + setups** (exits handled server-side) |
| `request.security()` calls | 12 (4 symbols × 3 TFs) | **8** (2 symbols × 4 call types) |
| Maintenance interval | 300s (5 min) | **150s** (2.5 min) |
| Total symbols | ~1,028 | **620** (expandable to 800) |
| Total alerts | ~338 | **~310** (expandable to 400) |

### V2 Pine Script Indicator

- **File**: `Pine Script Code/TTE Screener V2.txt`
- **Indicator**: "TTE Screener V2" (short title: "Screener V2")
- **`max_bars_back`**: 5000
- **Stateless**: No `var` position tracking. Setup data computed fresh each bar.
- **Setup types**: LTF (1H NWE + H4/D1 OB) and HTF (H4 NWE + D1 OB), independent
- **SL**: MIN(confirming OB zoneLow) for buys, MAX(zoneHigh) for sells
- **TP**: 1:2 risk-reward from entry
- **Exit detection**: Handled by Stock Buddy cron (not in Pine Script)
- **Dedup**: Stock Buddy uses partial unique DB index — same setup sent repeatedly is ignored

### V2 Category-Aware Symbol Pairing

Symbols are paired within the same asset class (forex with forex, crypto with crypto, etc.) for matching market hours. This is handled by `fetch_symbols_by_category()` in `tte/main.py`.

| Category | Symbols | Alerts |
|----------|---------|--------|
| Currencies | 29 | 15 |
| Crypto | 18 | 9 |
| US Stocks | 376 | 188 |
| Indian Stocks | 197 | 99 |
| **Total** | **620** | **~310** |

### V2 Compact Payload Format

```json
{
  "ts": 1707264000000,
  "s": [{
    "sym": "GBPAUD", "c": 1.985,
    "nwe": [{"z": "la", "t": "bull", "tf": "1H", "ots": 1707264000}],
    "ob": [{"zt": "OB", "st": "un", "t": "bull", "zh": 1.99, "zl": 1.97, "tf": "H4", "zts": 1707260400, "ots": 1707264000}],
    "b": [{"e": 1.98, "sl": 1.975, "tp": 1.99, "et": 1707260000, "l": "LTF", "ntf": "1H", "otf": "H4"}, null],
    "se": [null, null]
  }]
}
```

Key legend: `ts`=timestamp, `s`=symbols, `sym`=symbol, `c`=close, `nwe`=NWE signals, `ob`=OB/FVG signals, `b`=buy setups [LTF, HTF], `se`=sell setups [LTF, HTF], `e`=entry, `sl`=stopLoss, `tp`=takeProfit, `et`=entryTime, `l`=label(LTF/HTF), `ntf`=nweTf, `otf`=obTf

### V2 Stateless Setup Behavior

Setup slots (`b` and `se` arrays, index 0 = LTF, index 1 = HTF) are computed fresh each bar:

- **Non-null** = NWE + OB/FVG conditions currently align for that setup type
- **`null`** = no conditions align
- Stock Buddy deduplicates: first non-null creates a setup, subsequent identical signals are ignored
- Exit detection is server-side (Stock Buddy cron checks Binance/Yahoo candles every 5 min)

### V2 Files

| File | Change |
|------|--------|
| `Pine Script Code/TTE Screener V2.txt` | **Stateless** — setup detection only, no position tracking or exit detection |
| `combo_settings.yaml` | Updated: 45s timeframe, batch_size=2, 150s maintenance |
| `tte/main.py` | Updated: `fetch_symbols_by_category()` for category-aware pairing |

---

## Docker / Linux Deployment (added 2026-04-30)

TTE now runs as a Docker service on the Hostinger VPS (`168.231.103.163`, KVM8) alongside Stock Buddy. Dev on Windows, prod on Linux — same codebase, same Pine Script.

### Container Shape

- **Image**: `python:3.11-slim-bookworm` base. Installs Chrome stable + matching ChromeDriver via the chrome-for-testing `LATEST_RELEASE_<MAJOR>` API (do NOT construct the URL from `chrome --product-version` — that endpoint is gone).
- **Service name**: `tte-1` (one container per TradingView Ultimate account; scale by adding `tte-2`, `tte-3`, etc.).
- **User**: non-root `tte` (uid 1000).
- **Entrypoint**: `python -m tte.main`.

### Per-Instance Isolation

Each `tte-N` container needs its own:
- **Chrome user-data-dir volume** mounted at `/home/tte/chrome-profile` — keeps the TV session, cookies, and any TV-side preferences isolated. No cross-container profile collisions.
- **`CHROME_PROFILE` env override** — `tte/config.py` reads `os.getenv("CHROME_PROFILE", "Profile 4")`. Inside a container we set `CHROME_PROFILE=Default` because the user-data-dir volume only contains one profile dir.
- **Log volume** mounted at `/app/logs` — `tte/log.py` writes to `${LOG_DIR:-logs}/app_log.log`. The compose file binds this to a host path so logs survive container rebuilds.

### Networking

- **Mongo**: containers connect to a local MongoDB service on the same Docker network (no longer Atlas).
- **Webhook**: alerts post to `https://stockbuddy.co/api/tte/combo` (was `*.vercel.app` previously — DNS now points at the VPS).
- **Snapshot uploads**: `STOCK_BUDDY_API_URL=http://stockbuddy:3000/api/tte` — Docker DNS over the internal network, no public hop.

### Bootstrap: TV Cookie Injection

TV's auto-login form does NOT survive Cloudflare/bot defenses on a fresh container Chrome. Run `inject_tv_cookies.py` once per new user-data-dir volume to seed `sessionid` + `sessionid_sign` cookies before bringing up `tte-1`. See `docs/SETUP.md` "Linux/Docker" section for the exact command.

### Platform-Portable Patches

The three platform-conditional patches that made the Linux port work (`platform.system()` guard for Chrome cleanup, `LOG_DIR` env, `CHROME_PROFILE` env) are documented in the root `CLAUDE.md`. None of them break Windows behaviour — defaults match the pre-port hard-coded values.

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

> **V1 archived section.** V2 uses 620 symbols, 2 per alert, ~310 alerts, 45-second timeframe, no divergence.

### Problem
TTE needs to monitor hundreds of trading symbols across multiple timeframes for NWE and Order Block/FVG signals, track positions, and send pre-computed trade state to Stock Buddy for real-time display.

### Why Combo Screener (Architecture 1) Over Separate Screeners (Architecture 2)

Two architectures were evaluated:

- **Architecture 1 (Combo)**: Single Pine Script indicator combining NWE + OB/FVG. 2 symbols per batch, 1 alert per batch.
- **Architecture 2 (Separate)**: 2 separate Pine Script indicators. 2 symbols per batch, 2 alerts per batch.

Architecture 1 was chosen because:

| Factor | Arch 1 (Combo) | Arch 2 (Separate) |
|--------|---------------|-------------------|
| Alert cycles for 620 symbols | **~310** | **~620** (2x more) |
| Browser automation interactions | 310 create | 620 create |
| Setup approach | Single browser, sequential | Single browser, sequential |
| Signal merging needed | No — single payload has all data | Yes — payloads must be correlated per batch |
| Pine Script already built | Yes | No |
| Selenium failure surface | Lower | 2x higher |

The 4-symbol hard limit (more causes memory/runtime errors in TradingView) and the goal of minimizing alert count make the combo approach optimal. V2 uses 2 symbols per batch for 45-second chart performance.

---

## 2. System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    ONE-TIME SETUP PHASE                         │
│                                                                 │
│  TTE Orchestrator (Python + Selenium, headless Chrome)          │
│  ├── Fetches 620 symbols (category-aware pairing)              │
│  ├── Takes batch of 2 symbols (same category)                  │
│  ├── Opens TradingView, inputs symbols into combo screener     │
│  ├── Creates webhook alert → points to Stock Buddy API         │
│  ├── Repeats for all ~310 batches (single browser, sequential) │
│  └── Result: ~310 alerts live on TradingView                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CONTINUOUS OPERATION                          │
│                                                                 │
│  TradingView (Server-Side)                                     │
│  ├── ~310 alerts running continuously                          │
│  ├── Each alert monitors 2 symbols via V2 combo screener       │
│  ├── On every 45-second bar close: evaluates signals/positions │
│  ├── Fires webhook with compact JSON payload                   │
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
│                   MAINTENANCE (Every 2.5 min)                   │
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

> **V2 active.** V1 (`TTE Screener.txt`) is archived.

- **File**: `Pine Script Code/TTE Screener V2.txt`
- **Version**: Pine Script v6
- **Indicator name**: "TTE Screener V2" (short title: "Screener V2")
- **Symbols**: 2 per instance (4-symbol hard limit — more causes memory/runtime errors)
- **Timeframes scanned**: 1H (NWE + OB), H4 (NWE + OB), D1 (OB only) — divergence removed in V2
- **`request.security()` calls**: 8 of 40 max (2 symbols × 4 call types)
- **Signal types detected**:
  - **NWE (Nadaraya-Watson Envelope)**: Price in lower/upper envelope zones on 1H/H4
  - **OB/FVG (Order Block / Fair Value Gap)**: Unmitigated OBs, breaker zones, unfilled FVGs on 1H/H4/D1
- **Setup detection**: Stateless — computes setup data fresh each bar (up to 4 per symbol: LTF buy, HTF buy, LTF sell, HTF sell)
- **Alert behavior**: Fires on every 45-second bar close (`alert.freq_once_per_bar_close`)
- **Payload**: Compact JSON with abbreviated keys (see Section 8 and V2 section at top)

### 3.2 TTE Orchestrator (Python)

- **File**: `tte/main.py`, `tte/config.py`
- **Purpose**: One-time setup of all ~310 alerts, plus periodic maintenance
- **Technology**: Python + Selenium (single headless Chrome browser)
- **GUI**: `tte_gui.py` (or standalone `dist/TTE.exe`) provides a desktop interface for settings and execution
- **Responsibilities**:
  1. Fetch 620 symbols from MongoDB, grouped by category
  2. Pair into batches of 2 within the same category (category-aware pairing)
  3. For each batch: open TradingView → input symbols → create webhook alert (sequential, single browser)
  4. Periodically (every 2.5 min): refresh page, clear alert log, restart stopped alerts

### 3.3 TradingView Platform

- **Subscription**: Premium (required for webhooks)
- **~310 alerts**: All running simultaneously as server-side alerts
- **Each alert**: Monitors 2 symbols via the V2 combo screener indicator
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
- **Trade Drawer v2**: Pine Script indicator (`Pine Script Code/Trade Drawer V2.txt`, v6) that draws NWE bands + entry/SL/TP levels on the chart. Controlled via 4 input fields: entry_time, entry_price, sl, tp1.
- **Chart defaults**: Bar style `candle`, with "Bars to right" margin set to 60 via chart settings (applied once at startup, then refreshed every 24h).
- **Dual-timer integration**: Runs every 60s in the maintenance loop. Maintenance (every 2.5 min) has priority — if both timers fire simultaneously, snapshots skip that tick.
- **Snapshot method**: Alt+R (auto-fit/reset scale) → Alt+S (snapshot) → reads clipboard URL via `navigator.clipboard.readText()` (CDP clipboard permission granted for headless Chrome)
- **Workflow per setup**: change_symbol → force_change_tframe → show legend → set Trade Drawer inputs → hide legend → Alt+R auto-fit → Alt+S snapshot → show legend → report URL
- **Initialization**: `_set_bars_to_right()` sets the right margin (60 bars) via the chart settings dialog (Canvas tab → `paneRightMargin` input). Runs once at startup, then every 24 hours.
- **Error handling**: Each setup processed independently; failures reported to Stock Buddy (max 3 retries). "Processing" snapshots older than 10 min auto-reset to "pending" by Stock Buddy.
- **GUI config**: Snapshot settings (enabled, layout name, bar style, batch size, poll interval, bars to right) are exposed in the GUI settings card.

### 3.8 Trade Drawer Indicator (Pine Script)

- **File**: `Pine Script Code/Trade Drawer V2.txt`
- **Version**: Pine Script v6
- **Purpose**: Self-contained indicator: NWE bands + entry/SL/TP trade levels on chart for snapshot screenshots
- **Inputs**: entry_time (Unix seconds, converted to ms internally), entry_price, sl_price, tp1_price + symbol inputs (for TTE to find the indicator)
- **Drawing behavior**: NWE bands via 7 plots + 4 fills; trade levels drawn on `barstate.islast` with 15-bar span. Deletes old drawings before redrawing.
- **Colors**: Orange `#FF6D00` for SL zone, Blue `#2962FF` for TP zone (distinct from NWE's red/green)

---

## 4. Data Flow — End to End

### Phase 1: Alert Setup (One-Time)

```
Step 1: TTE Orchestrator starts
Step 2: Fetches 620 symbols from MongoDB, grouped by category
Step 3: Divides into ~310 batches of 2 symbols (same category per batch)
Step 4: For batch #1 (e.g., GBPAUD, AUDJPY — both currencies):
        a. Opens TradingView in headless Chrome via Selenium
        b. Loads the "Screener" layout (has TTE Screener V2 indicator)
        c. Opens indicator settings panel
        d. Inputs 2 symbols into s01-s02 fields
        e. Clicks the indicator on chart to select it
        f. Opens alert dialog
        g. Selects "Any alert() function call" as condition
        h. Goes to Notifications tab
        i. Enables webhook checkbox
        j. Enters webhook URL: https://stockbuddy.co/api/tte/combo
        k. Clicks Create
Step 5: Repeats Step 4 for all ~310 batches (sequential, single browser)
Step 6: All ~310 alerts are now live on TradingView's servers
```

### Phase 2: Continuous Signal Flow

```
Step 1: TradingView server evaluates alert #47 (symbols: GBPAUD, AUDJPY)
Step 2: V2 combo screener runs on 45-second bar close
        → GBPAUD: bullish NWE on 1H + bullish OB on H4 → new LTF setup detected
        → AUDJPY: no conditions align this bar
Step 3: Screener builds compact JSON payload:
        - GBPAUD: nwe signals, ob signals, buy[0] = LTF setup data (entry/SL/TP)
        - AUDJPY: buy[0] = null (no conditions)
        - Stale symbols (timenow - symTime > 120000ms) excluded
Step 4: alert() fires → TradingView sends POST to Stock Buddy webhook URL
Step 5: Stock Buddy receives compact payload
        a. Zod validates the JSON structure
        b. Upserts signal + position state for each symbol
        c. Returns 200 OK
Step 6: Frontend polls signals endpoint
        → Shows setups, entry/SL/TP, NWE + OB signals per symbol
```

### Phase 3: Maintenance (Every 2.5 min)

```
Step 1: TTE Orchestrator runs maintenance check (every 2.5 minutes / 150s)
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

> **V2 active** (`TTE Screener V2.txt`). Divergence removed. 2 symbols per alert. Stateless setup detection; exit detection server-side.

### Signal Detection Logic (V2)

**A. NWE (Nadaraya-Watson Envelope)**

- Uses kernel regression to create support/resistance envelope bands
- Bullish signal: Price overlaps lower envelope zones (lower_near or lower_avg)
- Bearish signal: Price overlaps upper envelope zones (upper_near or upper_avg)
- Checked on: 1H and H4 timeframes

**B. OB/FVG (Order Block / Fair Value Gap)**

- Detects institutional supply/demand zones
- Bullish signals: Unmitigated bullish OB, breaker support, unfilled bullish FVG
- Bearish signals: Unmitigated bearish OB, breaker resistance, unfilled bearish FVG
- Checks if current price overlaps these zones
- Checked on: H4 and D1 timeframes

**C. Divergence** — **Removed in V2**

### Stateless Setup Detection (V2)

- **Setup detection**: NWE + OB/FVG alignment triggers LTF (1H NWE + H4 OB) or HTF (H4 NWE + D1 OB) setups
- **No position tracking**: Computed fresh each bar, no `var` state
- **Exit detection**: Server-side (Stock Buddy cron, 5-min candles from Binance/Yahoo)
- **TP**: 1:2 risk-reward from entry; **SL**: MIN/MAX of confirming OB zone
- **Dedup**: Stock Buddy uses partial unique DB index (`{ symbol, dedupKey }` where `outcome: "running"`)

### Alert Behavior (V2)

- `alert.freq_once_per_bar_close` — fires once per 45-second bar close
- Fires every bar (not conditional on signals) — payload always includes both symbols
- Stale symbols (market closed) excluded via staleness check

### `request.security()` Budget (V2)

| Call Type | Calls | What's Fetched |
|-----------|-------|----------------|
| Per symbol (2 symbols) | 4 calls each | NWE bands (1H, H4) + OB data (H4, D1) |
| **Total** | **8 of 40 max** | 32 calls remaining for future use |

### Timeframe Configuration (V2)

| Purpose | Timeframe | Description |
|---------|-----------|-------------|
| LTF NWE | 1H | Lower timeframe envelope |
| HTF NWE | H4 | Higher timeframe envelope |
| LTF OB | H4 | Order blocks for LTF setups |
| HTF OB | D1 | Order blocks for HTF setups |

---

## 6. TTE Orchestrator (Python)

### Setup Phase Workflow

```python
# Pseudocode for the setup phase (V2)
def setup_all_alerts():
    batches, total = fetch_symbols_by_category(batch_size=2)  # ~310 batches of 2

    browser = Browser()  # Selenium Chrome
    browser.open_tradingview()
    browser.load_layout("Screener")  # Layout with TTE Screener V2 indicator

    for batch in batches:
        # Input symbols into screener (same category per batch)
        browser.open_indicator_settings()
        for i, symbol in enumerate(batch):
            browser.set_symbol_input(f"s{i+1:02d}", symbol)
        browser.close_indicator_settings()

        # Create webhook alert
        browser.click_indicator()  # Select it
        browser.create_webhook_alert(
            webhook_url="https://stockbuddy.co/api/tte/combo",
            condition="Any alert() function call"
        )

    print(f"Created {len(batches)} alerts covering {total} symbols")
```

### Maintenance Loop (Dual Timers)

```python
# Pseudocode for the dual-timer maintenance loop (V2)
def run_maintenance(browser, config):
    snapshot_worker = SnapshotWorker(browser, config) if config.snapshot_enabled else None

    while not shutdown_event.is_set():
        maintenance_due = (now - last_maintenance) >= 150  # 2.5 minutes

        # Maintenance has priority (same browser, can't run concurrently)
        if maintenance_due:
            browser.refresh_page()
            browser.restart_inactive_alerts()
            browser.clear_alert_log()

        # Snapshots run only when maintenance isn't running
        if snapshot_worker and (now - last_snapshot) >= 60 and not maintenance_due:
            snapshot_worker.process_pending_snapshots()

        shutdown_event.wait(timeout=60)  # Interruptible sleep
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
| `Pine Script Code/Trade Drawer V2.txt` | Trade Drawer V2 indicator (NWE bands + trade levels) for chart snapshots |

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
- Evaluates the screener on every 45-second bar close (`alert.freq_once_per_bar_close`)
- Fires webhook every bar close — staleness check excludes symbols with no recent data

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
https://stockbuddy.co/api/tte/combo
```

### JSON Payload Structure (V2 Compact Format)

> See the full V2 payload spec at the top of this document.

```json
{
  "ts": 1707264000000,
  "s": [{
    "sym": "GBPAUD", "c": 1.985,
    "nwe": [{"z": "la", "t": "bull", "tf": "1H", "ots": 1707264000}],
    "ob": [{"zt": "OB", "st": "un", "t": "bull", "zh": 1.99, "zl": 1.97, "tf": "H4", "zts": 1707260400, "ots": 1707264000}],
    "b": [{"e": 1.98, "sl": 1.975, "tp": 1.99, "et": 1707260000, "l": "LTF", "ntf": "1H", "otf": "H4"}, null],
    "se": [null, null]
  }]
}
```

**Key legend**: `ts`=timestamp, `s`=symbols, `sym`=symbol, `c`=close, `nwe`=NWE signals, `ob`=OB/FVG signals, `b`=buy setups [LTF, HTF], `se`=sell setups [LTF, HTF], `e`=entry, `sl`=stopLoss, `tp`=takeProfit, `et`=entryTime, `l`=label, `ntf`=nweTf, `otf`=obTf

**Key rules**:
- Both symbols included when conditions align (session.ismarket guard)
- `b` and `se` arrays have fixed slots: index 0 = LTF, index 1 = HTF
- `null` in a slot means no setup conditions align for that type
- Non-null = Stock Buddy checks DB for dedup, creates setup if new
- Divergence removed in V2 — no `divergence` field

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

> **V2**: Both symbols in an alert fire on every bar close. Stock Buddy receives setup data + signals together.

### Decisions Made (V2)

- **Payload**: Both alert symbols are included on every bar close (unless stale).
- **Signal + setup state**: NWE signals, OB signals, and setup data (buy/sell, LTF/HTF) all in one payload.
- **Divergence**: Removed. No longer tracked or sent.
- **Stateless**: Setup slots computed fresh each bar. Stock Buddy handles dedup and exit detection.

### How State Flows (V2)

When a webhook arrives, Stock Buddy upserts the signal + setup state for each included symbol. The V2 payload provides stateless setup data on every bar — Stock Buddy handles dedup (DB partial unique index) and exit detection (cron every 5 min).

### Volume Estimate (V2 — 45-second timeframe)

With `alert.freq_once_per_bar_close` at 45 seconds:
- ~310 alerts × ~1.3 bars/min × 60 min × market hours ≈ manageable volume
- Actual firing depends on when symbols are active vs stale
- Well within Vercel Pro capacity

### MongoDB Document Structure (V2)

```json
// tte_live_signals collection — one document per symbol (V2 state)
{
  "_id": "GBPAUD",
  "symbol": "GBPAUD",
  "close": 1.985,
  "nwe": [{"z": "la", "t": "bull", "tf": "1H", "ots": 1707264000}],
  "ob": [{"zt": "OB", "st": "un", "t": "bull", "zh": 1.99, "zl": 1.97, "tf": "H4", "zts": 1707260400, "ots": 1707264000}],
  "buy": [{"e": 1.98, "sl": 1.975, "tp": 1.99, "et": 1707260000, "l": "LTF", "ntf": "1H", "otf": "H4", "n": false}, null],
  "sell": [null, null],
  "last_updated": "2026-02-27T12:00:00Z"
}
```

### Frontend Display (V2)

- Grid showing symbols with active positions and/or signals
- Columns: Symbol | Buy positions (LTF/HTF) | Sell positions (LTF/HTF) | NWE | OB/FVG | Last Updated
- Position shows entry, SL, TP, and whether it is new this bar
- `last_updated` shown as relative time

---

## 10. Symbol Coverage

### Overview (V2)

- **Total symbols**: 620 (expandable to ~800)
- **Batch size**: 2 symbols per alert (category-aware pairing)
- **Total batches**: ~310 alerts
- **Full coverage**: All 620 symbols covered by ~310 simultaneously running alerts

### Symbol Categories (V2)

| Category | Symbols | Alerts |
|----------|---------|--------|
| Currencies | 29 | 15 |
| Crypto | 18 | 9 |
| US Stocks | 376 | 188 |
| Indian Stocks | 197 | 99 |
| **Total** | **620** | **~310** |

### Category-Aware Pairing

Symbols are paired within the same asset class so that both symbols in an alert have matching market hours. This prevents one symbol from being "stale" while the other is active, keeping the alert effective. Implemented in `fetch_symbols_by_category()` in `tte/main.py`.

### Important Note

"Rotation" in V2 means the initial setup phase. Once all ~310 alerts are created and running, they continuously monitor their 2 symbols. The setup must be re-run when:
1. **Script updates**: After editing the Pine Script indicator (alerts use a snapshot of the code at creation time)
2. **Symbol list changes**: If symbols are added/removed from MongoDB
3. **Fresh start**: Use `--fresh` flag to delete all alerts and recreate

---

## 11. Error Handling & Resilience

### Pine Script Runtime Errors

- **Problem**: Runtime errors (na arithmetic, array bounds, etc.) silently stop individual alerts
- **Mitigation**:
  - Defensive coding in Pine Script (na checks, validation)
  - TTE Orchestrator periodically detects and restarts stopped alerts
- **Impact**: 2 symbols go unmonitored until alert is restarted

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

- **Problem**: If an alert stops and isn't restarted, its 2 symbols show stale data
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

With V2 `alert.freq_once_per_bar_close` at 45-second timeframe:
- Alerts fire once per 45-second bar close
- ~310 alerts × ~1,920 bars/day (45-second bars during 24h) = manageable volume
- Active symbol filtering (staleness check) further reduces payload size
- **Verdict**: Tested and confirmed working without capacity issues

---

## 13. Constraints & Limitations

| Constraint | Value | Impact |
|------------|-------|--------|
| Symbols per batch | 2 (4 hard limit) | Category-aware pairing for matching market hours |
| `request.security()` per indicator | 40 max (8 used) | 32 calls available for future expansion |
| Total alerts needed | ~310 | One-time setup, single browser sequential |
| Alert snapshot behavior | Code frozen at creation time | Must delete & recreate after script edits |
| Webhook payload size | ~500 bytes - 2 KB | Compact keys keep within TradingView limits |
| Bar close delivery | Every 45-second bar close | Predictable, manageable webhook volume |
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
| Q5 | Alert maintenance frequency | **Every 2.5 minutes (150s)** in V2. Orchestrator runs continuously and calls `restart_inactive_alerts()` on each cycle. This method opens the TradingView alerts settings menu → selects "All" → clicks "Restart all inactive" → confirms. Logs each restart event. |
| Q9 | Alert creation approach | **Single browser, sequential**. Each batch of 3 symbols is processed one at a time in a single headless Chrome instance. Parallel tab approach was evaluated but abandoned in favor of simplicity and reliability. |

### Q5 Detail: Alert Maintenance

- **Frequency**: Every 2.5 minutes / 150s (configurable via `maintenance.interval` in `combo_settings.yaml`)
- **Method**: Reuse `restart_inactive_alerts()` from `tte/main.py`
- **How it works**:
  1. Opens the Alerts tab via `open_alert_tab()`
  2. Clicks the 3-dot settings button (`alerts-settings-button`)
  3. Expands "Show Alerts" section if collapsed
  4. Selects "All" filter to show all alerts
  5. Clicks "Restart all inactive" button
  6. Confirms via the popup dialog ("Yes")
- **Logging**: Each restart cycle logs whether inactive alerts were found and restarted
- **Runs continuously**: The orchestrator's maintenance loop sleeps 150 seconds (2.5 minutes) between checks (not cron-based)

### Q9 Detail: Single Browser Sequential Creation

- **Approach**: Single headless Chrome browser, processing batches sequentially
- **Why not parallel**: Parallel tab approach was evaluated but abandoned — single browser is simpler, more reliable, and avoids TradingView session limit issues
- **Workflow**:
  1. Open one headless Chrome instance with the "Screener" layout
  2. For each of the ~310 batches: input 2 symbols → create webhook alert → next batch
  3. Progress tracked in `combo_progress.json` for resume capability on interruption
- **Headless mode**: Runs without visible browser window (`headless: true` in combo_settings.yaml)
- **GUI**: `tte_gui.py` (or `dist/TTE.exe`) provides a desktop interface for configuration and execution
