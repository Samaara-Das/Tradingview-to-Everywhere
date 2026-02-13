# MongoDB Schema Reference

Complete documentation of all data schemas used in the TTE project.

## Contents

- TTE Local Database schemas (PyMongo direct access)
- Stock Buddy Database schemas (REST API access)
- Field definitions and data types
- Index recommendations
- Example documents

## Database Systems Overview

The TTE project uses two separate database systems:

1. **TTE Local Database** - Direct MongoDB access via PyMongo
   - Database: `tte`
   - Collection: `Point Capitalis signals`
   - Access: `database/local_db.py`
   - Used by: Legacy mode trading operations

2. **Stock Buddy Database** - REST API access
   - Collections: `tte_symbols`, `tte_hot_list`, `tte_signals`, `tte_rotation_state`
   - Access: `api_client.py`
   - Used by: Tiered orchestrator system

## TTE Local Database (`tte`)

### Collection: "Point Capitalis signals"

Primary collection for storing trading signals in legacy mode.

#### Schema Definition

```python
{
    "_id": ObjectId,                    # Auto-generated MongoDB ID
    "symbol": str,                      # Trading symbol (e.g., "EURUSD", "AAPL")
    "direction": str,                   # "bullish" or "bearish"
    "timeframe": str,                   # "H4", "D1", "W", etc.
    "screener": str,                    # "NWE" or "OBDIV"
    "timestamp": int,                   # Unix timestamp (seconds)
    "unixTime": int,                    # Unix timestamp (seconds) - used for sorting
    "info": dict,                       # Additional signal information
    "tvEntrySnapshot": str,             # TradingView chart URL or PNG URL
    "pngEntrySnapshot": str,            # Direct PNG image URL
    "tvExitSnapshot": str,              # TradingView exit chart URL (added later)
    "category": str,                    # "currencies", "us_stocks", "indian_stocks", "crypto"
    "status": str,                      # "active" or "closed" (optional)
    "entry_price": float,               # Entry price (optional)
    "stop_loss": float,                 # Stop loss level (optional)
    "take_profit": float,               # Take profit level (optional)
    "exit_price": float,                # Exit price (optional)
    "profit_loss": float                # P/L calculation (optional)
}
```

#### Field Descriptions

**Core Fields:**

- **_id** - MongoDB ObjectId, automatically generated
- **symbol** - Trading pair or stock symbol
  - Format: No spaces, uppercase recommended
  - Examples: "EURUSD", "AAPL", "BTC/USD"

- **direction** - Trade direction
  - Valid values: "bullish", "bearish"
  - Determines buy/sell recommendation

- **timeframe** - Chart timeframe for analysis
  - Common values: "H1", "H4", "D1", "W", "M"
  - Matches TradingView timeframe codes

- **screener** - Screener that generated the signal
  - Valid values: "NWE", "OBDIV"
  - "NWE" = New Week Environment zones
  - "OBDIV" = Order Block + Divergence

**Timestamp Fields:**

- **timestamp** - Unix timestamp in seconds
  - Used for: Signal creation time
  - Type: Integer (seconds since epoch)

- **unixTime** - Unix timestamp in seconds
  - Used for: Sorting and querying latest signals
  - Type: Integer (seconds since epoch)
  - Note: Often same as `timestamp` but specifically for sorting

**Chart/Image Fields:**

- **tvEntrySnapshot** - TradingView chart URL
  - Format: "https://www.tradingview.com/x/..."
  - May be converted to direct PNG URL

- **pngEntrySnapshot** - Direct PNG image URL
  - Format: "https://s3.tradingview.com/..."
  - Extracted from TradingView snapshot page

- **tvExitSnapshot** - Exit chart snapshot
  - Added when trade exits
  - Same format as entry snapshot

**Classification:**

- **category** - Asset class
  - Valid values: "currencies", "us_stocks", "indian_stocks", "crypto"
  - Defined in `tte/data/symbols.py`

**Trade Management (Optional):**

- **status** - Trade lifecycle status
  - Values: "active", "closed"
  - Used for tracking open positions

- **entry_price** - Actual entry price
- **stop_loss** - Stop loss level
- **take_profit** - Target profit level
- **exit_price** - Actual exit price
- **profit_loss** - Calculated P/L

**Additional Data:**

- **info** - Flexible dict for extra data
  - Can contain: indicator values, confidence scores, notes
  - Structure varies by screener

#### Example Documents

**Minimal signal document:**
```python
{
    "_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e1"),
    "symbol": "EURUSD",
    "direction": "bullish",
    "timeframe": "H4",
    "screener": "NWE",
    "timestamp": 1705132800,
    "unixTime": 1705132800,
    "info": {},
    "tvEntrySnapshot": "https://www.tradingview.com/x/abc123/",
    "pngEntrySnapshot": "https://s3.tradingview.com/snapshots/abc123.png",
    "category": "currencies"
}
```

**Complete signal document:**
```python
{
    "_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e1"),
    "symbol": "AAPL",
    "direction": "bearish",
    "timeframe": "D1",
    "screener": "OBDIV",
    "timestamp": 1705132800,
    "unixTime": 1705132800,
    "info": {
        "divergence_type": "regular",
        "rsi": 68.5,
        "confidence": "high"
    },
    "tvEntrySnapshot": "https://www.tradingview.com/x/xyz789/",
    "pngEntrySnapshot": "https://s3.tradingview.com/snapshots/xyz789.png",
    "tvExitSnapshot": "https://s3.tradingview.com/snapshots/exit123.png",
    "category": "us_stocks",
    "status": "closed",
    "entry_price": 182.50,
    "stop_loss": 185.00,
    "take_profit": 177.00,
    "exit_price": 177.25,
    "profit_loss": 5.25
}
```

#### Index Recommendations

```python
# Sorting index (most commonly used)
db["Point Capitalis signals"].create_index([("unixTime", -1)])

# Symbol lookup
db["Point Capitalis signals"].create_index("symbol")

# Status filtering
db["Point Capitalis signals"].create_index("status")

# Category filtering
db["Point Capitalis signals"].create_index("category")

# Compound index for common queries
db["Point Capitalis signals"].create_index([
    ("status", 1),
    ("unixTime", -1)
])

# TTL index for automatic cleanup (30 days)
db["Point Capitalis signals"].create_index(
    "timestamp",
    expireAfterSeconds=2592000
)
```

#### Common Queries

**Get latest signal:**
```python
latest = db["Point Capitalis signals"].find_one(
    sort=[("unixTime", pymongo.DESCENDING)]
)
```

**Get active trades:**
```python
active_trades = db["Point Capitalis signals"].find(
    {"status": "active"}
).sort("unixTime", -1)
```

**Get signals by symbol:**
```python
eurusd_signals = db["Point Capitalis signals"].find(
    {"symbol": "EURUSD"}
).sort("unixTime", -1).limit(10)
```

**Get signals by timeframe and direction:**
```python
h4_bullish = db["Point Capitalis signals"].find({
    "timeframe": "H4",
    "direction": "bullish"
}).sort("unixTime", -1)
```

## Stock Buddy Database (API Access)

These collections are accessed via REST API (`api_client.py`), not directly via PyMongo.

### Collection: `tte_symbols`

Symbol registry with priority and rotation tracking.

#### Schema

```python
{
    "_id": ObjectId,
    "symbol": str,              # Trading symbol
    "priority": int,            # Processing priority (1-5)
    "last_scanned": datetime,   # Last NWE scan timestamp
    "scan_count": int,          # Total number of scans
    "is_active": bool,          # Whether symbol is currently active
    "category": str,            # Asset category
    "metadata": dict            # Additional symbol metadata
}
```

#### Example Document

```python
{
    "_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e1"),
    "symbol": "EURUSD",
    "priority": 1,
    "last_scanned": ISODate("2025-01-13T12:00:00Z"),
    "scan_count": 47,
    "is_active": true,
    "category": "currencies",
    "metadata": {
        "exchange": "forex",
        "base_currency": "EUR",
        "quote_currency": "USD"
    }
}
```

#### API Access

```python
# Get next batch for scanning
symbols = client.get_next_batch(size=20)
# Returns: List[str] of symbol names

# Mark symbols as scanned
client.mark_scanned(["EURUSD", "GBPUSD"])
# Returns: bool
```

### Collection: `tte_hot_list`

Symbols that passed Tier 1 (NWE), pending Tier 2 (OBDIV) processing.

#### Schema

```python
{
    "_id": ObjectId,
    "symbol": str,              # Trading symbol
    "timeframe": str,           # Timeframe from Tier 1
    "direction": str,           # Direction from Tier 1
    "tier1_timestamp": datetime, # When added to hot list
    "tier1_data": dict,         # NWE screener data
    "status": str,              # "pending_tier2", "processing", "completed"
    "tier2_timestamp": datetime, # When Tier 2 processed (optional)
    "expires_at": datetime      # Expiration timestamp
}
```

#### Example Document

```python
{
    "_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e1"),
    "symbol": "GBPUSD",
    "timeframe": "H4",
    "direction": "bullish",
    "tier1_timestamp": ISODate("2025-01-13T12:00:00Z"),
    "tier1_data": {
        "nwe_zone_price": 1.2650,
        "current_price": 1.2655,
        "zone_strength": "strong"
    },
    "status": "pending_tier2",
    "expires_at": ISODate("2025-01-13T16:00:00Z")
}
```

#### API Access

```python
# Get hot symbols for Tier 2
hot_symbols = client.get_hot_symbols(limit=50, status="pending_tier2")
# Returns: List[Dict] with symbol data

# Delete expired hot symbols
client.delete_expired_hot_symbols()
# Returns: Dict with deletion count
```

### Collection: `tte_signals`

Confirmed trading signals that passed both Tier 1 and Tier 2.

#### Schema

```python
{
    "_id": ObjectId,
    "symbol": str,
    "direction": str,
    "timeframe": str,
    "tier1_screener": str,      # "NWE"
    "tier2_screener": str,      # "OBDIV"
    "tier1_timestamp": datetime,
    "tier2_timestamp": datetime,
    "tier1_data": dict,         # NWE data
    "tier2_data": dict,         # OBDIV data
    "confidence_score": float,  # Combined confidence (0-1)
    "status": str,              # "active", "closed"
    "created_at": datetime,
    "updated_at": datetime
}
```

#### Example Document

```python
{
    "_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e1"),
    "symbol": "EURUSD",
    "direction": "bullish",
    "timeframe": "H4",
    "tier1_screener": "NWE",
    "tier2_screener": "OBDIV",
    "tier1_timestamp": ISODate("2025-01-13T12:00:00Z"),
    "tier2_timestamp": ISODate("2025-01-13T12:15:00Z"),
    "tier1_data": {
        "nwe_zone_price": 1.0950,
        "zone_strength": "strong"
    },
    "tier2_data": {
        "divergence_type": "bullish_regular",
        "order_block_price": 1.0945,
        "rsi": 32.5
    },
    "confidence_score": 0.85,
    "status": "active",
    "created_at": ISODate("2025-01-13T12:15:00Z"),
    "updated_at": ISODate("2025-01-13T12:15:00Z")
}
```

### Collection: `tte_rotation_state`

Tracks batch rotation state for symbol processing.

#### Schema

```python
{
    "_id": ObjectId,
    "current_batch": int,           # Current batch number (0-based)
    "total_batches": int,           # Total number of batches
    "batch_size": int,              # Symbols per batch (usually 20)
    "last_rotation": datetime,      # Last rotation timestamp
    "cycle_start": datetime,        # Current cycle start time
    "symbols_in_current_batch": list, # List of symbols in current batch
    "completed_batches": list       # List of completed batch numbers
}
```

#### Example Document

```python
{
    "_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e1"),
    "current_batch": 2,
    "total_batches": 5,
    "batch_size": 20,
    "last_rotation": ISODate("2025-01-13T12:00:00Z"),
    "cycle_start": ISODate("2025-01-13T10:00:00Z"),
    "symbols_in_current_batch": [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "..."
    ],
    "completed_batches": [0, 1]
}
```

## Data Type Mappings

### Python to MongoDB

```python
# String
"EURUSD" → BSON String

# Integer
1705132800 → BSON Int32 or Int64

# Float
1.0950 → BSON Double

# Boolean
True → BSON Boolean

# Dictionary
{"key": "value"} → BSON Document

# List
["EURUSD", "GBPUSD"] → BSON Array

# Datetime
datetime.now() → BSON Date

# None
None → BSON Null
```

### Common Type Issues

**Issue: Timestamp as string**
```python
# ❌ Bad: String timestamp
{"timestamp": "1705132800"}

# ✅ Good: Integer timestamp
{"timestamp": 1705132800}
```

**Issue: Boolean as string**
```python
# ❌ Bad: String boolean
{"is_active": "true"}

# ✅ Good: Actual boolean
{"is_active": True}
```

**Issue: Numeric as string**
```python
# ❌ Bad: String number
{"entry_price": "182.50"}

# ✅ Good: Float
{"entry_price": 182.50}
```

## Schema Validation (Optional)

MongoDB schema validation can be added for data integrity:

```python
# Add validation rules
db.command({
    "collMod": "Point Capitalis signals",
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["symbol", "direction", "timeframe", "screener", "timestamp"],
            "properties": {
                "symbol": {
                    "bsonType": "string",
                    "description": "Trading symbol (required)"
                },
                "direction": {
                    "enum": ["bullish", "bearish"],
                    "description": "Trade direction (required)"
                },
                "timeframe": {
                    "bsonType": "string",
                    "description": "Chart timeframe (required)"
                },
                "screener": {
                    "enum": ["NWE", "OBDIV"],
                    "description": "Screener type (required)"
                },
                "timestamp": {
                    "bsonType": "int",
                    "description": "Unix timestamp (required)"
                }
            }
        }
    },
    "validationLevel": "moderate"  # "strict" or "moderate"
})
```

## Migration Considerations

When migrating between schema versions:

1. **Add new fields with defaults:**
```python
db["Point Capitalis signals"].update_many(
    {"status": {"$exists": False}},
    {"$set": {"status": "active"}}
)
```

2. **Rename fields:**
```python
db["Point Capitalis signals"].update_many(
    {},
    {"$rename": {"old_field": "new_field"}}
)
```

3. **Change data types:**
```python
# Convert string to int
for doc in db["Point Capitalis signals"].find({"timestamp": {"$type": "string"}}):
    db["Point Capitalis signals"].update_one(
        {"_id": doc["_id"]},
        {"$set": {"timestamp": int(doc["timestamp"])}}
    )
```

4. **Remove deprecated fields:**
```python
db["Point Capitalis signals"].update_many(
    {},
    {"$unset": {"deprecated_field": ""}}
)
```
