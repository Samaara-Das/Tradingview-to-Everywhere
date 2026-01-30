# ADR-002: Webhook-Based Alert Delivery vs Alert Scraping

**Status:** Accepted
**Date:** 2026-01-29
**Decision Makers:** Development Team
**Category:** Integration

---

## Context

The TTE system needs to receive trading signals from TradingView screeners. There were two approaches to consider:

1. **Alert Scraping (Previous Approach)**
   - Python/Selenium opens TradingView alerts panel
   - Reads unread alert messages from the DOM
   - Parses alert text to extract signal data

2. **Webhook Delivery (New Approach)**
   - TradingView sends HTTP POST to our API endpoint
   - API receives structured JSON payload
   - No browser automation needed for alert receipt

---

## Decision

We chose **Webhook-Based Alert Delivery** for Tier 1 and Tier 2 screeners.

### Implementation

```
┌─────────────────┐     HTTP POST      ┌─────────────────┐
│   TradingView   │────────────────────│   Stock Buddy   │
│    Screener     │   JSON Payload     │      API        │
│                 │                    │    (Vercel)     │
└─────────────────┘                    └─────────────────┘
        │                                      │
        │ alert("{{alert.message}}")           │
        │                                      │
        │ Webhook URL configured               │
        │ in TradingView alert                 │
        ▼                                      ▼
   Pine Script                           /api/nwe or
   alert() call                          /api/obdiv
```

### Webhook Payload Example

```json
{
  "tier": "nwe",
  "symbol": "GBPAUD",
  "direction": "bullish",
  "timeframes": ["H4", "D1"],
  "timestamp": 1672531200
}
```

---

## Rationale

### Why Webhooks Over Scraping

| Factor | Webhooks | Scraping |
|--------|----------|----------|
| **Latency** | Instant (~1 second) | 5-30 seconds (poll interval) |
| **Reliability** | HTTP is robust | DOM changes can break scraping |
| **Scalability** | Handles high volume | Sequential processing |
| **Maintenance** | Stable contract | TradingView UI changes break scraping |
| **Resources** | Minimal server compute | Requires browser running 24/7 |

### Specific Benefits

1. **Instant Delivery**
   - Webhook fires immediately when alert triggers
   - No waiting for next poll cycle
   - Critical for time-sensitive trading signals

2. **Structured Data**
   - JSON payload is explicitly defined
   - No text parsing or regex extraction
   - Validation is straightforward

3. **Decoupled Components**
   - API can be deployed independently
   - No dependency on browser automation for alerts
   - Easier testing and debugging

4. **Error Handling**
   - HTTP status codes provide clear feedback
   - Can implement retry logic
   - Webhook delivery logs in TradingView

### Previous Scraping Approach (Reference)

```python
# Old approach - Alert scraping
def scrape_alerts(driver):
    alerts_panel = driver.find_element(By.CSS_SELECTOR, ".alerts-panel")
    unread_alerts = alerts_panel.find_elements(By.CSS_SELECTOR, ".unread-alert")

    for alert in unread_alerts:
        text = alert.text
        # Parse alert text with regex
        match = re.match(r"(\w+) (BUY|SELL) Level (\d)", text)
        if match:
            symbol, direction, level = match.groups()
            # Process signal...
```

Problems with this approach:
- Brittle regex parsing
- CSS selectors change with TradingView updates
- Race conditions with DOM updates
- Browser must be running 24/7

---

## Consequences

### Positive

- **Faster Signal Processing**: Instant webhook delivery vs polling delay
- **More Reliable**: HTTP is stable; DOM scraping is fragile
- **Cleaner Architecture**: API receives structured data directly
- **Reduced Browser Usage**: Selenium only needed for screenshots

### Negative

- **Requires External API**: Need to deploy and maintain Stock Buddy
- **Webhook Limitations**: TradingView webhooks cannot include images
- **Network Dependency**: Requires internet connectivity
- **Webhook URL Exposure**: URL is somewhat public (obscurity only)

### Mitigations

- **API Deployment**: Vercel free tier is sufficient
- **Screenshots**: Python/Selenium handles screenshot capture separately
- **Network**: Vercel has high availability; TradingView retries failed webhooks
- **Security**: Webhook secret validation implemented

---

## Implementation Notes

### TradingView Alert Configuration

```
Condition: TTE NWE Screener → Any alert() function call
Actions:
  - Webhook URL: https://stock-buddy-app.vercel.app/api/nwe
  - Message: {{alert.message}}
Expiration: Open-ended
```

### Pine Script Alert Code

```pinescript
// Build JSON payload
payload = '{"tier":"nwe","symbol":"' + symbol + '","direction":"' + direction + '"}'

// Fire alert with webhook
if signalCondition
    alert(payload, alert.freq_once_per_bar_close)
```

### API Endpoint

```typescript
// pages/api/nwe.ts
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { tier, symbol, direction, timeframes, secret } = req.body;

  // Validate secret (optional)
  if (process.env.WEBHOOK_SECRET && secret !== process.env.WEBHOOK_SECRET) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  // Process webhook...
}
```

---

## Where Selenium Is Still Used

Webhooks replaced alert scraping, but Selenium is still required for:

1. **Screenshot Capture**
   - TradingView webhooks cannot include chart images
   - Python navigates to chart and captures screenshot
   - Screenshot URL stored in signal record

2. **Dynamic Symbol Updates**
   - Tier 2 screener needs symbol inputs changed
   - Python uses Selenium to update TradingView indicator settings

---

## Related Decisions

- [ADR-001: Tiered Screener Architecture](001-tiered-architecture.md)
- [ADR-003: Remove NWE from Tier 2](003-remove-nwe-from-tier2.md)

---

## References

- TradingView Webhook Documentation
- Previous point-capital branch (alert scraping implementation)
- Stock Buddy API implementation plan
