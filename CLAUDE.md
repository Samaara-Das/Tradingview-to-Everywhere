# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TradingView to Everywhere (TTE) is an automated trading signals distribution system that bridges TradingView alerts with Stock Buddy API. It uses Selenium browser automation to interact with TradingView and webhooks to distribute signals.

### Hybrid Hosting (as of 2026-05-04)

- **TTE container `tte-1`** runs on a Hostinger VPS in Mumbai (KVM tier; see `docs/SETUP.md` "Linux/Docker"). The VPS is TTE-only — Stock Buddy and Mongo no longer share it.
- **Database**: MongoDB Atlas (M10). `MONGODB_URI` in `.env.tte.1` points at the same Atlas SRV string Stock Buddy uses. Atlas IP allowlist must include the VPS public IP.
- **Stock Buddy API**: Vercel-hosted, public URL. `STOCK_BUDDY_API_URL=https://stockbuddy.co/api/tte` and `COMBO_WEBHOOK_URL=https://stockbuddy.co/api/tte/combo`. No internal Docker DNS hops anymore.
- **Container state**: `change_settings()` screener-gear bug fixed (PR #28 — `self.driver` was incorrectly passed as a WebElement to `WebDriverWait`). Chromedriver version-mismatch fallback bug also fixed (PR #29).

### Critical Principles
1. **Reuse existing code**: Before implementing anything, check if it already exists in the codebase
2. **Changes to `tte/browser/tradingview.py` should be tested carefully**: It contains all browser automation logic
3. **Use built-in task management**: Always use TaskCreate/TaskUpdate/TaskList tools for tracking work

## Combo Mode (`tte/main.py`) — Production

- **Platform**: Runs on Windows AND Linux/Docker (Hostinger VPS, since 2026-04-30). See root `Dockerfile` and `docs/SETUP.md` "Linux/Docker" section. Three platform-portable patches landed in this codebase:
  - `tte/browser/tradingview.py`: Chrome-process-cleanup block guarded by `platform.system() == "Windows"` (Linux containers never have stale Chrome to kill).
  - `tte/log.py`: file handler writes under `${LOG_DIR:-logs}/app_log.log` (Docker mounts `/app/logs` to a host volume).
  - `tte/config.py`: `PROFILE = os.getenv("CHROME_PROFILE", "Profile 4")` so each container can override (per-instance user-data-dir volumes).
- **Method**: Single combo screener (NWE + OB/FVG, stateless setup detection) with persistent webhook alerts
- **Workflow**: ~340 persistent alerts (2 symbols each, category-aware pairing) covering ~677 symbols → webhook every 45s to Stock Buddy API
- **Alert lifecycle**: Create once → run forever (+ maintenance every 2.5 mins)
- **Screener V2**: Stateless setup detection (NWE + OB/FVG alignment). Exit detection handled by Stock Buddy cron (every 5 min via Binance/Yahoo candles)
- **Single browser**: Alerts created sequentially with one Chrome instance (headless by default)
- **Chart**: 45-second timeframe, candle bar style, `alert.freq_once_per_bar_close`
- **Key files**: `tte/main.py`, `tte/config.py`, `combo_settings.yaml`, `Pine Script Code/TTE Screener V2.txt`
- **Docs**: `docs/combo/ARCHITECTURE.md`, `docs/combo/PRD.md`

## Running Commands

```bash
pipenv shell                              # Activate environment
python combo_main.py                      # Full setup + maintenance (shim)
python -m tte.main                        # Full setup + maintenance (direct)
python combo_main.py --setup-only         # Create alerts, then exit
python combo_main.py --maintain-only      # Skip setup, run maintenance only
python combo_main.py --fresh              # Delete all existing alerts before setup
python combo_main.py --validate           # Validate config and exit
python combo_main.py --symbols EURUSD,GBPUSD  # Setup only these symbols
python tte_gui.py                         # GUI interface
```

## Core Architecture

### Package Structure (`tte/`)
- `tte/main.py` — Entry point (orchestrator)
- `tte/config.py` — Configuration loader + PROFILE constant
- `tte/log.py` — Logger setup (named `log` to avoid shadowing stdlib `logging`)
- `tte/browser/tradingview.py` — TradingView browser automation (Selenium)
- `tte/browser/chart.py` — Chart navigation & snapshots
- `tte/browser/helpers.py` — Selenium utility functions
- `tte/data/symbols.py` — MongoDB symbol fetching
- `tte/snapshot_worker.py` — Chart snapshot polling & browser orchestration
- `tte/backfill_reversed_snapshots.py` — One-off reversed-strategy snapshot re-render job (run via `scripts/run_reversed_backfill.py`)

### Browser Automation (`tte/browser/tradingview.py`)
- Manages all Selenium interactions with TradingView
- Key pattern: `_safe_indicator_access()` handles stale elements with retry logic
- `create_webhook_alert()` creates alerts with webhook notification
- `reupload_indicator()` recovers from screener errors
- `change_settings()` fills in symbol inputs for the screener

### Settings (`combo_settings.yaml`)
All combo mode options are configured in `combo_settings.yaml`. Secrets (webhook URL) are in `.env`.

| Setting | YAML Path | Default | Description |
|---------|-----------|---------|-------------|
| Layout | `chart.layout_name` | "Screener" | TradingView layout name |
| Timeframe | `chart.chart_timeframe` | "45 seconds" | Chart timeframe (must match dropdown label) |
| Bar style | `chart.bar_style` | "candle" | Chart bar style data-value (candle, line, ha, etc.) |
| Screener | `screener.shorttitle` | "Screener V2" | Indicator short title on chart |
| Batch size | `alerts.batch_size` | 2 | Symbols per alert (category-aware pairing) |
| Creation delay | `alerts.creation_delay` | 1.5 | Seconds between batches |
| Maintenance | `maintenance.interval` | 150 | Seconds between restart cycles |
| Snapshot enabled | `snapshot.enabled` | true | Enable chart snapshot worker |
| Snapshot layout | `snapshot.layout_name` | "Snapshot" | TradingView layout for snapshots |
| Snapshot bar style | `snapshot.bar_style` | "candle" | Bar style for snapshot charts |
| Snapshot batch size | `snapshot.batch_size` | 10 | Pending snapshots per poll |
| Snapshot poll interval | `snapshot.poll_interval` | 60 | Seconds between snapshot polls |
| Snapshot bars right | `snapshot.bars_to_right` | 60 | Right margin bars for chart framing |
| Reversed snapshots | `snapshot.reversed_strategy` | false | Emergency rollback only — keep false; reversed Trade Drawer V2 Pine handles TP/SL swap internally |

### Environment Variables
See `tte/config.py` and `.env` file. Key variables: `CHROME_PROFILES_PATH`, `TRADINGVIEW_EMAIL`, `TRADINGVIEW_PASSWORD`, `TRADINGVIEW_TOTP_SECRET` (optional — base32 TOTP secret for auto-2FA via pyotp; see `.claude/credentials-and-2fa.md`), `MONGODB_PWD`, `COMBO_WEBHOOK_URL`, `STOCK_BUDDY_API_URL`, `API_TIMEOUT`, `REVERSED_STRATEGY_SNAPSHOTS` (emergency rollback; default false)

### TradingView Requirements
- **2FA**: Can be on or off — if TV's "suspicious activity" detector forces 2FA on, set `TRADINGVIEW_TOTP_SECRET` in `.env` for auto-handling (PR #40); otherwise the backup-code workflow in `.claude/credentials-and-2fa.md` is the manual recovery path
- **Social accounts**: None linked
- **Subscription**: Premium (for webhooks)
- **Layout**: "Screener" with the combo indicator starred/favorited

## Development Guidelines

1. **Reuse existing code**: Check before implementing — patterns for alerts, tabs, indicators already exist
2. **Always log**: Use `logger.info/debug/error()` in every significant code block
3. **Test `tte/browser/tradingview.py` changes carefully**: Browser automation is fragile; verify with a real browser
4. **Document mistakes**: Write learnings to prevent repetition

## Key Code Locations

| What | Where | Use Case |
|------|-------|----------|
| Restart inactive alerts | `tte/main.py` `restart_inactive_alerts()` | Maintenance (every 2.5 mins) |
| Create webhook alert | `tte/browser/tradingview.py` `create_webhook_alert()` | Alert creation |
| Change screener settings | `tte/browser/tradingview.py` `change_settings()` | Symbol configuration |
| Safe element access | `tte/browser/tradingview.py` `_safe_indicator_access()` | When Selenium elements go stale |
| Re-upload indicator | `tte/browser/tradingview.py` `reupload_indicator()` | Screener error recovery |
| Login-state guard | `tte/browser/tradingview.py` `is_chart_layout_loaded()` / `ensure_chart_layout_loaded()` | TV session-expired recovery (PR #39) |
| Auto-2FA | `tte/browser/tradingview.py` `_maybe_auto_submit_totp()` | Optional pyotp-based 2FA submit when `TRADINGVIEW_TOTP_SECRET` is set (PR #40) |
| Renderer-stall recovery | `tte/browser/chart.py` `change_symbol()` retry-on-`Read timed out` + `tte/snapshot_worker.py` `_recycle_chart()` | WS-0 fixes for chronic renderer overload on long-running headless Chrome (lowers urllib3 timeout to 45s, retries on stall, recycles every 30 snapshots) |

## Documentation

| Change Type | Update |
|-------------|--------|
| Architecture/workflow | `docs/combo/ARCHITECTURE.md` |
| Implementation tasks | `docs/combo/PRD.md` |
| Other changes | `README.md`, `docs/SETUP.md`, `docs/API.md`, etc. |

Update docs in the same PR as code changes.
