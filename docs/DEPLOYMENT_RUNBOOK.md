# Deployment Runbook
# TTE Tiered Screener Architecture

This document provides step-by-step deployment procedures for all system components.

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Component Deployments](#component-deployments)
   - [Stock Buddy (Vercel)](#stock-buddy-vercel)
   - [TradingView Screeners](#tradingview-screeners)
   - [Python Orchestrator](#python-orchestrator)
3. [Post-Deployment Verification](#post-deployment-verification)
4. [Rollback Procedures](#rollback-procedures)
5. [Emergency Contacts](#emergency-contacts)

---

## Pre-Deployment Checklist

### Before Any Deployment

- [ ] All tests passing in CI/CD pipeline
- [ ] Code reviewed and approved
- [ ] Database migrations tested (if any)
- [ ] Environment variables configured
- [ ] Monitoring alerts configured
- [ ] Rollback plan documented
- [ ] Team notified of deployment window

### Environment Verification

```bash
# Stock Buddy - Verify environment variables in Vercel
vercel env ls

# Python Orchestrator - Verify .env file
cat .env | grep -E "^[A-Z_]+=.+"

# MongoDB - Verify connection
mongosh "$MONGODB_URI" --eval "db.adminCommand('ping')"
```

---

## Component Deployments

### Stock Buddy (Vercel)

#### First-Time Setup

1. **Create Vercel Project**
   ```bash
   cd stock-buddy
   vercel link
   ```

2. **Configure Environment Variables**
   ```bash
   # Set production environment variables
   vercel env add MONGODB_URI production
   vercel env add WEBHOOK_SECRET production
   ```

3. **Deploy to Production**
   ```bash
   vercel --prod
   ```

#### Routine Deployment

1. **Deploy from main branch**
   ```bash
   git checkout main
   git pull origin main
   vercel --prod
   ```

2. **Verify deployment**
   ```bash
   # Check deployment status
   vercel ls

   # Test API endpoints
   curl https://stock-buddy-app.vercel.app/api/signals?limit=1
   ```

#### Deployment via Git (Automatic)

Vercel automatically deploys when:
- Push to `main` branch → Production deployment
- Push to feature branch → Preview deployment

---

### TradingView Screeners

#### TTE NWE Screener (Tier 1)

1. **Open TradingView Pine Editor**
   - Go to tradingview.com/chart
   - Open Pine Editor (bottom panel)

2. **Create New Indicator**
   - Click "Open" → "New indicator"
   - Paste code from `Pine Script Code/TTE NWE Screener v2.txt`
   - Click "Save" → Name: "TTE NWE Screener v2"

3. **Add to Chart**
   - Click "Add to chart"
   - Verify it compiles without errors

4. **Configure Alert**
   - Right-click indicator → "Add Alert"
   - Condition: "TTE NWE Screener v2" → "Any alert() function call"
   - Webhook URL: `https://stock-buddy-app.vercel.app/api/nwe`
   - Message: `{{alert.message}}`
   - Expiration: "Open-ended"
   - Alert name: "TTE NWE Tier 1"

5. **Verify Alert**
   - Wait for market hours
   - Check Stock Buddy API logs for incoming webhooks

#### TTE OBDIV Screener (Tier 2)

1. **Create Indicator**
   - Same process as NWE Screener
   - Use code from `Pine Script Code/TTE OBDIV Screener.txt`
   - Name: "TTE OBDIV Screener"

2. **Configure Alert**
   - Webhook URL: `https://stock-buddy-app.vercel.app/api/obdiv`
   - Alert name: "TTE OBDIV Tier 2"

3. **Save Chart Layout**
   - Save layout as "OBDIV Screener"
   - This layout will be used by Python orchestrator

---

### Python Orchestrator

#### First-Time Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd tradingview-to-everywhere
   ```

2. **Install Dependencies**
   ```bash
   pipenv install
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

4. **Verify Chrome Profile**
   ```bash
   # Ensure Chrome is closed
   # Run test to verify Selenium works
   pipenv run python -c "from open_tv import get_driver; d = get_driver(); d.quit()"
   ```

#### Starting the Orchestrator

1. **Activate Environment**
   ```bash
   pipenv shell
   ```

2. **Run in Console Mode**
   ```bash
   python main.py
   ```

3. **Run with GUI**
   ```bash
   python gui.py
   ```

#### Running as Service (Windows)

1. **Create Scheduled Task**
   ```powershell
   $action = New-ScheduledTaskAction -Execute "pythonw.exe" -Argument "main.py" -WorkingDirectory "C:\path\to\tradingview-to-everywhere"
   $trigger = New-ScheduledTaskTrigger -AtStartup
   Register-ScheduledTask -TaskName "TTE Orchestrator" -Action $action -Trigger $trigger
   ```

2. **Verify Service Running**
   ```powershell
   Get-ScheduledTask -TaskName "TTE Orchestrator" | Get-ScheduledTaskInfo
   ```

#### Running as Service (Linux)

1. **Create systemd Service**
   ```bash
   sudo nano /etc/systemd/system/tte-orchestrator.service
   ```

   ```ini
   [Unit]
   Description=TTE Tiered Orchestrator
   After=network.target

   [Service]
   Type=simple
   User=your-user
   WorkingDirectory=/path/to/tradingview-to-everywhere
   ExecStart=/usr/bin/pipenv run python main.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

2. **Enable and Start**
   ```bash
   sudo systemctl enable tte-orchestrator
   sudo systemctl start tte-orchestrator
   ```

3. **Check Status**
   ```bash
   sudo systemctl status tte-orchestrator
   journalctl -u tte-orchestrator -f
   ```

---

## Post-Deployment Verification

### Smoke Tests

Run these tests after every deployment:

```bash
# 1. Health check - Stock Buddy API
curl -s https://stock-buddy-app.vercel.app/api/signals?limit=1 | jq '.success'
# Expected: true

# 2. Test NWE webhook endpoint (dry run)
curl -X POST https://stock-buddy-app.vercel.app/api/nwe \
  -H "Content-Type: application/json" \
  -d '{"tier":"nwe","symbol":"TEST","direction":"bullish","timeframes":["H4"]}'
# Expected: {"success":true,...}

# 3. Verify hot symbols endpoint
curl -s https://stock-buddy-app.vercel.app/api/hot-symbols | jq '.success'
# Expected: true

# 4. Check MongoDB connection
curl -s https://stock-buddy-app.vercel.app/api/signals | jq '.pagination.total'
# Expected: number >= 0
```

### Integration Test

1. **Manual NWE Trigger**
   - Manually send test webhook to `/api/nwe`
   - Verify symbol appears in hot list

2. **Manual OBDIV Trigger**
   - Send test webhook to `/api/obdiv` for hot symbol
   - Verify signal created with correct level

3. **Dashboard Verification**
   - Open Stock Buddy dashboard
   - Verify signal appears in table
   - Check filtering works

### Monitoring Verification

- [ ] Vercel function logs accessible
- [ ] MongoDB Atlas metrics visible
- [ ] Python orchestrator logs writing
- [ ] Error alerting configured

---

## Rollback Procedures

### Stock Buddy Rollback

1. **Identify Previous Deployment**
   ```bash
   vercel ls
   # Note the URL of the previous working deployment
   ```

2. **Rollback to Previous**
   ```bash
   vercel rollback <deployment-url>
   ```

3. **Verify Rollback**
   ```bash
   curl https://stock-buddy-app.vercel.app/api/signals?limit=1
   ```

### TradingView Screener Rollback

1. **Open TradingView**
2. **Load Previous Version**
   - Pine Editor → Open → Select previous saved version
3. **Update Alert**
   - Delete current alert
   - Create new alert with old indicator

### Python Orchestrator Rollback

1. **Stop Current Process**
   ```bash
   # Find and kill process
   pkill -f "python main.py"
   ```

2. **Checkout Previous Version**
   ```bash
   git log --oneline -10
   git checkout <previous-commit-hash>
   ```

3. **Restart**
   ```bash
   pipenv run python main.py
   ```

### Database Rollback

**CAUTION**: Database rollback should be last resort.

1. **Point-in-Time Recovery (MongoDB Atlas)**
   - Go to Atlas Console → Cluster → Backup
   - Select point-in-time before issue
   - Restore to new cluster
   - Update `MONGODB_URI` to point to restored cluster

2. **Manual Data Fix**
   ```javascript
   // Remove bad data
   db.signals.deleteMany({ created_at: { $gte: ISODate("2026-01-29T12:00:00Z") } })

   // Clear hot list
   db.hot_list.deleteMany({ updated_at: { $gte: ISODate("2026-01-29T12:00:00Z") } })
   ```

---

## Emergency Procedures

### Complete System Outage

1. **Disable TradingView Alerts**
   - Open TradingView → Alerts panel
   - Disable all TTE alerts (prevents webhook buildup)

2. **Check Each Component**
   ```bash
   # Vercel status
   curl -s https://www.vercel-status.com/api/v2/status.json | jq '.status'

   # MongoDB Atlas status
   curl -s https://status.cloud.mongodb.com/api/v2/status.json | jq '.status'
   ```

3. **Identify Root Cause**
   - Check Vercel function logs
   - Check MongoDB Atlas logs
   - Check Python orchestrator logs

4. **Restore Service**
   - Fix issue or rollback
   - Re-enable TradingView alerts
   - Process any backlogged webhooks

### Webhook Flood

If receiving too many webhooks:

1. **Rate Limit Response**
   - Vercel will automatically rate limit
   - Check function logs for 429 errors

2. **Disable Alerts Temporarily**
   - Disable TradingView alerts
   - Process backlog
   - Re-enable with adjusted parameters

### Database Connection Issues

1. **Check Atlas Status**
   - https://status.cloud.mongodb.com/

2. **Verify IP Whitelist**
   - Atlas Console → Network Access
   - Ensure Vercel IPs are whitelisted (or use 0.0.0.0/0)

3. **Check Connection String**
   - Verify MONGODB_URI is correct
   - Test with mongosh locally

---

## Emergency Contacts

| Role | Contact | Escalation |
|------|---------|------------|
| Primary On-Call | [Your Name] | Slack: @oncall |
| Database Admin | [DBA Name] | Email: dba@company.com |
| TradingView Support | N/A | support@tradingview.com |
| Vercel Support | N/A | https://vercel.com/support |
| MongoDB Support | N/A | https://www.mongodb.com/support |

---

## Deployment Checklist Templates

### Pre-Production Deployment

```markdown
## Pre-Production Checklist - [Date]

**Deployer**: [Name]
**Components**: [List components being deployed]

### Pre-Deployment
- [ ] Code reviewed and merged to main
- [ ] All tests passing
- [ ] Environment variables verified
- [ ] Rollback plan documented
- [ ] Team notified

### Deployment
- [ ] Stock Buddy deployed to Vercel
- [ ] TradingView screeners updated
- [ ] Python orchestrator restarted
- [ ] Database migrations run (if any)

### Post-Deployment
- [ ] Smoke tests passing
- [ ] Dashboard accessible
- [ ] Signals flowing correctly
- [ ] Monitoring working
- [ ] Documentation updated

### Sign-off
- [ ] QA verified: [Name]
- [ ] Deployment complete: [Name]
```

---

*Last updated: 2026-01-29*
