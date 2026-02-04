# Signal Freshness and Dashboard Timing

Understanding how the TTE tiered architecture affects signal timing, freshness, and when signals become stale.

---

## Executive Summary

The TTE tiered system scans **941 symbols** across two screener phases (NWE → OBDIV). Due to the sequential batch processing:

| Metric | Value |
|--------|-------|
| Total Symbols | 941 |
| NWE Batch Size | 20 symbols |
| OBDIV Batch Size | 8 symbols |
| Batches per Rotation | ~47 |
| Full Rotation Time | ~55 min (best) to ~6+ hours (worst) |

**Key insight**: Signal staleness is based on **timeframe bar close**, not fixed duration. A 5m signal becomes stale when the next 5m bar closes (max 5 minutes), while a 1H signal stays fresh for up to 60 minutes.

---

## Table of Contents

1. [Scanning Architecture](#scanning-architecture)
2. [Timeframe Staleness Rules](#timeframe-staleness-rules)
3. [Dashboard Freshness Interpretation](#dashboard-freshness-interpretation)
4. [Full Rotation Timing Analysis](#full-rotation-timing-analysis)
5. [Priority Rotation System](#priority-rotation-system)
6. [Current System Limitations](#current-system-limitations)
7. [API Reference for Freshness Queries](#api-reference-for-freshness-queries)
8. [Quick Reference Card](#quick-reference-card)

---

## Scanning Architecture

### Two-Tier Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                     TIER 1: NWE SCREENER                        │
│  Input: 20 symbols batch from API rotation                      │
│  Checks: NWE zone overlap on 5m, 15m timeframes                 │
│  Output: Hot symbols (those in NWE zones) → sent to API         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TIER 2: OBDIV SCREENER                       │
│  Input: 8 hot symbols per batch from hot list                   │
│  Checks:                                                        │
│    - OB/FVG overlap on 5m, 15m, 1H timeframes                   │
│    - Kernel AO Divergence on 5m, 15m timeframes                 │
│  Output: Confirmed signals (Level 1/2/3) → stored in database   │
└─────────────────────────────────────────────────────────────────┘
```

### Batch Timing Breakdown

| Phase | Operation | Typical Duration |
|-------|-----------|------------------|
| NWE | Input 20 symbols | ~5-10s |
| NWE | Create webhook alert | ~3-5s |
| NWE | Wait for webhook | 60s (configurable) |
| NWE | Delete alert + mark scanned | ~5s |
| OBDIV | Switch layout | ~5s |
| OBDIV | Input 8 symbols | ~3-5s |
| OBDIV | Create webhook alert | ~3-5s |
| OBDIV | Wait for webhook | 60s (configurable) |
| OBDIV | Delete alert | ~3s |
| **Total per NWE batch** | *Without hot symbols* | **~70-80s** |
| **Total per NWE batch** | *With 8 hot symbols* | **~130-150s** |
| **Total per NWE batch** | *With 16 hot symbols* | **~190-210s** |

### When Symbols Get Re-Scanned

A symbol gets re-scanned when:

1. **It's in the current batch** - The API returns it in `get_next_symbol_batch()`
2. **Priority A symbols** - Included in every batch (always re-scanned)
3. **Priority B symbols** - Every 3rd rotation
4. **Priority C symbols** - Every 10th rotation

See [Priority Rotation System](#priority-rotation-system) for details.

---

## Timeframe Staleness Rules

### Core Principle: Bar Close Determines Staleness

**Staleness is NOT based on fixed time duration.** Instead, a signal's timeframe component becomes stale when the next bar on that timeframe closes.

| Timeframe | Signal Becomes Stale | Max Fresh Duration |
|-----------|---------------------|-------------------|
| **5m** | When next 5m bar closes | 5 minutes |
| **15m** | When next 15m bar closes | 15 minutes |
| **1H** | When next 1H bar closes | 60 minutes |

### Why Bar Close Matters

Trading signals are derived from technical analysis that uses bar data (open, high, low, close). Once a new bar closes:

- The zone overlap may no longer exist
- Price may have moved away from the zone
- The divergence pattern may have resolved

Therefore, signals from that timeframe should be considered potentially invalid.

### Multi-Timeframe Signal Handling

A TTE signal can have components from multiple timeframes:

| Component | Source | Timeframes Used |
|-----------|--------|-----------------|
| `nwe_tf` | NWE Screener | 5m, 15m |
| `ob_tf` | OBDIV Screener | 5m, 15m, 1H |
| `div_tf` | OBDIV Screener | 5m, 15m |

**Each timeframe component has independent staleness.** A signal may be partially fresh (some components valid, others stale).

### Example 1: Fresh 5m Signal

```
Signal created at 10:03:45
nwe_tf = ["5m"]

Current time: 10:04:30
Next 5m bar closes at: 10:05:00

5m NWE Status: FRESH (35 seconds until stale)
Overall Status: FRESH
```

### Example 2: Multi-Timeframe Signal (All Fresh)

```
Signal created at 10:03:00
nwe_tf = ["5m", "15m"]
ob_tf = "1H"
div_tf = "15m"

Current time: 10:04:00

Component Analysis:
- 5m NWE: FRESH (stale at 10:05)
- 15m NWE: FRESH (stale at 10:15)
- 1H OB: FRESH (stale at 11:00)
- 15m DIV: FRESH (stale at 10:15)

Overall Status: FULLY FRESH
```

### Example 3: Multi-Timeframe Signal (Partial Staleness)

```
Signal created at 10:03:00
nwe_tf = ["5m", "15m"]
ob_tf = "1H"
div_tf = "5m"

Current time: 10:08:00

Component Analysis:
- 5m NWE: STALE (bar closed at 10:05)
- 15m NWE: FRESH (stale at 10:15)
- 1H OB: FRESH (stale at 11:00)
- 5m DIV: STALE (bar closed at 10:05)

Overall Status: PARTIALLY FRESH
Display: Show as "degraded" - higher TF components still valid
```

### Example 4: Completely Stale Signal

```
Signal created at 10:03:00
nwe_tf = ["5m"]
ob_tf = "5m"
div_tf = "5m"

Current time: 10:12:00

Component Analysis:
- 5m NWE: STALE (bar closed at 10:05)
- 5m OB: STALE (bar closed at 10:05)
- 5m DIV: STALE (bar closed at 10:05)

Overall Status: STALE
Display: Gray out or hide from active signals
```

---

## Dashboard Freshness Interpretation

### Signal Fields for Freshness Calculation

From the `tte_signals` collection:

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | Unix (seconds) | When signal was created |
| `nwe_tf` | string[] | NWE timeframes (e.g., `["5m", "15m"]`) |
| `ob_tf` | string | OB timeframe (e.g., `"1H"`) |
| `div_tf` | string | Divergence timeframe (e.g., `"15m"`) |
| `created_at` | ISO date | MongoDB creation timestamp |

### Freshness Calculation Algorithm

```python
def calculate_next_bar_close(timeframe: str, signal_time: datetime) -> datetime:
    """Calculate when the next bar closes for a given timeframe."""

    # Timeframe durations in minutes
    tf_minutes = {
        "5m": 5,
        "15m": 15,
        "1H": 60
    }

    minutes = tf_minutes.get(timeframe, 5)  # Default to 5m if unknown

    # Calculate current bar start (floor to timeframe boundary)
    bar_start_minute = (signal_time.minute // minutes) * minutes
    bar_start = signal_time.replace(minute=bar_start_minute, second=0, microsecond=0)

    # If signal is after bar start, next close is one period later
    if signal_time >= bar_start:
        next_close = bar_start + timedelta(minutes=minutes)
    else:
        next_close = bar_start

    return next_close


def get_signal_freshness(signal: dict, current_time: datetime) -> dict:
    """
    Calculate freshness status for each signal component.

    Returns dict with:
    - overall_status: "fresh", "partial", "stale"
    - components: dict of component -> {"status": str, "stale_at": datetime}
    """
    signal_time = datetime.fromtimestamp(signal["timestamp"])
    components = {}

    # Check NWE timeframes
    for tf in signal.get("nwe_tf", []):
        stale_at = calculate_next_bar_close(tf, signal_time)
        components[f"nwe_{tf}"] = {
            "status": "fresh" if current_time < stale_at else "stale",
            "stale_at": stale_at
        }

    # Check OB timeframe
    if signal.get("ob_tf"):
        tf = signal["ob_tf"]
        stale_at = calculate_next_bar_close(tf, signal_time)
        components[f"ob_{tf}"] = {
            "status": "fresh" if current_time < stale_at else "stale",
            "stale_at": stale_at
        }

    # Check DIV timeframe
    if signal.get("div_tf"):
        tf = signal["div_tf"]
        stale_at = calculate_next_bar_close(tf, signal_time)
        components[f"div_{tf}"] = {
            "status": "fresh" if current_time < stale_at else "stale",
            "stale_at": stale_at
        }

    # Determine overall status
    statuses = [c["status"] for c in components.values()]
    if all(s == "fresh" for s in statuses):
        overall = "fresh"
    elif all(s == "stale" for s in statuses):
        overall = "stale"
    else:
        overall = "partial"

    return {
        "overall_status": overall,
        "components": components
    }
```

### Display Recommendations

| Overall Status | Visual Indicator | Recommended Action |
|---------------|------------------|-------------------|
| **Fresh** | Green badge/dot | Show prominently, actionable |
| **Partial** | Yellow/amber badge | Show with warning, still tradeable |
| **Stale** | Gray/dim or hidden | Hide from main view or gray out |

#### Suggested UI Pattern

```
┌────────────────────────────────────────────────────────────┐
│ EURUSD   🟢 FRESH   Bullish L3                             │
│ Created: 10:03:00   Expires: 11:00 (1H OB)                 │
│ Components: 5m NWE ✓  15m NWE ✓  1H OB ✓  15m DIV ✓        │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ GBPJPY   🟡 PARTIAL   Bearish L2                           │
│ Created: 10:03:00   Lowest TF expired                      │
│ Components: 5m NWE ✗  15m NWE ✓  1H OB ✓                   │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ AUDNZD   ⚫ STALE   Bullish L1                              │
│ Created: 09:03:00   All components expired                 │
│ [Hidden from main view or grayed out]                      │
└────────────────────────────────────────────────────────────┘
```

---

## Full Rotation Timing Analysis

### Rotation Metrics

| Metric | Formula | Value |
|--------|---------|-------|
| Total Symbols | - | 941 |
| NWE Batch Size | - | 20 |
| Total NWE Batches | 941 ÷ 20 | ~47 batches |
| OBDIV Batch Size | - | 8 |

### Scenario Analysis

| Scenario | Hot Symbols per Batch | Time per Batch | Full Rotation |
|----------|----------------------|----------------|---------------|
| **Best Case** | 0 (no hot symbols) | ~70s | ~55 minutes |
| **Average** | 4 (~20% hit rate) | ~130s | ~1.7 hours |
| **Busy** | 8 (~40% hit rate) | ~150s | ~2 hours |
| **Very Busy** | 16+ | ~210s+ | ~2.7 hours |
| **Worst Case** | All 20 hot | ~270s+ | ~3.5+ hours |

### "When Will My Symbol Be Scanned Again?"

For a specific symbol, calculate:

```python
def estimate_next_scan(symbol: str, current_rotation_progress: int,
                       symbol_position: int, batch_size: int = 20,
                       avg_batch_time_seconds: int = 130) -> int:
    """
    Estimate seconds until a symbol is scanned again.

    Args:
        symbol: The symbol to check
        current_rotation_progress: Symbols already scanned this rotation
        symbol_position: Position of symbol in rotation queue
        batch_size: NWE batch size (default 20)
        avg_batch_time_seconds: Average time per batch (default 130s)

    Returns:
        Estimated seconds until next scan
    """
    if symbol_position <= current_rotation_progress:
        # Symbol already scanned this rotation - wait for next full rotation
        remaining_in_rotation = 941 - current_rotation_progress
        batches_remaining = remaining_in_rotation // batch_size
        time_to_end = batches_remaining * avg_batch_time_seconds

        # Plus time to reach symbol in next rotation
        batches_to_symbol = symbol_position // batch_size
        time_in_next_rotation = batches_to_symbol * avg_batch_time_seconds

        return time_to_end + time_in_next_rotation
    else:
        # Symbol not yet scanned this rotation
        batches_until = (symbol_position - current_rotation_progress) // batch_size
        return batches_until * avg_batch_time_seconds
```

### Priority Impact on Wait Time

| Priority | Scan Frequency | Typical Wait (Best) | Typical Wait (Worst) |
|----------|---------------|---------------------|----------------------|
| **A** | Every batch | 0-70s | 0-210s |
| **B** | Every 3rd rotation | ~3-5 hours | ~6-10 hours |
| **C** | Every 10th rotation | ~10-18 hours | ~24-60 hours |

---

## Priority Rotation System

### Priority Definitions

| Priority | Symbol Count | Description | Examples |
|----------|--------------|-------------|----------|
| **A** | 28 | Major pairs, high-volume | EURUSD, GBPUSD, BTCUSD |
| **B** | 150 | Secondary symbols | AUDJPY, EURCHF, major stocks |
| **C** | 763 | Low-volume/exotic | Minor pairs, small caps |

### Scan Frequency by Priority

```
Priority A (28 symbols):
├── Scanned EVERY batch (always included)
├── Time between scans: 70-210 seconds
└── Signal freshness: Nearly always fresh

Priority B (150 symbols):
├── Scanned every 3rd ROTATION (not batch)
├── Time between scans: ~3-10 hours
└── Signal freshness: May be stale by next scan

Priority C (763 symbols):
├── Scanned every 10th ROTATION
├── Time between scans: ~10-60 hours
└── Signal freshness: Usually stale by next scan
```

### Rotation State Tracking

The API tracks rotation progress in `tte_rotation_state`:

```json
{
  "_id": "current",
  "batch_number": 47,
  "rotation_number": 2,
  "symbols_scanned_this_rotation": 120,
  "total_symbols": 941
}
```

Use `GET /api/tte/stats` to retrieve current rotation state.

---

## Current System Limitations

### Known Gaps

1. **No Auto-Expiration on Confirmed Signals**
   - Once a Level 1/2/3 signal is created, it stays in the database indefinitely
   - Dashboard must implement client-side staleness filtering
   - Recommendation: Add `expires_at` field based on longest timeframe component

2. **Hot List 24-Hour Expiration Only**
   - Hot list entries expire after 24 hours
   - This is much longer than signal freshness windows
   - A hot symbol may produce stale OBDIV signals if not processed quickly

3. **No Real-Time Signal Updates**
   - Signals are point-in-time snapshots
   - If price exits a zone, the signal isn't automatically invalidated
   - Dashboard should re-check zone validity for active signals

4. **Priority B/C Signal Staleness**
   - By the time Priority C symbols are re-scanned, their signals are definitely stale
   - Consider whether low-priority signals should be treated differently

### Recommended Future Improvements

1. **Add `expires_at` to Signals**
   ```json
   {
     "symbol": "EURUSD",
     "timestamp": 1705316400,
     "expires_at": 1705320000,  // Based on longest TF component
     "nwe_tf": ["5m", "15m"],
     "ob_tf": "1H"
   }
   ```

2. **Auto-Archive Stale Signals**
   - Background job to move stale signals to archive collection
   - Or add TTL index for automatic deletion

3. **Real-Time Zone Validation**
   - Periodic re-check of active signals against current price
   - Mark signals as "invalidated" if price exits zone

4. **Priority-Based Freshness Weighting**
   - Priority A signals: Full freshness rules
   - Priority C signals: Relaxed freshness (informational only)

---

## API Reference for Freshness Queries

### Get Recent Fresh Signals

```bash
# Get signals from last 15 minutes (likely still fresh)
curl "https://stock-buddy-app.vercel.app/api/tte/signals?from=$(date -d '15 minutes ago' +%s)&limit=50"
```

### Filter by Level and Direction

```bash
# Get Level 3 bullish signals (highest confidence)
curl "https://stock-buddy-app.vercel.app/api/tte/signals?level=3&direction=bullish&limit=20"
```

### Check Rotation State

```bash
# Get current rotation progress
curl "https://stock-buddy-app.vercel.app/api/tte/stats"
```

Response includes:
```json
{
  "rotation": {
    "batch_number": 47,
    "rotation_number": 2,
    "symbols_scanned_this_rotation": 120,
    "total_symbols": 941
  }
}
```

### Signal Response Fields for Freshness

```json
{
  "symbol": "EURUSD",
  "direction": "bullish",
  "level": 3,
  "nwe_tf": ["5m", "15m"],      // NWE timeframes
  "nwe_timestamp": 1705312800,  // When NWE triggered
  "ob_tf": "1H",                // OB timeframe (can be null)
  "div_tf": "15m",              // Divergence timeframe (can be null)
  "timestamp": 1705316400,      // Signal creation time
  "created_at": "2024-01-15T11:30:00Z"
}
```

---

## Quick Reference Card

### Staleness Windows

| Timeframe | Stale After |
|-----------|-------------|
| 5m | 5 minutes max |
| 15m | 15 minutes max |
| 1H | 60 minutes max |

### Screener Timeframes

| Screener | Component | Timeframes |
|----------|-----------|------------|
| NWE | Zone overlap | 5m, 15m |
| OBDIV | OB/FVG | 5m, 15m, 1H |
| OBDIV | Divergence | 5m, 15m |

### Priority Scan Frequency

| Priority | Count | Frequency |
|----------|-------|-----------|
| A | 28 | Every batch |
| B | 150 | Every 3rd rotation |
| C | 763 | Every 10th rotation |

### Batch Sizes

| Screener | Batch Size |
|----------|------------|
| NWE | 20 symbols |
| OBDIV | 8 symbols |

### Rotation Timing

| Scenario | Per Batch | Full Rotation |
|----------|-----------|---------------|
| Best | ~70s | ~55 min |
| Average | ~130s | ~1.7 hours |
| Worst | ~270s+ | ~3.5+ hours |

### Freshness Status Meanings

| Status | Meaning | Action |
|--------|---------|--------|
| Fresh | All TFs valid | Trade signal |
| Partial | Some TFs stale | Use caution |
| Stale | All TFs stale | Ignore/archive |

---

## See Also

- [Architecture](ARCHITECTURE.md) - System overview
- [API Reference](API.md) - Complete endpoint documentation
- [Database](DATABASE.md) - Schema definitions
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues
