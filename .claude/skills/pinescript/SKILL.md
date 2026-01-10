---
name: pine-script-expert
description: Use when working with Pine Script code - indicators, strategies, screeners, or TradingView scripting. Applies to writing, debugging, optimizing, or explaining Pine Script.
allowed-tools: Read, Grep, Glob, WebFetch, Edit, Write, Bash
---

# Pine Script Development Skill

You are an expert Pine Script v6 developer. Apply these guidelines when working on any Pine Script task.

## Critical Rules

### Always Use Pine Script v6 Syntax
- Use `indicator()` not `study()`
- Use `strategy()` with v6 parameters
- Use `ta.sma()`, `ta.ema()`, `ta.rsi()` (not `sma()`, `ema()`, `rsi()`)
- Use `request.security()` not `security()`
- Use `str.tostring()` not `tostring()`
- Use `math.abs()`, `math.round()` etc. (not `abs()`, `round()`)

### Non-Repainting Code is Mandatory
All code must be non-repainting for reliable alerts. Follow these patterns:

```pinescript
// ALWAYS use [1] offset with barstate.isconfirmed for conditions
if condition[1] and barstate.isconfirmed
    alert(message, alert.freq_once_per_bar_close)

// ALWAYS use lookahead_on WITH [1] offset for request.security()
htf_close = request.security(symbol, "D", close[1], lookahead = barmerge.lookahead_on)

// NEVER use timenow - it causes repainting
// NEVER use request.security() without [1] offset when lookahead is on
```

### History Reference Operator []
- Only use `[]` in global scope for reliable results
- In local scopes (functions, if blocks, loops), history buffers may be fragmented
- If you need historical values in functions, pass them as parameters
- History buffers store up to 5,000 bars by default; use `max_bars_back()` for more
- Attempting to reference beyond buffer limits causes runtime errors

## Execution Model

### Bar-by-Bar Processing
- Scripts execute once per historical bar, **multiple times** per realtime bar
- Built-in variables (`open`, `high`, `low`, `close`, `volume`) update before each execution
- Only values from a bar's closing tick become part of the time series

### Variable Declaration Modes
| Keyword | Behavior |
|---------|----------|
| (none) | Reinitializes on every bar |
| `var` | Persists across bars, declared once |
| `varip` | Persists across all ticks within realtime bars (survives rollback) |

### Rollback Mechanism
Before each realtime bar update, non-`varip` variables revert to their last committed state.

**Survives rollback:** `varip` variables, Pine Logs, strategy orders, alert logs
**Does NOT survive:** `var` variables (revert to previous bar), plot outputs, objects without `varip`

### Script Reload Events
Scripts re-execute from bar 0 when:
- User saves edits or changes inputs
- Chart symbol/timeframe changes
- Chart refreshes
- Pine Logs pane opens/closes

**Critical:** Previously-realtime bars become historical on reload, causing potential repainting if realtime-only data was used.

## Function Limitations

Functions **CANNOT**:
- Modify global variables or parameters (read-only access)
- Call themselves (no recursion)
- Be defined inside other functions
- Call `plot()`, `plotshape()`, `label.new()`, `alertcondition()`, `indicator()`, `strategy()`
- Return inconsistent types across executions

Functions **CAN**:
- Access global variables declared before their definition
- Return tuples for multiple values
- Use default parameter values

## Collection Limits

| Collection | Max Elements |
|------------|--------------|
| Arrays | 100,000 |
| Matrices | 100,000 (rows × columns) |

## Fetching Documentation

When you need official Pine Script documentation or are unsure about syntax:

1. Fetch the Pine Script v6 reference: `https://www.tradingview.com/pine-script-reference/v6/`
2. For the language manual: `https://www.tradingview.com/pine-script-docs/language/`

## TTE Project Context

This project has specific indicators located in `Pine Script Code/`. Reference these when modifying or building on existing logic.

### Project Indicators

| Indicator | File | Version | Purpose |
|-----------|------|---------|---------|
| **Premium Screener** | `TTE Screener.txt` | v5 | Multi-symbol scanner (up to 20 symbols) using `request.security()`. Generates JSON alerts for the Python backend. |
| **OB & FVG** | `OB & FVG.txt` | v6 | Order Block and Fair Value Gap detection. Tracks institutional supply/demand zones, liquidity sweeps, breakers. Uses UDTs and arrays extensively. |
| **Kernel AO Divergence** | `Kenel AO Divergence.txt` | v5 | Divergence detection using kernel AO oscillator. Draws swing highs/lows, range shifts, Nadaraya-Watson kernel line. Uses external libraries. |
| **Multi Oscillator Swing** | `Multi Oscillator_swing high low.txt` | v5 | Swing high/low detection with selectable oscillators (AO, MACD 4C, RSI, Kernel AO). Includes same-side divergence logic. |
| **Nadaraya Watson Envelope** | `Nadaraya Watson Envelope.txt` | v5 | Non-parametric regression envelope using Rational Quadratic kernel. ATR-based upper/lower bounds for overbought/oversold zones. |

### External Libraries Used
Several indicators import external Pine Script libraries:
- `jdehorty/MLExtensions/2` - Machine learning extensions
- `jdehorty/KernelFunctions/2` - Kernel functions (Rational Quadratic, Gaussian)
- `sammie123567858/AoDivergenceLibrary_/5` - AO divergence detection

### Alert Message Format
Alerts should output JSON that the Python backend can parse:
```pinescript
alertMsg = '{"symbol":"' + syminfo.ticker + '","direction":"' + direction + '","entry":' + str.tostring(entryPrice) + '}'
alert(alertMsg, alert.freq_once_per_bar_close)
```

## Alert Rules

### Execution Constraints
- **Alerts only fire on realtime bars** - historical bars never trigger alerts
- When an alert is created in the UI, TradingView saves a snapshot of the script - subsequent edits don't affect existing alerts

### Frequency Options
| Frequency | When It Fires |
|-----------|---------------|
| `alert.freq_once_per_bar` | First call per realtime bar (default) |
| `alert.freq_once_per_bar_close` | Only when realtime bar closes (prevents repainting) |
| `alert.freq_all` | Every call during the realtime bar |

### alert() vs alertcondition()
- **`alert()`**: Dynamic messages, works in indicators and strategies, preferred
- **`alertcondition()`**: Legacy, constant messages only, indicators only, creates selectable conditions in UI

## request.security() Best Practices

### Parameter Summary
```pinescript
request.security(symbol, timeframe, expression, gaps, lookahead, ignore_invalid_symbol)
```

### Gaps Parameter
| Mode | Historical Bars | Realtime Bars |
|------|-----------------|---------------|
| `barmerge.gaps_off` (default) | Last confirmed value | Current unconfirmed value |
| `barmerge.gaps_on` | `na` when no data | `na` when no data |

### Non-Repainting Wrapper (ALWAYS USE)
```pinescript
noRepaintSecurity(sym, tf, expr) =>
    request.security(sym, tf, expr[1], lookahead = barmerge.lookahead_on)
```
Both `[1]` offset AND `lookahead_on` are required together - neither works alone.

### Limits
- Max 40 unique `request.*()` calls per script (64 with Ultimate plan)
- Redundant calls with identical arguments reuse cached data

## All Repainting Causes

| Cause | Why It Repaints | Solution |
|-------|-----------------|----------|
| `close`, `high`, `low` in realtime | Values fluctuate until bar closes | Use `[1]` offset or `barstate.isconfirmed` |
| `request.security()` without offset | Returns unconfirmed values in realtime | Use wrapper with `[1]` + `lookahead_on` |
| `lookahead_on` without `[1]` | Leaks future data into historical bars | Always pair with `[1]` offset |
| `timenow` | Returns current execution time | Avoid entirely |
| `varip` variables | Stores intrabar data unavailable historically | Accept or avoid for alerts |
| `barstate.isnew` | Triggers at open (realtime) vs close (historical) | Use `barstate.isconfirmed` instead |
| `calc_on_every_tick = true` | Strategy executes differently in realtime | Use default (false) for backtesting |
| Plotting into the past | Pivots detected N bars late, plotted back | Make it optional with clear documentation |
| Lower timeframe `request.security()` | Intrabars not sorted in realtime | Use `request.security_lower_tf()` |

## Time Handling

### Key Variables
| Variable | Returns | Timezone |
|----------|---------|----------|
| `time` | Bar opening timestamp (ms) | UTC |
| `time_close` | Bar closing timestamp (ms) | UTC |
| `timenow` | Current execution time | UTC (causes repainting!) |
| `year`, `month`, `hour`, etc. | Calendar values | Exchange timezone |

### Time Formatting
```pinescript
// Use str.format_time() for timestamps
str.format_time(time, "yyyy-MM-dd HH:mm:ss", syminfo.timezone)

// NEVER use str.format() for time - it always uses UTC+0
```

### Timezone Best Practices
- Use IANA identifiers (e.g., `"America/New_York"`) for automatic DST handling
- UTC offset notation (e.g., `"UTC-4"`) uses fixed offsets, won't adjust for DST
- `syminfo.timezone` returns the exchange's IANA timezone

### Time Difference Calculation
**NEVER** use `str.format_time()` for time differences - use modular arithmetic:
```pinescript
// Milliseconds per unit
MS_PER_HOUR = 3600000
MS_PER_DAY = 86400000

elapsed_hours = (time2 - time1) / MS_PER_HOUR
```

## Common Mistakes to Avoid

1. **Forgetting `var` for persistent variables**
   ```pinescript
   // WRONG - resets every bar
   array<string> signals = array.new_string(0)

   // CORRECT - persists across bars
   var array<string> signals = array.new_string(0)
   ```

2. **Using lookahead without offset**
   ```pinescript
   // WRONG - will show future data on historical bars
   htf = request.security(sym, "D", close, lookahead = barmerge.lookahead_on)

   // CORRECT
   htf = request.security(sym, "D", close[1], lookahead = barmerge.lookahead_on)
   ```

3. **Modifying arrays in request.security()**
   - Cannot use `array.push()` inside security expressions
   - Return primitives/tuples, then handle arrays in global scope

4. **Plotting from functions**
   - `plot()`, `plotshape()`, `label.new()` cannot be called from functions
   - Return values and plot in global scope

5. **Type mismatches in conditionals**
   ```pinescript
   // WRONG - inconsistent return types
   result = condition ? 1.0 : na  // na is not float

   // CORRECT
   result = condition ? 1.0 : float(na)
   ```

6. **Calling array methods on `na`**
   ```pinescript
   // WRONG - will error
   var array<float> arr = na
   array.push(arr, 1.0)  // Error!

   // CORRECT
   var array<float> arr = array.new<float>(0)
   array.push(arr, 1.0)
   ```

7. **Using `barstate.isnew` for confirmed signals**
   ```pinescript
   // WRONG - triggers at bar open (realtime) but bar close (historical)
   if barstate.isnew and condition
       alert(msg)

   // CORRECT - consistent behavior
   if barstate.isconfirmed and condition[1]
       alert(msg, alert.freq_once_per_bar_close)
   ```

8. **History reference in conditionally-called functions**
   ```pinescript
   // WRONG - fragmented history buffer
   myFunc() =>
       close[1]  // May reference wrong bar if function not called every bar

   if someCondition
       myFunc()

   // CORRECT - pass historical values as parameters
   myFunc(prevClose) =>
       prevClose

   if someCondition
       myFunc(close[1])
   ```

9. **Modifying globals from functions**
   ```pinescript
   var int counter = 0

   // WRONG - cannot modify global
   incrementCounter() =>
       counter := counter + 1  // Error!

   // CORRECT - return value and assign in global scope
   getIncrement(val) =>
       val + 1

   counter := getIncrement(counter)
   ```

10. **Objects assigned by reference**
    ```pinescript
    type Point
        float x
        float y

    p1 = Point.new(1.0, 2.0)
    p2 = p1          // p2 points to SAME object as p1
    p2.x := 5.0      // This also changes p1.x!

    // CORRECT - use .copy() for independent copy
    p2 = p1.copy()
    p2.x := 5.0      // p1.x unchanged
    ```

## Performance Guidelines

For screeners with multiple symbols:
1. Minimize logic inside `request.security()` expressions
2. Return tuples of primitives, not objects
3. Calculate shared values once in global scope
4. Test performance with target symbol count
5. Each `request.security()` call adds ~50-100ms overhead

## Code Review Checklist

Before finalizing any Pine Script code, verify:
- [ ] Uses v6 syntax throughout
- [ ] No repainting issues (barstate.isconfirmed, [1] offsets)
- [ ] `request.security()` uses lookahead_on with [1] offset
- [ ] Persistent variables use `var` keyword
- [ ] Arrays/objects properly initialized
- [ ] Alert frequency set to `alert.freq_once_per_bar_close`
- [ ] No `timenow` usage
- [ ] Functions don't try to plot or modify globals
