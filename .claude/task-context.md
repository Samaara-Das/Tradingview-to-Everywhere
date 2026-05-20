# Task Context Tracker

**Last Updated**: 2026-05-20 12:55 IST
**Current Task**: Multi-instance steady-state — tte-1 (Sammy's TV) at 1000 active alerts in `--maintain-only`, tte-2 (Rahul's TV) at Batch ~520/1001 in `--fresh` setup (ETA ~2h). Both have Trade Drawer V2 in favorites + Snapshot layout. PR #48 (`fix/alert-persistence-verify`) contains 9 commits worth of fixes from the 2026-05-19/20 multi-day incident.
**Active Branch**: `fix/alert-persistence-verify` @ `d2852ef`
**Cron monitor**: in-session cron `f51e3769` fires every :13 and :43 past hour, halts containers + DMs Sammy on any indicator destruction or restart loop.
**Session detail**: `memory/diary_2026-05-19.md` covers the bulk; this session's tail (2026-05-20 morning) covered Trade Drawer V2 install on both accounts via Pine Editor automation, Instance ID regression on tte-2, and TV-cap investigation.

---

## Task Progress Summary

| # | Task | Status |
|---|------|--------|
| 1-16 | Previous tasks (alerts, signals, snapshots, cleanup) | **done** |
| 17 | Fix TradingView layout selector bug | **done** (2026-04-06) |
| 18 | Update webhook URL to new Stock Buddy deployment | **done** (2026-04-06) |
| 19 | Update webhook URL to stockbuddy.co custom domain | **done** (2026-04-07) |
| 20 | Fix delete_all_alerts dropdown bug | **done** (2026-04-07) |
| 21 | Auto-retry failed alert batches after creation | **done** (2026-04-07) |
| 22 | Fix layout dropdown selector (scoped XPath + navigate via href) | **done** (2026-04-07) |
| 23 | Fix timeframe dropdown (collapsible sections redesign) | **done** (2026-04-07) |
| 24 | Fix alert creation hang (two root causes) | **done** (2026-04-07) |
| 25 | Run `--fresh` via TTE.exe to recreate 340 alerts | **done** (2026-04-07, 280/340) |
| 26 | Retry 60 failed alert batches (119 symbols) | **done** (2026-04-09, 60/60) |
| 27 | Fix `STOCK_BUDDY_API_URL` in `.env` (old Vercel → stockbuddy.co) | **done** (2026-04-09) |
| 28 | Sync all docs after PRs #19-#24 (webhook URLs, batch sizes, counts) | **done** (2026-04-09) |
| 29 | Create TTE-specific /update-docs skill | **done** (2026-04-09) |
| 30 | Rebuild TTE.exe (post-PR #24 UI fixes) | **done** (2026-04-09, 19.43 MB) |
| 31 | Diagnose 6-day snapshot blackout (root cause: TV session logged out) | **done** (2026-05-14) |
| 32 | Ship PR #39 — `is_chart_layout_loaded()` + `ensure_chart_layout_loaded()` guards in snapshot worker + maintenance | **done** (2026-05-14) |
| 33 | Rebuild + deploy tte:phase4 image on KVM8 (preserving 4 unupstreamed patches) | **done** (2026-05-14) |
| 34 | Verify 5 fresh `setup_messages` PNGs render reversed Trade Drawer V2 layout correctly | **done** (2026-05-14) |
| 35 | Install 6 TTE monitoring checks + `tte-checks.timer` (systemd, every 5 min) | **done** (2026-05-14) |
| 36 | Switch cc-trigger Telegram → Discord webhook digests | **done** (2026-05-14) |
| 37 | E2E smoke test all 6 monitoring → Discord pipeline | **done** (2026-05-14) |
| 38 | Coda task `i-iNXjRwYS9h` closure (server migration & docker setup) | **done** (2026-05-14 via `.claude/coda-closure-2026-05-14.md`) |
| 39 | Ship PR #40 — auto-2FA via pyotp + `TRADINGVIEW_TOTP_SECRET` env | **done** (2026-05-15, code merged) |
| 40 | Verify-and-store correct TOTP secret in `.env.tte.1` | **parked** (2026-05-15) — TV's secret display unreliable; pivoted to backup-code workflow |
| 41 | Autonomous backup-code regeneration via local Chrome MCP | **done** (2026-05-15) — 6 fresh codes captured + saved |

---

## Session History

### Session: 2026-05-15 (TOTP follow-up + production unblock)

**User request**: complete the 2FA follow-up so future container restarts don't need manual 2FA injection.

#### 1. Shipped PR #40 (`feat/totp-autoinject`) — auto-2FA via pyotp
- Added `Browser._maybe_auto_submit_totp()` that polls for TV's 2FA input, computes the current 6-digit code from `TRADINGVIEW_TOTP_SECRET` env var via pyotp, and submits via JS event dispatch (React-friendly).
- Code-reviewer sub-agent caught 2 HIGH issues (8s poll vs slow render, single-text-input vs 6-digit-boxes assumption) — both addressed.
- Merged at commit `40ab6bf` after squash. Pipfile + Pipfile.lock regenerated with pyotp dep.

#### 2. Production outage during TOTP deploy (90 min)
- After user disabled+re-enabled TV 2FA to capture the secret, the displayed base32 string (`4ZE3CWH77ER37PSQ`) **was NOT the secret TV ultimately stored** — TV rejected every code derived from it with `Incorrect verification code (403)`.
- Container crash-looped for ~45 min through 5 hotfix iterations (TV signin UI moved past Email-button picker → fix; 2FA input renamed `code`→`id_code` → fix; React-controlled input ignored Selenium `send_keys` → switched to JS event dispatch; etc.).
- Pyotp code path itself works correctly — verified `pyotp.TOTP(secret).now()` matched the user's phone code for the right time window. The blocker was the secret string never matching TV's server-stored secret.

#### 3. Pivot to autonomous backup-code regeneration
- Used `mcp__chrome-devtools` to drive a local Chrome through TV's "Generate new codes" flow programmatically (password-only auth, no email/SMS verification needed).
- Captured 6 fresh codes (`txrvcBBb mdHZH07u NHSceF6k Qn4EpZZz wCYA4Yhc YosLNyUZ`) directly from the modal DOM.
- Saved to `C:\Users\dassa\Passwords and tokens\tradingview backup codes.txt`.

#### 4. Cookies-survive-disconnect observation
- TV's "Session disconnected — only one session allowed per user" modal pops up when a second browser signs in, but **does NOT invalidate** the first session's cookies in the user-data-dir volume. After my local Chrome stole the session, tte-1's restart re-used its existing cookies and reached "Browser ready" without needing any backup code.

#### 5. Documentation updates
- `.claude/credentials-and-2fa.md` — autonomous regen-codes procedure documented end-to-end.
- `.claude/learnings.md` — 5+ new entries (TV signin UI changes, React fill vs evaluate_script, settings URL `/settings/#account-settings`, session-disconnect doesn't invalidate cookies, must-verify-TOTP-secret before deploy).
- `tradingview backup codes.txt` — 6 fresh codes; format documents how to mark consumed.

---

### Session: 2026-05-14 (Snapshot blackout incident response + Phase 6 monitoring)

**User request**: investigate why snapshot pipeline has been 100% failing since 2026-05-08, fix it, build monitoring so it doesn't happen again.

#### 1. Root cause: TV session logged out (NOT selector breakage)
- Live tte-1 DevTools probe via port `/home/tte/chrome-profile/TTE/DevToolsActivePort` revealed `document.title = "Chart Not Found — TradingView"` and `body = "We can't open this chart layout for you. You need to log in..."` on the owner-only Snapshot layout (`yDNmRCDO`).
- All 6 chart selectors (chart-markup-table, header-toolbar-symbol-search, right-toolbar Alerts, etc.) returned 0 elements — because the chart simply doesn't exist on the placeholder page.
- Earlier hypothesis of TV-UI-redesign-breaks-selectors was wrong; all selectors are intact in a logged-in Chrome.

#### 2. PR #39 (`fix/snapshot-pipeline-2026-05-14`)
- `Browser.is_chart_layout_loaded()`: detects placeholder page via title + chart-markup-table presence.
- `Browser.ensure_chart_layout_loaded()`: if not loaded, re-runs `setup_tv()` to re-establish session. Suppresses `self.start_fresh` during recovery so a transient logout never deletes production alerts.
- `snapshot_worker.process_pending_snapshots`: guard at top of poll loop.
- `main.restart_inactive_alerts` (maintenance): same guard, hoisted to run **before** `open_alerts_sidebar()` (reviewer caught this — that selector itself times out on the placeholder).

#### 3. Deploy + verification
- Rebuilt `tte:phase4` on KVM8 preserving 4 unupstreamed source patches (`tframe_skip` and `sleep(2)` tightening in `snapshot_worker.py`, `bus_log_try_except` in backfill module, `launcher_syspath` + `sign_in_call` in `scripts/run_reversed_backfill.py`).
- One-shot stop+rm+up. **2FA hit on first cold start** — TV had auto-enabled 2FA on the bot account during the 6-day outage. User-injected backup code via DevTools script unblocked.
- Verified 5 fresh post-deploy snapshots (GBPUSD, ODFL, BLDR, QUBT, ADSK) render Trade Drawer V2 + correctly-REVERSED TP/SL layout (Mongo `stopLoss` → on-chart `TP1`, Mongo `takeProfit` → on-chart `SL`).

#### 4. Monitoring infrastructure (Phase 6 MVP)
- 6 check scripts at `/opt/stockbuddy/monitoring/checks/tte-*.sh`:
  - snapshot-success-rate (<80% over 1h fires)
  - snapshot-failed-burst (>10 failures in 30m)
  - change-symbol-errors (>5 in 30m)
  - alert-sidebar-errors (>5 ERROR/WARNING lines in 30m — regex tightened next session to avoid false positive on success log line)
  - container-restart (delta in RestartCount)
  - webhook-delivery (maintenance-cycle marker count during market hours)
- `tte-checks.timer` (systemd, every 5 min), `run-checks.sh` wrapper.
- Helpers: `_alert_helper.sh` with dedupe state at `/opt/stockbuddy/cc-state/check-state/<name>.json` (min 1h between repeat alerts) + `fire_alert` that POSTs to `127.0.0.1:8765/alert`.
- Mongo-backed checks call `docker exec tte-1 python3` with pymongo (no local Mongo container in this hybrid setup; data lives in Atlas).

#### 5. cc-trigger migration (Telegram → Discord)
- `/opt/stockbuddy/cc-trigger/server.js` rewritten — Telegram code path removed entirely. Discord embeds with severity-color sidebar + fields for component/severity/window/values.
- Discord webhook URL stored at `/opt/stockbuddy/secrets/.env.cc` (chmod 600 stockbuddy-owned), NEVER committed. `cc-trigger.service` already loads via `EnvironmentFile=`.
- E2E smoke test: 6 alerts (1 natural from monitoring + 1 explicit smoke + 4 simulated) → 0 Discord delivery errors, each cc-trigger spawn produced a meaningful claude-investigation summary.

#### 6. Coda task closure
- Coda MCP disconnected mid-session; fallback `.claude/coda-closure-2026-05-14.md` written with full closure summary, PR/commit/deploy/verification links, and limitations (orphan-image risk, off-screen-entry-time bug for old setups).

---

### Session: 2026-04-09

**User request**: Retry 60 failed alert batches, fix maintenance loop, fix snapshot worker, update docs, rebuild exe.

#### 1. Retried 60 failed alert batches (119 symbols)

**Root cause of original failure**: Screener V2 indicator had been removed from the "Screener" layout after force-kills corrupted Chrome profile state. `get_indicator()` timed out on `legend-source-item`.

**How**: User manually re-added the indicator to the layout. Then we ran `--symbols` with all 119 symbols via Python directly (bash line-length limit prevented `--symbols` CLI with that many symbols).

**Result**: 60/60 alerts created successfully. Total alert count: ~340.

#### 2. Fixed snapshot worker (402 errors)

**Root cause**: `STOCK_BUDDY_API_URL` in `.env` still pointed to old Vercel deployment: `https://stock-buddy-app.vercel.app/api/tte`. That deployment is paused/over quota, returning 402.

**Fix**: Updated `.env` line 34: `STOCK_BUDDY_API_URL="https://stockbuddy.co/api/tte"`

**Verified**: Snapshot worker fetched 10 pending snapshots, took screenshots, submitted to Stock Buddy with no errors. Log line: `Fetched 10 pending snapshots` + multiple `Snapshot completed for NSE:*` with no `Failed to update snapshot` errors.

#### 3. Fixed maintenance loop (zombie process)

**Root cause**: Previous `--symbols` runs left 3 stale Python processes (PIDs 17640, 9376, 16704) with dead browser sessions. Killed them all, started fresh `--maintain-only`.

**Confirmed working**: First cycle: `No inactive alerts to restart (button is disabled)` + `Alert log cleared!`

#### 4. Documentation sync (after PRs #19-#24)

Updated 8 doc files and the /update-docs skill itself:

| File | Changes |
|------|---------|
| `CLAUDE.md` | Added `snapshot_worker.py`, `--symbols` flag, `STOCK_BUDDY_API_URL`/`API_TIMEOUT` env vars, fixed `snapshot.batch_size` (5→10), removed stale AGENTS.md reference |
| `README.md` | Updated webhook URL, added `--symbols` flag, added `snapshot_worker.py` to structure |
| `docs/combo/ARCHITECTURE.md` | Updated webhook URL, fixed `handle_alerts.py` ref → `tte/main.py` |
| `docs/combo/PRD.md` | Moved failed-batch-retry/UI-fixes to Completed; fixed `snapshot.batch_size` (5→10) |
| `docs/API.md` | Updated base URL and all curl examples |
| `docs/SETUP.md` | Updated webhook URL, fixed `snapshot.batch_size` (5→10) |
| `docs/TROUBLESHOOTING.md` | Updated ChromeDriver section (Selenium 4 built-in); added TradingView UI Changes section |
| `docs/DATABASE.md` | Updated symbol counts (us_stocks ~719→~376, indian_stocks ~268→~197), updated webhook URL |
| `.claude/skills/update-docs/SKILL.md` | Full rewrite: TTE-specific (was Stock Buddy) |
| `.claude/skills/update-docs/references/doc-inventory.md` | Updated to April 2026; added Trade Drawer V2 |

#### 5. Rebuilt TTE.exe

Previous exe (built 15:38 Apr 7) was missing PR #24 UI fixes (merged 16:08 Apr 7).

**Result**: New `dist/TTE.exe` — 19.43 MB, PyInstaller 6.18.0, all validations passed. User launched it successfully.

---

### Session: 2026-04-07 (TradingView UI Redesign Fixes)

**User request**: Run `--fresh` to recreate all 340 alerts. Hit multiple TradingView UI breakages.

#### Bug 1 — Layout dropdown XPath too broad (FIXED)
**Root cause**: XPath `//*[normalize-space(text())="Screener"]` matched chart legend instead of dropdown item.
**Fix** (`tte/browser/tradingview.py` `change_layout()`): Scoped to `data-qa-id="save-load-menu-item-recent"`. Non-current layouts are `<a target="_blank">` links — extract `href`, navigate via `driver.get(url)`.

#### Bug 2 — Timeframe dropdown redesigned (FIXED)
**Root cause**: Changed from flat list to collapsible sections (Ticks/Seconds/Minutes/Hours/Days/Ranges).
**Fix** (`tte/browser/chart.py`): New helpers `_get_timeframe_section()`, `_open_timeframe_dropdown()`, `_expand_timeframe_section()`. Rewrote `change_tframe()` and `force_change_tframe()`.

#### Bug 3 — Alert creation hang (FIXED — two root causes)
**Root Cause 1**: Screener V2 missing from chart layout (Chrome profile corruption from force-kills).
**Root Cause 2**: TradingView alert dialog redesigned — removed tabs, now uses "Webhook >" button opening a separate sub-dialog.
**Fix** (`tradingview.py` `create_webhook_alert()`): Two-dialog flow (see Alert Dialog Selectors below).

**Other fixes**: `_validate_alert_condition()` contains-match selector; `is_no_error()` stable `data-qa-id` selectors.

---

## Important Decisions Made

### STOCK_BUDDY_API_URL base path (2026-04-09)
`https://stockbuddy.co/api/tte` is correct. The snapshot worker appends sub-paths (`/snapshots/pending`, `/snapshots/update`). The base URL itself returns 404 — that's expected, only sub-routes exist.

### Layout Navigation via href (2026-04-07)
Non-current layouts in TradingView's dropdown are `<a target="_blank">` links. Clicking them opens a new tab. **Solution**: Extract `href` and navigate via `driver.get(url)`.

### Timeframe Dropdown Section Expansion (2026-04-07)
TradingView now groups timeframes into collapsible sections. TTE must: (1) identify section, (2) expand if `aria-expanded="false"`, (3) find item.

### Alert Dialog Two-Step Flow (2026-04-07)
Webhook settings are now behind a "Webhook >" button that opens a separate sub-dialog. TTE must: (1) configure conditions in main dialog, (2) click webhook button, (3) configure webhook in sub-dialog, (4) apply, (5) create in main dialog.

### legend-source-item vs legend-series-item (2026-04-07)
- `legend-series-item` = main chart series (OHLC bars)
- `legend-source-item` = added indicators/studies (Screener V2) — use this for indicator access

---

## Key Reference Files

| File | Purpose |
|------|---------|
| `tte/main.py` | Entry point (orchestrator, alert creation loop, auto-retry) |
| `tte/browser/tradingview.py` | Browser automation (layout, indicator, alert creation, `is_no_error`) |
| `tte/browser/chart.py` | Chart navigation (timeframe collapsible sections, symbol search) |
| `tte/snapshot_worker.py` | Chart snapshot polling & browser orchestration |
| `tte/config.py` | Config dataclass (`recalc_wait=2.0`, `headless=true`) |
| `combo_settings.yaml` | Settings (batch_size=2, 45 seconds, screener "Screener V2", snapshot.batch_size=10) |
| `.env` | `COMBO_WEBHOOK_URL=https://stockbuddy.co/api/tte/combo`, `STOCK_BUDDY_API_URL=https://stockbuddy.co/api/tte` |

---

## Verified Patterns (Updated 2026-04-09)

### Layout Toolbar Selectors
```
Save button:        button#header-toolbar-save-load
Layout name:        button#header-toolbar-save-load .text (use .text.strip())
Dropdown trigger:   button[data-name="save-load-menu"]
Dropdown menu:      div[data-qa-id="menu-inner"]
Layout items:       *[@data-qa-id="save-load-menu-item-recent"]
  Current layout:   <div> element (no href)
  Other layouts:    <a href="/chart/{id}" target="_blank"> element
Layout name span:   .//span[normalize-space(text())="LayoutName"]
```

### Timeframe Toolbar Selectors
```
Quick-access btns:  #header-toolbar-intervals button
Active timeframe:   #header-toolbar-intervals button[aria-checked="true"]
Dropdown chevron:   #header-toolbar-intervals > button[aria-label="Chart interval"]
Dropdown menu:      div[data-qa-id="menu-inner"]
Section headers:    button[data-qa-id="ui-lib-title-list-item"][aria-label="Seconds"]
  Expanded:         aria-expanded="true"
  Collapsed:        aria-expanded="false"
Timeframe items:    div[data-qa-id="interval-menu-item"][aria-label="45 seconds"]
  Selected:         aria-selected="true"
```

### Legend/Indicator Selectors
```
Legend items:       div[data-qa-id="legend-source-item"]   (indicators/studies)
Chart series:       div[data-qa-id="legend-series-item"]   (main chart bars)
Indicator title:    [data-qa-id*="legend-source-title"]
Settings button:    button[data-qa-id="legend-settings-action"]
Statuses wrapper:   div[data-qa-id="legend-statuses-wrapper"]
Error detection:    [data-qa-id="legend-statuses-wrapper"] [class*="dataProblem"]
```

### Alert Dialog Selectors (VERIFIED WORKING 2026-04-07)
```
+ button:           div[data-name="set-alert-button"]
Main dialog:        div[data-qa-id="alerts-create-edit-dialog"]
Condition dropdown: [data-qa-id*="main-series-select"]
Operator dropdown:  button[data-qa-id="operator-dropdown"]
Webhook nav button: button[data-qa-id="alert-notifications-button"]
Submit/Create:      button[data-qa-id="submit"]
Cancel:             button[name="cancel"][data-qa-id="cancel"]
Close (X):          button[data-qa-id="close"]

Notifications sub-dialog:
  Dialog container: div[data-qa-id="alerts-notifications-edit-dialog"]
  Back button:      button[data-qa-id="back"]
  Webhook checkbox: label[data-qa-id="webhook"] input[type="checkbox"]
  Webhook URL input: input#webhook-url
  Apply button:     button[data-qa-id="submit"] (inside sub-dialog context)
```

### Alerts Settings Dropdown
```
3-dots button:      div[data-name="alerts-settings-button"]
Menu items (text):  XPath: //div[@data-qa-id="menu-inner"]/div[.//span[normalize-space(text())="Label"]]
Confirm dialog:     div[data-name="confirm-dialog"]
Confirm yes:        button[name="yes"]
```

---

## Test Commands

```bash
# TTE
pipenv run python combo_main.py --fresh             # Delete alerts & recreate (~340 alerts)
pipenv run python combo_main.py --setup-only         # Setup only
pipenv run python combo_main.py --maintain-only      # Maintenance + snapshots (headless)
pipenv run python combo_main.py --validate           # Validate config
pipenv run python combo_main.py --symbols A,B,C      # Create alerts for specific symbols only
dist/TTE.exe                                         # GUI (requires rebuild after code changes)

# Verification
pipenv run pyright tte/                              # Type checking
pipenv run ruff check tte/                           # Linting
python -c "from tte.data.symbols import get_symbols; s=get_symbols(); print(sum(len(v) for v in s.values()))"
```

## Remaining Tasks

1. [ ] Delete debug PNG files (`debug_headless.png`, `debug_tte_profile.png`, `debug_flow.png`, `debug_get_indicator_fail.png`)
2. [ ] Fix Chrome/ChromeDriver version mismatch (Chrome 146, cached driver 145) when convenient
3. [ ] **Off-screen-entry-time bug** — old setups have entryTime hours/days before render time → TP/SL labels drawn off the visible range. Cosmetic, doesn't affect new setups. Fix likely involves `chart_scroll_to_date(entryTime)` before snapshot capture.
4. [ ] **TOTP auto-2FA verification** — pyotp code path (PR #40) is in the image but inert. To reactivate: capture a verified-correct TV TOTP secret (via a fully-instrumented disable+re-enable flow with same-window pyotp-vs-phone comparison), then populate `/opt/stockbuddy/secrets/.env.tte.1::TRADINGVIEW_TOTP_SECRET`. Backup-code workflow is fine in the meantime.
5. [ ] Tighten `tte-alert-sidebar-errors.sh` regex — already done in this session (filters on ` - (ERROR|WARNING) - ` prefix) but worth a second review next time the file is touched.
6. ~~When backup-code count drops to 1-2 left~~ — N/A: TV backup codes are **reusable** (confirmed 2026-05-15). Only regenerate if Sammy wants to rotate (e.g. after sharing a code with someone like Nili).
