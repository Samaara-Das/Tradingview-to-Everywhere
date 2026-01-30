# Environment Configuration Guide
# TTE Tiered Screener Architecture

This document describes all environment variables required for the project.

---

## Overview

The project consists of two main components with separate environment configurations:

1. **TTE (Python Orchestrator)** - Local machine
2. **Stock Buddy (Next.js App)** - Vercel

---

## TTE Python Orchestrator

### File Location
```
tradingview-to-everywhere/.env
```

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `STOCK_BUDDY_API_URL` | Base URL for Stock Buddy API | `https://stock-buddy-app.vercel.app/api` |
| `CHROME_PROFILE_PATH` | Path to Chrome user data directory | `C:/Users/YourName/AppData/Local/Google/Chrome/User Data` |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `LOG_LEVEL` | Logging verbosity | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `POLL_INTERVAL` | Seconds between API polls | `60` | `30`, `120` |
| `BATCH_SIZE` | Max symbols per OBDIV batch | `8` | `4`, `8` |
| `SELENIUM_IMPLICIT_WAIT` | Selenium implicit wait (seconds) | `10` | `15`, `20` |
| `SELENIUM_EXPLICIT_WAIT` | Selenium explicit wait (seconds) | `30` | `45`, `60` |
| `SCREENSHOT_WAIT` | Wait before screenshot (seconds) | `2` | `3`, `5` |

### Sample .env File

```env
# ===========================================
# TTE Tiered Orchestrator Configuration
# ===========================================

# Stock Buddy API
STOCK_BUDDY_API_URL=https://stock-buddy-app.vercel.app/api

# Chrome Configuration
# Windows: C:/Users/YourName/AppData/Local/Google/Chrome/User Data
# macOS: /Users/YourName/Library/Application Support/Google/Chrome
# Linux: /home/YourName/.config/google-chrome
CHROME_PROFILE_PATH=C:/Users/dassa/AppData/Local/Google/Chrome/User Data

# Logging
LOG_LEVEL=INFO

# Polling Configuration
POLL_INTERVAL=60
BATCH_SIZE=8

# Selenium Timeouts
SELENIUM_IMPLICIT_WAIT=10
SELENIUM_EXPLICIT_WAIT=30
SCREENSHOT_WAIT=2
```

### Finding Chrome Profile Path

**Windows:**
```
C:\Users\<USERNAME>\AppData\Local\Google\Chrome\User Data
```

**macOS:**
```
/Users/<USERNAME>/Library/Application Support/Google/Chrome
```

**Linux:**
```
/home/<USERNAME>/.config/google-chrome
```

---

## Stock Buddy (Vercel)

### File Location (Local Development)
```
stock-buddy/.env.local
```

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB Atlas connection string | `mongodb+srv://user:pass@cluster.mongodb.net/tte` |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `WEBHOOK_SECRET` | Secret for webhook authentication | (none) | `your-random-secret-min-32-chars` |
| `NODE_ENV` | Environment mode | `development` | `production` |

### Sample .env.local File

```env
# ===========================================
# Stock Buddy Configuration
# ===========================================

# MongoDB Atlas Connection
# Format: mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>
MONGODB_URI=mongodb+srv://tteuser:yourpassword@cluster0.abc123.mongodb.net/tte?retryWrites=true&w=majority

# Webhook Security (optional but recommended)
# Generate with: openssl rand -hex 32
WEBHOOK_SECRET=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6

# Environment
NODE_ENV=development
```

### Vercel Environment Variables

Set these in Vercel Dashboard → Project Settings → Environment Variables:

| Variable | Environment | Value |
|----------|-------------|-------|
| `MONGODB_URI` | Production, Preview, Development | Your MongoDB connection string |
| `WEBHOOK_SECRET` | Production, Preview, Development | Your webhook secret |

**Steps to configure in Vercel:**
1. Go to https://vercel.com/dashboard
2. Select your project
3. Click "Settings" tab
4. Click "Environment Variables"
5. Add each variable with appropriate scope

---

## MongoDB Atlas

### Connection String Format

```
mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>?retryWrites=true&w=majority
```

### Components

| Part | Description | Example |
|------|-------------|---------|
| `<username>` | Database user username | `tteuser` |
| `<password>` | Database user password (URL encoded) | `MyP%40ssw0rd` |
| `<cluster>` | Atlas cluster hostname | `cluster0.abc123` |
| `<database>` | Database name | `tte` |

### Password URL Encoding

Special characters in passwords must be URL encoded:

| Character | Encoded |
|-----------|---------|
| `@` | `%40` |
| `:` | `%3A` |
| `/` | `%2F` |
| `#` | `%23` |
| `?` | `%3F` |

**Example:**
- Password: `MyP@ss:word`
- Encoded: `MyP%40ss%3Aword`

---

## TradingView Webhook Configuration

### Webhook URLs

| Screener | Webhook URL |
|----------|-------------|
| TTE NWE Screener | `https://stock-buddy-app.vercel.app/api/nwe` |
| TTE OBDIV Screener | `https://stock-buddy-app.vercel.app/api/obdiv` |

### Alert Configuration

In TradingView alert settings:
- **Webhook URL**: Use URLs above
- **Message**: `{{alert.message}}`

### With Webhook Secret (Optional)

If using webhook authentication, include secret in Pine Script payload:

```pinescript
// Include secret in payload
buildPayload(sym, direction, timeframes) =>
    '{"secret":"' + WEBHOOK_SECRET + '","tier":"nwe","symbol":"' + sym + '",...}'
```

---

## Development vs Production

### Development Configuration

```env
# .env (TTE)
STOCK_BUDDY_API_URL=http://localhost:3000/api
LOG_LEVEL=DEBUG

# .env.local (Stock Buddy)
MONGODB_URI=mongodb+srv://...
NODE_ENV=development
```

### Production Configuration

```env
# .env (TTE)
STOCK_BUDDY_API_URL=https://stock-buddy-app.vercel.app/api
LOG_LEVEL=INFO

# Vercel Environment Variables
MONGODB_URI=mongodb+srv://...
NODE_ENV=production
WEBHOOK_SECRET=your-production-secret
```

---

## Security Best Practices

### Do's
- Use strong, unique passwords for MongoDB
- Use different credentials for development and production
- Rotate secrets periodically
- Use environment variables, never hardcode secrets

### Don'ts
- Never commit `.env` or `.env.local` files to git
- Never share credentials in plain text
- Never use production credentials in development
- Never expose MongoDB URI in client-side code

### .gitignore

Ensure these are in `.gitignore`:

```gitignore
# Environment files
.env
.env.local
.env.*.local

# Credentials
*.pem
*.key
credentials.json
```

---

## Troubleshooting

### "MONGODB_URI not defined"
- Check `.env.local` exists in Stock Buddy root
- Verify variable name is exactly `MONGODB_URI`
- Restart development server after adding

### "Connection refused" to Stock Buddy API
- Check `STOCK_BUDDY_API_URL` is correct
- Verify Stock Buddy is running (`npm run dev`)
- Check for typos in URL

### Chrome profile not found
- Verify `CHROME_PROFILE_PATH` exists
- Close all Chrome windows before running
- Check path uses forward slashes on Windows

### Webhook not received
- Verify webhook URL is HTTPS in production
- Check Vercel function logs for errors
- Test with curl to isolate issue

---

## Environment Variable Reference

### All Variables Summary

| Variable | Component | Required | Default |
|----------|-----------|----------|---------|
| `STOCK_BUDDY_API_URL` | TTE | Yes | - |
| `CHROME_PROFILE_PATH` | TTE | Yes | - |
| `LOG_LEVEL` | TTE | No | `INFO` |
| `POLL_INTERVAL` | TTE | No | `60` |
| `BATCH_SIZE` | TTE | No | `8` |
| `SELENIUM_IMPLICIT_WAIT` | TTE | No | `10` |
| `SELENIUM_EXPLICIT_WAIT` | TTE | No | `30` |
| `SCREENSHOT_WAIT` | TTE | No | `2` |
| `MONGODB_URI` | Stock Buddy | Yes | - |
| `WEBHOOK_SECRET` | Stock Buddy | No | - |
| `NODE_ENV` | Stock Buddy | No | `development` |

---

*Keep this document updated when adding new environment variables.*
