# ADR-001: Tiered Screener Architecture

**Status:** Accepted
**Date:** 2026-01-28
**Decision Makers:** Development Team
**Category:** Architecture

---

## Context

The TTE (TradingView to Everywhere) project needed to screen 40+ forex symbols for trading signals using a combination of three indicators:
1. NWE (Nadaraya-Watson Envelope) - Zone entry detection
2. OB/FVG (Order Block / Fair Value Gap) - Support/resistance zones
3. Divergence (Kernel AO) - Momentum confirmation

### The Problem

Pine Script has a hard limit of **40 `request.security()` calls per script** (64 with Ultimate plan). Our full screener was using ~24 calls for just 8 symbols (8 × 3 timeframes). This made scaling to 40+ symbols impossible with a single script.

### Options Considered

**Option A: Multiple Full Screeners**
- Copy the full screener multiple times
- Each copy watches ~8 symbols
- All indicators run simultaneously for all symbols

**Option B: Lightweight Screeners + Manual Selenium Checks**
- NWE-only screeners watch 20 symbols each
- When NWE triggers, Python opens that symbol's chart
- Python manually loads OB and DIV indicators sequentially

**Option C: Tiered Architecture (Chosen)**
- Tier 1: Lightweight NWE-only screeners (20 symbols × 2 TFs = 40 calls)
- Tier 2: Focused OB+DIV screener (8 symbols, dynamically set)
- Hot list manages symbols between tiers

---

## Decision

We chose **Option C: Tiered Architecture** because it provides the best balance of efficiency, scalability, and maintainability.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         TIER 1                                   │
│  TTE NWE Screener (20 symbols × H4+D1 = 40 request.security)    │
│  - Lightweight NWE zone detection only                          │
│  - Fires webhook when symbol enters NWE zone                    │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         HOT LIST                                 │
│  MongoDB collection storing symbols awaiting Tier 2 check       │
│  - Symbol, direction, NWE timeframes, timestamp                 │
│  - Status: pending_tier2 → tier2_complete → expired             │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         TIER 2                                   │
│  TTE OBDIV Screener (8 symbols, dynamically set by Python)      │
│  - OB/FVG and Divergence detection only (no NWE)                │
│  - Fires webhook with OB/DIV findings                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Rationale

### Why Tiered Architecture Works

1. **Efficient Use of request.security()**
   - Tier 1 uses 40 calls for 20 symbols (2 TFs each)
   - Tier 2 uses 24 calls for 8 symbols (3 TFs each)
   - Total: 2 screeners instead of 5+ full screeners

2. **Conditional Processing**
   - Only ~10% of symbols trigger NWE (Tier 1) at any time
   - Tier 2 only runs for symbols that passed Tier 1
   - Saves 90% of unnecessary OB/DIV calculations

3. **Dynamic Symbol Updates**
   - Hot list continuously updated by Tier 1 webhooks
   - Python orchestrator batches hot symbols for Tier 2
   - Selenium changes Tier 2 screener inputs dynamically

4. **Scalability**
   - Can add more Tier 1 screeners (20 symbols each)
   - Multiple Tier 1 screeners feed into same hot list
   - Tier 2 capacity determined by poll frequency

### Why Not Option A

- **Wasteful**: 90% of OB/DIV calculations are unnecessary (NWE didn't trigger)
- **Limited**: Can only watch ~40 symbols total (5 screeners × 8 symbols)
- **Expensive**: More TradingView compute usage

### Why Not Option B

- **Slow**: Sequential Selenium navigation per symbol
- **Brittle**: Relies heavily on TradingView UI stability
- **Complex**: Python needs to interpret visual indicator output

---

## Consequences

### Positive

- **Scalable**: Can watch 100+ symbols with minimal changes
- **Efficient**: Only processes symbols with potential signals
- **Maintainable**: Clear separation of concerns between tiers
- **Flexible**: Easy to add new indicators or modify thresholds

### Negative

- **More Components**: Requires API, database, Python orchestrator
- **Latency**: Small delay between Tier 1 and Tier 2 (polling interval)
- **Complexity**: More moving parts to monitor and maintain

### Neutral

- **Infrastructure**: Requires MongoDB and Vercel deployment
- **Cost**: Minimal (free tiers sufficient for current scale)

---

## Implementation Notes

### Tier 1 Screener
- Watches 20 forex pairs on H4 and D1 timeframes
- Sends webhook with: symbol, direction, timeframes
- Non-repainting (fires on bar close only)

### Hot List Management
- 24-hour expiration for stale entries
- Status tracking for Tier 2 processing
- Prevents duplicate processing

### Tier 2 Screener
- Dynamic symbol inputs (Python changes via Selenium)
- Reports both bullish and bearish findings
- API matches direction with hot list

### Signal Creation
- Level 1: NWE only
- Level 2: NWE + OB/FVG
- Level 3: NWE + OB/FVG + Divergence

---

## Related Decisions

- [ADR-002: Webhook vs Alert Scraping](002-webhook-vs-scraping.md)
- [ADR-003: Remove NWE from Tier 2](003-remove-nwe-from-tier2.md)

---

## References

- Pine Script request.security() documentation
- TradingView indicator limits
- Original architecture discussion (2026-01-28)
