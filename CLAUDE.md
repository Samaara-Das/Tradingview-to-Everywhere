# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TradingView to Everywhere (TTE) is an automated trading signals distribution system that bridges TradingView alerts with multiple social media platforms. It monitors TradingView for trading signals via Selenium browser automation, captures and processes them, and distributes formatted trade information to Discord, Facebook, Twitter/X, and Firebase Firestore.

## Commands

```bash
# Activate virtual environment
pipenv shell

# Install dependencies
pipenv install

# Run the main application (console mode)
python main.py

# Run with GUI
python gui.py

# Test Firebase connection
python database/test_firebase.py
```

## Architecture

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
- `CHROME_PROFILES_PATH` - Path to Chrome user data folder
- `TRADINGVIEW_EMAIL` / `TRADINGVIEW_PASSWORD` - TradingView login (2FA must be disabled, no linked social accounts)
- `FIREBASE_PROJECT_ID` / `FIREBASE_CREDENTIALS_PATH` - Firebase authentication
- Discord webhook URLs and Twitter API keys in `.env` file

### TradingView Setup
- Saved layout "Screener" with Premium Screener + Trade Drawer indicators
- Saved layout "Exits" with Get Exits indicator
- Both indicators must be starred/favorited
- Alerts log must be visible (not minimized)

### Symbol Categories
Configured in `resources/symbol_settings.py`: Currencies, US Stocks, Indian Stocks, Crypto. Each category has separate Discord channels for entries, exits, and before-and-after.

## Critical Notes

- Never interact with the Selenium-controlled browser manually
- Close all Chrome browsers before running
- `START_FRESH=True` deletes all existing alerts and creates new ones
- `START_FRESH=False` keeps existing alerts and reads unread messages
- Browser refreshes every `INTERVAL_MINUTES` (default: 10) to prevent freezing
- Log file: `app_log.log` (auto-trimmed to prevent overflow)

## Lessons Learned

When making mistakes, document them in `AGENTS.md` to prevent repetition.
