# Database Schema Reference

Complete reference for Stock Buddy MongoDB collections and document structures.

## Table of Contents

- [Overview](#overview)
- [Collections Summary](#collections-summary)
- [tte_symbols Collection](#tte_symbols-collection)
- [tte_hot_list Collection](#tte_hot_list-collection)
- [tte_signals Collection](#tte_signals-collection)
- [tte_rotation_state Collection](#tte_rotation_state-collection)
- [Indexes](#indexes)
- [Collection Helpers](#collection-helpers)
- [Data Lifecycle](#data-lifecycle)

## Overview

Stock Buddy uses MongoDB to store symbol metadata, rotation state, hot symbols, and confirmed trading signals.

**Database Name**: `stock_buddy_db` (or configured name)

**Connection**: Managed via Next.js MongoDB client in `src/lib/mongodb.ts`

**Collections**: 4 core collections

## Collections Summary

| Collection | Purpose | Document Count | Key Fields |
|------------|---------|----------------|------------|
| `tte_symbols` | Symbol metadata and scan tracking | ~941 | `symbol`, `priority`, `last_scanned` |
| `tte_hot_list` | Temporary queue for NWE-triggered symbols | 0-50 | `symbol`, `direction`, `expires_at` |
| `tte_signals` | Confirmed trading signals (levels 1/2/3) | Growing | `symbol`, `level`, `direction` |
| `tte_rotation_state` | Single document tracking rotation progress | 1 | `batch_number`, `rotation_number` |

## tte_symbols Collection

Stores metadata for all symbols in the rotation system.

### Document Structure

```typescript
{
  _id: ObjectId("..."),
  symbol: "EURUSD",
  exchange: "FX",
  priority: "A",
  category: "forex",
  notes: "",
  active: true,
  last_scanned: Date("2024-01-15T10:30:00Z"),
  scan_count: 15,
  signal_count: 3,
  created_at: Date("2024-01-01T00:00:00Z"),
  updated_at: Date("2024-01-15T10:30:00Z")
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `_id` | ObjectId | Auto | MongoDB document ID |
| `symbol` | string | Yes | Symbol name (uppercase, e.g., "EURUSD") |
| `exchange` | string | Yes | Exchange type: `"FX"`, `"CRYPTO"`, `"STOCKS"`, `"INDICES"`, `"COMMODITIES"` |
| `priority` | string | Yes | Scan priority: `"A"`, `"B"`, or `"C"` |
| `category` | string | No | Category/group name (e.g., "forex", "us_stocks") |
| `notes` | string | No | Optional notes or comments |
| `active` | boolean | Yes | Whether symbol is active for scanning (default: `true`) |
| `last_scanned` | Date | Nullable | Timestamp of last NWE scan (null if never scanned) |
| `scan_count` | number | Yes | Total number of times scanned (default: 0) |
| `signal_count` | number | Yes | Total confirmed signals generated (default: 0) |
| `created_at` | Date | Yes | Document creation timestamp |
| `updated_at` | Date | Yes | Last modification timestamp |

### Priority System

| Priority | Description | Scan Frequency | Typical Count |
|----------|-------------|----------------|---------------|
| **A** | Major pairs/high-volume symbols | Every batch | ~28 |
| **B** | Secondary symbols | Every 3rd rotation | ~150 |
| **C** | Exotic/low-volume symbols | Every 10th rotation | ~763 |

### Collection Helpers

**File**: `src/lib/tte/collections.ts`

```typescript
// Get active symbol count
const total = await getActiveSymbolCount();

// Get next batch (priority rotation + least-recently-scanned)
const batch = await getNextBatch(20, rotationNumber);

// Increment signal count for a symbol
await incrementSignalCount("EURUSD");
```

## tte_hot_list Collection

Temporary queue for symbols that triggered NWE zones (Tier 1) and are awaiting OBDIV processing (Tier 2).

### Document Structure

```typescript
{
  _id: ObjectId("..."),
  symbol: "GBPAUD",
  direction: "bullish",
  nwe_timeframe: "5m",
  nwe_timestamp: 1705312800,
  status: "pending_tier2",
  created_at: Date("2024-01-15T10:30:00Z"),
  expires_at: Date("2024-01-15T10:35:00Z")
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `_id` | ObjectId | Auto | MongoDB document ID |
| `symbol` | string | Yes | Symbol name (uppercase) |
| `direction` | string | Yes | Signal direction: `"bullish"` or `"bearish"` |
| `nwe_timeframe` | string | Yes | Single timeframe (e.g., `"5m"`, `"15m"`, `"1H"`) |
| `nwe_timestamp` | number | Yes | Unix timestamp when NWE zone was detected |
| `status` | string | Yes | Processing status (see below) |
| `created_at` | Date | Yes | Document creation timestamp |
| `expires_at` | Date | Yes | Expiration timestamp (no refresh) |

**Note**: Each symbol+timeframe combination creates a separate document. A symbol can have multiple hot list entries for different timeframes.

### Status Values

| Status | Description |
|--------|-------------|
| `pending_tier2` | Awaiting OBDIV processing |
| `tier2_complete` | OBDIV processing complete (signal created) |
| `expired` | Expiration timestamp passed (not actively used, documents are deleted) |

### Expiration Logic

Expiration is calculated as: `nwe_timestamp + timeframe_duration`

**Timeframe Durations**:
```typescript
const TIMEFRAME_SECONDS = {
  "5m": 300,      // 5 minutes
  "15m": 900,     // 15 minutes
  "1H": 3600,     // 1 hour
  "H4": 14400,    // 4 hours
  "D1": 86400     // 24 hours
};
```

**No Refresh**: Once created, expiration is never extended. If a document exists for symbol+direction+timeframe, new NWE triggers are skipped.

### Collection Helpers

**File**: `src/lib/tte/collections.ts`

```typescript
// Get hot list collection
const collection = await getHotListCollection();

// Get hot list entry (for validation in OBDIV webhook)
const entry = await getHotListEntry("EURUSD", "bullish");

// Mark hot list entry as complete
await markHotListComplete("EURUSD", "bullish");
```

## tte_signals Collection

Stores confirmed trading signals with technical analysis details.

### Document Structure

```typescript
{
  _id: ObjectId("..."),
  symbol: "EURUSD",
  direction: "bullish",
  level: 3,
  nwe_tf: ["5m", "15m"],
  nwe_timestamp: 1705312800,
  ob_tf: "5m",
  ob_type: "OB",
  ob_high: 1.1050,
  ob_low: 1.1000,
  div_tf: "15m",
  div_type: "Logic2",
  screenshot_url: null,
  status: "pending_screenshot",
  timestamp: 1705316400,
  created_at: Date("2024-01-15T11:30:00Z"),
  updated_at: Date("2024-01-15T11:30:00Z")
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `_id` | ObjectId | Auto | MongoDB document ID |
| `symbol` | string | Yes | Symbol name (uppercase) |
| `direction` | string | Yes | Signal direction: `"bullish"` or `"bearish"` |
| `level` | number | Yes | Signal level: `1`, `2`, or `3` |
| `nwe_tf` | array | Yes | NWE timeframes (from hot list entry) |
| `nwe_timestamp` | number | Yes | Unix timestamp when NWE zone was detected |
| `ob_tf` | string | Nullable | Order block timeframe (null if not found) |
| `ob_type` | string | Nullable | Order block type: `"OB"`, `"FVG"`, or `"Breaker"` |
| `ob_high` | number | Nullable | Order block high price |
| `ob_low` | number | Nullable | Order block low price |
| `div_tf` | string | Nullable | Divergence timeframe (null if not found) |
| `div_type` | string | Nullable | Divergence type: `"Logic2"`, `"Internal"`, or `"Logic1"` |
| `screenshot_url` | string | Nullable | TradingView chart screenshot URL |
| `status` | string | Yes | Processing status: `"pending_screenshot"` or `"complete"` |
| `timestamp` | number | Yes | Unix timestamp when signal was created |
| `created_at` | Date | Yes | Document creation timestamp |
| `updated_at` | Date | Yes | Last modification timestamp |

### Signal Levels

Signal level is automatically calculated based on confirmations:

```typescript
function calculateSignalLevel(hasOB: boolean, hasDiv: boolean): 1 | 2 | 3 {
  if (hasOB && hasDiv) return 3;  // High confidence
  if (hasOB || hasDiv) return 2;  // Medium confidence
  return 1;                        // Low confidence (NWE only)
}
```

| Level | Criteria | Confidence | Color |
|-------|----------|------------|-------|
| **1** | NWE zone only | Low | Yellow |
| **2** | NWE + (OB OR DIV) | Medium | Orange |
| **3** | NWE + OB + DIV | High | Green |

### Collection Helpers

**File**: `src/lib/tte/collections.ts`

```typescript
// Create a new signal
const result = await createSignal({
  symbol: "EURUSD",
  direction: "bullish",
  level: 3,
  nwe_tf: ["5m"],
  nwe_timestamp: 1705312800,
  ob_tf: "5m",
  ob_type: "OB",
  ob_high: 1.1050,
  ob_low: 1.1000,
  div_tf: "15m",
  div_type: "Logic2",
  screenshot_url: null,
  status: "pending_screenshot",
  timestamp: 1705316400,
  created_at: new Date(),
  updated_at: new Date()
});
```

## tte_rotation_state Collection

Single document that tracks rotation progress and batch metadata.

**Document ID**: Always `"current"` (singleton pattern)

### Document Structure

```typescript
{
  _id: "current",
  batch_number: 6,
  rotation_number: 1,
  symbols_scanned_this_rotation: 120,
  total_symbols: 941,
  last_batch_at: Date("2024-01-15T10:30:00Z"),
  last_batch_symbols: ["EURUSD", "GBPUSD", "USDJPY"],
  started_at: Date("2024-01-01T00:00:00Z"),
  updated_at: Date("2024-01-15T10:30:00Z")
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `_id` | string | Fixed | Always `"current"` (singleton) |
| `batch_number` | number | Yes | Total batches processed (increments on each batch) |
| `rotation_number` | number | Yes | Complete rotation cycles (resets when all symbols scanned) |
| `symbols_scanned_this_rotation` | number | Yes | Symbols scanned in current rotation |
| `total_symbols` | number | Yes | Total active symbols in database |
| `last_batch_at` | Date | Nullable | Timestamp of last batch fetch (null if no batches yet) |
| `last_batch_symbols` | array | Yes | Symbols from last batch (empty array if no batches yet) |
| `started_at` | Date | Yes | Timestamp when rotation state was initialized |
| `updated_at` | Date | Yes | Last modification timestamp |

### Rotation Logic

**Batch Increment**: Incremented on every `get_next_symbol_batch()` call

**Rotation Completion**: When `symbols_scanned_this_rotation >= total_symbols`:
- `rotation_number` increments
- `symbols_scanned_this_rotation` resets to 0
- All symbols' `last_scanned` timestamps reset to allow re-scanning

### Collection Helpers

**File**: `src/lib/tte/collections.ts`

```typescript
// Get current rotation state
const state = await getRotationState();

// Update rotation state after batch fetch
await updateRotationState({
  batch_number: state.batch_number + 1,
  symbols_scanned_this_rotation: state.symbols_scanned_this_rotation + 20,
  last_batch_at: new Date(),
  last_batch_symbols: ["EURUSD", "GBPUSD"]
});
```

## Indexes

Recommended indexes for optimal query performance:

### tte_symbols

```typescript
// Unique index on symbol
{ symbol: 1 }  // Unique

// Compound index for batch selection
{ active: 1, priority: 1, last_scanned: 1 }

// Index for priority filtering
{ priority: 1 }
```

### tte_hot_list

```typescript
// Compound index for hot symbol queries
{ status: 1, expires_at: 1, created_at: 1 }

// Compound index for hot list entry lookup
{ symbol: 1, direction: 1, nwe_timeframe: 1, status: 1 }
```

### tte_signals

```typescript
// Compound index for signal queries
{ level: 1, direction: 1, created_at: -1 }

// Index for symbol filtering
{ symbol: 1, created_at: -1 }

// Index for timestamp range queries
{ timestamp: 1 }
```

### tte_rotation_state

No indexes needed (single document with fixed ID)

## Collection Helpers

All collection helper functions are in `src/lib/tte/collections.ts`:

### Symbol Management

```typescript
getActiveSymbolCount(): Promise<number>
getNextBatch(size: number, rotationNumber: number): Promise<Symbol[]>
incrementSignalCount(symbol: string): Promise<void>
```

### Hot List Management

```typescript
getHotListCollection(): Promise<Collection>
getHotListEntry(symbol: string, direction: string): Promise<HotListDocument | null>
markHotListComplete(symbol: string, direction: string): Promise<void>
```

### Signal Management

```typescript
createSignal(data: SignalData): Promise<{ inserted: boolean; id?: string }>
```

### Rotation State Management

```typescript
getRotationState(): Promise<RotationStateDocument | null>
updateRotationState(updates: Partial<RotationStateDocument>): Promise<void>
```

## Data Lifecycle

### Symbol Lifecycle

1. **Import**: Symbol added via `/api/tte/symbols/import`
2. **Scanning**: Symbol included in batches based on priority rotation
3. **Tracking**: `last_scanned` and `scan_count` updated after each scan
4. **Signals**: `signal_count` incremented when signals are created

### Hot Symbol Lifecycle

1. **Creation**: NWE webhook creates hot list entry with expiration
2. **Pending**: Status `pending_tier2`, waiting for OBDIV processing
3. **Processing**: TTE fetches hot symbol, processes through OBDIV screener
4. **Completion**: OBDIV webhook creates signal, marks hot entry as `tier2_complete`
5. **Expiration**: Expired entries deleted at TTE startup (or manually via API)

**Timeline Example** (5m timeframe):
```
00:00 - NWE triggers, hot entry created (expires_at: 00:05)
00:01 - TTE fetches hot symbol, inputs into OBDIV
00:02 - OBDIV webhook fires, signal created, hot entry marked complete
00:05 - Entry expires (if not processed, deleted at next startup)
```

### Signal Lifecycle

1. **Creation**: OBDIV webhook creates signal with `status: "pending_screenshot"`
2. **Screenshot**: TTE captures chart screenshot (legacy mode, not used in tiered mode)
3. **Update**: Screenshot URL added via `PATCH /api/tte/signals/{id}`
4. **Completion**: Status changed to `"complete"`
5. **Display**: Frontend queries and displays signal to user

### Rotation State Lifecycle

1. **Initialization**: Created via `POST /api/tte/init`
2. **Batch Processing**: Updated on each `get_next_symbol_batch()` call
3. **Rotation Completion**: Resets when all symbols scanned
4. **Continuous**: Runs indefinitely until manually reset

---

**Related**:
- [API Endpoints](api_endpoints.md) - Endpoints that interact with these collections
- [Symbol Management](symbol_management.md) - Priority rotation algorithm details
- [Integration Flow](integration_flow.md) - How data flows through the system
