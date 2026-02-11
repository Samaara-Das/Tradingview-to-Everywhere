# Setup Guide

Complete installation and configuration guide for TradingView to Everywhere (TTE).

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Python Environment Setup](#python-environment-setup)
3. [Chrome Profile Configuration](#chrome-profile-configuration)
4. [TradingView Account Setup](#tradingview-account-setup)
5. [Environment Variables](#environment-variables)
6. [MongoDB Setup](#mongodb-setup)
7. [API Keys Setup](#api-keys-setup)
8. [Verification Steps](#verification-steps)

---

## System Requirements

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11.x | Must be exactly 3.11 |
| Google Chrome | Latest | Auto-updated preferred |
| MongoDB | 6.0+ | Atlas Cloud or local |
| Operating System | Windows 10/11 | Tested on Windows |
| RAM | 8GB+ | Browser automation is memory-intensive |

### Verify Python Version

```bash
python --version
# Output: Python 3.11.x
```

If you have multiple Python versions, use `py -3.11` on Windows.

---

## Python Environment Setup

### 1. Install Pipenv

```bash
pip install pipenv
```

### 2. Clone and Setup Project

```bash
# Clone the repository
git clone <repository-url>
cd tradingview-to-everywhere

# Install dependencies
pipenv install

# Activate the virtual environment
pipenv shell
```

### 3. Verify Installation

```bash
# List installed packages
pipenv graph

# Should show: selenium, pymongo, requests, etc.
```

---

## Chrome Profile Configuration

TTE uses a dedicated Chrome profile to maintain TradingView session state.

### 1. Locate Chrome User Data Directory

**Windows**:
```
C:\Users\<YourUsername>\AppData\Local\Google\Chrome\User Data
```

### 2. Create TTE Profile Folder

Create a folder named `TTE` inside the Chrome user data directory:

```
C:\Users\<YourUsername>\AppData\Local\Google\Chrome\User Data\TTE
```

### 3. Configure Environment Variable

Set the `CHROME_PROFILES_PATH` in your `.env` file:

```bash
CHROME_PROFILES_PATH=C:\Users\<YourUsername>\AppData\Local\Google\Chrome\User Data
```

### 4. Configure Profile Name

In `env.py`, verify the `PROFILE` constant matches your setup:

```python
PROFILE = "Profile 4"  # Or the profile number you want to use
```

### Important Notes

- Close all Chrome browsers before running TTE
- Do not manually interact with the Selenium-controlled browser
- Each profile maintains its own TradingView session

---

## TradingView Account Setup

### Account Requirements

1. **Disable Two-Factor Authentication**
   - Go to TradingView Settings > Security
   - Disable all 2FA methods

2. **Unlink Social Accounts**
   - Remove any linked Google, Facebook, or Apple accounts
   - TTE needs email/password login

3. **Premium Subscription** (Recommended)
   - Required for full screener functionality
   - Free accounts have limited features

### TradingView Layout Setup

#### For Legacy Mode

Create and save these layouts:

1. **"Screener" Layout**:
   - Add Premium Screener indicator
   - Add Trade Drawer 2 indicator
   - Star/favorite both indicators

2. **"Exits" Layout**:
   - Add Get Exits indicator
   - Star/favorite the indicator

#### For Tiered Mode

Create and save these layouts:

1. **"NWE" Layout**:
   - Add TTE NWE Screener v2 indicator
   - Star/favorite the indicator
   - Set chart to 5-minute timeframe

2. **"OBDIV" Layout**:
   - Add TTE OBDIV Screener v2 indicator
   - Star/favorite the indicator
   - Set chart to 5-minute timeframe

### Get Chart URLs (Tiered Mode)

1. Open TradingView chart with NWE layout
2. Copy the URL (e.g., `https://www.tradingview.com/chart/abcd1234/`)
3. This is your `NWE_CHART_URL`

4. Open TradingView chart with OBDIV layout
5. Copy the URL
6. This is your `OBDIV_CHART_URL`

---

## Environment Variables

Create a `.env` file in the project root with the following variables:

### Required Variables

```bash
# Chrome Configuration
CHROME_PROFILES_PATH=C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data

# TradingView Credentials
TRADINGVIEW_EMAIL=your@email.com
TRADINGVIEW_PASSWORD=your_password

# MongoDB
MONGODB_PWD=your_mongodb_password
# OR use full connection string:
# MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true
MONGODB_DATABASE=tte
```

### Tiered Mode Variables

```bash
# Stock Buddy API
STOCK_BUDDY_API_URL=https://stock-buddy-app.vercel.app/api/tte
API_TIMEOUT=30

# TradingView Chart URLs
NWE_CHART_URL=https://www.tradingview.com/chart/your-nwe-chart-id/
OBDIV_CHART_URL=https://www.tradingview.com/chart/your-obdiv-chart-id/

# Batch Configuration
NWE_BATCH_SIZE=20
OBDIV_BATCH_SIZE=8
NWE_BATCH_WAIT=60
OBDIV_BATCH_WAIT=60

# Orchestrator Settings
CYCLE_INTERVAL=300
MAX_RETRIES=3
RETRY_DELAY=5

# Chrome Profile (if different from default)
CHROME_PROFILE=Profile 2
```

### Discord Webhooks (Legacy Mode)

```bash
# Webhook Names
CURRENCIES_WEBHOOK_NAME=Currencies
US_STOCKS_WEBHOOK_NAME=US Stocks
INDIAN_STOCKS_WEBHOOK_NAME=Indian Stocks
CRYPTO_WEBHOOK_NAME=Crypto

# Entry Webhook URLs
CURRENCIES_ENTRY_WEBHOOK_LINK=https://discord.com/api/webhooks/xxx/yyy
US_STOCKS_ENTRY_WEBHOOK_LINK=https://discord.com/api/webhooks/xxx/yyy
INDIAN_STOCKS_ENTRY_WEBHOOK_LINK=https://discord.com/api/webhooks/xxx/yyy
CRYPTO_ENTRY_WEBHOOK_LINK=https://discord.com/api/webhooks/xxx/yyy

# Exit Webhook URLs
CURRENCIES_EXIT_WEBHOOK_LINK=https://discord.com/api/webhooks/xxx/yyy
US_STOCKS_EXIT_WEBHOOK_LINK=https://discord.com/api/webhooks/xxx/yyy
INDIAN_STOCKS_EXIT_WEBHOOK_LINK=https://discord.com/api/webhooks/xxx/yyy
CRYPTO_EXIT_WEBHOOK_LINK=https://discord.com/api/webhooks/xxx/yyy

# Before/After Webhook URLs
CURRENCIES_BEFORE_AFTER_WEBHOOK_LINK=https://discord.com/api/webhooks/xxx/yyy
US_STOCKS_BEFORE_AFTER_WEBHOOK_LINK=https://discord.com/api/webhooks/xxx/yyy
INDIAN_STOCKS_BEFORE_AFTER_WEBHOOK_LINK=https://discord.com/api/webhooks/xxx/yyy
CRYPTO_BEFORE_AFTER_WEBHOOK_LINK=https://discord.com/api/webhooks/xxx/yyy
```

### Twitter API (Legacy Mode)

```bash
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_BEARER=your_bearer_token
X_ACCESS_TOKEN=your_access_token
X_ACCESS_SECRET=your_access_secret
X_CLIENT_ID=your_client_id
X_CLIENT_SECRET=your_client_secret
```

---

## MongoDB Setup

### Option 1: MongoDB Atlas (Recommended)

1. Create account at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a free M0 cluster
3. Create database user with read/write permissions
4. Add your IP to the IP Access List (or use 0.0.0.0/0 for all IPs)
5. Get connection string and add to `.env`

### Option 2: Local MongoDB

1. Install MongoDB Community Server
2. Start MongoDB service
3. Use local connection string:
   ```bash
   MONGODB_URI=mongodb://127.0.0.1:27017/?directConnection=true
   ```

### Required Collections

The following collections will be created automatically:

| Collection | Purpose |
|------------|---------|
| `Point Capitalis signals` | Trading signals storage |
| `symbols` | Symbol definitions and categories |

### Verify MongoDB Connection

```bash
python -c "from database.local_db import Database; db = Database(); print('Connected!')"
```

---

## API Keys Setup

### Discord Webhooks

1. Open your Discord server
2. Go to Server Settings > Integrations > Webhooks
3. Click "New Webhook"
4. Name it according to category (e.g., "Currencies Entry")
5. Copy the webhook URL
6. Add to `.env` file

### Twitter API

1. Create Twitter Developer account at [developer.twitter.com](https://developer.twitter.com)
2. Create a new project and app
3. Generate API keys and tokens
4. Add all credentials to `.env`

---

## Verification Steps

### 1. Verify Configuration (Tiered Mode)

```bash
python tiered_main.py --validate
```

Expected output:
```
Validating configuration...

API Base URL: https://stock-buddy-app.vercel.app/api/tte
NWE Chart URL: https://www.tradingview.com/chart/xxxxx/
OBDIV Chart URL: https://www.tradingview.com/chart/yyyyy/
NWE Batch Size: 20
OBDIV Batch Size: 8
...

Configuration VALID
```

### 2. Test API Connection

```bash
python tiered_main.py --test-api
```

Expected output:
```
Testing API connection...

API Base URL: https://stock-buddy-app.vercel.app/api/tte
Health check: PASS

API Statistics:
  Total symbols: 941
  ...

API test completed successfully!
```

### 3. Test Browser Automation

```bash
python tiered_main.py --test-browser
```

This will:
- Launch Chrome with your profile
- Navigate to TradingView
- Verify login status
- Leave browser open for inspection

### 4. Test MongoDB Connection

```bash
python -c "from database.local_db import Database; db = Database(); print(db.get_latest_doc())"
```

### 5. Run a Single Cycle

```bash
python tiered_main.py --single-cycle
```

This runs one complete NWE + OBDIV cycle and exits.

---

## Combo Mode Setup

### Configuration File

Combo mode uses `combo_settings.yaml` for all configuration. Edit this file to customize behavior:

```yaml
chart:
  layout_name: "Screener"        # TradingView layout name
  chart_timeframe: "1 minute"     # Chart timeframe
  bar_style: "line"               # Bar style (line for minimal resources)

alerts:
  batch_size: 3                   # Symbols per alert (max 4)
  num_browsers: 2                 # Parallel browser instances
  creation_delay: 3.0             # Seconds between batches

webhook:
  url: ""                         # Set via COMBO_WEBHOOK_URL env var

maintenance:
  interval: 300                   # Seconds between restart cycles
```

### Environment Variables

Add these to your `.env` file:

```bash
COMBO_WEBHOOK_URL=https://stock-buddy-app.vercel.app/api/tte/combo
COMBO_NUM_BROWSERS=2
```

### TradingView Layout (Combo Mode)

1. Create layout named **"Screener"**
2. Add **TTE Screener** indicator
3. Star/favorite the indicator
4. Set chart to **1-minute** timeframe
5. Set bar style to **Line**
6. Save layout

### Running Combo Mode

```bash
# Validate configuration
python combo_main.py --validate

# Full setup (create all alerts) + maintenance
python combo_main.py

# Delete all alerts first, then fresh setup
python combo_main.py --fresh

# Run maintenance only (alerts already created)
python combo_main.py --maintain-only
```

---

## Common Setup Issues

### Chrome Profile Locked

**Error**: `Chrome is being controlled by automated test software`

**Solution**: Close all Chrome windows before running TTE.

### TradingView Login Failed

**Error**: `Failed to sign in to TradingView`

**Solution**:
1. Verify credentials in `.env`
2. Ensure 2FA is disabled
3. Try logging in manually to check for captcha

### MongoDB Connection Failed

**Error**: `Failed to connect to MongoDB`

**Solution**:
1. Check `MONGODB_PWD` or `MONGODB_URI`
2. Verify IP is whitelisted in Atlas
3. Test connection string in MongoDB Compass

### ChromeDriver Version Mismatch

**Error**: `This version of ChromeDriver only supports Chrome version X`

**Solution**: TTE auto-downloads matching ChromeDriver. If issues persist:
1. Update Chrome to latest version
2. Delete cached ChromeDriver
3. Restart TTE

---

## Next Steps

After successful setup:

1. Review [Architecture](legacy/ARCHITECTURE.md) to understand the system
2. Check [API Reference](API.md) for endpoint details
3. See [Troubleshooting](TROUBLESHOOTING.md) for runtime issues
