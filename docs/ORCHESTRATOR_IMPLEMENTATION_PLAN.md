# TTE Python Orchestrator - Implementation Plan

## Overview

The Python Orchestrator manages the tiered screening workflow:
1. **NWE Batch Rotation** - Cycles 1,041 symbols through NWE Screener (20 at a time)
2. **OBDIV Processing** - Processes hot symbols through OBDIV Screener (8 at a time)  
3. **Screenshot Capture** - Captures chart screenshots for completed signals

---

## Current State: ✅ Ready for Configuration

### What Already Exists

| Component | File | Status |
|-----------|------|--------|
| **Orchestrator** | `orchestrator.py` | ✅ Complete (426 lines) |
| **Entry Point** | `tiered_main.py` | ✅ Complete |
| **API Client** | `api_client.py` | ✅ Complete |
| **Config** | `config.py` | ✅ Complete |
| **Selenium Manager** | `selenium_manager.py` | ✅ Complete |
| **Start/Stop Scripts** | `start_prod.sh`, `stop_prod.sh` | ✅ Complete |

### API Endpoints (Stock Buddy)

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `GET /api/tte/symbols/next-batch` | Get next 20 symbols | ✅ Exists |
| `POST /api/tte/symbols/mark-scanned` | Mark symbols scanned | ✅ Exists |
| `GET /api/tte/hot-symbols` | Get pending Tier 2 symbols | ✅ Exists |
| `GET /api/tte/signals` | Get signals | ✅ Exists |
| `PATCH /api/tte/signals/[id]` | Update with screenshot | ✅ Exists |
| `GET /api/health` | Health check | ✅ Exists |

---

## Implementation Steps

### Step 1: Update Environment Configuration (5 min)

Update `.env.production` with your actual values:

```bash
# Stock Buddy API (PRODUCTION - Already deployed!)
STOCK_BUDDY_API_URL=https://stock-buddy-app.vercel.app/api/tte

# Chrome Configuration
CHROME_PROFILE_PATH=C:/Users/dassa/AppData/Local/Google/Chrome/User Data
CHROME_PROFILE_NAME=Default

# TradingView Charts (GET THESE FROM TRADINGVIEW)
NWE_CHART_URL=https://www.tradingview.com/chart/XXXXXXXX/
OBDIV_CHART_URL=https://www.tradingview.com/chart/YYYYYYYY/

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/orchestrator.log

# Timing (seconds)
NWE_BATCH_WAIT=120      # Wait after updating NWE symbols
OBDIV_BATCH_WAIT=30     # Wait after updating OBDIV symbols
SCREENSHOT_WAIT=3       # Wait before taking screenshot
POLL_INTERVAL=60        # Wait between cycles

# Batch Sizes
NWE_BATCH_SIZE=20       # Max 20 (TradingView limit)
OBDIV_BATCH_SIZE=8      # Max 8 (TradingView limit)
SCREENSHOT_BATCH_SIZE=5 # Screenshots per cycle

# Selenium Timeouts (seconds)
SELENIUM_IMPLICIT_WAIT=10
SELENIUM_EXPLICIT_WAIT=30
PAGE_LOAD_TIMEOUT=60

# Retry Configuration
MAX_RETRIES=3
RETRY_DELAY=5
```

---

### Step 2: Get TradingView Chart URLs (10 min)

**IMPORTANT**: You need to save chart layouts in TradingView and get the URLs.

#### For NWE Chart:
1. Open TradingView
2. Add "TTE NWE Screener v2" indicator to chart
3. Configure the 20 symbol inputs
4. Save the chart layout (Ctrl+S or cloud icon)
5. Copy the URL: `https://www.tradingview.com/chart/XXXXXXXX/`

#### For OBDIV Chart:
1. Open TradingView (new tab/layout)
2. Add "TTE OBDIV Screener v2" indicator to chart
3. Configure placeholder symbols (will be updated by orchestrator)
4. Save the chart layout
5. Copy the URL: `https://www.tradingview.com/chart/YYYYYYYY/`

---

### Step 3: Install Python Dependencies (2 min)

```bash
cd "C:\Users\dassa\Work\For Poolsifi\tradingview to everywhere"

# Using pipenv (recommended)
pipenv install

# Or using pip
pip install -r requirements.txt
```

---

### Step 4: Test API Connectivity (5 min)

```bash
cd "C:\Users\dassa\Work\For Poolsifi\tradingview to everywhere"

# Test API connection
python tiered_main.py --test-api
```

Expected output:
```
============================================================
  TTE Tiered Orchestrator
  1000+ Symbol Screening System
============================================================

Testing API connection...
[OK] API is healthy
[OK] System stats: 1041 symbols, 3 signals
[OK] API connection successful
```

---

### Step 5: Test Browser Automation (10 min)

```bash
python tiered_main.py --test-browser
```

This will:
1. Open Chrome with your profile
2. Navigate to TradingView
3. Verify you're logged in
4. Test indicator settings access

---

### Step 6: Single Cycle Test (15 min)

```bash
python tiered_main.py --single-cycle --debug
```

This runs ONE complete cycle:
1. Get next 20 symbols from API
2. Update NWE Screener via Selenium
3. Wait 120 seconds for NWE scan
4. Mark symbols as scanned
5. Get hot symbols (pending Tier 2)
6. Update OBDIV Screener via Selenium
7. Wait 30 seconds for OBDIV scan
8. Capture pending screenshots
9. Exit

---

### Step 7: Production Run

#### Option A: Foreground (for testing)
```bash
python tiered_main.py
```

#### Option B: Background (production)
```bash
# Start
./start_prod.sh

# Check status
./status_prod.sh

# View logs
tail -f logs/orchestrator.log

# Stop
./stop_prod.sh
```

#### Option C: Windows Task Scheduler

Create a scheduled task to run at system startup:
- Program: `python`
- Arguments: `C:\Users\dassa\Work\For Poolsifi\tradingview to everywhere\tiered_main.py`
- Start in: `C:\Users\dassa\Work\For Poolsifi\tradingview to everywhere`

---

## Signal Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR CYCLE                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [00:00] PHASE 1: NWE Batch Rotation                                     │
│          │                                                               │
│          ├─► GET /api/tte/symbols/next-batch?size=20                     │
│          │   Response: {symbols: [...], batch: 5, rotation: 1}           │
│          │                                                               │
│          ├─► Selenium: Open NWE Screener settings                        │
│          │   Update symbol inputs 1-20                                   │
│          │   Click OK                                                    │
│          │                                                               │
│          ├─► Wait 120 seconds (NWE_BATCH_WAIT)                           │
│          │   TradingView processes and fires webhooks                    │
│          │                                                               │
│          └─► POST /api/tte/symbols/mark-scanned                          │
│                                                                          │
│  [02:00] PHASE 2: OBDIV Processing                                       │
│          │                                                               │
│          ├─► GET /api/tte/hot-symbols?status=pending_tier2&limit=8       │
│          │   Response: [{symbol: "GBPAUD", direction: "bullish"}, ...]   │
│          │                                                               │
│          ├─► Selenium: Open OBDIV Screener settings                      │
│          │   Update symbol inputs 1-8                                    │
│          │   Click OK                                                    │
│          │                                                               │
│          └─► Wait 30 seconds (OBDIV_BATCH_WAIT)                          │
│              TradingView processes and fires webhooks                    │
│                                                                          │
│  [02:30] PHASE 3: Screenshot Capture                                     │
│          │                                                               │
│          ├─► GET /api/tte/signals?status=pending_screenshot&limit=5      │
│          │                                                               │
│          ├─► For each signal:                                            │
│          │   Selenium: Navigate to symbol + timeframe                    │
│          │   Selenium: Capture screenshot (Alt+S)                        │
│          │   PATCH /api/tte/signals/{id} with screenshot_url             │
│          │                                                               │
│          └─► Screenshots complete                                        │
│                                                                          │
│  [03:00] CYCLE COMPLETE                                                  │
│          Wait 60 seconds (POLL_INTERVAL)                                 │
│          Loop back to Phase 1                                            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Timing Analysis

### Per Cycle
| Phase | Duration |
|-------|----------|
| NWE Batch | 120s (wait) + 10s (selenium) = **130s** |
| OBDIV Processing | 30s (wait) + 5s (selenium) = **35s** |
| Screenshots | 5 × 10s = **50s** |
| Overhead | **5s** |
| **Total Cycle** | **~220s (3.7 min)** |

### Full Rotation (1,041 symbols)
- Batches needed: 1041 ÷ 20 = **53 batches**
- Time per batch: ~220s
- **Full rotation: ~3.2 hours**

### Signals per Day (Estimate)
- Cycles per day: 24h × 60min ÷ 3.7min = **~390 cycles**
- Full rotations: 390 ÷ 53 = **~7.3 rotations/day**
- Each symbol scanned: **~7 times/day**

---

## Monitoring

### Log Output Example
```
2026-01-29 14:00:00 INFO [orchestrator] ========================================
2026-01-29 14:00:00 INFO [orchestrator] TTE Tiered Orchestrator Starting
2026-01-29 14:00:00 INFO [orchestrator] ========================================
2026-01-29 14:00:01 INFO [orchestrator] API health check passed
2026-01-29 14:00:01 INFO [orchestrator] Symbols: 1041, Signals: 47, Hot: 3
2026-01-29 14:00:01 INFO [orchestrator] ----------------------------------------
2026-01-29 14:00:01 INFO [orchestrator] Starting cycle #1
2026-01-29 14:00:02 INFO [orchestrator] Phase 1: NWE Batch Rotation
2026-01-29 14:00:03 INFO [orchestrator] Batch #6: 20 symbols [EURUSD, GBPUSD, ...]
2026-01-29 14:00:05 INFO [orchestrator] Selenium: Updated NWE Screener symbols
2026-01-29 14:00:05 INFO [orchestrator] Waiting 120s for NWE scan...
2026-01-29 14:02:05 INFO [orchestrator] Phase 2: OBDIV Processing
2026-01-29 14:02:06 INFO [orchestrator] Hot symbols: 3 [GBPAUD, USDJPY, EURJPY]
2026-01-29 14:02:08 INFO [orchestrator] Selenium: Updated OBDIV Screener symbols
2026-01-29 14:02:08 INFO [orchestrator] Waiting 30s for OBDIV scan...
2026-01-29 14:02:38 INFO [orchestrator] Phase 3: Screenshot Capture
2026-01-29 14:02:39 INFO [orchestrator] Pending screenshots: 2
2026-01-29 14:02:50 INFO [orchestrator] Screenshot captured: GBPAUD (signal_123)
2026-01-29 14:03:01 INFO [orchestrator] Screenshot captured: USDJPY (signal_456)
2026-01-29 14:03:01 INFO [orchestrator] Cycle #1 complete (181s)
2026-01-29 14:03:01 INFO [orchestrator] Waiting 60s until next cycle...
```

### Health Check Commands
```bash
# Check if orchestrator is running
ps aux | grep tiered_main.py

# Check recent logs
tail -50 logs/orchestrator.log

# Check for errors
grep ERROR logs/orchestrator.log | tail -20

# Check API stats
curl -s https://stock-buddy-app.vercel.app/api/tte/stats | jq
```

---

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| **Chrome doesn't open** | Check `CHROME_PROFILE_PATH` is correct |
| **TradingView not logged in** | Open Chrome manually, log in to TradingView, close Chrome |
| **Indicator settings not found** | Ensure indicator is added to chart layout |
| **API connection failed** | Check `STOCK_BUDDY_API_URL`, verify internet |
| **Screenshots blank** | Increase `SCREENSHOT_WAIT` time |
| **Symbols not updating** | TradingView UI may have changed; update selectors |

### Debug Mode
```bash
python tiered_main.py --debug
```

This enables:
- Verbose logging
- Screenshots saved locally on error
- Step-by-step execution output

---

## Checklist

### Configuration
- [ ] Update `STOCK_BUDDY_API_URL` in `.env.production`
- [ ] Update `CHROME_PROFILE_PATH` in `.env.production`
- [ ] Get and set `NWE_CHART_URL`
- [ ] Get and set `OBDIV_CHART_URL`

### Testing
- [ ] Run `python tiered_main.py --test-api` → SUCCESS
- [ ] Run `python tiered_main.py --test-browser` → SUCCESS
- [ ] Run `python tiered_main.py --single-cycle` → SUCCESS

### Production
- [ ] Start orchestrator: `./start_prod.sh`
- [ ] Verify logs: `tail -f logs/orchestrator.log`
- [ ] Check dashboard for new signals

---

## Summary

**Estimated Setup Time: 45-60 minutes**

1. **Config update**: 5 min
2. **Get TradingView URLs**: 10 min
3. **Install dependencies**: 2 min
4. **Test API**: 5 min
5. **Test browser**: 10 min
6. **Single cycle test**: 15 min
7. **Production start**: 5 min

**You're ready to begin!** Start with Step 1.
