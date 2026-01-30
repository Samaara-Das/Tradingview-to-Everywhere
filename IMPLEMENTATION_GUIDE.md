# Implementation Guide
# TTE Tiered Screener Architecture

**Version**: 1.0
**Created**: 2026-01-29
**Audience**: Developers implementing the tiered screener system

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Project Setup](#2-project-setup)
3. [Phase 1: Symbol Selection](#3-phase-1-symbol-selection)
4. [Phase 2: TTE NWE Screener](#4-phase-2-tte-nwe-screener)
5. [Phase 3: TTE OBDIV Screener](#5-phase-3-tte-obdiv-screener)
6. [Phase 4: Stock Buddy API](#6-phase-4-stock-buddy-api)
7. [Phase 5: MongoDB Setup](#7-phase-5-mongodb-setup)
8. [Phase 6: Python Orchestrator](#8-phase-6-python-orchestrator)
9. [Phase 7: Stock Buddy Dashboard](#9-phase-7-stock-buddy-dashboard)
10. [Phase 8: Integration Testing](#10-phase-8-integration-testing)
11. [Phase 9: Production Deployment](#11-phase-9-production-deployment)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Prerequisites

### 1.1 Required Accounts

| Account | Purpose | Setup Link |
|---------|---------|------------|
| TradingView | Pine Script screeners | https://www.tradingview.com (Pro+ or higher for webhooks) |
| MongoDB Atlas | Database | https://www.mongodb.com/cloud/atlas |
| Vercel | Stock Buddy hosting | https://vercel.com |
| GitHub | Source control | https://github.com |

### 1.2 Required Software

```bash
# Node.js (v18 or higher)
node --version  # Should show v18.x.x or higher

# Python (v3.11 or higher)
python --version  # Should show 3.11.x or higher

# Git
git --version

# Chrome browser (for Selenium)
# Download from https://www.google.com/chrome/
```

### 1.3 Required Knowledge

- Pine Script v5 basics
- Next.js / React fundamentals
- Python and Selenium
- MongoDB queries
- REST API concepts

### 1.4 Project Repositories

```
tradingview-to-everywhere/     # This repo - Python orchestrator
stock-buddy/                   # Stock Buddy Next.js app (separate repo)
```

---

## 2. Project Setup

### 2.1 Clone and Setup TTE Repository

```bash
# Navigate to your work directory
cd ~/Work

# Clone the repository (if not already)
git clone <your-repo-url> tradingview-to-everywhere
cd tradingview-to-everywhere

# Create and activate virtual environment
pipenv install
pipenv shell

# Verify setup
python --version
pip list
```

### 2.2 Create Stock Buddy Repository (if not exists)

```bash
# Create new Next.js app
npx create-next-app@latest stock-buddy --typescript --tailwind --app --src-dir

# Navigate to project
cd stock-buddy

# Install additional dependencies
npm install @tanstack/react-query mongodb lucide-react recharts
npm install -D @types/node

# Verify setup
npm run dev
# Visit http://localhost:3000
```

### 2.3 Environment Files Setup

**TTE Repository (`.env`):**
```bash
# Create .env file
touch .env
```

```env
# Stock Buddy API
STOCK_BUDDY_API_URL=https://stock-buddy-app.vercel.app/api

# Chrome Profile (for Selenium)
CHROME_PROFILE_PATH=C:/Users/YourName/AppData/Local/Google/Chrome/User Data

# Logging
LOG_LEVEL=INFO
```

**Stock Buddy Repository (`.env.local`):**
```bash
# Create .env.local file
touch .env.local
```

```env
# MongoDB
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/tte?retryWrites=true&w=majority

# Webhook Security (generate random string)
WEBHOOK_SECRET=your-random-secret-here-min-32-chars

# Environment
NODE_ENV=development
```

### 2.4 Verification Checklist

- [ ] TTE repo cloned and pipenv working
- [ ] Stock Buddy repo created with Next.js
- [ ] Both .env files created
- [ ] `npm run dev` works for Stock Buddy
- [ ] `python main.py` runs without import errors in TTE

---

## 3. Phase 1: Symbol Selection

### 3.1 Objective
Finalize the 20 forex pairs for initial deployment.

### 3.2 Selected Symbols

Create a reference file for symbols:

**File: `resources/tier1_symbols.py`**

```python
"""
Tier 1 NWE Screener Symbols
20 forex pairs monitored for NWE zone entries
"""

TIER1_SYMBOLS = [
    # Batch 1 (1-10) - Major pairs
    "FX:EURUSD",   # 1. Euro / US Dollar
    "FX:GBPUSD",   # 2. British Pound / US Dollar
    "FX:USDJPY",   # 3. US Dollar / Japanese Yen
    "FX:USDCHF",   # 4. US Dollar / Swiss Franc
    "FX:AUDUSD",   # 5. Australian Dollar / US Dollar
    "FX:NZDUSD",   # 6. New Zealand Dollar / US Dollar
    "FX:USDCAD",   # 7. US Dollar / Canadian Dollar
    "FX:GBPJPY",   # 8. British Pound / Japanese Yen
    "FX:EURJPY",   # 9. Euro / Japanese Yen
    "FX:AUDJPY",   # 10. Australian Dollar / Japanese Yen

    # Batch 2 (11-20) - Cross pairs
    "FX:GBPAUD",   # 11. British Pound / Australian Dollar
    "FX:EURAUD",   # 12. Euro / Australian Dollar
    "FX:EURGBP",   # 13. Euro / British Pound
    "FX:EURCAD",   # 14. Euro / Canadian Dollar
    "FX:GBPCAD",   # 15. British Pound / Canadian Dollar
    "FX:AUDCAD",   # 16. Australian Dollar / Canadian Dollar
    "FX:NZDJPY",   # 17. New Zealand Dollar / Japanese Yen
    "FX:CADJPY",   # 18. Canadian Dollar / Japanese Yen
    "FX:CHFJPY",   # 19. Swiss Franc / Japanese Yen
    "FX:AUDNZD",   # 20. Australian Dollar / New Zealand Dollar
]

# Short names (without FX: prefix) for display
SYMBOL_NAMES = [s.replace("FX:", "") for s in TIER1_SYMBOLS]
```

### 3.3 Verification Checklist

- [ ] File created at `resources/tier1_symbols.py`
- [ ] 20 symbols listed
- [ ] All symbols use `FX:` prefix for TradingView

---

## 4. Phase 2: TTE NWE Screener

### 4.1 Objective
Create Pine Script indicator that monitors 20 symbols for NWE zone entries and fires webhooks.

### 4.2 Step-by-Step Instructions

#### Step 1: Create New Pine Script File

**File: `Pine Script Code/TTE NWE Screener v2.txt`**

```pinescript
// This file is for reference. Copy to TradingView Pine Editor.

//@version=5
indicator("TTE NWE Screener v2", overlay=false, max_bars_back=500)

// ============================================================================
// IMPORTS
// ============================================================================
import jdehorty/KernelFunctions/2 as kernels

// ============================================================================
// INPUTS - SYMBOLS (20)
// ============================================================================
s01 = input.symbol("FX:EURUSD", "Symbol 01")
s02 = input.symbol("FX:GBPUSD", "Symbol 02")
s03 = input.symbol("FX:USDJPY", "Symbol 03")
s04 = input.symbol("FX:USDCHF", "Symbol 04")
s05 = input.symbol("FX:AUDUSD", "Symbol 05")
s06 = input.symbol("FX:NZDUSD", "Symbol 06")
s07 = input.symbol("FX:USDCAD", "Symbol 07")
s08 = input.symbol("FX:GBPJPY", "Symbol 08")
s09 = input.symbol("FX:EURJPY", "Symbol 09")
s10 = input.symbol("FX:AUDJPY", "Symbol 10")
s11 = input.symbol("FX:GBPAUD", "Symbol 11")
s12 = input.symbol("FX:EURAUD", "Symbol 12")
s13 = input.symbol("FX:EURGBP", "Symbol 13")
s14 = input.symbol("FX:EURCAD", "Symbol 14")
s15 = input.symbol("FX:GBPCAD", "Symbol 15")
s16 = input.symbol("FX:AUDCAD", "Symbol 16")
s17 = input.symbol("FX:NZDJPY", "Symbol 17")
s18 = input.symbol("FX:CADJPY", "Symbol 18")
s19 = input.symbol("FX:CHFJPY", "Symbol 19")
s20 = input.symbol("FX:AUDNZD", "Symbol 20")

// ============================================================================
// INPUTS - NWE PARAMETERS
// ============================================================================
nwe_h = input.int(8, "NWE Bandwidth (h)", minval=1)
nwe_alpha = input.float(8.0, "NWE Alpha", minval=0.1)
nwe_x0 = input.int(25, "NWE x0", minval=1)
nwe_atrLen = input.int(60, "NWE ATR Length", minval=1)
nwe_nearFactor = input.float(1.5, "NWE Near Factor", minval=0.1)
nwe_farFactor = input.float(8.0, "NWE Far Factor", minval=0.1)

// ============================================================================
// FUNCTIONS
// ============================================================================

// Kernel ATR calculation
kernel_atr(length, yhat_high, yhat_low, yhat_close) =>
    tr = math.max(yhat_high - yhat_low, math.abs(yhat_high - yhat_close[1]), math.abs(yhat_low - yhat_close[1]))
    ta.sma(tr, length)

// NWE Zone Detection
// Returns: [isBullish, isBearish]
calcNWEZone() =>
    // Kernel regression
    float yhat_close = kernels.rationalQuadratic(close, nwe_h, nwe_alpha, nwe_x0)
    float yhat_high = kernels.rationalQuadratic(high, nwe_h, nwe_alpha, nwe_x0)
    float yhat_low = kernels.rationalQuadratic(low, nwe_h, nwe_alpha, nwe_x0)

    // Kernel ATR for bands
    float ktr = kernel_atr(nwe_atrLen, yhat_high, yhat_low, yhat_close)

    // Calculate zone boundaries
    float upper_far = yhat_close + nwe_farFactor * ktr
    float upper_near = yhat_close + nwe_nearFactor * ktr
    float upper_avg = (upper_far + upper_near) / 2
    float lower_near = yhat_close - nwe_nearFactor * ktr
    float lower_far = yhat_close - nwe_farFactor * ktr
    float lower_avg = (lower_far + lower_near) / 2

    // Zone overlap detection
    // Bullish: price overlaps lower zones
    bool nweBull = (low <= lower_near and high >= lower_avg) or (low <= lower_avg and high >= lower_far)
    // Bearish: price overlaps upper zones
    bool nweBear = (high >= upper_near and low <= upper_avg) or (high >= upper_avg and low <= upper_far)

    [nweBull, nweBear]

// Get clean symbol name (remove exchange prefix)
getSymbolName(sym) =>
    str.replace_all(sym, "FX:", "")

// Build timeframe array string
buildTfArray(hasH4, hasD1) =>
    string result = "["
    bool needComma = false
    if hasH4
        result := result + '"H4"'
        needComma := true
    if hasD1
        result := needComma ? result + ',"D1"' : result + '"D1"'
    result := result + "]"
    result

// Build webhook payload
buildPayload(sym, direction, tfArray) =>
    '{"tier":"nwe","symbol":"' + getSymbolName(sym) + '","direction":"' + direction + '","timeframes":' + tfArray + ',"timestamp":' + str.tostring(time) + '}'

// ============================================================================
// REQUEST.SECURITY CALLS (40 total: 20 symbols × 2 timeframes)
// ============================================================================

// Symbol 01
[bull01_h4, bear01_h4] = request.security(s01, "240", calcNWEZone())
[bull01_d1, bear01_d1] = request.security(s01, "D", calcNWEZone())

// Symbol 02
[bull02_h4, bear02_h4] = request.security(s02, "240", calcNWEZone())
[bull02_d1, bear02_d1] = request.security(s02, "D", calcNWEZone())

// Symbol 03
[bull03_h4, bear03_h4] = request.security(s03, "240", calcNWEZone())
[bull03_d1, bear03_d1] = request.security(s03, "D", calcNWEZone())

// Symbol 04
[bull04_h4, bear04_h4] = request.security(s04, "240", calcNWEZone())
[bull04_d1, bear04_d1] = request.security(s04, "D", calcNWEZone())

// Symbol 05
[bull05_h4, bear05_h4] = request.security(s05, "240", calcNWEZone())
[bull05_d1, bear05_d1] = request.security(s05, "D", calcNWEZone())

// Symbol 06
[bull06_h4, bear06_h4] = request.security(s06, "240", calcNWEZone())
[bull06_d1, bear06_d1] = request.security(s06, "D", calcNWEZone())

// Symbol 07
[bull07_h4, bear07_h4] = request.security(s07, "240", calcNWEZone())
[bull07_d1, bear07_d1] = request.security(s07, "D", calcNWEZone())

// Symbol 08
[bull08_h4, bear08_h4] = request.security(s08, "240", calcNWEZone())
[bull08_d1, bear08_d1] = request.security(s08, "D", calcNWEZone())

// Symbol 09
[bull09_h4, bear09_h4] = request.security(s09, "240", calcNWEZone())
[bull09_d1, bear09_d1] = request.security(s09, "D", calcNWEZone())

// Symbol 10
[bull10_h4, bear10_h4] = request.security(s10, "240", calcNWEZone())
[bull10_d1, bear10_d1] = request.security(s10, "D", calcNWEZone())

// Symbol 11
[bull11_h4, bear11_h4] = request.security(s11, "240", calcNWEZone())
[bull11_d1, bear11_d1] = request.security(s11, "D", calcNWEZone())

// Symbol 12
[bull12_h4, bear12_h4] = request.security(s12, "240", calcNWEZone())
[bull12_d1, bear12_d1] = request.security(s12, "D", calcNWEZone())

// Symbol 13
[bull13_h4, bear13_h4] = request.security(s13, "240", calcNWEZone())
[bull13_d1, bear13_d1] = request.security(s13, "D", calcNWEZone())

// Symbol 14
[bull14_h4, bear14_h4] = request.security(s14, "240", calcNWEZone())
[bull14_d1, bear14_d1] = request.security(s14, "D", calcNWEZone())

// Symbol 15
[bull15_h4, bear15_h4] = request.security(s15, "240", calcNWEZone())
[bull15_d1, bear15_d1] = request.security(s15, "D", calcNWEZone())

// Symbol 16
[bull16_h4, bear16_h4] = request.security(s16, "240", calcNWEZone())
[bull16_d1, bear16_d1] = request.security(s16, "D", calcNWEZone())

// Symbol 17
[bull17_h4, bear17_h4] = request.security(s17, "240", calcNWEZone())
[bull17_d1, bear17_d1] = request.security(s17, "D", calcNWEZone())

// Symbol 18
[bull18_h4, bear18_h4] = request.security(s18, "240", calcNWEZone())
[bull18_d1, bear18_d1] = request.security(s18, "D", calcNWEZone())

// Symbol 19
[bull19_h4, bear19_h4] = request.security(s19, "240", calcNWEZone())
[bull19_d1, bear19_d1] = request.security(s19, "D", calcNWEZone())

// Symbol 20
[bull20_h4, bear20_h4] = request.security(s20, "240", calcNWEZone())
[bull20_d1, bear20_d1] = request.security(s20, "D", calcNWEZone())

// ============================================================================
// STATE TRACKING (persist across bars)
// ============================================================================
var bool prevBull01 = false, var bool prevBear01 = false
var bool prevBull02 = false, var bool prevBear02 = false
var bool prevBull03 = false, var bool prevBear03 = false
var bool prevBull04 = false, var bool prevBear04 = false
var bool prevBull05 = false, var bool prevBear05 = false
var bool prevBull06 = false, var bool prevBear06 = false
var bool prevBull07 = false, var bool prevBear07 = false
var bool prevBull08 = false, var bool prevBear08 = false
var bool prevBull09 = false, var bool prevBear09 = false
var bool prevBull10 = false, var bool prevBear10 = false
var bool prevBull11 = false, var bool prevBear11 = false
var bool prevBull12 = false, var bool prevBear12 = false
var bool prevBull13 = false, var bool prevBear13 = false
var bool prevBull14 = false, var bool prevBear14 = false
var bool prevBull15 = false, var bool prevBear15 = false
var bool prevBull16 = false, var bool prevBear16 = false
var bool prevBull17 = false, var bool prevBear17 = false
var bool prevBull18 = false, var bool prevBear18 = false
var bool prevBull19 = false, var bool prevBear19 = false
var bool prevBull20 = false, var bool prevBear20 = false

// ============================================================================
// CURRENT STATE CALCULATION
// ============================================================================
bool currBull01 = bull01_h4 or bull01_d1, bool currBear01 = bear01_h4 or bear01_d1
bool currBull02 = bull02_h4 or bull02_d1, bool currBear02 = bear02_h4 or bear02_d1
bool currBull03 = bull03_h4 or bull03_d1, bool currBear03 = bear03_h4 or bear03_d1
bool currBull04 = bull04_h4 or bull04_d1, bool currBear04 = bear04_h4 or bear04_d1
bool currBull05 = bull05_h4 or bull05_d1, bool currBear05 = bear05_h4 or bear05_d1
bool currBull06 = bull06_h4 or bull06_d1, bool currBear06 = bear06_h4 or bear06_d1
bool currBull07 = bull07_h4 or bull07_d1, bool currBear07 = bear07_h4 or bear07_d1
bool currBull08 = bull08_h4 or bull08_d1, bool currBear08 = bear08_h4 or bear08_d1
bool currBull09 = bull09_h4 or bull09_d1, bool currBear09 = bear09_h4 or bear09_d1
bool currBull10 = bull10_h4 or bull10_d1, bool currBear10 = bear10_h4 or bear10_d1
bool currBull11 = bull11_h4 or bull11_d1, bool currBear11 = bear11_h4 or bear11_d1
bool currBull12 = bull12_h4 or bull12_d1, bool currBear12 = bear12_h4 or bear12_d1
bool currBull13 = bull13_h4 or bull13_d1, bool currBear13 = bear13_h4 or bear13_d1
bool currBull14 = bull14_h4 or bull14_d1, bool currBear14 = bear14_h4 or bear14_d1
bool currBull15 = bull15_h4 or bull15_d1, bool currBear15 = bear15_h4 or bear15_d1
bool currBull16 = bull16_h4 or bull16_d1, bool currBear16 = bear16_h4 or bear16_d1
bool currBull17 = bull17_h4 or bull17_d1, bool currBear17 = bear17_h4 or bear17_d1
bool currBull18 = bull18_h4 or bull18_d1, bool currBear18 = bear18_h4 or bear18_d1
bool currBull19 = bull19_h4 or bull19_d1, bool currBear19 = bear19_h4 or bear19_d1
bool currBull20 = bull20_h4 or bull20_d1, bool currBear20 = bear20_h4 or bear20_d1

// ============================================================================
// ALERT LOGIC (fire on state change only)
// ============================================================================
if barstate.isconfirmed
    // Symbol 01
    if currBull01 and not prevBull01
        alert(buildPayload(s01, "bullish", buildTfArray(bull01_h4, bull01_d1)), alert.freq_once_per_bar_close)
    if currBear01 and not prevBear01
        alert(buildPayload(s01, "bearish", buildTfArray(bear01_h4, bear01_d1)), alert.freq_once_per_bar_close)
    prevBull01 := currBull01, prevBear01 := currBear01

    // Symbol 02
    if currBull02 and not prevBull02
        alert(buildPayload(s02, "bullish", buildTfArray(bull02_h4, bull02_d1)), alert.freq_once_per_bar_close)
    if currBear02 and not prevBear02
        alert(buildPayload(s02, "bearish", buildTfArray(bear02_h4, bear02_d1)), alert.freq_once_per_bar_close)
    prevBull02 := currBull02, prevBear02 := currBear02

    // Symbol 03
    if currBull03 and not prevBull03
        alert(buildPayload(s03, "bullish", buildTfArray(bull03_h4, bull03_d1)), alert.freq_once_per_bar_close)
    if currBear03 and not prevBear03
        alert(buildPayload(s03, "bearish", buildTfArray(bear03_h4, bear03_d1)), alert.freq_once_per_bar_close)
    prevBull03 := currBull03, prevBear03 := currBear03

    // Symbol 04
    if currBull04 and not prevBull04
        alert(buildPayload(s04, "bullish", buildTfArray(bull04_h4, bull04_d1)), alert.freq_once_per_bar_close)
    if currBear04 and not prevBear04
        alert(buildPayload(s04, "bearish", buildTfArray(bear04_h4, bear04_d1)), alert.freq_once_per_bar_close)
    prevBull04 := currBull04, prevBear04 := currBear04

    // Symbol 05
    if currBull05 and not prevBull05
        alert(buildPayload(s05, "bullish", buildTfArray(bull05_h4, bull05_d1)), alert.freq_once_per_bar_close)
    if currBear05 and not prevBear05
        alert(buildPayload(s05, "bearish", buildTfArray(bear05_h4, bear05_d1)), alert.freq_once_per_bar_close)
    prevBull05 := currBull05, prevBear05 := currBear05

    // Symbol 06-20: Same pattern (abbreviated for space)
    // ... repeat for symbols 06-20 ...

    // Symbol 06
    if currBull06 and not prevBull06
        alert(buildPayload(s06, "bullish", buildTfArray(bull06_h4, bull06_d1)), alert.freq_once_per_bar_close)
    if currBear06 and not prevBear06
        alert(buildPayload(s06, "bearish", buildTfArray(bear06_h4, bear06_d1)), alert.freq_once_per_bar_close)
    prevBull06 := currBull06, prevBear06 := currBear06

    // Symbol 07
    if currBull07 and not prevBull07
        alert(buildPayload(s07, "bullish", buildTfArray(bull07_h4, bull07_d1)), alert.freq_once_per_bar_close)
    if currBear07 and not prevBear07
        alert(buildPayload(s07, "bearish", buildTfArray(bear07_h4, bear07_d1)), alert.freq_once_per_bar_close)
    prevBull07 := currBull07, prevBear07 := currBear07

    // Symbol 08
    if currBull08 and not prevBull08
        alert(buildPayload(s08, "bullish", buildTfArray(bull08_h4, bull08_d1)), alert.freq_once_per_bar_close)
    if currBear08 and not prevBear08
        alert(buildPayload(s08, "bearish", buildTfArray(bear08_h4, bear08_d1)), alert.freq_once_per_bar_close)
    prevBull08 := currBull08, prevBear08 := currBear08

    // Symbol 09
    if currBull09 and not prevBull09
        alert(buildPayload(s09, "bullish", buildTfArray(bull09_h4, bull09_d1)), alert.freq_once_per_bar_close)
    if currBear09 and not prevBear09
        alert(buildPayload(s09, "bearish", buildTfArray(bear09_h4, bear09_d1)), alert.freq_once_per_bar_close)
    prevBull09 := currBull09, prevBear09 := currBear09

    // Symbol 10
    if currBull10 and not prevBull10
        alert(buildPayload(s10, "bullish", buildTfArray(bull10_h4, bull10_d1)), alert.freq_once_per_bar_close)
    if currBear10 and not prevBear10
        alert(buildPayload(s10, "bearish", buildTfArray(bear10_h4, bear10_d1)), alert.freq_once_per_bar_close)
    prevBull10 := currBull10, prevBear10 := currBear10

    // Symbol 11
    if currBull11 and not prevBull11
        alert(buildPayload(s11, "bullish", buildTfArray(bull11_h4, bull11_d1)), alert.freq_once_per_bar_close)
    if currBear11 and not prevBear11
        alert(buildPayload(s11, "bearish", buildTfArray(bear11_h4, bear11_d1)), alert.freq_once_per_bar_close)
    prevBull11 := currBull11, prevBear11 := currBear11

    // Symbol 12
    if currBull12 and not prevBull12
        alert(buildPayload(s12, "bullish", buildTfArray(bull12_h4, bull12_d1)), alert.freq_once_per_bar_close)
    if currBear12 and not prevBear12
        alert(buildPayload(s12, "bearish", buildTfArray(bear12_h4, bear12_d1)), alert.freq_once_per_bar_close)
    prevBull12 := currBull12, prevBear12 := currBear12

    // Symbol 13
    if currBull13 and not prevBull13
        alert(buildPayload(s13, "bullish", buildTfArray(bull13_h4, bull13_d1)), alert.freq_once_per_bar_close)
    if currBear13 and not prevBear13
        alert(buildPayload(s13, "bearish", buildTfArray(bear13_h4, bear13_d1)), alert.freq_once_per_bar_close)
    prevBull13 := currBull13, prevBear13 := currBear13

    // Symbol 14
    if currBull14 and not prevBull14
        alert(buildPayload(s14, "bullish", buildTfArray(bull14_h4, bull14_d1)), alert.freq_once_per_bar_close)
    if currBear14 and not prevBear14
        alert(buildPayload(s14, "bearish", buildTfArray(bear14_h4, bear14_d1)), alert.freq_once_per_bar_close)
    prevBull14 := currBull14, prevBear14 := currBear14

    // Symbol 15
    if currBull15 and not prevBull15
        alert(buildPayload(s15, "bullish", buildTfArray(bull15_h4, bull15_d1)), alert.freq_once_per_bar_close)
    if currBear15 and not prevBear15
        alert(buildPayload(s15, "bearish", buildTfArray(bear15_h4, bear15_d1)), alert.freq_once_per_bar_close)
    prevBull15 := currBull15, prevBear15 := currBear15

    // Symbol 16
    if currBull16 and not prevBull16
        alert(buildPayload(s16, "bullish", buildTfArray(bull16_h4, bull16_d1)), alert.freq_once_per_bar_close)
    if currBear16 and not prevBear16
        alert(buildPayload(s16, "bearish", buildTfArray(bear16_h4, bear16_d1)), alert.freq_once_per_bar_close)
    prevBull16 := currBull16, prevBear16 := currBear16

    // Symbol 17
    if currBull17 and not prevBull17
        alert(buildPayload(s17, "bullish", buildTfArray(bull17_h4, bull17_d1)), alert.freq_once_per_bar_close)
    if currBear17 and not prevBear17
        alert(buildPayload(s17, "bearish", buildTfArray(bear17_h4, bear17_d1)), alert.freq_once_per_bar_close)
    prevBull17 := currBull17, prevBear17 := currBear17

    // Symbol 18
    if currBull18 and not prevBull18
        alert(buildPayload(s18, "bullish", buildTfArray(bull18_h4, bull18_d1)), alert.freq_once_per_bar_close)
    if currBear18 and not prevBear18
        alert(buildPayload(s18, "bearish", buildTfArray(bear18_h4, bear18_d1)), alert.freq_once_per_bar_close)
    prevBull18 := currBull18, prevBear18 := currBear18

    // Symbol 19
    if currBull19 and not prevBull19
        alert(buildPayload(s19, "bullish", buildTfArray(bull19_h4, bull19_d1)), alert.freq_once_per_bar_close)
    if currBear19 and not prevBear19
        alert(buildPayload(s19, "bearish", buildTfArray(bear19_h4, bear19_d1)), alert.freq_once_per_bar_close)
    prevBull19 := currBull19, prevBear19 := currBear19

    // Symbol 20
    if currBull20 and not prevBull20
        alert(buildPayload(s20, "bullish", buildTfArray(bull20_h4, bull20_d1)), alert.freq_once_per_bar_close)
    if currBear20 and not prevBear20
        alert(buildPayload(s20, "bearish", buildTfArray(bear20_h4, bear20_d1)), alert.freq_once_per_bar_close)
    prevBull20 := currBull20, prevBear20 := currBear20

// ============================================================================
// DEBUG TABLE (optional - shows current state)
// ============================================================================
var table debugTable = table.new(position.top_right, 3, 22, bgcolor=color.black)

if barstate.islast
    table.cell(debugTable, 0, 0, "Symbol", text_color=color.white)
    table.cell(debugTable, 1, 0, "Bull", text_color=color.white)
    table.cell(debugTable, 2, 0, "Bear", text_color=color.white)

    table.cell(debugTable, 0, 1, getSymbolName(s01), text_color=color.white)
    table.cell(debugTable, 1, 1, currBull01 ? "YES" : "-", text_color=currBull01 ? color.green : color.gray)
    table.cell(debugTable, 2, 1, currBear01 ? "YES" : "-", text_color=currBear01 ? color.red : color.gray)

    // ... repeat for remaining symbols ...
```

#### Step 2: Add to TradingView

1. Open TradingView
2. Go to Pine Editor (bottom panel)
3. Click "New" → "New indicator"
4. Paste the code above
5. Click "Save" and name it "TTE NWE Screener v2"
6. Click "Add to Chart"

#### Step 3: Configure Webhook Alert

1. Right-click on the indicator in the chart legend
2. Select "Add Alert..."
3. Configure:
   - **Condition**: "TTE NWE Screener v2" → "Any alert() function call"
   - **Options**: "Once Per Bar Close"
   - **Alert actions**: Check "Webhook URL"
   - **Webhook URL**: `https://stock-buddy-app.vercel.app/api/nwe`
   - **Message**: `{{alert.message}}`
4. Click "Create"

#### Step 4: Test the Alert

1. Open browser developer tools (F12)
2. Wait for a bar to close with NWE signal
3. Check TradingView alerts log
4. Verify webhook fired (check Stock Buddy logs)

### 4.3 Verification Checklist

- [ ] Pine Script compiles without errors
- [ ] Indicator shows on chart
- [ ] Debug table displays symbol states
- [ ] Alert created with webhook URL
- [ ] Test webhook received at API (use ngrok for local testing)

---

## 5. Phase 3: TTE OBDIV Screener

### 5.1 Objective
Create Pine Script indicator that checks OB and Divergence for 8 dynamically-set symbols.

### 5.2 Key Differences from TTE Screener

| Aspect | Original TTE Screener | TTE OBDIV Screener |
|--------|----------------------|---------------------|
| NWE Calculation | Yes | **Removed** |
| Table Display | Yes | **Removed** |
| Symbols | Fixed | **Dynamic** (set by Python) |
| Direction Output | Single | **Both** (bull + bear) |

### 5.3 Step-by-Step Instructions

#### Step 1: Create Pine Script File

**File: `Pine Script Code/TTE OBDIV Screener.txt`**

```pinescript
//@version=5
indicator("TTE OBDIV Screener", overlay=false, max_bars_back=500)

// ============================================================================
// IMPORTS
// ============================================================================
import jdehorty/KernelFunctions/2 as kernels

// ============================================================================
// INPUTS - SYMBOLS (8 dynamic)
// ============================================================================
s01 = input.symbol("FX:EURUSD", "Symbol 01")
s02 = input.symbol("FX:GBPUSD", "Symbol 02")
s03 = input.symbol("FX:USDJPY", "Symbol 03")
s04 = input.symbol("FX:USDCHF", "Symbol 04")
s05 = input.symbol("FX:AUDUSD", "Symbol 05")
s06 = input.symbol("FX:NZDUSD", "Symbol 06")
s07 = input.symbol("FX:USDCAD", "Symbol 07")
s08 = input.symbol("FX:GBPJPY", "Symbol 08")

// ============================================================================
// INPUTS - OB PARAMETERS
// ============================================================================
ob_lookback = input.int(50, "OB Lookback", minval=10)
ob_mitDepth = input.int(100, "OB Mitigation Depth", minval=10)

// ============================================================================
// INPUTS - DIVERGENCE PARAMETERS
// ============================================================================
div_fastH = input.int(5, "DIV Fast Kernel H", minval=1)
div_fastAlpha = input.float(8.0, "DIV Fast Alpha")
div_fastX0 = input.int(25, "DIV Fast x0")
div_slowH = input.int(34, "DIV Slow Kernel H", minval=1)
div_slowAlpha = input.float(3.0, "DIV Slow Alpha")
div_slowX0 = input.int(120, "DIV Slow x0")

// ============================================================================
// OB/FVG DETECTION FUNCTIONS
// ============================================================================
// (Copy from existing TTE Screener - detectOB, detectFVG functions)
// Returns: [bullOB, bearOB, bullFVG, bearFVG, breakerSupport, breakerResistance, type, tf]

detectOBFVG() =>
    // ... OB/FVG detection logic from TTE Screener ...
    // Simplified for brevity - copy from existing code

    bool bullOB = false
    bool bearOB = false
    bool bullFVG = false
    bool bearFVG = false
    bool breakerSupport = false
    bool breakerResistance = false
    string obType = ""

    // ... detection logic ...

    [bullOB, bearOB, bullFVG, bearFVG, breakerSupport, breakerResistance, obType]

// ============================================================================
// DIVERGENCE DETECTION FUNCTIONS
// ============================================================================
// (Copy from existing TTE Screener - divergence detection)
// Returns: [bullDiv, bearDiv, divType]

detectDivergence() =>
    // ... Divergence detection logic from TTE Screener ...

    bool bullDiv = false
    bool bearDiv = false
    string divType = ""

    // ... detection logic ...

    [bullDiv, bearDiv, divType]

// ============================================================================
// COMBINED CHECK FUNCTION
// ============================================================================
checkOBDIV() =>
    [bullOB, bearOB, bullFVG, bearFVG, brkSupp, brkRes, obType] = detectOBFVG()
    [bullDiv, bearDiv, divType] = detectDivergence()

    // Combine OB results
    bool hasBullOB = bullOB or bullFVG or brkSupp
    bool hasBearOB = bearOB or bearFVG or brkRes

    [hasBullOB, hasBearOB, bullDiv, bearDiv, obType, divType]

// ============================================================================
// REQUEST.SECURITY CALLS
// ============================================================================
// Per symbol: 5 calls (H4, D1, W1 for OB; H4, D1 for DIV)
// Total: 8 symbols × 5 = 40 calls

// Symbol 01
[bullOB01_h4, bearOB01_h4, bullDiv01_h4, bearDiv01_h4, obType01_h4, divType01_h4] = request.security(s01, "240", checkOBDIV())
[bullOB01_d1, bearOB01_d1, bullDiv01_d1, bearDiv01_d1, obType01_d1, divType01_d1] = request.security(s01, "D", checkOBDIV())
[bullOB01_w1, bearOB01_w1, _, _, obType01_w1, _] = request.security(s01, "W", checkOBDIV())

// ... repeat for symbols 02-08 ...

// ============================================================================
// PAYLOAD BUILDING
// ============================================================================
getSymbolName(sym) =>
    str.replace_all(sym, "FX:", "")

buildObObject(found, tf, obType) =>
    found ? '{"found":true,"tf":"' + tf + '","type":"' + obType + '"}' : '{"found":false}'

buildDivObject(found, tf, divType) =>
    found ? '{"found":true,"tf":"' + tf + '","type":"' + divType + '"}' : '{"found":false}'

buildPayload(sym, bullOB_h4, bullOB_d1, bullOB_w1, bullDiv_h4, bullDiv_d1, bearOB_h4, bearOB_d1, bearOB_w1, bearDiv_h4, bearDiv_d1, obType_h4, obType_d1, obType_w1, divType_h4, divType_d1) =>
    // Find best timeframe for each
    string bullObTf = bullOB_w1 ? "W1" : (bullOB_d1 ? "D1" : (bullOB_h4 ? "H4" : ""))
    string bullObType = bullOB_w1 ? obType_w1 : (bullOB_d1 ? obType_d1 : obType_h4)
    string bullDivTf = bullDiv_d1 ? "D1" : (bullDiv_h4 ? "H4" : "")
    string bullDivType = bullDiv_d1 ? divType_d1 : divType_h4

    string bearObTf = bearOB_w1 ? "W1" : (bearOB_d1 ? "D1" : (bearOB_h4 ? "H4" : ""))
    string bearObType = bearOB_w1 ? obType_w1 : (bearOB_d1 ? obType_d1 : obType_h4)
    string bearDivTf = bearDiv_d1 ? "D1" : (bearDiv_h4 ? "H4" : "")
    string bearDivType = bearDiv_d1 ? divType_d1 : divType_h4

    bool hasBullOB = bullOB_h4 or bullOB_d1 or bullOB_w1
    bool hasBullDiv = bullDiv_h4 or bullDiv_d1
    bool hasBearOB = bearOB_h4 or bearOB_d1 or bearOB_w1
    bool hasBearDiv = bearDiv_h4 or bearDiv_d1

    '{"tier":"obdiv","symbol":"' + getSymbolName(sym) + '",' +
    '"bull_ob":' + buildObObject(hasBullOB, bullObTf, bullObType) + ',' +
    '"bull_div":' + buildDivObject(hasBullDiv, bullDivTf, bullDivType) + ',' +
    '"bear_ob":' + buildObObject(hasBearOB, bearObTf, bearObType) + ',' +
    '"bear_div":' + buildDivObject(hasBearDiv, bearDivTf, bearDivType) + ',' +
    '"timestamp":' + str.tostring(time) + '}'

// ============================================================================
// ALERT LOGIC
// ============================================================================
if barstate.isconfirmed
    // Always fire for all symbols (Python will match direction)
    alert(buildPayload(s01, bullOB01_h4, bullOB01_d1, bullOB01_w1, bullDiv01_h4, bullDiv01_d1, bearOB01_h4, bearOB01_d1, bearOB01_w1, bearDiv01_h4, bearDiv01_d1, obType01_h4, obType01_d1, obType01_w1, divType01_h4, divType01_d1), alert.freq_once_per_bar_close)
    // ... repeat for symbols 02-08 ...
```

#### Step 2: Add to TradingView

1. Open Pine Editor
2. Create new indicator with the code
3. Save as "TTE OBDIV Screener"
4. Add to chart

#### Step 3: Configure Webhook Alert

Same process as NWE Screener, but webhook URL: `https://stock-buddy-app.vercel.app/api/obdiv`

### 5.4 Verification Checklist

- [ ] Pine Script compiles without errors
- [ ] No NWE calculation in code
- [ ] No table display
- [ ] Reports both bullish and bearish findings
- [ ] Alert configured with webhook

---

## 6. Phase 4: Stock Buddy API

### 6.1 Objective
Create 5 API endpoints for webhook reception and dashboard data.

### 6.2 Step-by-Step Instructions

#### Step 1: Set Up MongoDB Client

**File: `src/lib/mongodb.ts`**

```typescript
import { MongoClient } from 'mongodb';

if (!process.env.MONGODB_URI) {
  throw new Error('Please add MONGODB_URI to .env.local');
}

const uri = process.env.MONGODB_URI;
const options = {};

let client: MongoClient;
let clientPromise: Promise<MongoClient>;

if (process.env.NODE_ENV === 'development') {
  // Use global variable to preserve connection across hot reloads
  let globalWithMongo = global as typeof globalThis & {
    _mongoClientPromise?: Promise<MongoClient>;
  };

  if (!globalWithMongo._mongoClientPromise) {
    client = new MongoClient(uri, options);
    globalWithMongo._mongoClientPromise = client.connect();
  }
  clientPromise = globalWithMongo._mongoClientPromise;
} else {
  client = new MongoClient(uri, options);
  clientPromise = client.connect();
}

export default clientPromise;
```

#### Step 2: Create NWE Endpoint

**File: `src/app/api/nwe/route.ts`**

```typescript
import { NextRequest, NextResponse } from 'next/server';
import clientPromise from '@/lib/mongodb';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { tier, symbol, direction, timeframes, timestamp } = body;

    // Validation
    if (tier !== 'nwe') {
      return NextResponse.json(
        { success: false, error: 'Invalid tier', code: 'INVALID_TIER' },
        { status: 400 }
      );
    }

    if (!symbol || !direction) {
      return NextResponse.json(
        { success: false, error: 'Missing required fields', code: 'MISSING_FIELD' },
        { status: 400 }
      );
    }

    if (!['bullish', 'bearish'].includes(direction)) {
      return NextResponse.json(
        { success: false, error: 'Invalid direction', code: 'INVALID_DIRECTION' },
        { status: 400 }
      );
    }

    const client = await clientPromise;
    const db = client.db('tte');

    const result = await db.collection('hot_list').updateOne(
      { symbol },
      {
        $set: {
          symbol,
          direction,
          nwe_timeframes: timeframes || [],
          nwe_timestamp: timestamp || Math.floor(Date.now() / 1000),
          status: 'pending_tier2',
          updated_at: new Date(),
        },
      },
      { upsert: true }
    );

    const action = result.upsertedCount > 0 ? 'inserted' : 'updated';

    console.log(`[NWE] ${action} hot_list: ${symbol} (${direction})`);

    return NextResponse.json({
      success: true,
      action,
      symbol,
    });
  } catch (error) {
    console.error('[NWE] Error:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error', code: 'DB_ERROR' },
      { status: 500 }
    );
  }
}
```

#### Step 3: Create OBDIV Endpoint

**File: `src/app/api/obdiv/route.ts`**

```typescript
import { NextRequest, NextResponse } from 'next/server';
import clientPromise from '@/lib/mongodb';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { symbol, bull_ob, bull_div, bear_ob, bear_div, timestamp } = body;

    const client = await clientPromise;
    const db = client.db('tte');

    // Find hot symbol to get NWE direction
    const hotSymbol = await db.collection('hot_list').findOne({
      symbol,
      status: { $in: ['pending_tier2', 'tier2_complete'] },
    });

    if (!hotSymbol) {
      console.log(`[OBDIV] ${symbol} not in hot_list, ignoring`);
      return NextResponse.json({
        success: true,
        signal_created: false,
        reason: 'not_in_hot_list',
      });
    }

    // Match direction from hot list
    const isBullish = hotSymbol.direction === 'bullish';
    const ob = isBullish ? bull_ob : bear_ob;
    const div = isBullish ? bull_div : bear_div;

    // Calculate signal level
    let level = 1; // NWE only
    if (ob?.found) level = 2; // NWE + OB
    if (ob?.found && div?.found) level = 3; // NWE + OB + DIV

    // Create signal
    const signal = {
      symbol,
      direction: hotSymbol.direction,
      level,
      nwe_tf: hotSymbol.nwe_timeframes,
      ob_tf: ob?.tf || null,
      ob_type: ob?.type || null,
      div_tf: div?.tf || null,
      div_type: div?.type || null,
      timestamp: timestamp || Math.floor(Date.now() / 1000),
      screenshot_url: null,
      status: 'pending_screenshot',
      created_at: new Date(),
    };

    const result = await db.collection('signals').insertOne(signal);

    // Update hot_list status
    await db.collection('hot_list').updateOne(
      { symbol },
      { $set: { status: 'tier2_complete', last_checked: new Date() } }
    );

    console.log(`[OBDIV] Created Level ${level} signal: ${symbol} (${hotSymbol.direction})`);

    return NextResponse.json({
      success: true,
      signal_created: true,
      signal_id: result.insertedId.toString(),
      level,
      direction: hotSymbol.direction,
    });
  } catch (error) {
    console.error('[OBDIV] Error:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

#### Step 4: Create Signals Endpoint

**File: `src/app/api/signals/route.ts`**

```typescript
import { NextRequest, NextResponse } from 'next/server';
import clientPromise from '@/lib/mongodb';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);

    const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 100);
    const offset = parseInt(searchParams.get('offset') || '0');
    const level = searchParams.get('level');
    const direction = searchParams.get('direction');
    const status = searchParams.get('status');
    const symbol = searchParams.get('symbol');
    const sort = searchParams.get('sort') || 'created_at';
    const order = searchParams.get('order') || 'desc';

    const client = await clientPromise;
    const db = client.db('tte');

    // Build query
    const query: any = {};
    if (level) query.level = parseInt(level);
    if (direction) query.direction = direction;
    if (status) query.status = status;
    if (symbol) query.symbol = { $regex: symbol, $options: 'i' };

    // Build sort
    const sortObj: any = {};
    sortObj[sort] = order === 'asc' ? 1 : -1;

    // Execute query
    const [signals, total] = await Promise.all([
      db.collection('signals')
        .find(query)
        .sort(sortObj)
        .skip(offset)
        .limit(limit)
        .toArray(),
      db.collection('signals').countDocuments(query),
    ]);

    return NextResponse.json({
      success: true,
      data: signals,
      pagination: {
        total,
        limit,
        offset,
        hasMore: offset + signals.length < total,
      },
    });
  } catch (error) {
    console.error('[SIGNALS] Error:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

#### Step 5: Create Signal Update Endpoint

**File: `src/app/api/signals/[id]/route.ts`**

```typescript
import { NextRequest, NextResponse } from 'next/server';
import clientPromise from '@/lib/mongodb';
import { ObjectId } from 'mongodb';

export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json();
    const { screenshot_url, status } = body;

    const client = await clientPromise;
    const db = client.db('tte');

    const updateDoc: any = { updated_at: new Date() };
    if (screenshot_url !== undefined) updateDoc.screenshot_url = screenshot_url;
    if (status !== undefined) updateDoc.status = status;

    const result = await db.collection('signals').updateOne(
      { _id: new ObjectId(params.id) },
      { $set: updateDoc }
    );

    if (result.matchedCount === 0) {
      return NextResponse.json(
        { success: false, error: 'Signal not found', code: 'NOT_FOUND' },
        { status: 404 }
      );
    }

    console.log(`[SIGNALS] Updated ${params.id}: ${JSON.stringify(updateDoc)}`);

    return NextResponse.json({
      success: true,
      updated: true,
      signal_id: params.id,
    });
  } catch (error) {
    console.error('[SIGNALS] Update error:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

#### Step 6: Create Hot Symbols Endpoint

**File: `src/app/api/hot-symbols/route.ts`**

```typescript
import { NextRequest, NextResponse } from 'next/server';
import clientPromise from '@/lib/mongodb';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const status = searchParams.get('status') || 'pending_tier2';
    const limit = Math.min(parseInt(searchParams.get('limit') || '8'), 20);

    const client = await clientPromise;
    const db = client.db('tte');

    const hotSymbols = await db.collection('hot_list')
      .find({ status })
      .sort({ updated_at: -1 })
      .limit(limit)
      .toArray();

    return NextResponse.json({
      success: true,
      data: hotSymbols,
      count: hotSymbols.length,
    });
  } catch (error) {
    console.error('[HOT-SYMBOLS] Error:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

#### Step 7: Test Endpoints Locally

```bash
# Start dev server
cd stock-buddy
npm run dev

# Test NWE endpoint
curl -X POST http://localhost:3000/api/nwe \
  -H "Content-Type: application/json" \
  -d '{"tier":"nwe","symbol":"GBPAUD","direction":"bullish","timeframes":["H4","D1"]}'

# Test signals endpoint
curl http://localhost:3000/api/signals

# Test hot-symbols endpoint
curl http://localhost:3000/api/hot-symbols
```

### 6.3 Verification Checklist

- [ ] All 5 API files created
- [ ] MongoDB client configured
- [ ] POST /api/nwe returns success
- [ ] POST /api/obdiv creates signal
- [ ] GET /api/signals returns array
- [ ] PATCH /api/signals/[id] updates signal
- [ ] GET /api/hot-symbols returns pending symbols

---

## 7. Phase 5: MongoDB Setup

### 7.1 Objective
Create database collections with proper indexes.

### 7.2 Step-by-Step Instructions

#### Step 1: Create MongoDB Atlas Cluster

1. Go to https://www.mongodb.com/cloud/atlas
2. Create account or sign in
3. Create new cluster (free tier is fine for development)
4. Create database user with password
5. Add your IP to allowed list (or 0.0.0.0/0 for all)
6. Get connection string

#### Step 2: Create Database and Collections

```bash
# Connect via mongosh or MongoDB Compass
mongosh "mongodb+srv://cluster.mongodb.net/tte" --username <user>

# Create collections
use tte
db.createCollection("hot_list")
db.createCollection("signals")
```

#### Step 3: Create Indexes

```javascript
// hot_list indexes
db.hot_list.createIndex({ symbol: 1 }, { unique: true })
db.hot_list.createIndex({ status: 1, updated_at: -1 })

// Optional: TTL index for auto-expiry (24 hours)
db.hot_list.createIndex({ updated_at: 1 }, { expireAfterSeconds: 86400 })

// signals indexes
db.signals.createIndex({ created_at: -1 })
db.signals.createIndex({ status: 1 })
db.signals.createIndex({ level: 1 })
db.signals.createIndex({ symbol: 1 })
db.signals.createIndex({ direction: 1 })
```

#### Step 4: Verify Indexes

```javascript
// Check indexes
db.hot_list.getIndexes()
db.signals.getIndexes()
```

### 7.3 Verification Checklist

- [ ] MongoDB Atlas cluster created
- [ ] Database `tte` created
- [ ] Collections `hot_list` and `signals` created
- [ ] All indexes created
- [ ] Connection string added to .env.local

---

## 8. Phase 6: Python Orchestrator

### 8.1 Objective
Update Python orchestrator for webhook-based flow.

### 8.2 Step-by-Step Instructions

#### Step 1: Create Orchestrator Module

**File: `tiered_orchestrator.py`**

```python
"""
TTE Tiered Orchestrator
Polls Stock Buddy API for hot symbols, updates OBDIV screener, captures screenshots.
"""

import os
import time
import logging
from dataclasses import dataclass
from typing import List, Optional

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class HotSymbol:
    """Represents a symbol from the hot list."""
    symbol: str
    direction: str
    nwe_timeframes: List[str]
    status: str


@dataclass
class PendingSignal:
    """Represents a signal needing screenshot."""
    id: str
    symbol: str
    direction: str
    level: int
    nwe_tf: List[str]


class Config:
    """Configuration constants."""
    API_BASE_URL = os.getenv('STOCK_BUDDY_API_URL', 'https://stock-buddy-app.vercel.app/api')
    API_TIMEOUT = 10
    POLL_INTERVAL = 60
    BATCH_SIZE = 8
    IMPLICIT_WAIT = 10
    EXPLICIT_WAIT = 30
    SCREENSHOT_WAIT = 2
    OBDIV_INDICATOR_NAME = "TTE OBDIV Screener"


class TieredOrchestrator:
    """Orchestrates the tiered screener workflow."""

    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.driver.implicitly_wait(Config.IMPLICIT_WAIT)

    def run(self):
        """Main orchestration loop."""
        logger.info("Starting TieredOrchestrator")
        logger.info(f"API Base URL: {Config.API_BASE_URL}")
        logger.info(f"Poll Interval: {Config.POLL_INTERVAL}s")

        while True:
            try:
                # Step 1: Get hot symbols
                hot_symbols = self.get_hot_symbols()

                if hot_symbols:
                    logger.info(f"Found {len(hot_symbols)} hot symbols")

                    # Step 2: Process in batches
                    for i in range(0, len(hot_symbols), Config.BATCH_SIZE):
                        batch = hot_symbols[i:i + Config.BATCH_SIZE]
                        symbols_str = ', '.join([s.symbol for s in batch])
                        logger.info(f"Processing batch: {symbols_str}")

                        # Step 3: Update OBDIV Screener
                        self.update_obdiv_screener(batch)

                        # Step 4: Wait for recalculation
                        logger.info("Waiting for OBDIV recalculation...")
                        time.sleep(30)

                # Step 5: Process pending screenshots
                self.process_pending_screenshots()

            except Exception as e:
                logger.exception(f"Orchestrator error: {e}")

            # Wait before next poll
            logger.info(f"Sleeping for {Config.POLL_INTERVAL}s...")
            time.sleep(Config.POLL_INTERVAL)

    def get_hot_symbols(self) -> List[HotSymbol]:
        """Fetch hot symbols from Stock Buddy API."""
        try:
            response = requests.get(
                f"{Config.API_BASE_URL}/hot-symbols",
                params={"status": "pending_tier2", "limit": Config.BATCH_SIZE * 2},
                timeout=Config.API_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            return [
                HotSymbol(
                    symbol=item['symbol'],
                    direction=item['direction'],
                    nwe_timeframes=item.get('nwe_timeframes', []),
                    status=item['status']
                )
                for item in data.get('data', [])
            ]
        except requests.RequestException as e:
            logger.error(f"Failed to fetch hot symbols: {e}")
            return []

    def update_obdiv_screener(self, symbols: List[HotSymbol]):
        """Update OBDIV Screener symbol inputs via Selenium."""
        try:
            # Open indicator settings
            if not self._open_indicator_settings(Config.OBDIV_INDICATOR_NAME):
                raise Exception(f"Could not find indicator: {Config.OBDIV_INDICATOR_NAME}")

            time.sleep(1)

            # Find symbol inputs
            wait = WebDriverWait(self.driver, Config.EXPLICIT_WAIT)
            symbol_inputs = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'input[data-property-id*="symbol"]')
                )
            )

            # Update each symbol
            for i, hot_symbol in enumerate(symbols[:8]):
                if i < len(symbol_inputs):
                    self._set_input_value(symbol_inputs[i], f"FX:{hot_symbol.symbol}")
                    logger.debug(f"Set symbol {i+1} to {hot_symbol.symbol}")

            # Clear remaining inputs
            for i in range(len(symbols), min(8, len(symbol_inputs))):
                self._set_input_value(symbol_inputs[i], "")

            # Click OK
            self._click_ok_button()

            logger.info(f"Updated OBDIV Screener with {len(symbols)} symbols")

        except Exception as e:
            logger.exception(f"Failed to update OBDIV Screener: {e}")
            self._press_escape()
            raise

    def process_pending_screenshots(self):
        """Process signals needing screenshots."""
        pending = self.get_pending_screenshots()

        for signal in pending:
            try:
                logger.info(f"Capturing screenshot for {signal.symbol}")
                url = self.capture_screenshot(signal)

                if url:
                    self.update_signal_screenshot(signal.id, url)
                    logger.info(f"Screenshot saved: {url}")
                else:
                    logger.warning(f"Failed to capture screenshot for {signal.symbol}")

            except Exception as e:
                logger.exception(f"Screenshot error for {signal.symbol}: {e}")

    def get_pending_screenshots(self) -> List[PendingSignal]:
        """Fetch signals needing screenshots."""
        try:
            response = requests.get(
                f"{Config.API_BASE_URL}/signals",
                params={"status": "pending_screenshot", "limit": 10},
                timeout=Config.API_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            return [
                PendingSignal(
                    id=item['_id'],
                    symbol=item['symbol'],
                    direction=item['direction'],
                    level=item['level'],
                    nwe_tf=item.get('nwe_tf', [])
                )
                for item in data.get('data', [])
            ]
        except requests.RequestException as e:
            logger.error(f"Failed to fetch pending screenshots: {e}")
            return []

    def capture_screenshot(self, signal: PendingSignal) -> Optional[str]:
        """Capture screenshot for a signal."""
        try:
            # Change symbol
            self._change_symbol(signal.symbol)
            time.sleep(1)

            # Change timeframe
            tf = signal.nwe_tf[0] if signal.nwe_tf else "240"
            self._change_timeframe(tf)
            time.sleep(Config.SCREENSHOT_WAIT)

            # Take snapshot
            return self._take_tradingview_snapshot()

        except Exception as e:
            logger.exception(f"Screenshot capture failed: {e}")
            return None

    def update_signal_screenshot(self, signal_id: str, url: str):
        """Update signal with screenshot URL."""
        try:
            response = requests.patch(
                f"{Config.API_BASE_URL}/signals/{signal_id}",
                json={"screenshot_url": url, "status": "complete"},
                timeout=Config.API_TIMEOUT
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to update signal {signal_id}: {e}")
            raise

    # ==================== SELENIUM HELPERS ====================

    def _open_indicator_settings(self, indicator_name: str) -> bool:
        """Open settings dialog for an indicator."""
        try:
            indicators = self.driver.find_elements(
                By.CSS_SELECTOR, 'div[data-name="legend-source-item"]'
            )

            for indicator in indicators:
                try:
                    title = indicator.find_element(By.CSS_SELECTOR, 'div[class*="title"]').text
                    if indicator_name.lower() in title.lower():
                        ActionChains(self.driver).double_click(indicator).perform()
                        return True
                except:
                    continue

            return False
        except Exception as e:
            logger.error(f"Error opening indicator settings: {e}")
            return False

    def _set_input_value(self, input_element, value: str):
        """Set value for an input element."""
        input_element.click()
        input_element.send_keys(Keys.CONTROL + "a")
        input_element.send_keys(Keys.DELETE)
        if value:
            input_element.send_keys(value)
            input_element.send_keys(Keys.TAB)

    def _click_ok_button(self):
        """Click OK button in settings dialog."""
        wait = WebDriverWait(self.driver, Config.EXPLICIT_WAIT)
        ok_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="submit"]'))
        )
        ok_button.click()

    def _press_escape(self):
        """Press Escape to close dialogs."""
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()

    def _change_symbol(self, symbol: str):
        """Change chart symbol."""
        wait = WebDriverWait(self.driver, Config.EXPLICIT_WAIT)
        search = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[data-role="search"]'))
        )
        search.click()
        search.send_keys(Keys.CONTROL + "a")
        search.send_keys(symbol)
        time.sleep(0.5)
        search.send_keys(Keys.ENTER)

    def _change_timeframe(self, timeframe: str):
        """Change chart timeframe."""
        tf_map = {"240": "4h", "D": "1D", "W": "1W"}
        tf_label = tf_map.get(timeframe, timeframe)

        wait = WebDriverWait(self.driver, Config.EXPLICIT_WAIT)
        tf_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-name="time-interval-button"]'))
        )
        tf_button.click()
        time.sleep(0.3)

        tf_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, f'//div[text()="{tf_label}"]'))
        )
        tf_option.click()

    def _take_tradingview_snapshot(self) -> Optional[str]:
        """Take TradingView snapshot."""
        # Implementation depends on TradingView UI
        # May need to use existing screenshot logic from open_entry_chart.py

        # Placeholder - implement based on existing code
        logger.warning("Snapshot capture not fully implemented")
        return None


# ==================== ENTRY POINT ====================

def main():
    """Entry point for orchestrator."""
    from open_tv import create_driver  # Import your existing driver setup

    logger.info("Initializing Tiered Orchestrator...")

    # Create driver
    driver = create_driver()

    try:
        # Navigate to TradingView
        driver.get("https://www.tradingview.com/chart")
        time.sleep(5)  # Wait for load

        # Start orchestrator
        orchestrator = TieredOrchestrator(driver)
        orchestrator.run()

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
```

#### Step 2: Test the Orchestrator

```bash
# Activate environment
pipenv shell

# Run orchestrator
python tiered_orchestrator.py
```

### 8.3 Verification Checklist

- [ ] `tiered_orchestrator.py` created
- [ ] Connects to Stock Buddy API
- [ ] Fetches hot symbols
- [ ] Updates OBDIV Screener via Selenium
- [ ] Captures screenshots
- [ ] Updates signals with screenshot URLs

---

## 9. Phase 7: Stock Buddy Dashboard

### 9.1 Objective
Create web dashboard for signal display.

### 9.2 Component Overview

Due to length, this phase is summarized. See `TECHNICAL_SPEC.md` Section 7 for detailed component specs.

#### Key Components to Create:

1. **`src/app/dashboard/page.tsx`** - Main dashboard page
2. **`src/components/dashboard/StatsGrid.tsx`** - Statistics cards
3. **`src/components/dashboard/FilterBar.tsx`** - Filter controls
4. **`src/components/dashboard/SignalsTable.tsx`** - Desktop table
5. **`src/components/dashboard/SignalCard.tsx`** - Mobile cards
6. **`src/components/dashboard/ScreenshotModal.tsx`** - Screenshot viewer

#### Quick Start:

```bash
# Install UI dependencies
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu
npm install lucide-react recharts

# Create dashboard page
mkdir -p src/app/dashboard
touch src/app/dashboard/page.tsx

# Create components directory
mkdir -p src/components/dashboard
```

### 9.3 Verification Checklist

- [ ] Dashboard page loads at /dashboard
- [ ] Statistics cards show counts
- [ ] Signals table displays data
- [ ] Filtering works
- [ ] Sorting works
- [ ] Screenshot modal opens

---

## 10. Phase 8: Integration Testing

### 10.1 Test Scenarios

#### Test 1: NWE Webhook

```bash
# Simulate NWE webhook
curl -X POST https://stock-buddy-app.vercel.app/api/nwe \
  -H "Content-Type: application/json" \
  -d '{"tier":"nwe","symbol":"GBPAUD","direction":"bullish","timeframes":["H4"],"timestamp":1672531200}'

# Verify hot_list entry created
curl https://stock-buddy-app.vercel.app/api/hot-symbols
```

#### Test 2: OBDIV Webhook

```bash
# Simulate OBDIV webhook (GBPAUD must be in hot_list first)
curl -X POST https://stock-buddy-app.vercel.app/api/obdiv \
  -H "Content-Type: application/json" \
  -d '{"tier":"obdiv","symbol":"GBPAUD","bull_ob":{"found":true,"tf":"W1","type":"OB"},"bull_div":{"found":true,"tf":"H4","type":"Logic2"},"bear_ob":{"found":false},"bear_div":{"found":false}}'

# Verify signal created
curl https://stock-buddy-app.vercel.app/api/signals
```

#### Test 3: Full Flow

1. Add TTE NWE Screener to TradingView
2. Configure webhook alert
3. Wait for NWE signal to fire
4. Verify hot_list entry
5. Run Python orchestrator
6. Verify OBDIV screener updates
7. Verify signal created
8. Verify screenshot captured
9. Verify dashboard shows signal

### 10.2 Verification Checklist

- [ ] NWE webhook creates hot_list entry
- [ ] OBDIV webhook creates signal with correct level
- [ ] Direction matching works correctly
- [ ] Python orchestrator updates OBDIV screener
- [ ] Screenshots captured successfully
- [ ] Dashboard displays signals correctly
- [ ] Full flow works end-to-end

---

## 11. Phase 9: Production Deployment

### 11.1 Stock Buddy Deployment

```bash
# Deploy to Vercel
cd stock-buddy
vercel --prod

# Set environment variables in Vercel dashboard
# MONGODB_URI=mongodb+srv://...
```

### 11.2 TradingView Setup

1. Create saved layout "Tiered Screener"
2. Add TTE NWE Screener v2
3. Add TTE OBDIV Screener
4. Create webhook alerts for both
5. Test alerts are firing

### 11.3 Python Orchestrator Setup

```bash
# Run as background service
nohup python tiered_orchestrator.py > orchestrator.log 2>&1 &

# Or use systemd service (Linux)
# Or use Task Scheduler (Windows)
```

### 11.4 Monitoring Setup

1. Set up error alerting (email/Discord)
2. Monitor Vercel function logs
3. Monitor orchestrator logs
4. Set up uptime monitoring

### 11.5 Deployment Checklist

- [ ] Stock Buddy deployed to Vercel
- [ ] Environment variables configured
- [ ] MongoDB indexes created
- [ ] TradingView alerts active
- [ ] Python orchestrator running
- [ ] Monitoring configured
- [ ] Documentation updated

---

## 12. Troubleshooting

### 12.1 Webhook Not Received

**Symptoms**: No hot_list entries after NWE signal

**Checks**:
1. TradingView alert is active (not paused)
2. Webhook URL is correct
3. Check Vercel function logs

**Solution**:
```bash
# Test webhook manually
curl -X POST https://stock-buddy-app.vercel.app/api/nwe \
  -H "Content-Type: application/json" \
  -d '{"tier":"nwe","symbol":"TEST","direction":"bullish"}'
```

### 12.2 Signal Not Created

**Symptoms**: OBDIV webhook received but no signal

**Checks**:
1. Symbol is in hot_list
2. Direction matches (bullish NWE + bullish OB)
3. Check API logs

**Solution**:
```bash
# Check hot_list
curl https://stock-buddy-app.vercel.app/api/hot-symbols

# Verify direction matches
```

### 12.3 Selenium Element Not Found

**Symptoms**: "Element not found" errors

**Checks**:
1. TradingView UI may have changed
2. Page not fully loaded

**Solution**:
```python
# Increase wait time
Config.EXPLICIT_WAIT = 60

# Update selectors if TradingView changed
```

### 12.4 Screenshot Capture Failed

**Symptoms**: Signals stuck in "pending_screenshot"

**Checks**:
1. Chrome profile logged into TradingView
2. Chart loads correctly
3. Snapshot feature works manually

**Solution**:
```python
# Add more wait time
Config.SCREENSHOT_WAIT = 5

# Check for popup blockers
```

### 12.5 MongoDB Connection Failed

**Symptoms**: "MongoNetworkError" or timeout

**Checks**:
1. IP address whitelisted in MongoDB Atlas
2. Connection string correct
3. Database user credentials valid

**Solution**:
```bash
# Test connection
mongosh "mongodb+srv://cluster.mongodb.net/tte" --username <user>
```

---

## Quick Reference

### File Locations

```
tradingview-to-everywhere/
├── Pine Script Code/
│   ├── TTE NWE Screener v2.txt      # Tier 1
│   └── TTE OBDIV Screener.txt       # Tier 2
├── resources/
│   └── tier1_symbols.py             # Symbol list
├── tiered_orchestrator.py           # Python orchestrator
├── PRD.md                           # Product requirements
├── TECHNICAL_SPEC.md                # Technical specifications
└── IMPLEMENTATION_GUIDE.md          # This file

stock-buddy/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── nwe/route.ts
│   │   │   ├── obdiv/route.ts
│   │   │   ├── signals/route.ts
│   │   │   ├── signals/[id]/route.ts
│   │   │   └── hot-symbols/route.ts
│   │   └── dashboard/page.tsx
│   ├── components/dashboard/
│   └── lib/mongodb.ts
└── .env.local
```

### Common Commands

```bash
# TTE
pipenv shell
python tiered_orchestrator.py

# Stock Buddy
npm run dev          # Development
vercel --prod        # Deploy

# Testing
curl -X POST http://localhost:3000/api/nwe -H "Content-Type: application/json" -d '{...}'
```

### Webhook URLs

```
NWE:   https://stock-buddy-app.vercel.app/api/nwe
OBDIV: https://stock-buddy-app.vercel.app/api/obdiv
```

---

*This guide provides step-by-step instructions for implementing the TTE Tiered Screener Architecture. For detailed specifications, see TECHNICAL_SPEC.md. For product context, see PRD.md.*
