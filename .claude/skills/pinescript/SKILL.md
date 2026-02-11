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
All code must be non-repainting for reliable alerts. Follow these patterns (see "Alerts and Webhooks" section for alert-specific repainting prevention):

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

**Survives rollback:** `varip` variables, Pine Logs, strategy orders, alert logs (alerts fire even if condition becomes false later on same bar - see "Alerts and Webhooks")
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
| **Premium Screener** | `TTE Screener.txt` | v5 | Multi-symbol scanner (up to 4 symbols per alert, 3 in production) using `request.security()`. Generates JSON alerts for the Python backend. |
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

TTE screeners output structured JSON that the Python backend (or Stock Buddy API in tiered mode) can parse. The project uses a hierarchical pattern where details are added based on signal strength.

**Production pattern from TTE Screener.txt (line 1190)**:

```pinescript
// Build JSON alert message for Python backend
// Format: {"symbol":"XXX","signal":"BUY","level":3,"details":"NWE:H4,D1 OB:W1 DIV:H4"}
buildAlertMsg(string sym, string signal, int level, string details) =>
    '{"symbol":"' + sym +
     '","signal":"' + signal +
     '","level":' + str.tostring(level) +
     ',"details":"' + details + '"}'
```

**Usage in screener with signal change detection (lines 1237-1249)**:

```pinescript
if barstate.isconfirmed
    // Only alert when signal changes from previous bar
    if buyLvl01 != prevBuyLvl01 or sellLvl01 != prevSellLvl01
        bool isBuy = buyLvl01 >= sellLvl01 and buyLvl01 > 0
        int lvl = isBuy ? buyLvl01 : sellLvl01

        if lvl > 0
            string sig = isBuy ? "BUY" : "SELL"

            // Level 1: NWE only
            string det = "NWE:" + buildNweDetail(nweBull01_h4, nweBull01_d1)

            // Level 2: NWE + OB/FVG
            if lvl >= 2
                det := det + " OB:" + buildObDetail(bullF01_h4, bullF01_d1, bullF01_w1)

            // Level 3: NWE + OB/FVG + Divergence
            if lvl == 3
                det := det + " DIV:" + buildDivDetail(divBullTm01_h4, intBullTm01_h4, divBullTm01_d1, intBullTm01_d1, time)

            alert(buildAlertMsg(getSymbolName(s01), sig, lvl, det), alert.freq_once_per_bar_close)

        prevBuyLvl01 := buyLvl01
        prevSellLvl01 := sellLvl01
```

**Key patterns**:
- **Signal change detection**: Only alert when `buyLvl != prevBuyLvl` (prevents rate limiting)
- **Hierarchical details**: Build details string incrementally based on signal level
- **Non-repainting**: Uses `barstate.isconfirmed` guard
- **JSON structure**: Consistent format for backend parsing

See "Alerts and Webhooks" section below for comprehensive webhook integration patterns.

## Alerts and Webhooks

Alerts enable automated trading systems by triggering webhooks with structured data (JSON). Understanding alert execution constraints and webhook patterns is critical for building reliable signal distribution like TTE's tiered architecture.

**For deep technical reference**: See `references/alerts_and_webhooks.md` for comprehensive coverage of server-side execution, rate limiting, error handling, troubleshooting, and complete examples.

### Critical Constraints

**1. Server-Side Execution**
- Scripts run on TradingView's cloud servers (not your computer)
- Alerts continue firing after you close your browser (server-side alerts)
- Resource limits enforced: 40 `request.security()` calls (64 with Ultimate), 500ms loop timeout

**2. Alert Snapshots**
- When you create an alert, TradingView captures a **snapshot** of your script
- Editing script code does NOT update existing alerts
- **You must delete and recreate alerts** after script changes
- This is why TTE's `START_FRESH` flag exists (deletes and recreates alerts)

**3. Rate Limiting**
- **Limit**: 15 alerts per 3 minutes per script (rolling window)
- Exceeded alerts are **delayed** (not dropped), causing late signal delivery
- **Solution**: Use signal change detection (only alert when signal changes, not every bar)
- See TTE screener pattern below for implementation

**4. Runtime Errors Stop Alerts**
- If script encounters runtime error, execution halts immediately
- Alert logic never executes, no alerts fire (silently fails)
- Common errors: array out of bounds, division by zero, na value arithmetic
- **Prevention**: Defensive coding with na checks, array size validation, safe arithmetic

**5. Realtime Bars Only**
- Alerts only fire on realtime bars (currently forming bars)
- Historical bars never trigger alerts (server can't retroactively notify)
- Use `barstate.isconfirmed` to fire at bar close (non-repainting)

### Alert Functions Comparison

| Feature | `alert()` | `alertcondition()` |
|---------|-----------|-------------------|
| **Message Type** | Series string (dynamic values) | Const string (compile-time only) |
| **Dynamic Values** | ✓ Any expression (`close`, `level`, etc.) | ✗ Placeholders only (`{{close}}`) |
| **Works In** | Indicators AND strategies | Indicators only |
| **Account Limit** | 1 alert per script (all `alert()` calls count as one) | Each `alertcondition()` counts separately |
| **Webhook JSON** | ✓ Full control over JSON structure | Limited (placeholders) |
| **TTE Convention** | **Always use `alert()`** | Not used |
| **UI Interaction** | Automatic (no UI needed) | Requires UI to select condition |

**Decision rule**: Always use `alert()` for webhook-based systems. Use `alertcondition()` only for legacy compatibility.

### Frequency Options

| Frequency | When Fires | Repainting Risk | Use Case |
|-----------|------------|-----------------|----------|
| `alert.freq_once_per_bar_close` | Bar close only | **None** (bar won't reopen) | ✓ **Recommended** - Non-repainting signals |
| `alert.freq_once_per_bar` | First time condition true per bar | **High** (bar can still repaint) | Time-sensitive signals (rare) |
| `alert.freq_all` | Every tick while condition true | **Extreme** + rate limit issues | High-frequency trading (very rare) |

**TTE convention**: Always use `alert.freq_once_per_bar_close` with `barstate.isconfirmed` guard.

**Timing relative to bar close**:
```pinescript
// Bar forming... → Condition becomes true → Bar closes → alert.freq_once_per_bar_close fires
if buyCondition and barstate.isconfirmed
    alert(buildAlertMsg(...), alert.freq_once_per_bar_close)
```

### Webhook Integration Patterns

#### JSON Message Format

Build JSON strings for webhook payloads:

```pinescript
// Basic pattern
buildJsonAlert(string symbol, string signal, float price, int level) =>
    // Validate inputs (prevent JSON corruption)
    if na(price) or na(level)
        runtime.error("Cannot build JSON with na values")

    // Build JSON string
    '{"symbol":"' + symbol +
     '","signal":"' + signal +
     '","price":' + str.tostring(price, '#.#####') +
     ',"level":' + str.tostring(level) +
     '"}'

// Usage
if signalChange and barstate.isconfirmed
    alert(buildJsonAlert(syminfo.ticker, "BUY", close, 1), alert.freq_once_per_bar_close)
```

**Key rules**:
- Always check for `na` values before building JSON
- Use `str.tostring()` with format specifiers (`'#.#####'` for decimals)
- Escape special characters in strings (quotes, backslashes)
- Validate JSON structure with online tools during development

#### TTE Project Pattern

TTE screeners use this proven pattern from `TTE Screener.txt`:

```pinescript
// Build JSON alert message for Python backend (line 1190)
// Format: {"symbol":"XXX","signal":"BUY","level":3,"details":"NWE:H4,D1 OB:W1 DIV:H4"}
buildAlertMsg(string sym, string signal, int level, string details) =>
    '{"symbol":"' + sym +
     '","signal":"' + signal +
     '","level":' + str.tostring(level) +
     ',"details":"' + details + '"}'

// Signal change detection with hierarchical details (lines 1237-1249)
if barstate.isconfirmed
    // Only alert if signal changed from previous bar (prevents rate limiting)
    if buyLvl01 != prevBuyLvl01 or sellLvl01 != prevSellLvl01
        bool isBuy = buyLvl01 >= sellLvl01 and buyLvl01 > 0
        int lvl = isBuy ? buyLvl01 : sellLvl01

        if lvl > 0
            string sig = isBuy ? "BUY" : "SELL"
            string det = "NWE:" + buildNweDetail(...)  // Level 1 details

            if lvl >= 2
                det := det + " OB:" + buildObDetail(...)  // Level 2 adds OB

            if lvl == 3
                det := det + " DIV:" + buildDivDetail(...)  // Level 3 adds divergence

            alert(buildAlertMsg(getSymbolName(s01), sig, lvl, det),
                  alert.freq_once_per_bar_close)

        prevBuyLvl01 := buyLvl01  // Update previous state
        prevSellLvl01 := sellLvl01
```

**Key patterns**:
1. **Signal change detection** - Compare current signal with previous bar (`buyLvl01 != prevBuyLvl01`)
2. **Rate limit prevention** - Only alert when signal changes, not every bar
3. **Hierarchical details** - Build details incrementally based on signal level
4. **Non-repainting** - Uses `barstate.isconfirmed` guard
5. **State tracking** - Store previous signal in `var` variables

#### Discord Webhook

Discord expects `{"content": "message"}` format:

```pinescript
discordWebhook(string content) =>
    '{"content":"' + content + '"}'

// Usage
if buySignal and barstate.isconfirmed
    alert(discordWebhook("🚀 BUY signal on " + syminfo.ticker),
          alert.freq_once_per_bar_close)
```

For rich embeds with colors and fields, see `references/alerts_and_webhooks.md` section 5.

### Error Handling for Alerts

**Problem**: Runtime errors silently stop all alerts until resolved.

**Solution**: Defensive validation before alert() call:

```pinescript
safeAlert(string symbol, string signal, float price, float level) =>
    // Validate ALL values before building message
    if na(price)
        log.error("Price is na, skipping alert")
        false
    else if na(level) or level <= 0
        log.error("Invalid level, skipping alert")
        false
    else
        // Safe to build JSON
        alert(buildJsonAlert(symbol, signal, price, level),
              alert.freq_once_per_bar_close)
        true

// Usage
if signalChange and barstate.isconfirmed
    bool success = safeAlert(syminfo.ticker, "BUY", close, calcLevel())
    if not success
        log.warning("Failed to send alert for " + syminfo.ticker)
```

### Multi-Symbol Screener Pattern

For screeners monitoring 5+ symbols without hitting rate limits:

```pinescript
// Track previous signals for change detection
var int prevS1Sig = 0
var int prevS2Sig = 0

if barstate.isconfirmed
    // Symbol 1 - only alert on change
    if s1_signal != prevS1Sig and s1_signal != 0
        alert(buildJsonAlert(symbol1, getSigText(s1_signal), close, s1_level),
              alert.freq_once_per_bar_close)
    prevS1Sig := s1_signal

    // Symbol 2 - only alert on change
    if s2_signal != prevS2Sig and s2_signal != 0
        alert(buildJsonAlert(symbol2, getSigText(s2_signal), close, s2_level),
              alert.freq_once_per_bar_close)
    prevS2Sig := s2_signal

    // ... repeat for all symbols
```

**Result**: Only new/changed signals trigger alerts (typically 0-3 per bar instead of 20).

### Cross-References

- **Non-Repainting Code**: Use [1] offset and `barstate.isconfirmed` for alerts (see "All Repainting Causes" below)
- **Execution Model**: Alert logs survive bar state rollback (logged even if condition later becomes false on same bar)
- **Code Review Checklist**: Verify alert rate limiting prevention, na validation, JSON structure

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

## Debugging Techniques

### Pine Logs (Primary Method)
Pine Logs are the recommended debugging tool. They work from any scope, support filtering, and provide interactive navigation.

```pinescript
// Three severity levels with distinct colors
log.info("Value: {0,number,#.####}", someFloat)    // Gray - general info
log.warning("Condition triggered at bar {0}", bar_index)  // Orange - warnings
log.error("Division by zero detected")              // Red - errors

// Multiple values in one log
log.info("open: {0}, high: {1}, low: {2}, close: {3}", open, high, low, close)
```

**Key characteristics:**
- Work from global AND local scopes (unlike plot functions)
- Survive rollback (logs persist even when realtime bar reverts)
- Support filtering by level, date range, and regex patterns
- Click logs to navigate to source code or chart location
- Store ~10,000 historical logs maximum

**Limitations:**
- Only personal scripts can use Pine Logs (published scripts cannot)
- Opening/closing Pine Logs pane triggers full script reload

**Prevent log spam on realtime bars:**
```pinescript
if barstate.isconfirmed
    log.info("Bar {0} confirmed: close={1}", bar_index, close)
```

### Labels for Visual Debugging
Labels display text directly on the chart with tooltips for detailed info.

```pinescript
// Simple debug label
label.new(bar_index, high, "Debug: " + str.tostring(value))

// With tooltip for detailed data (hover to see)
label.new(bar_index, high, "!", tooltip =
    "close: " + str.tostring(close) +
    "\nvolume: " + str.tostring(volume))

// Force overlay on non-overlay indicators
label.new(bar_index, high, "Signal", force_overlay = true)
```

**Restrict to visible chart range (for earlier bar debugging):**
```pinescript
if time >= chart.left_visible_bar_time and time <= chart.right_visible_bar_time
    label.new(bar_index, high, "Visible range debug")
```

**Limitations:** Max 500 labels per script; oldest removed when exceeded.

### Tables for Fixed-Position Display
Tables stay in one screen position - ideal for summary info.

```pinescript
// Create table once with var
var table debugTable = table.new(position.top_right, 2, 5, bgcolor = color.black)

// Update on last bar only
if barstate.islast
    table.cell(debugTable, 0, 0, "Variable", text_color = color.white)
    table.cell(debugTable, 1, 0, str.tostring(myVar), text_color = color.yellow)
    table.cell(debugTable, 0, 1, "Condition", text_color = color.white)
    table.cell(debugTable, 1, 1, str.tostring(myCondition), text_color = color.green)
```

### Plot Functions for Series Debugging
Plots show values in chart pane, status line, Data Window, and price scale.

```pinescript
// Basic series plot
plot(debugValue, "Debug Value", color.orange, 2)

// Plot condition as 1/0
plot(condition ? 1 : 0, "Condition Active")

// Exclude from chart pane (show only in Data Window)
plot(value, "Hidden Debug", display = display.data_window)

// Visual condition markers
plotshape(condition, "Event", shape.circle, location.top, color.red)
bgcolor(condition ? color.new(color.red, 80) : na)
```

**Limitations:** Max 64 plots per script; cannot access local scope data.

### Decomposing Complex Expressions
Break apart nested expressions to inspect intermediate values:

```pinescript
// BEFORE - hard to debug
float result = ta.ema(math.avg(ta.change(diff1), ta.change(diff2)), length)

// AFTER - each step visible
float change1 = ta.change(diff1)
float change2 = ta.change(diff2)
float avgChange = math.avg(change1, change2)
float result = ta.ema(avgChange, length)

log.info("change1: {0}, change2: {1}, avg: {2}, result: {3}",
    change1, change2, avgChange, result)
```

### Extracting Local Scope Data
Functions cannot call `plot()` or `log.*()`. Extract data via returns or reference types.

**Method 1: Tuple returns**
```pinescript
myFunction() =>
    localValue1 = someCalculation()
    localValue2 = anotherCalculation()
    result = localValue1 + localValue2
    [result, localValue1, localValue2]  // Return debug values too

[output, dbg1, dbg2] = myFunction()
plot(dbg1, "Debug Local 1")
plot(dbg2, "Debug Local 2")
```

**Method 2: Reference type (map/array) updates**
```pinescript
var map<string, float> debugData = map.new<string, float>()

myFunction() =>
    value1 = calculate()
    debugData.put("value1", value1)  // Functions CAN modify reference type contents
    value2 = calculate()
    debugData.put("value2", value2)
    value1 + value2

result = myFunction()
log.info("value1: {0}, value2: {1}", debugData.get("value1"), debugData.get("value2"))
```

### Debugging Collections

**Arrays and matrices:**
```pinescript
log.info("Array: {0}", str.tostring(myArray))
log.info("Size: {0}, First: {1}, Last: {2}",
    array.size(myArray), array.first(myArray), array.last(myArray))

// Iterate with index
for [index, element] in myArray
    log.info("Index {0}: {1,number,#.####}", index, element)
```

**Inspect all labels/lines/boxes:**
```pinescript
if barstate.islast
    for [i, lbl] in label.all
        log.info("Label {0}: x={1}, y={2}, text={3}",
            i, lbl.get_x(), lbl.get_y(), lbl.get_text())
```

### Debugging Loops

```pinescript
log.warning("=== LOOP START ===")
for i = 1 to length
    value = calculate(i)
    log.info("Iteration {0}: value={1,number,#.####}", i, value)
    if skipCondition
        log.warning("CONTINUE triggered at {0}", i)
        continue
    result += value
log.warning("=== LOOP END: result={0} ===", result)
```

### Debugging User-Defined Types

```pinescript
type MyData
    array<float> values
    float threshold
    int counter

var MyData data = MyData.new(array.new<float>(), 0.5, 0)

// Log individual fields
log.info("threshold: {0}, counter: {1}, values: {2}",
    data.threshold, data.counter, str.tostring(data.values))

// Plot numeric fields
plot(data.threshold, "Threshold")
plot(array.size(data.values), "Values Count")
```

### String Formatting Reference

```pinescript
// Number formatting
log.info("Integer: {0,number,#}", intValue)           // No decimals
log.info("Float: {0,number,#.####}", floatValue)      // 4 decimals
log.info("Float: {0,number,#.########}", floatValue)  // 8 decimals (max precision)

// Multi-line output
log.info("Line1: {0}\nLine2: {1}\nLine3: {2}", val1, val2, val3)

// Conditional string building
string status = condition ? "ACTIVE" : "INACTIVE"
log.info("Status: {0}", status)
```

### Custom Debug Filtering

```pinescript
var bool debugEnabled = input.bool(true, "Enable Debug Logs")
var int debugStartTime = input.time(0, "Debug Start Time")
var int debugEndTime = input.time(0, "Debug End Time")

shouldLog() =>
    if not debugEnabled
        false
    else if debugStartTime == 0 and debugEndTime == 0
        true
    else
        time >= debugStartTime and time <= debugEndTime

if shouldLog() and barstate.isconfirmed
    log.info("Debug: {0}", someValue)
```

### Debugging Best Practices

1. **Use Pine Logs as primary tool** - most flexible, works everywhere
2. **Always guard with `barstate.isconfirmed`** - prevents log spam on realtime ticks
3. **Decompose complex expressions** - inspect each calculation step
4. **Use tables for summary data** - fixed position, doesn't clutter chart
5. **Use labels with tooltips** - hover for details without visual clutter
6. **Extract local scope data via returns** - functions can't log directly
7. **Filter logs by time range** - focus on specific bars
8. **Use severity levels meaningfully** - info for data, warning for flow, error for problems
9. **Remember Pine Logs survive rollback** - realtime logs persist even when bar reverts
10. **Clean up debug code before publishing** - Pine Logs don't work in published scripts

## Code Review Checklist

Before finalizing any Pine Script code, verify:

**General**:
- [ ] Uses v6 syntax throughout
- [ ] No repainting issues (barstate.isconfirmed, [1] offsets)
- [ ] `request.security()` uses lookahead_on with [1] offset
- [ ] Persistent variables use `var` keyword
- [ ] Arrays/objects properly initialized
- [ ] No `timenow` usage
- [ ] Functions don't try to plot or modify globals
- [ ] Debug code removed or disabled before publishing

**Alert-Specific** (if script uses alerts):
- [ ] Alert frequency set to `alert.freq_once_per_bar_close`
- [ ] Uses `barstate.isconfirmed` guard before alert() calls
- [ ] Signal change detection implemented (prevents rate limiting)
- [ ] All values validated for na before building JSON
- [ ] JSON structure validated (test with online validator)
- [ ] String values properly escaped in JSON (quotes, backslashes)
- [ ] Error handling prevents runtime errors from stopping alerts
- [ ] Multi-symbol screeners stay under request.security() limit (40 or 64)
