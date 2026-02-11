---
name: stock-buddy
description: Stock Buddy web app architecture and TTE integration. Use when working with Stock Buddy codebase, debugging TTE-Stock Buddy integration, modifying signal APIs, querying trading signals, or understanding the combo/tiered signal workflow. Covers API endpoints, database schema, frontend components, and combo live signals.
---

# Stock Buddy Skill

Comprehensive knowledge of the Stock Buddy web application and its integration with TradingView to Everywhere (TTE).

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [When to Use This Skill](#when-to-use-this-skill)
- [System Architecture](#system-architecture)
- [Key Concepts](#key-concepts)
- [Navigation Guide](#navigation-guide)
- [Critical Files](#critical-files)
- [Common Workflows](#common-workflows)

## Overview

Stock Buddy is a Next.js web application that receives and displays trading signals from TradingView via the TTE (TradingView to Everywhere) orchestrator. It manages:

- **Symbol rotation**: Priority-based batch scheduling for 900+ symbols
- **Hot symbol tracking**: Temporary queue for symbols that triggered NWE zones
- **Signal storage**: Level 1/2/3 trading signals with technical confirmation
- **REST API**: 12+ endpoints for webhook processing and data queries
- **Frontend display**: React components for signal visualization and chat integration

### The TTE + Stock Buddy Relationship

```
TradingView Screeners (Pine Script)
         ↓
TTE Orchestrator (Python - Selenium automation)
         ↓
Stock Buddy API (Next.js - REST endpoints)
         ↓
Stock Buddy Frontend (React - Signal display)
```

> **Production System**: Combo mode is the active production system (Feb 2026). The tiered mode described below is legacy. See [Combo Architecture](../../docs/combo/ARCHITECTURE.md) and [Combo PRD](../../docs/combo/PRD.md) for combo mode details.

### Combo Mode Data Flow (Production)
1. 352 persistent TradingView alerts monitor ~1,054 symbols (3 per alert)
2. Combo screener (NWE + OB/FVG + Divergence) fires webhook on every tick
3. Stock Buddy receives webhook at `POST /api/tte/combo`
4. Upserts signal state into `tte_live_signals` collection
5. Frontend queries via `GET /api/tte/combo/signals`
6. Maintenance every 5 minutes restarts any inactive alerts

### Tiered Mode Data Flow (Legacy)
1. **Tiered (legacy)**: TTE fetches 20 symbols from Stock Buddy API
2. TTE inputs symbols into TradingView NWE screener
3. TTE creates webhook alert, TradingView fires webhook to Stock Buddy
4. Stock Buddy stores hot symbols in `tte_hot_list` collection
5. TTE fetches hot symbols from Stock Buddy API
6. TTE processes hot symbols through OBDIV screener (batches of 8)
7. OBDIV webhook creates confirmed signals in `tte_signals` collection
8. Frontend queries signals via RTK Query and displays to user

## Quick Start

### Key Terminology

| Term | Definition |
|------|------------|
| **NWE** | Nadaraya-Watson Envelope - Tier 1 screener for zone entries |
| **OBDIV** | Order Block + Divergence - Tier 2 screener for confirmation |
| **Hot Symbol** | Symbol that triggered NWE zone (pending OBDIV processing) |
| **Signal Level** | 1 (NWE only), 2 (NWE + OB/DIV), 3 (NWE + OB + DIV) |
| **Priority** | A (every batch), B (every 3rd rotation), C (every 10th rotation) |
| **Rotation** | Complete cycle through all symbols once |
| **Batch** | Symbols processed in a single scan (20 for tiered, 3 for combo) |

### Project Locations

- **TTE Repository**: `C:\Users\dassa\Work\For Poolsifi\tradingview to everywhere`
- **Stock Buddy Repository**: `C:\Users\dassa\Work\Stock-Buddy-App`

### API Base URL

Production: `https://stock-buddy-app.vercel.app/api/tte`

## When to Use This Skill

Invoke this skill for:

- ✓ Understanding how Stock Buddy receives signals from TTE
- ✓ Debugging webhook integration issues
- ✓ Querying or filtering signals by level/direction/timeframe
- ✓ Modifying API endpoints or Zod schemas
- ✓ Working on the signal display frontend
- ✓ Understanding the symbol rotation algorithm
- ✓ Adding new database collections or fields
- ✓ Investigating hot symbol expiration logic
- ✓ Creating new API endpoints for TTE orchestrator

## System Architecture

### Two-Tier Signal Workflow

**Phase 1: NWE Screening (Tier 1)**
1. **(Tiered only)** Stock Buddy API provides next batch of 20 symbols (priority-rotated)
2. TTE inputs symbols into TradingView NWE screener
3. TTE creates webhook alert with URL: `/api/tte/nwe`
4. TradingView sends batch webhook when symbols enter zones
5. Stock Buddy stores hot symbols with expiration timestamps
6. TTE marks symbols as scanned, deletes alert

**Phase 2: OBDIV Confirmation (Tier 2)**
1. TTE fetches hot symbols from Stock Buddy (max 8 at a time)
2. TTE inputs hot symbols into TradingView OBDIV screener
3. TTE creates webhook alert with URL: `/api/tte/obdiv`
4. TradingView sends webhook with OB/DIV findings
5. Stock Buddy validates hot list entry, creates signal with level
6. TTE deletes alert, repeats until hot list is empty

### Tech Stack

**Frontend**:
- Next.js 14 (App Router)
- React 18
- TypeScript
- Redux Toolkit + RTK Query
- Tailwind CSS
- Vercel (deployment)

**Backend**:
- Next.js API routes
- MongoDB (hosted database)
- Zod (validation)

**Integration**:
- TradingView webhooks (POST from Pine Script)
- TTE API client (Python requests)

## Key Concepts

### Signal Levels

Stock Buddy assigns levels based on confirmation strength:

| Level | Criteria | Description | Color |
|-------|----------|-------------|-------|
| **1** | NWE zone only | Symbol entered NWE envelope | Yellow |
| **2** | NWE + (OB OR DIV) | Zone + Order Block OR Divergence | Orange |
| **3** | NWE + OB + DIV | Zone + Order Block AND Divergence | Green |

Calculation logic (automatic):
```typescript
if (hasOB && hasDiv) return 3;
if (hasOB || hasDiv) return 2;
return 1;
```

### Hot Symbol Expiration

Each hot symbol has an expiration based on its NWE timeframe:

| Timeframe | Expiration Duration |
|-----------|---------------------|
| 5m | 5 minutes |
| 15m | 15 minutes |
| 1H | 1 hour |
| H4 | 4 hours |
| D1 | 24 hours |

**Expiration rules**:
- Calculated as: `nwe_timestamp + timeframe_duration`
- No refresh: once created, expiration is never extended
- Auto-cleanup: TTE deletes expired hot symbols at startup

### Priority Rotation System

Symbols are assigned priorities that control scan frequency:

| Priority | Description | Scan Frequency | Count |
|----------|-------------|----------------|-------|
| **A** | Major pairs (EURUSD, GBPUSD, etc.) | Every batch | ~28 |
| **B** | Secondary symbols | Every 3rd rotation | ~150 |
| **C** | Exotic/low-volume | Every 10th rotation | ~763 |

**Algorithm**:
1. Always include all A-priority symbols
2. Include B symbols if `rotation_number % 3 == 0`
3. Include C symbols if `rotation_number % 10 == 0`
4. Fill remaining slots with least-recently-scanned symbols

### Batch and Rotation Tracking

The `tte_rotation_state` collection tracks progress:

```typescript
{
  _id: "current",
  batch_number: 6,              // Total batches processed
  rotation_number: 1,            // Complete rotation cycles
  symbols_scanned_this_rotation: 120,
  total_symbols: 941,
  last_batch_at: Date,
  last_batch_symbols: ["EURUSD", "GBPUSD", ...]
}
```

**Rotation completion**: When `symbols_scanned_this_rotation >= total_symbols`, rotation resets to 0.

## Navigation Guide

Based on your task, read the appropriate reference file:

| Task Type | Reference File |
|-----------|----------------|
| Working with API endpoints, webhooks, or TTE client | [API Endpoints](references/api_endpoints.md) |
| Understanding database collections, fields, or queries | [Database Schema](references/database_schema.md) |
| Working on frontend signal display or components | [Frontend Components](references/frontend_components.md) |
| Debugging TTE → Stock Buddy integration flow | [Integration Flow](references/integration_flow.md) |
| Understanding symbol rotation or batch selection | [Symbol Management](references/symbol_management.md) |

## Critical Files

### TTE Codebase (Python)

| File | Purpose |
|------|---------|
| `tiered_main.py` | Entry point for tiered orchestrator |
| `orchestrator.py` | `TieredOrchestrator` class - two-phase workflow |
| `api_client.py` | `StockBuddyAPIClient` - HTTP client for Stock Buddy API |
| `config.py` | Configuration (API URL, timeouts, delays) |
| `docs/API.md` | API endpoint documentation |
| `docs/legacy/PRD.md` | Complete technical specification (1800+ lines) |

### Stock Buddy Codebase (TypeScript/Next.js)

| File | Purpose |
|------|---------|
| `src/app/api/tte/nwe/route.ts` | NWE webhook endpoint (Tier 1) |
| `src/app/api/tte/obdiv/route.ts` | OBDIV webhook endpoint (Tier 2) |
| `src/app/api/tte/hot-symbols/route.ts` | Get hot symbols (pending Tier 2) |
| `src/app/api/tte/symbols/next-batch/route.ts` | Get next symbol batch (priority rotation) |
| `src/app/api/tte/signals/route.ts` | Query signals with filters |
| `src/lib/tte/schemas.ts` | Zod validation schemas + TypeScript types |
| `src/lib/tte/collections.ts` | MongoDB collection helpers |
| `src/lib/redux/api/signalsApi.ts` | RTK Query hooks for frontend |
| `src/components/signals/*` | React components for signal display |

## Common Workflows

### Debugging Webhook Integration

1. Read [Integration Flow](references/integration_flow.md) for complete workflow
2. Read [API Endpoints](references/api_endpoints.md) for webhook payload schemas
3. Check TTE logs: `app_log.log` (webhook creation and alert timing)
4. Check Stock Buddy API logs: Vercel dashboard or local console
5. Validate payload format against Zod schemas in `src/lib/tte/schemas.ts`

**Common issues**:
- NWE webhook sends empty `symbols: []` array (valid - no triggers)
- OBDIV webhook sent but no matching hot list entry (symbol expired)
- Webhook URL mismatch (check `config.py` and endpoint paths)

### Querying Signals

Read [API Endpoints](references/api_endpoints.md) for:
- `/api/tte/signals` query parameters
- Filtering by level, direction, status, symbol
- Pagination with limit/offset
- Sorting options

Example API calls:
```bash
# Get latest 10 Level 3 signals
curl "https://stock-buddy-app.vercel.app/api/tte/signals?limit=10&level=3"

# Get bullish signals for EURUSD
curl "https://stock-buddy-app.vercel.app/api/tte/signals?symbol=EURUSD&direction=bullish"
```

### Working on Frontend Signal Display

1. Read [Frontend Components](references/frontend_components.md) for component hierarchy
2. Read [Database Schema](references/database_schema.md) for signal field definitions
3. Check RTK Query hooks in `src/lib/redux/api/signalsApi.ts`
4. Modify components in `src/components/signals/`

**Data flow**:
```
API endpoint → RTK Query → Redux store → React component → UI
```

### Modifying Symbol Rotation Logic

1. Read [Symbol Management](references/symbol_management.md) for algorithm details
2. Read [Database Schema](references/database_schema.md) for `tte_symbols` and `tte_rotation_state`
3. Modify `src/lib/tte/collections.ts` - `getNextBatch()` function
4. Test with `/api/tte/symbols/next-batch` endpoint

### Adding a New API Endpoint

1. Read [API Endpoints](references/api_endpoints.md) for existing patterns
2. Create new route file in `src/app/api/tte/<endpoint>/route.ts`
3. Define Zod schema in `src/lib/tte/schemas.ts` (if needed)
4. Add collection helper in `src/lib/tte/collections.ts` (if needed)
5. Update TTE's `api_client.py` with new method
6. Document in TTE's `docs/API.md`

## Testing the Integration

### Test API Connection (TTE side)

```bash
# From TTE repository
python tiered_main.py --test-api    # Full API connection test
python tiered_main.py --stats       # View current statistics
python tiered_main.py --validate    # Validate configuration
```

### Manual API Testing

```bash
# Health check
curl https://stock-buddy-app.vercel.app/api/health

# Get stats
curl https://stock-buddy-app.vercel.app/api/tte/stats

# Get next batch
curl "https://stock-buddy-app.vercel.app/api/tte/symbols/next-batch?size=20"

# Get hot symbols
curl "https://stock-buddy-app.vercel.app/api/tte/hot-symbols?limit=8"

# Test NWE webhook
curl -X POST https://stock-buddy-app.vercel.app/api/tte/nwe \
  -H "Content-Type: application/json" \
  -d '{"tier":"nwe","symbols":[{"symbol":"EURUSD","direction":"bullish","timeframes":["5m"]}],"timestamp":1705312800,"count":1}'
```

## Additional Resources

- [TTE CLAUDE.md](../../CLAUDE.md) - TTE development guidelines
- [TTE docs/legacy/PRD.md](../../docs/legacy/PRD.md) - Complete technical specification
- [Anthropic Skills Best Practices](https://github.com/anthropics/anthropic-skills) - Skill creation guide

---

**Last Updated**: 2026-02-06
**Skill Version**: 1.0.0
**Maintained By**: TTE Development Team
