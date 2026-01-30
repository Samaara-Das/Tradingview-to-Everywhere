# Technical Specification
# TTE Tiered Screener Architecture

**Version**: 1.0
**Created**: 2026-01-29
**Status**: Draft
**Last Updated**: 2026-01-29

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Pine Script Specifications](#2-pine-script-specifications)
3. [API Specifications](#3-api-specifications)
4. [Database Specifications](#4-database-specifications)
5. [Python Orchestrator Specifications](#5-python-orchestrator-specifications)
6. [Selenium Automation Specifications](#6-selenium-automation-specifications)
7. [Dashboard Specifications](#7-dashboard-specifications)
8. [Sequence Diagrams](#8-sequence-diagrams)
9. [Error Handling](#9-error-handling)
10. [Performance Requirements](#10-performance-requirements)
11. [Security Considerations](#11-security-considerations)
12. [Monitoring and Logging](#12-monitoring-and-logging)

---

## 1. System Overview

### 1.1 Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                                 SYSTEM ARCHITECTURE                                 │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  ┌──────────────────────────────────────────────────────────────────────────────┐ │
│  │                         TRADINGVIEW (Browser)                                 │ │
│  │  ┌─────────────────────────┐      ┌─────────────────────────┐                │ │
│  │  │  TTE NWE Screener       │      │  TTE OBDIV Screener     │                │ │
│  │  │  (Tier 1)               │      │  (Tier 2)               │                │ │
│  │  │  - 20 symbols           │      │  - 8 symbols            │                │ │
│  │  │  - H4, D1 timeframes    │      │  - H4, D1, W1           │                │ │
│  │  │  - NWE detection only   │      │  - OB + DIV detection   │                │ │
│  │  └───────────┬─────────────┘      └───────────┬─────────────┘                │ │
│  │              │                                │                               │ │
│  └──────────────┼────────────────────────────────┼───────────────────────────────┘ │
│                 │ Webhook POST                   │ Webhook POST                    │
│                 │ /api/nwe                       │ /api/obdiv                      │
│                 ▼                                ▼                                 │
│  ┌──────────────────────────────────────────────────────────────────────────────┐ │
│  │                         STOCK BUDDY (Vercel)                                  │ │
│  │                                                                               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │ │
│  │  │ POST        │  │ POST        │  │ GET         │  │ PATCH       │          │ │
│  │  │ /api/nwe    │  │ /api/obdiv  │  │ /api/signals│  │ /api/signals│          │ │
│  │  │             │  │             │  │             │  │ /[id]       │          │ │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │ │
│  │         │                │                │                │                  │ │
│  │         ▼                ▼                ▼                ▼                  │ │
│  │  ┌───────────────────────────────────────────────────────────────────────┐   │ │
│  │  │                     MongoDB Atlas                                      │   │ │
│  │  │  ┌─────────────────┐              ┌─────────────────┐                 │   │ │
│  │  │  │   hot_list      │              │    signals      │                 │   │ │
│  │  │  │   collection    │              │    collection   │                 │   │ │
│  │  │  └─────────────────┘              └─────────────────┘                 │   │ │
│  │  └───────────────────────────────────────────────────────────────────────┘   │ │
│  │                                                                               │ │
│  │  ┌───────────────────────────────────────────────────────────────────────┐   │ │
│  │  │                     Dashboard (Next.js)                                │   │ │
│  │  │  - Signals table with sorting/filtering                               │   │ │
│  │  │  - Statistics cards                                                   │   │ │
│  │  │  - Screenshot modal                                                   │   │ │
│  │  └───────────────────────────────────────────────────────────────────────┘   │ │
│  └──────────────────────────────────────────────────────────────────────────────┘ │
│                 ▲                                                                  │
│                 │ GET /api/hot-symbols                                            │
│                 │ PATCH /api/signals/[id]                                         │
│                 │                                                                  │
│  ┌──────────────┴───────────────────────────────────────────────────────────────┐ │
│  │                     PYTHON ORCHESTRATOR (Local)                               │ │
│  │                                                                               │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐               │ │
│  │  │ Hot Symbol      │  │ Symbol Input    │  │ Screenshot      │               │ │
│  │  │ Poller          │  │ Updater         │  │ Capturer        │               │ │
│  │  │ (60s interval)  │  │ (Selenium)      │  │ (Selenium)      │               │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘               │ │
│  │                                                                               │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Inventory

| Component | Technology | Location | Port/URL |
|-----------|------------|----------|----------|
| TTE NWE Screener | Pine Script v5 | TradingView | N/A |
| TTE OBDIV Screener | Pine Script v5 | TradingView | N/A |
| Stock Buddy API | Next.js 14 | Vercel | https://stock-buddy-app.vercel.app/api |
| Stock Buddy Dashboard | Next.js 14 + React | Vercel | https://stock-buddy-app.vercel.app |
| MongoDB | MongoDB Atlas | Cloud | mongodb+srv://... |
| Python Orchestrator | Python 3.11 | Local | N/A |
| Selenium WebDriver | ChromeDriver | Local | N/A |

### 1.3 Data Flow Summary

```
1. NWE Screener detects zone entry
   └─► Webhook to /api/nwe
       └─► Insert/update hot_list document
           └─► Python polls /api/hot-symbols
               └─► Selenium updates OBDIV Screener symbols
                   └─► OBDIV Screener detects OB/DIV
                       └─► Webhook to /api/obdiv
                           └─► Create signal document
                               └─► Python captures screenshot
                                   └─► Update signal with screenshot URL
                                       └─► Dashboard displays signal
```

---

## 2. Pine Script Specifications

### 2.1 TTE NWE Screener (Tier 1)

#### 2.1.1 Indicator Metadata

```pinescript
//@version=5
indicator("TTE NWE Screener", overlay=false, max_bars_back=500)
```

#### 2.1.2 Input Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `s01` - `s20` | symbol | FX:EURUSD, etc. | 20 symbol inputs |
| `nwe_h` | int | 8 | Kernel bandwidth |
| `nwe_alpha` | float | 8.0 | Kernel alpha |
| `nwe_x0` | int | 25 | Kernel x0 |
| `nwe_atrLen` | int | 60 | ATR length for bands |
| `nwe_nearFactor` | float | 1.5 | Near band multiplier |
| `nwe_farFactor` | float | 8.0 | Far band multiplier |

#### 2.1.3 Function Signatures

```pinescript
// Kernel regression calculation
kernels.rationalQuadratic(source, h, alpha, x0) => float

// Kernel ATR calculation
kernel_atr(length, yhat_high, yhat_low, yhat_close) => float

// NWE zone detection for single symbol/timeframe
calcNWEZone(float _close, float _high, float _low) => [bool nweBull, bool nweBear]

// Zone overlap detection
// Bullish: (low <= lower_near AND high >= lower_avg) OR (low <= lower_avg AND high >= lower_far)
// Bearish: (high >= upper_near AND low <= upper_avg) OR (high >= upper_avg AND low <= upper_far)
```

#### 2.1.4 Request.security Calls

```pinescript
// Per symbol: 2 calls (H4 + D1)
// Total: 20 symbols × 2 timeframes = 40 calls

[nweBull01_h4, nweBear01_h4] = request.security(s01, "240", calcNWEZone(close, high, low))
[nweBull01_d1, nweBear01_d1] = request.security(s01, "D", calcNWEZone(close, high, low))
// ... repeat for s02-s20
```

#### 2.1.5 Alert Payload Structure

```pinescript
// Build JSON payload
buildNwePayload(symbol, direction, timeframes, timestamp) =>
    '{"tier":"nwe","symbol":"' + symbol + '","direction":"' + direction +
    '","timeframes":' + timeframes + ',"timestamp":' + str.tostring(timestamp) + '}'

// Example output:
// {"tier":"nwe","symbol":"GBPAUD","direction":"bullish","timeframes":["H4","D1"],"timestamp":1672531200}
```

#### 2.1.6 Alert Trigger Logic

```pinescript
// State tracking (persist across bars)
var bool prevBull01 = false
var bool prevBear01 = false

// Current state
bool currBull01 = nweBull01_h4 or nweBull01_d1
bool currBear01 = nweBear01_h4 or nweBear01_d1

// Fire on state CHANGE only (not every bar)
if barstate.isconfirmed
    if currBull01 and not prevBull01
        alert(buildNwePayload(s01, "bullish", buildTfArray(nweBull01_h4, nweBull01_d1), time), alert.freq_once_per_bar_close)
    if currBear01 and not prevBear01
        alert(buildNwePayload(s01, "bearish", buildTfArray(nweBear01_h4, nweBear01_d1), time), alert.freq_once_per_bar_close)

    // Update state
    prevBull01 := currBull01
    prevBear01 := currBear01
```

### 2.2 TTE OBDIV Screener (Tier 2)

#### 2.2.1 Indicator Metadata

```pinescript
//@version=5
indicator("TTE OBDIV Screener", overlay=false, max_bars_back=500)
```

#### 2.2.2 Input Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `s01` - `s08` | symbol | (dynamic) | 8 symbol inputs |
| `ob_lookback` | int | 50 | OB detection lookback |
| `ob_mitigation_depth` | int | 100 | OB mitigation check depth |
| `fvg_min_size` | float | 0.0 | Minimum FVG size |
| `div_kernel_fast_h` | int | 5 | Fast kernel bandwidth |
| `div_kernel_slow_h` | int | 34 | Slow kernel bandwidth |

#### 2.2.3 Function Signatures

```pinescript
// OB/FVG detection
detectOBFVG(float _high, float _low, float _close, float _open) =>
    [bool bullOB, bool bearOB, bool bullFVG, bool bearFVG,
     bool breakerSupport, bool breakerResistance,
     string obType, float obHigh, float obLow, int obTimestamp]

// Divergence detection (Logic 2 + Internal)
detectDivergence(float _close, float _high, float _low) =>
    [bool bullDiv, bool bearDiv, string divType, int divTimestamp]

// Combined check for single symbol
checkOBDIV(symbol) =>
    [bull_ob_h4, bear_ob_h4, bull_div_h4, bear_div_h4, ...]
```

#### 2.2.4 Request.security Calls

```pinescript
// Per symbol: ~5 calls (H4, D1, W1 for OB; H4, D1 for DIV)
// Total: 8 symbols × 5 timeframes = 40 calls

// OB/FVG on H4, D1, W1
[bullOB01_h4, bearOB01_h4, ...] = request.security(s01, "240", detectOBFVG(...))
[bullOB01_d1, bearOB01_d1, ...] = request.security(s01, "D", detectOBFVG(...))
[bullOB01_w1, bearOB01_w1, ...] = request.security(s01, "W", detectOBFVG(...))

// DIV on H4, D1
[bullDiv01_h4, bearDiv01_h4, ...] = request.security(s01, "240", detectDivergence(...))
[bullDiv01_d1, bearDiv01_d1, ...] = request.security(s01, "D", detectDivergence(...))
```

#### 2.2.5 Alert Payload Structure

```pinescript
// Reports BOTH bullish and bearish findings
// Python matches direction based on hot_list

buildObdivPayload(symbol, bull_ob, bull_div, bear_ob, bear_div, timestamp) =>
    '{' +
    '"tier":"obdiv",' +
    '"symbol":"' + symbol + '",' +
    '"bull_ob":' + formatObObject(bull_ob) + ',' +
    '"bull_div":' + formatDivObject(bull_div) + ',' +
    '"bear_ob":' + formatObObject(bear_ob) + ',' +
    '"bear_div":' + formatDivObject(bear_div) + ',' +
    '"timestamp":' + str.tostring(timestamp) +
    '}'

// Example output:
// {
//   "tier": "obdiv",
//   "symbol": "GBPAUD",
//   "bull_ob": {"found": true, "tf": "W1", "type": "OB", "high": 1.0550, "low": 1.0500},
//   "bull_div": {"found": true, "tf": "H4", "type": "Logic2"},
//   "bear_ob": {"found": false},
//   "bear_div": {"found": false},
//   "timestamp": 1672531200
// }
```

#### 2.2.6 Key Differences from TTE Screener

| Aspect | TTE Screener (Original) | TTE OBDIV Screener |
|--------|-------------------------|---------------------|
| NWE Calculation | Yes | **No** (removed) |
| Table Display | Yes | **No** (removed) |
| Symbols | 8 (fixed) | 8 (dynamic) |
| Output | Table + Alert | **Webhook only** |
| Direction | Single (based on NWE) | **Both** (bull + bear) |

---

## 3. API Specifications

### 3.1 Base URL

```
Production: https://stock-buddy-app.vercel.app/api
Development: http://localhost:3000/api
```

### 3.2 Common Headers

```
Content-Type: application/json
```

### 3.3 Endpoint: POST /api/nwe

#### Purpose
Receive Tier 1 NWE alerts, add/update hot list entry.

#### Request

```typescript
// Request Body
interface NweWebhookRequest {
  tier: "nwe";
  symbol: string;           // e.g., "GBPAUD"
  direction: "bullish" | "bearish";
  timeframes: string[];     // e.g., ["H4", "D1"]
  timestamp: number;        // Unix timestamp
}
```

#### Response

```typescript
// Success Response (200)
interface NweWebhookResponse {
  success: true;
  action: "inserted" | "updated";
  symbol: string;
  id: string;               // MongoDB ObjectId
}

// Error Response (400)
interface NweErrorResponse {
  success: false;
  error: string;
  code: "INVALID_PAYLOAD" | "MISSING_FIELD" | "INVALID_DIRECTION";
}

// Error Response (500)
interface NweServerError {
  success: false;
  error: "Internal server error";
  code: "DB_ERROR" | "UNKNOWN";
}
```

#### Implementation

```typescript
// pages/api/nwe.ts
import { NextApiRequest, NextApiResponse } from 'next';
import clientPromise from '@/lib/mongodb';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { tier, symbol, direction, timeframes, timestamp } = req.body;

    // Validation
    if (tier !== 'nwe') {
      return res.status(400).json({
        success: false,
        error: 'Invalid tier',
        code: 'INVALID_PAYLOAD'
      });
    }
    if (!symbol || typeof symbol !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'Missing or invalid symbol',
        code: 'MISSING_FIELD'
      });
    }
    if (!['bullish', 'bearish'].includes(direction)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid direction',
        code: 'INVALID_DIRECTION'
      });
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
          updated_at: new Date()
        }
      },
      { upsert: true }
    );

    const action = result.upsertedCount > 0 ? 'inserted' : 'updated';
    const id = result.upsertedId?.toString() || 'existing';

    console.log(`[NWE] ${action} hot_list entry for ${symbol} (${direction})`);

    res.status(200).json({ success: true, action, symbol, id });
  } catch (error) {
    console.error('[NWE] Error:', error);
    res.status(500).json({
      success: false,
      error: 'Internal server error',
      code: 'DB_ERROR'
    });
  }
}
```

### 3.4 Endpoint: POST /api/obdiv

#### Purpose
Receive Tier 2 OB+DIV alerts, combine with NWE direction, create final signal.

#### Request

```typescript
interface ObdivWebhookRequest {
  tier: "obdiv";
  symbol: string;
  bull_ob: ObFinding;
  bull_div: DivFinding;
  bear_ob: ObFinding;
  bear_div: DivFinding;
  timestamp: number;
}

interface ObFinding {
  found: boolean;
  tf?: string;              // "H4" | "D1" | "W1"
  type?: string;            // "OB" | "FVG" | "Breaker"
  high?: number;
  low?: number;
}

interface DivFinding {
  found: boolean;
  tf?: string;              // "H4" | "D1"
  type?: string;            // "Logic2" | "Internal" | "Logic1"
}
```

#### Response

```typescript
// Success Response (200) - Signal created
interface ObdivSuccessResponse {
  success: true;
  signal_created: true;
  signal_id: string;
  level: 1 | 2 | 3;
  direction: "bullish" | "bearish";
}

// Success Response (200) - No signal (not in hot list)
interface ObdivNoSignalResponse {
  success: true;
  signal_created: false;
  reason: "not_in_hot_list" | "no_matching_direction";
}

// Error Response (400/500)
interface ObdivErrorResponse {
  success: false;
  error: string;
  code: string;
}
```

#### Implementation

```typescript
// pages/api/obdiv.ts
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { symbol, bull_ob, bull_div, bear_ob, bear_div, timestamp } = req.body;

    const client = await clientPromise;
    const db = client.db('tte');

    // Find hot symbol to get NWE direction
    const hotSymbol = await db.collection('hot_list').findOne({
      symbol,
      status: { $in: ['pending_tier2', 'tier2_complete'] }
    });

    if (!hotSymbol) {
      console.log(`[OBDIV] ${symbol} not in hot_list, ignoring`);
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
    let level = 1; // NWE only (from hot_list)
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
      ob_high: ob?.high || null,
      ob_low: ob?.low || null,
      div_tf: div?.tf || null,
      div_type: div?.type || null,
      timestamp: timestamp || Math.floor(Date.now() / 1000),
      screenshot_url: null,
      status: 'pending_screenshot',
      created_at: new Date()
    };

    const result = await db.collection('signals').insertOne(signal);

    // Update hot_list status
    await db.collection('hot_list').updateOne(
      { symbol },
      { $set: { status: 'tier2_complete', last_checked: new Date() } }
    );

    console.log(`[OBDIV] Created Level ${level} signal for ${symbol} (${hotSymbol.direction})`);

    res.status(200).json({
      success: true,
      signal_created: true,
      signal_id: result.insertedId.toString(),
      level,
      direction: hotSymbol.direction
    });
  } catch (error) {
    console.error('[OBDIV] Error:', error);
    res.status(500).json({ success: false, error: 'Internal server error' });
  }
}
```

### 3.5 Endpoint: GET /api/signals

#### Purpose
Fetch signals for dashboard display.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | number | 50 | Max results (1-100) |
| `offset` | number | 0 | Pagination offset |
| `level` | number | - | Filter by level (1, 2, 3) |
| `direction` | string | - | Filter by direction |
| `status` | string | - | Filter by status |
| `symbol` | string | - | Filter by symbol (partial match) |
| `from` | number | - | Unix timestamp (start) |
| `to` | number | - | Unix timestamp (end) |
| `sort` | string | "created_at" | Sort field |
| `order` | string | "desc" | Sort order (asc/desc) |

#### Response

```typescript
interface SignalsResponse {
  success: true;
  data: Signal[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
  };
}

interface Signal {
  _id: string;
  symbol: string;
  direction: "bullish" | "bearish";
  level: 1 | 2 | 3;
  nwe_tf: string[];
  ob_tf: string | null;
  ob_type: string | null;
  div_tf: string | null;
  div_type: string | null;
  screenshot_url: string | null;
  status: "pending_screenshot" | "complete";
  created_at: string;        // ISO 8601
  timestamp: number;         // Unix timestamp
}
```

### 3.6 Endpoint: GET /api/hot-symbols

#### Purpose
Python orchestrator polls this to get symbols needing Tier 2 check.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | "pending_tier2" | Filter by status |
| `limit` | number | 8 | Max results (matches OBDIV capacity) |

#### Response

```typescript
interface HotSymbolsResponse {
  success: true;
  data: HotSymbol[];
  count: number;
}

interface HotSymbol {
  symbol: string;
  direction: "bullish" | "bearish";
  nwe_timeframes: string[];
  nwe_timestamp: number;
  status: string;
  updated_at: string;
}
```

### 3.7 Endpoint: PATCH /api/signals/[id]

#### Purpose
Update signal with screenshot URL or status.

#### Request

```typescript
interface UpdateSignalRequest {
  screenshot_url?: string;
  status?: "pending_screenshot" | "complete" | "screenshot_failed";
}
```

#### Response

```typescript
interface UpdateSignalResponse {
  success: true;
  updated: true;
  signal_id: string;
}
```

### 3.8 Error Codes Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_PAYLOAD` | 400 | Request body malformed or missing required fields |
| `MISSING_FIELD` | 400 | Required field not provided |
| `INVALID_DIRECTION` | 400 | Direction must be "bullish" or "bearish" |
| `INVALID_TIER` | 400 | Tier must be "nwe" or "obdiv" |
| `NOT_FOUND` | 404 | Resource not found |
| `DB_ERROR` | 500 | Database operation failed |
| `UNKNOWN` | 500 | Unexpected error |

---

## 4. Database Specifications

### 4.1 Connection Configuration

```typescript
// lib/mongodb.ts
import { MongoClient } from 'mongodb';

const uri = process.env.MONGODB_URI;
const options = {
  maxPoolSize: 10,
  minPoolSize: 5,
  maxIdleTimeMS: 60000,
  connectTimeoutMS: 10000,
  socketTimeoutMS: 45000,
};

let client: MongoClient;
let clientPromise: Promise<MongoClient>;

if (process.env.NODE_ENV === 'development') {
  // Use global variable in development to preserve connection across hot reloads
  if (!global._mongoClientPromise) {
    client = new MongoClient(uri, options);
    global._mongoClientPromise = client.connect();
  }
  clientPromise = global._mongoClientPromise;
} else {
  client = new MongoClient(uri, options);
  clientPromise = client.connect();
}

export default clientPromise;
```

### 4.2 Database: `tte`

### 4.3 Collection: `hot_list`

#### Schema

```typescript
interface HotListDocument {
  _id: ObjectId;
  symbol: string;                    // "GBPAUD" - unique
  direction: "bullish" | "bearish";
  nwe_timeframes: string[];          // ["H4", "D1"]
  nwe_timestamp: number;             // Unix timestamp when NWE triggered
  status: "pending_tier2" | "tier2_complete" | "expired";
  updated_at: Date;
  last_checked: Date | null;
}
```

#### Indexes

```javascript
// Create indexes
db.hot_list.createIndex({ symbol: 1 }, { unique: true });
db.hot_list.createIndex({ status: 1, updated_at: -1 });
db.hot_list.createIndex({ updated_at: 1 }, { expireAfterSeconds: 86400 }); // TTL: 24 hours
```

#### Index Rationale

| Index | Purpose | Query Pattern |
|-------|---------|---------------|
| `{ symbol: 1 }` | Unique constraint, fast lookup | `findOne({ symbol })` |
| `{ status: 1, updated_at: -1 }` | Get pending symbols sorted by time | `find({ status: "pending_tier2" }).sort({ updated_at: -1 })` |
| `{ updated_at: 1 }` TTL | Auto-delete expired entries | N/A (automatic) |

### 4.4 Collection: `signals`

#### Schema

```typescript
interface SignalDocument {
  _id: ObjectId;
  symbol: string;                    // "GBPAUD"
  direction: "bullish" | "bearish";
  level: 1 | 2 | 3;
  nwe_tf: string[];                  // ["H4", "D1"]
  ob_tf: string | null;              // "W1"
  ob_type: string | null;            // "OB", "FVG", "Breaker"
  ob_high: number | null;            // OB zone upper bound
  ob_low: number | null;             // OB zone lower bound
  div_tf: string | null;             // "H4"
  div_type: string | null;           // "Logic2", "Internal", "Logic1"
  timestamp: number;                 // Unix timestamp from alert
  screenshot_url: string | null;     // TradingView snapshot URL
  status: "pending_screenshot" | "complete" | "screenshot_failed";
  created_at: Date;
  updated_at: Date | null;
}
```

#### Indexes

```javascript
// Create indexes
db.signals.createIndex({ created_at: -1 });
db.signals.createIndex({ status: 1 });
db.signals.createIndex({ level: 1 });
db.signals.createIndex({ symbol: 1 });
db.signals.createIndex({ direction: 1 });
db.signals.createIndex({ symbol: 1, created_at: -1 });
```

#### Index Rationale

| Index | Purpose | Query Pattern |
|-------|---------|---------------|
| `{ created_at: -1 }` | Dashboard default sort | `find().sort({ created_at: -1 })` |
| `{ status: 1 }` | Find pending screenshots | `find({ status: "pending_screenshot" })` |
| `{ level: 1 }` | Filter by signal level | `find({ level: 3 })` |
| `{ symbol: 1 }` | Search by symbol | `find({ symbol: /GBPAUD/i })` |
| `{ direction: 1 }` | Filter by direction | `find({ direction: "bullish" })` |
| `{ symbol: 1, created_at: -1 }` | Symbol history | `find({ symbol }).sort({ created_at: -1 })` |

### 4.5 Sample Documents

#### hot_list

```json
{
  "_id": { "$oid": "65b7c1234567890abcdef123" },
  "symbol": "GBPAUD",
  "direction": "bullish",
  "nwe_timeframes": ["H4", "D1"],
  "nwe_timestamp": 1672531200,
  "status": "pending_tier2",
  "updated_at": { "$date": "2026-01-29T12:00:00.000Z" },
  "last_checked": null
}
```

#### signals

```json
{
  "_id": { "$oid": "65b7c1234567890abcdef456" },
  "symbol": "GBPAUD",
  "direction": "bullish",
  "level": 3,
  "nwe_tf": ["H4", "D1"],
  "ob_tf": "W1",
  "ob_type": "OB",
  "ob_high": 1.0550,
  "ob_low": 1.0500,
  "div_tf": "H4",
  "div_type": "Logic2",
  "timestamp": 1672531200,
  "screenshot_url": "https://www.tradingview.com/x/ABC123DEF/",
  "status": "complete",
  "created_at": { "$date": "2026-01-29T12:05:00.000Z" },
  "updated_at": { "$date": "2026-01-29T12:07:00.000Z" }
}
```

---

## 5. Python Orchestrator Specifications

### 5.1 Class Structure

```python
# tiered_orchestrator.py

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import logging

logger = logging.getLogger(__name__)

@dataclass
class HotSymbol:
    symbol: str
    direction: str
    nwe_timeframes: List[str]
    nwe_timestamp: int
    status: str
    updated_at: str

@dataclass
class PendingSignal:
    id: str
    symbol: str
    direction: str
    level: int
    nwe_tf: List[str]

class TieredOrchestrator:
    """Orchestrates the tiered screener workflow."""

    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.api_base = "https://stock-buddy-app.vercel.app/api"
        self.poll_interval = 60  # seconds
        self.batch_size = 8      # OBDIV screener capacity

    def run(self):
        """Main orchestration loop."""
        pass

    def get_hot_symbols(self) -> List[HotSymbol]:
        """Fetch hot symbols from API."""
        pass

    def update_obdiv_screener(self, symbols: List[HotSymbol]):
        """Update OBDIV Screener symbol inputs via Selenium."""
        pass

    def get_pending_screenshots(self) -> List[PendingSignal]:
        """Fetch signals needing screenshots."""
        pass

    def capture_screenshot(self, signal: PendingSignal) -> Optional[str]:
        """Navigate to chart and capture screenshot."""
        pass

    def update_signal_screenshot(self, signal_id: str, url: str):
        """Update signal with screenshot URL."""
        pass
```

### 5.2 Main Loop Implementation

```python
def run(self):
    """Main orchestration loop."""
    logger.info("Starting TieredOrchestrator")

    while True:
        try:
            # Step 1: Get hot symbols needing Tier 2 check
            hot_symbols = self.get_hot_symbols()

            if hot_symbols:
                logger.info(f"Found {len(hot_symbols)} hot symbols")

                # Step 2: Process in batches of 8
                for i in range(0, len(hot_symbols), self.batch_size):
                    batch = hot_symbols[i:i + self.batch_size]
                    logger.info(f"Processing batch {i // self.batch_size + 1}: {[s.symbol for s in batch]}")

                    # Step 3: Update OBDIV Screener with batch
                    self.update_obdiv_screener(batch)

                    # Step 4: Wait for screener to recalculate and fire webhooks
                    time.sleep(30)

            # Step 5: Process signals needing screenshots
            pending = self.get_pending_screenshots()
            for signal in pending:
                try:
                    url = self.capture_screenshot(signal)
                    if url:
                        self.update_signal_screenshot(signal.id, url)
                        logger.info(f"Screenshot captured for {signal.symbol}: {url}")
                    else:
                        logger.warning(f"Failed to capture screenshot for {signal.symbol}")
                except Exception as e:
                    logger.exception(f"Screenshot error for {signal.symbol}: {e}")

        except Exception as e:
            logger.exception(f"Orchestrator error: {e}")

        # Poll interval
        time.sleep(self.poll_interval)
```

### 5.3 API Interaction Methods

```python
def get_hot_symbols(self) -> List[HotSymbol]:
    """Fetch hot symbols from API."""
    try:
        response = requests.get(
            f"{self.api_base}/hot-symbols",
            params={"status": "pending_tier2", "limit": self.batch_size * 2},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        return [
            HotSymbol(
                symbol=item['symbol'],
                direction=item['direction'],
                nwe_timeframes=item.get('nwe_timeframes', []),
                nwe_timestamp=item.get('nwe_timestamp', 0),
                status=item['status'],
                updated_at=item.get('updated_at', '')
            )
            for item in data.get('data', [])
        ]
    except requests.RequestException as e:
        logger.error(f"Failed to fetch hot symbols: {e}")
        return []

def get_pending_screenshots(self) -> List[PendingSignal]:
    """Fetch signals needing screenshots."""
    try:
        response = requests.get(
            f"{self.api_base}/signals",
            params={"status": "pending_screenshot", "limit": 10},
            timeout=10
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

def update_signal_screenshot(self, signal_id: str, url: str):
    """Update signal with screenshot URL."""
    try:
        response = requests.patch(
            f"{self.api_base}/signals/{signal_id}",
            json={"screenshot_url": url, "status": "complete"},
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"Updated signal {signal_id} with screenshot")
    except requests.RequestException as e:
        logger.error(f"Failed to update signal {signal_id}: {e}")
        raise
```

### 5.4 Configuration

```python
# config.py

class OrchestratorConfig:
    # API
    API_BASE_URL = "https://stock-buddy-app.vercel.app/api"
    API_TIMEOUT = 10  # seconds

    # Polling
    POLL_INTERVAL = 60  # seconds
    BATCH_SIZE = 8      # OBDIV screener capacity

    # Selenium
    IMPLICIT_WAIT = 10  # seconds
    EXPLICIT_WAIT = 30  # seconds
    PAGE_LOAD_TIMEOUT = 60  # seconds

    # Screenshot
    SCREENSHOT_WAIT = 2  # seconds to wait before capture
    MAX_SCREENSHOT_RETRIES = 3

    # TradingView
    TV_BASE_URL = "https://www.tradingview.com/chart"
    OBDIV_INDICATOR_NAME = "TTE OBDIV Screener"
```

---

## 6. Selenium Automation Specifications

### 6.1 WebDriver Configuration

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def create_driver(profile_path: str) -> webdriver.Chrome:
    """Create configured Chrome WebDriver."""
    options = Options()

    # Use existing Chrome profile (for TradingView login)
    options.add_argument(f"user-data-dir={profile_path}")

    # Performance options
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Window size for consistent screenshots
    options.add_argument("--window-size=1920,1080")

    # Disable automation flags (reduce detection)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    driver.set_page_load_timeout(60)

    return driver
```

### 6.2 Selector Specifications

#### TradingView Indicator Settings

| Element | Selector Type | Selector Value | Notes |
|---------|---------------|----------------|-------|
| Indicator in legend | CSS | `div[data-name="legend-source-item"]` | Contains indicator name |
| Indicator title | CSS | `div[class*="title"]` | Text content has indicator name |
| Settings dialog | CSS | `div[data-name="indicator-properties-dialog"]` | Modal container |
| Symbol input | CSS | `input[data-property-id*="symbol"]` | Multiple (one per symbol) |
| OK button | CSS | `button[name="submit"]` | Closes dialog and applies |
| Cancel button | CSS | `button[name="cancel"]` | Closes without applying |

#### TradingView Chart

| Element | Selector Type | Selector Value | Notes |
|---------|---------------|----------------|-------|
| Symbol input | CSS | `input[data-role="search"]` | Main symbol search |
| Timeframe selector | CSS | `button[data-name="time-interval-button"]` | Opens timeframe menu |
| Timeframe option | XPath | `//div[text()="4h"]` | Specific timeframe |
| Screenshot button | CSS | `button[data-name="save-chart-image"]` | Opens save dialog |
| Snapshot option | CSS | `div[data-name="publish-chart-image"]` | TradingView snapshot |

### 6.3 Update OBDIV Screener Implementation

```python
def update_obdiv_screener(self, symbols: List[HotSymbol]):
    """Update OBDIV Screener symbol inputs via Selenium."""
    try:
        # Step 1: Find and double-click indicator to open settings
        if not self._open_indicator_settings(Config.OBDIV_INDICATOR_NAME):
            raise Exception(f"Could not find indicator: {Config.OBDIV_INDICATOR_NAME}")

        time.sleep(1)  # Wait for dialog to open

        # Step 2: Find all symbol inputs
        wait = WebDriverWait(self.driver, Config.EXPLICIT_WAIT)
        symbol_inputs = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'input[data-property-id*="symbol"]')
            )
        )

        # Step 3: Update each symbol input
        for i, hot_symbol in enumerate(symbols[:8]):
            if i < len(symbol_inputs):
                self._set_input_value(symbol_inputs[i], hot_symbol.symbol)
                logger.debug(f"Set symbol {i+1} to {hot_symbol.symbol}")

        # Step 4: Clear remaining inputs if fewer than 8 symbols
        for i in range(len(symbols), min(8, len(symbol_inputs))):
            self._set_input_value(symbol_inputs[i], "")

        # Step 5: Click OK to apply
        self._click_ok_button()

        logger.info(f"Updated OBDIV Screener with {len(symbols)} symbols")

    except Exception as e:
        logger.exception(f"Failed to update OBDIV Screener: {e}")
        # Try to close any open dialog
        self._press_escape()
        raise

def _open_indicator_settings(self, indicator_name: str) -> bool:
    """Open settings dialog for an indicator by double-clicking it."""
    try:
        indicators = self.driver.find_elements(
            By.CSS_SELECTOR, 'div[data-name="legend-source-item"]'
        )

        for indicator in indicators:
            try:
                title_elem = indicator.find_element(By.CSS_SELECTOR, 'div[class*="title"]')
                if indicator_name.lower() in title_elem.text.lower():
                    ActionChains(self.driver).double_click(indicator).perform()
                    return True
            except:
                continue

        return False
    except Exception as e:
        logger.error(f"Error opening indicator settings: {e}")
        return False

def _set_input_value(self, input_element, value: str):
    """Clear and set value for an input element."""
    input_element.click()
    input_element.send_keys(Keys.CONTROL + "a")
    input_element.send_keys(Keys.DELETE)
    if value:
        input_element.send_keys(value)
        input_element.send_keys(Keys.TAB)  # Trigger validation

def _click_ok_button(self):
    """Click OK button in settings dialog."""
    wait = WebDriverWait(self.driver, Config.EXPLICIT_WAIT)
    ok_button = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="submit"]'))
    )
    ok_button.click()

def _press_escape(self):
    """Press Escape to close any open dialog."""
    ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
```

### 6.4 Screenshot Capture Implementation

```python
def capture_screenshot(self, signal: PendingSignal) -> Optional[str]:
    """Navigate to chart and capture screenshot."""
    try:
        # Step 1: Change to signal's symbol
        self._change_symbol(signal.symbol)
        time.sleep(1)

        # Step 2: Change to first NWE timeframe
        tf = signal.nwe_tf[0] if signal.nwe_tf else "240"  # Default to H4
        self._change_timeframe(tf)
        time.sleep(Config.SCREENSHOT_WAIT)

        # Step 3: Take screenshot via TradingView snapshot
        snapshot_url = self._take_tradingview_snapshot()

        return snapshot_url

    except Exception as e:
        logger.exception(f"Screenshot capture failed: {e}")
        return None

def _change_symbol(self, symbol: str):
    """Change chart to specified symbol."""
    wait = WebDriverWait(self.driver, Config.EXPLICIT_WAIT)

    # Click on symbol search
    search_input = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[data-role="search"]'))
    )
    search_input.click()
    search_input.send_keys(Keys.CONTROL + "a")
    search_input.send_keys(symbol)
    time.sleep(0.5)
    search_input.send_keys(Keys.ENTER)

def _change_timeframe(self, timeframe: str):
    """Change chart to specified timeframe."""
    # Map Pine Script timeframe to TradingView UI
    tf_map = {
        "240": "4h",
        "D": "1D",
        "W": "1W",
        "60": "1h",
        "15": "15m"
    }
    tf_label = tf_map.get(timeframe, timeframe)

    wait = WebDriverWait(self.driver, Config.EXPLICIT_WAIT)

    # Click timeframe button
    tf_button = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-name="time-interval-button"]'))
    )
    tf_button.click()
    time.sleep(0.3)

    # Select timeframe
    tf_option = wait.until(
        EC.element_to_be_clickable((By.XPATH, f'//div[text()="{tf_label}"]'))
    )
    tf_option.click()

def _take_tradingview_snapshot(self) -> Optional[str]:
    """Take TradingView snapshot and return URL."""
    wait = WebDriverWait(self.driver, Config.EXPLICIT_WAIT)

    # Click camera/screenshot button
    screenshot_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-name="save-chart-image"]'))
    )
    screenshot_btn.click()
    time.sleep(0.3)

    # Click "Publish snapshot" option
    snapshot_option = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="publish-chart-image"]'))
    )
    snapshot_option.click()

    # Wait for upload and get URL
    time.sleep(2)

    # Get URL from clipboard or success message
    # Implementation depends on TradingView's current UI
    # May need to extract from notification or clipboard

    return self._extract_snapshot_url()

def _extract_snapshot_url(self) -> Optional[str]:
    """Extract snapshot URL after publishing."""
    # Try to get from success notification
    try:
        wait = WebDriverWait(self.driver, 10)
        notification = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div[class*="notification"] a[href*="tradingview.com/x/"]')
            )
        )
        return notification.get_attribute("href")
    except:
        pass

    # Fallback: try clipboard
    try:
        import pyperclip
        url = pyperclip.paste()
        if "tradingview.com/x/" in url:
            return url
    except:
        pass

    return None
```

---

## 7. Dashboard Specifications

### 7.1 Component Hierarchy

```
app/
├── dashboard/
│   └── page.tsx                    # Main dashboard page
├── components/
│   └── dashboard/
│       ├── Header.tsx              # Logo, notifications, profile
│       ├── StatsGrid.tsx           # Statistics cards container
│       │   └── StatsCard.tsx       # Individual stat card
│       ├── FilterBar.tsx           # Filter controls
│       │   ├── FilterDropdown.tsx  # Dropdown selector
│       │   ├── SearchInput.tsx     # Symbol search
│       │   └── LiveIndicator.tsx   # Real-time status
│       ├── SignalsTable.tsx        # Desktop table view
│       │   ├── TableHeader.tsx     # Column headers with sort
│       │   └── TableRow.tsx        # Signal row
│       ├── CardGrid.tsx            # Mobile card view
│       │   └── SignalCard.tsx      # Individual signal card
│       ├── ActionButtons.tsx       # Screenshot, chart, share buttons
│       ├── Pagination.tsx          # Page navigation
│       ├── ScreenshotModal.tsx     # Screenshot viewer
│       ├── DistributionChart.tsx   # Level distribution bar chart
│       └── ToastNotification.tsx   # New signal alerts
├── hooks/
│   ├── useSignals.ts               # React Query hook for signals
│   ├── useStats.ts                 # Stats aggregation hook
│   └── useRealtime.ts              # Real-time updates hook
└── lib/
    └── api.ts                      # API client functions
```

### 7.2 Component Specifications

#### StatsCard

```typescript
interface StatsCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  trend?: {
    direction: "up" | "down" | "neutral";
    percentage: number;
  };
  color: "default" | "gold" | "green" | "red";
}

// Usage
<StatsCard
  title="Level 3 Signals"
  value={12}
  icon={<StarIcon />}
  trend={{ direction: "up", percentage: 25 }}
  color="gold"
/>
```

#### FilterBar State

```typescript
interface FilterState {
  level: number | null;           // null = all
  direction: "bullish" | "bearish" | null;
  symbol: string;                  // search query
  period: "24h" | "7d" | "30d" | "all";
  status: "all" | "complete" | "pending_screenshot";
  screenshotOnly: boolean;
  sort: {
    field: "created_at" | "level" | "symbol";
    order: "asc" | "desc";
  };
}
```

#### SignalsTable Column Definitions

```typescript
const columns = [
  { key: "created_at", label: "Time", width: "100px", sortable: true },
  { key: "symbol", label: "Symbol", width: "100px", sortable: true },
  { key: "direction", label: "Direction", width: "80px", sortable: true },
  { key: "level", label: "Level", width: "80px", sortable: true },
  { key: "nwe_tf", label: "NWE", width: "80px", sortable: false },
  { key: "ob_tf", label: "OB", width: "60px", sortable: false },
  { key: "div_tf", label: "DIV", width: "60px", sortable: false },
  { key: "actions", label: "Actions", width: "100px", sortable: false },
];
```

### 7.3 Styling Tokens

```css
/* Color palette */
:root {
  /* Signal levels */
  --level-3-bg: #FEF3C7;        /* Amber 100 */
  --level-3-border: #F59E0B;    /* Amber 500 */
  --level-3-text: #92400E;      /* Amber 800 */

  --level-2-bg: #E0E7FF;        /* Indigo 100 */
  --level-2-border: #6366F1;    /* Indigo 500 */
  --level-2-text: #3730A3;      /* Indigo 800 */

  --level-1-bg: #F3F4F6;        /* Gray 100 */
  --level-1-border: #9CA3AF;    /* Gray 400 */
  --level-1-text: #374151;      /* Gray 700 */

  /* Directions */
  --bullish-bg: #D1FAE5;        /* Emerald 100 */
  --bullish-text: #059669;      /* Emerald 600 */
  --bullish-icon: #10B981;      /* Emerald 500 */

  --bearish-bg: #FEE2E2;        /* Red 100 */
  --bearish-text: #DC2626;      /* Red 600 */
  --bearish-icon: #EF4444;      /* Red 500 */

  /* Status */
  --status-live: #10B981;       /* Emerald 500 */
  --status-pending: #F59E0B;    /* Amber 500 */
  --status-error: #EF4444;      /* Red 500 */
}
```

### 7.4 Responsive Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | < 640px | CardGrid, single column stats |
| Tablet | 640px - 1024px | CardGrid, 2-column stats |
| Desktop | > 1024px | SignalsTable, 5-column stats |

### 7.5 API Hook Implementation

```typescript
// hooks/useSignals.ts
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Signal, FilterState } from '@/types';
import { fetchSignals } from '@/lib/api';

export function useSignals(filters: FilterState) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['signals', filters],
    queryFn: () => fetchSignals(filters),
    staleTime: 30 * 1000,        // 30 seconds
    refetchInterval: 60 * 1000,  // 1 minute auto-refresh
  });

  // Manual refresh function
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['signals'] });
  };

  return {
    ...query,
    refresh,
  };
}
```

---

## 8. Sequence Diagrams

### 8.1 Complete Signal Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  NWE    │     │  Stock  │     │  Python │     │  OBDIV  │     │Dashboard│
│Screener │     │  Buddy  │     │  Orch.  │     │Screener │     │         │
└────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘
     │               │               │               │               │
     │  NWE Zone     │               │               │               │
     │  Detected     │               │               │               │
     │───────────────>               │               │               │
     │  POST /api/nwe│               │               │               │
     │               │               │               │               │
     │               │ Insert        │               │               │
     │               │ hot_list      │               │               │
     │               │──────┐        │               │               │
     │               │      │        │               │               │
     │               │<─────┘        │               │               │
     │               │               │               │               │
     │               │  GET          │               │               │
     │               │<──────────────│               │               │
     │               │ /hot-symbols  │               │               │
     │               │               │               │               │
     │               │ Return        │               │               │
     │               │ pending       │               │               │
     │               │───────────────>               │               │
     │               │               │               │               │
     │               │               │  Selenium:    │               │
     │               │               │  Update       │               │
     │               │               │  symbols      │               │
     │               │               │───────────────>               │
     │               │               │               │               │
     │               │               │               │  OB/DIV       │
     │               │               │               │  Detection    │
     │               │               │               │──────┐        │
     │               │               │               │      │        │
     │               │               │               │<─────┘        │
     │               │               │               │               │
     │               │  POST         │               │               │
     │               │<──────────────────────────────│               │
     │               │  /api/obdiv   │               │               │
     │               │               │               │               │
     │               │ Create        │               │               │
     │               │ signal        │               │               │
     │               │──────┐        │               │               │
     │               │      │        │               │               │
     │               │<─────┘        │               │               │
     │               │               │               │               │
     │               │  GET          │               │               │
     │               │<──────────────│               │               │
     │               │ /signals?     │               │               │
     │               │ pending       │               │               │
     │               │               │               │               │
     │               │ Return        │               │               │
     │               │ pending       │               │               │
     │               │───────────────>               │               │
     │               │               │               │               │
     │               │               │  Selenium:    │               │
     │               │               │  Screenshot   │               │
     │               │               │──────────────────────────────>│
     │               │               │               │               │
     │               │  PATCH        │               │               │
     │               │<──────────────│               │               │
     │               │  /signals/id  │               │               │
     │               │               │               │               │
     │               │               │               │               │
     │               │  GET          │               │               │
     │               │<──────────────────────────────────────────────│
     │               │  /signals     │               │               │
     │               │               │               │               │
     │               │ Return        │               │               │
     │               │ signals       │               │               │
     │               │───────────────────────────────────────────────>
     │               │               │               │               │
     ▼               ▼               ▼               ▼               ▼
```

### 8.2 Hot Symbol Batch Processing

```
┌─────────┐          ┌─────────┐          ┌─────────┐
│  Python │          │  Stock  │          │  OBDIV  │
│  Orch.  │          │  Buddy  │          │Screener │
└────┬────┘          └────┬────┘          └────┬────┘
     │                    │                    │
     │  GET /hot-symbols  │                    │
     │  limit=16          │                    │
     │───────────────────>│                    │
     │                    │                    │
     │  Returns 10        │                    │
     │  hot symbols       │                    │
     │<───────────────────│                    │
     │                    │                    │
     │  Batch 1 (8)       │                    │
     │  Update symbols    │                    │
     │────────────────────────────────────────>│
     │                    │                    │
     │  Wait 30s          │                    │
     │  (recalculation)   │                    │
     │                    │                    │
     │                    │  Webhooks for      │
     │                    │  batch 1           │
     │                    │<───────────────────│
     │                    │                    │
     │  Batch 2 (2)       │                    │
     │  Update symbols    │                    │
     │────────────────────────────────────────>│
     │                    │                    │
     │  Wait 30s          │                    │
     │                    │                    │
     │                    │  Webhooks for      │
     │                    │  batch 2           │
     │                    │<───────────────────│
     │                    │                    │
     ▼                    ▼                    ▼
```

---

## 9. Error Handling

### 9.1 Error Categories

| Category | Examples | Handling Strategy |
|----------|----------|-------------------|
| **Network** | Timeout, connection refused | Retry with exponential backoff |
| **Validation** | Invalid payload, missing fields | Return 400, log warning |
| **Database** | Connection lost, query timeout | Retry once, then fail gracefully |
| **Selenium** | Element not found, stale element | Retry with fresh locator |
| **TradingView** | Rate limit, session expired | Pause and retry, re-authenticate |

### 9.2 Retry Configuration

```python
# Python retry decorator
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError))
)
def api_call_with_retry(url, **kwargs):
    response = requests.get(url, timeout=10, **kwargs)
    response.raise_for_status()
    return response.json()
```

### 9.3 Selenium Error Recovery

```python
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    NoSuchElementException
)

def safe_click(driver, selector, max_attempts=3):
    """Click element with retry on stale reference."""
    for attempt in range(max_attempts):
        try:
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            element.click()
            return True
        except StaleElementReferenceException:
            if attempt == max_attempts - 1:
                raise
            time.sleep(0.5)
    return False
```

### 9.4 API Error Responses

```typescript
// Standard error response format
interface ApiError {
  success: false;
  error: string;           // Human-readable message
  code: string;            // Machine-readable code
  details?: object;        // Additional context
  timestamp: string;       // ISO 8601
  requestId?: string;      // For debugging
}

// Example
{
  "success": false,
  "error": "Symbol not found in hot list",
  "code": "NOT_IN_HOT_LIST",
  "details": { "symbol": "GBPAUD" },
  "timestamp": "2026-01-29T12:00:00.000Z",
  "requestId": "req_abc123"
}
```

---

## 10. Performance Requirements

### 10.1 Latency Targets

| Operation | Target | Maximum |
|-----------|--------|---------|
| Webhook delivery (TV → API) | < 500ms | 2s |
| API response (GET /signals) | < 200ms | 1s |
| Hot symbol polling | < 500ms | 2s |
| Screenshot capture | < 10s | 30s |
| Dashboard initial load | < 2s | 5s |
| Real-time update | < 1s | 3s |

### 10.2 Throughput Targets

| Metric | Target |
|--------|--------|
| Webhooks per minute | 100 |
| API requests per minute | 1000 |
| Concurrent dashboard users | 100 |
| Signals per day | 500 |

### 10.3 Database Query Optimization

```javascript
// Ensure queries use indexes
// Bad: Full collection scan
db.signals.find({ created_at: { $gt: date } }).sort({ level: -1 })

// Good: Uses compound index
db.signals.createIndex({ created_at: -1, level: -1 })
db.signals.find({ created_at: { $gt: date } }).sort({ created_at: -1, level: -1 })
```

### 10.4 Caching Strategy

| Data | Cache Duration | Cache Location |
|------|----------------|----------------|
| Statistics | 30 seconds | React Query |
| Signal list | 30 seconds | React Query |
| Hot symbols | 10 seconds | Python memory |
| Screenshots | Indefinite | TradingView CDN |

---

## 11. Security Considerations

### 11.1 Webhook Authentication

```typescript
// Option 1: Shared secret in header
// TradingView alert message includes: {"secret": "YOUR_SECRET", ...}

export default async function handler(req, res) {
  const { secret } = req.body;
  if (secret !== process.env.WEBHOOK_SECRET) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  // Process webhook...
}

// Option 2: IP allowlist (TradingView IPs)
// Note: TradingView IPs can change, use with caution
```

### 11.2 Input Validation

```typescript
import { z } from 'zod';

const NwePayloadSchema = z.object({
  tier: z.literal('nwe'),
  symbol: z.string().min(1).max(20).regex(/^[A-Z]{6}$/),
  direction: z.enum(['bullish', 'bearish']),
  timeframes: z.array(z.string()).min(1).max(5),
  timestamp: z.number().int().positive(),
});

export default async function handler(req, res) {
  const result = NwePayloadSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(400).json({
      success: false,
      error: 'Invalid payload',
      code: 'VALIDATION_ERROR',
      details: result.error.issues,
    });
  }
  // Process validated data...
}
```

### 11.3 Rate Limiting

```typescript
// Using Vercel Edge Config or Upstash Redis
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(100, '1 m'), // 100 requests per minute
});

export default async function handler(req, res) {
  const ip = req.headers['x-forwarded-for'] || 'anonymous';
  const { success, limit, remaining } = await ratelimit.limit(ip);

  if (!success) {
    return res.status(429).json({
      error: 'Rate limit exceeded',
      limit,
      remaining,
    });
  }
  // Process request...
}
```

### 11.4 Environment Variables

```bash
# Required environment variables
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/tte
WEBHOOK_SECRET=your-random-secret-here

# Optional
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=...
```

---

## 12. Monitoring and Logging

### 12.1 Logging Format

```python
# Python logging configuration
import logging
import json
from datetime import datetime

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

# Usage
logger = logging.getLogger("orchestrator")
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### 12.2 Key Metrics to Track

| Metric | Type | Description |
|--------|------|-------------|
| `nwe_webhooks_received` | Counter | Total NWE webhooks received |
| `obdiv_webhooks_received` | Counter | Total OBDIV webhooks received |
| `signals_created` | Counter | Total signals created (by level) |
| `screenshots_captured` | Counter | Successful screenshot captures |
| `screenshots_failed` | Counter | Failed screenshot captures |
| `hot_list_size` | Gauge | Current hot list size |
| `api_latency_ms` | Histogram | API response latency |
| `selenium_action_latency_ms` | Histogram | Selenium action latency |

### 12.3 Alert Conditions

| Condition | Threshold | Action |
|-----------|-----------|--------|
| API error rate | > 5% over 5 min | Alert + investigate |
| Screenshot failure rate | > 20% over 10 min | Alert + restart orchestrator |
| Hot list not draining | > 20 items for 1 hour | Alert + check Tier 2 |
| No webhooks received | 0 in 1 hour | Alert + check TradingView |
| Database connection failures | > 3 in 5 min | Alert + check MongoDB |

### 12.4 Health Check Endpoint

```typescript
// pages/api/health.ts
export default async function handler(req, res) {
  const checks = {
    api: true,
    database: false,
    timestamp: new Date().toISOString(),
  };

  try {
    const client = await clientPromise;
    await client.db('tte').command({ ping: 1 });
    checks.database = true;
  } catch (e) {
    checks.database = false;
  }

  const healthy = Object.values(checks).every(v => v === true || typeof v === 'string');

  res.status(healthy ? 200 : 503).json({
    status: healthy ? 'healthy' : 'unhealthy',
    checks,
  });
}
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-29 | Claude | Initial technical specification |

---

*This document provides the complete technical specification for the TTE Tiered Screener Architecture. For product requirements, see PRD.md. For implementation guide, see .claude/TIERED_ARCHITECTURE_IMPLEMENTATION_PLAN.md.*
