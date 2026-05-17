# TradingView to Everywhere (TTE)

An automated trading signals distribution system that bridges TradingView alerts with Stock Buddy API via webhooks.

## Overview

TTE uses Selenium browser automation to create and maintain persistent webhook alerts on TradingView. A stateless combo screener indicator (NWE + OB/FVG setup detection) monitors 620 symbols across ~310 alerts, sending signals and setup data to Stock Buddy API on every 45-second bar close. Exit detection is handled server-side by a Stock Buddy cron job.

## Features

- **Combo Mode V2**: Single-indicator webhook with ~310 persistent alerts monitoring 620 symbols
- **Stateless Setup Detection**: Pine Script detects NWE + OB/FVG alignment; exit detection handled by Stock Buddy cron (every 5 min)
- **Category-Aware Pairing**: Symbols paired within the same asset class (forex/crypto/stocks) for matching market hours
- **Automated Browser Control**: Selenium-based TradingView automation (headless Chrome)
- **Webhook Distribution**: Compact JSON payload fires to Stock Buddy API on every 45-second bar close
- **Alert Maintenance**: Automatic restart of inactive alerts every 2.5 minutes
- **GUI Interface**: Visual interface for configuration and monitoring (`TTE.exe` or `tte_gui.py`)
- **Chart Snapshots**: Asynchronous chart screenshot worker for setup messages in Stock Buddy

## Quick Start

### Prerequisites

- Python 3.11
- Google Chrome browser
- TradingView account (Premium; 2FA optional — set `TRADINGVIEW_TOTP_SECRET` if enabled)
- MongoDB Atlas account (for symbol storage)

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

**CLI**:
```bash
# Validate configuration
python combo_main.py --validate

# Full setup (create all alerts) + maintenance
python combo_main.py

# Delete all alerts and start fresh
python combo_main.py --fresh

# Setup only (create alerts, then exit)
python combo_main.py --setup-only

# Maintenance only (skip setup)
python combo_main.py --maintain-only

# Setup specific symbols only
python combo_main.py --symbols EURUSD,GBPUSD
```

**GUI** (recommended):
```bash
python tte_gui.py
# Or use the standalone executable:
dist\TTE.exe
```

## Project Structure

```
tradingview-to-everywhere/
├── combo_main.py               # Backward-compatible entry point (shim)
├── combo_settings.yaml         # All combo mode settings
├── tte_gui.py                  # GUI interface
├── dist/TTE.exe                # Standalone GUI executable
├── tte/                        # Main package
│   ├── __init__.py             # Re-exports: Browser, ComboConfig
│   ├── main.py                 # Entry point (orchestrator)
│   ├── config.py               # Configuration loader + PROFILE
│   ├── log.py                  # Logger setup
│   ├── browser/                # Browser automation sub-package
│   │   ├── __init__.py         # Re-exports: Browser, OpenChart, Utils
│   │   ├── tradingview.py      # TradingView automation (Selenium)
│   │   ├── chart.py            # Chart navigation & snapshots
│   │   └── helpers.py          # Selenium utility functions
│   ├── snapshot_worker.py      # Chart snapshot polling & orchestration
│   └── data/                   # Data access layer
│       ├── __init__.py         # Re-exports: get_symbols, get_symbol_categories
│       └── symbols.py          # MongoDB symbol fetching
├── docs/
│   ├── combo/
│   │   ├── ARCHITECTURE.md     # Combo mode architecture
│   │   └── PRD.md              # Combo mode PRD
│   ├── SETUP.md                # Setup guide
│   ├── API.md                  # Stock Buddy API reference
│   ├── DATABASE.md             # Database schema
│   ├── TROUBLESHOOTING.md      # Common issues
│   └── CONTRIBUTING.md         # Contribution guidelines
└── Pine Script Code/           # TradingView indicator source
```

## Configuration

### Settings (`combo_settings.yaml`)

All options are configured in `combo_settings.yaml`. The GUI provides a visual editor for this file.

Key settings:
- `chart.layout_name` — TradingView layout name (default: `"Screener"`)
- `chart.chart_timeframe` — Chart timeframe (default: `"45 seconds"`)
- `chart.headless` — Run Chrome without visible window (default: `true`)
- `alerts.batch_size` — Symbols per alert (default: `2`, hard limit: `4`)
- `maintenance.interval` — Seconds between restart cycles (default: `150`)
- `snapshot.enabled` — Enable chart snapshot worker (default: `true`)

### Environment Variables

```bash
# Chrome
CHROME_PROFILES_PATH=C:\Users\<YourUsername>\AppData\Local\Google\Chrome\User Data

# TradingView
TRADINGVIEW_EMAIL=your@email.com
TRADINGVIEW_PASSWORD=your_password
# Optional: base32 TOTP secret for auto-2FA (set if TV enables 2FA on the account)
# TRADINGVIEW_TOTP_SECRET=your_base32_secret

# MongoDB
MONGODB_PWD=your_mongodb_password

# Webhook
COMBO_WEBHOOK_URL=https://stockbuddy.co/api/tte/combo
```

## Documentation

- [Setup Guide](docs/SETUP.md) — Installation and configuration
- [API Reference](docs/API.md) — Stock Buddy API endpoints and webhooks
- [Database Schema](docs/DATABASE.md) — MongoDB collections
- [Combo Architecture](docs/combo/ARCHITECTURE.md) — System design
- [Combo PRD](docs/combo/PRD.md) — Product requirements
- [Troubleshooting](docs/TROUBLESHOOTING.md) — Common issues and solutions
- [Contributing](docs/CONTRIBUTING.md) — Development guidelines

## Requirements

- Python 3.11
- Chrome browser (latest)
- TradingView account with:
  - Two-factor authentication: optional (set `TRADINGVIEW_TOTP_SECRET` in `.env` if TV enables 2FA)
  - No linked social accounts
  - "Screener" layout with TTE Screener indicator saved and starred

## License

Proprietary - All rights reserved.

## Support

For issues and feature requests, please create an issue in the repository.
