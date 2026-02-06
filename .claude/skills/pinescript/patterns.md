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

---

## Webhook Alert Patterns

These patterns demonstrate best practices for webhook-based alert systems, focusing on JSON formatting, rate limiting prevention, and error handling.

### Pattern 1: Webhook JSON Alert

**Use Case**: Sending structured JSON to webhooks (Discord, Slack, custom APIs)

**Key Concepts**:
- Always validate values before JSON construction
- Use format specifiers for decimal control
- Implement signal change detection to prevent rate limiting

```pinescript
// ==================================================================
// PATTERN: Webhook JSON Alert
// ==================================================================

//@version=6
indicator("Webhook JSON Alert Example", overlay=true)

// ===== Configuration =====
int maFastLen = input.int(10, "Fast MA Length", minval=1)
int maSlowLen = input.int(20, "Slow MA Length", minval=1)

// ===== Calculations =====
float maFast = ta.sma(close, maFastLen)
float maSlow = ta.sma(close, maSlowLen)

bool buyCondition = ta.crossover(maFast, maSlow)
bool sellCondition = ta.crossunder(maFast, maSlow)

// ===== Helper: Build JSON Message with Error Checking =====
buildJsonAlert(string symbol, string signal, float price, float level) =>
    // Validate inputs (prevent JSON corruption)
    if na(price) or na(level)
        runtime.error("Cannot build JSON with na values")

    // Build JSON string (proper formatting)
    '{"symbol":"' + symbol +
     '","signal":"' + signal +
     '","price":' + str.tostring(price, '#.#####') +
     ',"level":' + str.tostring(level) +
     '"}'

// ===== Signal Change Detection =====
// Track previous signal to only alert on changes (prevents rate limiting)
var int prevSignal = 0

if barstate.isconfirmed
    int currentSignal = buyCondition ? 1 : (sellCondition ? -1 : 0)

    // Only alert when signal changes
    if currentSignal != prevSignal and currentSignal != 0
        string sig = currentSignal == 1 ? "BUY" : "SELL"
        string msg = buildJsonAlert(syminfo.ticker, sig, close, math.abs(currentSignal))
        alert(msg, alert.freq_once_per_bar_close)

    prevSignal := currentSignal

// ===== Visual Feedback =====
plot(maFast, "Fast MA", color.blue)
plot(maSlow, "Slow MA", color.orange)
plotshape(buyCondition, "Buy", shape.triangleup, location.belowbar, color.green, size=size.small)
plotshape(sellCondition, "Sell", shape.triangledown, location.abovebar, color.red, size=size.small)
```

**Example webhook payload**:
```json
{"symbol":"AAPL","signal":"BUY","price":150.25000,"level":1}
```

---

### Pattern 2: Multi-Symbol Screener with Rate-Limit-Aware Alerts

**Use Case**: Monitoring 5+ symbols without hitting 15 alerts/3min limit

**Key Concepts**:
- Request data for multiple symbols using request.security()
- Only alert on signal changes, not every bar
- Use [1] offset with lookahead_on for non-repainting

```pinescript
// ==================================================================
// PATTERN: Multi-Symbol Screener with Batched Alerts
// ==================================================================

//@version=6
indicator("Multi-Symbol Screener", overlay=true)

// ===== Inputs =====
string symbol1 = input.symbol("NASDAQ:AAPL", "Symbol 1")
string symbol2 = input.symbol("NASDAQ:GOOGL", "Symbol 2")
string symbol3 = input.symbol("NASDAQ:MSFT", "Symbol 3")
string symbol4 = input.symbol("NASDAQ:TSLA", "Symbol 4")
string symbol5 = input.symbol("NASDAQ:AMZN", "Symbol 5")

// ===== Helper Functions =====

// Calculate signal: 1=BUY, -1=SELL, 0=NEUTRAL
calcSignal(float closePrice, float maFast, float maSlow) =>
    if closePrice > maFast and maFast > maSlow
        1  // BUY
    else if closePrice < maFast and maFast < maSlow
        -1  // SELL
    else
        0  // NEUTRAL

// Build JSON alert message
buildAlertMsg(string sym, string signal, float price, int level) =>
    '{"symbol":"' + sym +
     '","signal":"' + signal +
     '","price":' + str.tostring(price, '#.#####') +
     ',"level":' + str.tostring(level) +
     '"}'

// Get symbol name without exchange prefix
getSymbolName(string fullSymbol) =>
    array.get(str.split(fullSymbol, ":"), 1)

// Convert signal integer to text
getSigText(int sig) =>
    sig == 1 ? "BUY" : (sig == -1 ? "SELL" : "NEUTRAL")

// ===== Request Data for All Symbols =====
// Use [1] offset and lookahead=on for non-repainting

[s1_close, s1_maFast, s1_maSlow] = request.security(symbol1, timeframe.period,
    [close[1], ta.sma(close, 10)[1], ta.sma(close, 20)[1]], lookahead=barmerge.lookahead_on)

[s2_close, s2_maFast, s2_maSlow] = request.security(symbol2, timeframe.period,
    [close[1], ta.sma(close, 10)[1], ta.sma(close, 20)[1]], lookahead=barmerge.lookahead_on)

[s3_close, s3_maFast, s3_maSlow] = request.security(symbol3, timeframe.period,
    [close[1], ta.sma(close, 10)[1], ta.sma(close, 20)[1]], lookahead=barmerge.lookahead_on)

[s4_close, s4_maFast, s4_maSlow] = request.security(symbol4, timeframe.period,
    [close[1], ta.sma(close, 10)[1], ta.sma(close, 20)[1]], lookahead=barmerge.lookahead_on)

[s5_close, s5_maFast, s5_maSlow] = request.security(symbol5, timeframe.period,
    [close[1], ta.sma(close, 10)[1], ta.sma(close, 20)[1]], lookahead=barmerge.lookahead_on)

// ===== Calculate Signals =====
int s1_sig = calcSignal(s1_close, s1_maFast, s1_maSlow)
int s2_sig = calcSignal(s2_close, s2_maFast, s2_maSlow)
int s3_sig = calcSignal(s3_close, s3_maFast, s3_maSlow)
int s4_sig = calcSignal(s4_close, s4_maFast, s4_maSlow)
int s5_sig = calcSignal(s5_close, s5_maFast, s5_maSlow)

// ===== Track Previous Signals (Signal Change Detection) =====
var int prevS1Sig = 0
var int prevS2Sig = 0
var int prevS3Sig = 0
var int prevS4Sig = 0
var int prevS5Sig = 0

// ===== Alert on Signal Changes Only =====
if barstate.isconfirmed
    // Symbol 1
    if s1_sig != prevS1Sig and s1_sig != 0 and not na(s1_close)
        alert(buildAlertMsg(getSymbolName(symbol1), getSigText(s1_sig), s1_close, 1),
              alert.freq_once_per_bar_close)
    prevS1Sig := s1_sig

    // Symbol 2
    if s2_sig != prevS2Sig and s2_sig != 0 and not na(s2_close)
        alert(buildAlertMsg(getSymbolName(symbol2), getSigText(s2_sig), s2_close, 1),
              alert.freq_once_per_bar_close)
    prevS2Sig := s2_sig

    // Symbol 3
    if s3_sig != prevS3Sig and s3_sig != 0 and not na(s3_close)
        alert(buildAlertMsg(getSymbolName(symbol3), getSigText(s3_sig), s3_close, 1),
              alert.freq_once_per_bar_close)
    prevS3Sig := s3_sig

    // Symbol 4
    if s4_sig != prevS4Sig and s4_sig != 0 and not na(s4_close)
        alert(buildAlertMsg(getSymbolName(symbol4), getSigText(s4_sig), s4_close, 1),
              alert.freq_once_per_bar_close)
    prevS4Sig := s4_sig

    // Symbol 5
    if s5_sig != prevS5Sig and s5_sig != 0 and not na(s5_close)
        alert(buildAlertMsg(getSymbolName(symbol5), getSigText(s5_sig), s5_close, 1),
              alert.freq_once_per_bar_close)
    prevS5Sig := s5_sig

// ===== Visual Feedback (for current chart symbol only) =====
plotshape(s1_sig == 1, "Buy", shape.triangleup, location.belowbar, color.green, size=size.small)
plotshape(s1_sig == -1, "Sell", shape.triangledown, location.abovebar, color.red, size=size.small)
```

**Result**: Only new/changed signals trigger alerts (typically 0-3 per bar instead of 5).

---

### Pattern 3: Error-Resistant Alert with Validation

**Use Case**: Prevent runtime errors from stopping alerts

**Key Concepts**:
- Validate ALL values before alert() call
- Use defensive checks for na, invalid ranges
- Return success indicator for debugging

```pinescript
// ==================================================================
// PATTERN: Error-Resistant Alert with Validation
// ==================================================================

//@version=6
indicator("Error-Resistant Alert", overlay=true)

// ===== Inputs =====
int rsiLen = input.int(14, "RSI Length", minval=1, maxval=500)
float obLevel = input.float(70, "Overbought Level", minval=50, maxval=100)
float osLevel = input.float(30, "Oversold Level", minval=0, maxval=50)

// ===== Calculations =====

// Validate inputs (runtime error prevention)
if rsiLen > bar_index
    runtime.error("RSI length exceeds available bars")

// Calculate RSI with error handling
float rsi = ta.rsi(close, rsiLen)

// Calculate signal with na checks
int signal = 0
if not na(rsi)
    if rsi > obLevel and rsi[1] <= obLevel
        signal := -1  // Overbought (sell signal)
    else if rsi < osLevel and rsi[1] >= osLevel
        signal := 1  // Oversold (buy signal)

// ===== Safe Alert Function =====

// Validate ALL values before building message
// Returns: true if alert sent successfully, false if validation failed
safeAlert(string symbol, string signalText, float price, float rsiValue, string details) =>
    // Comprehensive validation
    if na(price)
        log.error("Price is na, skipping alert for " + symbol)
        false
    else if na(rsiValue)
        log.error("RSI is na, skipping alert for " + symbol)
        false
    else if price <= 0
        log.error("Invalid price (" + str.tostring(price) + "), skipping alert for " + symbol)
        false
    else if rsiValue < 0 or rsiValue > 100
        log.error("Invalid RSI (" + str.tostring(rsiValue) + "), skipping alert for " + symbol)
        false
    else
        // Safe to build JSON
        string msg = '{"symbol":"' + symbol +
                      '","signal":"' + signalText +
                      '","price":' + str.tostring(price, '#.#####') +
                      ',"rsi":' + str.tostring(rsiValue, '#.##') +
                      ',"details":"' + details +
                      '"}'
        alert(msg, alert.freq_once_per_bar_close)
        log.info("Alert sent successfully for " + symbol + ": " + signalText)
        true

// ===== Alert Logic with Error Handling =====

if barstate.isconfirmed and signal != 0
    string sigText = signal == 1 ? "BUY" : "SELL"
    string det = signal == 1 ?
                 "RSI crossed below " + str.tostring(osLevel) + " (oversold)" :
                 "RSI crossed above " + str.tostring(obLevel) + " (overbought)"

    // Attempt to send alert with validation
    bool success = safeAlert(syminfo.ticker, sigText, close, rsi, det)

    if not success
        log.warning("Failed to send alert, check error logs above")

// ===== Visual Feedback =====
hline(obLevel, "Overbought", color.red, hline.style_dashed)
hline(osLevel, "Oversold", color.green, hline.style_dashed)
plot(rsi, "RSI", color.blue)
plotshape(signal == 1, "Buy", shape.triangleup, location.bottom, color.green, size=size.small)
plotshape(signal == -1, "Sell", shape.triangledown, location.top, color.red, size=size.small)
```

**Example webhook payload (success)**:
```json
{"symbol":"AAPL","signal":"BUY","price":150.25000,"rsi":28.50,"details":"RSI crossed below 30 (oversold)"}
```

**Benefits**:
- Prevents runtime errors from silently stopping alerts
- Detailed error logging for debugging
- Returns success indicator for conditional logic
- Validates value ranges before JSON construction
