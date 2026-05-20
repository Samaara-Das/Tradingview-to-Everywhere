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
- `tte/main.py` — Entry point (orchestrator). `--symbols=<csv>` filter is partition-aware (Mongo `assigned_instance`) and works WITHOUT `--fresh` to add to an existing alert set.
- `tte/config.py` — Configuration loader. Module constant `INSTANCE` (from `TTE_INSTANCE` env) drives partition selection. `_build_webhook_url()` appends `?instance=<INSTANCE>` to `COMBO_WEBHOOK_URL`. `PROFILE` constant from `CHROME_PROFILE` env.
- `tte/log.py` — Logger setup (named `log` to avoid shadowing stdlib `logging`)
- `tte/browser/tradingview.py` — TradingView browser automation (Selenium). Key methods detailed in [Key Code Locations](#key-code-locations) below.
- `tte/browser/chart.py` — Chart navigation & snapshots. WS-0 renderer-stall recovery via `change_symbol()` retry + page-refresh fallback.
- `tte/browser/helpers.py` — Selenium utility functions
- `tte/data/symbols.py` — MongoDB symbol fetching. Filters by `assigned_instance` per `INSTANCE`; for `tte-1` includes legacy docs without the field, for `tte-N` (N>=2) strict-matches.
- `tte/snapshot_worker.py` — Chart snapshot polling & Trade Drawer V2 rendering. `StockBuddyClient` passes `instance` to the SB polling endpoint so each container only picks up its own pending snapshots.
- `tte/backfill_reversed_snapshots.py` — One-off reversed-strategy snapshot re-render job (run via `scripts/run_reversed_backfill.py`)

### Browser Automation (`tte/browser/tradingview.py`)
- Manages all Selenium interactions with TradingView
- Key pattern: `_safe_indicator_access()` handles stale elements with retry logic
- `create_webhook_alert()` — creates webhook alerts AND verifies persistence by snapshotting topmost alert-sidebar row before+after Create. Returns `(False, "not_persisted")` on silent TV drops (PR #48).
- `reupload_indicator()` — add-before-delete order to prevent chart destruction; uses text-content match on `data-role="menuitem"` instead of hashed CSS classes (PR #48). Calls `_set_indicator_instance_id()` automatically when `INSTANCE != "tte-1"` so the fresh copy doesn't carry the Pine default.
- `change_settings()` — waits up to 6s for symbol-input fields in the settings dialog, falls back to broader `data-name="edit-button"` selector if hashed `.inlineRow-uuCuCMOL` doesn't match (PR #48).
- `_maybe_auto_submit_totp()` — `Ctrl+A+Delete` clears React-controlled OTP input (`.clear()` is unreliable; observed 28-char accumulation across retries), then `send_keys(code) + Enter` (PR #48).

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
See `tte/config.py` and `.env` file. Key variables:
- `TTE_INSTANCE` — instance identifier (e.g. `tte-1`, `tte-2`); selects the Mongo symbol partition and is appended to webhook URL as `?instance=<value>`. Defaults to `tte-1`.
- `CHROME_PROFILE` — per-instance Chrome profile name (e.g. `Profile 4` for tte-1, `Default` for tte-2). The actual user-data-dir is `/home/tte/chrome-profile/TTE[-<instance>]` inside containers.
- `TRADINGVIEW_EMAIL`, `TRADINGVIEW_PASSWORD` — sign-in credentials
- `TRADINGVIEW_TOTP_SECRET` — **required** (base32) for auto-2FA via pyotp; TV refuses webhook-alert creation without 2FA enabled on the account (see TradingView Requirements below)
- `MONGODB_URI` — Atlas SRV connection string (shared with Stock Buddy)
- `COMBO_WEBHOOK_URL` — Stock Buddy combo webhook base URL; runtime appends `?instance=<TTE_INSTANCE>`
- `STOCK_BUDDY_API_URL`, `API_TIMEOUT` — Stock Buddy REST API base + HTTP timeout
- `REVERSED_STRATEGY_SNAPSHOTS` — emergency rollback flag (default false)
- `TTE_INITIAL_CHART_URL` — optional override of initial chart URL on sign-in (e.g. `/chart/bSgWQNPC/` for Rahul's saved Screener layout); skips layout-switch step during setup_tv

### TradingView Requirements
- **2FA**: **REQUIRED on every TV account TTE drives.** TV silently rejects webhook-alert creation when 2FA is off — it shows a "Protect your data — enable 2-factor authentication" modal that the alert dialog doesn't surface as an error, so Selenium's Create click appears to succeed while the alert never persists. Discovered 2026-05-19 via Rahul's tte-2 (1001 ghost-creates). Set `TRADINGVIEW_TOTP_SECRET` (base32) in each instance's `.env.tte.<N>` so pyotp auto-handles the OTP prompt at sign-in (PR #40).
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
| Create webhook alert + persistence verify | `tte/browser/tradingview.py` `create_webhook_alert()` | Alert creation. Returns `(False, "not_persisted")` if sidebar topmost row doesn't change after Create — catches TV silent-drop bugs (PR #48) |
| Change screener settings (with input-render wait) | `tte/browser/tradingview.py` `change_settings()` | Waits up to 6s for symbol-input fields to render in dialog, falls back to broader `data-name="edit-button"` selector if hashed `.inlineRow-uuCuCMOL` doesn't match (PR #48) |
| Delete all alerts (incl. stopped sweep) | `tte/browser/tradingview.py` `delete_all_alerts()` | Pauses + deletes inactive, then sweeps "Delete all" + per-row fallback to clean stopped-state survivors (PR #48) |
| Safe element access | `tte/browser/tradingview.py` `_safe_indicator_access()` | When Selenium elements go stale |
| Re-upload indicator (add-before-delete) | `tte/browser/tradingview.py` `reupload_indicator()` | Add fresh copy from Favorites FIRST, confirm on chart, THEN remove old. Stable text-match selector instead of hashed CSS classes. Prevents chart destruction (PR #48). |
| Set Instance ID after reupload | `tte/browser/tradingview.py` `_set_indicator_instance_id()` | Restores Pine `Instance ID` input to the running container's `TTE_INSTANCE` after reupload's fresh copy lands (PR #48) |
| TOTP auto-submit | `tte/browser/tradingview.py` `_maybe_auto_submit_totp()` | `target.click() + Ctrl+A+Delete + send_keys(code) + Enter` (PR #48). React-controlled input — `.clear()` is unreliable. |
| Login-state guard | `tte/browser/tradingview.py` `is_chart_layout_loaded()` / `ensure_chart_layout_loaded()` | TV session-expired recovery (PR #39) |
| Skip reupload on `not_persisted` | `tte/main.py` retry path | Skips reupload-retry when failure is `not_persisted` (TV silent rejection) — reupload destroys chart and cascades into 100% failure otherwise (PR #48) |
| Renderer-stall recovery | `tte/browser/chart.py` `change_symbol()` retry-on-`Read timed out` + `tte/snapshot_worker.py` `_recycle_chart()` | WS-0 fixes (PR #42) |

## Tools (`tools/`)

One-off and bootstrap utilities (NOT part of the runtime loop):

| Script | Purpose |
|--------|---------|
| `tools/compute_missing_symbols.py` | Parse `app_log.log` for "Alert created for" lines in a time window, diff against the Mongo partition, write missing symbols CSV. Used to drive `--symbols` supplementary fills. |
| `tools/fix_instance_id.py` | Open chart via `Browser.setup_tv()` then call `Browser._set_indicator_instance_id()` to restore Pine `Instance ID` input on the Screener layout. Saves layout via Ctrl+S. Use after a reupload-recovery side-effect leaves the wrong Instance ID. |
| `tools/add_trade_drawer.py` | Switch to Snapshot layout, open Favorites, click `Trade Drawer V2`, save. Use after Trade Drawer V2 is favorited on a TV account to add it to the Snapshot layout. |
| `tools/favorite_trade_drawer.py` | Check whether `Trade Drawer V2` is in My Scripts and favorited. Reports current Favorites list. Read-only diagnostic. |
| `tools/pine_install_trade_drawer.py` | Full Pine Editor automation: paste `Pine Script Code/Trade Drawer V2.txt` into Monaco's hidden textarea → Ctrl+S → save (TV auto-populates name from `indicator('Title', ...)`). Save-and-star is partial (star-click selector hunting needed). |
| `tools/investigate_alert_cap.py` | Read-only: open alerts sidebar, dump alerts-settings menu (shows `Active 1000 / Inactive N` and `Technicals X/1000` cap usage). |
| `tools/csv_to_scraped_json.py` | Convert TV screener CSV exports → JSON for `tools/ingest_scraped_symbols.py`. Used during the symbol-partition bootstrap. |
| `tools/scrape_tv_screener.py` | Selenium fallback scraper for TV screener pages (used when CSV export isn't available). |
| `inject_tv_cookies.py` (top-level) | One-off cookie-injection bootstrap. Reads `TV_SESSION_ID`/`TV_SESSION_ID_SIGN` from env, persists them into a Chrome user-data-dir so containers skip `/accounts/signin/`. **Important**: pass `CHROME_USER_DATA_DIR=/home/tte/chrome-profile/TTE-tte-<N>` (with the subdir) so cookies land where tte-N's Chrome reads them. |
| `tools/onboard_tv_account.py` | Skeleton script for new-TV-account bootstrap (manual setup steps live at `.claude/specs/manual-tv-account-setup.md`). |

## Documentation

| Change Type | Update |
|-------------|--------|
| Architecture/workflow | `docs/combo/ARCHITECTURE.md` |
| Implementation tasks | `docs/combo/PRD.md` |
| Other changes | `README.md`, `docs/SETUP.md`, `docs/API.md`, etc. |

Update docs in the same PR as code changes.
