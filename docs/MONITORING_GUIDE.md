# Monitoring Guide
# TTE Tiered Screener Architecture

This document describes what to monitor, how to set up alerts, and troubleshooting procedures.

---

## Table of Contents

1. [Monitoring Overview](#monitoring-overview)
2. [Key Metrics](#key-metrics)
3. [Dashboards](#dashboards)
4. [Alert Configuration](#alert-configuration)
5. [Log Analysis](#log-analysis)
6. [Troubleshooting Playbooks](#troubleshooting-playbooks)

---

## Monitoring Overview

### System Components to Monitor

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MONITORING ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │  TradingView    │    │  Stock Buddy    │    │    MongoDB      │ │
│  │   Screeners     │───▶│  (Vercel)       │───▶│    Atlas        │ │
│  │                 │    │                 │    │                 │ │
│  │ Monitor:        │    │ Monitor:        │    │ Monitor:        │ │
│  │ - Alert firing  │    │ - Function logs │    │ - Connections   │ │
│  │ - Webhook send  │    │ - Error rates   │    │ - Query perf    │ │
│  │                 │    │ - Latency       │    │ - Storage       │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │    Python       │    │   Dashboard     │    │    Alerts       │ │
│  │  Orchestrator   │    │   (Browser)     │    │   (Discord)     │ │
│  │                 │    │                 │    │                 │ │
│  │ Monitor:        │    │ Monitor:        │    │ Monitor:        │ │
│  │ - Process alive │    │ - Load time     │    │ - Delivery rate │ │
│  │ - Screenshot OK │    │ - API errors    │    │ - Webhook OK    │ │
│  │ - Selenium err  │    │ - Real-time     │    │                 │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Metrics

### Stock Buddy API (Vercel)

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| Function Invocations | Total API calls | - | > 10,000/day |
| Error Rate | 4xx/5xx responses | < 1% | > 5% |
| Cold Start Duration | First invocation time | < 500ms | > 2000ms |
| Function Duration | Execution time | < 200ms | > 1000ms |
| Bandwidth | Data transferred | - | > 100MB/day |

### MongoDB Atlas

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| Connections | Active connections | < 50 | > 100 |
| Operations/sec | Read/write ops | - | > 1000/sec |
| Document Count (hot_list) | Pending symbols | < 50 | > 100 |
| Document Count (signals) | Total signals | - | Growth > 500/day |
| Query Time | Average execution | < 50ms | > 500ms |
| Storage Used | Database size | - | > 80% of limit |

### Python Orchestrator

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| Process Uptime | Time since start | 24/7 | Restart detected |
| Poll Success Rate | Successful API polls | 100% | < 95% |
| Screenshot Success | Successful captures | > 95% | < 80% |
| Selenium Errors | Browser automation failures | 0 | > 5/hour |
| Memory Usage | Process memory | < 500MB | > 1GB |
| CPU Usage | Process CPU | < 20% | > 80% |

### Signal Flow

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| Tier 1 Alerts/Day | NWE webhook count | 10-50 | 0 for 4 hours |
| Tier 2 Checks/Day | OBDIV webhook count | 5-30 | 0 for 4 hours |
| Signal Creation Rate | New signals/day | 5-20 | 0 for 8 hours |
| Hot List Staleness | Oldest pending item | < 1 hour | > 4 hours |
| Screenshot Pending | Signals without screenshot | 0 | > 10 |

---

## Dashboards

### Vercel Dashboard

**Location**: https://vercel.com/dashboard

**Key Views**:
1. **Deployments** - Recent deployments and status
2. **Analytics** - Traffic and performance metrics
3. **Logs** - Real-time function logs
4. **Usage** - Bandwidth and function invocations

**Custom Filters for Logs**:
```
# Error logs only
level:error

# Specific endpoint
path:/api/nwe

# Slow requests
duration:>1000
```

### MongoDB Atlas Dashboard

**Location**: https://cloud.mongodb.com

**Key Views**:
1. **Metrics** - Real-time cluster metrics
2. **Performance Advisor** - Query optimization suggestions
3. **Real-Time Performance** - Live query analysis
4. **Alerts** - Configured alerts

**Useful Aggregations**:
```javascript
// Signals per day
db.signals.aggregate([
  { $group: {
    _id: { $dateToString: { format: "%Y-%m-%d", date: "$created_at" } },
    count: { $sum: 1 }
  }},
  { $sort: { _id: -1 } },
  { $limit: 7 }
])

// Hot list by status
db.hot_list.aggregate([
  { $group: { _id: "$status", count: { $sum: 1 } } }
])

// Average signal level
db.signals.aggregate([
  { $group: { _id: null, avgLevel: { $avg: "$level" } } }
])
```

### Python Orchestrator Logs

**Location**: `app_log.log` in project directory

**Log Format**:
```
2026-01-29 14:30:00 INFO [orchestrator] Polling for hot symbols...
2026-01-29 14:30:01 INFO [orchestrator] Found 3 pending symbols
2026-01-29 14:30:05 INFO [selenium] Updating OBDIV screener symbols
2026-01-29 14:30:30 INFO [selenium] Screenshot captured for GBPAUD
2026-01-29 14:30:31 INFO [api] Updated signal 65b7c123 with screenshot
```

**Log Analysis Commands**:
```bash
# Recent errors
grep -i error app_log.log | tail -20

# Screenshot failures
grep -i "screenshot failed" app_log.log

# API communication
grep -i "\[api\]" app_log.log | tail -50

# Count events by type
grep -oP '\[[\w]+\]' app_log.log | sort | uniq -c
```

---

## Alert Configuration

### Vercel Alerts

Configure in Vercel Dashboard → Project → Settings → Notifications

1. **Deployment Failed**
   - Trigger: Build or deployment fails
   - Action: Slack/Email notification

2. **High Error Rate**
   - Trigger: Error rate > 5% for 5 minutes
   - Action: Slack/Email notification

### MongoDB Atlas Alerts

Configure in Atlas → Project → Alerts

1. **Connection Spike**
   ```
   Condition: Connections > 100
   For: 5 minutes
   Notification: Email
   ```

2. **High Query Time**
   ```
   Condition: Query Targeting: Scanned Objects / Returned > 1000
   For: 10 minutes
   Notification: Email
   ```

3. **Storage Warning**
   ```
   Condition: Data Size > 80% of limit
   Notification: Email
   ```

### Custom Monitoring (Discord Webhook)

Add to Python orchestrator for custom alerts:

```python
import requests
from datetime import datetime

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/..."

def send_alert(title: str, message: str, severity: str = "warning"):
    """Send alert to Discord monitoring channel."""
    color = {
        "info": 0x3498db,
        "warning": 0xf39c12,
        "error": 0xe74c3c,
        "success": 0x2ecc71
    }.get(severity, 0x95a5a6)

    payload = {
        "embeds": [{
            "title": f"🚨 {title}",
            "description": message,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "TTE Monitoring"}
        }]
    }

    requests.post(DISCORD_WEBHOOK_URL, json=payload)

# Example usage
send_alert(
    "Screenshot Failure",
    "Failed to capture screenshot for GBPAUD after 3 retries",
    "error"
)
```

### Heartbeat Monitoring

Use a service like UptimeRobot or Healthchecks.io:

```python
import requests

HEALTHCHECK_URL = "https://hc-ping.com/your-uuid"

def send_heartbeat():
    """Send heartbeat to monitoring service."""
    try:
        requests.get(HEALTHCHECK_URL, timeout=10)
    except:
        pass  # Don't fail on monitoring errors

# Call every poll cycle
def poll_cycle():
    # ... normal poll logic ...
    send_heartbeat()
```

---

## Log Analysis

### Common Log Patterns

**Successful Signal Flow**:
```
14:30:00 INFO NWE webhook received: GBPAUD bullish
14:30:01 INFO Added GBPAUD to hot list
14:35:00 INFO OBDIV webhook received: GBPAUD
14:35:01 INFO Signal created: level 3, bullish
14:40:00 INFO Screenshot captured for signal 65b7c123
14:40:01 INFO Signal updated with screenshot URL
```

**API Connection Failure**:
```
14:30:00 ERROR Failed to poll hot symbols: Connection refused
14:30:05 WARN Retrying poll (attempt 2/3)
14:30:10 ERROR Failed to poll hot symbols: Connection refused
14:30:15 WARN Retrying poll (attempt 3/3)
14:30:20 ERROR All retries exhausted, skipping poll cycle
```

**Selenium Failure**:
```
14:30:00 INFO Updating OBDIV screener symbols
14:30:05 ERROR Selenium error: Element not found (symbol_input_1)
14:30:06 WARN Refreshing page and retrying
14:30:15 INFO Retry successful
```

### Log Aggregation Queries

**Errors by Hour**:
```bash
grep ERROR app_log.log | cut -d' ' -f1,2 | cut -d':' -f1,2 | uniq -c
```

**Response Times**:
```bash
grep "API response" app_log.log | grep -oP '\d+ms' | sort -n | tail -10
```

**Signal Creation Rate**:
```bash
grep "Signal created" app_log.log | cut -d' ' -f1 | uniq -c
```

---

## Troubleshooting Playbooks

### Playbook: No Signals for 4+ Hours

**Symptoms**:
- Dashboard shows no new signals
- Last signal older than 4 hours

**Investigation Steps**:

1. **Check TradingView Alerts**
   - Open TradingView → Alerts panel
   - Verify alerts are active (not paused)
   - Check last trigger time

2. **Check Vercel Function Logs**
   ```bash
   # Look for recent webhook calls
   vercel logs --filter "path:/api/nwe"
   ```

3. **Check MongoDB Hot List**
   ```javascript
   db.hot_list.find({ status: "pending_tier2" }).sort({ updated_at: -1 })
   ```

4. **Check Python Orchestrator**
   ```bash
   # Is it running?
   ps aux | grep "python main.py"

   # Check recent logs
   tail -100 app_log.log | grep -E "(ERROR|WARN)"
   ```

**Resolution**:
- If TradingView alerts not firing: Check market hours, verify screener logic
- If webhooks not reaching API: Check Vercel deployment, verify webhook URL
- If hot list has items: Check Python orchestrator, may need restart
- If orchestrator down: Restart the process

---

### Playbook: High Error Rate on API

**Symptoms**:
- Vercel dashboard shows > 5% error rate
- Users report dashboard not loading

**Investigation Steps**:

1. **Identify Error Type**
   ```bash
   vercel logs --filter "level:error" | head -50
   ```

2. **Check MongoDB Connection**
   ```bash
   # Test connection string
   mongosh "$MONGODB_URI" --eval "db.adminCommand('ping')"
   ```

3. **Check for Rate Limiting**
   - Look for 429 errors in logs
   - Check request volume

4. **Check Deployment**
   ```bash
   vercel ls
   # Verify latest deployment is healthy
   ```

**Resolution**:
- MongoDB connection: Check Atlas status, verify IP whitelist
- Rate limiting: Reduce request frequency, implement caching
- Deployment issue: Rollback to previous version

---

### Playbook: Screenshot Failures

**Symptoms**:
- Signals missing screenshots
- Python logs show Selenium errors

**Investigation Steps**:

1. **Check Chrome/Selenium**
   ```bash
   # Is Chrome closed (required for Selenium)?
   tasklist | grep chrome  # Windows
   pgrep chrome            # Linux/Mac
   ```

2. **Check TradingView Session**
   - May need to re-login
   - Check if session expired

3. **Check Selenium Logs**
   ```bash
   grep -i selenium app_log.log | tail -50
   ```

4. **Test Manual Screenshot**
   ```python
   from open_tv import get_driver
   driver = get_driver()
   driver.get("https://www.tradingview.com/chart")
   driver.save_screenshot("test.png")
   driver.quit()
   ```

**Resolution**:
- Chrome running: Close all Chrome windows
- Session expired: Re-login to TradingView
- Selenium error: Update ChromeDriver, check Chrome version
- Element not found: TradingView UI may have changed

---

### Playbook: Database Performance Degradation

**Symptoms**:
- Slow API responses
- Dashboard taking long to load

**Investigation Steps**:

1. **Check Atlas Metrics**
   - Look at Query Targeting ratio
   - Check index usage

2. **Identify Slow Queries**
   ```javascript
   // In MongoDB Atlas, enable profiling
   db.setProfilingLevel(1, { slowms: 100 })

   // Check slow queries
   db.system.profile.find().sort({ ts: -1 }).limit(10)
   ```

3. **Check Collection Sizes**
   ```javascript
   db.signals.stats()
   db.hot_list.stats()
   ```

**Resolution**:
- Missing index: Create appropriate indexes
- Large collection: Implement data archival
- High traffic: Consider read replicas

---

## Health Check Endpoints

Add to Stock Buddy for monitoring:

```typescript
// pages/api/health.ts
export default function handler(req, res) {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 7) || 'dev'
  });
}

// pages/api/health/db.ts
import clientPromise from '@/lib/mongodb';

export default async function handler(req, res) {
  try {
    const client = await clientPromise;
    await client.db().admin().ping();
    res.status(200).json({ database: 'connected' });
  } catch (error) {
    res.status(503).json({ database: 'disconnected', error: error.message });
  }
}
```

---

*Last updated: 2026-01-29*
