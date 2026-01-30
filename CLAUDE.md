# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TradingView to Everywhere (TTE) is an automated trading signals distribution system that bridges TradingView alerts with multiple platforms. The project has two operational modes:

1. **Legacy Mode**: Alert-based system using Selenium to capture TradingView alerts and distribute to Discord, Twitter/X, Facebook, and Firebase Firestore.

2. **Tiered Screener Mode** (Active/Primary): Webhook-based multi-symbol screening system with Stock Buddy dashboard integration for scalable signal detection.

## Current System Status (Updated January 29, 2026)

| Component | Status | URL/Location |
|-----------|--------|--------------|
| Stock Buddy API | ✅ Live | https://stock-buddy-app.vercel.app/api/tte |
| TTE Dashboard | ✅ Live | https://stock-buddy-app.vercel.app/tte |
| NWE Webhook | ✅ Configured | https://stock-buddy-app.vercel.app/api/tte/nwe |
| OBDIV Webhook | ✅ Configured | https://stock-buddy-app.vercel.app/api/tte/obdiv |
| TradingView Alerts | ✅ Configured | Pine Scripts added, alerts active |
| Symbols Database | ✅ Seeded | **1000+ symbols** in MongoDB |
| Python Orchestrator | ⏳ Ready | Not yet started |

## Tiered Screener Architecture

### The Problem

Pine Script has a hard limit of **40 `request.security()` calls** per script (64 with Ultimate plan). A full screener with NWE + OB/FVG + Divergence uses ~3 calls per symbol per timeframe. Scaling to 40+ symbols with multiple timeframes is impossible with a single script.

### The Solution: Tiered Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TIER 1: TTE NWE Screener v2 (Pine Script)                                  │
│  - 40 symbols per screener (with rotation), H4 + D1 timeframes              │
│  - Lightweight NWE zone detection only                                       │
│  - Webhook: POST to /api/tte/nwe                                            │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STOCK BUDDY API (Vercel + MongoDB)                                         │
│  Base URL: https://stock-buddy-app.vercel.app/api/tte                       │
│                                                                             │
│  /api/tte/nwe         → Receives NWE webhooks, adds to hot_list            │
│  /api/tte/obdiv       → Receives OBDIV webhooks, creates signals           │
│  /api/tte/signals     → Returns signals for dashboard                      │
│  /api/tte/hot-symbols → Returns symbols pending Tier 2 check               │
│  /api/tte/stats       → Returns system statistics                          │
│  /api/tte/symbols/next-batch → Returns next batch for rotation             │
│  /api/tte/symbols/mark-scanned → Marks batch as scanned                    │
│  /api/health          → Health check endpoint                               │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PYTHON ORCHESTRATOR (This Module - Local Machine)                          │
│  Entry point: python tiered_main.py                                         │
│                                                                             │
│  Phase 1: NWE Batch Rotation                                                │
│  - GET /api/tte/symbols/next-batch                                          │
│  - Update NWE Screener watchlist via Selenium                               │
│  - POST /api/tte/symbols/mark-scanned                                       │
│                                                                             │
│  Phase 2: OBDIV Processing                                                  │
│  - GET /api/tte/hot-symbols (pending_tier2)                                 │
│  - Update OBDIV Screener watchlist via Selenium                             │
│  - Wait for webhooks to fire                                                │
│                                                                             │
│  Phase 3: Screenshot Capture                                                │
│  - GET /api/tte/signals?status=pending_screenshot                           │
│  - Navigate to chart, capture screenshot                                    │
│  - PATCH /api/tte/signals/{id} with screenshot URL                          │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  TIER 2: TTE OBDIV Screener v2 (Pine Script)                                │
│  - 8-10 symbols (dynamically set by orchestrator)                           │
│  - Checks OB/FVG + Divergence (NWE removed for efficiency)                  │
│  - Reports BOTH bullish and bearish findings                                │
│  - Webhook: POST to /api/tte/obdiv                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Signal Levels

- **Level 1**: NWE zone entry only (H4 or D1)
- **Level 2**: NWE + OB/FVG overlap (H4, D1, or W1)
- **Level 3**: NWE + OB/FVG + Divergence (H4 or D1)

### Pine Script Screeners

| File | Purpose | Symbols | Timeframes | request.security() |
|------|---------|---------|------------|-------------------|
| `TTE NWE Screener v2.txt` | Tier 1 - NWE zone detection | 40 (rotation) | H4, D1 | 80 |
| `TTE OBDIV Screener v2.txt` | Tier 2 - OB/DIV detection | 8-10 | H4, D1, W1 | 24-30 |
| `TTE Screener.txt` | Legacy full screener | 8 | H4, D1, W1 | 24 |

### Webhook Payload Formats

**Tier 1 (NWE → /api/tte/nwe):**
```json
{"tier":"nwe","symbol":"GBPAUD","direction":"bullish","timeframes":["H4","D1"],"timestamp":1672531200}
```

**Tier 2 (OBDIV → /api/tte/obdiv):**
```json
{"tier":"obdiv","symbol":"GBPAUD","bull_ob":{"found":true,"tf":"W1","type":"OB","high":1.055,"low":1.050},"bull_div":{"found":true,"tf":"H4","type":"Logic2"},"bear_ob":{"found":false},"bear_div":{"found":false},"timestamp":1672531200}
```

### Symbol Priorities (1000+ Total)

| Priority | Count | Scan Frequency | Categories |
|----------|-------|----------------|------------|
| A | ~100 | Every batch | Major FX, Top Crypto, Major Indices |
| B | ~300 | Every 3rd batch | Minor FX, Mid-cap Stocks |
| C | ~600 | Every 10th batch | Small-cap, Less liquid |

**Symbol Categories:**
- Currencies (FX): 30
- Crypto: 19
- Indices: 8
- Indian Stocks (NSE): 500+
- US Stocks: 400+

## Commands

```bash
# Activate virtual environment
pipenv shell

# Install dependencies
pipenv install
# OR
pip install -r requirements.txt

# Run tiered orchestrator (PRIMARY)
python tiered_main.py

# Orchestrator test commands
python tiered_main.py --validate      # Check configuration
python tiered_main.py --test-api      # Test API connection
python tiered_main.py --test-browser  # Test Chrome automation
python tiered_main.py --stats         # Show current statistics
python tiered_main.py --single-cycle  # Run one test cycle
python tiered_main.py --init          # Initialize rotation state

# Legacy commands (secondary)
python main.py      # Run legacy alert system
python gui.py       # Run with GUI

# Test Firebase connection
python database/test_firebase.py
```

## Production URLs

| Endpoint | URL |
|----------|-----|
| Dashboard | https://stock-buddy-app.vercel.app/tte |
| Health | https://stock-buddy-app.vercel.app/api/health |
| Stats | https://stock-buddy-app.vercel.app/api/tte/stats |
| NWE Webhook | https://stock-buddy-app.vercel.app/api/tte/nwe |
| OBDIV Webhook | https://stock-buddy-app.vercel.app/api/tte/obdiv |
| Signals | https://stock-buddy-app.vercel.app/api/tte/signals |
| Hot Symbols | https://stock-buddy-app.vercel.app/api/tte/hot-symbols |

## Project Locations

| Component | Path |
|-----------|------|
| Stock Buddy App (Next.js) | `C:\Users\dassa\Work\Stock-Buddy-App` |
| Python Orchestrator | `C:\Users\dassa\Work\For Poolsifi\tradingview to everywhere` |
| Pine Scripts | `C:\Users\dassa\Work\For Poolsifi\tradingview to everywhere\Pine Script Code` |

## Legacy Architecture

### Data Flow
1. TradingView generates alerts based on Premium Screener indicator
2. TTE captures alert messages via Selenium (`handle_alerts.py`)
3. TTE navigates to relevant chart/timeframe (`open_entry_chart.py`)
4. Trade Drawer indicator draws entry with TP/SL levels
5. Screenshots captured and distributed to Discord, Twitter/X, Facebook
6. Entry stored in Firebase Firestore (`database/firebase_db.py`)
7. Exit monitor (`exits.py`) checks if entries hit TP/SL in last 15 days
8. Exit notifications distributed to all platforms

### Core Modules
- `main.py` - Entry point with main trading loop. Key constants: `SCREENER_SHORT`, `DRAWER_SHORT`, `INTERVAL_MINUTES`, `START_FRESH`
- `open_tv.py` - Selenium browser automation. Key constants: `SYMBOL_INPUTS`, `CHART_TIMEFRAME`, `LAYOUT_NAME`
- `handle_alerts.py` - Alert message parsing and entry extraction
- `exits.py` - Monitors Firebase for entries that hit TP/SL targets
- `env.py` - Environment configuration. `PROFILE` (Chrome profile), `COLLECTION` (Firestore collection name)

### Database
Uses Firebase Firestore (migrated from MongoDB). Collection name configured in `env.py` as `COLLECTION`.

Document schema:
- `direction`, `symbol`, `timeframe`, `category`
- `entryPrice`, `slPrice`, `tp1Price`, `tp2Price`, `tp3Price`
- `tvEntrySnapshot`, `pngEntrySnapshot`, `tvExitSnapshot`, `pngExitSnapshot`
- `unixTime`, `content`
- `isSlHit`, `isTp1Hit`, `isTp2Hit`, `isTp3Hit`

### Social Distribution (`send_to_socials/`)
- `discord.py` - Webhook-based posting to category-specific channels
- `twitter.py` - X API integration
- `_facebook.py` - Facebook posting (prefixed with `_` when inactive)

## Configuration

### Required Environment Variables

**For Tiered Mode (Primary):**
```env
STOCK_BUDDY_API_URL=https://stock-buddy-app.vercel.app/api/tte
NWE_CHART_URL=https://www.tradingview.com/chart/YOUR_NWE_CHART/
OBDIV_CHART_URL=https://www.tradingview.com/chart/YOUR_OBDIV_CHART/
NWE_BATCH_SIZE=40
OBDIV_BATCH_SIZE=10
NWE_BATCH_WAIT=60
OBDIV_BATCH_WAIT=30
```

**For Legacy Mode:**
- `CHROME_PROFILES_PATH` - Path to Chrome user data folder
- `TRADINGVIEW_EMAIL` / `TRADINGVIEW_PASSWORD` - TradingView login (2FA must be disabled, no linked social accounts)
- `FIREBASE_PROJECT_ID` / `FIREBASE_CREDENTIALS_PATH` - Firebase authentication
- Discord webhook URLs and Twitter API keys in `.env` file

### TradingView Setup

**For Tiered Mode (Primary):**
- Saved layout with TTE NWE Screener v2 (Tier 1)
- Saved layout with TTE OBDIV Screener v2 (Tier 2)
- Alert configured with webhook URL: `https://stock-buddy-app.vercel.app/api/tte/nwe` (Tier 1)
- Alert configured with webhook URL: `https://stock-buddy-app.vercel.app/api/tte/obdiv` (Tier 2)
- Alert message must be: `{{alert.message}}`

**For Legacy Mode:**
- Saved layout "Screener" with Premium Screener + Trade Drawer indicators
- Saved layout "Exits" with Get Exits indicator
- Both indicators must be starred/favorited
- Alerts log must be visible (not minimized)

### Symbol Categories
Configured in `resources/symbol_settings.py`: Currencies, US Stocks, Indian Stocks, Crypto. Each category has separate Discord channels for entries, exits, and before-and-after.

## File Structure

```
Pine Script Code/
├── TTE NWE Screener v2.txt      # Tier 1 - NWE zone detection (40 symbols rotation)
├── TTE OBDIV Screener v2.txt    # Tier 2 - OB/DIV detection (8-10 symbols)
├── TTE Screener.txt             # Legacy full screener
├── TTE NWE Screener.txt         # Original NWE screener (reference)
├── Kernel AO Divergence.txt     # Original divergence indicator
├── Nadaraya Watson Envelope.txt # Original NWE indicator
└── OB & FVG.txt                 # Original OB/FVG indicator

docs/
├── ORCHESTRATOR_GUIDE.md        # Detailed orchestrator documentation
├── API_DOCUMENTATION.md         # API endpoint reference
├── ENVIRONMENT_CONFIG.md        # Environment setup
├── DEPLOYMENT_RUNBOOK.md        # Deployment procedures
└── adr/                         # Architecture Decision Records
    ├── 001-tiered-architecture.md
    ├── 002-webhook-vs-scraping.md
    └── 003-remove-nwe-from-tier2.md

Key Python Files:
├── tiered_main.py               # Entry point for tiered orchestrator
├── orchestrator.py              # Main orchestration logic (production)
├── tiered_orchestrator.py       # Legacy orchestrator (local state)
├── api_client.py                # Stock Buddy API client
├── selenium_manager.py          # Browser automation
├── config.py                    # Configuration management
└── symbol_settings.py           # Symbol definitions
```

## Critical Notes

- Never interact with the Selenium-controlled browser manually
- Close all Chrome browsers before running
- `START_FRESH=True` deletes all existing alerts and creates new ones
- `START_FRESH=False` keeps existing alerts and reads unread messages
- Browser refreshes every `INTERVAL_MINUTES` (default: 10) to prevent freezing
- Log file: `app_log.log` (auto-trimmed to prevent overflow)
- Pine Script limit: 40 `request.security()` calls max (64 with Ultimate)

## Known Issues & Solutions

### Pine Script Conditional Execution Bug
**Problem**: Cannot optimize by conditionally skipping indicator calculations inside `if` blocks.
**Cause**: Pine Script history buffer fragmentation - functions using `[]` operators get inconsistent history when called conditionally.
**Solution**: Use external orchestration (tiered architecture) instead of conditional Pine Script execution.

### NWE Zone Detection
**Correct Zone Structure:**
```
upper_far   ─────  (highest red line)
              UPPER FAR ZONE
upper_avg   ─────  (middle red line)
              UPPER AVG ZONE
upper_near  ─────  (bottom red line)
yhat        ═════  (regression line - NOT a zone boundary)
lower_near  ─────  (top green line)
              LOWER AVG ZONE
lower_avg   ─────  (middle green line)
              LOWER FAR ZONE
lower_far   ─────  (lowest green line)
```

## Lessons Learned

When making mistakes, ALWAYS document them in `AGENTS.md` to prevent repetition.

## Pine Script

Pine Script guidelines are in `.claude/skills/pinescript/`. The skill auto-applies when working on Pine Script tasks.

Unless explicitly stated, use shift 0 when working in Pine Script.

### Key Functions Reference

**NWE Screener v2:**
- `calcNWE()` - Returns 7 values: yhat, upper_near, upper_far, upper_avg, lower_near, lower_far, lower_avg
- `checkNWEZone()` - Returns NWE zone overlap status for bullish/bearish

**OBDIV Screener v2:**
- `scanOBRange()` - Returns 12 values for OB/FVG detection
- `calcKernelOsc()` - Kernel AO oscillator (fast - slow)
- `detectBullishDiv()` / `detectBearishDiv()` - Logic 2 divergence
- `detectBullishIntDiv()` / `detectBearishIntDiv()` - Internal divergence
- `checkOBDivOnly()` - Combined OB + DIV scan (16 values)
- `checkOBOnly()` - OB scan only for W1 timeframe (12 values)
