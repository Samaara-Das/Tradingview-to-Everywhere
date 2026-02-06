# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TradingView to Everywhere (TTE) is an automated trading signals distribution system that bridges TradingView alerts with multiple social media platforms. It monitors TradingView for trading signals, captures and processes them, and distributes formatted trade information to Discord, Facebook, Twitter/X, and MongoDB.

### Things to always keep in mind
This new tiered architecture in TTE should use existing code in the codebase whenever possible. Before implementing any code that performs a particular action, thoroughly check if this has been done before. If so, decide if it's best to use the existing code or not.

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

### Data Flow (Legacy Mode)

1. TradingView generates alerts based on technical analysis
2. TTE captures alert messages via Selenium
3. TTE navigates to relevant chart/timeframe
4. Screenshots taken with trade information overlay
5. Distribution to multiple platforms
6. Exit monitoring and notification

## Tiered Architecture (New)

The tiered architecture uses webhook-based alerts instead of poll-based scraping.

### Key Files
- `tiered_main.py`: Entry point for tiered orchestrator
- `orchestrator.py`: TieredOrchestrator class managing two-phase workflow
- `api_client.py`: Stock Buddy API client
- `config.py`: Tiered orchestrator configuration
- `docs/PRD.md`: Complete technical specification (1800+ lines)

### TradingView Screeners
Located in `screeners on TV/`:
- `TTE NWE Screener v2.txt` - Tier 1: 20 symbols, H4/D1 NWE zones
- `TTE OBDIV Screener v2.txt` - Tier 2: 8 symbols, OB/FVG + Divergence

### Tiered Workflow (Single Cycle = One 20-Symbol Batch)
1. Input 20 symbols to NWE screener
2. Create webhook alert, wait for it to trigger
3. Delete alert
4. Hot symbols (from webhook) go to OBDIV screener (batches of 8)
5. Create webhook alert, wait for it to trigger
6. Delete alert, repeat until all hot symbols processed
7. Move to next 20-symbol batch

### Running Tiered Mode
```bash
python tiered_main.py              # Run continuously
python tiered_main.py --validate   # Validate configuration
python tiered_main.py --test-api   # Test API connection
python tiered_main.py --stats      # Show system statistics
```

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

**For Legacy Mode:**
1. Disable two-factor authentication
2. No linked social accounts
3. Saved layout named "Screener" with Premium Screener and Trade Drawer indicators
4. Saved layout named "Exits" with Get Exits indicator
5. Indicators must be starred/favorited

**For Tiered Mode:**
1. Disable two-factor authentication
2. No linked social accounts
3. Saved layout named "NWE" with TTE NWE Screener v2 indicator
4. Saved layout named "OBDIV" with TTE OBDIV Screener v2 indicator
5. Both indicators must be starred/favorited

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
5. Never commit credentials or sensitive information
6. **Always add logging**: Every new function or significant code block should include debug logging (using `print(..., flush=True)` for immediate output or `logger.info/debug/error()` for file logging). This is essential for debugging browser automation issues.
7. Whenever you make a mistake, write what you learnt from it in @AGENTS.md so that it's never repeated in the future


## Documentation Maintenance

When making significant changes to the codebase, update the relevant documentation:

| Change Type | Files to Update |
|-------------|-----------------|
| Features or usage changes | `README.md` |
| Setup/configuration changes | `docs/SETUP.md` |
| API endpoint changes | `docs/API.md` |
| Database schema changes | `docs/DATABASE.md` |
| Architecture/module changes | `docs/ARCHITECTURE.md` |
| New issues/solutions discovered | `docs/TROUBLESHOOTING.md` |
| Implementation phase progress | `docs/PRD.md` |

Documentation should be updated as part of the same PR that introduces the code changes.

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