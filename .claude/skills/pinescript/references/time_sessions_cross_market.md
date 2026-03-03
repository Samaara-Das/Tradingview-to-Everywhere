# Time, Sessions, and Cross-Market Data in Pine Script

Comprehensive reference for handling time zones, sessions, market hours, and cross-market data alignment. Critical for multi-symbol screeners that span different exchanges (e.g., US stocks + Indian stocks + Crypto).

---

## 1. Time System Fundamentals

### UNIX Timestamps
- Pine Script uses UNIX timestamps in **milliseconds** (not seconds)
- Timestamps are **timezone-agnostic** — represent absolute points in time regardless of location
- All `time`, `time_close`, `timenow` values are in UTC milliseconds

### Key Time Variables

| Variable | What It Returns | When to Use |
|----------|----------------|-------------|
| `time` | Bar opening timestamp (ms, UTC) | Most common — when bar started |
| `time_close` | Bar closing timestamp (ms, UTC) | When bar ends; `na` on realtime non-time-based charts |
| `time_tradingday` | UTC 00:00 of bar's trading day | Overnight sessions (futures, forex) |
| `timenow` | Current execution timestamp | **AVOID** — causes repainting |
| `last_bar_time` | Last available bar's opening time | Detecting end of data |
| `syminfo.timezone` | Exchange's IANA timezone ID | Formatting, session checks |

### Calendar Variables
- `year`, `month`, `dayofmonth`, `dayofweek`, `hour`, `minute`, `second`
- Expressed in **exchange timezone** by default
- Accept optional timezone parameter: `hour(time, "America/New_York")`
- `dayofweek`: 1=Sunday through 7=Saturday (Pine Script convention)

### Time Constants (milliseconds)

```pinescript
MS_PER_SECOND = 1000
MS_PER_MINUTE = 60000
MS_PER_HOUR   = 3600000
MS_PER_DAY    = 86400000
```

---

## 2. Timezone Handling

### Three Time Zones in Pine Script

1. **Exchange timezone** — Default for all calculations. Set by the symbol's exchange.
2. **Chart timezone** — Visual display only. Does NOT affect script calculations. Scripts cannot access this.
3. **Custom timezone parameter** — Specified in function calls to override exchange default.

### Timezone Notation

| Format | Example | DST Handling | Recommendation |
|--------|---------|--------------|----------------|
| IANA identifier | `"America/New_York"` | Auto-adjusts | **Always prefer** |
| UTC offset | `"UTC-5"` or `"GMT-5"` | Fixed, no DST | Avoid for regions with DST |

**Key exchanges and their IANA timezones:**

| Exchange | `syminfo.timezone` | UTC Offset |
|----------|-------------------|------------|
| NSE (India) | `"Asia/Kolkata"` | UTC+5:30 (no DST) |
| NYSE/NASDAQ | `"America/New_York"` | UTC-5 / UTC-4 (DST) |
| Binance (crypto) | `"Etc/UTC"` | UTC+0 (no DST) |
| LSE (London) | `"Europe/London"` | UTC+0 / UTC+1 (DST) |
| TSE (Tokyo) | `"Asia/Tokyo"` | UTC+9 (no DST) |

### Formatting Time

```pinescript
// Use str.format_time() — respects timezone
str.format_time(time, "yyyy-MM-dd HH:mm:ss", syminfo.timezone)

// For specific timezone
str.format_time(time, "HH:mm dd-MMM-yyyy", "Asia/Kolkata")

// NEVER use str.format_time() for time DIFFERENCES — it treats input as absolute time
// Use modular arithmetic instead:
elapsed_hours = (time2 - time1) / 3600000
```

---

## 3. Sessions

### Session State Variables

| Variable | True When | Note |
|----------|-----------|------|
| `session.ismarket` | Regular trading hours | **ALWAYS true on daily+ timeframes** |
| `session.ispremarket` | Pre-market (extended hours) | Intraday only |
| `session.ispostmarket` | Post-market (extended hours) | Intraday only |
| `session.isfirstbar` | First bar of session | |
| `session.islastbar` | Last bar of session | |
| `session.isfirstbar_regular` | First bar of regular session | |
| `session.islastbar_regular` | Last bar of regular session | |

### Session String Format

```
"HHmm-HHmm:BITMASK"
```

- Time in 24-hour format
- Bitmask: digits 1-7 (1=Sunday, 2=Monday, ..., 7=Saturday)
- Omit bitmask for all days

| Example | Meaning |
|---------|---------|
| `"24x7"` | 24/7 trading (crypto) |
| `"0000-0000"` | Full day, all days |
| `"0930-1600:23456"` | 9:30-16:00 Mon-Fri |
| `"0915-1530:23456"` | NSE India hours Mon-Fri |
| `"2000-1630:1234567"` | Overnight session |

### Checking If Bar Is In Session

```pinescript
// time() returns timestamp if bar is in session, na if outside
int timeInSession = time(timeframe.period, "0915-1530", "Asia/Kolkata")
bool inIndianSession = not na(timeInSession)

// Multiple sessions (e.g., morning + afternoon)
int timeInSplit = time(timeframe.period, "0915-1200,1300-1530", "Asia/Kolkata")
```

### Named Sessions for request.security()

```pinescript
// Create ticker with specific session type
string extendedTicker = ticker.modify(syminfo.tickerid, session.extended)
string regularTicker = ticker.modify(syminfo.tickerid, session.regular)

// Use in request.security()
float extClose = request.security(extendedTicker, "D", close[1], lookahead=barmerge.lookahead_on)
```

**Important**: Time-based session strings (e.g., `"0930-1600"`) work only with `time()`, `time_close()`, and `input.session()`. For `request.security()`, use named sessions via `ticker.modify()` or `ticker.new()`.

---

## 4. Cross-Market Data Alignment (CRITICAL)

### The Fundamental Rule

> **Data alignment follows the CHART symbol's time axis, NOT the requested symbol's native timeframe.**

When using `request.security()` to fetch data for a symbol from a different exchange:
- New data values only appear when the **chart symbol** has new data
- If the chart symbol's market is closed, NO new data arrives — even if the requested symbol's market is open

### Example: The Indian Stock Problem

```
Chart symbol: NSE:RELIANCE (Indian stock, trades 09:15-15:30 IST)
Requested symbol: BINANCE:BTCUSDT (crypto, trades 24/7)

Result: BTCUSDT data will ONLY update during NSE market hours (09:15-15:30 IST)
Outside NSE hours: BTCUSDT data is STALE (returns last known value with gaps_off, or na with gaps_on)
```

### The Screener Implication

For a multi-symbol screener that monitors symbols from different exchanges:

1. **The chart symbol determines when the script executes**
2. **No ticks = no script execution = no alerts**
3. **If chart is on a US stock, Indian stock data only updates during US market hours overlap with Indian market hours**

**US Market Hours**: 09:30-16:00 ET (14:00-20:30 UTC)
**Indian Market Hours**: 09:15-15:30 IST (03:45-10:00 UTC)
**Overlap**: Only ~0-30 minutes depending on DST

This means if the chart symbol is a US stock, Indian stock data is almost never fresh — and alerts for Indian stocks will almost never fire.

### Solutions for Cross-Market Screeners

**Solution 1: Use a 24/7 Chart Symbol**
```pinescript
// Chart symbol should be crypto (24/7) so script always executes
// Example: Set chart to BINANCE:BTCUSDT, then request.security() for all other symbols
// This ensures the script runs continuously and can detect signals for any market
```

**Solution 2: Separate Alerts Per Market**
```
// Create separate alerts for each market group:
// Alert 1: Chart=NSE:NIFTY50 → monitors Indian stocks only
// Alert 2: Chart=NASDAQ:QQQ → monitors US stocks only
// Alert 3: Chart=BINANCE:BTCUSDT → monitors crypto only
```

**Solution 3: Category-Aware Chart Symbol Selection**
```
// In the TTE automation, when creating alerts:
// For Indian stock pairs → set chart to an Indian stock symbol
// For US stock pairs → set chart to a US stock symbol
// For crypto pairs → set chart to a crypto symbol
// This ensures the chart symbol and requested symbols share market hours
```

### Gaps Parameter Behavior

| `gaps` Setting | Chart Symbol Market Open | Chart Symbol Market Closed |
|----------------|--------------------------|---------------------------|
| `barmerge.gaps_off` (default) | Latest value from requested symbol | **Last known value** (stale!) |
| `barmerge.gaps_on` | Latest value from requested symbol | `na` |

**For screeners**: `gaps_off` is dangerous because stale data looks like valid data. Consider using `gaps_on` and checking for `na` to detect when data is not fresh.

---

## 5. Alert Timing and Market Hours

### When Alerts Fire

1. Alerts **only fire on realtime bars** (never historical)
2. Realtime bars only form when **new price updates (ticks) arrive**
3. **No ticks in a closed market** → no script execution → no alerts
4. "There are no price updates in a closed market, meaning an alert will not fire until the market opens again"

### Alert Frequency Options

| Frequency | Behavior | Repainting Risk |
|-----------|----------|-----------------|
| `alert.freq_once_per_bar_close` | Fires when realtime bar closes with active alert() call | **None** |
| `alert.freq_once_per_bar` | First time condition is true per realtime bar | **High** |
| `alert.freq_all` | Every tick while condition true | **Extreme** + rate limit |

### Rate Limiting

- **15 alerts per 3 minutes** per script (rolling window)
- Exceeding this causes the system to **HALT** further alerts
- Prevention: Signal change detection (only alert when signal state changes)

### Alert Snapshots

When an alert is created in TradingView's UI:
- TradingView saves a **mirror image** of the script + inputs
- Subsequent changes to script code or inputs do NOT affect running alerts
- **Must delete and recreate alerts** after any script modification

---

## 6. Timeframe String Reference

### Format
Multiplier + Unit letter. Minutes have NO letter.

| Unit | Letter | Valid Multipliers | Examples |
|------|--------|-------------------|----------|
| Ticks | `T` | 1, 10, 100, 1000 | `"1T"`, `"100T"` |
| Seconds | `S` | 1, 5, 10, 15, 30, 45 | `"45S"`, `"15S"` |
| Minutes | (none) | 1-1440 | `"1"`, `"60"`, `"240"` |
| Days | `D` | 1-365 | `"1D"`, `"5D"` |
| Weeks | `W` | 1-52 | `"1W"` |
| Months | `M` | 1-12 | `"1M"`, `"3M"` |

**Common mistake**: `"1H"` is INVALID. Use `"60"` for 1 hour, `"240"` for 4 hours.

### Comparing Timeframes

```pinescript
// Convert to seconds for comparison
int chartTfSecs = timeframe.in_seconds(timeframe.period)
int htfSecs = timeframe.in_seconds("240")  // 4H = 14400 seconds

bool isHTF = htfSecs > chartTfSecs
```

---

## 7. request.security() and Sessions

### Key Parameters

```pinescript
request.security(symbol, timeframe, expression, gaps, lookahead, ignore_invalid_symbol, currency, calc_bars_count)
```

### Cross-Session Behavior

- Data alignment follows chart's time axis
- `gaps = barmerge.gaps_off` (default): Returns last confirmed value when no new data
- `gaps = barmerge.gaps_on`: Returns `na` when no new data from requested context
- `ignore_invalid_symbol = true`: Returns `na` for invalid symbols instead of runtime error

### Limits
- Max **40** unique `request.*()` calls per script (64 with Ultimate plan)
- Redundant calls with identical arguments reuse cached data

### Pine v6 Dynamic Requests
- Series arguments for symbol/timeframe (can change per bar)
- `request.security()` calls inside loops and conditionals
- All datasets must be requested on historical bars; realtime bars can only access previously-loaded contexts

---

## 8. Staleness Detection Patterns

### Pattern 1: Time-Based Staleness

```pinescript
// Check if data is stale (market closed, no recent ticks)
// Compare bar time to current time
int barAge = timenow - time  // WARNING: timenow causes repainting
bool isStale = barAge > MS_PER_HOUR * 2  // Stale if >2 hours old

// Better: Check if bar time matches expected interval
int expectedInterval = timeframe.in_seconds(timeframe.period) * 1000
int actualInterval = time - time[1]
bool hasGap = actualInterval > expectedInterval * 3  // Gap if >3x expected
```

### Pattern 2: Session-Based Staleness

```pinescript
// Check if requested symbol is in its trading session
// Only works for the CHART symbol's session context
bool inMarketHours = session.ismarket  // ALWAYS true on daily+ timeframes

// For checking a SPECIFIC session time
bool inIndianHours = not na(time(timeframe.period, "0915-1530", "Asia/Kolkata"))
bool inUSHours = not na(time(timeframe.period, "0930-1600", "America/New_York"))
```

### Pattern 3: Data Freshness via Gaps

```pinescript
// Use gaps_on to detect when data is not fresh
float dataWithGaps = request.security(symbol, tf, close[1],
    gaps = barmerge.gaps_on,
    lookahead = barmerge.lookahead_on)

bool dataIsFresh = not na(dataWithGaps)
```

---

## 9. Overnight and Multi-Day Sessions

### The `time_tradingday` Variable

For symbols with overnight sessions (futures, forex):
- `time` (bar open) may show the **previous calendar day**
- `time_tradingday` always shows the **actual trading day**
- Always use `time_tradingday` with `"UTC"` timezone since it returns 00:00 UTC

```pinescript
// WRONG: May show wrong day for overnight sessions
int day = dayofmonth(time)

// CORRECT: Shows actual trading day
int tradingDay = dayofmonth(time_tradingday, "UTC")
```

### Detecting New Trading Days

```pinescript
// Reliable new-day detection (works with overnight sessions)
bool newDay = ta.change(time("D")) > 0
bool newWeek = ta.change(time("W")) > 0
bool newMonth = ta.change(time("M")) > 0
```
