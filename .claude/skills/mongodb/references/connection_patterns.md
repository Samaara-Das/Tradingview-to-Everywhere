# MongoDB Connection Patterns

Complete guide to MongoDB connection setup, security, and troubleshooting for the TTE project.

## Contents

- Connection methods and configuration
- Environment variable setup
- Security best practices
- Connection pooling
- Error handling and retry logic
- Troubleshooting common issues

## Connection Methods

### Method 1: Full Connection URI (Recommended)

Use `MONGODB_URI` environment variable with complete connection string:

```python
import os
from pymongo import MongoClient

mongo_uri = os.getenv("MONGODB_URI")
# Example: "mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(mongo_uri)
```

**Advantages:**
- No hardcoded values
- Easy to change clusters/users
- Works across environments
- More secure

### Method 2: Component-Based (Current Implementation)

Build URI from separate components:

```python
import os
from pymongo import MongoClient

# Get components from environment
username = os.getenv("MONGODB_USER", "sammy")  # Fallback for compatibility
password = os.getenv("MONGODB_PWD")
cluster = os.getenv("MONGODB_CLUSTER", "cluster1.565lfln.mongodb.net")
database = os.getenv("MONGODB_DATABASE", "tte")

# Build connection string
mongo_uri = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"
client = MongoClient(mongo_uri)
db = client[database]
```

**Current issue in `local_db.py` (line 42):**
```python
# ❌ Hardcoded username and cluster
mongo_uri = f"mongodb+srv://sammy:{pwd}@cluster1.565lfln.mongodb.net/?retryWrites=true&w=majority"

# ✅ Better approach
username = os.getenv("MONGODB_USER", "sammy")
cluster = os.getenv("MONGODB_CLUSTER", "cluster1.565lfln.mongodb.net")
mongo_uri = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"
```

## Environment Variables

### Required Variables

```bash
# Option 1: Full URI (recommended)
MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"

# Option 2: Component-based
MONGODB_USER="username"
MONGODB_PWD="password"
MONGODB_CLUSTER="cluster1.565lfln.mongodb.net"

# Common
MONGODB_DATABASE="tte"  # Defaults to "tte" if not set
```

### .env File Structure

```bash
# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=tte

# Legacy support (not recommended)
# MONGODB_PWD=password
```

## Security Best Practices

### 1. Never Hardcode Credentials

**❌ Bad:**
```python
client = MongoClient("mongodb+srv://sammy:password123@cluster.mongodb.net/")
```

**✅ Good:**
```python
uri = os.getenv("MONGODB_URI")
if not uri:
    raise ValueError("MONGODB_URI environment variable not set")
client = MongoClient(uri)
```

### 2. Validate Environment Variables

```python
import os
import sys

def validate_env_vars():
    """Validate required environment variables exist."""
    required = ["MONGODB_URI"]
    missing = [var for var in required if not os.getenv(var)]

    if missing:
        print(f"Error: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

validate_env_vars()
```

### 3. Use Read-Only Access Where Possible

For analytics or reporting scripts:

```python
# Connection string with read-only user
uri = "mongodb+srv://readonly_user:password@cluster.mongodb.net/?readPreference=secondary"
```

### 4. Enable SSL/TLS

Ensure connection string includes `ssl=true` or uses `mongodb+srv://` protocol (SSL enabled by default):

```python
# SSL is enabled by default with srv protocol
mongo_uri = "mongodb+srv://user:pass@cluster.mongodb.net/"

# Explicit SSL for non-srv connections
mongo_uri = "mongodb://user:pass@host:27017/?ssl=true"
```

### 5. Set Connection Timeout

```python
client = MongoClient(
    mongo_uri,
    serverSelectionTimeoutMS=5000,  # 5 second timeout
    connectTimeoutMS=10000,          # 10 second connection timeout
    socketTimeoutMS=30000            # 30 second socket timeout
)
```

## Connection Pooling

### Basic Pool Configuration

```python
from pymongo import MongoClient

client = MongoClient(
    mongo_uri,
    maxPoolSize=50,        # Maximum connections in pool
    minPoolSize=10,        # Minimum connections to maintain
    maxIdleTimeMS=45000,   # Close idle connections after 45s
    waitQueueTimeoutMS=5000  # Max wait time for connection from pool
)
```

### Singleton Pattern for Connection Management

```python
# database/connection_manager.py
from pymongo import MongoClient
import os

class ConnectionManager:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_client(self):
        if self._client is None:
            mongo_uri = os.getenv("MONGODB_URI")
            self._client = MongoClient(
                mongo_uri,
                maxPoolSize=50,
                minPoolSize=10
            )
            # Test connection
            self._client.admin.command("ping")
        return self._client

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

# Usage
manager = ConnectionManager()
client = manager.get_client()
db = client["tte"]
```

### Application-Level Connection Sharing

```python
# Initialize once at app startup
from database.connection_manager import ConnectionManager

# In main.py or app.py
connection_manager = ConnectionManager()
client = connection_manager.get_client()

# Share client across modules
db = client["tte"]
collection = db["Point Capitalis signals"]

# Close on shutdown
import atexit
atexit.register(connection_manager.close)
```

## Connection Validation

### Startup Validation

```python
def validate_connection(client):
    """Validate MongoDB connection at startup."""
    try:
        # Ping the server
        client.admin.command("ping")
        print("MongoDB connection successful")
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return False

# Usage
client = MongoClient(mongo_uri)
if not validate_connection(client):
    sys.exit(1)
```

### Health Check Function

```python
def health_check(client):
    """Check if MongoDB connection is healthy."""
    try:
        # Server status
        status = client.admin.command("serverStatus")

        # Check if server is responding
        if status.get("ok") == 1:
            return {
                "status": "healthy",
                "connections": status.get("connections", {}),
                "uptime": status.get("uptimeMillis", 0)
            }
        return {"status": "unhealthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## Error Handling and Retry Logic

### Specific Exception Handling

```python
import pymongo.errors
import logging

logger = logging.getLogger(__name__)

def insert_document(collection, document):
    """Insert document with proper error handling."""
    try:
        result = collection.insert_one(document)
        return result.inserted_id

    except pymongo.errors.ConnectionFailure as e:
        # Network issue - retry may help
        logger.error(f"Connection failure: {e}")
        raise

    except pymongo.errors.OperationFailure as e:
        # Operation issue - retry won't help
        logger.error(f"Operation failure: {e}")
        return None

    except pymongo.errors.DuplicateKeyError as e:
        # Duplicate key - handle accordingly
        logger.warning(f"Duplicate key: {e}")
        return None

    except pymongo.errors.WriteConcernError as e:
        # Write concern issue
        logger.error(f"Write concern error: {e}")
        raise

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise
```

### Retry Logic with Exponential Backoff

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import pymongo.errors

@retry(
    retry=retry_if_exception_type(pymongo.errors.ConnectionFailure),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def insert_with_retry(collection, document):
    """Insert document with retry on connection failures."""
    return collection.insert_one(document)

# Usage
try:
    result = insert_with_retry(collection, {"key": "value"})
    print(f"Inserted: {result.inserted_id}")
except pymongo.errors.ConnectionFailure:
    print("Failed after 3 retries")
```

### Manual Retry Implementation

```python
import time

def insert_with_manual_retry(collection, document, max_retries=3, delay=2):
    """Insert document with manual retry logic."""
    for attempt in range(max_retries):
        try:
            return collection.insert_one(document)
        except pymongo.errors.ConnectionFailure as e:
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed after {max_retries} retries")
                raise
```

## Troubleshooting

### Issue: Connection Timeout

**Symptoms:** `ServerSelectionTimeoutError` after 30 seconds

**Causes:**
- Wrong connection string
- Network firewall blocking MongoDB port
- MongoDB Atlas IP whitelist not configured
- Wrong credentials

**Solutions:**
```python
# 1. Verify connection string format
print(f"URI: {mongo_uri[:50]}...")  # Print safely without password

# 2. Check network connectivity
import socket
try:
    socket.create_connection(("cluster1.565lfln.mongodb.net", 27017), timeout=5)
    print("Network connectivity OK")
except Exception as e:
    print(f"Network issue: {e}")

# 3. Test with shorter timeout
client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
```

### Issue: Authentication Failed

**Symptoms:** `OperationFailure: Authentication failed`

**Causes:**
- Wrong password
- User doesn't exist
- User doesn't have permissions on database

**Solutions:**
```python
# 1. Verify password (don't print actual password)
password = os.getenv("MONGODB_PWD")
if not password:
    print("Password not set in environment")
elif len(password) < 8:
    print("Password seems too short")

# 2. Check user permissions in MongoDB Atlas
# User needs: readWrite role on database

# 3. Test connection with admin database
client = MongoClient(mongo_uri)
try:
    client.admin.command("ping")
    print("Authentication successful")
except Exception as e:
    print(f"Authentication failed: {e}")
```

### Issue: SSL Certificate Verification Failed

**Symptoms:** `CertificateError` or SSL errors

**Solutions:**
```python
# Option 1: Update certificates (recommended)
# pip install --upgrade certifi

# Option 2: Disable SSL verification (not recommended for production)
client = MongoClient(mongo_uri, tlsAllowInvalidCertificates=True)
```

### Issue: Too Many Connections

**Symptoms:** `MongoClient opened before fork` or connection pool exhausted

**Solutions:**
```python
# 1. Use singleton pattern (see Connection Pooling section)

# 2. Configure pool size
client = MongoClient(
    mongo_uri,
    maxPoolSize=50,  # Increase if needed
    minPoolSize=10
)

# 3. Close connections properly
def cleanup():
    client.close()

import atexit
atexit.register(cleanup)
```

## Connection String Options

### Common Options

```
mongodb+srv://user:pass@cluster.mongodb.net/?
    retryWrites=true          # Automatically retry write operations
    &w=majority               # Write concern: majority of nodes
    &readPreference=primary   # Read from primary (default)
    &maxPoolSize=50           # Connection pool size
    &minPoolSize=10           # Minimum pool size
    &maxIdleTimeMS=45000      # Idle connection timeout
    &serverSelectionTimeoutMS=5000  # Server selection timeout
```

### Read Preference Options

```python
# Primary (default) - all reads from primary
uri = "mongodb+srv://.../?readPreference=primary"

# PrimaryPreferred - primary if available, else secondary
uri = "mongodb+srv://.../?readPreference=primaryPreferred"

# Secondary - read from secondary only
uri = "mongodb+srv://.../?readPreference=secondary"

# SecondaryPreferred - secondary if available, else primary
uri = "mongodb+srv://.../?readPreference=secondaryPreferred"

# Nearest - read from lowest latency node
uri = "mongodb+srv://.../?readPreference=nearest"
```

## Testing Connections

### Connection Test Script

```python
# scripts/test_connection.py
import os
from pymongo import MongoClient
import sys

def test_connection():
    """Test MongoDB connection and display info."""
    try:
        # Get URI
        uri = os.getenv("MONGODB_URI")
        if not uri:
            print("❌ MONGODB_URI not set")
            return False

        # Connect
        print("Connecting to MongoDB...")
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)

        # Ping
        client.admin.command("ping")
        print("✅ Connection successful")

        # Get database info
        db_name = os.getenv("MONGODB_DATABASE", "tte")
        db = client[db_name]

        # List collections
        collections = db.list_collection_names()
        print(f"\nDatabase: {db_name}")
        print(f"Collections: {', '.join(collections)}")

        # Get server info
        server_info = client.server_info()
        print(f"\nMongoDB version: {server_info['version']}")

        # Connection pool stats
        pool_stats = client._MongoClient__all_credentials
        print(f"\nConnection pool configured")

        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
```

Run: `python scripts/test_connection.py`
