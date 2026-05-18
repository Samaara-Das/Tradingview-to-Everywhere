# Task B — TTE-side context (durable reference)

> Captured 2026-05-15 by `tte worker` session in collaboration with `sb worker` (Stock Buddy Claude). Source plan: `C:\Users\dassa\.claude\plans\luminous-strolling-catmull.md`.
>
> Read this at session start when working on Task B. Section C.6 has the open questions for Sammy — keep them in mind, don't act on assumed answers.

## 0. Coda task & cross-Claude bus

- **Coda row**: `i-Bg86Rc9w5Z` ("Connect 2 TV accounts to Stock Buddy") in doc `gQSY1wWZMv`, table `My To-dos`. Status: In progress.
- **Bus file**: `.claude/agent-comms.md`. Append a dated section per handoff; the other Claude polls this file every 90s.
- **Sammy is unavailable during day-job hours** — both sessions must operate without questions back. Park questions in this file's C.6 section.

## 1. Task B in one sentence

Run two TTE instances (`tte-1` for Sammy's `dassamaara`, `tte-2` for Rahul's TV account) on KVM8, watching ~4000 symbols total (2000/account), with autonomous onboarding for future accounts and recovery from multi-device session disconnects.

## 2. Single-tenant assumptions in current code

Every place where the codebase assumes one TV account / one TTE instance. All citations verified against `main` HEAD `63bc7e6`. Severity scale: TRIVIAL (env-var swap) / MEDIUM (code path needs parameter threaded) / HARD (schema or contract change).

| # | Area | File:line | Current assumption | Knob today | Severity |
|---|------|-----------|--------------------|-----------|----------|
| 1 | Chrome profile dir | `tte/config.py:18`; `tte/browser/tradingview.py:~141, ~190` | `CHROME_PROFILE` env; `user_data_suffix=""` accepted by `Browser()` but never passed | env-only | TRIVIAL — pass `user_data_suffix="-2"` |
| 2 | TV credentials | `tte/browser/tradingview.py:~350-382`; `.env` | Single `TRADINGVIEW_EMAIL` / `_PASSWORD` / `_TOTP_SECRET` per process | env-only | TRIVIAL — separate `.env.tte-1` / `.env.tte-2` |
| 3 | Mongo `symbols` collection | `tte/data/symbols.py:56,65,87,96` | Shared read-only; no `instance_id` field | none | TRIVIAL (read-only) — partitioning logic lives in `main.py`, not here |
| 4 | Webhook URL | `tte/config.py:55`; `combo_settings.yaml:15` | Single `COMBO_WEBHOOK_URL` for all alerts | env-only | MEDIUM — needs `?instance=tte-1` query param; Stock Buddy must parse |
| 5 | Alert maintenance | `tte/main.py` `restart_inactive_alerts()` (~line 397) | "Restart all inactive" UI button operates on the entire TV account | none | HARD if same TV account; **mitigated by tte-2 using a different account**. Still need alert-name partitioning if both ever watch overlapping symbols on one account |
| 6 | Symbol assignment | `tte/main.py` `fetch_symbols_by_category()` (~line 82); `tte/data/symbols.py:111` | Loads all symbols from Mongo, batches them all | `--symbols A,B,C` CLI override (~line 723) | MEDIUM — need per-instance slice. Options: (a) add `instance` field on symbol docs, (b) compute slice in main.py from `TTE_INSTANCE` env, (c) drive via `--symbols` flag with two static lists |
| 7 | TV layout names | `combo_settings.yaml:2,18`; `tte/config.py:40,69` | "Screener" / "Snapshot" — global names | YAML/env | TRIVIAL — each TV account has its own layout namespace; collisions only matter within an account |
| 8 | Logging | `tte/log.py:20-22` | `LOG_DIR` env defaults to `logs/`; single `app_log.log` | env | TRIVIAL — `LOG_DIR=/app/logs` already per-container in Docker; host-bind `/var/log/tte-1`, `/var/log/tte-2` |
| 9 | Snapshot worker polling | `tte/snapshot_worker.py:42-116` | `GET /api/tte/snapshots/pending?limit=N` with no instance filter | none | HARD — two instances will race for the same pending snapshots. **Stock Buddy** must add instance filter + atomic claim |
| 10 | Dockerfile | `Dockerfile` (root) | `CHROME_USER_DATA_DIR=/home/tte/chrome-profile`, `LOG_DIR=/app/logs`, user uid 1000 | docker run/compose env override | MEDIUM — single image, per-container env; need compose template or two compose files |
| 11 | GUI / scripts | `tte_gui.py`, `combo_main.py`, `scripts/` | Single-process assumptions only at entry-point | n/a | TRIVIAL — out of scope for prod |

## 3. Coordination hazards (shared resources)

Need explicit ownership semantics before `tte-2` goes live:

| Resource | Hazard | Required mitigation | Owner |
|----------|--------|---------------------|-------|
| TV account credentials | If `tte-2` runs with Sammy's creds, both containers fight the same TV session | Use Rahul's account for `tte-2`, full stop | TTE (creds split) |
| Stock Buddy `/api/tte/snapshots/pending` | Both instances poll same queue → duplicate snapshot work | SB tags snapshot docs with `tteInstance`, filters by caller's `?instance=`, claims atomically on poll | **Stock Buddy** (primary) + TTE (pass instance) |
| Webhook URL `/api/tte/combo` | SB can't tell which instance/account a signal came from | TTE appends `?instance=tte-1` / `tte-2`; Pine Script payload also includes instance | **Stock Buddy** (parse) + TTE (URL/payload) |
| Mongo `symbols` read | None — shared read-only | None | n/a |
| Mongo `tte_live_signals`, `setup_messages` | If both instances watch overlapping symbols, duplicate signal docs | Symbol partitioning at source: tte-1 owns set A, tte-2 owns set B, no overlap | **TTE** (symbol slice) |
| TV alerts ("Restart all inactive") | Within an account, this button is global | Naturally partitioned because each instance is on its own TV account | n/a |

## 4. Workstream decomposition (TTE side)

### WS-1 — Symbol scaling (~677 → ~4000)
*Greenfield TV-screener scraper.*

- **Current state**: `tte/data/symbols.py` reads `db.symbols` collection. Schema: `{symbol, full_symbol, category}`. Verified live counts on 2026-05-15: 387 Indian + 243 US + 29 Currencies + 18 Crypto = **677**. The header comment in `symbols.py` was stale (claimed 1053); now corrected to "snapshot only — drifts."
- **Need**: ~3000 more US stocks + ~2800 more Indian stocks, ranked by valuation/market cap, scraped from TV screener.
- **Options**:
  - (a) Selenium driver targeting `https://www.tradingview.com/screener/`, configure exchange + sort by market cap, paginate.
  - (b) Reverse-engineer TV's screener WebSocket API (public, undocumented; the `tradingview-screener` PyPI package wraps it — worth evaluating).
- **Risk**: `batch_size=2` category-aware pairing in `tte/main.py` (~line 82) assumes balanced categories. With US Stocks growing 4× and currencies static, the tail batches will be all-US-stocks. Load-test required but probably fine.
- **Hard constraint**: `tte/config.py:96` validates `batch_size between 1 and 4 (TradingView hard limit)`. Don't scale by raising batch size.

### WS-2 — Multi-instance plumbing (`tte-2` alongside `tte-1`)
- Apply rows 1, 2, 4, 6, 8, 10 from Section 2. Mostly env/config plumbing.
- **New file likely needed**: `docker-compose.yml` at repo root (absent today; `Dockerfile` exists). Two services, two env files, two named volumes.
- **Pass-through change**: read `TTE_INSTANCE` once in `tte/__init__.py` or new `tte/instance.py` and expose throughout.

### WS-3 — Autonomous onboarding
- **Current state**:
  - `_maybe_auto_submit_totp()` (`tte/browser/tradingview.py:415-557`) handles TOTP submit with React-state-aware native value setter + dispatch (2026-05-14 fix is in code on `main`).
  - `setup_tv()` (~line 559-649) post-login: change layout → timeframe → open alerts → verify screener → set bar style → save layout.
  - `is_chart_layout_loaded()` / `ensure_chart_layout_loaded()` (lines 269, 292) detect chart-not-found and re-run `setup_tv()`.
- **Gaps**:
  - No layout export/import. `save_layout()` writes to TV cloud but doesn't replicate to other accounts.
  - No indicator-favoriting automation. Screener must be manually starred on each TV account first.
  - No backup-code rotation helpers (codes are reusable per 2026-05-15 learning, but no file-based store).
  - No noVNC-driven first-login script committed (manual workflow referenced in MemPalace).
- **Build needed**: an onboarding script that takes `(email, password, totp_secret_or_backup_codes_path)` and:
  1. Spins up a fresh Chrome profile in an isolated dir.
  2. Logs in (reuses `setup_tv` minus the layout step).
  3. Stars TTE Screener V2 + Trade Drawer V2 (new Selenium flow).
  4. Saves layouts "Screener" and "Snapshot".
  5. Registers the profile path with the TTE compose stack (writes `.env.tte-N`).

### WS-4 — Session-disconnect recovery (multi-device aware)
- **Current state**: PR #39 (`is_chart_layout_loaded` + `ensure_chart_layout_loaded`) handles chart-gone-from-page case. The maintenance loop calls it pre-emptively (`tte/main.py` ~line 412).
- **Gaps**:
  - No detection of "your session was signed out elsewhere" modal as a distinct state — just falls through to chart-not-found.
  - No backup-code consumer (file → submit → mark consumed, with refill prompt).
  - No metric/alert if recovery loops without converging. 2026-05-08 → 2026-05-14 blackout would have been caught earlier with a recovery-failure counter.
- **Build needed**:
  - Login-state probe richer than chart-presence: URL contains `/chart`, absence of `/signin`, session-disconnected modal selector if known.
  - Backup-code fallback inside `_maybe_auto_submit_totp` (or sibling function) when TOTP secret is unset/rejected.
  - Maintenance-loop counter: if `ensure_chart_layout_loaded()` runs > N times in M minutes without converging, log loudly + emit a cc-trigger alert (existing infra).

## 5. Recommended TTE-side starting point

**WS-2 first** because:
- Almost entirely env/config — low risk to production `tte-1`.
- Unblocks parallel work: once `tte-2` can boot empty, WS-3 (onboarding) has a target and WS-1 (scraper) has a consumer.
- Surfaces the SB-side API contract (instance filter on snapshots, instance param on webhook) early, which is where the SB-Claude worker pairs.

**WS-1 (scraper)** can run in parallel with WS-2 since it doesn't touch the live container.

**WS-3 / WS-4** share heavy code in `tte/browser/tradingview.py` — sequence WS-3 first (greenfield), WS-4 as refinement once a second account exists to test multi-device disconnect against.

## 6. Open questions for Sammy

Do NOT block on these — capture for the next sync window:

1. Mongo currently has **677** symbols (verified via aggregation 2026-05-15). The target is "4000". Confirm the split: ~3300 new symbols across US + IN, ~700 capacity reserved for currencies/crypto/indices growth?
2. Should `tte-2`'s ~2000 symbols be a disjoint partition of `tte-1`'s set (no overlap, double-coverage), or a shared subset (some overlap for redundancy)?
3. For Rahul's account: does Sammy already have credentials, or is onboarding-script-first?
4. TTE screener scraper: PyPI `tradingview-screener` package OK to add as a dependency, or build from scratch?

## 7. Things NOT to do

- Do **not** raise `batch_size` above 4 — TradingView hard limit (validated at `tte/config.py:96`).
- Do **not** run both instances against Sammy's TV account simultaneously — they will fight over alerts and the "restart all inactive" button is global.
- Do **not** POST to `/api/tte/combo` without an instance discriminator once `tte-2` is live — Stock Buddy can't disambiguate.
- Do **not** touch `tte/config.py` Python fallback defaults to "match" YAML — the YAML always wins; touching them buys nothing and adds churn.

## 8. Critical files (cheatsheet)

- `tte/main.py` — entry point. ~line 82 `fetch_symbols_by_category`, ~line 397 `restart_inactive_alerts`, ~line 412 `ensure_chart_layout_loaded` call, ~line 723 CLI args.
- `tte/config.py` — `PROFILE` const (18), `ComboConfig` dataclass (35-87), `validate()` (89-134).
- `tte/data/symbols.py` — Mongo loader (full file, 119 lines).
- `tte/browser/tradingview.py` — login at 327-413, TOTP at 415-557, post-login `setup_tv` at 559-649, layout guards at 269 / 292, webhook alert at ~953.
- `tte/snapshot_worker.py` — pending-snapshot poll loop (35-116).
- `tte/log.py` — `LOG_DIR` handling (20-22).
- `combo_settings.yaml` — entire file (32 lines).
- `Dockerfile` — env defaults (51-58).
- `Pine Script Code/TTE Screener V2.txt` — payload template, will need `instance` field for SB to disambiguate.

## 9. SB-side contract changes (TTE will request)

For coordination via `agent-comms.md`. The Stock Buddy Claude owns implementation; we own the call sites.

1. **`/api/tte/snapshots/pending`** must accept `?instance=<id>` and return only snapshots assigned to that instance, claimed atomically.
2. **`/api/tte/combo`** must parse `?instance=<id>` (or `instance` field in payload) and tag downstream `tte_live_signals` / `setup_messages` docs with `tteInstance`.
3. **Snapshot upload endpoint** must accept and persist `tteInstance` alongside the screenshot.
4. Existing `tte-1` continues to work without passing `instance` (treat missing as `tte-1` for back-compat during rollout).
