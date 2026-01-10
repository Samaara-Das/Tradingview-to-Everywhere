# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TradingView to Everywhere (TTE) is an automated trading signals distribution system that bridges TradingView alerts with multiple social media platforms. It monitors TradingView for trading signals via Selenium browser automation, captures and processes them, and distributes formatted trade information to Discord, Facebook, Twitter/X, and Firebase Firestore.

## Commands

```bash
# Activate virtual environment
pipenv shell

# Install dependencies
pipenv install

# Run the main application (console mode)
python main.py

# Run with GUI
python gui.py

# Test Firebase connection
python database/test_firebase.py
```

## Architecture

### Data Flow
1. TradingView generates alerts based on Premium Screener indicator
2. TTE captures alert messages via Selenium (`handle_alerts.py`)
3. TTE navigates to relevant chart/timeframe (`open_entry_chart.py`)
4. Trade Drawer indicator draws entry with TP/SL levels
5. Screenshots captured and distributed to Discord, Twitter/X, Facebook
6. Entry stored in Firebase Firestore (`database/firebase_db.py`)
7. Exit monitor (`exits.py`) checks if entries hit TP/SL in last 15 days
8. Exit notifications distributed to all platforms

### Core Modules
- `main.py` - Entry point with main trading loop. Key constants: `SCREENER_SHORT`, `DRAWER_SHORT`, `INTERVAL_MINUTES`, `START_FRESH`
- `open_tv.py` - Selenium browser automation. Key constants: `SYMBOL_INPUTS`, `CHART_TIMEFRAME`, `LAYOUT_NAME`
- `handle_alerts.py` - Alert message parsing and entry extraction
- `exits.py` - Monitors Firebase for entries that hit TP/SL targets
- `env.py` - Environment configuration. `PROFILE` (Chrome profile), `COLLECTION` (Firestore collection name)

### Database
Uses Firebase Firestore (migrated from MongoDB). Collection name configured in `env.py` as `COLLECTION`.

Document schema:
- `direction`, `symbol`, `timeframe`, `category`
- `entryPrice`, `slPrice`, `tp1Price`, `tp2Price`, `tp3Price`
- `tvEntrySnapshot`, `pngEntrySnapshot`, `tvExitSnapshot`, `pngExitSnapshot`
- `unixTime`, `content`
- `isSlHit`, `isTp1Hit`, `isTp2Hit`, `isTp3Hit`

### Social Distribution (`send_to_socials/`)
- `discord.py` - Webhook-based posting to category-specific channels
- `twitter.py` - X API integration
- `_facebook.py` - Facebook posting (prefixed with `_` when inactive)

## Configuration

### Required Environment Variables
- `CHROME_PROFILES_PATH` - Path to Chrome user data folder
- `TRADINGVIEW_EMAIL` / `TRADINGVIEW_PASSWORD` - TradingView login (2FA must be disabled, no linked social accounts)
- `FIREBASE_PROJECT_ID` / `FIREBASE_CREDENTIALS_PATH` - Firebase authentication
- Discord webhook URLs and Twitter API keys in `.env` file

### TradingView Setup
- Saved layout "Screener" with Premium Screener + Trade Drawer indicators
- Saved layout "Exits" with Get Exits indicator
- Both indicators must be starred/favorited
- Alerts log must be visible (not minimized)

### Symbol Categories
Configured in `resources/symbol_settings.py`: Currencies, US Stocks, Indian Stocks, Crypto. Each category has separate Discord channels for entries, exits, and before-and-after.

## Critical Notes

- Never interact with the Selenium-controlled browser manually
- Close all Chrome browsers before running
- `START_FRESH=True` deletes all existing alerts and creates new ones
- `START_FRESH=False` keeps existing alerts and reads unread messages
- Browser refreshes every `INTERVAL_MINUTES` (default: 10) to prevent freezing
- Log file: `app_log.log` (auto-trimmed to prevent overflow)

## Lessons Learned

When making mistakes, ALWAYS document them in `AGENTS.md` to prevent repetition.

---

## Pine Script Development Guide

This section contains essential knowledge for working with Pine Script indicators in this project, particularly the TTE Screener and related indicators.

### Execution Model: The Foundation

**Bar-by-Bar Processing**: Pine Script executes once per bar, from the oldest historical bar to the most recent. On each execution:
- Built-in variables (`open`, `high`, `low`, `close`, `volume`) update to reflect the current bar
- Variables without `var` keyword reinitialize on every bar
- Variables with `var` keyword persist across bars (declared once, retain value)
- Variables with `varip` keyword persist across all ticks within realtime bars

**Historical vs Realtime Bars**:
- **Historical bars**: Execute once with final confirmed OHLCV values
- **Realtime bars**: Execute multiple times per tick with fluctuating values; a "rollback" resets data before each recalculation

**Time Series & History Reference**: The `[]` operator accesses historical values:
```pinescript
close[1]   // Previous bar's close
close[10]  // Close from 10 bars ago
```
History buffers store up to 5,000 bars. **Critical**: The `[]` operator only works reliably in global scope. In local scopes (conditionals, loops, functions), it may reference non-consecutive bars due to fragmented buffers.

### request.security(): Multi-Symbol/Timeframe Data

The TTE Screener heavily uses `request.security()` to monitor multiple symbols. Key parameters:

```pinescript
request.security(symbol, timeframe, expression, gaps, lookahead, ignore_invalid_symbol)
```

**gaps parameter**:
- `barmerge.gaps_off` (default): Fills gaps with last values on historical bars
- `barmerge.gaps_on`: Returns `na` when no new confirmed data

**lookahead parameter** (critical for avoiding repainting):
- `barmerge.lookahead_off` (default): No lookahead, but can repaint on realtime bars
- `barmerge.lookahead_on`: Use with `[1]` offset to get confirmed data only

**Best Practice for Non-Repainting HTF Data**:
```pinescript
// CORRECT: Gets confirmed higher-timeframe data without repainting
htf_close = request.security(symbol, "D", close[1], lookahead = barmerge.lookahead_on)

// WRONG: Will repaint - shows unconfirmed realtime values
htf_close = request.security(symbol, "D", close)
```

**Performance Note**: Each `request.security()` call adds computational overhead. The screener currently supports 5 symbols; increasing to 10+ requires careful optimization.

### Avoiding Repainting

Repainting occurs when historical calculations differ from realtime calculations. For reliable alerts:

1. **Use confirmed bar data**: Add `and barstate.isconfirmed` or use `[1]` offset
2. **request.security() with lookahead + offset**: Always use `expression[1]` with `lookahead_on`
3. **Avoid `timenow`**: It changes every execution
4. **Use `alert.freq_once_per_bar_close`**: Triggers only on confirmed bar close

```pinescript
// Non-repainting alert pattern
if condition[1] and barstate.isconfirmed
    alert(message, alert.freq_once_per_bar_close)
```

### User-Defined Types (Objects)

Use UDTs to organize related data, especially useful in screeners:

```pinescript
type TradeSignal
    string symbol
    string direction
    float entryPrice
    float slPrice
    float tp1Price

// Create instance
signal = TradeSignal.new("EURUSD", "Buy", 1.0850, 1.0800, 1.0900)

// Access fields
signal.entryPrice
signal.direction
```

**When to Use Objects**:
- Grouping related values that travel together (trade signals, indicator settings)
- Storing in arrays/matrices for collections of similar items
- Making code more readable and maintainable

**Important**: Objects are assigned by reference. Use `.copy()` for independent copies.

### Arrays

Arrays store multiple values of the same type. Essential for screeners that collect signals:

```pinescript
var array<string> entries = array.new_string(0)

// Add elements
array.push(entries, newSignal)

// Loop through
for entry in entries
    // process each entry

// Get size
array.size(entries)

// Join for alert message
alert_msg = array.join(entries, ", ")
```

**Key Constraints**:
- Maximum 100,000 elements
- All elements must be same type
- Use `var` to persist across bars (otherwise reinitializes each bar)

### Functions Best Practices

```pinescript
// Single-line for simple calculations
sma(src, len) => ta.sma(src, len)

// Multi-line for complex logic
calculateEntry(direction, swingBar) =>
    float entry = na
    float sl = na
    if direction == "Buy"
        entry := close > open ? open : close
        sl := low[bar_index - swingBar]
    [entry, sl]
```

**Limitations**:
- Cannot modify global variables (read-only access)
- Cannot call themselves (no recursion)
- Cannot call global-only built-ins like `plot()` or `indicator()`
- Must maintain consistent return types across executions

### Alerts in Pine Script

The TTE Screener uses `alert()` for JSON-formatted messages:

```pinescript
// Dynamic message construction
alert(message, alert.freq_once_per_bar)
```

**Frequency Options**:
- `alert.freq_once_per_bar`: Once when condition first true (default)
- `alert.freq_once_per_bar_close`: Only on confirmed bar close (prevents repainting)
- `alert.freq_all`: Every time condition is true

**Critical**: Alerts only trigger on realtime bars. Historical bars never execute alert logic.

### Time Handling

Pine uses UNIX timestamps in milliseconds. Key variables:
- `time`: Current bar's opening timestamp
- `time_close`: Bar's closing timestamp
- `timenow`: Current execution time (causes repainting)

```pinescript
// Format time for alerts
str.format_time(time, "HH:mm:ss dd-MM-yyyy", "Asia/Kolkata")
```

Use IANA timezone identifiers (e.g., "Asia/Kolkata") for automatic DST handling.

### Screener Optimization Guidelines

For the TTE Screener and similar multi-symbol indicators:

1. **Minimize calculations per symbol**: Extract only essential logic into the `request.security()` expression
2. **Use simple types in security calls**: Return tuples of primitives rather than objects
3. **Avoid redundant calculations**: Calculate shared values once in global scope
4. **Limit indicator complexity**: Each additional indicator in the screener function multiplies computation
5. **Consider bar lookback**: Reduce `maxBarsBack` where possible to limit memory usage
6. **Test with increasing symbols**: Performance degrades non-linearly; test at target symbol count

