# ADR-003: Remove NWE Calculation from Tier 2 Screener

**Status:** Accepted
**Date:** 2026-01-29
**Decision Makers:** Development Team
**Category:** Optimization

---

## Context

In the original tiered architecture design, the Tier 2 (OBDIV) screener included NWE zone calculation to verify that the symbol was still in an NWE zone at the time of OB/DIV check.

### Original Tier 2 Design

```pinescript
// Original OBDIV Screener (with NWE)
checkSignal(symbol) =>
    // 1. Calculate NWE zones
    [nweBull, nweBear] = calcNWE(...)

    // 2. Check OB/FVG
    [obFound, obTf, obType] = calcOB(...)

    // 3. Check Divergence
    [divFound, divTf, divType] = calcDiv(...)

    // 4. Return combined signal
    signal = nweBull and obFound and divFound
```

This raised a question: **Is NWE calculation in Tier 2 necessary or redundant?**

---

## Decision

We decided to **remove NWE calculation from the Tier 2 screener** entirely.

### Simplified Tier 2 Design

```pinescript
// New OBDIV Screener (without NWE)
checkSignal(symbol) =>
    // 1. Check OB/FVG (bullish and bearish)
    [bullObFound, bullObTf, bullObType] = calcBullOB(...)
    [bearObFound, bearObTf, bearObType] = calcBearOB(...)

    // 2. Check Divergence (bullish and bearish)
    [bullDivFound, bullDivTf, bullDivType] = calcBullDiv(...)
    [bearDivFound, bearDivTf, bearDivType] = calcBearDiv(...)

    // 3. Return both directions (API matches with hot list)
    [bullObFound, bullObTf, bullDivFound, bullDivTf,
     bearObFound, bearObTf, bearDivFound, bearDivTf]
```

---

## Rationale

### Why NWE in Tier 2 is Redundant

1. **Tier 1 Already Confirmed NWE**
   - Symbol only reaches hot list because Tier 1 detected NWE zone entry
   - Hot list stores the direction and timeframes from Tier 1
   - Re-checking NWE in Tier 2 duplicates this work

2. **NWE Zones Are Relatively Stable**
   - NWE uses kernel regression with smoothing
   - Zone boundaries don't change dramatically bar-to-bar
   - If NWE triggered on bar N, it's likely still valid on bar N+1

3. **Timing Between Tiers Is Short**
   - Tier 1 webhook fires immediately on NWE entry
   - Python polls hot list every 60 seconds (configurable)
   - Tier 2 check happens within minutes of Tier 1

4. **API Handles Direction Matching**
   - Hot list stores direction from Tier 1 (bullish/bearish)
   - Tier 2 reports both bullish and bearish OB/DIV findings
   - API matches Tier 2 findings with Tier 1 direction

### Request.Security Savings

| Calculation | Calls Saved | Notes |
|-------------|-------------|-------|
| NWE (2 timeframes) | 2 per symbol | yhat_close, ktr |
| Total for 8 symbols | 16 calls | Significant savings |

Without NWE, Tier 2 uses ~24 calls for 8 symbols.
With NWE, Tier 2 would use ~40 calls for 8 symbols.

### Why Report Both Directions

Instead of only checking the direction from the hot list, we report **both** bullish and bearish findings:

```json
{
  "tier": "obdiv",
  "symbol": "GBPAUD",
  "bull_ob": {"found": true, "tf": "W1", "type": "OB"},
  "bull_div": {"found": true, "tf": "H4", "type": "Logic2"},
  "bear_ob": {"found": false},
  "bear_div": {"found": false}
}
```

**Benefits:**
- Tier 2 screener is direction-agnostic
- Simpler Pine Script logic (no need to check hot list direction)
- API handles the matching logic
- If hot list is wrong, we still have all data

---

## Consequences

### Positive

- **Simpler Tier 2 Screener**: Less code, fewer calculations
- **Faster Processing**: 16 fewer request.security() calls
- **Cleaner Separation**: Each tier has one job
- **More Flexible**: Tier 2 provides all data, API decides

### Negative

- **Potential Race Condition**: If NWE zone exits between Tier 1 and Tier 2
  - Mitigated by short timing (minutes, not hours)
  - NWE zones are stable (kernel smoothing)

- **Extra API Logic**: API must match direction from hot list
  - Simple database lookup
  - Clear matching rules

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| NWE zone exits before Tier 2 | Low | Low | Short timing, stable zones |
| Direction mismatch | Very Low | Medium | API validates direction |
| Hot list corruption | Very Low | Medium | Database validation |

---

## Implementation Details

### Tier 2 Screener Changes

**Before (with NWE):**
```pinescript
// Calculate NWE
[nweBull, nweBear] = calcNWE(...)

// Only check matching direction
if nweBull
    checkBullishOB(...)
    checkBullishDiv(...)
```

**After (without NWE):**
```pinescript
// Check both directions
[bullOb] = checkBullishOB(...)
[bullDiv] = checkBullishDiv(...)
[bearOb] = checkBearishOB(...)
[bearDiv] = checkBearishDiv(...)

// Report everything
alert(buildPayload(bullOb, bullDiv, bearOb, bearDiv))
```

### API Direction Matching

```typescript
// /api/obdiv handler
const hotEntry = await db.hot_list.findOne({
  symbol,
  status: 'pending_tier2'
});

if (!hotEntry) {
  return res.json({ success: true, signal_created: false, reason: 'not_in_hot_list' });
}

// Match direction
const { direction } = hotEntry;
const obFound = direction === 'bullish' ? bull_ob.found : bear_ob.found;
const divFound = direction === 'bullish' ? bull_div.found : bear_div.found;

// Calculate level
const level = divFound ? 3 : (obFound ? 2 : 1);
```

---

## Alternative Considered: NWE Expiration Check

We considered adding an "expiration check" instead of full NWE recalculation:

```pinescript
// Check if last NWE trigger was within X bars
barsAgo = ta.barssince(nweTriggered)
stillValid = barsAgo <= 5  // Within 5 bars
```

**Rejected because:**
- Still requires NWE calculation to track the trigger
- Adds complexity for marginal benefit
- Hot list expiration (24hr) handles stale entries

---

## Related Decisions

- [ADR-001: Tiered Screener Architecture](001-tiered-architecture.md)
- [ADR-002: Webhook vs Alert Scraping](002-webhook-vs-scraping.md)

---

## References

- Signal flow timing analysis
- request.security() limit documentation
- Hot list expiration design
