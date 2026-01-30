# Glossary
# TTE Tiered Screener Architecture

This document defines key terms used throughout the project documentation.

---

## Trading Concepts

### NWE (Nadaraya-Watson Envelope)
A technical indicator using kernel regression to create dynamic support/resistance zones. Price entering these zones suggests potential reversal areas.

**Zone Structure:**
```
upper_far   ─────  Bearish zone (furthest from regression)
upper_avg   ─────  Bearish zone (middle)
upper_near  ─────  Bearish zone (closest to regression)
yhat        ═════  Regression line (not a zone)
lower_near  ─────  Bullish zone (closest to regression)
lower_avg   ─────  Bullish zone (middle)
lower_far   ─────  Bullish zone (furthest from regression)
```

### OB (Order Block)
A price zone where institutional orders were placed. Identified by the last opposing candle before a strong move. Price often reacts when returning to these zones.

- **Bullish OB**: Last bearish candle before strong upward move
- **Bearish OB**: Last bullish candle before strong downward move

### FVG (Fair Value Gap)
A price imbalance created when a candle's body doesn't overlap with the previous candle's wick, leaving a "gap" in price action.

- **Bullish FVG**: Gap below price (support)
- **Bearish FVG**: Gap above price (resistance)

### Breaker
An Order Block that has been "broken" (price traded through it) and now acts as the opposite type of support/resistance.

- **Breaker Support**: Former bearish OB now acting as support
- **Breaker Resistance**: Former bullish OB now acting as resistance

### Divergence
When price makes a new high/low but the oscillator doesn't confirm, suggesting potential reversal.

**Types in this project:**
- **Logic 2**: Divergence across two separate oscillator ranges
- **Internal**: Divergence within a single oscillator range
- **Logic 1**: Traditional divergence (not used in current implementation)

### Kernel Regression
A non-parametric regression technique using the Rational Quadratic kernel function. Creates smooth trend lines that adapt to price action.

**Parameters:**
- **h (bandwidth)**: Smoothing factor - higher = smoother
- **alpha**: Shape parameter
- **x0**: Lookback period

### Kernel AO (Awesome Oscillator)
Custom oscillator calculated as: `kernelFast - kernelSlow`
- Fast kernel: h=5, alpha=8, x0=25
- Slow kernel: h=34, alpha=3, x0=120

---

## Architecture Terms

### Tier 1
The first screening layer. NWE-only screeners that monitor many symbols (20 each) for zone entries. Lightweight and always running.

### Tier 2
The second screening layer. OB+DIV screener that checks "hot" symbols for confluence. Only runs when Tier 1 triggers.

### Hot List
Collection of symbols that have triggered NWE zone entry (Tier 1) and are awaiting Tier 2 confirmation.

**Statuses:**
- `pending_tier2`: Awaiting OB+DIV check
- `tier2_complete`: OB+DIV check done
- `expired`: No longer valid (24hr timeout)

### Hot Symbol
A symbol currently on the hot list with an active NWE signal.

### Signal Level
Quality indicator based on how many conditions are met:

| Level | Conditions | Quality |
|-------|------------|---------|
| 1 | NWE only | Low |
| 2 | NWE + OB/FVG | Medium |
| 3 | NWE + OB/FVG + Divergence | High |

### Webhook
HTTP POST request sent automatically by TradingView when alert conditions are met. Contains JSON payload with signal data.

### Orchestrator
Python service that coordinates the tiered system:
1. Polls API for hot symbols
2. Updates Tier 2 screener via Selenium
3. Captures screenshots
4. Updates signal records

---

## Timeframe Abbreviations

| Code | Meaning | Pine Script |
|------|---------|-------------|
| H4 | 4-hour | "240" |
| D1 | Daily | "D" |
| W1 | Weekly | "W" |
| H1 | 1-hour | "60" |
| M15 | 15-minute | "15" |

---

## Technical Terms

### request.security()
Pine Script function to fetch data from different symbols/timeframes. Limited to 40 calls per script (64 with Ultimate plan).

### barstate.isconfirmed
Pine Script variable that's true only when the current bar has closed. Used for non-repainting signals.

### Selenium
Browser automation framework used to control TradingView for:
- Updating indicator symbol inputs
- Capturing chart screenshots
- Navigating between charts

### MongoDB Atlas
Cloud-hosted MongoDB database service used for storing hot list and signals.

### Vercel
Serverless hosting platform for Stock Buddy Next.js application.

### React Query
Data fetching library for React that handles caching, refetching, and state management.

---

## Signal Directions

### Bullish
Expecting price to go UP. Associated with:
- Lower NWE zones (lower_near, lower_avg, lower_far)
- Bullish OB, Bullish FVG, Breaker Support
- Bullish divergence (higher lows on oscillator)

### Bearish
Expecting price to go DOWN. Associated with:
- Upper NWE zones (upper_near, upper_avg, upper_far)
- Bearish OB, Bearish FVG, Breaker Resistance
- Bearish divergence (lower highs on oscillator)

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/nwe` | POST | Receive Tier 1 webhooks |
| `/api/obdiv` | POST | Receive Tier 2 webhooks |
| `/api/signals` | GET | Fetch signals for dashboard |
| `/api/signals/[id]` | PATCH | Update signal (screenshot) |
| `/api/hot-symbols` | GET | Get pending hot symbols |

---

## File Naming Conventions

| Pattern | Meaning |
|---------|---------|
| `TTE` | TradingView to Everywhere |
| `NWE` | Nadaraya-Watson Envelope |
| `OBDIV` | Order Block + Divergence |
| `v2` | Version 2 (webhook-based) |
| `_h4`, `_d1`, `_w1` | Timeframe suffix |
| `bull`, `bear` | Direction prefix |

---

## Abbreviations

| Abbrev | Full Term |
|--------|-----------|
| TTE | TradingView to Everywhere |
| NWE | Nadaraya-Watson Envelope |
| OB | Order Block |
| FVG | Fair Value Gap |
| DIV | Divergence |
| TF | Timeframe |
| API | Application Programming Interface |
| DB | Database |
| UI | User Interface |
| UX | User Experience |
| PRD | Product Requirements Document |
| ADR | Architecture Decision Record |

---

*This glossary is maintained as part of the TTE project documentation.*
