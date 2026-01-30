# TTE Python Orchestrator Guide

**Last Updated:** January 29, 2026
**Status:** Ready for Testing

## Overview

The Python Orchestrator is the bridge between TradingView screeners and the Stock Buddy dashboard. It manages three key workflows:

1. **NWE Symbol Batch Rotation** - Cycles through **1000+ symbols** in batches of 40
2. **OBDIV Hot Symbol Processing** - Processes NWE-triggered symbols through Tier 2
3. **Screenshot Capture** - Captures chart screenshots for completed signals

---

## Current System Status

| Component | Status | Details |
|-----------|--------|---------|
| Stock Buddy API | ✅ Live | https://stock-buddy-app.vercel.app/api/tte |
| TTE Dashboard | ✅ Live | https://stock-buddy-app.vercel.app/tte |
| TradingView Alerts | ✅ Configured | NWE + OBDIV webhooks active |
| Symbols Database | ✅ Seeded | **1000+ symbols** in MongoDB |
| Python Orchestrator | ⏳ Ready | Not yet started |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TIERED ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 1: NWE Screener v2 (TradingView - Pine Script)                │   │
│  │  - 40 symbols per batch (rotation), H4 + D1 timeframes              │   │
│  │  - Fires webhook when price enters NWE zone                         │   │
│  │  - Webhook URL: POST /api/tte/nwe                                   │   │
│  └───────────────────────────────────┬─────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STOCK BUDDY API (Vercel + MongoDB)                                 │   │
│  │  Base URL: https://stock-buddy-app.vercel.app/api/tte               │   │
│  │                                                                     │   │
│  │  /api/tte/nwe              → Receives NWE webhooks, adds to hot_list│   │
│  │  /api/tte/obdiv            → Receives OBDIV webhooks, creates signals│  │
│  │  /api/tte/hot-symbols      → Returns symbols pending Tier 2 check   │   │
│  │  /api/tte/signals          → Returns signals for dashboard          │   │
│  │  /api/tte/stats            → System statistics                      │   │
│  │  /api/tte/symbols/next-batch    → Returns next rotation batch       │   │
│  │  /api/tte/symbols/mark-scanned  → Marks batch as scanned            │   │
│  │  /api/health               → Health check                           │   │
│  └───────────────────────────────────┬─────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PYTHON ORCHESTRATOR (This Module - Local Machine)                  │   │
│  │  Entry point: python tiered_main.py                                 │   │
│  │                                                                     │   │
│  │  Phase 1: NWE Batch Rotation                                        │   │
│  │  - GET /api/tte/symbols/next-batch                                  │   │
│  │  - Update NWE Screener watchlist via Selenium                       │   │
│  │  - Wait for screener to scan (NWE_BATCH_WAIT seconds)               │   │
│  │  - POST /api/tte/symbols/mark-scanned                               │   │
│  │                                                                     │   │
│  │  Phase 2: OBDIV Processing                                          │   │
│  │  - GET /api/tte/hot-symbols (pending_tier2)                         │   │
│  │  - Update OBDIV Screener watchlist via Selenium                     │   │
│  │  - Wait for webhooks to fire (OBDIV_BATCH_WAIT seconds)             │   │
│  │                                                                     │   │
│  │  Phase 3: Screenshot Capture                                        │   │
│  │  - GET /api/tte/signals?status=pending_screenshot                   │   │
│  │  - Navigate to chart, capture screenshot                            │   │
│  │  - PATCH /api/tte/signals/{id} with screenshot URL                  │   │
│  └───────────────────────────────────┬─────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 2: OBDIV Screener v2 (TradingView - Pine Script)              │   │
│  │  - 8-10 symbols (dynamically set by orchestrator)                   │   │
│  │  - Checks OB/FVG + Divergence (NWE removed for efficiency)          │   │
│  │  - Reports BOTH bullish and bearish findings                        │   │
│  │  - Webhook URL: POST /api/tte/obdiv                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
1. Python 3.8+
2. Chrome browser installed
3. ChromeDriver (handled by selenium-manager)
4. TradingView account (logged in via Chrome profile)

### Setup Steps

```bash
# 1. Navigate to orchestrator directory
cd "C:\Users\dassa\Work\For Poolsifi\tradingview to everywhere"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment (create/edit .env file)
# See Configuration section below

# 4. Validate configuration
python tiered_main.py --validate

# 5. Test API connection
python tiered_main.py --test-api

# 6. Test browser automation
python tiered_main.py --test-browser

# 7. Run single test cycle
python tiered_main.py --single-cycle

# 8. Run continuously
python tiered_main.py
```

---

## Configuration

### Environment Variables (`.env`)

```bash
# Stock Buddy API Configuration
STOCK_BUDDY_API_URL=https://stock-buddy-app.vercel.app/api/tte

# TradingView Chart URLs (your saved charts with indicators)
NWE_CHART_URL=https://www.tradingview.com/chart/YOUR_NWE_CHART_ID/
OBDIV_CHART_URL=https://www.tradingview.com/chart/YOUR_OBDIV_CHART_ID/

# Batch Configuration
NWE_BATCH_SIZE=40        # Symbols per NWE batch
OBDIV_BATCH_SIZE=10      # Symbols per OBDIV batch  
SCREENSHOT_BATCH_SIZE=5  # Screenshots per cycle

# Timing (seconds)
NWE_BATCH_WAIT=60        # Wait after updating NWE symbols
OBDIV_BATCH_WAIT=30      # Wait after updating OBDIV symbols
CYCLE_DELAY=300          # Wait between cycles (5 minutes)

# Chrome Configuration
CHROME_PROFILE_PATH=C:/Users/YourName/AppData/Local/Google/Chrome/User Data
CHROME_PROFILE_NAME=Default

# Selenium Timeouts
SELENIUM_IMPLICIT_WAIT=15
SELENIUM_EXPLICIT_WAIT=45
PAGE_LOAD_TIMEOUT=90
```

### Config Class (`config.py`)

The `Config` class validates and loads all configuration:

```python
from config import Config

# Access configuration
print(Config.STOCK_BUDDY_API_URL)  # https://stock-buddy-app.vercel.app/api/tte
print(Config.NWE_BATCH_SIZE)       # 40
print(Config.NWE_CHART_URL)        # Your TradingView chart URL

# Validate configuration
Config.validate(strict=True)  # Raises ValueError if invalid
```

---

## Command Line Interface

### Available Commands

```bash
# Validate configuration
python tiered_main.py --validate

# Test API connection
python tiered_main.py --test-api

# Test browser automation  
python tiered_main.py --test-browser

# View current statistics
python tiered_main.py --stats

# Initialize rotation state (run once)
python tiered_main.py --init

# Force reinitialize (clears existing state)
python tiered_main.py --init-force

# Run single test cycle
python tiered_main.py --single-cycle

# Run continuously (production)
python tiered_main.py

# Enable debug logging
python tiered_main.py --debug
```

### Expected Output

**--validate:**
```
Validating configuration...
[OK] Configuration is valid
```

**--test-api:**
```
Testing API connection...
[OK] Connected to API at https://stock-buddy-app.vercel.app/api/tte
Fetching system stats...
  Signals today: 5
  Total signals: 47
  Hot list pending: 2
  Current batch: #6
  Current rotation: #1
[OK] API test passed
```

**--test-browser:**
```
Testing browser automation...
  Launching Chrome...
  [OK] Chrome launched successfully
  Navigating to TradingView...
  [OK] Navigation successful
[OK] Browser test passed
Press Enter to close browser...
```

**--stats:**
```
--- Signal Statistics ---
  Today:     5
  This week: 25
  This month: 47
  Total:     47
  Pending screenshots: 3

--- By Level ---
  Level 1 (NWE only):    20
  Level 2 (NWE + OB):    15
  Level 3 (NWE + OB + DIV): 12

--- By Direction ---
  Bullish: 30
  Bearish: 17

--- Hot List ---
  Pending Tier 2: 2
  Avg age: 15 minutes

--- Symbol Rotation ---
  Current batch: #6
  Current rotation: #1
  Progress: 30.5%
  Scanned: 142/466
```

---

## Orchestrator Workflow

### Phase 1: NWE Batch Rotation

1. **GET** `/api/tte/symbols/next-batch?size=40`
   - Returns next batch of symbols based on rotation state
   - Priority A symbols included in every batch
   - Priority B symbols every 3rd batch
   - Priority C symbols every 10th batch

2. **Selenium**: Navigate to NWE chart and update watchlist
   - Open indicator settings
   - Update symbol inputs
   - Apply changes

3. **Wait** `NWE_BATCH_WAIT` seconds for screener to scan

4. **POST** `/api/tte/symbols/mark-scanned`
   - Marks symbols as scanned
   - Advances batch counter

### Phase 2: OBDIV Processing

1. **GET** `/api/tte/hot-symbols?limit=10`
   - Returns symbols with `status: "pending_tier2"`
   - These are symbols where NWE triggered

2. **Selenium**: Navigate to OBDIV chart and update watchlist
   - Open indicator settings
   - Update symbol inputs with hot symbols
   - Apply changes

3. **Wait** `OBDIV_BATCH_WAIT` seconds for screener to scan
   - OBDIV screener will fire webhooks to `/api/tte/obdiv`
   - API creates signals based on OB/DIV findings

### Phase 3: Screenshot Capture

1. **GET** `/api/tte/signals?status=pending_screenshot&limit=5`
   - Returns signals needing screenshots

2. **For each signal:**
   - Navigate to symbol chart
   - Change to appropriate timeframe (ob_tf or H4)
   - Wait for chart to load
   - Take TradingView snapshot
   - **PATCH** `/api/tte/signals/{id}` with screenshot URL

3. **Repeat** for all pending signals in batch

### Cycle Timing

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Cycle                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Phase 1: NWE Batch (~2 minutes)                           │
│  ├─ Fetch next batch (1s)                                  │
│  ├─ Update watchlist (5s)                                  │
│  ├─ Wait for scan (60s)                                    │
│  └─ Mark scanned (1s)                                      │
│                                                             │
│  Phase 2: OBDIV (~1 minute)                                │
│  ├─ Fetch hot symbols (1s)                                 │
│  ├─ Update watchlist (5s)                                  │
│  └─ Wait for scan (30s)                                    │
│                                                             │
│  Phase 3: Screenshots (~2-5 minutes, variable)             │
│  ├─ Fetch pending (1s)                                     │
│  └─ For each signal:                                       │
│      ├─ Navigate to chart (3s)                             │
│      ├─ Take screenshot (2s)                               │
│      └─ Update API (1s)                                    │
│                                                             │
│  Wait CYCLE_DELAY (300s = 5 minutes)                       │
│                                                             │
│  Total cycle: ~8-10 minutes                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Files

| File | Purpose |
|------|---------|
| `tiered_main.py` | Entry point with CLI commands |
| `orchestrator.py` | Main orchestration logic (production) |
| `tiered_orchestrator.py` | Legacy orchestrator (local state) |
| `api_client.py` | Stock Buddy API client |
| `selenium_manager.py` | Browser automation |
| `config.py` | Configuration management |
| `symbol_settings.py` | Symbol definitions (466 symbols) |
| `logger_setup.py` | Logging configuration |

---

## API Client Usage

```python
from api_client import StockBuddyAPIClient

# Create client
client = StockBuddyAPIClient()

# Health check
if client.health_check():
    print("API is healthy")

# Get statistics
stats = client.get_stats()
print(f"Total signals: {stats['signals']['total']}")
print(f"Hot list pending: {stats['hot_list']['pending']}")

# Get next batch for NWE rotation
batch = client.get_next_symbol_batch(size=40)
symbols = [s['symbol'] for s in batch.get('batch', [])]
print(f"Next batch: {len(symbols)} symbols")

# Mark symbols as scanned
client.mark_symbols_scanned(symbols)

# Get hot symbols for OBDIV
hot_symbols = client.get_hot_symbols(limit=10)
print(f"Hot symbols: {[s['symbol'] for s in hot_symbols]}")

# Get pending screenshots
pending = client.get_pending_screenshots(limit=5)
for signal in pending:
    print(f"Pending: {signal['symbol']} Level {signal['level']}")

# Update signal with screenshot
client.update_signal_screenshot(signal_id, screenshot_url)

# Close client
client.close()
```

---

## Selenium Automation

### Browser Setup

The `SeleniumManager` handles Chrome automation:

```python
from selenium_manager import SeleniumManager

# Create browser manager
browser = SeleniumManager()

# Get WebDriver
driver = browser.get_driver()

# Navigate to chart
browser.navigate_to_chart("https://www.tradingview.com/chart/ABC123/")

# Close browser
browser.close()
```

### TradingView Watchlist Update

The orchestrator updates TradingView watchlist to change which symbols are scanned:

1. Opens indicator settings (double-click on indicator legend)
2. Updates symbol input fields
3. Clicks OK to apply

This triggers the screener to recalculate for new symbols.

---

## Signal Levels

| Level | Conditions | Quality |
|-------|------------|---------|
| 1 | NWE zone entry only | Weakest |
| 2 | NWE + OB/FVG overlap | Medium |
| 3 | NWE + OB + Divergence | Strongest |

---

## Monitoring & Logs

### Log Location

```
logs/orchestrator.log
```

### Log Format

```
2026-01-29 14:00:00 INFO [orchestrator] Starting cycle #1
2026-01-29 14:00:01 INFO [orchestrator] Phase 1: NWE Batch Rotation
2026-01-29 14:00:02 INFO [orchestrator] Batch #6: 40 symbols (30.5% progress)
2026-01-29 14:01:02 INFO [orchestrator] Batch complete, marking scanned
2026-01-29 14:01:03 INFO [orchestrator] Phase 2: OBDIV Processing
2026-01-29 14:01:04 INFO [orchestrator] Processing 3 hot symbols
2026-01-29 14:01:34 INFO [orchestrator] OBDIV complete
2026-01-29 14:01:35 INFO [orchestrator] Phase 3: Screenshots
2026-01-29 14:01:36 INFO [orchestrator] Capturing 2 screenshots
2026-01-29 14:01:45 INFO [orchestrator] Screenshot complete: GBPAUD
2026-01-29 14:01:54 INFO [orchestrator] Screenshot complete: EURUSD
2026-01-29 14:01:55 INFO [orchestrator] Cycle #1 complete (115s)
```

### Health Checks

```bash
# Check API health
curl https://stock-buddy-app.vercel.app/api/health

# Check stats
curl https://stock-buddy-app.vercel.app/api/tte/stats

# Check orchestrator process
ps aux | grep tiered_main.py
```

---

## Troubleshooting

### API Connection Issues

| Problem | Solution |
|---------|----------|
| Health check fails | Verify STOCK_BUDDY_API_URL is correct |
| Timeout errors | Check internet connection |
| 404 errors | Ensure using `/api/tte/` prefix |

### Browser Issues

| Problem | Solution |
|---------|----------|
| Chrome doesn't open | Check CHROME_PROFILE_PATH |
| Can't find indicator | Ensure indicator is loaded on saved chart |
| Symbol input not found | TradingView UI may have changed |
| Timeout errors | Increase SELENIUM_EXPLICIT_WAIT |

### Screenshot Issues

| Problem | Solution |
|---------|----------|
| Screenshot not captured | Verify TradingView snapshot works manually |
| Wrong chart | Add more wait time for chart to load |
| Blank screenshot | Increase SCREENSHOT_WAIT time |

---

## Production Scripts

### Start Orchestrator

```bash
# Linux/Mac
./start_prod.sh

# Windows
python tiered_main.py
```

### Check Status

```bash
# Linux/Mac
./status_prod.sh

# Windows - Check process
tasklist | findstr python
```

### Stop Orchestrator

```bash
# Linux/Mac
./stop_prod.sh

# Windows - Ctrl+C or
taskkill /F /IM python.exe
```

---

## Related Documentation

- `CLAUDE.md` - Main project guide
- `docs/API_DOCUMENTATION.md` - Full API reference
- `docs/ENVIRONMENT_CONFIG.md` - Environment setup
- `PRD.md` - Product requirements
- `TECHNICAL_SPEC.md` - Technical specifications
