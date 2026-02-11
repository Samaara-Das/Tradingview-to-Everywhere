> ⚠️ **LEGACY**: This document describes the **Tiered mode** symbol rotation system. Production uses **Combo mode**, which has no symbol rotation — all ~1,054 symbols are monitored simultaneously via 352 persistent alerts (3 symbols per alert). See [Combo Architecture](../../../../docs/combo/ARCHITECTURE.md).

# Symbol Management Reference

Complete reference for Stock Buddy's priority rotation algorithm and symbol lifecycle management.

## Table of Contents

- [Overview](#overview)
- [Symbol Lifecycle](#symbol-lifecycle)
- [Priority System](#priority-system)
- [Rotation Algorithm](#rotation-algorithm)
- [Batch Selection Logic](#batch-selection-logic)
- [Rotation State Tracking](#rotation-state-tracking)
- [Symbol Import](#symbol-import)
- [Performance Optimization](#performance-optimization)

## Overview

Stock Buddy manages 900+ trading symbols using a priority-based rotation system that ensures:
- High-priority symbols are scanned frequently (every batch)
- Medium-priority symbols are scanned regularly (every 3rd rotation)
- Low-priority symbols are scanned periodically (every 10th rotation)
- All symbols are eventually scanned (fair rotation)

**Goal**: Maximize signal quality while minimizing scan time.

## Symbol Lifecycle

### 1. Import

Symbols are imported into the `tte_symbols` collection via the API.

**Import Sources**:
- TTE's `symbol_settings.py` (legacy format)
- Manual API calls
- Bulk CSV import

**Initial State**:
```typescript
{
  symbol: "EURUSD",
  exchange: "FX",
  priority: "A",
  category: "forex",
  active: true,
  last_scanned: null,      // Never scanned
  scan_count: 0,           // No scans yet
  signal_count: 0,         // No signals yet
  created_at: Date,
  updated_at: Date
}
```

### 2. Rotation

Symbols are selected for batches based on:
- **Priority**: A symbols always included, B every 3rd rotation, C every 10th
- **Last scanned**: Least-recently-scanned symbols fill remaining slots
- **Active status**: Only active symbols are included

### 3. Scanning

After batch is processed:
- `last_scanned` timestamp updated
- `scan_count` incremented
- Rotation state updated (batch number, symbols scanned)

### 4. Signal Generation

When OBDIV webhook creates a signal:
- `signal_count` incremented for the symbol
- Signal stored in `tte_signals` collection
- Symbol remains in rotation for future scans

### 5. Lifecycle Loop

Symbols continue in rotation indefinitely:
- Active symbols are scanned repeatedly
- Inactive symbols are excluded from batches
- Priority can be adjusted based on performance

## Priority System

### Priority Levels

| Priority | Description | Examples | Scan Frequency | Count |
|----------|-------------|----------|----------------|-------|
| **A** | Major pairs, high-volume symbols | EURUSD, GBPUSD, BTCUSD | Every batch | ~28 |
| **B** | Secondary symbols, regional pairs | AUDNZD, EURJPY, TSLA | Every 3rd rotation | ~150 |
| **C** | Exotic pairs, low-volume stocks | ZARJPY, EURTRY, penny stocks | Every 10th rotation | ~763 |

### Frequency Formula

```
A symbols: included if TRUE (always)
B symbols: included if rotation_number % 3 == 0
C symbols: included if rotation_number % 10 == 0
```

**Examples**:

| Rotation | A Included | B Included | C Included |
|----------|------------|------------|------------|
| 1 | ✓ | ✗ | ✗ |
| 2 | ✓ | ✗ | ✗ |
| 3 | ✓ | ✓ | ✗ |
| 6 | ✓ | ✓ | ✗ |
| 9 | ✓ | ✓ | ✗ |
| 10 | ✓ | ✗ | ✓ |
| 30 | ✓ | ✓ | ✓ |

### Priority Assignment Strategy

**A Priority** (28 symbols):
- Major forex pairs (EUR, GBP, USD, JPY)
- Top cryptocurrencies (BTC, ETH)
- High-volume indices (SPX, DJI)

**B Priority** (150 symbols):
- Secondary forex pairs
- Major stocks (AAPL, GOOGL, TSLA)
- Commodities (GOLD, OIL)

**C Priority** (763 symbols):
- Exotic forex pairs
- Small-cap stocks
- Regional markets

## Rotation Algorithm

### High-Level Logic

```typescript
function getNextBatch(batchSize: number, rotationNumber: number): Symbol[] {
  const batch = [];

  // Step 1: Always include A-priority symbols
  const aSymbols = await getSymbolsByPriority("A");
  batch.push(...aSymbols);

  // Step 2: Include B symbols every 3rd rotation
  if (rotationNumber % 3 === 0) {
    const bSymbols = await getSymbolsByPriority("B");
    batch.push(...bSymbols);
  }

  // Step 3: Include C symbols every 10th rotation
  if (rotationNumber % 10 === 0) {
    const cSymbols = await getSymbolsByPriority("C");
    batch.push(...cSymbols);
  }

  // Step 4: Fill remaining slots with least-recently-scanned
  const remaining = batchSize - batch.length;
  if (remaining > 0) {
    const lrsSymbols = await getLeastRecentlyScanned(remaining);
    batch.push(...lrsSymbols);
  }

  // Step 5: Return first batchSize symbols
  return batch.slice(0, batchSize);
}
```

### Detailed Steps

**Step 1: Fetch A-Priority Symbols**

```typescript
const aSymbols = await collection
  .find({ active: true, priority: "A" })
  .sort({ last_scanned: 1 })  // Oldest first
  .toArray();
```

**Result**: ~28 symbols

**Step 2: Conditionally Fetch B-Priority Symbols**

```typescript
if (rotationNumber % 3 === 0) {
  const bSymbols = await collection
    .find({ active: true, priority: "B" })
    .sort({ last_scanned: 1 })
    .toArray();
  batch.push(...bSymbols);
}
```

**Result**: 0 or ~150 symbols (depending on rotation)

**Step 3: Conditionally Fetch C-Priority Symbols**

```typescript
if (rotationNumber % 10 === 0) {
  const cSymbols = await collection
    .find({ active: true, priority: "C" })
    .sort({ last_scanned: 1 })
    .toArray();
  batch.push(...cSymbols);
}
```

**Result**: 0 or ~763 symbols (depending on rotation)

**Step 4: Fill Remaining Slots**

```typescript
const remaining = batchSize - batch.length;
if (remaining > 0) {
  const lrsSymbols = await collection
    .find({ active: true })
    .sort({ last_scanned: 1 })  // Least recently scanned
    .limit(remaining)
    .toArray();
  batch.push(...lrsSymbols);
}
```

**Result**: Fills up to `batchSize` (default 20)

**Step 5: Truncate to Batch Size**

```typescript
return batch.slice(0, batchSize);
```

**Result**: Exactly `batchSize` symbols (or fewer if not enough symbols)

## Batch Selection Logic

### Typical Batches

**Rotation 1** (A only + LRS):
```
Batch size: 20
- 28 A symbols (truncated to 20)
Result: First 20 A symbols (sorted by last_scanned)
```

**Rotation 3** (A + B + LRS):
```
Batch size: 20
- 28 A symbols (all included, but capped at 20)
Result: First 20 A symbols
```

**Note**: In most rotations, A symbols alone exceed batch size, so B/C symbols are rarely included directly. They get scanned via the "least recently scanned" fill logic.

### Least-Recently-Scanned (LRS) Fill

The LRS fill ensures all symbols eventually get scanned, even if not in their priority rotation window.

**Query**:
```typescript
const lrsSymbols = await collection
  .find({ active: true })
  .sort({ last_scanned: 1 })  // null values first (never scanned)
  .limit(remaining)
  .toArray();
```

**Sort Order**:
1. Symbols with `last_scanned: null` (never scanned)
2. Symbols with oldest `last_scanned` timestamp

This ensures:
- New symbols are scanned first
- Stale symbols are re-scanned
- No symbol is forgotten

## Rotation State Tracking

### Rotation State Document

**Collection**: `tte_rotation_state` (singleton, `_id: "current"`)

```typescript
{
  _id: "current",
  batch_number: 47,              // Total batches processed
  rotation_number: 1,             // Complete rotation cycles
  symbols_scanned_this_rotation: 120,
  total_symbols: 941,
  last_batch_at: Date("2024-01-15T10:30:00Z"),
  last_batch_symbols: ["EURUSD", "GBPUSD", "USDJPY"],
  started_at: Date("2024-01-01T00:00:00Z"),
  updated_at: Date("2024-01-15T10:30:00Z")
}
```

### Update After Each Batch

```typescript
async function markSymbolsScanned(symbols: string[]) {
  const state = await getRotationState();
  const scannedCount = state.symbols_scanned_this_rotation + symbols.length;

  // Check if rotation complete
  const rotationComplete = scannedCount >= state.total_symbols;

  await updateRotationState({
    batch_number: state.batch_number + 1,
    rotation_number: rotationComplete ? state.rotation_number + 1 : state.rotation_number,
    symbols_scanned_this_rotation: rotationComplete ? 0 : scannedCount,
    last_batch_at: new Date(),
    last_batch_symbols: symbols,
    updated_at: new Date()
  });

  // Update symbols' last_scanned timestamps
  await collection.updateMany(
    { symbol: { $in: symbols } },
    { $set: { last_scanned: new Date() }, $inc: { scan_count: 1 } }
  );
}
```

### Rotation Completion

When `symbols_scanned_this_rotation >= total_symbols`:
1. Increment `rotation_number`
2. Reset `symbols_scanned_this_rotation` to 0
3. All symbols' `last_scanned` timestamps remain (for LRS sorting)

**Example**:
```
Rotation 1 complete after 47 batches (941 symbols / 20 per batch)
- rotation_number: 1 → 2
- symbols_scanned_this_rotation: 941 → 0
- batch_number: 47 → 48 (continues incrementing)
```

## Symbol Import

### Import Endpoint

**Endpoint**: `POST /api/tte/symbols/import`

**Request**:
```json
{
  "symbols": [
    {
      "symbol": "EURUSD",
      "exchange": "FX",
      "priority": "A",
      "category": "forex"
    }
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

### Import Behavior

**clearExisting: false** (default):
- Inserts new symbols
- Updates existing symbols (upsert)
- Preserves `last_scanned` and `scan_count` for existing symbols

**clearExisting: true**:
- Deletes all existing symbols
- Inserts new symbols
- Resets all tracking data

### Bulk Import from TTE

TTE's `symbol_settings.py` contains symbol definitions:

```python
SYMBOL_CATEGORIES = {
    "forex_majors": {
        "symbols": ["EURUSD", "GBPUSD", "USDJPY"],
        "priority": "A",
        "exchange": "FX"
    },
    "crypto": {
        "symbols": ["BTCUSD", "ETHUSD"],
        "priority": "A",
        "exchange": "CRYPTO"
    }
}
```

**Import Script**:
```python
import requests
from resources.symbol_settings import SYMBOL_CATEGORIES

symbols = []
for category, config in SYMBOL_CATEGORIES.items():
    for symbol in config["symbols"]:
        symbols.append({
            "symbol": symbol,
            "exchange": config["exchange"],
            "priority": config["priority"],
            "category": category
        })

response = requests.post(
    "https://stock-buddy-app.vercel.app/api/tte/symbols/import",
    json={"symbols": symbols, "clearExisting": False}
)
```

## Performance Optimization

### Database Indexes

**Recommended Indexes**:
```typescript
// Compound index for batch selection
{ active: 1, priority: 1, last_scanned: 1 }

// Index for symbol lookup
{ symbol: 1 }  // Unique

// Index for priority filtering
{ priority: 1 }
```

### Query Optimization

**Before Optimization**:
```typescript
// Fetches all A symbols, then sorts in application
const aSymbols = await collection.find({ priority: "A" }).toArray();
aSymbols.sort((a, b) => a.last_scanned - b.last_scanned);
```

**After Optimization**:
```typescript
// Database sorts and limits results
const aSymbols = await collection
  .find({ active: true, priority: "A" })
  .sort({ last_scanned: 1 })
  .toArray();
```

### Caching Strategy

**Current**: No caching (fresh data on each request)

**Future Enhancement**: Cache rotation state for 1 minute
```typescript
const cachedState = cache.get("rotation_state");
if (!cachedState || cache.isExpired("rotation_state")) {
  const state = await getRotationState();
  cache.set("rotation_state", state, { ttl: 60 });
}
```

### Batch Size Tuning

**Current**: 20 symbols (max for NWE screener inputs)

**Trade-offs**:
- **Larger batches**: Fewer API calls, longer processing time per batch
- **Smaller batches**: More API calls, faster individual batches

**Optimal**: 20 symbols (hardware limit of NWE screener)

---

**Related**:
- [API Endpoints](api_endpoints.md) - Endpoints for symbol management
- [Database Schema](database_schema.md) - Symbol document structure
- [Integration Flow](integration_flow.md) - How batches are processed
