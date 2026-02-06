---
name: mongodb
description: MongoDB operations for TradingView to Everywhere (TTE) project. Use when working with MongoDB connections, CRUD operations, data schemas, webhooks, API integrations, or database queries. Applies to both direct PyMongo access (legacy mode) and Stock Buddy REST API (tiered mode).
---

# MongoDB for TTE

## Overview

This skill provides MongoDB expertise for the TradingView to Everywhere project, covering connection management, data schemas, CRUD operations, API integrations, and security best practices. The project uses two database systems: direct MongoDB access via PyMongo (legacy mode) and Stock Buddy REST API (tiered mode).

## When to Use This Skill

Use this skill when:
- Setting up or troubleshooting MongoDB connections
- Working with trading signal data schemas
- Implementing CRUD operations for signals, symbols, or hot lists
- Integrating webhooks or APIs with MongoDB
- Debugging database-related issues
- Optimizing queries or bulk operations
- Implementing security best practices
- Managing connection pooling or retry logic

## Workflow Decision Tree

**Are you setting up a new connection?**
→ See [Connection Patterns](references/connection_patterns.md) for secure connection setup

**Are you working with data models or schemas?**
→ See [Schema Reference](references/schema_reference.md) for complete schema documentation

**Are you implementing queries or CRUD operations?**
→ See [Query Patterns](references/query_patterns.md) for common patterns and best practices

**Are you integrating webhooks or APIs?**
→ See [API Integration](references/api_integration.md) for webhook and API patterns

## Quick Start

### Direct MongoDB Connection (Legacy Mode)

```python
from database.local_db import Database

# Initialize with environment variables
db = Database()

# Add a trading signal
db.add_doc({
    "direction": "bullish",
    "symbol": "EURUSD",
    "timeframe": "H4",
    "screener": "NWE",
    "timestamp": 1234567890,
    "category": "currencies",
    "tvEntrySnapshot": "https://...",
    "pngEntrySnapshot": "https://..."
})

# Get latest signal
latest = db.get_latest_doc()
```

### Stock Buddy API (Tiered Mode)

```python
from api_client import StockBuddyAPIClient

# Initialize with base URL
client = StockBuddyAPIClient("http://api.example.com", timeout=30)

# Health check
if client.health_check():
    # Get next batch of symbols
    symbols = client.get_next_batch(size=20)

    # Mark symbols as scanned
    client.mark_scanned(["EURUSD", "GBPUSD"])

    # Get hot symbols for Tier 2
    hot_symbols = client.get_hot_symbols(limit=50, status="pending_tier2")
```

## Core Operations

### Connection Management

**Environment variables required:**
- `MONGODB_URI` - Full connection string (preferred)
- `MONGODB_PWD` - Password only (uses default cluster)
- `MONGODB_DATABASE` - Database name (defaults to "tte")

**Security considerations:**
- Never hardcode credentials in code
- Use environment variables for all sensitive data
- Validate connection at startup with `client.admin.command("ping")`
- Implement connection pooling for production
- Use retry logic for transient failures

See [Connection Patterns](references/connection_patterns.md) for detailed setup.

### Data Models

**Two database systems:**

1. **TTE Local Database** (`tte`) - Direct PyMongo access
   - Collection: "Point Capitalis signals"
   - Used by: Legacy mode trading signals
   - Access: `database/local_db.py`

2. **Stock Buddy Database** - REST API access
   - Collections: `tte_symbols`, `tte_hot_list`, `tte_signals`, `tte_rotation_state`
   - Used by: Tiered system signals
   - Access: `api_client.py`

See [Schema Reference](references/schema_reference.md) for complete schemas.

### CRUD Operations

**Create:**
```python
db.add_doc(document)  # Returns bool
```

**Read:**
```python
db.get_latest_doc()  # Returns most recent by unixTime
```

**Update:**
```python
# Bulk update example
collection.bulk_write([
    UpdateOne({"_id": doc_id}, {"$set": {"field": value}})
])
```

**Delete:**
```python
db.delete_all()           # Delete all documents
db.delete_some(count)     # Keep latest N, delete rest
```

See [Query Patterns](references/query_patterns.md) for advanced operations.

### API Integration

**External webhook (NK Database):**
```python
from database.nk_db import Post

poster = Post()
response = poster.post_to_url(payload_dict)
```

**Stock Buddy API endpoints:**
- `GET /api/health` - Health check
- `GET /api/tte/symbols/next-batch?size=20` - Get symbols
- `POST /api/tte/symbols/mark-scanned` - Mark as scanned
- `GET /api/tte/hot-symbols?limit=50&status=pending_tier2` - Get hot list
- `DELETE /api/tte/hot-symbols/expired` - Cleanup

See [API Integration](references/api_integration.md) for complete reference.

## Common Patterns

### Error Handling

**Specific exception handling (preferred):**
```python
import pymongo.errors

try:
    collection.insert_one(doc)
except pymongo.errors.ConnectionFailure:
    logger.error("MongoDB connection failed (transient)")
    # Retry logic
except pymongo.errors.OperationFailure:
    logger.error("MongoDB operation failed (permanent)")
    # Handle differently
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
```

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def insert_with_retry(collection, document):
    return collection.insert_one(document)
```

### Bulk Operations

```python
# Process in chunks to avoid memory issues
CHUNK_SIZE = 1000

def bulk_update_in_chunks(collection, operations):
    for i in range(0, len(operations), CHUNK_SIZE):
        chunk = operations[i:i + CHUNK_SIZE]
        collection.bulk_write(chunk)
```

## Known Issues and Solutions

### Issue: Hardcoded connection details
**Problem:** Username and cluster hardcoded in `local_db.py`
**Solution:** Use full `MONGODB_URI` environment variable instead

### Issue: No connection pooling
**Problem:** New client created per Database instance
**Solution:** Use singleton pattern or app-level client management

### Issue: Broad exception handling
**Problem:** `except Exception` catches all errors, hard to debug
**Solution:** Use specific PyMongo exceptions (see Error Handling above)

### Issue: No TTL indexes
**Problem:** Manual cleanup required, storage limits not enforced
**Solution:** Add TTL index in initialization:
```python
collection.create_index("timestamp", expireAfterSeconds=2592000)  # 30 days
```

### Issue: Inconsistent timezone handling
**Problem:** Hardcoded Asia/Kolkata timezone
**Solution:** Use UTC consistently or make timezone configurable

## Best Practices

1. **Always validate connections at startup** - Use `ping` command to verify
2. **Use specific exception types** - PyMongo has detailed exception hierarchy
3. **Implement retry logic** - Handle transient network failures gracefully
4. **Chunk bulk operations** - Process in batches to avoid memory issues
5. **Use UTC timestamps** - Store all times in UTC, convert for display only
6. **Create indexes for queries** - Add indexes for frequently queried fields
7. **Monitor storage usage** - M0 tier has 512MB limit
8. **Log all operations** - Use structured logging for debugging
9. **Validate before bulk updates** - Check documents exist before updating
10. **Use connection pooling** - Configure maxPoolSize and minPoolSize

## References

- [Connection Patterns](references/connection_patterns.md) - Connection setup and security
- [Schema Reference](references/schema_reference.md) - Complete data schemas
- [Query Patterns](references/query_patterns.md) - Common query patterns
- [API Integration](references/api_integration.md) - Webhook and API integration

## File Locations

- **Local DB module:** `database/local_db.py`
- **NK DB webhook:** `database/nk_db.py`
- **API client:** `api_client.py`
- **Configuration:** `env.py`, `config.py`
- **Documentation:** `docs/DATABASE.md`
