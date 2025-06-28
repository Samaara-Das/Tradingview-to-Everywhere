# Point Capital Project Requirements

## Questions and Answers

### Q1: What are the names of these 3 new indicators?
**A:** They are Pine Script indicators similar to Premium Screener. The 3 screener indicators are:
1. "Order Block Screener"
2. "Structure break Screener" 
3. "Nadaraya Watson Screener"

### Q2: What kind of alert messages do these screeners generate?
**A:** Each screener gives JSON formatted alert messages. The alert messages that each give is inconsistent.

**Structure Break Screener:**
- Format: Ultra-compact JSON with abbreviated keys
- Example: `{"t":"sb","s":"BTCUSDT","tf":"1D","d":"bullish","zz":"ZZ1","ts":"2024-01-01 12:00:00","p":45000.50}`
- Multiple breaks: `{"1":{"t":"sb","s":"BTCUSDT","tf":"1D","d":"bullish","zz":"ZZ1","ts":"2024-01-01 12:00:00","p":45000.50},"2":{"t":"sb","s":"ETHUSDT","tf":"4H","d":"bearish","zz":"ZZ2","ts":"2024-01-01 12:00:00","p":3200.25}}`
- Fields:
  - t: Type, always "sb" for structure break
  - s: Symbol name
  - tf: Timeframe
  - d: Direction ("bullish" or "bearish")
  - zz: ZigZag degree ("ZZ1", "ZZ2", "ZZ3")
  - ts: Timestamp
  - p: Current price

**Nadaraya Watson Screener:**
- Format: Clean JSON structure
- Single Signal: `{"type":"nw","symbol":"BTCUSDT","timeframe":"1D","direction":"buy","timestamp":"2024-01-01 12:00:00"}`
- Multiple Signals: `{"1":{"type":"nw","symbol":"BTCUSDT","timeframe":"1D","direction":"buy","timestamp":"2024-01-01 12:00:00"},"2":{"type":"nw","symbol":"ETHUSDT","timeframe":"4H","direction":"sell","timestamp":"2024-01-01 12:00:00"}}`
- Fields:
  - type: Always "nw" for Nadaraya Watson
  - symbol: Trading pair (e.g., "BTCUSDT")
  - timeframe: Time period (e.g., "1D", "4H", "1W")
  - direction: "buy" or "sell"
  - timestamp: UTC timestamp

**Order Block Screener:**
- Format: Standard JSON structure
- Example: `{"timestamp": "2024-01-01T12:00:00Z","symbol": "BTCUSDT","timeframe": "240","signal_type": "buy_signal","ob_type": "bullish","ob_high": 45000.50000,"ob_low": 44500.25000,"current_price": 44750.00000}`
- Fields:
  - timestamp: ISO format timestamp
  - symbol: Trading symbol
  - timeframe: Timeframe string
  - signal_type: "buy_signal" or "sell_signal"
  - ob_type: "bullish" or "bearish"
  - ob_high: Order block high price
  - ob_low: Order block low price
  - current_price: Current market price

### Q3: What symbols should these screeners monitor?
**A:** They should use the same 1300+ symbols across 4 categories (US Stocks, Indian Stocks, Crypto, Currencies) as the current TTE system, and use the same grouping approach (5 symbols per alert).

### Q4: How should the data be stored in MongoDB?
**A:** All data should go into one collection with a field to identify which screener it came from. Do not use the existing "Entries" collection but create a new one called "Point Capitalis".

### Q5: Should the new system work alongside the existing TTE functionality, or replace it entirely?
**A:** Only modify the existing code to only work with these 3 new screeners. Keep the social media distribution features along with MongoDB storage. For now, disable the social media distribution features as the goal is to just get the alert messages from the TradingView website into a MongoDB database.

### Q6: Should the system still use TradingView layouts and setup?
**A:** 
- Browser automation setup should remain the same (Chrome profile, debugging port 9224, etc.)
- The 3 screeners are already installed and starred in TradingView
- User will need to create new TradingView layout(s) if needed - waiting for specific instructions

## Layout Requirements (PENDING USER RESPONSE)
The current TTE system uses:
- "Screener" layout: Has Premium Screener and Trade Drawer indicators
- "Exits" layout: Has Get Exits indicator

For the new Point Capital system, you will need to create a new layout. Here's what you should do:

**Create a new layout called "PointCapital" with:**
1. All 3 screeners added to the chart:
   - Order Block Screener
   - Structure break Screener 
   - Nadaraya Watson Screener
2. Save this layout in TradingView
3. Make sure all 3 indicators are visible on the chart

**CONFIRMED:** Single layout approach with all 3 screeners on one chart.

### Q7: How should alerts be created for these 3 screeners?
**A:** Create an alert for each screener which is on the layout. Each screener's inputs should be configured.

**Input Structure for New Screeners:**
- **SYMBOL SELECTION:**
  - Symbol 1, Symbol 2, Symbol 3, Symbol 4, Symbol 5
- **TIMEFRAME SELECTION:**  
  - 4H Timeframe, Daily Timeframe, Weekly Timeframe

**Code Changes Required:**
- The current code looks for "Used Symbols" input but new screeners use "Symbol 1", "Symbol 2", etc.
- Need to update input scraping logic to handle this new structure

### Q8: Should the system process alerts from all 3 screeners simultaneously?
**A:** Process one screener at a time as their alert messages appear in the alerts logs. Leave inputs for timeframe configuration in the GUI.

**Processing Approach:**
- Monitor alerts log for messages from any of the 3 screeners
- Process alerts sequentially as they appear
- GUI should allow configuration of timeframe settings for each screener

## Final Understanding Summary
- Replace existing TTE functionality with 3 new screeners
- Process 1300+ symbols across 4 categories using 5 symbols per alert
- Create 3 separate alerts per symbol set (one for each screener)
- Store all data in new "Point Capitalis" MongoDB collection
- Disable social media distribution initially (keep code for future)
- **KEEP screenshot functionality enabled**
- Process alerts sequentially as they appear in logs
- Update GUI to configure screener-specific settings
- Modify input scraping to handle new symbol input structure

## Next Steps
- Create detailed PRD in .taskmaster/docs/prd file
- Generate tasks using Task Master AI