# API and Webhook Integration

Complete guide to API integrations and webhook patterns for the TTE project.

## Contents

- External webhook integrations (NK Database)
- Stock Buddy REST API reference
- Webhook alert patterns
- Request/response formats
- Error handling
- Rate limiting and retries

## Overview

The TTE project integrates with MongoDB through two primary channels:

1. **Direct MongoDB Access** - PyMongo for local `tte` database
2. **External APIs** - REST APIs and webhooks for external systems

## External Webhook: NK Database

### Implementation

Located in `database/nk_db.py`:

```python
from requests import Session
from requests.adapters import HTTPAdapter
import logging

nk_db_logger = logging.getLogger(__name__)

class Post:
    def __init__(self, max_retries=3):
        self.url = "https://pointcapitalis.com/meta/addTradeViewData"
        self.adapter = HTTPAdapter(max_retries=max_retries)
        self.session = Session()
        self.session.mount(self.url, self.adapter)

    def post_to_url(self, payload: dict):
        """Post trading signal data to external webhook."""
        try:
            response = self.session.post(self.url, data=payload)
            nk_db_logger.info(f"Post request sent successfully! Response: {response}")
            return response
        except ConnectionError as e:
            nk_db_logger.exception("ConnectionError occurred while sending post request")
            return False
```

### Usage

```python
from database.nk_db import Post

# Initialize
poster = Post(max_retries=3)

# Send data
payload = {
    "symbol": "EURUSD",
    "direction": "bullish",
    "timeframe": "H4",
    "entry_price": "1.0950",
    "timestamp": "1705132800"
}

response = poster.post_to_url(payload)

if response:
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
```

### Payload Format

The webhook expects form data (not JSON):

```python
# ✅ Correct: Form data
payload = {
    "symbol": "EURUSD",
    "direction": "bullish",
    "timeframe": "H4"
}
response = session.post(url, data=payload)

# ❌ Incorrect: JSON
response = session.post(url, json=payload)  # Won't work with this endpoint
```

### Error Handling

```python
def safe_webhook_post(poster, payload, max_attempts=3):
    """Post to webhook with retry logic."""
    for attempt in range(max_attempts):
        try:
            response = poster.post_to_url(payload)

            if response and response.status_code == 200:
                logger.info("Webhook post successful")
                return True

            elif response:
                logger.warning(f"Webhook returned {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")

        if attempt < max_attempts - 1:
            time.sleep(2 ** attempt)  # Exponential backoff

    return False
```

## Stock Buddy REST API

### API Client Implementation

Located in `api_client.py`:

```python
import requests
import logging

logger = logging.getLogger(__name__)

class StockBuddyAPIClient:
    def __init__(self, base_url, timeout=30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()

    def _make_request(self, method, endpoint, **kwargs):
        """Internal method for making HTTP requests."""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout: {endpoint}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None

    def health_check(self):
        """Check if API is responsive."""
        data = self._make_request('GET', '/api/health')
        return data.get('status') == 'ok' if data else False

    def get_next_batch(self, size=20):
        """Get next batch of symbols for NWE scanning."""
        data = self._make_request('GET', f'/api/tte/symbols/next-batch?size={size}')
        return data.get('symbols', []) if data else []

    def mark_scanned(self, symbols):
        """Mark symbols as scanned."""
        data = self._make_request('POST', '/api/tte/symbols/mark-scanned', json={'symbols': symbols})
        return data.get('success', False) if data else False

    def get_hot_symbols(self, limit=50, status='pending_tier2'):
        """Get hot symbols pending Tier 2 processing."""
        params = {'limit': limit, 'status': status}
        data = self._make_request('GET', '/api/tte/hot-symbols', params=params)
        return data.get('symbols', []) if data else []

    def delete_expired_hot_symbols(self):
        """Delete expired hot symbols."""
        data = self._make_request('DELETE', '/api/tte/hot-symbols/expired')
        return data.get('deleted_count', 0) if data else 0

    def get_stats(self):
        """Get system statistics."""
        return self._make_request('GET', '/api/tte/stats')
```

### API Endpoints Reference

#### Health Check

**Endpoint:** `GET /api/health`

**Response:**
```json
{
    "status": "ok",
    "timestamp": "2025-01-13T12:00:00Z"
}
```

**Usage:**
```python
client = StockBuddyAPIClient("http://api.example.com")
is_healthy = client.health_check()
```

#### Get Next Batch

**Endpoint:** `GET /api/tte/symbols/next-batch`

**Query Parameters:**
- `size` (int, optional): Number of symbols to retrieve (default: 20)

**Response:**
```json
{
    "symbols": ["EURUSD", "GBPUSD", "USDJPY", ...],
    "batch_number": 2,
    "total_batches": 5
}
```

**Usage:**
```python
symbols = client.get_next_batch(size=20)
for symbol in symbols:
    process_symbol(symbol)
```

#### Mark Symbols as Scanned

**Endpoint:** `POST /api/tte/symbols/mark-scanned`

**Request Body:**
```json
{
    "symbols": ["EURUSD", "GBPUSD", "USDJPY"]
}
```

**Response:**
```json
{
    "success": true,
    "updated_count": 3
}
```

**Usage:**
```python
scanned = ["EURUSD", "GBPUSD"]
success = client.mark_scanned(scanned)
```

#### Get Hot Symbols

**Endpoint:** `GET /api/tte/hot-symbols`

**Query Parameters:**
- `limit` (int, optional): Maximum symbols to return (default: 50)
- `status` (str, optional): Filter by status (default: "pending_tier2")

**Response:**
```json
{
    "symbols": [
        {
            "symbol": "EURUSD",
            "timeframe": "H4",
            "direction": "bullish",
            "tier1_timestamp": "2025-01-13T12:00:00Z",
            "tier1_data": {
                "nwe_zone_price": 1.0950
            }
        },
        ...
    ],
    "count": 15
}
```

**Usage:**
```python
hot_symbols = client.get_hot_symbols(limit=8, status="pending_tier2")
for symbol_data in hot_symbols:
    process_hot_symbol(symbol_data)
```

#### Delete Expired Hot Symbols

**Endpoint:** `DELETE /api/tte/hot-symbols/expired`

**Response:**
```json
{
    "success": true,
    "deleted_count": 12
}
```

**Usage:**
```python
deleted_count = client.delete_expired_hot_symbols()
print(f"Cleaned up {deleted_count} expired symbols")
```

#### Get Statistics

**Endpoint:** `GET /api/tte/stats`

**Response:**
```json
{
    "total_symbols": 100,
    "active_symbols": 85,
    "hot_symbols_pending": 15,
    "signals_today": 8,
    "current_batch": 2,
    "total_batches": 5
}
```

**Usage:**
```python
stats = client.get_stats()
if stats:
    print(f"Active symbols: {stats['active_symbols']}")
    print(f"Pending Tier 2: {stats['hot_symbols_pending']}")
```

## Webhook Alert Integration

### TradingView Webhook Configuration

The tiered orchestrator creates webhook alerts on TradingView that POST to Stock Buddy API.

#### Webhook URLs

```python
# From orchestrator.py
NWE_WEBHOOK_URL = f"{config.api_base_url}/nwe"
OBDIV_WEBHOOK_URL = f"{config.api_base_url}/obdiv"
```

#### Creating Webhook Alerts

```python
# From orchestrator.py (simplified)
def create_nwe_webhook_alert(self):
    """Create webhook alert for NWE screener."""
    success, error_type = self.browser.create_webhook_alert(
        screener_shorttitle="NWE Screener",
        webhook_url=self.nwe_webhook_url
    )
    return success

def create_obdiv_webhook_alert(self):
    """Create webhook alert for OBDIV screener."""
    success, error_type = self.browser.create_webhook_alert(
        screener_shorttitle="OBDIV Screener",
        webhook_url=self.obdiv_webhook_url
    )
    return success
```

### Webhook Payload Format

TradingView sends JSON payload when indicator triggers:

```json
{
    "symbol": "EURUSD",
    "timeframe": "240",
    "direction": "bullish",
    "screener": "NWE",
    "timestamp": 1705132800,
    "indicator_data": {
        "zone_price": 1.0950,
        "current_price": 1.0955
    }
}
```

### Webhook Receiver (Server-Side)

Example Stock Buddy webhook receiver:

```python
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
logger = logging.getLogger(__name__)

@app.route('/nwe', methods=['POST'])
def nwe_webhook():
    """Receive NWE webhook from TradingView."""
    try:
        data = request.get_json()

        # Validate required fields
        required = ['symbol', 'timeframe', 'direction']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400

        # Process signal
        symbol = data['symbol']
        timeframe = data['timeframe']
        direction = data['direction']

        # Add to hot list
        hot_symbol = {
            'symbol': symbol,
            'timeframe': timeframe,
            'direction': direction,
            'tier1_timestamp': datetime.now(),
            'tier1_data': data.get('indicator_data', {}),
            'status': 'pending_tier2',
            'expires_at': datetime.now() + timedelta(hours=4)
        }

        db.tte_hot_list.insert_one(hot_symbol)
        logger.info(f"Added {symbol} to hot list")

        return jsonify({'success': True}), 200

    except Exception as e:
        logger.exception(f"Webhook error: {e}")
        return jsonify({'error': 'Internal error'}), 500

@app.route('/obdiv', methods=['POST'])
def obdiv_webhook():
    """Receive OBDIV webhook from TradingView."""
    try:
        data = request.get_json()

        # Validate required fields
        required = ['symbol', 'timeframe', 'direction']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400

        # Find corresponding hot symbol
        hot_symbol = db.tte_hot_list.find_one({
            'symbol': data['symbol'],
            'status': 'pending_tier2'
        })

        if not hot_symbol:
            logger.warning(f"No hot symbol found for {data['symbol']}")
            return jsonify({'error': 'Symbol not in hot list'}), 404

        # Create confirmed signal
        signal = {
            'symbol': data['symbol'],
            'direction': data['direction'],
            'timeframe': data['timeframe'],
            'tier1_screener': 'NWE',
            'tier2_screener': 'OBDIV',
            'tier1_timestamp': hot_symbol['tier1_timestamp'],
            'tier2_timestamp': datetime.now(),
            'tier1_data': hot_symbol['tier1_data'],
            'tier2_data': data.get('indicator_data', {}),
            'status': 'active',
            'created_at': datetime.now()
        }

        db.tte_signals.insert_one(signal)

        # Update hot symbol status
        db.tte_hot_list.update_one(
            {'_id': hot_symbol['_id']},
            {'$set': {'status': 'completed', 'tier2_timestamp': datetime.now()}}
        )

        logger.info(f"Created confirmed signal for {data['symbol']}")
        return jsonify({'success': True}), 200

    except Exception as e:
        logger.exception(f"Webhook error: {e}")
        return jsonify({'error': 'Internal error'}), 500
```

## Error Handling Patterns

### Retry with Exponential Backoff

```python
import time
from functools import wraps

def retry_api_call(max_attempts=3, base_delay=1):
    """Decorator for retrying API calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.Timeout:
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Timeout, retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        raise
                except requests.exceptions.ConnectionError:
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Connection error, retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator

# Usage
@retry_api_call(max_attempts=3, base_delay=2)
def get_symbols():
    return client.get_next_batch(size=20)
```

### Circuit Breaker Pattern

```python
from datetime import datetime, timedelta

class CircuitBreaker:
    """Prevent cascading failures by stopping requests after threshold."""

    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == 'open':
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = 'half-open'
                logger.info("Circuit breaker: half-open, trying request")
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            if self.state == 'half-open':
                self.state = 'closed'
                self.failures = 0
                logger.info("Circuit breaker: closed")
            return result

        except Exception as e:
            self.failures += 1
            self.last_failure_time = datetime.now()

            if self.failures >= self.failure_threshold:
                self.state = 'open'
                logger.error(f"Circuit breaker: open after {self.failures} failures")

            raise

# Usage
breaker = CircuitBreaker(failure_threshold=5, timeout=60)

def make_api_call():
    return breaker.call(client.get_next_batch, size=20)
```

### Timeout Configuration

```python
# Per-request timeout
response = requests.get(url, timeout=5)

# Connect and read timeouts separately
response = requests.get(url, timeout=(3, 10))  # 3s connect, 10s read

# In API client
class StockBuddyAPIClient:
    def __init__(self, base_url, timeout=30):
        self.timeout = timeout

    def _make_request(self, method, endpoint, **kwargs):
        kwargs.setdefault('timeout', self.timeout)
        return self.session.request(method, url, **kwargs)
```

## Rate Limiting

### Client-Side Rate Limiting

```python
import time
from collections import deque

class RateLimiter:
    """Limit API calls to N per time window."""

    def __init__(self, max_calls, time_window):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()

        # Remove calls outside time window
        while self.calls and self.calls[0] < now - self.time_window:
            self.calls.popleft()

        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_window - (now - self.calls[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached, waiting {sleep_time:.2f}s")
                time.sleep(sleep_time)

        self.calls.append(now)

# Usage
limiter = RateLimiter(max_calls=10, time_window=60)  # 10 calls per minute

for symbol in symbols:
    limiter.wait_if_needed()
    data = client.get_symbol_data(symbol)
```

### Respecting Server Rate Limits

```python
def handle_rate_limit_response(response):
    """Handle 429 Too Many Requests response."""
    if response.status_code == 429:
        retry_after = response.headers.get('Retry-After')

        if retry_after:
            wait_time = int(retry_after)
            logger.warning(f"Rate limited, waiting {wait_time}s")
            time.sleep(wait_time)
            return True

    return False

# Usage
response = session.post(url, data=payload)
if handle_rate_limit_response(response):
    response = session.post(url, data=payload)  # Retry
```

## Best Practices

### 1. Always Use Timeouts

```python
# ✅ Good
response = requests.get(url, timeout=10)

# ❌ Bad - can hang forever
response = requests.get(url)
```

### 2. Validate API Responses

```python
def safe_api_call(client, method_name, *args, **kwargs):
    """Call API method with validation."""
    method = getattr(client, method_name)
    result = method(*args, **kwargs)

    if result is None:
        logger.error(f"API call {method_name} returned None")
        return None

    return result
```

### 3. Log Request/Response Details

```python
def log_request(method, url, **kwargs):
    """Log API request details."""
    logger.debug(f"API Request: {method} {url}")
    if 'json' in kwargs:
        logger.debug(f"Request body: {kwargs['json']}")

def log_response(response):
    """Log API response details."""
    logger.debug(f"API Response: {response.status_code}")
    logger.debug(f"Response body: {response.text[:200]}")  # First 200 chars
```

### 4. Use Session for Connection Reuse

```python
# ✅ Good - reuses connection
session = requests.Session()
for url in urls:
    response = session.get(url)

# ❌ Bad - creates new connection each time
for url in urls:
    response = requests.get(url)
```

### 5. Handle Authentication Securely

```python
# ✅ Good - from environment
api_key = os.getenv("API_KEY")
headers = {"Authorization": f"Bearer {api_key}"}

# ❌ Bad - hardcoded
headers = {"Authorization": "Bearer sk-1234567890"}
```

### 6. Implement Health Checks

```python
def check_api_health(client, max_wait=30):
    """Wait for API to become healthy."""
    start_time = time.time()

    while time.time() - start_time < max_wait:
        if client.health_check():
            logger.info("API is healthy")
            return True

        time.sleep(2)

    logger.error("API health check failed")
    return False

# Usage at startup
if not check_api_health(client):
    sys.exit(1)
```

## Testing API Integrations

### Mock API Responses

```python
from unittest.mock import Mock, patch

def test_get_next_batch():
    """Test API client with mocked response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'symbols': ['EURUSD', 'GBPUSD'],
        'batch_number': 1
    }

    with patch('requests.Session.request', return_value=mock_response):
        client = StockBuddyAPIClient("http://test.com")
        symbols = client.get_next_batch(size=2)

        assert symbols == ['EURUSD', 'GBPUSD']
```

### Integration Test Script

```python
# scripts/test_api.py
def test_api_integration():
    """Test Stock Buddy API integration."""
    client = StockBuddyAPIClient(os.getenv("API_BASE_URL"))

    # Health check
    print("Testing health check...")
    assert client.health_check(), "Health check failed"
    print("✅ Health check passed")

    # Get symbols
    print("Testing get_next_batch...")
    symbols = client.get_next_batch(size=5)
    assert len(symbols) > 0, "No symbols returned"
    print(f"✅ Got {len(symbols)} symbols")

    # Mark as scanned
    print("Testing mark_scanned...")
    success = client.mark_scanned(symbols[:2])
    assert success, "Mark scanned failed"
    print("✅ Marked symbols as scanned")

    print("\n✅ All tests passed")

if __name__ == "__main__":
    test_api_integration()
```
