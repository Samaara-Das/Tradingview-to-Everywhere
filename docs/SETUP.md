# Setup Guide

Complete installation and configuration guide for TradingView to Everywhere (TTE).

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Python Environment Setup](#python-environment-setup)
3. [Chrome Profile Configuration](#chrome-profile-configuration)
4. [TradingView Account Setup](#tradingview-account-setup)
5. [Environment Variables](#environment-variables)
6. [MongoDB Setup](#mongodb-setup)
7. [Combo Mode Setup](#combo-mode-setup)
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

# Should show: selenium, pymongo, pyyaml, etc.
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

3. **Premium Subscription** (Required)
   - Required for webhook alerts and full screener functionality

### TradingView Layout Setup

Create and save this layout:

1. **"Screener" Layout**:
   - Add **TTE Screener** indicator
   - Star/favorite the indicator
   - Set chart to **1-minute** timeframe
   - Set bar style to **Line**
   - Save layout

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

# Combo Webhook
COMBO_WEBHOOK_URL=https://stock-buddy-app.vercel.app/api/tte/combo
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

The following collections are used:

| Collection | Purpose |
|------------|---------|
| `symbols` | Symbol definitions and categories |

### Verify MongoDB Connection

```bash
python -c "from resources.symbol_settings import get_symbols; print(f'Loaded {sum(len(v) for v in get_symbols().values())} symbols')"
```

---

## Combo Mode Setup

### Configuration File

Combo mode uses `combo_settings.yaml` for all configuration. Edit this file to customize behavior:

```yaml
chart:
  layout_name: "Screener"        # TradingView layout name
  chart_timeframe: "1 minute"     # Chart timeframe
  bar_style: "line"               # Bar style (line for minimal resources)
  headless: true                  # Run Chrome without visible window

screener:
  shorttitle: "Screener"          # Indicator short title on chart
  name: "TTE Screener"           # Full indicator name

alerts:
  batch_size: 3                   # Symbols per alert (max 4)
  creation_delay: 1.5             # Seconds between batches
  recalc_wait: 1.5                # Wait for indicator recalculation
  start_fresh: false              # Delete all alerts before setup

webhook:
  url: ""                         # Set via COMBO_WEBHOOK_URL env var

maintenance:
  interval: 300                   # Seconds between restart cycles

progress:
  file: combo_progress.json       # Progress tracking for resume
```

### Running Combo Mode

**CLI**:
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

**GUI** (recommended):
```bash
# Launch the GUI
python tte_gui.py

# Or use the standalone executable (no Python needed)
dist\TTE.exe
```

The GUI provides a visual interface for editing `combo_settings.yaml`, selecting run modes, and monitoring progress.

---

## Verification Steps

### 1. Validate Configuration

```bash
python combo_main.py --validate
```

### 2. Test Browser Launch

Run combo mode without `--setup-only` and verify:
- Chrome launches (or runs headless)
- TradingView login succeeds
- Layout loads correctly
- Indicator is detected

### 3. Verify MongoDB Connection

```bash
python -c "from resources.symbol_settings import get_symbols; symbols = get_symbols(); print(f'OK: {sum(len(v) for v in symbols.values())} symbols loaded')"
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

1. Review [Combo Architecture](combo/ARCHITECTURE.md) to understand the system
2. Check [API Reference](API.md) for endpoint details
3. See [Troubleshooting](TROUBLESHOOTING.md) for runtime issues
