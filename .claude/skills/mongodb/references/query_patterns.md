# MongoDB Query Patterns

Common query patterns, CRUD operations, and optimization techniques for the TTE project.

## Contents

- Basic CRUD operations
- Advanced queries with aggregation
- Bulk operations and optimization
- Sorting and pagination
- Update patterns
- Delete patterns
- Performance optimization

## Basic CRUD Operations

### Create (Insert)

**Single document:**
```python
from database.local_db import Database

db = Database()
result = db.add_doc({
    "symbol": "EURUSD",
    "direction": "bullish",
    "timeframe": "H4",
    "screener": "NWE",
    "timestamp": int(time.time()),
    "unixTime": int(time.time()),
    "category": "currencies",
    "tvEntrySnapshot": "https://...",
    "pngEntrySnapshot": "https://..."
})
```

**Multiple documents:**
```python
collection = db.db["Point Capitalis signals"]

documents = [
    {"symbol": "EURUSD", "direction": "bullish", ...},
    {"symbol": "GBPUSD", "direction": "bearish", ...},
    {"symbol": "USDJPY", "direction": "bullish", ...}
]

result = collection.insert_many(documents)
print(f"Inserted {len(result.inserted_ids)} documents")
```

**Insert with validation:**
```python
def insert_signal(collection, signal_data):
    """Insert signal with validation."""
    required_fields = ["symbol", "direction", "timeframe", "screener", "timestamp"]

    # Validate required fields
    missing = [f for f in required_fields if f not in signal_data]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    # Validate direction
    if signal_data["direction"] not in ["bullish", "bearish"]:
        raise ValueError("Direction must be 'bullish' or 'bearish'")

    # Validate screener
    if signal_data["screener"] not in ["NWE", "OBDIV"]:
        raise ValueError("Screener must be 'NWE' or 'OBDIV'")

    # Insert
    return collection.insert_one(signal_data)
```

### Read (Query)

**Get latest document:**
```python
# Current implementation in local_db.py
def get_latest_doc(self):
    try:
        doc = self.db[self.collection_name].find_one(
            sort=[("unixTime", pymongo.DESCENDING)]
        )
        return doc
    except Exception as e:
        logger.exception(f"Error: {e}")
        return None
```

**Find by symbol:**
```python
# Get all signals for EURUSD
eurusd_signals = collection.find({"symbol": "EURUSD"})

# With projection (only specific fields)
eurusd_signals = collection.find(
    {"symbol": "EURUSD"},
    {"symbol": 1, "direction": 1, "timestamp": 1, "_id": 0}
)
```

**Find with conditions:**
```python
# Bullish signals on H4 timeframe
query = {
    "direction": "bullish",
    "timeframe": "H4"
}
results = collection.find(query)

# Multiple conditions with OR
query = {
    "$or": [
        {"symbol": "EURUSD"},
        {"symbol": "GBPUSD"}
    ]
}
results = collection.find(query)

# Range queries
query = {
    "timestamp": {
        "$gte": 1704067200,  # After Jan 1, 2024
        "$lt": 1735689600     # Before Jan 1, 2025
    }
}
results = collection.find(query)
```

**Find with regex:**
```python
# Find all EUR pairs
query = {"symbol": {"$regex": "^EUR", "$options": "i"}}
eur_pairs = collection.find(query)

# Find symbols containing "USD"
query = {"symbol": {"$regex": "USD", "$options": "i"}}
usd_pairs = collection.find(query)
```

**Find one vs find:**
```python
# find_one - returns single document (dict) or None
latest = collection.find_one(sort=[("unixTime", -1)])

# find - returns cursor (iterator)
all_signals = collection.find()
for signal in all_signals:
    print(signal["symbol"])
```

### Update

**Update single document:**
```python
# Update by _id
from bson import ObjectId

collection.update_one(
    {"_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e1")},
    {"$set": {"status": "closed", "exit_price": 1.0975}}
)

# Update by field
collection.update_one(
    {"symbol": "EURUSD", "status": "active"},
    {"$set": {"status": "closed"}}
)
```

**Update multiple documents:**
```python
# Close all active EURUSD trades
result = collection.update_many(
    {"symbol": "EURUSD", "status": "active"},
    {"$set": {"status": "closed", "exit_timestamp": int(time.time())}}
)
print(f"Modified {result.modified_count} documents")
```

**Update operators:**
```python
# $set - Set field value
collection.update_one({"_id": doc_id}, {"$set": {"field": "value"}})

# $inc - Increment numeric field
collection.update_one({"symbol": "EURUSD"}, {"$inc": {"view_count": 1}})

# $push - Add to array
collection.update_one({"_id": doc_id}, {"$push": {"tags": "important"}})

# $pull - Remove from array
collection.update_one({"_id": doc_id}, {"$pull": {"tags": "old"}})

# $addToSet - Add to array if not exists
collection.update_one({"_id": doc_id}, {"$addToSet": {"tags": "new"}})

# $unset - Remove field
collection.update_one({"_id": doc_id}, {"$unset": {"deprecated_field": ""}})

# $rename - Rename field
collection.update_one({"_id": doc_id}, {"$rename": {"old_name": "new_name"}})
```

**Upsert (update or insert):**
```python
# If document exists, update it; otherwise, insert new
collection.update_one(
    {"symbol": "EURUSD", "timeframe": "H4"},
    {"$set": {"last_price": 1.0950, "updated_at": datetime.now()}},
    upsert=True
)
```

### Delete

**Delete single document:**
```python
# Delete by _id
collection.delete_one({"_id": ObjectId("65a1b2c3d4e5f6a7b8c9d0e1")})

# Delete first match
collection.delete_one({"symbol": "EURUSD", "status": "closed"})
```

**Delete multiple documents:**
```python
# Delete all closed trades
result = collection.delete_many({"status": "closed"})
print(f"Deleted {result.deleted_count} documents")

# Delete all (implemented in local_db.py)
def delete_all(self):
    try:
        result = self.db[self.collection_name].delete_many({})
        logger.info(f"Deleted {result.deleted_count} documents")
    except Exception as e:
        logger.exception(f"Error: {e}")
```

**Delete with limit (keep latest N):**
```python
# Implementation from local_db.py
def delete_some(self, count: int):
    """Keep latest 'count' documents, delete rest."""
    try:
        # Get IDs of latest documents
        latest_ids = [
            x["_id"]
            for x in self.db[self.collection_name]
            .find()
            .sort("unixTime", pymongo.DESCENDING)
            .limit(count)
        ]

        # Delete all except latest
        if latest_ids:
            result = self.db[self.collection_name].delete_many(
                {"_id": {"$nin": latest_ids}}
            )
            logger.info(f"Deleted {result.deleted_count} documents")
    except Exception as e:
        logger.exception(f"Error: {e}")
```

## Advanced Queries

### Aggregation Pipeline

**Count by direction:**
```python
pipeline = [
    {"$group": {
        "_id": "$direction",
        "count": {"$sum": 1}
    }}
]
results = collection.aggregate(pipeline)
# Output: {"_id": "bullish", "count": 45}, {"_id": "bearish", "count": 32}
```

**Average profit/loss by symbol:**
```python
pipeline = [
    {"$match": {"status": "closed"}},  # Filter closed trades
    {"$group": {
        "_id": "$symbol",
        "avg_profit": {"$avg": "$profit_loss"},
        "total_trades": {"$sum": 1}
    }},
    {"$sort": {"avg_profit": -1}}  # Sort by avg profit descending
]
results = collection.aggregate(pipeline)
```

**Group by timeframe and screener:**
```python
pipeline = [
    {"$group": {
        "_id": {
            "timeframe": "$timeframe",
            "screener": "$screener"
        },
        "count": {"$sum": 1}
    }},
    {"$sort": {"count": -1}}
]
results = collection.aggregate(pipeline)
```

**Date-based aggregation:**
```python
from datetime import datetime, timedelta

# Signals in last 7 days
seven_days_ago = int((datetime.now() - timedelta(days=7)).timestamp())

pipeline = [
    {"$match": {"timestamp": {"$gte": seven_days_ago}}},
    {"$group": {
        "_id": {
            "$dateToString": {
                "format": "%Y-%m-%d",
                "date": {"$toDate": {"$multiply": ["$timestamp", 1000]}}
            }
        },
        "count": {"$sum": 1}
    }},
    {"$sort": {"_id": 1}}
]
results = collection.aggregate(pipeline)
```

### Complex Queries

**Find with multiple conditions:**
```python
query = {
    "$and": [
        {"direction": "bullish"},
        {"timeframe": {"$in": ["H4", "D1"]}},
        {"timestamp": {"$gte": 1704067200}},
        {"$or": [
            {"screener": "NWE"},
            {"screener": "OBDIV"}
        ]}
    ]
}
results = collection.find(query)
```

**Nested field queries:**
```python
# Query nested info dict
query = {"info.divergence_type": "regular"}
results = collection.find(query)

# Check if nested field exists
query = {"info.rsi": {"$exists": True}}
results = collection.find(query)

# Query nested array
query = {"info.indicators": {"$in": ["RSI", "MACD"]}}
results = collection.find(query)
```

**Text search (requires text index):**
```python
# Create text index first
collection.create_index([("symbol", "text"), ("category", "text")])

# Search
results = collection.find({"$text": {"$search": "EUR USD"}})
```

## Sorting and Pagination

### Sorting

**Single field:**
```python
# Ascending
results = collection.find().sort("timestamp", 1)

# Descending (most recent first)
results = collection.find().sort("timestamp", -1)
```

**Multiple fields:**
```python
# Sort by direction (asc), then timestamp (desc)
results = collection.find().sort([
    ("direction", 1),
    ("timestamp", -1)
])
```

### Pagination

**Basic pagination:**
```python
def get_page(collection, page=1, per_page=20):
    """Get paginated results."""
    skip = (page - 1) * per_page
    return collection.find().sort("timestamp", -1).skip(skip).limit(per_page)

# Usage
page_1 = get_page(collection, page=1, per_page=20)
page_2 = get_page(collection, page=2, per_page=20)
```

**Cursor-based pagination (more efficient):**
```python
def get_next_page(collection, last_timestamp=None, limit=20):
    """Get next page using cursor-based pagination."""
    query = {}
    if last_timestamp:
        query["timestamp"] = {"$lt": last_timestamp}

    results = collection.find(query).sort("timestamp", -1).limit(limit)
    return list(results)

# Usage
page_1 = get_next_page(collection, limit=20)
last_ts = page_1[-1]["timestamp"] if page_1 else None
page_2 = get_next_page(collection, last_timestamp=last_ts, limit=20)
```

## Bulk Operations

### Bulk Write

**Implementation from local_db.py:**
```python
def change_tv_links(self):
    """Convert TradingView URLs to PNG links using bulk operations."""
    try:
        collection = self.db[self.collection_name]
        bulk_operations = []

        # Find documents needing conversion
        query = {
            "tvExitSnapshot": {"$regex": r"\.png", "$options": "i"},
            "tvEntrySnapshot": {"$not": {"$regex": r"\.png", "$options": "i"}},
        }

        # Build bulk operations
        for doc in collection.find(query, {"_id": 1, "tvEntrySnapshot": 1}):
            entry_url = doc.get("tvEntrySnapshot")
            new_entry_link = self.extract_img_src(entry_url, "entry")

            if new_entry_link:
                bulk_operations.append(
                    UpdateOne(
                        {"_id": doc["_id"]},
                        {"$set": {"tvEntrySnapshot": new_entry_link}},
                    )
                )

        # Execute bulk write
        if bulk_operations:
            result = collection.bulk_write(bulk_operations)
            logger.info(f"Modified: {result.modified_count}")

    except Exception as e:
        logger.exception(f"Error: {e}")
```

**Bulk insert:**
```python
from pymongo import InsertOne

bulk_operations = [
    InsertOne({"symbol": "EURUSD", "direction": "bullish", ...}),
    InsertOne({"symbol": "GBPUSD", "direction": "bearish", ...}),
]
result = collection.bulk_write(bulk_operations)
```

**Mixed bulk operations:**
```python
from pymongo import InsertOne, UpdateOne, DeleteOne

bulk_operations = [
    InsertOne({"symbol": "EURUSD", ...}),
    UpdateOne({"symbol": "GBPUSD"}, {"$set": {"status": "closed"}}),
    DeleteOne({"symbol": "USDJPY", "status": "expired"}),
]
result = collection.bulk_write(bulk_operations, ordered=False)
```

**Chunked bulk operations (memory efficient):**
```python
def bulk_update_in_chunks(collection, operations, chunk_size=1000):
    """Execute bulk operations in chunks."""
    total_modified = 0

    for i in range(0, len(operations), chunk_size):
        chunk = operations[i:i + chunk_size]
        result = collection.bulk_write(chunk)
        total_modified += result.modified_count
        logger.info(f"Processed chunk {i//chunk_size + 1}, modified: {result.modified_count}")

    return total_modified

# Usage
operations = [UpdateOne(...) for doc in large_dataset]
total = bulk_update_in_chunks(collection, operations, chunk_size=1000)
```

## Performance Optimization

### Indexes

**Create indexes for common queries:**
```python
# Single field index
collection.create_index("symbol")
collection.create_index([("timestamp", -1)])

# Compound index
collection.create_index([("symbol", 1), ("timeframe", 1)])

# Unique index
collection.create_index("symbol", unique=True)

# TTL index (auto-delete after expiration)
collection.create_index("timestamp", expireAfterSeconds=2592000)  # 30 days

# Text index for full-text search
collection.create_index([("symbol", "text"), ("category", "text")])
```

**List indexes:**
```python
indexes = collection.list_indexes()
for index in indexes:
    print(index)
```

**Drop index:**
```python
collection.drop_index("symbol_1")
```

### Query Optimization

**Use projection to limit fields:**
```python
# Only get fields you need
results = collection.find(
    {"symbol": "EURUSD"},
    {"symbol": 1, "direction": 1, "timestamp": 1, "_id": 0}
)
```

**Use limit when possible:**
```python
# Don't fetch all if you only need 10
latest_10 = collection.find().sort("timestamp", -1).limit(10)
```

**Use explain to analyze query performance:**
```python
query = {"symbol": "EURUSD"}
explanation = collection.find(query).explain()
print(explanation["executionStats"])
```

**Batch processing:**
```python
# Process large result sets in batches
cursor = collection.find().batch_size(100)
for doc in cursor:
    process_document(doc)
```

### Connection Optimization

**Connection pooling:**
```python
from pymongo import MongoClient

client = MongoClient(
    mongo_uri,
    maxPoolSize=50,      # Max connections
    minPoolSize=10,      # Min connections to maintain
    maxIdleTimeMS=45000  # Close idle connections
)
```

**Read preference:**
```python
from pymongo import ReadPreference

# Read from secondary (for analytics)
collection = db.get_collection(
    "Point Capitalis signals",
    read_preference=ReadPreference.SECONDARY
)
```

## Common Query Patterns for TTE

### Get Active Trades

```python
def get_active_trades(collection, symbol=None):
    """Get all active trades, optionally filtered by symbol."""
    query = {"status": "active"}
    if symbol:
        query["symbol"] = symbol

    return list(collection.find(query).sort("timestamp", -1))
```

### Get Recent Signals

```python
def get_recent_signals(collection, hours=24):
    """Get signals from last N hours."""
    from datetime import datetime, timedelta

    cutoff = int((datetime.now() - timedelta(hours=hours)).timestamp())
    return list(collection.find(
        {"timestamp": {"$gte": cutoff}}
    ).sort("timestamp", -1))
```

### Get Signals by Category

```python
def get_signals_by_category(collection, category, limit=50):
    """Get latest signals for a category."""
    return list(collection.find(
        {"category": category}
    ).sort("timestamp", -1).limit(limit))

# Usage
forex_signals = get_signals_by_category(collection, "currencies")
stock_signals = get_signals_by_category(collection, "us_stocks")
```

### Calculate Win Rate

```python
def calculate_win_rate(collection, symbol=None):
    """Calculate win rate for symbol or all symbols."""
    query = {"status": "closed", "profit_loss": {"$exists": True}}
    if symbol:
        query["symbol"] = symbol

    closed_trades = list(collection.find(query))

    if not closed_trades:
        return {"win_rate": 0, "total_trades": 0}

    wins = sum(1 for trade in closed_trades if trade["profit_loss"] > 0)
    total = len(closed_trades)

    return {
        "win_rate": (wins / total) * 100,
        "wins": wins,
        "losses": total - wins,
        "total_trades": total
    }
```

### Update Exit Information

```python
def update_exit(collection, doc_id, exit_price, exit_snapshot):
    """Update trade with exit information."""
    entry_doc = collection.find_one({"_id": doc_id})

    if not entry_doc:
        return False

    entry_price = entry_doc.get("entry_price")
    direction = entry_doc.get("direction")

    # Calculate P/L
    if entry_price:
        if direction == "bullish":
            profit_loss = exit_price - entry_price
        else:  # bearish
            profit_loss = entry_price - exit_price
    else:
        profit_loss = None

    # Update document
    collection.update_one(
        {"_id": doc_id},
        {"$set": {
            "status": "closed",
            "exit_price": exit_price,
            "exit_timestamp": int(time.time()),
            "tvExitSnapshot": exit_snapshot,
            "profit_loss": profit_loss
        }}
    )

    return True
```

## Error Handling Patterns

### Robust Insert

```python
import pymongo.errors

def safe_insert(collection, document):
    """Insert with comprehensive error handling."""
    try:
        result = collection.insert_one(document)
        logger.info(f"Inserted: {result.inserted_id}")
        return result.inserted_id

    except pymongo.errors.DuplicateKeyError:
        logger.warning("Duplicate key, document already exists")
        return None

    except pymongo.errors.WriteError as e:
        logger.error(f"Write error: {e}")
        return None

    except pymongo.errors.ConnectionFailure:
        logger.error("Connection failed, will retry")
        raise  # Re-raise for retry logic

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return None
```

### Robust Update with Retry

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def update_with_retry(collection, query, update):
    """Update with automatic retry on connection failures."""
    return collection.update_one(query, update)
```

### Transaction-Safe Operations (MongoDB 4.0+)

```python
def transfer_signal(client, from_collection, to_collection, signal_id):
    """Move signal between collections atomically."""
    with client.start_session() as session:
        with session.start_transaction():
            # Read signal
            signal = from_collection.find_one(
                {"_id": signal_id},
                session=session
            )

            if signal:
                # Insert into destination
                to_collection.insert_one(signal, session=session)

                # Delete from source
                from_collection.delete_one(
                    {"_id": signal_id},
                    session=session
                )
```
