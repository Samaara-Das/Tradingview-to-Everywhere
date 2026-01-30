# TTE Tiered Screener Architecture - Complete Implementation Plan

**Created**: 2026-01-29
**Status**: Ready for Implementation
**Estimated Phases**: 9

---

## Executive Summary

This document provides a complete implementation plan for the TTE Tiered Screener Architecture. The system enables scalable trading signal detection across 1000+ symbols using a two-tier approach:

- **Tier 1 (NWE Screener)**: Lightweight Pine Script screeners that monitor 20 symbols each for Nadaraya-Watson Envelope (NWE) zone entries
- **Tier 2 (OB+DIV Screener)**: Focused Pine Script screener that checks hot symbols for Order Block and Divergence confluence
- **Stock Buddy Dashboard**: Web application showing real-time signals with screenshots

The architecture uses TradingView webhooks for instant alert delivery, MongoDB for persistence, and Python/Selenium for screenshot capture.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COMPLETE ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 1: NWE Screener (TradingView)                                 │   │
│  │  - 20 symbols, H4 + D1 timeframes                                   │   │
│  │  - Webhook: POST to Stock Buddy /api/nwe                            │   │
│  │  - Payload: {"tier":"nwe","symbol":"X","direction":"bullish",...}   │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STOCK BUDDY API (Vercel + MongoDB)                                 │   │
│  │  - /api/nwe → Adds to hot_list collection                           │   │
│  │  - /api/obdiv → Combines with NWE → final signal                    │   │
│  │  - /api/signals → Dashboard fetches signals                         │   │
│  │  - /api/hot-symbols → Python fetches symbols for Tier 2             │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PYTHON ORCHESTRATOR (Local)                                        │   │
│  │  - Polls /api/hot-symbols for pending Tier 2 checks                 │   │
│  │  - Changes OB+DIV Screener symbol inputs (Selenium)                 │   │
│  │  - Takes screenshots for final signals                              │   │
│  │  - Updates /api/signals with screenshot URLs                        │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 2: OB+DIV Screener (TradingView)                              │   │
│  │  - 8 symbols (dynamically set by Python)                            │   │
│  │  - Checks OB + Divergence (NWE removed for efficiency)              │   │
│  │  - Webhook: POST to Stock Buddy /api/obdiv                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STOCK BUDDY DASHBOARD                                              │   │
│  │  - Real-time signals table with sorting/filtering                   │   │
│  │  - Statistics cards (today, level 3, bullish/bearish)               │   │
│  │  - Screenshot modal                                                 │   │
│  │  - Notifications for new signals                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Symbol Selection

### Selected Symbols (20 Forex Pairs)

```
Batch 1 (1-10):
1.  EURUSD   - Euro / US Dollar
2.  GBPUSD   - British Pound / US Dollar
3.  USDJPY   - US Dollar / Japanese Yen
4.  USDCHF   - US Dollar / Swiss Franc
5.  AUDUSD   - Australian Dollar / US Dollar
6.  NZDUSD   - New Zealand Dollar / US Dollar
7.  USDCAD   - US Dollar / Canadian Dollar
8.  GBPJPY   - British Pound / Japanese Yen
9.  EURJPY   - Euro / Japanese Yen
10. AUDJPY   - Australian Dollar / Japanese Yen

Batch 2 (11-20):
11. GBPAUD   - British Pound / Australian Dollar
12. EURAUD   - Euro / Australian Dollar
13. EURGBP   - Euro / British Pound
14. EURCAD   - Euro / Canadian Dollar
15. GBPCAD   - British Pound / Canadian Dollar
16. AUDCAD   - Australian Dollar / Canadian Dollar
17. NZDJPY   - New Zealand Dollar / Japanese Yen
18. CADJPY   - Canadian Dollar / Japanese Yen
19. CHFJPY   - Swiss Franc / Japanese Yen
20. AUDNZD   - Australian Dollar / New Zealand Dollar
```

### Symbol Configuration in Pine Script

```pinescript
// Symbol inputs for NWE Screener
s01 = input.symbol("FX:EURUSD", "Symbol 1")
s02 = input.symbol("FX:GBPUSD", "Symbol 2")
s03 = input.symbol("FX:USDJPY", "Symbol 3")
// ... up to s20
```

---

## Phase 2: TTE NWE Screener (Tier 1)

### Purpose
Lightweight screener that monitors 20 symbols for NWE zone entry. Fires webhook when price enters upper or lower NWE zone on H4 or D1 timeframe.

### File Location
`Pine Script Code/TTE NWE Screener v2.txt`

### Technical Specifications

| Specification | Value |
|---------------|-------|
| Symbols | 20 |
| Timeframes | H4, D1 |
| request.security() calls | 40 (20 × 2) |
| Alert type | Webhook |
| Alert frequency | Once per bar close |

### Webhook Payload Format

```json
{
  "tier": "nwe",
  "symbol": "GBPAUD",
  "direction": "bullish",
  "timeframes": ["H4", "D1"],
  "timestamp": 1672531200
}
```

### NWE Zone Detection Logic

```pinescript
// NWE Zone Structure
upper_far   = yhat + bandwidth * 3
upper_avg   = (upper_far + upper_near) / 2
upper_near  = yhat + bandwidth * 1
yhat        = regression line (not a boundary)
lower_near  = yhat - bandwidth * 1
lower_avg   = (lower_far + lower_near) / 2
lower_far   = yhat - bandwidth * 3

// Bullish: price overlaps lower zone
bullish = (low <= lower_near and high >= lower_avg) or
          (low <= lower_avg and high >= lower_far)

// Bearish: price overlaps upper zone
bearish = (high >= upper_near and low <= upper_avg) or
          (high >= upper_avg and low <= upper_far)
```

### Alert Configuration in TradingView

1. Add TTE NWE Screener indicator to chart
2. Create alert:
   - Condition: "TTE NWE Screener" → "Any alert() function call"
   - Options: Once per bar close
   - Actions: Webhook URL
   - Webhook URL: `https://stock-buddy-app.vercel.app/api/nwe`
   - Message: `{{alert.message}}`

---

## Phase 3: TTE OBDIV Screener (Tier 2)

### Purpose
Focused screener that checks hot symbols (from Tier 1) for Order Block and Divergence confluence. NWE calculation is removed since Tier 1 already confirmed NWE zone entry.

### File Location
`Pine Script Code/TTE OBDIV Screener.txt`

### Technical Specifications

| Specification | Value |
|---------------|-------|
| Symbols | 8 (dynamically set) |
| OB Timeframes | H4, D1, W1 |
| DIV Timeframes | H4, D1 |
| request.security() calls | ~40 |
| Alert type | Webhook |

### Changes from Original TTE Screener

1. **REMOVED**: NWE calculation (redundant with Tier 1)
2. **REMOVED**: Table display (signals go to webhook)
3. **KEPT**: OB & FVG detection
4. **KEPT**: Divergence detection (Logic 2 + Internal)
5. **ADDED**: Report both bullish AND bearish findings

### Webhook Payload Format

```json
{
  "tier": "obdiv",
  "symbol": "GBPAUD",
  "bull_ob": {
    "found": true,
    "tf": "W1",
    "type": "OB",
    "high": 1.0550,
    "low": 1.0500
  },
  "bull_div": {
    "found": true,
    "tf": "H4",
    "type": "Logic2"
  },
  "bear_ob": {
    "found": false
  },
  "bear_div": {
    "found": false
  },
  "timestamp": 1672531200
}
```

### Why Report Both Directions?

Python orchestrator knows the NWE direction from the hot list. By reporting both bullish and bearish OB+DIV findings, the screener doesn't need to know the intended direction. Python matches the correct side.

---

## Phase 4: Stock Buddy API Endpoints

### Base URL
`https://stock-buddy-app.vercel.app/api`

### Endpoint 1: POST /api/nwe

**Purpose**: Receive NWE alerts from Tier 1, add to hot list

**Request Body**:
```json
{
  "tier": "nwe",
  "symbol": "GBPAUD",
  "direction": "bullish",
  "timeframes": ["H4", "D1"],
  "timestamp": 1672531200
}
```

**Response**:
```json
{
  "success": true,
  "action": "upserted",
  "symbol": "GBPAUD"
}
```

**Implementation**:
```javascript
// pages/api/nwe.js
import clientPromise from '@/lib/mongodb';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { symbol, direction, timeframes, timestamp } = req.body;

    const client = await clientPromise;
    const db = client.db('tte');

    await db.collection('hot_list').updateOne(
      { symbol },
      {
        $set: {
          symbol,
          direction,
          nwe_timeframes: timeframes,
          nwe_timestamp: timestamp,
          status: 'pending_tier2',
          updated_at: new Date()
        }
      },
      { upsert: true }
    );

    res.status(200).json({ success: true, action: 'upserted', symbol });
  } catch (error) {
    console.error('NWE webhook error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}
```

### Endpoint 2: POST /api/obdiv

**Purpose**: Receive OB+DIV alerts from Tier 2, combine with NWE, create final signal

**Request Body**:
```json
{
  "tier": "obdiv",
  "symbol": "GBPAUD",
  "bull_ob": {"found": true, "tf": "W1", "type": "OB"},
  "bull_div": {"found": true, "tf": "H4", "type": "Logic2"},
  "bear_ob": {"found": false},
  "bear_div": {"found": false},
  "timestamp": 1672531200
}
```

**Response**:
```json
{
  "success": true,
  "signal_created": true,
  "level": 3
}
```

**Implementation**:
```javascript
// pages/api/obdiv.js
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { symbol, bull_ob, bull_div, bear_ob, bear_div, timestamp } = req.body;

    const client = await clientPromise;
    const db = client.db('tte');

    // Find hot symbol to get NWE direction
    const hotSymbol = await db.collection('hot_list').findOne({ symbol });

    if (!hotSymbol) {
      return res.status(200).json({
        success: true,
        signal_created: false,
        reason: 'not_in_hot_list'
      });
    }

    // Match direction from hot list
    const isBullish = hotSymbol.direction === 'bullish';
    const ob = isBullish ? bull_ob : bear_ob;
    const div = isBullish ? bull_div : bear_div;

    // Calculate signal level
    let level = 1; // NWE only (default)
    if (ob?.found) level = 2; // NWE + OB
    if (ob?.found && div?.found) level = 3; // NWE + OB + DIV

    // Create final signal
    const signal = {
      symbol,
      direction: hotSymbol.direction,
      level,
      nwe_tf: hotSymbol.nwe_timeframes,
      ob_tf: ob?.tf || null,
      ob_type: ob?.type || null,
      div_tf: div?.tf || null,
      div_type: div?.type || null,
      timestamp,
      screenshot_url: null,
      status: 'pending_screenshot',
      created_at: new Date()
    };

    await db.collection('signals').insertOne(signal);

    // Update hot_list status
    await db.collection('hot_list').updateOne(
      { symbol },
      { $set: { status: 'tier2_complete', last_checked: new Date() } }
    );

    res.status(200).json({ success: true, signal_created: true, level });
  } catch (error) {
    console.error('OBDIV webhook error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}
```

### Endpoint 3: GET /api/signals

**Purpose**: Fetch signals for dashboard

**Query Parameters**:
- `limit` (default: 50)
- `level` (optional: 1, 2, 3)
- `direction` (optional: bullish, bearish)
- `status` (optional: pending_screenshot, complete)

**Response**:
```json
[
  {
    "_id": "...",
    "symbol": "GBPAUD",
    "direction": "bullish",
    "level": 3,
    "nwe_tf": ["H4", "D1"],
    "ob_tf": "W1",
    "div_tf": "H4",
    "screenshot_url": "https://...",
    "status": "complete",
    "created_at": "2026-01-29T12:00:00Z"
  }
]
```

### Endpoint 4: GET /api/hot-symbols

**Purpose**: Python polls this to get symbols needing Tier 2 check

**Response**:
```json
[
  {
    "symbol": "GBPAUD",
    "direction": "bullish",
    "nwe_timeframes": ["H4", "D1"],
    "status": "pending_tier2"
  }
]
```

### Endpoint 5: PATCH /api/signals/[id]

**Purpose**: Update signal with screenshot URL

**Request Body**:
```json
{
  "screenshot_url": "https://www.tradingview.com/x/ABC123/",
  "status": "complete"
}
```

---

## Phase 5: MongoDB Schema

### Database: `tte`

### Collection: `hot_list`

```javascript
{
  _id: ObjectId,
  symbol: String,           // "GBPAUD"
  direction: String,        // "bullish" | "bearish"
  nwe_timeframes: [String], // ["H4", "D1"]
  nwe_timestamp: Number,    // Unix timestamp
  status: String,           // "pending_tier2" | "tier2_complete" | "expired"
  updated_at: Date,
  last_checked: Date
}

// Indexes
{ symbol: 1 }              // Unique
{ status: 1, updated_at: 1 }
```

### Collection: `signals`

```javascript
{
  _id: ObjectId,
  symbol: String,           // "GBPAUD"
  direction: String,        // "bullish" | "bearish"
  level: Number,            // 1, 2, or 3
  nwe_tf: [String],         // ["H4", "D1"]
  ob_tf: String,            // "W1" or null
  ob_type: String,          // "OB", "FVG", "Breaker" or null
  div_tf: String,           // "H4" or null
  div_type: String,         // "Logic2", "Internal" or null
  timestamp: Number,        // Unix timestamp from alert
  screenshot_url: String,   // URL or null
  status: String,           // "pending_screenshot" | "complete"
  created_at: Date
}

// Indexes
{ created_at: -1 }
{ status: 1 }
{ level: 1 }
{ symbol: 1 }
```

---

## Phase 6: Python Orchestrator

### File Location
`tiered_orchestrator.py`

### Main Loop

```python
class TieredOrchestrator:
    def __init__(self, driver):
        self.driver = driver
        self.api_base = "https://stock-buddy-app.vercel.app/api"
        self.chart = OpenChart(driver)

    def run(self):
        """Main orchestration loop"""
        while True:
            try:
                # Step 1: Get hot symbols needing Tier 2 check
                hot_symbols = self.get_hot_symbols()

                if hot_symbols:
                    logger.info(f"Found {len(hot_symbols)} hot symbols")

                    # Step 2: Update OB+DIV Screener with hot symbols
                    self.update_obdiv_screener(hot_symbols)

                    # Step 3: Wait for screener to recalculate and fire webhooks
                    sleep(30)

                # Step 4: Process signals needing screenshots
                self.process_pending_screenshots()

                # Step 5: Clean up expired hot symbols
                self.cleanup_expired()

            except Exception as e:
                logger.exception(f"Orchestrator error: {e}")

            sleep(60)  # Check every minute

    def get_hot_symbols(self) -> list:
        """Fetch hot symbols from Stock Buddy API"""
        response = requests.get(f"{self.api_base}/hot-symbols")
        return response.json()

    def update_obdiv_screener(self, symbols: list):
        """Change OB+DIV Screener symbol inputs via Selenium"""
        # 1. Open indicator settings
        self.open_indicator_settings("TTE OBDIV")

        # 2. For each symbol input (1-8), set to hot symbol
        for i, sym in enumerate(symbols[:8], 1):
            self.set_symbol_input(i, sym['symbol'])

        # 3. Click OK
        self.click_ok_button()

        # 4. Wait for recalculation
        sleep(5)

    def process_pending_screenshots(self):
        """Take screenshots for signals that need them"""
        response = requests.get(
            f"{self.api_base}/signals",
            params={"status": "pending_screenshot", "limit": 10}
        )
        signals = response.json()

        for signal in signals:
            try:
                screenshot_url = self.take_screenshot(signal)
                if screenshot_url:
                    self.update_signal_screenshot(signal['_id'], screenshot_url)
            except Exception as e:
                logger.error(f"Screenshot error for {signal['symbol']}: {e}")

    def take_screenshot(self, signal: dict) -> str:
        """Navigate to chart and take screenshot"""
        # Change to signal's symbol
        self.chart.change_symbol(signal['symbol'])

        # Change to first NWE timeframe
        tf = signal['nwe_tf'][0] if signal['nwe_tf'] else 'H4'
        self.chart.change_tframe(tf)

        # Take screenshot
        sleep(2)  # Wait for chart to load
        links = self.chart.save_chart_img()

        return links['png'] if links else None

    def update_signal_screenshot(self, signal_id: str, url: str):
        """Update signal with screenshot URL"""
        requests.patch(
            f"{self.api_base}/signals/{signal_id}",
            json={"screenshot_url": url, "status": "complete"}
        )
```

### Selenium Methods for Screener Update

```python
def open_indicator_settings(self, indicator_name: str):
    """Open settings dialog for an indicator"""
    # Find indicator in legend
    indicators = self.driver.find_elements(
        By.CSS_SELECTOR, 'div[data-name="legend-source-item"]'
    )

    for ind in indicators:
        title = ind.find_element(By.CSS_SELECTOR, 'div[class*="title"]').text
        if indicator_name in title:
            # Double-click to open settings
            ActionChains(self.driver).double_click(ind).perform()
            sleep(1)
            return True

    return False

def set_symbol_input(self, index: int, symbol: str):
    """Set symbol input field in indicator settings"""
    # Find the Nth symbol input
    inputs = WebDriverWait(self.driver, 10).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'input[data-property-id*="symbol"]')
        )
    )

    if index <= len(inputs):
        input_field = inputs[index - 1]
        input_field.clear()
        input_field.send_keys(symbol)

def click_ok_button(self):
    """Click OK button in settings dialog"""
    ok_button = WebDriverWait(self.driver, 10).until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[name="submit"]')
        )
    )
    ok_button.click()
```

---

## Phase 7: Stock Buddy Dashboard

### Page Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  HEADER: Logo | Notifications Badge | Profile                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  STATS GRID                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ TODAY    │  │ LEVEL 3  │  │ LEVEL 2  │  │ BULLISH  │  │ BEARISH  │      │
│  │   12     │  │    3     │  │    5     │  │    8     │  │    4     │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
├─────────────────────────────────────────────────────────────────────────────┤
│  FILTER BAR                                                                 │
│  Level: [All ▼] Direction: [All ▼] Symbol: [Search...] Period: [24h ▼]     │
│  Sort: [Time ▼] [↑↓]    [ ] Screenshots only    [🔴 Live]                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  SIGNALS TABLE (Desktop) / CARD GRID (Mobile)                               │
│  ┌───────┬────────┬───────┬───────┬────────┬──────┬───────┬──────────┐     │
│  │ Time  │ Symbol │ Dir   │ Level │ NWE    │ OB   │ DIV   │ Actions  │     │
│  ├───────┼────────┼───────┼───────┼────────┼──────┼───────┼──────────┤     │
│  │ 14:30 │ GBPAUD │ 🟢BUY │ ⭐⭐⭐│ H4,D1  │ W1   │ H4    │ 📸 📈 🔗 │     │
│  │ 14:15 │ EURUSD │ 🔴SELL│ ⭐⭐  │ D1     │ H4   │ -     │ 📸 📈 🔗 │     │
│  └───────┴────────┴───────┴───────┴────────┴──────┴───────┴──────────┘     │
│                                                                             │
│  PAGINATION: ◀ Prev | Page 1 of 5 | Next ▶                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  DISTRIBUTION CHART                                                         │
│  Level 3 ████████████████░░░░░░░░░░░░░░░░░░░░░░  35%                       │
│  Level 2 ████████████████████████░░░░░░░░░░░░░░  45%                       │
│  Level 1 ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  20%                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Tree

```
app/dashboard/page.jsx
├── components/dashboard/Header.jsx
├── components/dashboard/StatsGrid.jsx
│   └── components/dashboard/StatsCard.jsx
├── components/dashboard/FilterBar.jsx
│   ├── components/dashboard/FilterDropdown.jsx
│   ├── components/dashboard/SearchInput.jsx
│   └── components/dashboard/LiveIndicator.jsx
├── components/dashboard/SignalsTable.jsx (desktop)
│   ├── components/dashboard/TableRow.jsx
│   └── components/dashboard/ActionButtons.jsx
├── components/dashboard/CardGrid.jsx (mobile)
│   └── components/dashboard/SignalCard.jsx
├── components/dashboard/Pagination.jsx
├── components/dashboard/DistributionChart.jsx
├── components/dashboard/ScreenshotModal.jsx
└── components/dashboard/ToastNotification.jsx
```

### Color Scheme

```css
/* Signal Levels */
.level-3 { background: #FEF3C7; border-color: #F59E0B; } /* Amber/Gold */
.level-2 { background: #E0E7FF; border-color: #6366F1; } /* Indigo */
.level-1 { background: #F3F4F6; border-color: #9CA3AF; } /* Gray */

/* Directions */
.bullish { color: #059669; background: #D1FAE5; } /* Emerald */
.bearish { color: #DC2626; background: #FEE2E2; } /* Red */
```

### Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | Next.js 14 (App Router) |
| Styling | Tailwind CSS |
| UI Components | shadcn/ui |
| Data Fetching | React Query |
| Charts | Recharts |
| Notifications | react-hot-toast |
| Icons | Lucide React |

---

## Phase 8: Signal Flow Timeline

```
TIME ──────────────────────────────────────────────────────────────────────►

[T+0s]     NWE Screener detects GBPAUD in bullish zone (H4 + D1)
              │
              ▼
           Webhook POST to /api/nwe
           {"tier":"nwe","symbol":"GBPAUD","direction":"bullish","timeframes":["H4","D1"]}
              │
              ▼
           Stock Buddy adds GBPAUD to hot_list (status: pending_tier2)

[T+60s]    Python polls /api/hot-symbols
              │
              ▼
           Gets [{"symbol":"GBPAUD","direction":"bullish",...}]
              │
              ▼
           Selenium opens OB+DIV Screener settings
           Sets Symbol 1 = "GBPAUD"
           Clicks OK
              │
              ▼
           Waits 30s for recalculation

[T+90s]    OB+DIV Screener fires webhook for GBPAUD
              │
              ▼
           Webhook POST to /api/obdiv
           {"tier":"obdiv","symbol":"GBPAUD","bull_ob":{"found":true,"tf":"W1"},...}
              │
              ▼
           Stock Buddy:
           1. Looks up GBPAUD in hot_list → direction = bullish
           2. Matches bull_ob and bull_div
           3. Calculates level = 3 (NWE + OB + DIV)
           4. Creates signal (status: pending_screenshot)

[T+120s]   Python polls /api/signals?status=pending_screenshot
              │
              ▼
           Selenium navigates to GBPAUD H4 chart
           Takes screenshot
           Uploads to TradingView snapshot
              │
              ▼
           PATCH /api/signals/{id}
           {"screenshot_url":"https://...","status":"complete"}

[T+120s+]  Dashboard auto-refreshes
              │
              ▼
           Shows new signal:
           ┌────────┬────────┬───────┬───────┬────────┬─────┬────────┬──────┐
           │ 12:00  │ GBPAUD │ 🟢 BUY│ ⭐⭐⭐│ H4, D1 │ W1  │ H4     │ 📸   │
           └────────┴────────┴───────┴───────┴────────┴─────┴────────┴──────┘
```

---

## Phase 9: Deployment Checklist

### TradingView Setup
- [ ] Add TTE NWE Screener to chart layout "NWE"
- [ ] Configure NWE Screener with 20 symbols
- [ ] Create webhook alert for NWE Screener
- [ ] Add TTE OBDIV Screener to chart layout "OBDIV"
- [ ] Configure OBDIV Screener with placeholder symbols
- [ ] Create webhook alert for OBDIV Screener

### Stock Buddy Deployment
- [ ] Deploy API endpoints to Vercel
- [ ] Configure environment variables (MONGODB_URI)
- [ ] Test webhook endpoints with Postman/curl
- [ ] Enable production logging

### MongoDB Setup
- [ ] Create hot_list collection
- [ ] Create signals collection
- [ ] Create indexes
- [ ] Verify connection from Vercel

### Python Orchestrator
- [ ] Update API base URL to production
- [ ] Configure Chrome/Edge profile
- [ ] Set up as background service or scheduled task
- [ ] Test connection to Stock Buddy API

### Monitoring
- [ ] Set up error alerting (email/Discord)
- [ ] Monitor webhook delivery success rate
- [ ] Track signal flow latency
- [ ] Monitor screenshot capture success

---

## Testing Checklist

### Unit Tests
- [ ] NWE zone detection logic
- [ ] Signal level calculation
- [ ] Hot list management
- [ ] API endpoint responses

### Integration Tests
- [ ] NWE webhook → hot_list creation
- [ ] OBDIV webhook → signal creation
- [ ] Python → API communication
- [ ] Screenshot capture and upload

### End-to-End Tests
- [ ] Level 1 signal flow (NWE only)
- [ ] Level 2 signal flow (NWE + OB)
- [ ] Level 3 signal flow (NWE + OB + DIV)
- [ ] Direction change handling
- [ ] Multiple symbols simultaneously
- [ ] Dashboard real-time updates

---

## Troubleshooting Guide

### Webhook Not Received
1. Check TradingView alert is active
2. Verify webhook URL is correct
3. Check Vercel function logs
4. Test with curl: `curl -X POST https://stock-buddy-app.vercel.app/api/nwe -H "Content-Type: application/json" -d '{"symbol":"TEST",...}'`

### Signal Not Created
1. Check hot_list has the symbol
2. Verify direction matches (bullish/bearish)
3. Check MongoDB connection
4. Review API logs for errors

### Screenshot Not Captured
1. Check Python orchestrator is running
2. Verify TradingView is logged in
3. Check chart loads correctly
4. Review screenshot save permissions

### Dashboard Not Updating
1. Check API returns correct data
2. Verify polling interval
3. Check browser console for errors
4. Test API directly: `GET /api/signals`

---

## Future Enhancements

1. **Scale to 1000+ symbols**: Add more NWE Screeners (50 screeners × 20 symbols)
2. **WebSocket updates**: Replace polling with real-time WebSocket
3. **Backtesting**: Add historical signal analysis
4. **Mobile app**: React Native version
5. **Alert routing**: Different channels for different signal levels
6. **Performance metrics**: Win rate, P&L tracking

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial comprehensive plan |

---

*This document serves as the single source of truth for the TTE Tiered Screener Architecture implementation.*
