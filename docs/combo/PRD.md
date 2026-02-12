# TTE Combo Mode — Product Requirements Document

**Version**: 1.0
**Last Updated**: 2026-02-11
**Status**: Production
**Branch**: `combo-architecture`

---

## 1. Product Overview

TradingView to Everywhere (TTE) Combo Mode is an automated trading signal distribution system. It creates persistent webhook alerts on TradingView that continuously monitor ~1,028 trading symbols for NWE, OB/FVG, and Divergence signals, sending results to the Stock Buddy API for display on a real-time signal grid.

### Why Combo Mode Replaced Tiered Mode

| Factor | Tiered Mode | Combo Mode |
|--------|-------------|------------|
| Alert lifecycle | Create → wait → delete → repeat | Create once → run forever |
| Symbol coverage | 20 per cycle, rotating | All ~1,028 simultaneously |
| Browser needed | Every cycle (~90s each) | Only setup + maintenance |
| Signal merging | 2 separate webhooks to correlate | Single payload with all data |
| Webhook delivery | After each batch cycle | Continuous, real-time |

---

## 2. Architecture

### Signal Flow

```
TradingView Pine Script (TTE Screener)
    → 338 persistent alerts (3 symbols each)
    → Webhook fires on every tick with signals
    → POST /api/tte/combo (Stock Buddy API)
    → Upsert into tte_live_signals (MongoDB)
    → ComboSignalGrid polls GET /api/tte/combo/signals
    → Real-time signal grid in Stock Buddy UI
```

### Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| TTE Screener | Pine Script v6 | Single combo indicator (NWE + OB/FVG + Divergence) |
| TTE Orchestrator | Python + Selenium | One-time alert setup + periodic maintenance |
| Stock Buddy API | Next.js / Vercel | Webhook receiver + signal query API |
| MongoDB Atlas | MongoDB | Signal storage (`tte_live_signals`) |
| Signal Grid | React + RTK Query | Real-time signal display |

### Production Configuration

| Setting | Value | Notes |
|---------|-------|-------|
| Total symbols | ~1,028 | Forex, stocks, crypto, indices |
| Batch size | 3 | Of 4-symbol hard limit (reduced for 1-min chart) |
| Total alerts | 338 | ~1,028 ÷ 3 (targets 343 for full coverage) |
| Browser mode | Single (sequential) | Headless Chrome, one browser instance |
| Chart timeframe | 1 minute | Fastest signal detection |
| Bar style | Line | Minimal resource usage |
| Maintenance interval | 5 minutes | Restart inactive alerts |
| Pine Script timeframes | 1H (TF_H4=60), H4 (TF_D1=240), D1 (TF_W1=D) | Variable names are legacy |

---

## 3. Pine Script Screener

**File**: `Pine Script Code/TTE Screener.txt`
**Indicator**: "TTE Screener" (short title: "Screener")

### Signal Types

| Signal | Timeframes | Detection |
|--------|-----------|-----------|
| NWE (Nadaraya-Watson Envelope) | 1H, H4 | Price overlapping envelope zones |
| OB/FVG (Order Block / Fair Value Gap) | 1H, H4, D1 | Unmitigated OBs, breaker zones, unfilled FVGs |
| Divergence (Kernel AO Logic 2) | 1H, H4 | Price/oscillator divergence |

### request.security() Budget

- **Used**: 12 of 40 max (4 symbols × 3 timeframes)
- **Remaining**: 28 calls for future expansion

### Alert Behavior

- `alert.freq_all` — fires on every tick while signals exist
- Only fires when at least 1 symbol has at least 1 signal
- Payload includes only symbols WITH active signals

---

## 4. Configuration

### combo_settings.yaml

```yaml
chart:
  layout_name: "Screener"
  chart_timeframe: "1 minute"
  bar_style: "line"
  headless: true

screener:
  shorttitle: "Screener"
  name: "TTE Screener"

alerts:
  batch_size: 3
  creation_delay: 1.5
  recalc_wait: 1.5
  start_fresh: false

webhook:
  url: "https://stock-buddy-app.vercel.app/api/tte/combo"

maintenance:
  interval: 300

progress:
  file: combo_progress.json
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `COMBO_WEBHOOK_URL` | Stock Buddy combo endpoint (overrides YAML) |
| `CHROME_PROFILES_PATH` | Chrome user data directory |
| `TRADINGVIEW_EMAIL` | TradingView login email |
| `TRADINGVIEW_PASSWORD` | TradingView login password |

---

## 5. Stock Buddy Integration

### Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/tte/combo` | Receive webhook payload from TradingView |
| GET | `/api/tte/combo/signals` | Query signals with pagination/filtering |
| GET | `/api/tte/stats` | System statistics (includes combo stats) |

### POST /api/tte/combo — Webhook Payload

```json
{
  "timestamp": 1707264000000,
  "signals": [
    {
      "symbol": "GBPAUD",
      "nwe": [{"zone": "lower_avg", "type": "bullish", "overlapTimestamp": 1707264000000, "timeframe": "1H"}],
      "ob_fvg": [{"zonetype": "OB", "subtype": "unmitigated", "type": "bullish", "timeframe": "H4"}],
      "divergence": []
    }
  ]
}
```

### GET /api/tte/combo/signals — Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Max signals (1-200) |
| `offset` | integer | 0 | Pagination offset |
| `sort` | string | `last_updated` | Sort field |
| `order` | string | `desc` | Sort order |
| `direction` | string | - | Filter: `bullish` or `bearish` |
| `signalType` | string | - | Filter: `nwe`, `ob_fvg`, `divergence` |
| `symbol` | string | - | Filter by symbol name |

### MongoDB Collection: `tte_live_signals`

```json
{
  "_id": "GBPAUD",
  "symbol": "GBPAUD",
  "nwe": [{"zone": "lower_avg", "type": "bullish", "overlapTimestamp": 1707264000000, "timeframe": "1H"}],
  "ob_fvg": [{"zonetype": "OB", "subtype": "unmitigated", "type": "bullish", "timeframe": "H4"}],
  "divergence": [],
  "last_updated": "2026-02-11T12:00:00Z"
}
```

- **Upsert behavior**: `_id` = symbol name, entire document replaced on each webhook
- **Signal persistence**: Signals persist with `last_updated` timestamp; users judge freshness

---

## 6. CLI Commands

```bash
python combo_main.py                  # Full setup + maintenance
python combo_main.py --setup-only     # Create alerts, then exit
python combo_main.py --maintain-only  # Skip setup, run maintenance only
python combo_main.py --fresh          # Delete all existing alerts before setup
python combo_main.py --validate       # Validate config and exit
```

---

## 7. Known Limitations

| Limitation | Details |
|------------|---------|
| Single browser architecture | Sequential alert creation with one Chrome instance |
| 4-symbol hard limit per alert | More causes TradingView memory/runtime errors |
| Alert snapshot behavior | Editing Pine Script doesn't update existing alerts — must recreate |
| Rate limit | 15 triggers per 3 minutes per individual alert (auto-disabled if exceeded) |
| No auto-removal of stale signals | Signals persist in DB; users judge freshness via timestamp |

---

## 8. Completed Enhancements

| Enhancement | Issue | Description |
|------------|-------|-------------|
| Headless Chrome | #81 | Runs in headless mode by default (`headless: true` in YAML) |
| GUI executable | #86 | Desktop app (`tte_gui.py` / `dist/TTE.exe`) with settings editor |
| Single browser | — | Switched from parallel multi-browser to single sequential browser |

## 9. Future Enhancements

| Enhancement | Issue | Description |
|------------|-------|-------------|
| Failed batch retry | #67 | Automatic retry for failed alert creation batches |

---

## 10. Production Metrics

- **Total symbols**: ~1,028 (forex, US stocks, Indian stocks, crypto, indices, commodities)
- **Total alerts**: 338 (targets 343 for full coverage of all 1,028 symbols)
- **Setup time**: Sequential with single headless browser
- **Browser mode**: Single Chrome instance, headless by default
- **Maintenance cycle**: Every 5 minutes (includes page refresh + alert log clearing)
- **Webhook volume**: ~5,000-50,000/day depending on market conditions
- **Tasks completed**: 97 implementation tasks (Feb 2026)
