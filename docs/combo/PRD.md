# TTE Combo Mode — Product Requirements Document

**Version**: 2.0
**Last Updated**: 2026-02-27
**Status**: Production (V2)

---

## 1. Product Overview

TradingView to Everywhere (TTE) Combo Mode V2 is an automated trading signal distribution system. It creates persistent webhook alerts on TradingView that continuously monitor 620 trading symbols for NWE + OB/FVG signals using stateless setup detection, and send compact pre-computed setup data to the Stock Buddy API on every 45-second bar close. Exit detection is handled server-side by a Stock Buddy cron job (every 5 min).

### Why Combo Mode Replaced Tiered Mode

| Factor | Tiered Mode | Combo Mode |
|--------|-------------|------------|
| Alert lifecycle | Create → wait → delete → repeat | Create once → run forever |
| Symbol coverage | 20 per cycle, rotating | All 620 simultaneously |
| Browser needed | Every cycle (~90s each) | Only setup + maintenance |
| Signal merging | 2 separate webhooks to correlate | Single payload with all data |
| Webhook delivery | After each batch cycle | Every bar close (45s) |

---

## 2. Architecture

### Signal Flow (V2)

```
TradingView Pine Script (TTE Screener V2)
    → ~310 persistent alerts (2 symbols each, category-aware)
    → Webhook fires on every 45-second bar close
    → POST /api/tte/combo (Stock Buddy API)
    → Upsert into tte_live_signals (MongoDB)
    → Frontend polls GET /api/tte/combo/signals
    → Real-time signal + position grid in Stock Buddy UI
```

### Components (V2)

| Component | Technology | Purpose |
|-----------|-----------|---------|
| TTE Screener V2 | Pine Script v6 | Combo indicator: NWE + OB/FVG (stateless setup detection) |
| TTE Orchestrator | Python + Selenium | One-time alert setup + periodic maintenance |
| Stock Buddy API | Next.js / Vercel | Webhook receiver + signal query API |
| MongoDB Atlas | MongoDB | Signal storage (`tte_live_signals`) |
| Signal Grid | React + RTK Query | Real-time signal + position display |

### Production Configuration (V2)

| Setting | Value | Notes |
|---------|-------|-------|
| Total symbols | 620 | Currencies, US stocks, Indian stocks, crypto |
| Batch size | 2 | Category-aware pairing (same asset class) |
| Total alerts | ~310 | 620 ÷ 2 |
| Browser mode | Single (sequential) | Headless Chrome, one browser instance |
| Chart timeframe | 45 seconds | Fastest practical bar close for signal detection |
| Bar style | Candle | Required for accurate high/low exit detection |
| Alert frequency | `alert.freq_once_per_bar_close` | Once per 45-second bar close |
| Maintenance interval | 2.5 minutes (150s) | Restart inactive alerts |
| Screener indicator | "TTE Screener V2" | Short title: "Screener V2" |

---

## 3. Pine Script Screener (V2)

**File**: `Pine Script Code/TTE Screener V2.txt`
**Indicator**: "TTE Screener V2" (short title: "Screener V2")

### Signal Types (V2)

| Signal | Timeframes | Detection |
|--------|-----------|-----------|
| NWE (Nadaraya-Watson Envelope) | 1H, H4 | Price overlapping envelope zones |
| OB/FVG (Order Block / Fair Value Gap) | H4, D1 | Unmitigated OBs, breaker zones, unfilled FVGs |
| Divergence | — | **Removed in V2** |

### Stateless Setup Detection (V2)

| Feature | Description |
|---------|-------------|
| Setup types | LTF (1H NWE + H4 OB), HTF (H4 NWE + D1 OB) |
| Max setup slots | 1 LTF buy + 1 HTF buy + 1 LTF sell + 1 HTF sell per symbol (4 concurrent) |
| SL calculation | MIN(confirming OB zoneLow) for buys, MAX(zoneHigh) for sells |
| TP calculation | 1:2 risk-reward from entry |
| Exit detection | **Server-side** — Stock Buddy cron (every 5 min) via Binance/Yahoo candles |
| Staleness | `timenow - symTime > 120000ms` → symbol excluded from payload |

### `request.security()` Budget (V2)

- **Used**: 8 of 40 max (2 symbols × 4 call types)
- **Remaining**: 32 calls for future expansion

### Alert Behavior (V2)

- `alert.freq_once_per_bar_close` — fires once per 45-second bar close
- Fires every bar (not conditional on signals)
- Stale symbols excluded via `timenow - symTime > 120000ms` check

---

## 4. Configuration

### combo_settings.yaml (V2)

```yaml
chart:
  layout_name: "Screener"
  chart_timeframe: "45 seconds"
  bar_style: "candle"
  headless: true

screener:
  shorttitle: "Screener V2"
  name: "TTE Screener V2"

alerts:
  batch_size: 2
  creation_delay: 1.5
  recalc_wait: 1.5
  start_fresh: false

webhook:
  url: ""  # Set via COMBO_WEBHOOK_URL env var

maintenance:
  interval: 150  # 2.5 minutes

snapshot:
  enabled: true
  layout_name: "Snapshot"
  bar_style: "candle"
  batch_size: 10
  poll_interval: 60
  bars_to_right: 60

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
| `MONGODB_PWD` | MongoDB password (or use `MONGODB_URI`) |

---

## 5. Stock Buddy Integration

### Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/tte/combo` | Receive V2 compact webhook payload |
| GET | `/api/tte/combo/signals` | Query signals with pagination/filtering |
| GET | `/api/tte/snapshots/pending` | Snapshot worker polls for pending screenshots |
| POST | `/api/tte/snapshots/update` | Snapshot worker reports completed URLs |

### POST /api/tte/combo — V2 Webhook Payload

```json
{
  "ts": 1707264000000,
  "s": [{
    "sym": "GBPAUD", "c": 1.985,
    "nwe": [{"z": "la", "t": "bull", "tf": "1H", "ots": 1707264000}],
    "ob": [{"zt": "OB", "st": "un", "t": "bull", "zh": 1.99, "zl": 1.97, "tf": "H4", "zts": 1707260400, "ots": 1707264000}],
    "b": [{"e": 1.98, "sl": 1.975, "tp": 1.99, "et": 1707260000, "l": "LTF", "ntf": "1H", "otf": "H4", "n": true}, null],
    "se": [null, null]
  }]
}
```

Key: `ts`=timestamp, `s`=symbols, `sym`=symbol, `c`=close, `nwe`=NWE signals, `ob`=OB signals, `b`=buy setups [LTF,HTF], `se`=sell setups [LTF,HTF], `e`=entry, `sl`=stopLoss, `tp`=takeProfit, `et`=entryTime, `l`=label, `ntf`=nweTf, `otf`=obTf

---

## 6. CLI Commands

```bash
python combo_main.py                  # Full setup + maintenance
python combo_main.py --setup-only     # Create alerts, then exit
python combo_main.py --maintain-only  # Skip setup, run maintenance only
python combo_main.py --fresh          # Delete all existing alerts before setup
python combo_main.py --validate       # Validate config and exit
python combo_main.py --symbols EURUSD,GBPUSD  # Test specific symbols only
python tte_gui.py                     # GUI interface
```

---

## 7. Known Limitations

| Limitation | Details |
|------------|---------|
| Single browser architecture | Sequential alert creation with one Chrome instance |
| 4-symbol hard limit per alert | More causes TradingView memory/runtime errors |
| Alert snapshot behavior | Editing Pine Script doesn't update existing alerts — must recreate with --fresh |
| Rate limit | 15 triggers per 3 minutes per individual alert (auto-disabled if exceeded) |
| Staleness window | Symbols not updated within 120s excluded from payload |

---

## 8. Completed Milestones

### V1 Milestones (Completed)
| Enhancement | Description |
|------------|-------------|
| Headless Chrome | Runs in headless mode by default |
| GUI executable | Desktop app (`tte_gui.py` / `dist/TTE.exe`) with settings editor |
| Single browser | Switched from parallel multi-browser to single sequential browser |

### V2 Milestones (Completed Feb 2026)
| Enhancement | Description |
|------------|-------------|
| TTE Screener V2 | Forked from V1, stripped divergence, reduced to 2 symbols |
| Stateless setup detection | Setup detection in Pine Script; exit detection moved to Stock Buddy cron |
| Compact payload | Abbreviated keys to fit 2KB TradingView alert message limit |
| Category-aware pairing | Symbols paired within same asset class for matching market hours |
| 45-second timeframe | Faster bar close for quicker signal/exit detection |
| Maintenance 150s | Reduced from 300s to 2.5 minutes |
| Graceful shutdown | `threading.Event` for interruptible waits on SIGINT/SIGTERM |
| Snapshot worker | Chart screenshot system for setup messages in Stock Buddy |
| GUI snapshot settings | Snapshot config exposed in GUI settings card |

### Post-V2 Milestones (Completed Mar-Apr 2026)
| Enhancement | Description |
|------------|-------------|
| Failed batch retry | Auto-retry failed alert creation batches once after initial setup |
| `--symbols` CLI flag | Test with specific symbols without full MongoDB fetch |
| Overlay retry in change_settings | Handles overlay popups during screener settings changes |
| delete_all_alerts text matching | XPath text-based matching instead of index-based dropdown selection |
| TradingView UI redesign adaptation | Alert dialog two-step flow, timeframe collapsible sections, layout href navigation |
| Selenium 4 built-in drivers | Removed webdriver-manager, uses Selenium 4's driver management |
| Snapshot pipeline fixes | Backfill, dialog cleanup, throughput improvements |

---

## 9. Future Enhancements

| Enhancement | Description |
|------------|-------------|
| Symbol expansion | Expand from 620 to ~800 symbols (architecture supports up to 400 alerts) |

---

## 10. Production Metrics (V2)

- **Total symbols**: 620 (currencies, US stocks, Indian stocks, crypto)
- **Total alerts**: ~310 (2 symbols per alert, category-aware pairing)
- **Setup time**: Sequential with single headless browser
- **Browser mode**: Single Chrome instance, headless by default
- **Maintenance cycle**: Every 2.5 minutes (includes page refresh + alert log clearing)
- **Webhook delivery**: Every 45-second bar close per alert
