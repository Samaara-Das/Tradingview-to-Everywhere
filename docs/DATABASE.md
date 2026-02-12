# Database Documentation

MongoDB schema and collections documentation for TTE and Stock Buddy integration.

## Overview

TTE uses two MongoDB databases:

1. **TTE Symbols Database**: Stores symbol definitions used by TTE's combo screener (accessed via `resources/symbol_settings.py`)
2. **Stock Buddy Database**: Stores live combo signals, symbol data, and rotation state (accessed via Stock Buddy API)

---

## TTE Symbols Database

TTE's symbols database stores symbol definitions used by the combo screener. Accessed via `resources/symbol_settings.py`.

**Database Name**: `tte` (configurable via `MONGODB_DATABASE` environment variable)

### Connection Configuration

```bash
# Option 1: Full connection string (preferred)
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority

# Option 2: Password only (uses default connection string)
MONGODB_PWD=your_password

# Database name (optional, defaults to "tte")
MONGODB_DATABASE=tte
```

### Collections

#### `symbols`

Stores symbol definitions and categories for the combo screener.

##### Document Schema

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `_id` | ObjectId | MongoDB auto-generated ID | `ObjectId("...")` |
| `symbol` | string | Short symbol name | `"EURUSD"` |
| `full_symbol` | string | Full symbol with exchange | `"OANDA:EURUSD"` |
| `category` | string | Symbol category | `"currencies"` |
| `active` | boolean | Whether symbol is active | `true` |

##### Categories

| Category | Typical Count |
|----------|---------------|
| `currencies` | ~30 |
| `us_stocks` | ~719 |
| `indian_stocks` | ~268 |
| `crypto` | ~19 |
| `indices` | ~18 |

---

## Stock Buddy Database

Stock Buddy maintains its own MongoDB database for signal storage. TTE interacts with this database through the Stock Buddy API, not directly.

**Database Name**: `tte` (on Stock Buddy's MongoDB Atlas cluster)

**Access Method**: Via Stock Buddy API endpoints (see [API.md](API.md))

### Collections

| Collection | Purpose | Access via API |
|------------|---------|----------------|
| `tte_symbols` | Symbol registry with priority/category | `/api/tte/symbols/*` |
| `tte_hot_list` | Symbols pending Tier 2 processing | `/api/tte/hot-symbols` |
| `tte_signals` | Confirmed TTE signals | `/api/tte/signals` |
| `tte_rotation_state` | Batch rotation tracking | `/api/tte/stats`, `/api/tte/init` |
| `tte_live_signals` | Live combo mode signal state per symbol | `/api/tte/combo/signals` |

---

#### 1. `tte_symbols`

Stores symbol configuration with priority for the tiered rotation system.

##### Document Schema

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `_id` | ObjectId | MongoDB auto-generated ID | `ObjectId("...")` |
| `symbol` | string | Symbol name (uppercase) | `"EURUSD"` |
| `exchange` | string | Exchange type | `"FX"`, `"CRYPTO"`, `"STOCKS"`, `"INDICES"`, `"COMMODITIES"` |
| `priority` | string | Scan priority | `"A"`, `"B"`, `"C"` |
| `category` | string | Symbol category | `"forex"`, `"us_stocks"` |
| `notes` | string | Optional notes | `""` |
| `active` | boolean | Whether symbol is active | `true` |
| `last_scanned` | Date | Last scan timestamp | `"2024-01-15T10:30:00Z"` |
| `scan_count` | number | Total times scanned | `42` |
| `signal_count` | number | Total signals generated | `5` |
| `created_at` | Date | Document creation time | `"2024-01-01T00:00:00Z"` |
| `updated_at` | Date | Last update time | `"2024-01-15T10:30:00Z"` |

##### Priority System

| Priority | Description | Scan Frequency |
|----------|-------------|----------------|
| **A** | Major pairs, high-volume symbols | Every batch |
| **B** | Secondary symbols | Every 3rd rotation |
| **C** | Low-volume/exotic symbols | Every 10th rotation |

##### Example Document

```json
{
  "_id": "ObjectId('65a5b2c1d4e5f6a7b8c9d0e3')",
  "symbol": "EURUSD",
  "exchange": "FX",
  "priority": "A",
  "category": "forex",
  "notes": "",
  "active": true,
  "last_scanned": "2024-01-15T10:30:00Z",
  "scan_count": 42,
  "signal_count": 5,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

#### 2. `tte_hot_list`

Stores symbols that triggered in Tier 1 (NWE) and are pending Tier 2 (OBDIV) processing.

##### Document Schema

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `_id` | ObjectId | MongoDB auto-generated ID | `ObjectId("...")` |
| `symbol` | string | Symbol name | `"EURUSD"` |
| `direction` | string | Trade direction | `"bullish"` or `"bearish"` |
| `nwe_timeframes` | array | Timeframes where NWE triggered | `["H4", "D1"]` |
| `nwe_timestamp` | number | Unix timestamp of NWE trigger | `1705312800` |
| `status` | string | Processing status | `"pending_tier2"`, `"tier2_complete"`, `"expired"` |
| `created_at` | Date | Document creation time | `"2024-01-15T10:30:00Z"` |
| `updated_at` | Date | Last update time | `"2024-01-15T10:30:00Z"` |
| `expires_at` | Date | Expiration time (24h after creation) | `"2024-01-16T10:30:00Z"` |

##### Status Values

| Status | Description |
|--------|-------------|
| `pending_tier2` | Waiting for OBDIV processing |
| `tier2_complete` | OBDIV processing completed |
| `expired` | Expired without Tier 2 processing |

##### Example Document

```json
{
  "_id": "ObjectId('65a5b2c1d4e5f6a7b8c9d0e4')",
  "symbol": "GBPAUD",
  "direction": "bullish",
  "nwe_timeframes": ["H4", "D1"],
  "nwe_timestamp": 1705312800,
  "status": "pending_tier2",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "expires_at": "2024-01-16T10:30:00Z"
}
```

---

#### 3. `tte_signals`

Stores confirmed trading signals from the tiered system.

##### Document Schema

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `_id` | ObjectId | MongoDB auto-generated ID | `ObjectId("...")` |
| `symbol` | string | Symbol name | `"EURUSD"` |
| `direction` | string | Trade direction | `"bullish"` or `"bearish"` |
| `level` | number | Signal confidence level | `1`, `2`, or `3` |
| `nwe_tf` | array | NWE timeframes | `["H4", "D1"]` |
| `nwe_timestamp` | number | NWE trigger timestamp | `1705312800` |
| `ob_tf` | string\|null | Order Block timeframe | `"H4"` or `null` |
| `ob_type` | string\|null | Order Block type | `"OB"`, `"FVG"`, `"Breaker"`, or `null` |
| `ob_high` | number\|null | Order Block high price | `1.1050` or `null` |
| `ob_low` | number\|null | Order Block low price | `1.1000` or `null` |
| `div_tf` | string\|null | Divergence timeframe | `"D1"` or `null` |
| `div_type` | string\|null | Divergence type | `"Logic2"`, `"Internal"`, `"Logic1"`, or `null` |
| `screenshot_url` | string\|null | Chart screenshot URL | `"https://..."` or `null` |
| `status` | string | Signal status | `"pending_screenshot"` or `"complete"` |
| `timestamp` | number | Signal creation timestamp | `1705316400` |
| `created_at` | Date | Document creation time | `"2024-01-15T11:30:00Z"` |
| `updated_at` | Date | Last update time | `"2024-01-15T11:30:00Z"` |

##### Signal Levels

| Level | Criteria | Confidence | UI Color |
|-------|----------|------------|----------|
| **1** | NWE zone entry only | Low | Yellow |
| **2** | NWE + OB or NWE + Divergence | Medium | Orange |
| **3** | NWE + OB + Divergence | High | Green |

##### Example Document (Level 3 Signal)

```json
{
  "_id": "ObjectId('65a5b2c1d4e5f6a7b8c9d0e5')",
  "symbol": "EURUSD",
  "direction": "bullish",
  "level": 3,
  "nwe_tf": ["H4", "D1"],
  "nwe_timestamp": 1705312800,
  "ob_tf": "H4",
  "ob_type": "OB",
  "ob_high": 1.1050,
  "ob_low": 1.1000,
  "div_tf": "D1",
  "div_type": "Logic2",
  "screenshot_url": null,
  "status": "pending_screenshot",
  "timestamp": 1705316400,
  "created_at": "2024-01-15T11:30:00Z",
  "updated_at": "2024-01-15T11:30:00Z"
}
```

---

#### 4. `tte_rotation_state`

Stores the current batch rotation state (singleton document).

##### Document Schema

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `_id` | string | Always `"current"` | `"current"` |
| `batch_number` | number | Total batches processed | `47` |
| `rotation_number` | number | Complete rotations | `2` |
| `symbols_scanned_this_rotation` | number | Progress in current rotation | `120` |
| `total_symbols` | number | Total active symbols | `941` |
| `last_batch_at` | Date\|null | Timestamp of last batch | `"2024-01-15T10:30:00Z"` |
| `last_batch_symbols` | array | Symbols in last batch | `["EURUSD", "GBPUSD"]` |
| `started_at` | Date | Rotation tracking start time | `"2024-01-01T00:00:00Z"` |
| `updated_at` | Date | Last update time | `"2024-01-15T10:30:00Z"` |

##### Example Document

```json
{
  "_id": "current",
  "batch_number": 47,
  "rotation_number": 2,
  "symbols_scanned_this_rotation": 120,
  "total_symbols": 941,
  "last_batch_at": "2024-01-15T10:30:00Z",
  "last_batch_symbols": ["EURUSD", "GBPUSD", "USDJPY"],
  "started_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

#### 5. `tte_live_signals`

Stores the current live signal state for combo mode. One document per symbol, upserted on every webhook.

##### Document Schema

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `_id` | string | Symbol name (used as document ID) | `"GBPAUD"` |
| `symbol` | string | Trading symbol | `"GBPAUD"` |
| `nwe` | array | NWE signal entries | See below |
| `ob_fvg` | array | OB/FVG signal entries | See below |
| `divergence` | array | Divergence signal entries | See below |
| `last_updated` | Date | Last webhook update time | `"2026-02-11T12:00:00Z"` |

##### NWE Entry Schema

| Field | Type | Description |
|-------|------|-------------|
| `zone` | string | NWE zone name (`lower_avg`, `lower_far`, `upper_avg`, `upper_far`) |
| `type` | string | Signal direction (`bullish` or `bearish`) |
| `overlapTimestamp` | number | Timestamp when price overlapped zone (ms) |
| `timeframe` | string | Signal timeframe (`1H`, `H4`) |

##### OB/FVG Entry Schema

| Field | Type | Description |
|-------|------|-------------|
| `zonetype` | string | Zone type (`OB`, `FVG`, `Breaker`) |
| `subtype` | string | Sub-type (`unmitigated`, `unfilled`, etc.) |
| `type` | string | Signal direction (`bullish` or `bearish`) |
| `zoneTimestamp` | number | When the zone was created (ms) |
| `overlapTimestamp` | number | When price overlapped the zone (ms) |
| `timeframe` | string | Signal timeframe (`1H`, `H4`, `D1`) |

##### Divergence Entry Schema

| Field | Type | Description |
|-------|------|-------------|
| `divType` | string | Divergence type (`Logic 2`) |
| `type` | string | Signal direction (`bullish` or `bearish`) |
| `timestamp` | number | Divergence detection time (ms) |
| `timeframe` | string | Signal timeframe (`1H`, `H4`) |

##### Example Document

```json
{
  "_id": "GBPAUD",
  "symbol": "GBPAUD",
  "nwe": [
    {"zone": "lower_avg", "type": "bullish", "overlapTimestamp": 1707264000000, "timeframe": "1H"}
  ],
  "ob_fvg": [
    {"zonetype": "OB", "subtype": "unmitigated", "type": "bullish", "zoneTimestamp": 1707260400000, "overlapTimestamp": 1707264000000, "timeframe": "H4"}
  ],
  "divergence": [],
  "last_updated": "2026-02-11T12:00:00Z"
}
```

##### Upsert Behavior

- Document `_id` is the symbol name (e.g., `"GBPAUD"`)
- Each webhook **replaces** the entire signal state for included symbols
- Symbols NOT in a webhook payload retain their previous state
- Signals persist indefinitely — users judge freshness via `last_updated`

---

## Database Operations

### TTE Symbols Access

Symbols are accessed via `resources/symbol_settings.py`:

```python
from resources.symbol_settings import get_symbols, get_symbol_categories

# Get all symbols grouped by category
symbols = get_symbols()
# Returns: {"currencies": ["OANDA:EURUSD", ...], "us_stocks": [...], ...}

# Get symbol-to-category mapping
categories = get_symbol_categories()
# Returns: {"EURUSD": "currencies", "AAPL": "us_stocks", ...}
```

### Stock Buddy Database Operations

Stock Buddy database is accessed via API. See [API.md](API.md) for complete endpoint documentation.

---

---

## Query Examples

### Stock Buddy Signals (via API)

```bash
# Get Level 3 signals
curl "https://stock-buddy-app.vercel.app/api/tte/signals?level=3&limit=20"

# Get bullish signals from last 48 hours
curl "https://stock-buddy-app.vercel.app/api/tte/signals?direction=bullish&from=1705226400"

# Get signals pending screenshots
curl "https://stock-buddy-app.vercel.app/api/tte/signals?status=pending_screenshot"
```

---

## Backup and Maintenance

### Backup with mongodump (TTE Local)

```bash
# Backup entire database
mongodump --uri="mongodb+srv://user:pass@cluster.mongodb.net/tte" --out=./backup

# Backup specific collection
mongodump --uri="mongodb+srv://user:pass@cluster.mongodb.net/tte" \
  --collection="Point Capitalis signals" --out=./backup
```

### Restore with mongorestore

```bash
# Restore database
mongorestore --uri="mongodb+srv://user:pass@cluster.mongodb.net/tte" ./backup/tte
```

### Maintenance Tasks

```python
from database.local_db import Database

db = Database()

# Keep only last 1000 signals
db.delete_some(1000)

# Update TV links to direct PNG URLs
db.change_tv_links()
```

### Atlas Considerations

- M0 (free tier) has 512MB storage limit
- Set up alerts for storage usage
- Consider TTL indexes for automatic document expiration
- Use Atlas triggers for automated maintenance

---

## Database Summary

| Database | Access | Key Collections |
|----------|--------|-----------------|
| **TTE Symbols** | Direct PyMongo (`resources/symbol_settings.py`) | `symbols` |
| **Stock Buddy** | Via REST API | `tte_live_signals`, `tte_symbols`, `tte_signals` |

---

## See Also

- [Setup Guide](SETUP.md) - MongoDB configuration
- [Combo Architecture](combo/ARCHITECTURE.md) - How database integrates with other components
- [API Reference](API.md) - Stock Buddy API endpoints
