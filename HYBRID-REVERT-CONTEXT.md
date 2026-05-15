# Hybrid-Revert Context — TTE (TradingView to Everywhere)

**Last updated:** 2026-05-04
**Status:** TTE STAYS on the Hostinger VPS through the hybrid revert. Only Stock Buddy + Mongo move back to Vercel + Atlas. TTE's Linux/Docker port (PR #25) is ready but the container is currently STOPPED due to a pre-existing screener bug.

---

## Why TTE stays on the VPS

TTE needs a long-running headless Chrome with a persisted user-data-dir, behaviour Vercel's serverless model fundamentally cannot host. Sammy's desktop also can't run 7 simultaneous TV-Ultimate-account browsers. So the VPS earns its keep — it's the one place TTE belongs.

When Stock Buddy + Mongo migrate back to Vercel + Atlas:
- TTE container `tte-1` stays put on VPS `168.231.103.163`
- TTE's `MONGODB_URI` env var swaps from `mongodb://mongo:27017/...` (VPS-internal) → Atlas SRV string (same one Stock Buddy uses)
- TTE's `COMBO_WEBHOOK_URL` env var stays as `https://stockbuddy.co/api/tte/combo` — DNS swap is transparent to TTE
- TTE's `STOCK_BUDDY_API_URL` env var stays as `https://stockbuddy.co/api/tte`

---

## Current state

### Repository

- Active repo: `C:\Users\dassa\Work\For Poolsifi\tradingview to everywhere`
- Migration artifacts mirror: `C:\Users\dassa\Work\vps-phase1\tte\` (Dockerfile, .dockerignore, inject_tv_cookies.py, debug_tv_overlay.py — same content as repo)
- Active branch: **`chore/linux-docker-support`** — PR #25 OPEN, NOT MERGED to `main`
- Latest commit: `20f1630` (2026-04-30) — "chore: Linux/Docker support + cookie-injection bootstrap"

### Linux/Docker port summary (PR #25)

Four surgical patches make TTE platform-portable:

1. **`tte/browser/tradingview.py:150-178`** — Windows Chrome cleanup (PowerShell `Get-CimInstance` + `taskkill`) wrapped in `if browser_id == 0 and platform.system() == "Windows":`. Linux skips entirely (fresh user-data-dir per container).
2. **`tte/log.py:18-22`** — Log directory honours `LOG_DIR` env var, default `"logs"`. Docker sets `LOG_DIR=/app/logs` (volume-bound).
3. **`tte/config.py:15-18`** — `PROFILE = os.getenv("CHROME_PROFILE", "Profile 4")`. Windows keeps `Profile 4`; Docker compose can override (e.g. `Default`).
4. **`tte/browser/chart.py:126-133`** — `change_symbol()` uses `driver.execute_script("arguments[0].click();", symbol_search)` to bypass TV's transient overlay (`container-VeoIyDt4`) that intercepts native clicks on fresh container Chrome.

Chrome user-data-dir construction at `tte/browser/tradingview.py:42, 187-190`:
```
CHROME_PROFILES_PATH = getenv("CHROME_PROFILES_PATH")
user_data_dir = f"{CHROME_PROFILES_PATH}/TTE{user_data_suffix}"
```
- Windows: `C:\Users\dassa\AppData\Local\Google\Chrome\User Data\TTE`
- Docker: `/home/tte/chrome-profile/TTE` (this is why cookies must live at `…/TTE/Default/Cookies`, **not** `…/Default/Cookies`)

### Container artifacts

#### `Dockerfile` (TTE repo root, identical to `vps-phase1/tte/Dockerfile`)

- Base: `python:3.11-slim-bookworm`
- Chrome: `apt-get install -y google-chrome-stable`
- ChromeDriver: fetched at build via `chrome-for-testing` LATEST_RELEASE API for matching major version
- User: `useradd -m -u 1000 tte`
- Volumes: `/home/tte/chrome-profile`, `/app/logs`
- Env defaults set in image:
  - `CHROME_USER_DATA_DIR=/home/tte/chrome-profile`
  - `CHROME_BIN=/usr/bin/google-chrome`
  - `CHROMEDRIVER_PATH=/usr/local/bin/chromedriver`
  - `CHROME_PROFILES_PATH=/home/tte/chrome-profile`
  - `LOG_DIR=/app/logs`
  - `PYTHONUNBUFFERED=1`
- Entrypoint: `CMD ["python", "-m", "tte.main"]`

#### `inject_tv_cookies.py` (`vps-phase1/tte/inject_tv_cookies.py`)

Bootstrap script (run once per container) that injects `sessionid` + `sessionid_sign` cookies into the per-instance Chrome user-data-dir. Required because TradingView's Cloudflare blocks Selenium form-fill from a fresh container Chrome.

Usage:
```
docker compose run --rm \
  -e TV_SESSION_ID=... \
  -e TV_SESSION_ID_SIGN=... \
  --entrypoint python tte-1 inject_tv_cookies.py
```

#### `debug_tv_overlay.py` (`vps-phase1/tte/debug_tv_overlay.py`)

Read-only diagnostic that screenshots `/app/logs/tv_chart.png` and dumps `/app/logs/tv_chart.html`, then inspects `[class*="container-"]` overlays and `[role="dialog"]` modals. Useful when debugging the screener bug.

#### `docker-compose.yml` (`vps-phase1/docker-compose.yml`, lines 46-65)

```yaml
tte-1:
  build: { context: ./tte, dockerfile: Dockerfile }
  image: tte:phase4
  container_name: tte-1
  restart: unless-stopped
  depends_on: { stockbuddy: {condition: service_healthy}, mongo: {condition: service_healthy} }
  networks: [internal]
  env_file: /opt/stockbuddy/secrets/.env.tte.1
  environment: [TTE_INSTANCE_ID=1]
  volumes:
    - tte1-userdata:/home/tte/chrome-profile
    - /opt/stockbuddy/logs/tte-1:/app/logs
  shm_size: 2gb
```

**Post-revert change required:** `depends_on` references must drop because `mongo` and `stockbuddy` containers will be removed. TTE will reach Atlas + Stock Buddy directly over the internet.

### MongoDB connection

Located at `tte/data/symbols.py:31-44`:
```
mongo_uri = os.getenv("MONGODB_URI")
if not mongo_uri:
    raise ValueError("MONGODB_URI environment variable is required. ...")
_mongodb_client = MongoClient(mongo_uri)
db_name = os.getenv("MONGODB_DATABASE", "tte")
```

Collections accessed: `symbols` (read), and various write paths through Stock Buddy's REST API (preferred) for `setup_messages`, `tte_webhook_log`, etc.

**Post-revert:** point `MONGODB_URI` at the Atlas cluster Stock Buddy is using. Same SRV string. `MONGODB_DATABASE` stays at `tte` or whatever the consolidated app DB name becomes.

### Webhook URLs

`tte/config.py`:
- Line 55: `webhook_url = os.getenv("COMBO_WEBHOOK_URL", _yaml.get("webhook", {}).get("url", ""))`
- Line 64-66: `api_base_url = os.getenv("STOCK_BUDDY_API_URL", "https://stock-buddy-app.vercel.app/api/tte")`

Current `.env`:
```
COMBO_WEBHOOK_URL=https://stockbuddy.co/api/tte/combo
STOCK_BUDDY_API_URL=https://stockbuddy.co/api/tte
```

**Post-revert:** unchanged. DNS swap routes the same hostnames to Vercel.

### Env var inventory (TTE-only)

| Var | Default | Source | Notes |
|---|---|---|---|
| `CHROME_PROFILES_PATH` | (required) | `.env` line 33 | Docker: `/home/tte/chrome-profile` |
| `CHROME_PROFILE` | `"Profile 4"` | `config.py:18` | Docker can override to `"Default"` |
| `CHROME_USER_DATA_DIR` | (Docker only) | Dockerfile env | `/home/tte/chrome-profile` |
| `CHROMEDRIVER_PATH` | auto-discovered | `tradingview.py:77` | Docker: `/usr/local/bin/chromedriver` |
| `LOG_DIR` | `"logs"` | `log.py:20` | Docker: `/app/logs` |
| `TRADINGVIEW_EMAIL` | (required) | `.env` line 35 | Currently `dassamaara@gmail.com` |
| `TRADINGVIEW_PASSWORD` | (required) | `.env` line 36 | — |
| `MONGODB_URI` | (required) | `.env` line 40 | **POST-REVERT: swap to Atlas SRV string** |
| `MONGODB_DATABASE` | `"tte"` | `symbols.py:44` | — |
| `MONGODB_PWD` | (required) | `.env` line 39 | Redundant if URI has password |
| `COMBO_WEBHOOK_URL` | (required if config valid) | `.env` line 43 | `https://stockbuddy.co/api/tte/combo` — unchanged post-revert |
| `STOCK_BUDDY_API_URL` | Vercel fallback | `config.py:65` | `https://stockbuddy.co/api/tte` — unchanged post-revert |
| `API_TIMEOUT` | `"30"` | `config.py:67` | seconds |
| `PYTHONUNBUFFERED` | (Docker only) | Dockerfile | `1` |

### Selenium-patterns agent rule (CRITICAL)

`.claude/agents/selenium-patterns.md` line 12-14:

> **NEVER modify `tte/browser/tradingview.py`** — All 2,100 lines of browser automation are reusable with different parameters. If you think you need to change it, you're doing it wrong. Find the right method and parameters instead.

Any TTE bug fix must come from `chart.py`, `main.py`, calling-side configuration, or by passing different `Browser` parameters that select an alternative interaction path.

### The blocking screener bug

`tte/browser/tradingview.py` `change_settings()` function (starts at line 519, fails at line 599):

```python
WebDriverWait(screener, 15).until(...)
```

The exploration agent flagged a likely root cause: `screener` is a WebElement, not a WebDriver. Should probably be `WebDriverWait(self.driver, 15)`. **However per the selenium-patterns rule, `tradingview.py` cannot be modified.** Fix has to come from the calling side.

Symptom: timeout waiting for `button[data-qa-id="legend-settings-action"]` to be clickable, even after JS-clicking the screener legend element. Same pattern as April 8 ("Screener V2 not found / Failed to make visible / dismiss overlay"). NOT a Docker issue — hits identically on Windows.

The retry loop (lines 576-598) does native click x3 then JS click as fallback. The JS click bypasses visual interception but doesn't open the legend dropdown (probably needs hover not click, or headless Chrome auto-hides UI for screenshots).

**This is independent of the hybrid revert.** Don't touch it during the revert. Schedule a focused TTE Selenium maintenance session afterwards.

### Connection to Stock Buddy

TTE writes to Stock Buddy primarily via the REST API (preferred) and reads from the shared Mongo (legacy / direct):

- HTTP POST to `https://stockbuddy.co/api/tte/combo` — main webhook
- HTTP POST to `https://stockbuddy.co/api/tte/*` — exits, stats
- HTTP timeout: `API_TIMEOUT` env (default 30s)
- Direct Mongo read: `db.symbols` for symbol catalog (677 symbols today)

Stock Buddy reads back from Mongo (writes from `/api/tte/*` route handlers).

### Single-tenant TV credentials today

One TV Premium account: `dassamaara@gmail.com` (`.env` line 35-36). Each future TTE instance (tte-2, tte-3, …, tte-N) needs:
- A separate TV Ultimate subscription
- A separate `.env.tte.<N>` file with that account's creds + cookies
- A separate `tte-<N>` service in `docker-compose.yml`
- A separate Docker volume for its Chrome user-data-dir
- A separate cookie-injection bootstrap

Mr Rahul's TV Ultimate (when provisioned) becomes `tte-2`.

---

## What changes during the hybrid revert

| What | Action | Where |
|---|---|---|
| `MONGODB_URI` in `.env.tte.1` | Swap from VPS-internal Mongo URL → Atlas SRV string | `/opt/stockbuddy/secrets/.env.tte.1` on VPS |
| `docker-compose.yml` `depends_on` for `tte-1` | Remove `mongo` and `stockbuddy` dependencies | `/opt/stockbuddy/docker-compose.yml` |
| `internal` Docker network | Either keep (orphan) or delete after stockbuddy/mongo containers removed | compose file |
| Webhook URLs (`COMBO_WEBHOOK_URL`, `STOCK_BUDDY_API_URL`) | UNCHANGED — DNS swap routes same hostnames to Vercel | env_file |
| TV cookies in volume | UNCHANGED — re-inject only if TV expires them | `tte1-userdata` volume |

That's the full TTE-side delta: one env var swap, one compose-file edit, one container restart. The screener bug stays where it is (independent fix).

---

## Verification (post-revert, TTE-side only)

1. `docker compose up -d tte-1` brings the container up cleanly (assuming screener bug fixed by then)
2. Container logs show successful Atlas connection: "MongoDB connected" with no auth errors
3. TTE pings `https://stockbuddy.co/api/health` → 200 (route now served by Vercel)
4. TTE writes a test webhook to `https://stockbuddy.co/api/tte/combo` → 200; verify the doc lands in Atlas `tte_webhook_log`
5. TV cookies still valid (visit `/u/SamaaraDas/` — should resolve, not redirect to login)
6. Symbol catalog loads (`db.symbols` reachable on Atlas, 677+ docs)

---

## Companion files

- Stock Buddy side: `C:\Users\dassa\Work\Stock-Buddy-App\HYBRID-REVERT-CONTEXT.md`
- VPS playbook: `C:\Users\dassa\Work\VPS-MIGRATION-DOC.md` (Phase 4 sections still relevant for TTE-only ops)
- Architecture diagram (pre-revert): `C:\Users\dassa\Work\vps-architecture.html`
