# API Documentation
# TTE Stock Buddy API

**Base URL:** `https://stock-buddy-app.vercel.app/api/tte`

**Version:** 1.1 (Updated January 29, 2026)

**Status:** ✅ Live in Production

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
   - [GET /api/health](#get-apihealth)
   - [POST /api/tte/nwe](#post-apittenwe)
   - [POST /api/tte/obdiv](#post-apitteobdiv)
   - [GET /api/tte/signals](#get-apittesignals)
   - [PATCH /api/tte/signals/:id](#patch-apittesignalsid)
   - [GET /api/tte/hot-symbols](#get-apittehot-symbols)
   - [GET /api/tte/stats](#get-apittestats)
   - [GET /api/tte/symbols/next-batch](#get-apittesymbolsnext-batch)
   - [POST /api/tte/symbols/mark-scanned](#post-apittesymbolsmark-scanned)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Examples](#examples)

---

## Overview

The Stock Buddy API provides endpoints for:
- Receiving webhooks from TradingView screeners (NWE and OBDIV)
- Managing the hot symbol list (symbols pending Tier 2 check)
- Storing and retrieving trading signals
- Managing symbol rotation for batch scanning
- Updating signal metadata (screenshots)
- System statistics and health monitoring

### Content Type

All requests and responses use JSON:
```
Content-Type: application/json
```

### Base URLs

| Environment | Base URL |
|-------------|----------|
| Production | `https://stock-buddy-app.vercel.app/api/tte` |
| Development | `http://localhost:3000/api/tte` |

### Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check |
| `/api/tte/nwe` | POST | Receive NWE webhooks |
| `/api/tte/obdiv` | POST | Receive OBDIV webhooks |
| `/api/tte/signals` | GET | Fetch signals |
| `/api/tte/signals/:id` | PATCH | Update signal |
| `/api/tte/hot-symbols` | GET | Get pending symbols |
| `/api/tte/stats` | GET | System statistics |
| `/api/tte/symbols/next-batch` | GET | Get next rotation batch |
| `/api/tte/symbols/mark-scanned` | POST | Mark batch as scanned |

---

## Authentication

### Webhook Endpoints (Public)

The webhook endpoints (`/api/tte/nwe` and `/api/tte/obdiv`) are **public** and do not require authentication. This is necessary for TradingView webhooks to work.

### Dashboard/API Endpoints

Currently unauthenticated (public read access). The middleware has been configured to bypass authentication for all `/api/tte/*` routes.

---

## Endpoints

### GET /api/health

Health check endpoint to verify API is running.

#### Request

```http
GET /api/health
```

#### Response

**Success (200):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-29T12:00:00.000Z"
}
```

---

### POST /api/tte/nwe

Receives NWE (Tier 1) webhook alerts from TradingView. Creates or updates hot list entry.

#### Request

```http
POST /api/tte/nwe
Content-Type: application/json
```

**Body Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tier` | string | Yes | Must be `"nwe"` |
| `symbol` | string | Yes | Trading symbol (e.g., `"GBPAUD"`, `"OANDA:EURUSD"`) |
| `direction` | string | Yes | `"bullish"` or `"bearish"` |
| `timeframes` | string[] | No | Timeframes that triggered (e.g., `["H4", "D1"]`) |
| `timestamp` | number | No | Unix timestamp (defaults to current time) |

**Example Request:**

```json
{
  "tier": "nwe",
  "symbol": "GBPAUD",
  "direction": "bullish",
  "timeframes": ["H4", "D1"],
  "timestamp": 1706540000
}
```

#### Response

**Success (200):**

```json
{
  "success": true,
  "message": "Hot list entry created",
  "symbol": "GBPAUD"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Always `true` on success |
| `message` | string | `"Hot list entry created"` or `"Hot list entry updated"` |
| `symbol` | string | The processed symbol |

**Error (400):**

```json
{
  "success": false,
  "error": "Invalid direction",
  "code": "INVALID_DIRECTION"
}
```

---

### POST /api/tte/obdiv

Receives OBDIV (Tier 2) webhook alerts. Creates signal by combining with hot list NWE data.

#### Request

```http
POST /api/tte/obdiv
Content-Type: application/json
```

**Body Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tier` | string | Yes | Must be `"obdiv"` |
| `symbol` | string | Yes | Trading symbol |
| `bull_ob` | object | Yes | Bullish OB/FVG finding |
| `bull_div` | object | Yes | Bullish divergence finding |
| `bear_ob` | object | Yes | Bearish OB/FVG finding |
| `bear_div` | object | Yes | Bearish divergence finding |
| `timestamp` | number | No | Unix timestamp |

**OB Finding Object:**

| Field | Type | Description |
|-------|------|-------------|
| `found` | boolean | Whether OB/FVG was found |
| `tf` | string | Timeframe (`"H4"`, `"D1"`, `"W1"`) |
| `type` | string | Type (`"OB"`, `"FVG"`, `"Breaker"`) |
| `high` | number | Zone upper boundary |
| `low` | number | Zone lower boundary |

**DIV Finding Object:**

| Field | Type | Description |
|-------|------|-------------|
| `found` | boolean | Whether divergence was found |
| `tf` | string | Timeframe (`"H4"`, `"D1"`) |
| `type` | string | Type (`"Logic2"`, `"Internal"`) |

**Example Request:**

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
  "timestamp": 1706540000
}
```

#### Response

**Success - Signal Created (200):**

```json
{
  "success": true,
  "message": "Created 1 signal(s)",
  "signals_created": [
    {
      "direction": "bullish",
      "level": 3
    }
  ]
}
```

**Success - No Signal (Symbol not in hot list) (200):**

```json
{
  "success": true,
  "message": "No matching hot symbols found",
  "signals_created": []
}
```

---

### GET /api/tte/signals

Retrieves signals for dashboard display. Supports filtering, sorting, and pagination.

#### Request

```http
GET /api/tte/signals?limit=50&level=3&direction=bullish
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | number | 50 | Max results (1-100) |
| `offset` | number | 0 | Pagination offset |
| `level` | number | - | Filter by level (1, 2, 3) |
| `direction` | string | - | Filter by direction |
| `status` | string | - | Filter by status (`pending_screenshot`, `complete`) |
| `symbol` | string | - | Filter by symbol (partial match) |
| `from` | number | - | Start timestamp (Unix) |
| `to` | number | - | End timestamp (Unix) |

#### Response

**Success (200):**

```json
{
  "success": true,
  "data": [
    {
      "_id": "65b7c1234567890abcdef456",
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
      "screenshot_url": null,
      "status": "pending_screenshot",
      "created_at": "2026-01-29T12:00:00.000Z",
      "timestamp": 1706540000
    }
  ],
  "pagination": {
    "total": 150,
    "limit": 50,
    "offset": 0,
    "hasMore": true
  }
}
```

---

### PATCH /api/tte/signals/:id

Updates a signal record (typically to add screenshot URL).

#### Request

```http
PATCH /api/tte/signals/65b7c1234567890abcdef456
Content-Type: application/json
```

**Body Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `screenshot_url` | string | No | TradingView snapshot URL |
| `status` | string | No | New status (`complete`, `screenshot_failed`) |

**Example Request:**

```json
{
  "screenshot_url": "https://www.tradingview.com/x/ABC123/",
  "status": "complete"
}
```

#### Response

**Success (200):**

```json
{
  "success": true,
  "updated": true
}
```

---

### GET /api/tte/hot-symbols

Retrieves symbols from the hot list awaiting Tier 2 processing.

#### Request

```http
GET /api/tte/hot-symbols?limit=10
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | `pending_tier2` | Filter by status |
| `limit` | number | 10 | Max results (1-50) |

#### Response

**Success (200):**

```json
{
  "success": true,
  "data": [
    {
      "symbol": "GBPAUD",
      "direction": "bullish",
      "nwe_timeframes": ["H4", "D1"],
      "nwe_timestamp": 1706540000,
      "status": "pending_tier2",
      "updated_at": "2026-01-29T12:00:00.000Z",
      "expires_at": "2026-01-30T12:00:00.000Z"
    }
  ],
  "count": 1
}
```

---

### GET /api/tte/stats

Returns system statistics for the dashboard.

#### Request

```http
GET /api/tte/stats
```

#### Response

**Success (200):**

```json
{
  "success": true,
  "signals": {
    "total": 47,
    "today": 5,
    "level1": 20,
    "level2": 15,
    "level3": 12,
    "bullish": 30,
    "bearish": 17,
    "pendingScreenshots": 3
  },
  "hot_list": {
    "pending": 2,
    "total": 5
  },
  "symbols": {
    "total": 1000,
    "byPriority": {
      "A": 100,
      "B": 300,
      "C": 600
    }
  },
  "rotation": {
    "batch_number": 5,
    "rotation_number": 1,
    "progress_percent": 30.5
  }
}
```

---

### GET /api/tte/symbols/next-batch

Returns the next batch of symbols for NWE screening based on rotation state.

#### Request

```http
GET /api/tte/symbols/next-batch?size=40
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `size` | number | 40 | Batch size (1-100) |

#### Response

**Success (200):**

```json
{
  "success": true,
  "batch": [
    {
      "symbol": "OANDA:EURUSD",
      "category": "currencies",
      "priority": "A"
    },
    {
      "symbol": "BINANCE:BTCUSDT",
      "category": "crypto",
      "priority": "A"
    }
  ],
  "batch_number": 6,
  "rotation_number": 1,
  "total_in_batch": 40,
  "progress_percent": 35.2
}
```

---

### POST /api/tte/symbols/mark-scanned

Marks symbols as scanned after NWE processing.

#### Request

```http
POST /api/tte/symbols/mark-scanned
Content-Type: application/json
```

**Body Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `symbols` | string[] | Yes | Array of symbols that were scanned |

**Example Request:**

```json
{
  "symbols": ["OANDA:EURUSD", "BINANCE:BTCUSDT", "NSE:RELIANCE"]
}
```

#### Response

**Success (200):**

```json
{
  "success": true,
  "message": "Marked 40 symbols as scanned",
  "batch_advanced": true,
  "new_batch_number": 7
}
```

---

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "code": "MACHINE_READABLE_CODE"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_PAYLOAD` | 400 | Request body malformed |
| `MISSING_FIELD` | 400 | Required field missing |
| `INVALID_TIER` | 400 | Tier must be "nwe" or "obdiv" |
| `INVALID_DIRECTION` | 400 | Direction must be "bullish" or "bearish" |
| `NOT_FOUND` | 404 | Resource not found |
| `DB_ERROR` | 500 | Database operation failed |

---

## Rate Limiting

Currently no rate limiting is enforced. TradingView webhooks are expected to fire at reasonable intervals.

---

## Examples

### cURL Examples

**Health check:**
```bash
curl https://stock-buddy-app.vercel.app/api/health
```

**Create NWE alert:**
```bash
curl -X POST https://stock-buddy-app.vercel.app/api/tte/nwe \
  -H "Content-Type: application/json" \
  -d '{
    "tier": "nwe",
    "symbol": "GBPAUD",
    "direction": "bullish",
    "timeframes": ["H4", "D1"]
  }'
```

**Create OBDIV alert:**
```bash
curl -X POST https://stock-buddy-app.vercel.app/api/tte/obdiv \
  -H "Content-Type: application/json" \
  -d '{
    "tier": "obdiv",
    "symbol": "GBPAUD",
    "bull_ob": {"found": true, "tf": "W1", "type": "OB", "high": 1.055, "low": 1.050},
    "bull_div": {"found": true, "tf": "H4", "type": "Logic2"},
    "bear_ob": {"found": false},
    "bear_div": {"found": false}
  }'
```

**Get system stats:**
```bash
curl https://stock-buddy-app.vercel.app/api/tte/stats
```

**Get Level 3 signals:**
```bash
curl "https://stock-buddy-app.vercel.app/api/tte/signals?level=3&limit=10"
```

**Get hot symbols:**
```bash
curl "https://stock-buddy-app.vercel.app/api/tte/hot-symbols"
```

**Get next batch for rotation:**
```bash
curl "https://stock-buddy-app.vercel.app/api/tte/symbols/next-batch?size=40"
```

**Mark symbols as scanned:**
```bash
curl -X POST https://stock-buddy-app.vercel.app/api/tte/symbols/mark-scanned \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["OANDA:EURUSD", "BINANCE:BTCUSDT"]}'
```

**Update signal with screenshot:**
```bash
curl -X PATCH https://stock-buddy-app.vercel.app/api/tte/signals/65b7c1234567890abcdef456 \
  -H "Content-Type: application/json" \
  -d '{
    "screenshot_url": "https://www.tradingview.com/x/ABC123/",
    "status": "complete"
  }'
```

### Python Examples

```python
import requests

BASE_URL = "https://stock-buddy-app.vercel.app/api/tte"

# Health check
response = requests.get("https://stock-buddy-app.vercel.app/api/health")
print(response.json())  # {"status": "healthy", ...}

# Get stats
response = requests.get(f"{BASE_URL}/stats")
stats = response.json()
print(f"Total signals: {stats['signals']['total']}")
print(f"Symbols tracked: {stats['symbols']['total']}")

# Get hot symbols for OBDIV processing
response = requests.get(f"{BASE_URL}/hot-symbols", params={"limit": 10})
hot_symbols = response.json()["data"]
print(f"Hot symbols pending: {len(hot_symbols)}")

# Get next batch for NWE rotation
response = requests.get(f"{BASE_URL}/symbols/next-batch", params={"size": 40})
batch = response.json()
symbols = [s["symbol"] for s in batch["batch"]]
print(f"Next batch: {len(symbols)} symbols")

# Mark as scanned
response = requests.post(f"{BASE_URL}/symbols/mark-scanned", json={"symbols": symbols})
print(response.json())

# Get pending screenshots
response = requests.get(f"{BASE_URL}/signals", params={"status": "pending_screenshot"})
pending = response.json()["data"]
print(f"Pending screenshots: {len(pending)}")
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2026-01-29 | Updated to `/api/tte/*` paths; added symbols rotation endpoints; production URLs |
| 1.0 | 2026-01-28 | Initial API documentation |

---

*For technical details, see TECHNICAL_SPEC.md. For orchestrator guide, see docs/ORCHESTRATOR_GUIDE.md.*
