# TradingView to Everywhere (TTE)

## Project Overview

TradingView to Everywhere (TTE) is an automated trading signals distribution system that bridges TradingView alerts with multiple social media platforms. It monitors TradingView for trading signals, captures and processes them, and distributes formatted trade information to various platforms including Discord, Facebook, Twitter (X), and a MongoDB database.

**Core Purpose:** To automate the process of monitoring, capturing, and distributing trading signals from TradingView to multiple platforms simultaneously.

**Key Features:**
1. Automated TradingView alert setup for over 1300 trading symbols across multiple categories (US Stocks, Indian Stocks, Crypto, Currencies)
2. Alert message parsing and entry signal extraction
3. Automated chart screenshot capture at entry points
4. Multi-platform distribution (Discord, Facebook, Twitter/X, MongoDB)
5. Automated exit monitoring and notification
6. Visual trade journey documentation (entry to exit)

## Technical Stack

### Frontend
- Python GUI interface (Tkinter-based)
- TradingView web interface (accessed via Selenium)

### Backend
- Python 3.11
- Selenium for browser automation
- MongoDB for data storage

### Database
- MongoDB for persistent storage of trade entries and exits

### External APIs
- Discord webhooks API
- Twitter API (via Tweepy)
- Facebook API
- TradingView (via browser automation)

## Architecture Overview

### Pattern
The application follows a modular architecture with clear separation of concerns:
- Browser automation (Selenium)
- Alert handling
- Chart manipulation
- Social media distribution
- Database storage

### Data Flow
1. TradingView generates alerts based on technical analysis criteria
2. TTE captures alert messages and extracts trade information
3. TTE navigates to the relevant chart and timeframe
4. TTE takes screenshots of the entry point with trade information overlaid
5. Trade data and screenshots are distributed to various platforms
6. TTE monitors for trade exits and distributes exit information when conditions are met

### Key Components
1. **Browser Controller** (`open_tv.py`): Manages browser automation and TradingView interaction
2. **Alert Handler** (`handle_alerts.py`): Processes alert messages and extracts trade information
3. **Chart Manager** (`open_entry_chart.py`): Navigates to and manipulates charts for screenshot capture
4. **Exit Monitor** (`exits.py`): Tracks trade exits and distributes exit information
5. **Social Distributors** (`send_to_socials/`): Sends formatted trade information to various platforms
6. **Database Manager** (`database/`): Stores and retrieves trade information

### Auth Strategy
- Environment variables for secure credential storage
- OAuth for Twitter API authentication
- Token-based authentication for Discord webhooks
- Chrome user profile for TradingView authentication

## Core Components

### Browser Controller (open_tv.py)
- **Purpose:** Manages browser automation, TradingView navigation, and indicator setup
- **Key Files:** `open_tv.py`
- **Data Models:** Browser session, TradingView layout
- **Technical Challenges:** Reliable browser automation, handling TradingView UI changes

### Alert Handler (handle_alerts.py)
- **Purpose:** Processes TradingView alerts and extracts trade information
- **Key Files:** `handle_alerts.py`
- **Data Models:** Alert message structure, trade entry data
- **Technical Challenges:** Parsing complex alert messages, handling alert rate limits

### Chart Manager (open_entry_chart.py)
- **Purpose:** Navigates to specific charts and manipulates indicators for screenshot capture
- **Key Files:** `open_entry_chart.py`
- **Data Models:** Chart layout, indicator settings
- **Technical Challenges:** Reliable chart navigation, handling TradingView rendering

### Exit Monitor (exits.py)
- **Purpose:** Tracks trade exits and distributes exit information
- **Key Files:** `exits.py`
- **Data Models:** Trade exit data, exit conditions
- **Technical Challenges:** Accurate exit detection, handling multiple exit conditions

### Social Distributors (send_to_socials/)
- **Purpose:** Distributes formatted trade information to various platforms
- **Key Files:** `discord.py`, `twitter.py`, `_facebook.py`, `linkedin.py`
- **Data Models:** Platform-specific message formats
- **Technical Challenges:** API rate limits, maintaining authentication

### Database Manager (database/)
- **Purpose:** Stores and retrieves trade information
- **Key Files:** `local_db.py`, `nk_db.py`, `firebase_db.py`
- **Data Models:** Trade entry/exit documents
- **Technical Challenges:** Reliable data storage, efficient querying

## Development Guidelines

### Code Organization
- Modular structure with clear separation of concerns
- Configuration via environment variables and constants
- Comprehensive logging throughout the application

### Testing Approach
- Manual testing of browser automation components
- Automated monitoring for failures and exceptions
- Logging and error handling for fault detection

### Performance Considerations
- Browser memory usage
- MongoDB connection management
- API rate limit handling
- Periodic restart of inactive alerts

## Setup Instructions

1. Clone the repository
2. Install Python 3.11
3. Install dependencies: `pipenv install`
4. Configure environment variables (see `.env` documentation)
5. Set up Chrome profiles as specified in documentation
6. Set up TradingView account (disable 2FA)
7. Install required TradingView indicators
8. Configure webhook URLs and API keys
9. Run the application: `python main.py` or use the compiled executable

## Usage

1. Start the application (via GUI or command line)
2. The application will automatically:
   - Open TradingView in a controlled browser session
   - Set up required indicators and alerts
   - Monitor for trading signals
   - Distribute trade information to configured platforms
   - Track and report trade exits

## Troubleshooting

- Check logs in the `app_log.log` file
- Ensure Chrome profile is configured correctly
- Verify TradingView account has no 2FA enabled
- Check webhook URLs and API keys in environment variables
- Ensure indicators are correctly installed in TradingView

## Contributing

1. Review the DEV-README.md for detailed technical information
2. Follow the existing code structure and patterns
3. Ensure comprehensive logging for all new components
4. Test thoroughly with various alert scenarios
5. Document any configuration changes

For detailed development information, see DEV-README.md.

