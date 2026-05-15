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
8. [Linux / Docker Deployment](#linux--docker-deployment)
9. [Verification Steps](#verification-steps)

---

## System Requirements

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11.x | Must be exactly 3.11 |
| Google Chrome | Latest | Auto-updated preferred |
| MongoDB | 6.0+ | Atlas Cloud or local |
| Operating System | Windows 10/11 OR Linux (Docker) | Windows for dev, Linux/Docker for prod (since 2026-04-30) |
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

Set the `CHROME_PROFILE` env var in `.env` (the `PROFILE` constant in `tte/config.py` reads from this; don't edit the constant manually):

```bash
CHROME_PROFILE=Profile 4   # Windows default; use "Default" inside Docker
```

Each Docker container should have its own user-data-dir volume so multiple TTE instances don't clobber each other's Chrome profile state.

### Important Notes

- Close all Chrome browsers before running TTE
- Do not manually interact with the Selenium-controlled browser
- Each profile maintains its own TradingView session

---

## TradingView Account Setup

### Account Requirements

1. **Two-Factor Authentication** — supports two paths:
   - **2FA off** (preferred): TradingView Settings → Security → disable all 2FA methods. Simplest path.
   - **2FA on with TOTP auto-submit** (PR #40): if TV's "suspicious activity" detector forces 2FA on, set `TRADINGVIEW_TOTP_SECRET` (base32 secret from the QR code) in `.env`. The login flow calls `pyotp.TOTP(secret).now()` and submits via React-aware native value setter + dispatch events.
   - **Backup-code fallback**: see `.claude/credentials-and-2fa.md` for manual recovery if both above fail. Backup codes on TV are reusable, not single-use.

2. **Unlink Social Accounts**
   - Remove any linked Google, Facebook, or Apple accounts
   - TTE needs email/password login

3. **Premium Subscription** (Required)
   - Required for webhook alerts and full screener functionality

### TradingView Layout Setup

Create and save these layouts:

1. **"Screener" Layout** (required for alerts):
   - Add **TTE Screener V2** indicator
   - Star/favorite the indicator
   - Set chart to **45 seconds** timeframe
   - Set bar style to **Candle**
   - Save layout

2. **"Snapshot" Layout** (required for chart screenshots):
   - Add **NWE** indicator and **Trade Drawer v2** indicator
   - Star/favorite both indicators
   - Set bar style to **Candle**
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
# Optional: base32 TOTP secret. Set only if TV forces 2FA on the account (PR #40).
# Leave empty to skip auto-2FA — the login flow no-ops if this is unset.
TRADINGVIEW_TOTP_SECRET=

# MongoDB
MONGODB_PWD=your_mongodb_password
# OR use full connection string:
# MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true
MONGODB_DATABASE=tte

# Combo Webhook
COMBO_WEBHOOK_URL=https://stockbuddy.co/api/tte/combo
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
python -c "from tte.data.symbols import get_symbols; print(f'Loaded {sum(len(v) for v in get_symbols().values())} symbols')"
```

---

## Combo Mode Setup

### Configuration File

Combo mode uses `combo_settings.yaml` for all configuration. Edit this file to customize behavior:

```yaml
chart:
  layout_name: "Screener"        # TradingView layout name
  chart_timeframe: "45 seconds"  # Chart timeframe (V2)
  bar_style: "candle"            # Bar style (candle for exit detection)
  headless: true                 # Run Chrome without visible window

screener:
  shorttitle: "Screener V2"      # Indicator short title on chart
  name: "TTE Screener V2"       # Full indicator name

alerts:
  batch_size: 2                  # Symbols per alert (V2: 2, category-aware)
  creation_delay: 1.5            # Seconds between batches
  recalc_wait: 1.5               # Wait for indicator recalculation
  start_fresh: false             # Delete all alerts before setup

webhook:
  url: ""                        # Set via COMBO_WEBHOOK_URL env var

maintenance:
  interval: 150                  # Seconds between restart cycles (V2: 2.5 min)

snapshot:
  enabled: true                  # Enable chart snapshot worker
  layout_name: "Snapshot"        # TradingView layout for snapshots
  bar_style: "candle"
  batch_size: 10
  poll_interval: 60
  bars_to_right: 60

progress:
  file: combo_progress.json      # Progress tracking for resume
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

## Linux / Docker Deployment

Production runs in a Docker container on the Hostinger VPS (`168.231.103.163`). Same codebase as Windows — three platform-portable patches (see root `CLAUDE.md`) make `tte/main.py` Linux-safe.

### Build the image

```bash
# From repo root
docker build -t tte:latest .
```

The `Dockerfile` (`python:3.11-slim-bookworm` base) installs Chrome stable + matching ChromeDriver via the chrome-for-testing `LATEST_RELEASE_<MAJOR>` API, runs as non-root user `tte` (uid 1000), and sets these env defaults:

| Variable | Default | Purpose |
|----------|---------|---------|
| `CHROME_USER_DATA_DIR` | `/home/tte/chrome-profile` | Chrome profile volume mount target |
| `CHROME_PROFILE` | `Default` (set by compose) | Profile dir name inside user-data-dir; overrides `tte/config.py` PROFILE constant |
| `LOG_DIR` | `/app/logs` | App log dir; mount a host volume here for persistence |
| `CHROMEDRIVER_PATH` | `/usr/local/bin/chromedriver` | Where the build placed chromedriver |
| `PYTHONUNBUFFERED` | `1` | Stream stdout/stderr to compose logs |

### Per-instance volumes (compose)

Run multiple TTE instances (one per TradingView Ultimate account) by giving each its own user-data-dir + log volume:

```yaml
services:
  tte-1:
    image: tte:latest
    environment:
      CHROME_PROFILE: Default
      LOG_DIR: /app/logs
      MONGODB_URI: mongodb+srv://<user>:<pwd>@<atlas-cluster>/tte
      COMBO_WEBHOOK_URL: https://stockbuddy.co/api/tte/combo
      STOCK_BUDDY_API_URL: https://stockbuddy.co/api/tte
      TRADINGVIEW_EMAIL: ...
      TRADINGVIEW_PASSWORD: ...
    volumes:
      - tte1-chrome-profile:/home/tte/chrome-profile
      - ./logs/tte-1:/app/logs
    networks: [stockbuddy_net]
```

### Bootstrap: TradingView cookie injection (REQUIRED)

TV's auto-login form does NOT survive Cloudflare/bot defenses on a fresh container Chrome. Before bringing `tte-1` up the first time (or after wiping its profile volume), inject the TV session cookies directly into the user-data-dir.

1. Sign in to TradingView from a normal browser, open DevTools → Application → Cookies → `https://www.tradingview.com`, copy the values of `sessionid` and `sessionid_sign`.
2. Run the one-off bootstrap script with the volume mounted:

```bash
docker compose run --rm \
  -e TV_SESSION_ID='<sessionid value>' \
  -e TV_SESSION_ID_SIGN='<sessionid_sign value>' \
  --entrypoint python tte-1 inject_tv_cookies.py
```

3. Start the service normally:

```bash
docker compose up -d tte-1
```

`inject_tv_cookies.py` writes the cookies into the same `CHROME_USER_DATA_DIR` that `tte-1` mounts and exits. TV will then recognize the existing session and the standard TTE login flow short-circuits.

Re-run the bootstrap whenever:
- The profile volume is wiped/recreated
- TV invalidates the session (every ~30 days, or after a manual logout)
- You see repeated "Failed to sign in to TradingView" errors in `app_log.log` from the container

### Resolved: change_settings() screener-gear bug

The `change_settings()` timeout that previously kept the VPS container stopped was fixed in **PR #28** (commit `7e5cf20`, 2026-05-05). Field-validated on Windows the same day. See `docs/TROUBLESHOOTING.md` → "Screener Gear Click Intercepted (Resolved)" for root cause + fix detail.

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
python -c "from tte.data.symbols import get_symbols; symbols = get_symbols(); print(f'OK: {sum(len(v) for v in symbols.values())} symbols loaded')"
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
