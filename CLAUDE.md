# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TradingView to Everywhere (TTE) is an automated trading signals distribution system that bridges TradingView alerts with multiple social media platforms. It monitors TradingView for trading signals, captures and processes them, and distributes formatted trade information to Discord, Facebook, Twitter (X), and Firebase.

## Common Development Commands

### Environment Setup
```bash
# Install dependencies using pipenv
pipenv install

# Activate virtual environment
pipenv shell

# Run the application
python main.py

# Run with GUI
python gui.py
```

### Testing
```bash
# Test Firebase connection
python database/test_firebase.py
```

## High-level Architecture

### Core Application Flow
1. **Browser Automation** (`open_tv.py`): Controls Chrome/Selenium to interact with TradingView
2. **Alert Processing** (`handle_alerts.py`): Captures and parses TradingView alerts
3. **Chart Management** (`open_entry_chart.py`): Takes screenshots of trades
4. **Exit Monitoring** (`exits.py`): Tracks trade exits and captures exit screenshots
5. **Distribution** (`send_to_socials/`): Sends formatted data to social platforms
6. **Database** (`database/firebase_db.py`): Stores entries/exits in Firebase Firestore

### Key Inter-Module Dependencies
- `main.py` orchestrates the entire flow, calling functions from other modules
- `env.py` centralizes configuration constants (COLLECTION, PROFILE, etc.)
- `handle_alerts.py` and `exits.py` both rely on `database/firebase_db.py` for storage
- Social media modules depend on environment variables for API credentials

### Database Architecture
- **Firebase Firestore** is used for persistent storage
- Main collection: "Entries" (configured in `env.py`)
- Document structure includes: direction, symbol, timeframe, prices (entry/tp/sl), timestamps, snapshots, hit status
- Indexes exist on: category, unixTime fields for efficient querying

### Authentication Strategy
- **TradingView**: Uses Chrome profile with saved login (no 2FA allowed)
- **Firebase**: Service account credentials via JSON file
- **Social APIs**: Environment variables store webhooks, API keys, and tokens

### Important Configuration
- **Chrome Profile**: Must be set in `env.py` (PROFILE constant)
- **TradingView Layouts**: "Screener" and "Exits" layouts must exist
- **Indicators**: Premium Screener, Trade Drawer, Get Exits must be installed and starred
- **Environment Variables**: See `.env` file for Discord webhooks, Twitter API keys, etc.

### Critical Constraints
- TradingView account must have 2FA disabled
- Chrome browser must be closed before running
- Selenium browser must not be manually interacted with during execution
- Maximum 5 symbols can be processed per screener alert

## Key Files Reference

- `main.py`: Entry point and main orchestration logic
- `open_tv.py`: Browser automation and TradingView interaction
- `handle_alerts.py`: Alert processing and entry detection
- `exits.py`: Exit monitoring and processing
- `database/firebase_db.py`: Firebase database operations
- `env.py`: Central configuration constants
- `resources/symbol_settings.py`: Trading symbol categories and settings

## Accessing Screener Indicators in open_tv.py

Due to TradingView's dynamic DOM updates, screener indicators must be accessed using safe methods to prevent StaleElementReferenceException errors.

### Methods to Use:

1. **`_safe_indicator_access(shorttitle)`** - RECOMMENDED
   - Primary method for safely accessing any indicator
   - Automatically handles stale element errors with retry logic
   - Returns `None` if indicator not found
   ```python
   # Get a screener indicator safely
   screener_ob = self._safe_indicator_access(self.screener_ob_short)
   screener_nw = self._safe_indicator_access(self.screener_nw_short)
   screener_sb = self._safe_indicator_access(self.screener_sb_short)
   drawer = self._safe_indicator_access(self.drawer_shorttitle)
   ```

2. **`_get_fresh_indicator(shorttitle)`**
   - Simple wrapper that calls `get_indicator()`
   - Use when you want a fresh reference without retry logic

3. **`get_indicator(shorttitle)`**
   - Base method that searches the DOM
   - Use when implementing custom error handling

### Available Screener Properties:
- `self.screener_ob_short` - Order Block screener
- `self.screener_nw_short` - Nadaraya Watson screener
- `self.screener_sb_short` - Structure Break screener
- `self.drawer_shorttitle` - Trade Drawer indicator

### Important Notes:
- **Never store indicator references** as instance variables (no `self.screener_ob_indicator`)
- **Always get fresh references** when needed
- **Check for `None`** before using returned indicators
- **DOM changes** during alert creation invalidate stored references

### Example Usage:
```python
def some_method(self):
    # Get the Order Block screener safely
    ob_screener = self._safe_indicator_access(self.screener_ob_short)
    if ob_screener:
        ob_screener.click()
        
    # Get all screeners at once
    screeners = {
        'ob': self._safe_indicator_access(self.screener_ob_short),
        'nw': self._safe_indicator_access(self.screener_nw_short),
        'sb': self._safe_indicator_access(self.screener_sb_short)
    }
```