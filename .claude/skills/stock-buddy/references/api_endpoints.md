# API Endpoints Reference

Complete reference for all Stock Buddy API endpoints and webhook integrations.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [TTE API Client](#tte-api-client)
- [System Endpoints](#system-endpoints)
- [Symbol Management Endpoints](#symbol-management-endpoints)
- [Hot Symbol Endpoints](#hot-symbol-endpoints)
- [Signal Endpoints](#signal-endpoints)
- [Webhook Endpoints](#webhook-endpoints)
- [Error Handling](#error-handling)
- [Rate Limits](#rate-limits)

## Overview

The Stock Buddy API provides REST endpoints for:
- Symbol rotation and batch management
- Hot symbol queuing and expiration
- Signal storage and querying
- Webhook processing from TradingView

All endpoints return JSON responses with a consistent structure.

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

**Request Headers**:
```
Content-Type: application/json
Accept: application/json
```

## Base URL

Production: `https://stock-buddy-app.vercel.app/api/tte`

Health endpoint: `https://stock-buddy-app.vercel.app/api/health` (note: not under `/tte`)

## TTE API Client

The TTE orchestrator uses `StockBuddyAPIClient` (Python) to interact with the API.

### Initialization

```python
from api_client import StockBuddyAPIClient
from config import config

api = StockBuddyAPIClient(
    base_url=config.api_base_url,
    timeout=config.api_timeout
)
```

### Available Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `health_check()` | Check API health | `bool` |
| `get_stats()` | Get system statistics | `dict` or `None` |
| `get_next_symbol_batch(size)` | Get next batch of symbols | `dict` |
| `mark_symbols_scanned(symbols)` | Mark symbols as scanned | `dict` |
| `get_hot_symbols(limit)` | Get hot symbols for OBDIV | `list[dict]` |
| `delete_expired_hot_symbols()` | Delete expired hot symbols | `dict` |
| `close()` | Close HTTP session | `None` |

### Context Manager Support

```python
with StockBuddyAPIClient(base_url, timeout) as api:
    stats = api.get_stats()
    # Session automatically closed on exit
```

## System Endpoints

### GET /api/health

Check if the API is healthy and responding.

**Note**: This endpoint is at `/api/health`, not `/api/tte/health`.

**Response** (200 OK):
```json
{
  "status": "healthy"
}
```

**Client Usage**:
```python
is_healthy = api.health_check()  # Returns True/False
```

### GET /api/tte/init

Check the current initialization status of the TTE system.

**Response** (200 OK):
```json
{
  "success": true,
  "initialized": true,
  "symbols": {
    "total": 941,
    "counts": {
      "A": 28,
      "B": 150,
      "C": 763,
      "total": 941
    }
  },
  "rotation_state": {
    "batch_number": 6,
    "rotation_number": 1,
    "symbols_scanned": 120,
    "total_symbols": 941
  }
}
```

### POST /api/tte/init

Initialize or reset the rotation state.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `seed` | boolean | If `true`, seeds default symbols (destructive with force) |

**Request Body**:
```json
{
  "force": false,
  "symbols": [
    {
      "symbol": "EURUSD",
      "exchange": "FX",
      "priority": "A",
      "category": "forex"
    }
  ]
}
```

**Response** (200 OK):
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

**Response** (400 Already Initialized):
```json
{
  "success": false,
  "error": "Rotation state already initialized (Batch #6, Rotation #1). Use force=true to reset.",
  "code": "ALREADY_INITIALIZED"
}
```

### GET /api/tte/stats

Retrieve comprehensive system statistics.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hours` | integer | 24 | Time period for signal statistics |

**Response** (200 OK):
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

**Client Usage**:
```python
stats = api.get_stats()
print(f"Total signals: {stats.get('signals', {}).get('total')}")
print(f"Level 3 signals: {stats.get('signals', {}).get('level3')}")
```

## Symbol Management Endpoints

### GET /api/tte/symbols/next-batch

Fetch the next batch of symbols for NWE (Tier 1) scanning using priority-based rotation.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `size` | integer | 20 | Number of symbols to fetch (max 50) |

**Response** (200 OK):
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
- Remaining slots filled with least-recently-scanned symbols

**Client Usage**:
```python
batch_response = api.get_next_symbol_batch(size=20)

if batch_response.get("success"):
    symbols = batch_response.get("batch", [])
    # Extract symbol strings
    symbol_strings = [s["symbol"] if isinstance(s, dict) else s for s in symbols]
```

### POST /api/tte/symbols/mark-scanned

Mark symbols as scanned after NWE processing completes.

**Request Body**:
```json
{
  "symbols": ["EURUSD", "GBPUSD", "USDJPY"]
}
```

**Validation**:
- `symbols`: array of 1-20 symbol strings (uppercase)

**Response** (200 OK):
```json
{
  "success": true,
  "marked_count": 20,
  "rotation_complete": false
}
```

**Client Usage**:
```python
response = api.mark_symbols_scanned(["EURUSD", "GBPUSD", "USDJPY"])
if response.get("success"):
    print(f"Marked {response.get('marked_count')} symbols as scanned")
```

### POST /api/tte/symbols/import

Import symbols in bulk from TTE's symbol_settings.py format.

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

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Symbols imported successfully",
  "imported": 150,
  "total": 941
}
```

### GET /api/tte/symbols/import

Get the total count of active symbols.

**Response** (200 OK):
```json
{
  "success": true,
  "total_symbols": 941
}
```

## Hot Symbol Endpoints

### GET /api/tte/hot-symbols

Retrieve hot symbols that need OBDIV (Tier 2) processing.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 8 | Maximum symbols to return (max 100) |
| `status` | string | `pending_tier2` | Filter by status |
| `include_expired` | boolean | `false` | Include expired symbols |

**Valid Status Values**:
- `pending_tier2` - Awaiting OBDIV processing
- `tier2_complete` - OBDIV processing complete
- `expired` - Expiration timestamp passed

**Response** (200 OK):
```json
{
  "success": true,
  "symbols": [
    {
      "_id": "65a5b2c1d4e5f6a7b8c9d0e1",
      "symbol": "GBPAUD",
      "direction": "bullish",
      "nwe_timeframe": "5m",
      "nwe_timestamp": 1705312800,
      "status": "pending_tier2",
      "created_at": "2024-01-15T10:30:00Z",
      "expires_at": "2024-01-15T10:35:00Z"
    }
  ],
  "count": 1
}
```

**Note**: Each symbol+timeframe combination creates a separate document. A symbol can have multiple hot list entries for different timeframes.

**Client Usage**:
```python
hot_symbols = api.get_hot_symbols(limit=8)

for symbol in hot_symbols:
    print(f"{symbol['symbol']}: {symbol['direction']} on {symbol['nwe_timeframe']}")
```

### DELETE /api/tte/hot-symbols/expired

Delete all expired hot symbols from the database.

**Response** (200 OK):
```json
{
  "success": true,
  "deleted_count": 15,
  "message": "Deleted 15 expired hot symbols"
}
```

**Client Usage**:
```python
result = api.delete_expired_hot_symbols()
print(f"Deleted {result.get('deleted_count', 0)} expired hot symbols")
```

## Signal Endpoints

### GET /api/tte/signals

Query TTE signals with filtering and pagination.

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

**Response** (200 OK):
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

**Example Queries**:
```bash
# Get latest 10 Level 3 signals
curl "https://stock-buddy-app.vercel.app/api/tte/signals?limit=10&level=3"

# Get bullish signals for EURUSD
curl "https://stock-buddy-app.vercel.app/api/tte/signals?symbol=EURUSD&direction=bullish"

# Get signals from last 24 hours
curl "https://stock-buddy-app.vercel.app/api/tte/signals?from=1705230000"
```

### PATCH /api/tte/signals/{id}

Update a specific signal by ID (e.g., add screenshot URL or mark complete).

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

**Validation**:
- At least one field required (`screenshot_url` or `status`)
- `screenshot_url`: valid URL format
- `status`: `"pending_screenshot"` or `"complete"`

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Signal updated",
  "id": "65a5b2c1d4e5f6a7b8c9d0e2"
}
```

**Response** (404 Not Found):
```json
{
  "success": false,
  "error": "Signal not found",
  "code": "NOT_FOUND"
}
```

## Webhook Endpoints

### POST /api/tte/nwe

Receives Nadaraya-Watson Envelope signals (Tier 1) and adds symbols to the hot list.

**Webhook URL**: `https://stock-buddy-app.vercel.app/api/tte/nwe`

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
| `symbols[].timeframes` | array | Yes | Timeframes where signal triggered |
| `timestamp` | integer | Yes | Unix timestamp |
| `count` | integer | Yes | Number of symbols in batch |

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Created 4 hot list entries (2 skipped)",
  "created": 4,
  "skipped": 2
}
```

**Behavior**:
- Creates separate documents for each symbol+timeframe combination
- Expiration calculated as: `nwe_timestamp + timeframe_duration`
- No refresh: if document exists for symbol+direction+timeframe, it's skipped
- Empty `symbols: []` array is valid (no triggers)

**Example Pine Script Webhook**:
```pine
alert("{\"tier\":\"nwe\",\"symbols\":[{\"symbol\":\"{{ticker}}\",\"direction\":\"bullish\",\"timeframes\":[\"5m\"]}],\"timestamp\":{{timenow}},\"count\":1}", alert.freq_once_per_bar)
```

### POST /api/tte/obdiv

Receives Order Block + Divergence confirmation signals (Tier 2) and creates confirmed trading signals.

**Webhook URL**: `https://stock-buddy-app.vercel.app/api/tte/obdiv`

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

**Response** (200 OK):
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

**Behavior**:
- Validates hot list entry exists for symbol+direction
- Calculates signal level: 3 (OB+DIV), 2 (OB OR DIV), 1 (neither)
- Creates signal with `status: "pending_screenshot"`
- Marks hot list entry as `tier2_complete`
- Increments symbol's `signal_count`

**Response** (200 No Match):
```json
{
  "success": true,
  "message": "No matching hot list entries found",
  "symbol": "EURUSD",
  "signals_created": []
}
```

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
| `NOT_INITIALIZED` | 500 | Rotation state not initialized |
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

## Rate Limits

The Stock Buddy API has the following rate limits:

| Endpoint | Limit | Window |
|----------|-------|--------|
| All endpoints | 100 requests | per minute |
| Webhook endpoints | 60 requests | per minute |

### Handling Rate Limits

The orchestrator uses configurable delays between operations:

```python
# config.py settings
nwe_batch_wait: int = 60    # Wait after NWE alert creation
obdiv_batch_wait: int = 60  # Wait after OBDIV alert creation
cycle_interval: int = 300   # Wait between complete cycles
```

### Retry Logic

The API client includes built-in retry logic for transient failures:

```python
# config.py settings
max_retries: int = 3    # Maximum retry attempts
retry_delay: int = 5    # Seconds between retries
api_timeout: int = 30   # Request timeout in seconds
```

**Retry Behavior**:
1. Connection errors trigger automatic retry
2. 5xx errors trigger retry with exponential backoff
3. 4xx errors do not trigger retry (client error)
4. Timeouts trigger retry after `retry_delay`

---

**Related**:
- [Database Schema](database_schema.md) - MongoDB collections and fields
- [Integration Flow](integration_flow.md) - Complete workflow with timing
- [Symbol Management](symbol_management.md) - Rotation algorithm details
