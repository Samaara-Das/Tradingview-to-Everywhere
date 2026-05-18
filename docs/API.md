# API Reference

Stock Buddy API reference and webhook documentation for TTE.

## Overview

The Stock Buddy API manages signal storage, symbol data, and combo mode live signals. TTE sends webhook payloads to Stock Buddy when TradingView alerts fire.

**Base URL**: `https://stockbuddy.co/api/tte`

---

## Authentication

Currently, the API does not require authentication. All endpoints are accessible via HTTP requests with JSON content type.

```python
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}
```

---

## Endpoints Reference

### Health Check

Check if the API is healthy and responding.

**Endpoint**: `GET /api/health`

**Note**: Health endpoint is at `/api/health`, not `/api/tte/health`

**Response**:
```json
{
  "status": "healthy"
}
```

---

### Initialization Check

Check the current initialization status of the TTE system.

**Endpoint**: `GET /api/tte/init`

**Response**:
```json
{
  "success": true,
  "initialized": true,
  "symbols": {
    "total": "<N>",
    "counts": {
      "A": "<N>",
      "B": "<N>",
      "C": "<N>",
      "total": "<N>"
    }
  },
  "rotation_state": {
    "batch_number": "<N>",
    "rotation_number": "<N>",
    "symbols_scanned": "<N>",
    "total_symbols": "<N>"
  }
}
```

---

### Initialize/Reset Rotation State

Initialize or reset the rotation state. Can optionally seed default symbols.

**Endpoint**: `POST /api/tte/init`

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `seed` | boolean | If `true`, seeds default symbols (destructive with force) |

**Request Body**:
```json
{
  "force": false,
  "symbols": [
    {"symbol": "EURUSD", "exchange": "FX", "priority": "A", "category": "forex"}
  ]
}
```

**Response (Success)**:
```json
{
  "success": true,
  "message": "TTE rotation state initialized successfully",
  "symbols": {
    "total": 8,
    "seeded": false,
    "reset": false,
    "counts": {"A": 8, "B": 0, "C": 0, "total": 8}
  },
  "rotation_state": {
    "batch_number": 0,
    "rotation_number": 0,
    "symbols_scanned_this_rotation": 0,
    "total_symbols": 8
  }
}
```

**Response (Already Initialized)**:
```json
{
  "success": false,
  "error": "Rotation state already initialized (Batch #6, Rotation #1). Use force=true to reset.",
  "code": "ALREADY_INITIALIZED"
}
```

---

### Get Statistics

Retrieve comprehensive system statistics including signals, hot list, rotation state, and symbol counts.

**Endpoint**: `GET /api/tte/stats`

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hours` | integer | 24 | Time period for signal statistics |

**Response**:
```json
{
  "success": true,
  "signals": {
    "total": 15,
    "level1": 8,
    "level2": 5,
    "level3": 2,
    "bullish": 9,
    "bearish": 6,
    "pendingScreenshots": 3
  },
  "hot_list": {
    "pending": 5,
    "complete": 12,
    "expired": 2
  },
  "rotation": {
    "batch_number": 6,
    "rotation_number": 1,
    "symbols_scanned_this_rotation": 120,
    "total_symbols": 941
  },
  "symbols": {
    "A": 28,
    "B": 150,
    "C": 763,
    "total": 941
  },
  "period_hours": 24
}
```

---

### Get Next Symbol Batch

Fetch the next batch of symbols for NWE (Tier 1) scanning. Uses priority-based rotation.

**Endpoint**: `GET /api/tte/symbols/next-batch`

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `size` | integer | 20 | Number of symbols to fetch (max 20 for NWE screener) |

**Response**:
```json
{
  "success": true,
  "batch": [
    {"symbol": "EURUSD", "exchange": "FX", "priority": "A"},
    {"symbol": "GBPUSD", "exchange": "FX", "priority": "A"},
    {"symbol": "USDJPY", "exchange": "FX", "priority": "B"}
  ],
  "count": 20,
  "rotation": {
    "batch_number": 6,
    "rotation_number": 1,
    "total_symbols": 941,
    "symbols_scanned_this_rotation": 120
  }
}
```

**Priority Rotation Logic**:
- Priority A symbols are always included in every batch
- Priority B symbols are included every 3rd rotation
- Priority C symbols are included every 10th rotation
- Remaining slots are filled with least-recently-scanned symbols

---

### Mark Symbols as Scanned

Mark symbols as scanned after NWE processing completes.

**Endpoint**: `POST /api/tte/symbols/mark-scanned`

**Request Body**:
```json
{
  "symbols": ["EURUSD", "GBPUSD", "USDJPY"]
}
```

**Response**:
```json
{
  "success": true,
  "marked_count": 20,
  "rotation_complete": false
}
```

---

### Import Symbols (Bulk)

Import symbols in bulk from TTE's symbol_settings.py format.

**Endpoint**: `POST /api/tte/symbols/import`

**Request Body**:
```json
{
  "symbols": [
    {"symbol": "EURUSD", "exchange": "FX", "priority": "A", "category": "forex"},
    {"symbol": "AAPL", "exchange": "STOCKS", "priority": "B", "category": "us_stocks"}
  ],
  "clearExisting": false
}
```

**Response**:
```json
{
  "success": true,
  "message": "Symbols imported successfully",
  "imported": 150,
  "total": 941
}
```

---

### Get Symbol Count

Get the total count of active symbols.

**Endpoint**: `GET /api/tte/symbols/import`

**Response**:
```json
{
  "success": true,
  "total_symbols": 941
}
```

---

### Get Hot Symbols

Retrieve hot symbols that need OBDIV (Tier 2) processing. Hot symbols are those that triggered in the NWE screener.

**Endpoint**: `GET /api/tte/hot-symbols`

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 8 | Maximum symbols to return (max 100) |
| `status` | string | `pending_tier2` | Filter by status (`pending_tier2`, `tier2_complete`, `expired`) |

**Response**:
```json
{
  "success": true,
  "symbols": [
    {
      "_id": "65a5b2c1d4e5f6a7b8c9d0e1",
      "symbol": "GBPAUD",
      "direction": "bullish",
      "nwe_timeframes": ["5m", "15m"],
      "nwe_timestamp": 1705312800,
      "status": "pending_tier2",
      "created_at": "2024-01-15T10:30:00Z",
      "expires_at": "2024-01-16T10:30:00Z"
    }
  ],
  "count": 5
}
```

---

### Query Signals

Query TTE signals with filtering and pagination.

**Endpoint**: `GET /api/tte/signals`

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Max signals to return (1-100) |
| `offset` | integer | 0 | Pagination offset |
| `level` | integer | - | Filter by signal level (1, 2, or 3) |
| `direction` | string | - | Filter by direction (`bullish` or `bearish`) |
| `status` | string | - | Filter by status (`pending_screenshot` or `complete`) |
| `symbol` | string | - | Filter by symbol name |
| `from` | integer | - | Unix timestamp for start of range |
| `to` | integer | - | Unix timestamp for end of range |
| `sort` | string | `created_at` | Sort field (`created_at`, `level`, `symbol`) |
| `order` | string | `desc` | Sort order (`asc` or `desc`) |

**Response**:
```json
{
  "success": true,
  "signals": [
    {
      "_id": "65a5b2c1d4e5f6a7b8c9d0e2",
      "symbol": "EURUSD",
      "direction": "bullish",
      "level": 3,
      "nwe_tf": ["5m", "15m"],
      "nwe_timestamp": 1705312800,
      "ob_tf": "5m",
      "ob_type": "OB",
      "ob_high": 1.1050,
      "ob_low": 1.1000,
      "div_tf": "15m",
      "div_type": "Logic2",
      "screenshot_url": null,
      "status": "pending_screenshot",
      "timestamp": 1705316400,
      "created_at": "2024-01-15T11:30:00Z",
      "updated_at": "2024-01-15T11:30:00Z"
    }
  ],
  "total": 234,
  "limit": 50,
  "offset": 0
}
```

---

### Update Signal

Update a specific signal by ID (e.g., add screenshot URL or mark complete).

**Endpoint**: `PATCH /api/tte/signals/{id}`

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | MongoDB ObjectId (24 hex characters) |

**Request Body**:
```json
{
  "screenshot_url": "https://www.tradingview.com/x/abc123/",
  "status": "complete"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Signal updated",
  "id": "65a5b2c1d4e5f6a7b8c9d0e2"
}
```

---

## Webhook Payload Formats

The TTE screeners send webhook payloads to the Stock Buddy API when alerts trigger.

### NWE Webhook (Tier 1)

Receives Nadaraya-Watson Envelope signals and adds symbols to the hot list. NWE screener sends a **batch** of all symbols currently in zones.

**URL**: `POST /api/tte/nwe`

**Payload Format** (sent by TradingView):
```json
{
  "tier": "nwe",
  "symbols": [
    {"symbol": "GBPAUD", "direction": "bullish", "timeframes": ["5m", "15m"]},
    {"symbol": "EURUSD", "direction": "bearish", "timeframes": ["5m"]}
  ],
  "timestamp": 1705312800,
  "count": 2
}
```

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tier` | string | Yes | Must be `"nwe"` |
| `symbols` | array | Yes | Array of symbol objects (can be empty) |
| `symbols[].symbol` | string | Yes | Symbol name (2-20 chars, auto-uppercased) |
| `symbols[].direction` | string | Yes | `"bullish"` or `"bearish"` |
| `symbols[].timeframes` | array | Yes | Timeframes where signal triggered (`"5m"`, `"15m"`) |
| `timestamp` | integer | Yes | Unix timestamp |
| `count` | integer | Yes | Number of symbols in batch |

**Response**:
```json
{
  "success": true,
  "message": "Hot list entries created",
  "count": 2
}
```

---

### OBDIV Webhook (Tier 2)

Receives Order Block + Divergence confirmation signals and creates confirmed trading signals.

**URL**: `POST /api/tte/obdiv`

**Payload Format** (sent by TradingView):
```json
{
  "tier": "obdiv",
  "symbol": "EURUSD",
  "bull_ob": {
    "found": true,
    "tf": "1H",
    "type": "OB",
    "high": 1.1050,
    "low": 1.1000
  },
  "bull_div": {
    "found": true,
    "tf": "5m",
    "type": "Logic2"
  },
  "bear_ob": {
    "found": false
  },
  "bear_div": {
    "found": false
  },
  "timestamp": 1705316400
}
```

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tier` | string | Yes | Must be `"obdiv"` |
| `symbol` | string | Yes | Symbol name (2-20 chars, auto-uppercased) |
| `bull_ob` | object | Yes | Bullish order block finding |
| `bull_div` | object | Yes | Bullish divergence finding |
| `bear_ob` | object | Yes | Bearish order block finding |
| `bear_div` | object | Yes | Bearish divergence finding |
| `timestamp` | integer | Yes | Unix timestamp |

**Order Block Finding Schema**:
```json
{
  "found": true,
  "tf": "1H",
  "type": "OB",
  "high": 1.1050,
  "low": 1.1000
}
```
- `found`: boolean (required) - Whether OB was found
- `tf`: string (optional) - Timeframe (`"5m"`, `"15m"`, `"1H"`)
- `type`: string (optional) - Type: `"OB"`, `"FVG"`, or `"Breaker"`
- `high`: number (optional) - OB high price
- `low`: number (optional) - OB low price

**Divergence Finding Schema**:
```json
{
  "found": true,
  "tf": "15m",
  "type": "Logic2"
}
```
- `found`: boolean (required) - Whether divergence was found
- `tf`: string (optional) - Timeframe (`"5m"`, `"15m"`)
- `type`: string (optional) - Type: `"Logic2"`, `"Internal"`, or `"Logic1"`

**Response**:
```json
{
  "success": true,
  "message": "Created 1 signal(s)",
  "symbol": "EURUSD",
  "signals_created": [
    {"direction": "bullish", "level": 3, "id": "65a5b2c1d4e5f6a7b8c9d0e2"}
  ]
}
```

---

## Combo Mode Endpoints (V2)

Combo mode V2 uses a single webhook endpoint that receives compact pre-computed signal + position state for all symbols in an alert. Divergence has been removed. The payload uses abbreviated keys to stay within TradingView's 2KB alert message limit.

### POST /api/tte/combo — Combo Webhook (V2)

Receives the V2 combo screener webhook payload containing NWE signals, OB/FVG signals, and active trade positions for 2 symbols.

**URL**: `POST /api/tte/combo`

**Payload Format** (sent by TradingView — V2 compact format):
```json
{
  "ts": 1707264000000,
  "s": [{
    "sym": "GBPAUD", "c": 1.985,
    "nwe": [{"z": "la", "t": "bull", "tf": "1H", "ots": 1707264000}],
    "ob": [{"zt": "OB", "st": "un", "t": "bull", "zh": 1.99, "zl": 1.97, "tf": "H4", "zts": 1707260400, "ots": 1707264000}],
    "b": [{"e": 1.98, "sl": 1.975, "tp": 1.99, "et": 1707260000, "l": "LTF", "ntf": "1H", "otf": "H4", "n": true}, null],
    "se": [null, null]
  }]
}
```

**Key legend**:
| Key | Meaning |
|-----|---------|
| `ts` | Timestamp (ms) |
| `s` | Symbols array |
| `sym` | Symbol name |
| `c` | Close price |
| `nwe` | NWE signal entries |
| `ob` | OB/FVG signal entries |
| `b` | Buy positions [LTF slot, HTF slot] |
| `se` | Sell positions [LTF slot, HTF slot] |
| `e` | Entry price |
| `sl` | Stop loss price |
| `tp` | Take profit price |
| `et` | Entry time (Unix s) |
| `l` | Label (LTF or HTF) |
| `ntf` | NWE timeframe |
| `otf` | OB timeframe |
| `n` | isNew (true on setup bar only) |
| `xt` | Exit type (tp or sl) |
| `xp` | Exit price |
| `xts` | Exit time (Unix s) |

**NWE zone codes** (`z` field): `la`=lower_avg, `lf`=lower_far, `ua`=upper_avg, `uf`=upper_far

**OB subtype codes** (`st` field): `un`=unmitigated, `br`=breaker, `fv`=fvg

**Response**:
```json
{
  "success": true,
  "updated": 1
}
```

---

### GET /api/tte/combo/signals — Query Combo Signals

Query live combo signals with pagination and filtering.

**Endpoint**: `GET /api/tte/combo/signals`

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Max signals to return (1-200) |
| `offset` | integer | 0 | Pagination offset |
| `sort` | string | `last_updated` | Sort field (`last_updated`, `symbol`) |
| `order` | string | `desc` | Sort order (`asc` or `desc`) |
| `direction` | string | - | Filter by direction (`bullish` or `bearish`) |
| `signalType` | string | - | Filter by signal type (`nwe`, `ob`) |
| `symbol` | string | - | Filter by symbol name |

**Response**:
```json
{
  "success": true,
  "signals": [
    {
      "_id": "GBPAUD",
      "symbol": "GBPAUD",
      "nwe": [...],
      "ob": [...],
      "buy": [{...}, null],
      "sell": [null, null],
      "last_updated": "2026-02-27T12:00:00Z"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### Snapshot Endpoints

Used by the TTE snapshot worker to manage chart screenshot requests.

**GET /api/tte/snapshots/pending** — Poll for setups needing screenshots
**POST /api/tte/snapshots/update** — Report completed snapshot URLs back to Stock Buddy

### Testing Combo Endpoints

```bash
# Test combo V2 webhook
curl -X POST https://stockbuddy.co/api/tte/combo \
  -H "Content-Type: application/json" \
  -d '{"ts":1707264000000,"s":[{"sym":"EURUSD","c":1.085,"nwe":[],"ob":[],"b":[null,null],"se":[null,null]}]}'

# Query combo signals
curl "https://stockbuddy.co/api/tte/combo/signals?limit=10"

# Filter by signal type
curl "https://stockbuddy.co/api/tte/combo/signals?signalType=nwe&direction=bullish"
```

---

## Signal Levels System

Stock Buddy uses a signal level system (1, 2, 3) to indicate signal strength:

| Level | Criteria | Confidence | Color |
|-------|----------|------------|-------|
| **Level 1** | NWE zone entry only | Low | Yellow |
| **Level 2** | NWE + Order Block OR NWE + Divergence | Medium | Orange |
| **Level 3** | NWE + Order Block + Divergence | High | Green |

The level is automatically calculated when an OBDIV webhook is processed:
```
Level 3: hasOB AND hasDiv
Level 2: hasOB OR hasDiv
Level 1: Neither (from hot list only)
```

---

## Priority Rotation System

Symbols are assigned priorities (A, B, C) that determine scanning frequency:

| Priority | Description | Scan Frequency |
|----------|-------------|----------------|
| **A** | Major pairs, high-volume symbols | Every batch |
| **B** | Secondary symbols | Every 3rd rotation |
| **C** | Low-volume/exotic symbols | Every 10th rotation |

A "rotation" is complete when all symbols have been scanned once. The system tracks:
- `batch_number`: Total batches processed
- `rotation_number`: Complete rotation cycles
- `symbols_scanned_this_rotation`: Progress within current rotation

---

## Error Handling

### Error Response Format

All error responses follow this format:

```json
{
  "success": false,
  "error": "Error message description",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid parameters or payload |
| `INVALID_ID` | 400 | Invalid MongoDB ObjectId format |
| `NOT_FOUND` | 404 | Resource not found |
| `ALREADY_INITIALIZED` | 400 | Rotation state already exists |
| `NO_SYMBOLS` | 400 | No symbols in database |
| `INTERNAL_ERROR` | 500 | Server-side error |

### Client Error Handling

The `StockBuddyAPIClient` handles errors internally and returns structured responses:

```python
try:
    batch = api.get_next_symbol_batch(20)
    if batch.get("success"):
        # Process batch
        pass
    else:
        print(f"Error: {batch.get('error', 'Unknown error')}")
except Exception as e:
    logger.error(f"API request failed: {e}")
```

---

## Rate Limits

The Stock Buddy API has the following rate limits:

| Endpoint | Limit | Window |
|----------|-------|--------|
| All endpoints | 100 requests | per minute |
| Webhook endpoints | 60 requests | per minute |

TTE's combo mode uses persistent alerts that fire continuously, so rate limiting is generally not a concern for the TTE client.

---

## Testing Endpoints

### Manual Testing with curl

```bash
# Health check
curl https://stockbuddy.co/api/health

# Get stats
curl https://stockbuddy.co/api/tte/stats

# Get init status
curl https://stockbuddy.co/api/tte/init

# Get next batch
curl "https://stockbuddy.co/api/tte/symbols/next-batch?size=20"

# Get hot symbols
curl "https://stockbuddy.co/api/tte/hot-symbols?limit=8"

# Get signals
curl "https://stockbuddy.co/api/tte/signals?limit=10&level=3"

# Test NWE webhook (batch format)
curl -X POST https://stockbuddy.co/api/tte/nwe \
  -H "Content-Type: application/json" \
  -d '{"tier":"nwe","symbols":[{"symbol":"EURUSD","direction":"bullish","timeframes":["5m"]}],"timestamp":1705312800,"count":1}'
```

---

## See Also

- [Combo Architecture](combo/ARCHITECTURE.md) - How the API integrates with TTE
- [Setup Guide](SETUP.md) - API configuration setup
- [Database](DATABASE.md) - Stock Buddy database collections
- [Troubleshooting](TROUBLESHOOTING.md) - API-related issues
