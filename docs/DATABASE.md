# Database Documentation

MongoDB schema and collections documentation for TTE and Stock Buddy integration.

## Overview

TTE uses two separate MongoDB databases:

1. **TTE Local Database**: Stores trading signals captured by TTE's legacy mode
2. **Stock Buddy Database**: Stores tiered signals, hot list, and symbol rotation data (accessed via API)

---

## TTE Local Database

TTE's local database stores trading signals and symbol management for legacy mode. The application supports both MongoDB Atlas (cloud) and local MongoDB installations.

**Database Name**: `tte` (configurable via `MONGODB_DATABASE` environment variable)

**Client Implementation**: `database/local_db.py` - `Database` class

### Connection Configuration

#### Environment Variables

```bash
# Option 1: Full connection string (preferred)
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority

# Option 2: Password only (uses default connection string)
MONGODB_PWD=your_password

# Database name (optional, defaults to "tte")
MONGODB_DATABASE=tte
```

#### Connection Code

```python
from database.local_db import Database

# Initialize connection
db = Database()

# With document deletion on init (use carefully)
db = Database(delete=True)
```

### Collections

#### 1. `Point Capitalis signals`

Stores trading signals captured from TradingView (legacy mode).

**Collection Name**: Defined in `env.py` as `COLLECTION`

##### Document Schema

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `_id` | ObjectId | MongoDB auto-generated ID | `ObjectId("...")` |
| `symbol` | string | Trading symbol | `"EURUSD"` |
| `direction` | string | Trade direction | `"bullish"` or `"bearish"` |
| `timeframe` | string | Signal timeframe | `"H4"` |
| `entry_price` | number | Entry price level | `1.0850` |
| `stop_loss` | number | Stop loss price | `1.0800` |
| `take_profit` | number | Take profit price | `1.0950` |
| `category` | string | Symbol category | `"currencies"` |
| `unixTime` | number | Unix timestamp (seconds) | `1705312800` |
| `tvEntrySnapshot` | string | TradingView entry chart URL | `"https://..."` |
| `tvExitSnapshot` | string | TradingView exit chart URL | `"https://..."` |
| `status` | string | Signal status | `"active"`, `"closed"` |
| `exit_price` | number | Exit price (if closed) | `1.0920` |
| `profit_loss` | number | P/L percentage | `0.65` |

##### Example Document

```json
{
  "_id": "ObjectId('65a5b2c1d4e5f6a7b8c9d0e1')",
  "symbol": "EURUSD",
  "direction": "bullish",
  "timeframe": "H4",
  "entry_price": 1.0850,
  "stop_loss": 1.0800,
  "take_profit": 1.0950,
  "category": "currencies",
  "unixTime": 1705312800,
  "tvEntrySnapshot": "https://www.tradingview.com/x/abc123/",
  "tvExitSnapshot": "",
  "status": "active"
}
```

##### Indexes

```javascript
// Recommended indexes for query optimization
db["Point Capitalis signals"].createIndex({ "unixTime": -1 })
db["Point Capitalis signals"].createIndex({ "symbol": 1, "status": 1 })
db["Point Capitalis signals"].createIndex({ "category": 1 })
```

---

#### 2. `symbols`

Stores symbol definitions and categories for the screeners.

##### Document Schema

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `_id` | ObjectId | MongoDB auto-generated ID | `ObjectId("...")` |
| `symbol` | string | Short symbol name | `"EURUSD"` |
| `full_symbol` | string | Full symbol with exchange | `"OANDA:EURUSD"` |
| `category` | string | Symbol category | `"currencies"` |
| `active` | boolean | Whether symbol is active | `true` |

##### Categories

| Category | Webhook Name | Typical Count |
|----------|-------------|---------------|
| `currencies` | `CURRENCIES_WEBHOOK_NAME` | ~30 |
| `us_stocks` | `US_STOCKS_WEBHOOK_NAME` | ~719 |
| `indian_stocks` | `INDIAN_STOCKS_WEBHOOK_NAME` | ~268 |
| `crypto` | `CRYPTO_WEBHOOK_NAME` | ~19 |
| `indices` | - | ~18 |

---

## Stock Buddy Database

Stock Buddy maintains its own MongoDB database for the tiered signal system. TTE interacts with this database through the Stock Buddy API, not directly.

**Database Name**: `tte` (on Stock Buddy's MongoDB Atlas cluster)

**Access Method**: Via Stock Buddy API endpoints (see [API.md](API.md))

### Collections

| Collection | Purpose | Access via API |
|------------|---------|----------------|
| `tte_symbols` | Symbol registry with priority/category | `/api/tte/symbols/*` |
| `tte_hot_list` | Symbols pending Tier 2 processing | `/api/tte/hot-symbols` |
| `tte_signals` | Confirmed TTE signals | `/api/tte/signals` |
| `tte_rotation_state` | Batch rotation tracking | `/api/tte/stats`, `/api/tte/init` |

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

## Database Operations

### TTE Local Database Operations

The `Database` class in `database/local_db.py` provides these methods:

#### `add_doc(doc: dict) -> bool`

Add a document to the signals collection.

```python
db = Database()
doc = {
    "symbol": "EURUSD",
    "direction": "bullish",
    "timeframe": "H4",
    "unixTime": int(time.time())
}
success = db.add_doc(doc)
```

#### `get_latest_doc() -> dict | None`

Get the most recent document by `unixTime`.

```python
latest = db.get_latest_doc()
if latest:
    print(f"Latest signal: {latest['symbol']}")
```

#### `delete_all()`

Delete all documents in the collection (use with caution).

```python
db = Database(delete=True)  # Deletes on init
# OR
db.delete_all()
```

#### `delete_some(count: int)`

Keep the latest `count` documents and delete the rest.

```python
db.delete_some(100)  # Keep only the 100 most recent signals
```

---

### Stock Buddy Database Operations

Stock Buddy database is accessed via API. See [API.md](API.md) for complete endpoint documentation.

**Common Operations via API:**

```python
from api_client import StockBuddyAPIClient

api = StockBuddyAPIClient(base_url, timeout)

# Get next batch of symbols
batch = api.get_next_symbol_batch(size=20)

# Mark symbols as scanned
api.mark_symbols_scanned(["EURUSD", "GBPUSD"])

# Get hot symbols pending Tier 2
hot_symbols = api.get_hot_symbols(limit=8)

# Get statistics
stats = api.get_stats()
```

---

## Symbol Operations

The `resources/symbol_settings.py` module provides symbol management for legacy mode:

### `get_symbols() -> dict`

Get all symbols grouped by category.

```python
from resources.symbol_settings import get_symbols

symbols = get_symbols()
# Returns: {"currencies": ["OANDA:EURUSD", ...], "us_stocks": [...], ...}
```

### `get_symbol_categories() -> dict`

Get symbol-to-category mapping.

```python
from resources.symbol_settings import get_symbol_categories

categories = get_symbol_categories()
# Returns: {"EURUSD": "currencies", "AAPL": "us_stocks", ...}
```

### `symbol_category(symbol: str) -> str | None`

Get the category for a specific symbol.

```python
from resources.symbol_settings import symbol_category

category = symbol_category("EURUSD")
# Returns: "currencies"
```

---

## Query Examples

### MongoDB Shell (TTE Local)

```javascript
// Find all active signals
db["Point Capitalis signals"].find({ status: "active" })

// Find signals for a specific symbol
db["Point Capitalis signals"].find({ symbol: "EURUSD" }).sort({ unixTime: -1 })

// Count signals by category
db["Point Capitalis signals"].aggregate([
  { $group: { _id: "$category", count: { $sum: 1 } } }
])

// Find signals from last 24 hours
db["Point Capitalis signals"].find({
  unixTime: { $gte: (Date.now() / 1000) - 86400 }
})
```

### Python (PyMongo) - TTE Local

```python
from database.local_db import Database

db = Database()

# Find active signals
active_signals = db.db[db.collection_name].find({"status": "active"})

# Find by symbol with sorting
signals = db.db[db.collection_name].find(
    {"symbol": "EURUSD"}
).sort("unixTime", -1).limit(10)
```

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

## Tiered Mode Considerations

In tiered mode, symbols are fetched from the Stock Buddy API rather than TTE's local MongoDB. The environment variable `SKIP_MONGODB_SYMBOLS` controls this:

```python
# In tiered_main.py
os.environ["SKIP_MONGODB_SYMBOLS"] = "true"
```

This prevents `symbol_settings.py` from loading symbols at import time, avoiding MongoDB dependency for the tiered orchestrator's symbol management.

---

## Database Comparison

| Feature | TTE Local DB | Stock Buddy DB |
|---------|--------------|----------------|
| **Access** | Direct PyMongo | Via REST API |
| **Signals** | Legacy format | Tiered (Level 1/2/3) |
| **Symbol Management** | `symbols` collection | `tte_symbols` with priority |
| **Rotation Tracking** | None | `tte_rotation_state` |
| **Hot List** | None | `tte_hot_list` |

---

## See Also

- [Setup Guide](SETUP.md) - MongoDB configuration
- [Architecture](ARCHITECTURE.md) - How database integrates with other components
- [API Reference](API.md) - Stock Buddy API endpoints
