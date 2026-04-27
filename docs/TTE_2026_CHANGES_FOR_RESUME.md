# TradingView to Everywhere (TTE) — 2026 Changes

A detailed reference of every meaningful change to the TTE system in 2026, written for resume use. Items are grouped by theme, with concrete numbers, technologies, and impact statements you can lift directly into bullet points.

## Project Summary (one-liner)

TTE is an automated trading-signals distribution system that bridges TradingView with the Stock Buddy backend. It uses Selenium to drive a real Chrome browser inside TradingView Premium, runs a custom Pine Script multi-symbol screener, and pushes structured webhook payloads (~340 persistent alerts covering 677 symbols across forex, crypto, US, and Indian equities — most alerts pair two symbols, a few hold one) into a downstream signal API.

---

## Background Primer (for non-trading readers)

If you've never used TradingView or written a trading bot, here's what each term in this doc means.

### TradingView
TradingView is the most popular charting website for traders (think "Google Docs for stock charts"). Users open a chart for a symbol like `EURUSD` or `AAPL`, apply technical indicators on top of it, and watch the price move in real time. A **Premium** subscription unlocks features that matter for automation — most importantly, the ability to send **webhooks** when an alert fires. TradingView has no public API for placing alerts programmatically, which is why this project drives the website through a real browser.

### Symbols, charts, timeframes, candles
- A **symbol** (or **ticker**) is the code for a tradable instrument: `EURUSD` (forex), `BTCUSDT` (crypto), `AAPL` (US stock), `RELIANCE` (Indian stock).
- A **chart** plots that symbol's price over time.
- A **timeframe** is how much time each "bar" on the chart represents — e.g. **45 seconds**, 1 minute, 1 hour (`1H`), 4 hours (`H4`), 1 day (`D1`). Smaller timeframes = more reactive but noisier; larger = slower but more reliable.
- Each bar is usually drawn as a **candle** showing the open, high, low, and close price for that interval.

### Pine Script
**Pine Script** is TradingView's proprietary scripting language for writing custom indicators and strategies. You upload a Pine script and it runs *inside* the TradingView chart, computing values bar-by-bar. The TTE project ships a custom Pine indicator called **TTE Screener V2** that watches multiple symbols at once and decides when conditions are right for a trade.

- **`request.security()`** — a Pine function that fetches data from a *different* symbol or timeframe than the one the chart is on. It's expensive (TradingView limits how many you can use), so reducing these calls is a real performance win.
- **Stateless vs stateful Pine** — A *stateful* script remembers things across bars using `var` variables (e.g. "I'm currently in a long trade"). A *stateless* script recomputes everything from scratch each bar. Stateless is simpler and lets the *server* (Stock Buddy) own the position-tracking logic instead.
- **`alert.freq_once_per_bar_close`** — tells TradingView "only fire this alert when a bar fully closes," which on a 45-second chart caps each alert at ~1 fire per 45 seconds. This matters because TradingView rate-limits any single alert to 15 fires per 3 minutes.

### Alerts and webhooks
- A **TradingView alert** is a rule attached to a chart that says "when condition X happens, do Y." TTE creates ~340 such alerts and leaves them running 24/7.
- A **webhook** is the "Y" part: when the alert triggers, TradingView sends an HTTP POST request with a JSON body to a URL you choose. TTE points all alerts at Stock Buddy's webhook endpoint.
- The webhook **payload** has a hard ~2 KB size limit, which is why TTE uses very short JSON keys (`e`, `sl`, `tp` instead of `entry`, `stopLoss`, `takeProfit`) — to fit two symbols' worth of data into one POST.

### The trading indicators TTE uses
- **NWE — Nadaraya–Watson Envelope.** A statistical "rubber band" drawn around price. When price stretches outside the band and starts coming back, the indicator emits a bounce signal (mean-reversion logic).
- **OB / FVG — Order Block / Fair Value Gap.** Patterns from "Smart Money" trading theory that mark zones on the chart where price is likely to react. An Order Block is the last opposing candle before a strong move; a Fair Value Gap is a price-imbalance gap left behind.
- **Kernel AO Divergence.** A momentum divergence signal that compares price action against a smoothed Awesome Oscillator using a kernel function. Used as a confirming filter.

### What "a setup" means
A **setup** in TTE is the moment when an NWE bounce signal and an OB/FVG zone *line up* on two different timeframes — for example, a 1-hour NWE bounce inside a 4-hour OB zone. When that happens the screener emits **entry**, **stop-loss (SL)**, and **take-profit (TP)** prices and ships them to Stock Buddy. SL/TP are computed at a fixed 1:2 risk-to-reward ratio.

### Stock Buddy
**Stock Buddy** is the downstream web app (a separate project) that receives TTE's webhooks. It deduplicates setups using a partial unique database index, runs a 5-minute server-side cron job to detect when trades hit their TP or SL using Binance/Yahoo candle data, and surfaces the results to end users. TTE produces signals; Stock Buddy decides what to do with them.

### Selenium and headless Chrome
**Selenium** is a browser-automation library. TTE uses it to launch a real Chrome window, log into TradingView, click through the alert-creation dialog, fill in symbols, and hit save — exactly like a human would, just faster and 24/7. **Headless** means Chrome runs without drawing a visible window, so the program can run on a server. Because TradingView's UI changes frequently, much of the engineering effort is keeping the CSS/XPath selectors working across redesigns.

### Other terms
- **Maintenance loop** — a background cycle (every 150 seconds) that walks through all alerts, finds any that have been auto-disabled by TradingView, and re-enables them.
- **Persistent alert** — created once and left in place forever, instead of being created and torn down per signal. Cheaper and more reliable.
- **Headless `.exe`** — the whole Python app is bundled into a single Windows executable with PyInstaller so it can be installed and auto-started on boot like a normal program.
- **Snapshot** — a PNG screenshot of a chart with the entry/SL/TP zones drawn on it, used by downstream consumers (e.g. Discord, the Stock Buddy web UI) to show users what the trade looks like.

---

## 1. New Architecture: V1 "Tiered" → V2 "Stateless Combo" (Jan–Mar 2026)

The biggest shift of the year. The system was rebuilt from a polling-style two-phase orchestrator into a stateless, persistent-alert architecture.

| Aspect | V1 (early 2026) | V2 (production, Mar 2026) |
|---|---|---|
| Detection model | Stock Buddy synthesised setups from raw signals | Pine Script does stateless NWE + OB/FVG alignment on every bar |
| Symbols / alert | 3 | 2 (category-aware pairing) |
| Chart timeframe | 1 minute | 45 seconds |
| Alert frequency | `alert.freq_all` (every tick) | `alert.freq_once_per_bar_close` |
| `request.security()` calls per alert | 12 | 8 |
| Maintenance interval | 300 s | 150 s |
| Exit detection | Pine Script (candle high/low) | Stock Buddy server-side cron (Binance/Yahoo candles every 5 min) |
| Payload | Verbose JSON | Compact 2 KB-safe keys (`e`, `sl`, `tp`, `et`, `l`, `ntf`, `otf`) |
| Total symbols | ~1,028 | 677 |
| Total alerts | ~338 | ~340 (mostly 2 symbols/alert; a few hold 1) |

**Resume bullets**

- Re-architected a real-time trading-signals pipeline from a polling orchestrator into a persistent-alert system, cutting `request.security()` calls per alert by ~33% and halving the maintenance interval (300 s → 150 s).
- Migrated stateful position-tracking out of Pine Script into a Python/Mongo cron job, simplifying the Pine indicator and centralising exit logic with deduplication via a partial unique DB index.
- Designed a 2 KB-safe compact JSON payload schema to fit TradingView's webhook size limit while supporting two symbols per alert across four signal types.

Key commits: `0b55698` (combo mode + multi-browser), `8686c7e` (consolidated NWE/OBDIV into one TTE Screener), `d295c83` (V2 setup/exit tracking, PR #8), `6712c4e` (rewrite to stateless), `cbd5481` (PR #16: V2 cleanup).

---

## 2. Pine Script Screener — From Two Indicators to a Single Multi-Symbol Engine

Throughout Feb–Mar 2026, the Pine Script `TTE Screener V2.txt` was rewritten from scratch.

- Consolidated separate **NWE** and **OBDIV** screeners into one unified indicator (`8686c7e`).
- Implemented **Nadaraya–Watson Envelope (NWE)** signal detection on chart timeframe (shift 0) instead of inside `request.security()`, fixing a "disappearing signals" bug caused by HTF bar timestamps being stale.
- Aligned **Order Block / Fair Value Gap (OB/FVG)** gap conditions and **Kernel AO Divergence** thresholds with the upstream community indicators (`fd9102d`).
- Enforced **UTC** uniformly across all tooltip displays for cross-region consistency (`15068f4`).
- Added `session.ismarket` and regular-hours guards so equity alerts don't fire pre/post market (`7c5ebd9`, PR #12).
- Made `max_bars_back = 5000`; SL = MIN/MAX of confirming OB zone, TP = 1:2 risk-reward.
- Added a separate **Trade Drawer V2** indicator (`dab4b33`, PR #14) for self-contained snapshot rendering on chart screenshots.

**Resume bullets**

- Wrote a stateless multi-symbol Pine Script screener (~700+ LOC) detecting NWE-bounce + OB/FVG alignment across two symbols and four timeframes per alert.
- Diagnosed and fixed an HTF-timestamp bug in `request.security()` by moving signal detection to the chart timeframe, eliminating a class of false-negative alerts.
- Authored a companion `Trade Drawer` Pine indicator that renders entry/SL/TP zones for snapshot images consumed by downstream Discord/web clients.

---

## 3. Symbol Universe Expansion (Feb–Mar 2026)

- Grew the symbol universe to **677 symbols** spanning forex, crypto, US equities, and Indian equities (PR #21).
- Implemented **category-aware pairing** (`fetch_symbols_by_category` in `tte/main.py`) so each alert pairs symbols of the same asset class — matching market hours and avoiding cross-class collisions.
- Added a memory rule: failed batches are retried with their original pairing intact, never flattened.
- Removed delisted EOSUSDT/EOSBTC and synced symbol counts (`225b0af`, PR #15).

---

## 4. Selenium Browser Automation Hardening

`tte/browser/tradingview.py` is the heart of the system. 2026 work focused on making it survive TradingView's frequent UI churn.

### TradingView UI Redesign Adaptations (Apr 2026)
- Rewrote selectors for the alert dialog, timeframe dropdown, and layout toolbar after a TradingView UI redesign (`6ccd672`, `a6e64b3`, PRs #23/#24).
- `delete_all_alerts` switched from class-based selectors to text-matching with auto-retry on failed batches (`104b7be`).

### Stale-Element Resilience
- `_safe_indicator_access()` retry helper for `StaleElementReferenceException`.
- `_validate_alert_condition()` + new `_verify_trigger_condition()` to catch a race condition where the trigger dropdown stayed on "Crossing" instead of "Any alert() function call" (root-cause fixed Mar 2026).
- Replaced fragile `.label-LM2kIa9B`-class selectors with `condition_dropdown.text` attribute checks.

### Maintenance Loop
- After page refresh, the sidebar is now opened explicitly before reading alert states, fixing recurring `TimeoutException`s (`f918d77`).
- Maintenance interval = **150 s**; restarts inactive alerts; clears alert log every 3 hours.

### Reupload + Overlay Recovery
- `reupload_indicator()` rebuilt with updated TradingView selectors (`43f94f4`).
- Added overlay-retry logic in `change_settings()` to dismiss modal overlays that block input (`87ef381`).

**Resume bullets**

- Maintained a Selenium 4 / Chrome browser-automation layer driving TradingView Premium, keeping it operational through three platform UI redesigns in three months.
- Built defensive selector helpers (text-match fallback, attribute-based reads, stale-element retry) that reduced unattended-failure rate and enabled fully headless 24/7 operation.
- Designed and shipped a `change_settings()` overlay-retry routine and a `--symbols` CLI flag to scope reruns to specific tickers without touching the full universe.

---

## 5. Single-Browser Headless Mode + GUI (Feb 2026)

- Switched from a multi-browser parallel architecture to a **single-browser sequential** flow (`4b9b246`), cutting Chrome memory footprint and simplifying error recovery.
- Added **headless mode** as default.
- Built a Tkinter **GUI** (`tte_gui.py`) with start/stop, headless toggle, and snapshot settings.
- Added **graceful shutdown** + Chrome process cleanup on stop (`8139027`).
- Packaged with PyInstaller into `dist/TTE.exe`, including `pystray` system-tray bundling (`27a12ff`, `9828446`).
- Auto-start on Windows boot via `setup_startup.ps1`; default to `--maintain-only`; 3-hour log auto-clear (`80d713a`).

---

## 6. Chart Snapshot Worker (Feb–Mar 2026, PRs #6, #7, #14, #20)

A new subsystem that captures branded chart images for every setup signal so downstream consumers can post screenshots to Discord/web.

- Added `tte/snapshot_worker.py` polling Stock Buddy for pending snapshot requests.
- Polls every 60 s, processes batches of 10, with explicit indicator-load waits before screenshotting (`0c61633`).
- Self-contained `Trade Drawer V2` indicator renders entry/SL/TP zones onto the chart for the snapshot.
- Hardened the pipeline (PR #20): backfill, dialog cleanup, throughput improvements.
- Snapshot worker uses `full_symbol` for exchange-prefixed resolution (`de9c310`), preventing wrong-exchange snapshots for ambiguous tickers.

**Resume bullets**

- Built a chart-snapshot subsystem that polls a REST queue, drives a second TradingView layout, and returns rendered PNG screenshots with overlaid trade zones — integrated with the main alert workflow without blocking webhook delivery.

---

## 7. Bug Fixes (notable)

- **Indian stock alerts never triggering** — fixed by adding a session.ismarket guard tuned for NSE/BSE hours (`e77888e`, PR #11).
- **NWE signals using wrong-symbol prices** in multi-symbol mode (`8e97197`).
- **Divergence false positives** gated to bar shift 0/1, replacing impossible timestamp matches (`ad9bee0`).
- **OB timestamps wrong** across all timeframes (`21e7c1a`).
- **Webhook URL accidentally committed** — reverted and untracked `.env` (`4d08793`, `d7964f4`).
- **Symbol button selector** updated to `span.value-JQZ0HKD4` (`0fff4f7`).
- **Selenium driver management**: removed `webdriver-manager`, switched to Selenium 4 built-in (PR #17), then added explicit chromedriver path to bypass `SeleniumManager` network calls (PR #19).

---

## 8. Code Quality & Tooling (Feb 2026)

- Reorganised the codebase from flat scripts into a proper `tte/` Python package (`9c87d44`).
- Removed legacy/tiered code paths and unused dependencies (`c5b269f`, `762800a`).
- Added **black** auto-format via PostToolUse hook (`2750d28`) and applied repo-wide formatting (`a566b80`).
- Added **pre-commit hooks** (PR #7).
- Added **pytest unit tests** for the `tte/` package (`7907ba7`).
- Replaced debug `print()` calls with structured `logging` (`5fa9578`).
- Fixed critical security issues: removed secrets from tracked files (`8558d25`).
- Wrote `.claudeignore` and a comprehensive deny list for dangerous shell commands.

---

## 9. Documentation & DevEx

- Authored `docs/combo/ARCHITECTURE.md`, `docs/combo/PRD.md`, `docs/combo/IMPLEMENTATION.md`, `README.md`, `SETUP.md`, `API.md`.
- Wrote dedicated indicator docs for **NWE**, **OB/FVG**, and **Kernel AO Divergence** (`274a881`).
- Built custom Claude Code agents (`qa`, `selenium-patterns`, `deploy`) for repeatable browser-automation review (`cf4cf35`).
- Created an `/update-docs` skill that audits and syncs all docs after feature changes.

---

## 10. Operational State (as of Apr 2026)

- 677 symbols across ~340 persistent webhook alerts (most pair two symbols; a few hold one), sequentially created with one headless Chrome instance.
- 45-second chart timeframe, candle bar style, `freq_once_per_bar_close`.
- Maintenance loop restarts inactive alerts every 150 s; logs auto-clear every 3 hours.
- Webhooks flowing at ~100+/24 h, 100% HTTP 200 to Stock Buddy.
- Auto-starts on Windows boot, runs unattended.

---

## Tech Stack (for the "Skills" line on a resume)

**Languages:** Python 3, Pine Script v5, PowerShell, Bash
**Automation/Browser:** Selenium 4, Chrome, undetected-chromedriver, PyInstaller, pystray, Tkinter
**Data/Backend:** MongoDB (PyMongo), REST webhooks, JSON
**Trading:** TradingView Premium, custom multi-symbol screeners, NWE / OB-FVG / Kernel AO Divergence
**Tooling:** pytest, black, pre-commit, GitHub CLI (`gh`), PyInstaller
**Patterns:** Stateless signal detection, server-side dedup via partial unique index, category-aware batching, graceful shutdown, headless 24/7 daemons

---

## Suggested Resume Bullets (copy-paste-ready)

- Re-architected a real-time trading-signals pipeline (TradingView → Stock Buddy) from a polling orchestrator into a persistent-alert system handling **677 symbols across ~340 webhook alerts** with sub-minute latency.
- Wrote and maintain a stateless multi-symbol **Pine Script v5** screener combining Nadaraya–Watson Envelope and Order-Block/FVG detection across four timeframes per alert; designed a 2 KB-safe compact JSON payload to fit TradingView's webhook size limit.
- Built and hardened the Selenium 4 / headless-Chrome automation layer that creates and maintains TradingView alerts unattended; kept it operational through three TradingView UI redesigns by introducing text-match fallbacks, stale-element retries, and overlay-recovery routines.
- Added a chart-snapshot subsystem polling a REST queue and returning rendered PNGs with overlaid entry/SL/TP zones; integrated without blocking the main webhook flow.
- Reorganised the codebase into a typed `tte/` Python package, added pytest, black, pre-commit, structured logging, secrets hygiene, and PyInstaller packaging into a single `TTE.exe` with a Tkinter GUI and Windows boot auto-start.
- Reduced operational toil: maintenance interval halved (300 s → 150 s), `request.security()` calls per alert cut by ~33%, headless mode by default, 3-hour log auto-clear, single-browser memory footprint.
