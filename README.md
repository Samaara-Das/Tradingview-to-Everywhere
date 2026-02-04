# TradingView to Everywhere (TTE)

An automated trading signals distribution system that bridges TradingView alerts with multiple social media platforms and databases.

## Overview

TTE monitors TradingView for trading signals, captures and processes them, and distributes formatted trade information to:
- Discord (via webhooks)
- Twitter/X
- Facebook
- MongoDB (for persistence and analytics)

## Features

- **Two Operational Modes**:
  - **Legacy Mode**: Poll-based alert scraping with screenshot capture
  - **Tiered Mode**: Webhook-based two-tier symbol scanning (NWE + OBDIV)
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
python gui.py
```

## Operational Modes

### Legacy Mode (`main.py`)

Uses Selenium to scrape TradingView alerts directly:
1. Monitors TradingView alert log
2. Captures screenshots of trade entries
3. Distributes to social platforms
4. Tracks exits and sends notifications

### Tiered Mode (`tiered_main.py`)

Uses webhook-based alerts for more reliable signal detection:

**Tier 1 (NWE Screener)**: Scans batches of 20 symbols for Nadaraya-Watson Envelope zones on H4/D1 timeframes

**Tier 2 (OBDIV Screener)**: Processes "hot" symbols (those showing NWE zones) through Order Block/FVG + Divergence analysis

## Project Structure

```
tradingview-to-everywhere/
├── main.py                 # Legacy mode entry point
├── tiered_main.py          # Tiered mode entry point
├── gui.py                  # GUI interface
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
    ├── PRD.md              # Technical specification
    ├── SETUP.md            # Setup guide
    ├── API.md              # API reference
    ├── DATABASE.md         # Database schema
    ├── ARCHITECTURE.md     # System architecture
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
```

## Documentation

- [Setup Guide](docs/SETUP.md) - Detailed installation and configuration
- [API Reference](docs/API.md) - Stock Buddy API endpoints and webhooks
- [Database Schema](docs/DATABASE.md) - MongoDB collections and schemas
- [Architecture](docs/ARCHITECTURE.md) - System design and module reference
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
