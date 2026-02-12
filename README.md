# TradingView to Everywhere (TTE)

An automated trading signals distribution system that bridges TradingView alerts with multiple social media platforms and databases.

## Overview

TTE monitors TradingView for trading signals, captures and processes them, and distributes formatted trade information to:
- Discord (via webhooks)
- Twitter/X
- Facebook
- MongoDB (for persistence and analytics)

## Features

- **Three Operational Modes**:
  - **Legacy Mode**: Poll-based alert scraping with screenshot capture
  - **Tiered Mode**: Webhook-based two-tier symbol scanning (NWE + OBDIV)
  - **Combo Mode**: Single-indicator webhook with 338 persistent alerts monitoring ~1,028 symbols
- **Multi-Platform Distribution**: Simultaneous posting to Discord, Twitter, and Facebook
- **Automated Browser Control**: Selenium-based TradingView automation
- **Persistent Storage**: MongoDB integration for signal tracking
- **Exit Monitoring**: Automatic trade exit detection and notification

## Quick Start (5 Minutes)

### Prerequisites

- Python 3.11
- Google Chrome browser
- TradingView account (Premium recommended, 2FA disabled)
- MongoDB Atlas account (or local MongoDB)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd tradingview-to-everywhere

# Install dependencies
pipenv install

# Activate virtual environment
pipenv shell

# Copy environment template and configure
cp .env.example .env
# Edit .env with your credentials
```

### Running

**Legacy Mode** (poll-based alerts):
```bash
python main.py
```

**Tiered Mode** (webhook-based, recommended):
```bash
# Validate configuration first
python tiered_main.py --validate

# Test API connection
python tiered_main.py --test-api

# Run continuously
python tiered_main.py

# Run single cycle (for testing)
python tiered_main.py --single-cycle
```

**GUI Mode**:
```bash
python tte_gui.py
# Or use the standalone executable:
dist\TTE.exe
```

## Operational Modes

### Legacy Mode (`main.py`)

Uses Selenium to scrape TradingView alerts directly:
1. Monitors TradingView alert log
2. Captures screenshots of trade entries
3. Distributes to social platforms
4. Tracks exits and sends notifications


### Critical Notes (legacy mode)

- Never manually interact with the Selenium-controlled browser
- Ensure all Chrome browsers are closed before running
- The Alerts log must be maximized (not minimized) in TradingView
- The application will delete existing alerts when `START_FRESH=True`
- MongoDB symbols must be synced with TradingView alerts


### Tiered Mode (`tiered_main.py`)

Uses webhook-based alerts for more reliable signal detection:

**Tier 1 (NWE Screener)**: Scans batches of 20 symbols for Nadaraya-Watson Envelope zones on H4/D1 timeframes

**Tier 2 (OBDIV Screener)**: Processes "hot" symbols (those showing NWE zones) through Order Block/FVG + Divergence analysis

### Combo Mode (`combo_main.py`)

Uses a single combo screener indicator (NWE + OB/FVG + Divergence) with persistent webhook alerts:

- **338 alerts** monitoring ~1,028 symbols (3 per alert)
- Alerts run continuously on TradingView servers
- Webhooks fire to Stock Buddy API on every signal
- Runs in headless Chrome by default (no visible browser window)
- Maintenance every 5 minutes restarts any inactive alerts

```bash
# Full setup + maintenance
python combo_main.py

# Setup only (create alerts, then exit)
python combo_main.py --setup-only

# Maintenance only (skip setup)
python combo_main.py --maintain-only

# Delete all alerts and start fresh
python combo_main.py --fresh

# Validate configuration
python combo_main.py --validate
```

## Project Structure

```
tradingview-to-everywhere/
├── main.py                 # Legacy mode entry point
├── tiered_main.py          # Tiered mode entry point
├── combo_main.py           # Combo mode entry point
├── combo_config.py         # Combo configuration loader
├── combo_settings.yaml     # Combo mode settings
├── tte_gui.py              # GUI interface
├── dist/TTE.exe            # Standalone GUI executable
├── orchestrator.py         # Tiered workflow orchestrator
├── api_client.py           # Stock Buddy API client
├── config.py               # Configuration management
├── open_tv.py              # Browser automation
├── handle_alerts.py        # Alert processing
├── open_entry_chart.py     # Chart navigation
├── exits.py                # Exit monitoring
├── env.py                  # Environment constants
├── logger_setup.py         # Logging configuration
├── database/
│   └── local_db.py         # MongoDB operations
├── resources/
│   └── symbol_settings.py  # Symbol management
├── send_to_socials/        # Platform distributors
└── docs/
    ├── combo/
    │   ├── ARCHITECTURE.md     # Combo mode architecture
    │   ├── IMPLEMENTATION.md   # Combo implementation (archived)
    │   └── PRD.md              # Combo mode PRD
    ├── legacy/
    │   ├── ARCHITECTURE.md     # Legacy/tiered architecture
    │   ├── PRD.md              # Tiered mode specification
    │   └── SIGNAL-FRESHNESS.md # Signal freshness analysis
    ├── SETUP.md            # Setup guide
    ├── API.md              # API reference
    ├── DATABASE.md         # Database schema
    ├── TROUBLESHOOTING.md  # Common issues
    └── CONTRIBUTING.md     # Contribution guidelines
```

## Configuration

Key environment variables (see [docs/SETUP.md](docs/SETUP.md) for complete list):

```bash
# Chrome
CHROME_PROFILES_PATH=/path/to/chrome/user/data

# TradingView
TRADINGVIEW_EMAIL=your@email.com
TRADINGVIEW_PASSWORD=your_password

# MongoDB
MONGODB_PWD=your_mongodb_password

# Tiered Mode
STOCK_BUDDY_API_URL=https://stock-buddy-app.vercel.app/api/tte
NWE_CHART_URL=https://www.tradingview.com/chart/xxxxx/
OBDIV_CHART_URL=https://www.tradingview.com/chart/yyyyy/

# Combo Mode
COMBO_WEBHOOK_URL=https://stock-buddy-app.vercel.app/api/tte/combo
```

## Documentation

- [Setup Guide](docs/SETUP.md) - Detailed installation and configuration
- [API Reference](docs/API.md) - Stock Buddy API endpoints and webhooks
- [Database Schema](docs/DATABASE.md) - MongoDB collections and schemas
- [Architecture (Legacy)](docs/legacy/ARCHITECTURE.md) - System design and module reference
- [Combo Architecture](docs/combo/ARCHITECTURE.md) - Combo mode design
- [Combo PRD](docs/combo/PRD.md) - Combo mode product requirements
- [Tiered PRD](docs/legacy/PRD.md) - Tiered mode specification
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Contributing](docs/CONTRIBUTING.md) - Development guidelines

## Requirements

- Python 3.11
- Chrome browser (latest)
- TradingView account with:
  - Two-factor authentication disabled
  - No linked social accounts
  - Required layouts and indicators saved

## License

Proprietary - All rights reserved.

## Support

For issues and feature requests, please create an issue in the repository.
