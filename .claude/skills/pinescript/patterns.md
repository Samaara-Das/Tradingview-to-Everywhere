# Pine Script Patterns for TTE

Common patterns used in this project's indicators.

## Non-Repainting Alert Pattern

```pinescript
//@version=6
indicator("Alert Example", overlay=true)

// Your condition logic
buyCondition = ta.crossover(ta.sma(close, 10), ta.sma(close, 20))

// Non-repainting alert - uses [1] and barstate.isconfirmed
if buyCondition[1] and barstate.isconfirmed
    alertMsg = '{"symbol":"' + syminfo.ticker + '","direction":"Buy","price":' + str.tostring(close) + '}'
    alert(alertMsg, alert.freq_once_per_bar_close)
```

## Multi-Symbol Screener Pattern

```pinescript
//@version=6
indicator("Screener", overlay=true)

// Input symbols
sym1 = input.symbol("EURUSD", "Symbol 1")
sym2 = input.symbol("GBPUSD", "Symbol 2")

// Function to check condition (returns tuple of primitives)
checkSignal(src, len) =>
    smaVal = ta.sma(src, len)
    signal = ta.crossover(src, smaVal)
    [signal, smaVal]

// Get data from each symbol - ALWAYS use [1] with lookahead_on
[sig1, sma1] = request.security(sym1, timeframe.period, checkSignal(close[1], 20), lookahead=barmerge.lookahead_on)
[sig2, sma2] = request.security(sym2, timeframe.period, checkSignal(close[1], 20), lookahead=barmerge.lookahead_on)

// Collect signals in global scope (not inside request.security)
var array<string> signals = array.new_string(0)

if barstate.isconfirmed
    array.clear(signals)
    if sig1
        array.push(signals, sym1)
    if sig2
        array.push(signals, sym2)

    if array.size(signals) > 0
        alert(array.join(signals, ","), alert.freq_once_per_bar_close)
```

## User-Defined Type for Trade Signals

```pinescript
//@version=6
indicator("Trade Signal UDT", overlay=true)

type TradeSignal
    string symbol
    string direction
    float entryPrice
    float slPrice
    float tp1Price
    float tp2Price
    float tp3Price
    int barTime

// Create a signal
createSignal(sym, dir, entry, sl, tp1, tp2, tp3) =>
    TradeSignal.new(sym, dir, entry, sl, tp1, tp2, tp3, time)

// Usage
if buyCondition[1] and barstate.isconfirmed
    signal = createSignal(syminfo.ticker, "Buy", close, low[1], close * 1.01, close * 1.02, close * 1.03)

    // Convert to JSON for alert
    alertMsg = '{"symbol":"' + signal.symbol + '",' +
               '"direction":"' + signal.direction + '",' +
               '"entry":' + str.tostring(signal.entryPrice) + ',' +
               '"sl":' + str.tostring(signal.slPrice) + ',' +
               '"tp1":' + str.tostring(signal.tp1Price) + '}'
    alert(alertMsg, alert.freq_once_per_bar_close)
```

## Higher Timeframe Data Pattern

```pinescript
//@version=6
indicator("HTF Data", overlay=true)

htfTimeframe = input.timeframe("D", "Higher Timeframe")

// CORRECT: Non-repainting HTF data
htfClose = request.security(syminfo.tickerid, htfTimeframe, close[1], lookahead=barmerge.lookahead_on)
htfHigh = request.security(syminfo.tickerid, htfTimeframe, high[1], lookahead=barmerge.lookahead_on)
htfLow = request.security(syminfo.tickerid, htfTimeframe, low[1], lookahead=barmerge.lookahead_on)

plot(htfClose, "HTF Close", color=color.blue)
```

## Swing High/Low Detection

```pinescript
//@version=6
indicator("Swing Points", overlay=true)

swingLen = input.int(5, "Swing Length")

// Detect swing high - confirmed pivot
swingHigh = ta.pivothigh(high, swingLen, swingLen)
swingLow = ta.pivotlow(low, swingLen, swingLen)

// Note: pivots are detected swingLen bars AFTER they occur
// So swingHigh is the high value from swingLen bars ago when confirmed

if not na(swingHigh)
    label.new(bar_index - swingLen, swingHigh, "SH", style=label.style_label_down)

if not na(swingLow)
    label.new(bar_index - swingLen, swingLow, "SL", style=label.style_label_up)
```

## Persistent State with var

```pinescript
//@version=6
indicator("Persistent State", overlay=true)

// These persist across bars
var float lastEntryPrice = na
var string currentPosition = "none"
var int entryBar = na

// This resets every bar
float tempCalc = close - open

// Update persistent state
if buyCondition[1] and barstate.isconfirmed and currentPosition == "none"
    lastEntryPrice := close
    currentPosition := "long"
    entryBar := bar_index

if sellCondition[1] and barstate.isconfirmed and currentPosition == "long"
    currentPosition := "none"
```

## Time Formatting for Alerts

```pinescript
//@version=6
indicator("Time Format", overlay=true)

// Format current bar time
timeStr = str.format_time(time, "yyyy-MM-dd HH:mm", syminfo.timezone)

// For specific timezone
indiaTime = str.format_time(time, "HH:mm:ss dd-MM-yyyy", "Asia/Kolkata")

// Include in alert
alertMsg = '{"time":"' + timeStr + '","symbol":"' + syminfo.ticker + '"}'
```

## Non-Repainting request.security() Wrapper

```pinescript
//@version=6
indicator("Safe HTF", overlay=true)

// ALWAYS use this wrapper for request.security() to prevent repainting
// Both [1] offset AND lookahead_on are REQUIRED together
noRepaintSecurity(sym, tf, expr) =>
    request.security(sym, tf, expr[1], lookahead = barmerge.lookahead_on)

// Usage
htfClose = noRepaintSecurity(syminfo.tickerid, "D", close)
htfRsi = noRepaintSecurity(syminfo.tickerid, "D", ta.rsi(close, 14))

plot(htfClose, "Daily Close")
```

## Session Time Checking

```pinescript
//@version=6
indicator("Session Check", overlay=true)

// Check if current bar is within a specific session
// Uses exchange timezone by default
sessionActive = not na(time("", "0930-1600"))  // US market hours

// With specific timezone
londonSession = not na(time("", "0800-1630", "Europe/London"))

// Multiple sessions
asiaSession = not na(time("", "0900-1500", "Asia/Tokyo"))

bgcolor(sessionActive ? color.new(color.blue, 90) : na)
```

## Timeframe Change Detection

```pinescript
//@version=6
indicator("TF Change", overlay=true)

// Detect when a higher timeframe bar closes
// More reliable than using calendar functions
newDay = ta.change(time("D")) > 0
newWeek = ta.change(time("W")) > 0
newMonth = ta.change(time("M")) > 0

// Use for resetting daily calculations
var float dailyHigh = na
var float dailyLow = na

if newDay
    dailyHigh := high
    dailyLow := low
else
    dailyHigh := math.max(dailyHigh, high)
    dailyLow := math.min(dailyLow, low)
```

## Safe History Reference in Functions

```pinescript
//@version=6
indicator("Safe Function History", overlay=true)

// WRONG: Using [] inside conditionally-called function
// The history buffer becomes fragmented
badFunction() =>
    close[1]  // Unreliable if function not called every bar

// CORRECT: Pass historical values as parameters
// History reference happens in global scope, always consecutive
goodFunction(prevClose, prevHigh) =>
    (prevClose + prevHigh) / 2

// Call with pre-computed history values
result = goodFunction(close[1], high[1])
```

## Object Deep Copy Pattern

```pinescript
//@version=6
indicator("Deep Copy", overlay=true)

type Position
    string symbol
    float entry
    array<float> targets  // Reference type field

// Shallow copy - targets array is shared!
method shallowCopy(Position this) =>
    this.copy()

// Deep copy - independent targets array
method deepCopy(Position this) =>
    Position newPos = this.copy()
    newPos.targets := array.copy(this.targets)
    newPos

// Usage
var Position pos1 = Position.new("EURUSD", 1.05, array.from(1.06, 1.07, 1.08))
var Position pos2 = pos1.deepCopy()  // Truly independent copy
```

## varip for Intrabar Tracking

```pinescript
//@version=6
indicator("Intrabar Tracker", overlay=true)

// varip survives rollback - tracks data across ticks within a bar
// WARNING: This data is NOT available on historical bars (causes repainting)
varip int tickCount = 0
varip float intabarHigh = na
varip float intrabarLow = na

if barstate.isnew
    tickCount := 0
    intabarHigh := high
    intrabarLow := low
else
    tickCount += 1
    intabarHigh := math.max(intabarHigh, high)
    intrabarLow := math.min(intrabarLow, low)

// Only useful for realtime monitoring, NOT for backtesting
plot(tickCount, "Tick Count")
```

## Array Operations with Error Handling

```pinescript
//@version=6
indicator("Safe Arrays", overlay=true)

// Always initialize arrays properly (not with na)
var array<float> prices = array.new<float>(0)

// Safe pop with size check
safePop(arr) =>
    array.size(arr) > 0 ? array.pop(arr) : na

// Negative indexing - access from end
// -1 = last element, -2 = second to last
getFromEnd(arr, negIndex) =>
    size = array.size(arr)
    size > 0 ? array.get(arr, size + negIndex) : na

// Usage
if barstate.isconfirmed
    array.push(prices, close)
    if array.size(prices) > 100
        safePop(prices)

lastPrice = getFromEnd(prices, -1)
secondLast = getFromEnd(prices, -2)
```

## Matrix for Multi-Timeframe Data

```pinescript
//@version=6
indicator("MTF Matrix", overlay=true)

// Store OHLC for multiple timeframes in a matrix
// Rows = timeframes, Columns = OHLC values
var matrix<float> mtfData = matrix.new<float>(3, 4, na)  // 3 TFs x 4 values

// Non-repainting wrapper
getHTF(tf, expr) => request.security(syminfo.tickerid, tf, expr[1], lookahead=barmerge.lookahead_on)

if barstate.isconfirmed
    // Row 0: 1H data
    matrix.set(mtfData, 0, 0, getHTF("60", open))
    matrix.set(mtfData, 0, 1, getHTF("60", high))
    matrix.set(mtfData, 0, 2, getHTF("60", low))
    matrix.set(mtfData, 0, 3, getHTF("60", close))

    // Row 1: 4H data
    matrix.set(mtfData, 1, 0, getHTF("240", open))
    matrix.set(mtfData, 1, 1, getHTF("240", high))
    matrix.set(mtfData, 1, 2, getHTF("240", low))
    matrix.set(mtfData, 1, 3, getHTF("240", close))

    // Row 2: Daily data
    matrix.set(mtfData, 2, 0, getHTF("D", open))
    matrix.set(mtfData, 2, 1, getHTF("D", high))
    matrix.set(mtfData, 2, 2, getHTF("D", low))
    matrix.set(mtfData, 2, 3, getHTF("D", close))
```

## Gap Detection Pattern

```pinescript
//@version=6
indicator("Gap Detection", overlay=true)

// Detect price gaps between bars
// Gap exists when current open differs from previous close
gapUp = open > close[1]
gapDown = open < close[1]
gapSize = open - close[1]

// Time gap detection (market was closed)
timeGap = time - time_close[1] > (time_close[1] - time[1]) * 1.5

// Visualize
plotshape(gapUp and barstate.isconfirmed[1], "Gap Up", shape.triangleup, location.belowbar, color.green)
plotshape(gapDown and barstate.isconfirmed[1], "Gap Down", shape.triangledown, location.abovebar, color.red)
```

## Elapsed Time Calculation

```pinescript
//@version=6
indicator("Time Elapsed", overlay=true)

// Constants for time calculations
MS_PER_SECOND = 1000
MS_PER_MINUTE = 60000
MS_PER_HOUR = 3600000
MS_PER_DAY = 86400000

// Calculate elapsed time since a condition
var int conditionTime = na

if someCondition and barstate.isconfirmed
    conditionTime := time

// Time since condition (in hours)
elapsedMs = not na(conditionTime) ? time - conditionTime : na
elapsedHours = elapsedMs / MS_PER_HOUR

// NEVER use str.format_time() for time differences!
// It treats input as absolute time from Unix epoch
```
