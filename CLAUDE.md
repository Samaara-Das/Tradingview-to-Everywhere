# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TradingView to Everywhere (TTE) is an automated trading signals distribution system that bridges TradingView alerts with multiple social media platforms. It monitors TradingView for trading signals, captures and processes them, and distributes formatted trade information to Discord, Facebook, Twitter/X, and MongoDB.

## Common Development Tasks

### Running the Application

```bash
# Activate the virtual environment
pipenv shell

# Run the main application
python main.py

# Run the GUI version
python gui.py
```

### Managing Dependencies

```bash
# Install all dependencies
pipenv install

# Add a new dependency
pipenv install <package-name>

# Sync dependencies from Pipfile
pipenv sync
```

## Architecture Overview

### Core Components

1. **Browser Controller** (`open_tv.py`): Manages Selenium browser automation and TradingView interaction
2. **Alert Handler** (`handle_alerts.py`): Processes alert messages and extracts trade information
3. **Chart Manager** (`open_entry_chart.py`): Navigates charts and captures screenshots
4. **Exit Monitor** (`exits.py`): Tracks trade exits and distributes exit information
5. **Social Distributors** (`send_to_socials/`): Distributes to Discord, Twitter, Facebook
6. **Database Manager** (`database/`): MongoDB integration for trade storage

### Key Files

- `main.py`: Entry point with main trading loop
- `gui.py`: Tkinter-based GUI interface
- `env.py`: Environment configuration
- `logger_setup.py`: Centralized logging configuration
- `resources/symbol_settings.py`: Trading symbol categories and configurations

### Data Flow

1. TradingView generates alerts based on technical analysis
2. TTE captures alert messages via Selenium
3. TTE navigates to relevant chart/timeframe
4. Screenshots taken with trade information overlay
5. Distribution to multiple platforms
6. Exit monitoring and notification

## Important Configuration

### Environment Variables Required

- `CHROME_PROFILES_PATH`: Path to Chrome user data folder
- `TRADINGVIEW_EMAIL`: TradingView login email (2FA must be disabled)
- `TRADINGVIEW_PASSWORD`: TradingView login password
- `MONGODB_PWD`: MongoDB database password
- Discord webhook URLs (in `.env` file)
- Twitter API keys (in `.env` file)

### Chrome Profile Setup

1. Create a `TTE` folder in Chrome user data directory
2. Configure the `PROFILE` constant in `env.py`
3. Ensure no other Chrome instances are running during execution

### TradingView Requirements

1. Disable two-factor authentication
2. No linked social accounts
3. Saved layout named "Screener" with Premium Screener and Trade Drawer indicators
4. Saved layout named "Exits" with Get Exits indicator
5. Indicators must be starred/favorited

## Key Constants

### main.py
- `SCREENER_SHORT`: 'Screener' (screener short title)
- `DRAWER_SHORT`: 'Trade Drawer 2' (indicator short title)
- `INTERVAL_MINUTES`: 10 (refresh and restart interval)
- `START_FRESH`: True (delete and recreate alerts)
- `SCREENER_TIMEFRAME_1/2/3`: Configured timeframes for screeners

### open_tv.py
- `SYMBOL_INPUTS`: Number of symbol inputs to fill (currently 5)
- `CHART_TIMEFRAME`: Trading timeframe for entries
- `SCREENER_REUPLOAD_TIMEOUT`: Wait time for screener re-upload

## Testing and Debugging

### Logs
- Main log file: `app_log.log`
- Continuous log trimming enabled to prevent overflow
- Comprehensive logging throughout all modules

### Common Issues
- Browser memory usage - periodic refresh implemented
- Alert rate limits - automatic restart of inactive alerts
- TradingView UI changes - may require selector updates
- MongoDB connection - check password and connection string

## Development Guidelines

1. Maintain modular structure with clear separation of concerns
2. Use environment variables for all credentials and configurations
3. Implement comprehensive error handling and logging
4. Test browser automation thoroughly before deployment
5. Handle API rate limits appropriately
6. Never commit credentials or sensitive information

## Critical Notes

- Never manually interact with the Selenium-controlled browser
- Ensure all Chrome browsers are closed before running
- The Alerts log must be maximized (not minimized) in TradingView
- The application will delete existing alerts when `START_FRESH=True`
- MongoDB symbols must be synced with TradingView alerts
- Whenever you make a mistake, write what you learnt from it in @AGENTS.md so that it's never repeated in the future

## Troubleshooting Commands

```bash
# Check Python version (must be 3.11)
python --version

# List installed packages
pipenv graph

# Clear log file
echo "" > app_log.log

# Test MongoDB connection
python -c "from database.local_db import db; print(db.list_collection_names())"
```