# Alerts and Webhooks: Comprehensive Technical Reference

This document provides deep technical reference for Pine Script alerts, webhooks, and TradingView's server-side execution model. For quick reference, see the "Alerts and Webhooks" section in SKILL.md.

---

## 1. Alert System Architecture

### Alert Lifecycle

Alerts in TradingView follow a specific lifecycle from creation to notification:

1. **Creation**: User creates alert via UI or script contains alert() call
2. **Snapshot**: TradingView captures script state at alert creation time
3. **Execution**: Script runs on cloud servers, evaluating alert conditions
4. **Triggering**: When condition met, alert fires
5. **Notification**: Alert message sent to configured channels (mobile, email, webhook, SMS)

### Alert Snapshots

**Critical concept**: When you create an alert, TradingView takes a **snapshot** of your script at that moment. This snapshot includes:

- Script version (code) at creation time
- Input values at creation time
- Chart settings (symbol, timeframe)

**Implications:**
- Editing script code does NOT update existing alerts
- Changing input values does NOT update existing alerts
- You must delete and recreate alerts after script changes
- This is why TTE's `START_FRESH` flag exists

### Account Tier Limits

Alert limits vary by TradingView account tier:

| Tier | Active Alerts | Server-Side Alerts | Alert Expirations |
|------|---------------|-------------------|-------------------|
| Basic | 1 | 0 | Max 2 days |
| Essential | 10 | 0 | Max 30 days |
| Plus | 20 | 10 | Max 60 days |
| Premium | 100 | 20 | Max 1 year |
| Ultimate | 400 | 30 | Max 1 year |

**Server-side alerts**: These continue running even when you're not viewing the chart. Scripts with alert() calls require server-side alerts.

**Important**: Each alertcondition() in a script counts as a separate alert toward your limit. Scripts with alert() count as one alert regardless of how many alert() calls exist in the code.

### Notification Channels

TradingView can deliver alerts to multiple channels:

1. **Mobile App**: Push notifications
2. **Email**: Sent to account email
3. **Webhook**: HTTP POST to custom URL
4. **SMS**: Text messages (Premium/Ultimate only)
5. **App**: In-app notifications

**For automated trading systems** (like TTE): Webhooks are the preferred method because they:
- Deliver structured data (JSON)
- Trigger immediate automation
- Have no human intervention required
- Can integrate with Discord, Slack, custom APIs

---

## 2. Server-Side Execution Model

### Cloud-Based Execution

**Critical understanding**: Pine Script code does NOT run on your computer. It runs on **TradingView's cloud servers**.

When you add an indicator/strategy to a chart:
1. TradingView server receives your script
2. Server compiles the Pine Script
3. Server executes on historical bars (backtesting data)
4. Server continues executing on real-time bars
5. Alert logic evaluated by server, not client

**Implications for alerts:**
- You can close browser, alerts keep running (server-side alerts)
- Debugging requires server-side tools (Pine Logs, alert logs)
- Network issues on client side don't affect alert execution
- Rate limits and resource limits enforced server-side

### Realtime vs Historical Bars (Server Perspective)

From the server's perspective:

**Historical bars**:
- Already closed bars in the past
- Script processes these during initial load
- Used for backtesting, calculating historical signals
- Variables calculate based on past data

**Realtime bar**:
- The currently forming bar
- Updates on every price tick
- Values change until bar closes
- Alert conditions evaluated on every tick (depending on frequency)

**Why alerts don't fire on historical bars**: TradingView server can't retroactively send notifications for past events. Alerts only fire when conditions met on realtime bars.

### Server Resource Limits

Each script execution has limits enforced by TradingView servers:

#### request.security() Limits
- **Max calls**: 40 per script (Basic/Essential/Plus/Premium)
- **Max calls**: 64 per script (Ultimate)
- Includes all calls across all scopes
- TTE screeners hit this limit with 20+ symbols

#### Loop Execution Timeout
- **Max runtime**: 500ms per loop iteration
- Applies to `for` and `while` loops
- Prevents infinite loops from hanging server
- Long-running calculations must be optimized

#### Collection Size Limits
- **Max elements**: 100,000 per array/map
- Prevents memory exhaustion on server
- Large datasets require careful management

#### Script Compilation Timeout
- Scripts must compile within reasonable time
- Extremely complex scripts may fail to compile
- Limits exist to prevent server resource abuse

### Debugging Server-Side Execution

Since scripts run on servers, debugging requires server-aware tools:

**1. Pine Logs**
```pinescript
if barstate.islast
    log.info("Current signal: " + str.tostring(signal))
    log.info("Level: " + str.tostring(level))
```
- Logs visible in Pine Logs panel
- Persist across realtime updates
- Survive bar state rollback

**2. Alert Logs**
- View in Alert dialog → "Alert Logs" tab
- Shows exactly what message was sent
- Includes timestamp and delivery status
- Critical for debugging webhook JSON issues

**3. plotchar() for Values**
```pinescript
plotchar(signal, "Signal", "", location.top)
```
- Visual debugging on chart
- Works in realtime and historical
- Survives script reloads

### Alert Execution Timing

Alerts execute based on server time, not your local time:

- **Server timezone**: Typically UTC or exchange timezone
- **Bar close timing**: Relative to server time
- **alert.freq_once_per_bar_close**: Fires when server considers bar closed

**Important**: `barstate.isconfirmed` uses server's understanding of bar state. Always use this for non-repainting alerts.

---

## 3. alert() Function Deep Dive

### Function Signature

```pinescript
alert(message, freq)
```

**Parameters:**
- `message` (series string): The alert message to send
- `freq` (input string): Trigger frequency (see Frequency Options below)

### Message Parameter: Series String

The `message` parameter accepts a **series string**, meaning:

**✓ Dynamic values allowed:**
```pinescript
alert("Price: " + str.tostring(close), alert.freq_once_per_bar_close)
alert("Signal: " + (signal == 1 ? "BUY" : "SELL"), alert.freq_once_per_bar_close)
alert(buildJsonMessage(syminfo.ticker, close, level), alert.freq_once_per_bar_close)
```

**✓ Can change on every bar:**
```pinescript
string msg = buySignal ? "BUY at " + str.tostring(close) : "SELL at " + str.tostring(close)
alert(msg, alert.freq_once_per_bar_close)
```

**✓ Can use any series string expression:**
```pinescript
alert(str.format("Symbol: {0}, Price: {1}, Level: {2}", syminfo.ticker, close, level),
      alert.freq_once_per_bar_close)
```

This flexibility makes alert() ideal for webhooks where you need dynamic JSON messages.

### Frequency Parameter Options

Three frequency options control when alerts fire:

**1. alert.freq_once_per_bar_close** (RECOMMENDED)
- Fires once when bar closes
- Uses `barstate.isconfirmed` internally
- Non-repainting (bar won't reopen after close)
- **TTE convention: Always use this**

**2. alert.freq_once_per_bar**
- Fires once when condition first becomes true on bar
- Can fire mid-bar (before bar closes)
- **Repainting risk**: Bar can still repaint before close
- Use case: Time-sensitive signals where bar close wait is too long

**3. alert.freq_all**
- Fires on every tick while condition is true
- **High volume**: Can fire hundreds of times per bar
- **Rate limiting**: Will quickly hit 15 alerts/3min limit
- Use case: High-frequency trading systems (rare)

### Message Length Limits

TradingView has practical limits on alert message length:

- **Recommended max**: 4,000 characters
- **Hard limit**: Approximately 8,000 characters (undocumented)
- **Webhook POST size**: Typically 10KB limit from receiving services

For multi-symbol screeners sending many details, be mindful of message size.

### Unicode and Emoji Support

Alert messages support full Unicode:

**✓ Emojis:**
```pinescript
alert("🚀 BUY signal detected!", alert.freq_once_per_bar_close)
alert("⚠️ SELL signal on " + syminfo.ticker, alert.freq_once_per_bar_close)
```

**✓ International characters:**
```pinescript
alert("Señal de compra en " + syminfo.ticker, alert.freq_once_per_bar_close)
```

**Note**: Webhook receivers must handle UTF-8 encoding properly.

### Execution Timing Within Bar Lifecycle

Understanding when alert() executes during bar processing:

```pinescript
// Bar starts forming (barstate.isnew == true)
// ↓
// Bar receives ticks (barstate.isrealtime == true)
// ↓
// Condition becomes true
// ↓
// alert.freq_once_per_bar fires immediately
// ↓
// More ticks arrive
// ↓
// Bar closes (barstate.isconfirmed == true)
// ↓
// alert.freq_once_per_bar_close fires
```

**Best practice**: Use `barstate.isconfirmed` guard for maximum reliability:

```pinescript
if barstate.isconfirmed
    if buyCondition
        alert("BUY signal", alert.freq_once_per_bar_close)
```

### Multiple alert() Calls in One Script

A script can have multiple alert() calls:

```pinescript
indicator("Multi Alert Example")

if buyCondition
    alert("BUY signal", alert.freq_once_per_bar_close)

if sellCondition
    alert("SELL signal", alert.freq_once_per_bar_close)

if warningCondition
    alert("WARNING", alert.freq_once_per_bar_close)
```

**Important**: All alert() calls in a script count as **one alert** toward your account limit. However, each alert() call that executes counts toward the **rate limit** (15 per 3 minutes).

### Alert Persistence

Alert state persists across:
- ✓ Script reloads (F5 refresh)
- ✓ Bar state rollback (when bar reopens)
- ✓ Chart navigation (pan/zoom)
- ✓ Browser close/reopen (server-side alerts)

Alert state does NOT persist across:
- ✗ Script edits (requires alert recreation)
- ✗ Input changes (requires alert recreation)
- ✗ Symbol/timeframe changes (requires alert recreation)

---

## 4. alertcondition() Function Deep Dive

### Function Signature

```pinescript
alertcondition(condition, title, message)
```

**Parameters:**
- `condition` (series bool): The condition that triggers the alert
- `title` (const string): Alert name in UI (compile-time constant)
- `message` (const string): Alert message with placeholders (compile-time constant)

### Legacy Function for Indicators Only

alertcondition() is a **legacy function** with limitations:

**Restrictions:**
- ✗ Indicators only (NOT strategies)
- ✗ Message must be const string (no dynamic values except placeholders)
- ✗ Each alertcondition() counts as separate alert toward account limit
- ✗ Requires UI interaction to create alert

**Why use alert() instead:**
- ✓ Works in strategies and indicators
- ✓ Series string message (fully dynamic)
- ✓ All alert() calls count as one alert
- ✓ No UI interaction required (automatic)

### Message Parameter: Const String Limitation

The `message` parameter must be a **const string** (known at compile time):

**✗ NOT allowed:**
```pinescript
alertcondition(buySignal, "Buy Alert", "Price: " + str.tostring(close))  // ERROR
```

**✓ Must use placeholders:**
```pinescript
alertcondition(buySignal, "Buy Alert", "Price: {{close}}")  // OK
```

This limitation makes alertcondition() less flexible for webhook JSON messages.

### Complete Placeholder Syntax Reference

alertcondition() supports placeholders for dynamic values:

#### Price Placeholders
- `{{close}}` - Closing price of the bar
- `{{open}}` - Opening price of the bar
- `{{high}}` - Highest price of the bar
- `{{low}}` - Lowest price of the bar
- `{{volume}}` - Volume of the bar

#### Time Placeholders
- `{{time}}` - Bar opening time (Unix timestamp)
- `{{timenow}}` - Current time when alert fires (Unix timestamp)

#### Symbol Placeholders
- `{{ticker}}` - Symbol name (e.g., "AAPL")
- `{{exchange}}` - Exchange name (e.g., "NASDAQ")
- `{{interval}}` - Timeframe (e.g., "60" for 1H, "D" for daily)

#### Plot Placeholders
- `{{plot_0}}` - Value of first plot
- `{{plot_1}}` - Value of second plot
- `{{plot_2}}` - Value of third plot
- etc.

**Named plot placeholder:**
- `{{plot("[plot_title]")}}` - Value of plot with specific title

**Example with multiple placeholders:**
```pinescript
alertcondition(
    crossover(maFast, maSlow),
    title = "MA Cross",
    message = "Symbol: {{ticker}}, Time: {{time}}, Price: {{close}}, Fast MA: {{plot_0}}, Slow MA: {{plot_1}}"
)
```

### UI Integration

alertcondition() creates selectable conditions in the alert dialog:

1. User clicks "Add Alert" on chart
2. TradingView shows list of alertcondition() titles
3. User selects condition
4. User can customize message (using placeholders)
5. User configures notification channels

**This UI requirement** makes alertcondition() unsuitable for automated systems that need to programmatically create alerts.

### Account Limit Implications

Each alertcondition() counts toward your alert limit:

**Example:**
```pinescript
indicator("Multi Condition Example")

alertcondition(buySignal, "Buy", "Buy at {{close}}")
alertcondition(sellSignal, "Sell", "Sell at {{close}}")
alertcondition(warningSignal, "Warning", "Warning at {{close}}")
```

This script requires **3 alerts** from your account limit (one per alertcondition()).

**Contrast with alert():**
```pinescript
indicator("Multi Alert Example")

if buySignal
    alert("Buy at " + str.tostring(close), alert.freq_once_per_bar_close)
if sellSignal
    alert("Sell at " + str.tostring(close), alert.freq_once_per_bar_close)
if warningSignal
    alert("Warning at " + str.tostring(close), alert.freq_once_per_bar_close)
```

This script requires **1 alert** from your account limit (regardless of alert() call count).

### Migration Path: alertcondition() → alert()

To migrate from alertcondition() to alert():

**Before (alertcondition):**
```pinescript
alertcondition(crossover(close, ma), "Cross Up", "Price crossed above MA: {{close}}")
```

**After (alert):**
```pinescript
if crossover(close, ma) and barstate.isconfirmed
    alert("Price crossed above MA: " + str.tostring(close), alert.freq_once_per_bar_close)
```

**Benefits of migration:**
- Full control over message formatting
- Can build JSON messages dynamically
- Works in strategies
- Reduces alert count toward account limit

---

## 5. Webhook Integration Patterns

### Webhook Fundamentals

When you configure a webhook URL in a TradingView alert, TradingView sends an HTTP POST request to that URL when the alert fires.

**Request details:**
- **Method**: POST
- **Content-Type**: text/plain (or application/json if message is valid JSON)
- **Body**: The alert message (raw text or JSON)
- **Delivery guarantee**: At-least-once (may receive duplicates)

**No authentication**: TradingView doesn't add authentication headers. Secure your webhook URL (use secret tokens in URL or validate message content).

### JSON Formatting Best Practices

To send structured data via webhooks, format alert messages as JSON.

**Essential rules:**
1. **Validate JSON structure** - Use online validators during development
2. **Escape special characters** - Quotes, backslashes, newlines
3. **Use str.tostring() with format specifiers** - Control decimal places
4. **Check for na values** - Prevent "null" or "NaN" in JSON

**Example of proper JSON formatting:**
```pinescript
buildJsonAlert(string symbol, string signal, float price, float level) =>
    // Validate inputs first
    if na(price) or na(level)
        runtime.error("Cannot build JSON with na values")

    // Build JSON with proper escaping
    '{"symbol":"' + symbol +
     '","signal":"' + signal +
     '","price":' + str.tostring(price, '#.#####') +
     ',"level":' + str.tostring(level) +
     '}'
```

**Format specifiers:**
- `'#.##'` - 2 decimal places
- `'#.#####'` - 5 decimal places
- `'#'` - Integer (no decimals)

### Discord Webhook Pattern

Discord expects JSON with specific structure:

**Simple message:**
```pinescript
discordWebhook(string content) =>
    '{"content":"' + content + '"}'

// Usage
if buySignal and barstate.isconfirmed
    alert(discordWebhook("🚀 BUY signal on " + syminfo.ticker), alert.freq_once_per_bar_close)
```

**Rich embed (advanced):**
```pinescript
discordEmbed(string title, string description, int color, string symbol, float price) =>
    '{"embeds":[{' +
    '"title":"' + title + '",' +
    '"description":"' + description + '",' +
    '"color":' + str.tostring(color) + ',' +
    '"fields":[' +
    '{"name":"Symbol","value":"' + symbol + '","inline":true},' +
    '{"name":"Price","value":"' + str.tostring(price, '#.#####') + '","inline":true}' +
    ']}]}'

// Usage
if buySignal and barstate.isconfirmed
    string msg = discordEmbed(
         "Buy Signal Detected",
         "Technical analysis indicates bullish momentum",
         3066993,  // Green color
         syminfo.ticker,
         close
    )
    alert(msg, alert.freq_once_per_bar_close)
```

**Discord color codes:**
- Green (bullish): 3066993
- Red (bearish): 15158332
- Yellow (warning): 16776960

### Slack Webhook Pattern

Slack uses a different JSON structure:

**Simple message:**
```pinescript
slackWebhook(string text) =>
    '{"text":"' + text + '"}'

// Usage
if sellSignal and barstate.isconfirmed
    alert(slackWebhook("🔻 SELL signal on " + syminfo.ticker), alert.freq_once_per_bar_close)
```

**Rich message block:**
```pinescript
slackBlock(string title, string symbol, string signal, float price) =>
    '{"blocks":[' +
    '{"type":"section","text":{"type":"mrkdwn","text":"*' + title + '*"}},' +
    '{"type":"section","fields":[' +
    '{"type":"mrkdwn","text":"*Symbol:*\\n' + symbol + '"},' +
    '{"type":"mrkdwn","text":"*Signal:*\\n' + signal + '"},' +
    '{"type":"mrkdwn","text":"*Price:*\\n' + str.tostring(price, '#.#####') + '"}' +
    ']}' +
    ']}'
```

**Note the escaped newlines:** `\\n` in JSON string.

### Custom API Webhook Pattern (Generic)

For custom APIs, design JSON structure based on API requirements:

**Example: Stock Buddy API (TTE tiered mode):**
```pinescript
// Stock Buddy expects: {"symbol": "...", "signal": "...", "level": ..., "details": "..."}
stockBuddyWebhook(string symbol, string signal, int level, string details) =>
    '{"symbol":"' + symbol +
     '","signal":"' + signal +
     '","level":' + str.tostring(level) +
     ',"details":"' + details +
     '"}'

// Usage in TTE screener
if signalChange and barstate.isconfirmed
    string sig = buySignal ? "BUY" : "SELL"
    string det = "NWE detected at " + str.tostring(close, '#.#####')
    alert(stockBuddyWebhook(syminfo.ticker, sig, 1, det), alert.freq_once_per_bar_close)
```

### TTE Project Webhook Pattern (Detailed Breakdown)

TTE uses a sophisticated pattern to build JSON messages:

**From TTE Screener.txt (line 1190):**
```pinescript
// Build JSON alert message
buildAlertMsg(string sym, string signal, int level, string details) =>
    '{"symbol":"' + sym +
     '","signal":"' + signal +
     '","level":' + str.tostring(level) +
     ',"details":"' + details +
     '"}'
```

**Component builders:**
```pinescript
// Build NWE detail string
buildNweDetail(string zone, string timeframe, float price) =>
    zone + " zone on " + timeframe + " at " + str.tostring(price, '#.#####')

// Build OB detail string
buildObDetail(string obType, float obPrice) =>
    obType + " OB at " + str.tostring(obPrice, '#.#####')

// Build divergence detail string
buildDivDetail(string divType) =>
    divType + " divergence detected"
```

**Usage in screener logic (lines 1237-1249):**
```pinescript
if barstate.isconfirmed
    // Check if signal changed from previous bar
    if buyLvl01 != prevBuyLvl01 or sellLvl01 != prevSellLvl01
        bool isBuy = buyLvl01 >= sellLvl01 and buyLvl01 > 0
        int lvl = isBuy ? buyLvl01 : sellLvl01

        if lvl > 0
            string sig = isBuy ? "BUY" : "SELL"
            string det = "NWE:" + buildNweDetail(nweZone, nweTimeframe, nwePrice)

            // Add OB details for level 2+
            if lvl >= 2
                det := det + " OB:" + buildObDetail(obType, obPrice)

            // Add divergence details for level 3
            if lvl == 3
                det := det + " DIV:" + buildDivDetail(divType)

            // Send alert with built message
            alert(buildAlertMsg(getSymbolName(s01), sig, lvl, det), alert.freq_once_per_bar_close)
```

**Key patterns:**
1. **Signal change detection** - Only alert when signal changes (prevents rate limiting)
2. **Hierarchical details** - Details added based on signal level
3. **Modular builders** - Each component has dedicated builder function
4. **Validated values** - Check lvl > 0 before building message

### Error Handling for Webhook JSON

Always validate values before building JSON:

**Problem: na values corrupt JSON:**
```pinescript
// BAD: If close is na, JSON becomes invalid
alert('{"price":' + str.tostring(close) + '}', alert.freq_once_per_bar_close)
// Result: {"price":NaN} ← Invalid JSON
```

**Solution: Check for na:**
```pinescript
// GOOD: Validate before building
if not na(close) and barstate.isconfirmed
    alert('{"price":' + str.tostring(close, '#.#####') + '}', alert.freq_once_per_bar_close)
```

**Defensive pattern:**
```pinescript
safeJsonValue(float value, float defaultValue = 0.0) =>
    na(value) ? str.tostring(defaultValue, '#.#####') : str.tostring(value, '#.#####')

// Usage
string msg = '{"price":' + safeJsonValue(close) + ',"level":' + safeJsonValue(level, 1.0) + '}'
alert(msg, alert.freq_once_per_bar_close)
```

---

## 6. Rate Limiting and Throttling

### Exact Limit: 15 Alerts Per 3 Minutes

TradingView enforces a rate limit on alert notifications:

**Limit**: 15 alerts per 3 minutes per script

**Calculation**: Rolling window (not fixed 3-minute intervals)

**Example timeline:**
- 10:00:00 - Alert #1 fires
- 10:00:30 - Alert #2 fires
- ... (13 more alerts)
- 10:02:00 - Alert #15 fires ← Limit reached
- 10:02:30 - Alert #16 delayed until 10:03:00 (3 minutes after alert #1)
- 10:03:00 - Alert #16 fires (slot from alert #1 freed)

### Throttling Behavior

When rate limit exceeded:

**Alerts are NOT dropped** - They are queued and delayed
**Delivery delayed** - Alerts wait until slots free up in the 3-minute window
**User notification** - TradingView shows warning in alert log

**Implication**: Time-sensitive trading signals may arrive late during high-activity periods.

### Multi-Symbol Screener Implications

Multi-symbol screeners can easily hit rate limits:

**Problem scenario:**
- Screener monitors 20 symbols
- All 20 symbols trigger alerts on same bar (high volatility event)
- 20 alerts × 1 bar = instant rate limit hit
- Some alerts delayed by minutes

**TTE's solution: Signal change detection**

Only alert when signal changes from previous bar:

```pinescript
// Track previous signals for all symbols
var int prevS01Sig = 0
var int prevS02Sig = 0
// ... repeat for all symbols

if barstate.isconfirmed
    // Symbol 1
    if s01_signal != prevS01Sig and s01_signal != 0
        alert(buildJsonAlert(symbol1, getSigText(s01_signal), close, s01_level),
              alert.freq_once_per_bar_close)
    prevS01Sig := s01_signal

    // Symbol 2
    if s02_signal != prevS02Sig and s02_signal != 0
        alert(buildJsonAlert(symbol2, getSigText(s02_signal), close, s02_level),
              alert.freq_once_per_bar_close)
    prevS02Sig := s02_signal

    // ... repeat for all symbols
```

**Result**: Only symbols with NEW signals trigger alerts, dramatically reducing alert volume.

### Prevention Strategies

#### Strategy 1: Use barstate.isconfirmed

Fire alerts only at bar close:

```pinescript
// BAD: Fires on every tick (hundreds per bar)
if buyCondition
    alert("BUY", alert.freq_all)

// GOOD: Fires once per bar
if buyCondition and barstate.isconfirmed
    alert("BUY", alert.freq_once_per_bar_close)
```

#### Strategy 2: Track Previous State

Only alert on condition changes:

```pinescript
var bool prevBuyCondition = false

if barstate.isconfirmed
    // Only alert if condition changed from false to true
    if buyCondition and not prevBuyCondition
        alert("BUY", alert.freq_once_per_bar_close)

    prevBuyCondition := buyCondition
```

#### Strategy 3: Batch Alerts

Combine multiple signals into one alert:

```pinescript
if barstate.isconfirmed
    var string[] signals = array.new_string()

    if s01_signal != 0
        array.push(signals, syminfo.ticker + ":" + getSigText(s01_signal))
    if s02_signal != 0
        array.push(signals, symbol2 + ":" + getSigText(s02_signal))

    // Send one alert with all signals
    if array.size(signals) > 0
        alert('{"signals":["' + array.join(signals, '","') + '"]}', alert.freq_once_per_bar_close)
```

**Trade-off**: Lose per-symbol webhook routing, but avoid rate limits.

### Monitoring Rate Limit Status

TradingView provides feedback on rate limit status:

**Alert log**: Shows when alerts are throttled
**Warning message**: "Alert frequency limit reached"
**Delayed timestamp**: Alert log shows delay between trigger and delivery

**Best practice**: Monitor alert logs during testing to ensure signals fire as expected.

---

## 7. Runtime Error Handling

### How Errors Stop Alerts Completely

**Critical concept**: When a Pine Script encounters a runtime error, script execution halts immediately. If execution stops before reaching alert() call, no alert fires.

**Error flow:**
1. Script starts executing on new bar/tick
2. Error occurs (e.g., array index out of bounds)
3. **Script execution stops immediately**
4. Alert logic never executes
5. No alert fires (even if condition is true)
6. TradingView shows error in indicator title

**Implication for trading systems**: A single runtime error can silently stop all alerts until the error resolves. This is catastrophic for automated trading.

### Common Error Types That Stop Alerts

#### 1. Array Index Out of Bounds

```pinescript
// BAD: No size check
var float[] prices = array.new_float()
array.push(prices, close)
float lastPrice = array.get(prices, 1)  // ERROR if array size is 1

// GOOD: Check size first
var float[] prices = array.new_float()
array.push(prices, close)
if array.size(prices) > 1
    float lastPrice = array.get(prices, 1)
```

#### 2. Division by Zero

```pinescript
// BAD: No denominator check
float ratio = close / volume  // ERROR if volume is 0

// GOOD: Check denominator
float ratio = volume != 0 ? close / volume : 0.0
```

#### 3. na Value Arithmetic

```pinescript
// BAD: No na check
float diff = close - close[100]  // ERROR if bar_index < 100 (close[100] is na)

// GOOD: Check for na
float diff = na(close[100]) ? 0.0 : close - close[100]
```

#### 4. Collection Size Exceeded

```pinescript
// BAD: Unbounded array growth
var float[] allPrices = array.new_float()
array.push(allPrices, close)  // ERROR after 100,000 bars

// GOOD: Limit array size
var float[] recentPrices = array.new_float()
array.push(recentPrices, close)
if array.size(recentPrices) > 1000
    array.shift(recentPrices)  // Remove oldest element
```

#### 5. Loop Timeout (>500ms)

```pinescript
// BAD: Potentially long loop
for i = 0 to 1000000
    float result = math.pow(close, 2)  // May timeout

// GOOD: Optimize or limit iterations
int maxIterations = 10000
for i = 0 to math.min(maxIterations, array.size(data) - 1)
    float result = array.get(data, i) * 2
```

### Prevention Patterns

#### Pattern 1: Defensive Array Access

```pinescript
safeArrayGet(float[] arr, int index, float defaultValue = 0.0) =>
    if array.size(arr) > index and index >= 0
        array.get(arr, index)
    else
        defaultValue

// Usage
var float[] prices = array.new_float()
array.push(prices, close)
float lastPrice = safeArrayGet(prices, 1, close)  // Safe, returns close if out of bounds
```

#### Pattern 2: Null-Safe Arithmetic

```pinescript
safeSub(float a, float b, float defaultValue = 0.0) =>
    na(a) or na(b) ? defaultValue : a - b

safeDiv(float a, float b, float defaultValue = 0.0) =>
    na(a) or na(b) or b == 0 ? defaultValue : a / b

// Usage
float diff = safeSub(close, close[100])
float ratio = safeDiv(close, volume)
```

#### Pattern 3: Validated Input

```pinescript
// In input declarations
int lookbackInput = input.int(20, "Lookback Period", minval=1, maxval=500)

// In calculations
if lookbackInput > bar_index
    runtime.error("Lookback period exceeds available bars")

// Safe to use
float avgPrice = ta.sma(close, lookbackInput)
```

#### Pattern 4: Error-Resistant Alert Pattern

```pinescript
safeAlert(string symbol, string signal, float price, float level, string details) =>
    // Validate ALL values before building message
    if na(price)
        log.error("Price is na, skipping alert for " + symbol)
        false
    else if na(level)
        log.error("Level is na, skipping alert for " + symbol)
        false
    else if level <= 0
        log.error("Invalid level, skipping alert for " + symbol)
        false
    else
        // Safe to build JSON
        string msg = '{"symbol":"' + symbol +
                      '","signal":"' + signal +
                      '","price":' + str.tostring(price, '#.#####') +
                      ',"level":' + str.tostring(level) +
                      ',"details":"' + details + '"}'
        alert(msg, alert.freq_once_per_bar_close)
        true

// Usage
if barstate.isconfirmed and signalChange
    bool success = safeAlert(syminfo.ticker, "BUY", close, calcLevel(), getDetails())
    if success
        log.info("Alert sent successfully for " + syminfo.ticker)
```

### Error Recovery

**How alerts resume after error resolution:**

1. Fix the code causing runtime error
2. Save script (TradingView recompiles)
3. Script re-executes from current bar
4. If condition is true, alert fires normally
5. Previous error state cleared

**Important**: Alerts don't fire retroactively for bars missed during error state. Only future bars trigger alerts after fix.

### Debugging Runtime Errors

**Pine Logs for error tracking:**
```pinescript
// Log potential error conditions
if bar_index < 100
    log.warning("Insufficient historical bars for calculation")

if na(close[100])
    log.error("close[100] is na at bar_index " + str.tostring(bar_index))
```

**Conditional execution:**
```pinescript
// Only execute alert logic if prerequisites met
if bar_index >= 100 and not na(close[100]) and volume > 0
    // Safe to calculate and alert
    float ratio = close / volume
    if buyCondition and barstate.isconfirmed
        alert("BUY at " + str.tostring(close), alert.freq_once_per_bar_close)
else
    log.info("Prerequisites not met, skipping alert logic")
```

---

## 8. Strategy Alerts

### Automatic Alerts on Order Fills

Strategies can fire alerts automatically when the broker emulator fills orders:

```pinescript
strategy("Auto Alert Example", overlay=true)

// Entry with alert message
if buyCondition
    strategy.entry("Long", strategy.long, alert_message="BUY order filled at " + str.tostring(close))

// Exit with alert message
if sellCondition
    strategy.close("Long", alert_message="SELL order filled at " + str.tostring(close))
```

**When alerts fire:**
- Alert fires when broker emulator fills the order
- Uses order fill price (may differ from close if slippage modeled)
- Fires even if alert.freq_once_per_bar_close used

### alert_message Parameter

The `alert_message` parameter is available on:
- `strategy.entry()` - Entry orders
- `strategy.exit()` - Exit orders with stops/limits
- `strategy.close()` - Close position orders
- `strategy.order()` - Generic orders

**Dynamic messages allowed:**
```pinescript
string entryMsg = "LONG entry at " + str.tostring(close) + " on " + syminfo.ticker
strategy.entry("Long", strategy.long, alert_message=entryMsg)
```

### Placeholder: {{strategy.order.alert_message}}

In the alert dialog, use this placeholder to include the alert_message:

**Alert message field in UI:**
```
Order filled: {{strategy.order.alert_message}}
Symbol: {{ticker}}
Time: {{timenow}}
```

**Result when alert fires:**
```
Order filled: BUY order filled at 150.25
Symbol: AAPL
Time: 1672531200
```

### One Alert for All Order Fills

**Important**: Strategy alerts count as one alert regardless of how many orders execute.

**Example:**
```pinescript
strategy("Multi Order Example")

if buyCondition1
    strategy.entry("Long1", strategy.long, alert_message="Entry 1")
if buyCondition2
    strategy.entry("Long2", strategy.long, alert_message="Entry 2")
if sellCondition
    strategy.exit("Exit1", "Long1", alert_message="Exit 1")
    strategy.exit("Exit2", "Long2", alert_message="Exit 2")
```

All order fills fire through the same alert (configured once in UI). Multiple orders can fire in one bar.

### Backtesting Integration

**Critical limitation**: Strategy alerts do NOT fire during backtesting.

**Why**: Backtesting processes historical bars rapidly. Firing alerts on every historical order would be meaningless and hit rate limits.

**Alerts fire only**:
- On realtime bars (after strategy is live)
- When broker emulator fills orders
- If alert configured in UI

**Testing strategy alerts**: Switch to real-time mode (paper trading) to verify alerts work.

### Use Case: Automated Trade Execution via Webhooks

Strategy alerts enable automated trading:

**Workflow:**
1. Strategy generates order (strategy.entry())
2. Broker emulator fills order
3. Alert fires with order details (alert_message)
4. Webhook POST sent to broker API
5. Broker API places real order

**Example alert_message for broker API:**
```pinescript
string orderJson = '{"action":"BUY","symbol":"' + syminfo.ticker +
                   '","quantity":100,"price":' + str.tostring(close, '#.##') + '}'
strategy.entry("Long", strategy.long, alert_message=orderJson)
```

**Broker receives:**
```json
{"action":"BUY","symbol":"AAPL","quantity":100,"price":150.25}
```

---

## 9. Troubleshooting Guide

### Q: Alert not firing at all

**Possible causes:**

1. **Script has runtime errors**
   - Check indicator title for red error badge
   - Review Pine Logs for error messages
   - Fix errors and resave script

2. **Alert expired**
   - Check alert expiration date in alert list
   - Alerts expire based on account tier (2 days to 1 year)
   - Recreate expired alerts

3. **Alert not configured correctly**
   - For alert(): Ensure alert created via UI (right-click chart → Add Alert)
   - For alertcondition(): Ensure alertcondition selected in alert dialog
   - Verify "Notify on App" or webhook URL configured

4. **Rate limit exceeded**
   - Check alert log for throttling messages
   - Reduce alert frequency (use signal change detection)
   - Wait 3 minutes for rate limit window to reset

5. **Script not running (stopped)**
   - Verify script has green checkmark (running)
   - Refresh page if script shows stopped
   - Check TradingView service status

6. **Condition never becomes true**
   - Add debug logging: `log.info("Condition: " + str.tostring(buyCondition))`
   - Verify condition logic is correct
   - Check input values are reasonable

### Q: Alert fires multiple times per bar

**Possible causes:**

1. **Using alert.freq_all**
   - **Fix**: Change to `alert.freq_once_per_bar_close`

2. **Using alert.freq_once_per_bar without barstate.isconfirmed**
   - **Fix**: Add `barstate.isconfirmed` guard:
   ```pinescript
   if buyCondition and barstate.isconfirmed
       alert("BUY", alert.freq_once_per_bar_close)
   ```

3. **Multiple alert() calls in local scopes**
   - **Problem**:
   ```pinescript
   if condition1
       alert("Signal 1", alert.freq_once_per_bar_close)
   if condition2
       alert("Signal 2", alert.freq_once_per_bar_close)
   ```
   Both fire if both conditions true.

   - **Fix**: Use mutually exclusive conditions or track previous alert state

4. **Alert condition repainting**
   - See "All Repainting Causes" section in SKILL.md
   - Use [1] offset for historical reference
   - Use barstate.isconfirmed

### Q: Webhook receives invalid JSON

**Possible causes:**

1. **JSON structure errors**
   - **Fix**: Validate JSON with online validator (jsonlint.com)
   - Check for missing commas, quotes, brackets
   - Use proper escaping for special characters

2. **Special characters not escaped**
   - **Problem**: Symbol name contains quotes or backslashes
   - **Fix**: Implement string escaping function:
   ```pinescript
   escapeJson(string s) =>
       str.replace_all(str.replace_all(s, '\\', '\\\\'), '"', '\\"')
   ```

3. **na values in string concatenation**
   - **Problem**:
   ```pinescript
   '{"price":' + str.tostring(close) + '}'  // If close is na, JSON is invalid
   ```

   - **Fix**: Check for na before building JSON:
   ```pinescript
   if not na(close)
       '{"price":' + str.tostring(close, '#.#####') + '}'
   ```

4. **Number formatting issues**
   - **Problem**: Too many decimal places, scientific notation
   - **Fix**: Use format specifiers:
   ```pinescript
   str.tostring(close, '#.#####')  // 5 decimal places
   str.tostring(level)  // Integer
   ```

### Q: Alert timing seems wrong (repainting)

**Causes and fixes:**

1. **Not using barstate.isconfirmed**
   - **Fix**: Always use:
   ```pinescript
   if condition and barstate.isconfirmed
       alert("Signal", alert.freq_once_per_bar_close)
   ```

2. **Using [0] offset for historical reference**
   - **Problem**: `close[0]` is current bar (repaints until close)
   - **Fix**: Use `close[1]` for previous bar (confirmed):
   ```pinescript
   bool crossUp = close[1] < ma[1] and close > ma  // Repaints
   bool crossUpSafe = close[2] < ma[2] and close[1] > ma[1]  // Non-repainting
   ```

3. **request.security() repainting**
   - **Problem**: Default lookahead shows unconfirmed HTF data
   - **Fix**: Use non-repaint wrapper:
   ```pinescript
   [htfClose] = request.security(syminfo.tickerid, "D", [close[1]], lookahead=barmerge.lookahead_on)
   ```
   See "Non-Repainting Higher Timeframe Data" in SKILL.md

4. **varip causing realtime-only logic**
   - **Problem**: varip variables behave differently on historical vs realtime bars
   - **Fix**: Avoid varip for alert conditions, use var instead

**Deep dive**: See SKILL.md section "All Repainting Causes (And How to Avoid Them)" for comprehensive repainting prevention.

### Q: Alerts delayed or missing

**Possible causes:**

1. **Rate limits (15 per 3 minutes)**
   - **Symptom**: Alert log shows delayed timestamp
   - **Fix**: Implement signal change detection (see section 6)
   - **Fix**: Use batched alerts for multi-symbol screeners

2. **TradingView service issues**
   - **Check**: https://status.tradingview.com/
   - **Temporary**: Wait for service restoration
   - **Persistent**: Contact TradingView support

3. **Webhook endpoint not responding**
   - **Check**: Test webhook URL manually (curl POST)
   - **Check**: Webhook service logs (Discord, Slack, custom API)
   - **Fix**: Ensure endpoint responds with 200 OK
   - **Fix**: Check webhook URL hasn't expired (Discord webhooks can expire)

4. **Network issues on TradingView server side**
   - **Symptom**: Intermittent delivery failures
   - **Check**: Alert log shows "failed to send" status
   - **Fix**: Implement retry logic on webhook receiver side (TradingView has no built-in retry)

5. **Alert snapshot outdated**
   - **Problem**: Script edited but alert not recreated
   - **Fix**: Delete old alert, recreate after script changes

### Q: Multi-symbol screener not alerting for all symbols

**Possible causes:**

1. **request.security() limit reached**
   - **Limit**: 40 calls (Basic/Pro/Premium), 64 calls (Ultimate)
   - **Fix**: Reduce number of symbols monitored
   - **Fix**: Upgrade to Ultimate account

2. **Runtime error in one symbol's calculation**
   - **Symptom**: Some symbols fire alerts, others don't
   - **Fix**: Add error handling for each symbol:
   ```pinescript
   [s01_sig, s01_lvl] = request.security(symbol1, timeframe.period, [getSignal()[1], getLevel()[1]], lookahead=barmerge.lookahead_on)
   if na(s01_sig) or na(s01_lvl)
       log.error("Failed to get data for " + symbol1)
   ```

3. **Symbol data unavailable**
   - **Problem**: Symbol not traded during bar (low volume, after hours)
   - **Fix**: Check syminfo.tickerid validity:
   ```pinescript
   if not na(close)
       // Symbol has data, safe to process
   ```

### Q: Alert fires on wrong timeframe

**Cause:** Alert created on different timeframe than intended

**Fix:**
1. Switch chart to desired timeframe BEFORE creating alert
2. Verify timeframe in alert dialog shows correct interval
3. For HTF alerts, ensure request.security() uses correct timeframe:
```pinescript
[dailyClose] = request.security(syminfo.tickerid, "D", [close[1]], lookahead=barmerge.lookahead_on)
```

### Q: Pine Logs not showing log.info() output

**Possible causes:**

1. **Log level filter set too high**
   - **Fix**: In Pine Logs panel, set filter to "Info" or "All"

2. **Logs only available on realtime bars**
   - **Limitation**: Logs don't persist from historical bar calculations
   - **Fix**: Wait for realtime bar to see logs

3. **Too many logs (truncated)**
   - **Limitation**: Pine Logs show last N entries only
   - **Fix**: Reduce logging frequency or use conditional logging

---

## 10. Complete Examples

### Example 1: Multi-Symbol Screener with Signal Change Detection (TTE Pattern)

This example demonstrates TTE's approach to monitoring multiple symbols without hitting rate limits.

```pinescript
//@version=5
indicator("Multi-Symbol Screener", overlay=true)

// ===== Inputs =====
string symbol1 = input.symbol("NASDAQ:AAPL", "Symbol 1")
string symbol2 = input.symbol("NASDAQ:GOOGL", "Symbol 2")
string symbol3 = input.symbol("NASDAQ:MSFT", "Symbol 3")
string symbol4 = input.symbol("NASDAQ:TSLA", "Symbol 4")
string symbol5 = input.symbol("NASDAQ:AMZN", "Symbol 5")

// ===== Helper Functions =====

// Calculate signal for given price data
// Returns: 1 = BUY, -1 = SELL, 0 = NEUTRAL
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

// Use [1] offset and lookahead=on for non-repainting HTF data
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
        log.info("Alert sent for " + getSymbolName(symbol1) + ": " + getSigText(s1_sig))
    prevS1Sig := s1_sig

    // Symbol 2
    if s2_sig != prevS2Sig and s2_sig != 0 and not na(s2_close)
        alert(buildAlertMsg(getSymbolName(symbol2), getSigText(s2_sig), s2_close, 1),
              alert.freq_once_per_bar_close)
        log.info("Alert sent for " + getSymbolName(symbol2) + ": " + getSigText(s2_sig))
    prevS2Sig := s2_sig

    // Symbol 3
    if s3_sig != prevS3Sig and s3_sig != 0 and not na(s3_close)
        alert(buildAlertMsg(getSymbolName(symbol3), getSigText(s3_sig), s3_close, 1),
              alert.freq_once_per_bar_close)
        log.info("Alert sent for " + getSymbolName(symbol3) + ": " + getSigText(s3_sig))
    prevS3Sig := s3_sig

    // Symbol 4
    if s4_sig != prevS4Sig and s4_sig != 0 and not na(s4_close)
        alert(buildAlertMsg(getSymbolName(symbol4), getSigText(s4_sig), s4_close, 1),
              alert.freq_once_per_bar_close)
        log.info("Alert sent for " + getSymbolName(symbol4) + ": " + getSigText(s4_sig))
    prevS4Sig := s4_sig

    // Symbol 5
    if s5_sig != prevS5Sig and s5_sig != 0 and not na(s5_close)
        alert(buildAlertMsg(getSymbolName(symbol5), getSigText(s5_sig), s5_close, 1),
              alert.freq_once_per_bar_close)
        log.info("Alert sent for " + getSymbolName(symbol5) + ": " + getSigText(s5_sig))
    prevS5Sig := s5_sig

// ===== Visual Feedback =====

// Plot signals for current chart symbol only (not screener symbols)
plotshape(s1_sig == 1 and barstate.isconfirmed, "Buy", shape.triangleup, location.belowbar, color.green, size=size.small)
plotshape(s1_sig == -1 and barstate.isconfirmed, "Sell", shape.triangledown, location.abovebar, color.red, size=size.small)
```

**Key features:**
- Monitors 5 symbols simultaneously
- Only alerts when signal changes (not every bar)
- Non-repainting (uses [1] offset and lookahead=on)
- Error-resistant (checks for na values)
- JSON webhook format
- Avoids rate limiting

### Example 2: Discord Rich Embed Alert

This example shows how to send rich embeds to Discord via webhook.

```pinescript
//@version=5
indicator("Discord Rich Embed Alert", overlay=true)

// ===== Inputs =====
int fastLen = input.int(10, "Fast MA Length", minval=1)
int slowLen = input.int(20, "Slow MA Length", minval=1)

// ===== Calculations =====
float maFast = ta.sma(close, fastLen)
float maSlow = ta.sma(close, slowLen)

bool buySignal = ta.crossover(maFast, maSlow)
bool sellSignal = ta.crossunder(maFast, maSlow)

// ===== Discord Embed Builder =====

// Build Discord embed JSON
// Discord color codes: Green=3066993, Red=15158332, Yellow=16776960
discordEmbed(string title, string description, int color, string symbol, float price, float maFast, float maSlow) =>
    '{"embeds":[{' +
    '"title":"' + title + '",' +
    '"description":"' + description + '",' +
    '"color":' + str.tostring(color) + ',' +
    '"fields":[' +
    '{"name":"Symbol","value":"' + symbol + '","inline":true},' +
    '{"name":"Price","value":"$' + str.tostring(price, '#.##') + '","inline":true},' +
    '{"name":"Fast MA","value":"' + str.tostring(maFast, '#.##') + '","inline":true},' +
    '{"name":"Slow MA","value":"' + str.tostring(maSlow, '#.##') + '","inline":true}' +
    '],' +
    '"timestamp":"' + str.format("{0,date,yyyy-MM-dd'T'HH:mm:ss'Z'}", timenow) + '",' +
    '"footer":{"text":"TradingView Alert"}' +
    '}]}'

// ===== Alert Logic =====

if barstate.isconfirmed
    if buySignal
        string msg = discordEmbed(
             "🚀 Buy Signal Detected",
             "Fast MA crossed above Slow MA, indicating bullish momentum.",
             3066993,  // Green
             syminfo.ticker,
             close,
             maFast,
             maSlow
        )
        alert(msg, alert.freq_once_per_bar_close)
        log.info("Buy alert sent for " + syminfo.ticker)

    if sellSignal
        string msg = discordEmbed(
             "🔻 Sell Signal Detected",
             "Fast MA crossed below Slow MA, indicating bearish momentum.",
             15158332,  // Red
             syminfo.ticker,
             close,
             maFast,
             maSlow
        )
        alert(msg, alert.freq_once_per_bar_close)
        log.info("Sell alert sent for " + syminfo.ticker)

// ===== Visual Feedback =====
plot(maFast, "Fast MA", color.blue)
plot(maSlow, "Slow MA", color.orange)
plotshape(buySignal, "Buy", shape.triangleup, location.belowbar, color.green, size=size.small)
plotshape(sellSignal, "Sell", shape.triangledown, location.abovebar, color.red, size=size.small)
```

**Key features:**
- Sends rich embeds to Discord (not just plain text)
- Includes multiple fields (symbol, price, MA values)
- Color-coded (green for buy, red for sell)
- Timestamp in ISO 8601 format
- Footer for branding

### Example 3: Error-Resistant Alert with Comprehensive Validation

This example demonstrates defensive programming to prevent runtime errors from stopping alerts.

```pinescript
//@version=5
indicator("Error-Resistant Alert", overlay=true)

// ===== Inputs =====
int rsiLen = input.int(14, "RSI Length", minval=1, maxval=500)
float obLevel = input.float(70, "Overbought Level", minval=50, maxval=100)
float osLevel = input.float(30, "Oversold Level", minval=0, maxval=50)

// ===== Calculations =====

// Validate inputs
if rsiLen > bar_index
    runtime.error("RSI length exceeds available bars")

// Calculate RSI with error handling
float rsi = ta.rsi(close, rsiLen)

// Calculate signal with na checks
int signal = 0
if not na(rsi)
    if rsi > obLevel and rsi[1] <= obLevel
        signal := -1  // Overbought (sell)
    else if rsi < osLevel and rsi[1] >= osLevel
        signal := 1  // Oversold (buy)

// ===== Safe Alert Function =====

// Validate ALL values before building message
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

    // Attempt to send alert
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

**Key features:**
- Comprehensive input validation (minval, maxval)
- Runtime error detection (bar_index check)
- na value checking before all operations
- Value range validation (RSI must be 0-100)
- Detailed error logging
- Returns bool success indicator
- Prevents JSON corruption from invalid values

---

## Summary

This reference provides comprehensive coverage of Pine Script alerts and webhooks:

1. **Alert System Architecture** - Lifecycle, snapshots, account limits, notification channels
2. **Server-Side Execution Model** - Cloud execution, resource limits, debugging
3. **alert() Function Deep Dive** - Series string messages, frequency options, timing
4. **alertcondition() Function Deep Dive** - Legacy function, const string limitation, placeholders
5. **Webhook Integration Patterns** - Discord, Slack, custom APIs, TTE project patterns
6. **Rate Limiting and Throttling** - 15 alerts/3min limit, prevention strategies
7. **Runtime Error Handling** - Common errors, prevention patterns, error recovery
8. **Strategy Alerts** - Automated order fill alerts, broker integration
9. **Troubleshooting Guide** - Q&A for common alert issues
10. **Complete Examples** - Multi-symbol screener, Discord embeds, error-resistant alerts

For quick reference, see the "Alerts and Webhooks" section in SKILL.md. For advanced topics like repainting prevention, execution model details, and TTE project context, refer to the main SKILL.md file.
