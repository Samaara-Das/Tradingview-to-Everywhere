# Exit Checker Architecture Spec

> **Date**: 2026-03-03
> **Status**: Implemented (Pine Script stateless: PR #13, Stock Buddy cron: PR #64)
> **Scope**: TTE Pine Script changes + Stock Buddy Vercel cron + API changes

---

## 1. Overview

### Problem

Running setups on Stock Buddy remain "running" forever even after their TP/SL was clearly hit on the chart. Root cause: Pine Script `var` state is wiped when TradingView alerts restart or get recreated, so exit detection in the screener is fundamentally unreliable.

### Solution

Decouple exit detection from TradingView entirely:

1. **Strip exit tracking from Pine Script** — screener becomes stateless, only sends signals + setup data
2. **Add a Vercel cron job** in Stock Buddy that polls price APIs every 5 minutes to detect TP/SL hits for all running setups
3. **Simplify the webhook handler** — remove exit processing, setup creation uses DB-level dedup instead of `n: true` flag

### Architecture Diagram

```
┌─────────────────────┐
│  TradingView Alerts  │
│  (Pine Script V2)    │
│                      │
│  Signals + Setups    │──── webhook every 45s ────┐
│  (stateless, no      │                           │
│   exit tracking)     │                           ▼
└─────────────────────┘              ┌──────────────────────────┐
                                     │  Stock Buddy API          │
                                     │  POST /api/tte/combo      │
                                     │                            │
                                     │  1. Upsert tte_live_signals│
                                     │  2. Create setup_messages  │
                                     │     (if not already running)│
                                     └──────────┬───────────────┘
                                                │
                                     ┌──────────▼───────────────┐
                                     │  MongoDB                   │
                                     │                            │
                                     │  tte_live_signals (live)   │
                                     │  setup_messages (tracking) │
                                     └──────────┬───────────────┘
                                                │
                                     ┌──────────▼───────────────┐
                                     │  Vercel Cron (every 5 min) │
                                     │  /api/cron/check-exits     │
                                     │                            │
                                     │  1. Fetch running setups    │
                                     │  2. Fetch OHLC candles      │
                                     │     (Binance / Yahoo)       │
                                     │  3. Scan for TP/SL hits     │
                                     │  4. Call resolveSetupExit() │
                                     └────────────────────────────┘
```

---

## 2. Pine Script Changes

### What to Remove

Strip all position state tracking and exit detection from `TTE Screener V2.txt`:

| Section | Lines (approx) | Action |
|---------|----------------|--------|
| Position state var declarations (96 vars) | 506–618 | **Delete** |
| Position clearing (`exitSent` check) | 620–656 | **Delete** |
| `isNew` reset logic | 658–674 | **Delete** |
| Setup detection | 682–748 | **Rewrite** (stateless — see below) |
| Exit detection | 754–804 | **Delete** |
| `buildPosV2()` function | 846–858 | **Rewrite** (remove exit fields) |
| `buildSymV2()` function | 877–883 | **Rewrite** (remove exit fields) |
| Position JSON build calls | 898–905 | **Rewrite** (stateless) |
| `buildSymV2()` calls | 908–909 | **Update** |
| `exitSent` flag setting | 922–937 | **Delete** |

### Stateless Setup Detection

Currently, setup detection checks `if na(pos_s1bl_entry)` before creating — this prevents re-creating a setup if one is already running. Without position state, this guard is removed.

**New behavior**: On every confirmed bar, if NWE + OB/FVG conditions align, the setup data (entry/SL/TP) is computed fresh and included in the payload. Stock Buddy handles dedup. (Staleness checks were removed in PR #11 — category-aware pairing makes them unnecessary.)

```pinescript
// STATELESS SETUP DETECTION — no var state, computed fresh each bar

// Symbol 1 — LTF Buy (1H NWE + H4/D1 OB)
string setup_s1bl = na
if nweBull01_1h and (bullF01_h4 == 1 or bullF01_d1 == 1)
    float sl = bullF01_h4 == 1 and bullF01_d1 == 1 ? math.min(bullZL01_h4, bullZL01_d1) : bullF01_h4 == 1 ? bullZL01_h4 : bullZL01_d1
    if not na(sl) and sl < close01
        float tp = close01 + 2 * (close01 - sl)
        string obTf = bullF01_h4 == 1 ? "H4" : "D1"
        setup_s1bl := buildSetupV2(close01, sl, tp, time01, "LTF", "1H", obTf)

// ... repeat for all 8 slots (s1bh, s1sl, s1sh, s2bl, s2bh, s2sl, s2sh)
```

### Updated Payload Format

**Removed fields**: `n` (isNew), `xt` (exitType), `xp` (exitPrice), `xts` (exitTimestamp)

**Position object (setup data only):**
```json
{"e": 1.98, "sl": 1.975, "tp": 1.99, "et": 1707260000, "l": "LTF", "ntf": "1H", "otf": "H4"}
```

**Full payload (unchanged structure, simplified positions):**
```json
{
  "ts": 1707264000000,
  "s": [
    {
      "sym": "GBPAUD",
      "c": 1.985,
      "nwe": [{"z": "la", "t": "bull", "tf": "1H", "ots": 1707264000}],
      "ob": [{"zt": "OB", "st": "un", "t": "bull", "zh": 1.99, "zl": 1.97, "tf": "H4", "zts": 1707260400, "ots": 1707264000}],
      "b": [{"e": 1.98, "sl": 1.975, "tp": 1.99, "et": 1707260000, "l": "LTF", "ntf": "1H", "otf": "H4"}, null],
      "se": [null, null]
    }
  ]
}
```

A non-null position in `b` or `se` means conditions currently align for that setup type. Stock Buddy compares against its own database to decide if this is a new setup or a duplicate.

---

## 3. Stock Buddy Webhook Handler Changes

### Current Flow (`POST /api/tte/combo`)

1. Validate V2 payload (Zod schema)
2. For each symbol: upsert to `tte_live_signals`
3. If position has `n: true` → `insertSetupMessage()` (creates running setup)
4. If position has `xt` → `resolveSetupExit()` (resolves setup)

### New Flow

1. Validate V2 payload (update Zod schema — remove `n`, `xt`, `xp`, `xts` fields)
2. For each symbol: upsert to `tte_live_signals`
3. For each non-null position: check if a running setup exists for `{symbol}-{direction}-{label}`
   - If no running setup → `insertSetupMessage()` (create new setup)
   - If running setup exists → skip (dedup)
4. ~~Exit processing~~ → **removed** (handled by cron)

### Setup Creation Dedup Strategy

Two approaches (recommend Option A):

**Option A — Check-first (recommended):**
```typescript
for (const pos of positions) {
  const dedupKey = `${symbol}-${direction}-${pos.l}`;
  const existing = await db.collection("setup_messages").findOne({
    dedupKey,
    outcome: "running"
  });
  if (!existing) {
    await insertSetupMessage({ symbol, direction, dedupKey, ...pos });
  }
}
```
The partial unique index on `{ symbol: 1, dedupKey: 1 }` where `outcome: "running"` makes the lookup fast. Most webhooks will hit the "already exists" path, avoiding unnecessary writes.

**Option B — Insert-and-catch:**
```typescript
try {
  await insertSetupMessage({ symbol, direction, dedupKey, ...pos });
} catch (err) {
  if (err.code === 11000) { /* duplicate — already running */ }
}
```
Simpler code but generates many failed writes (every bar for every qualifying position).

---

## 4. Exit Checker Cron

### Overview

A Vercel cron job running every 5 minutes in the Stock Buddy Next.js app. It fetches all running setups from MongoDB, gets OHLC candles from price APIs, scans for TP/SL hits, and resolves matched setups.

### API Route

**File**: `src/app/api/cron/check-exits/route.ts`

**Cron schedule**: `*/5 * * * *` (every 5 minutes)

**Vercel cron config** (in `vercel.json`):
```json
{
  "crons": [
    {
      "path": "/api/cron/check-exits",
      "schedule": "*/5 * * * *"
    }
  ]
}
```

### Algorithm

```
1. Fetch all setup_messages where outcome = "running"
2. Group setups by symbol (batch candle fetches)
3. For each unique symbol:
   a. Determine price source (Binance for crypto, Yahoo for stocks/forex)
   b. Fetch 5-min OHLC candles from entryTime → now
   c. For each setup on this symbol:
      - Walk candles chronologically from entryTime
      - For Buy: check high >= TP first, then low <= SL
      - For Sell: check low <= TP first, then high >= SL
      - On first hit: record exit type, exit price (TP or SL level), exit time (candle open_time)
4. For each resolved setup:
   - Call resolveSetupExit() with { outcome, exitPrice, outcomeTimestamp, durationMs }
   - Null out the position in tte_live_signals to keep collections in sync:
     e.g., Buy LTF resolved → set buy[0] to null in the symbol's tte_live_signals doc
5. Log summary: "Checked N setups, resolved M (X tp_hit, Y sl_hit)"
```

### Same-Candle Ambiguity

When both TP and SL are hit within the same 5-minute candle, **check TP first** (matches Pine Script screener behavior). This means:

- Buy: if `high >= TP` → TP hit, even if `low <= SL` on the same candle
- Sell: if `low <= TP` → TP hit, even if `high >= SL` on the same candle

### Timeout Protection

Vercel Pro has a 60-second function timeout. To stay within limits:

- Group setups by symbol to avoid redundant candle fetches
- Use `Promise.all()` with concurrency limit (e.g., 10 parallel fetches)
- If the function approaches 50s, stop processing and log remaining setups for next cycle
- Track last-checked timestamp per setup to avoid re-scanning old candles

### Cron Security

Vercel crons are triggered by Vercel's scheduler. To prevent unauthorized calls:

```typescript
export async function GET(request: Request) {
  // Verify the request is from Vercel Cron
  const authHeader = request.headers.get("authorization");
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return new Response("Unauthorized", { status: 401 });
  }
  // ... run exit checker
}
```

---

## 5. Symbol Mapping (TradingView → Price API)

### Category-Based Mapping

The MongoDB `symbols` collection (database `tte`) stores each symbol with a `category` field. Use this to determine the price source and transform the symbol name.

**Pre-processing**: Strip exchange prefix if present in the `symbol` field (e.g., `NSE:HAL` → `HAL`).

| Category | Price Source | Symbol Transform | Example |
|----------|-------------|-----------------|---------|
| Crypto | Binance REST API | Direct (already Binance format) | `BTCUSDT` → `BTCUSDT` |
| US Stocks | Yahoo Finance | Replace `.` and `/` with `-` | `BRK.A` → `BRK-A`, `C/PR` → `C-PR` |
| Indian Stocks | Yahoo Finance | Replace `_` with `-`, append `.NS` | `BAJAJ_AUTO` → `BAJAJ-AUTO.NS` |
| Currencies | Yahoo Finance | Append `=X` | `EURUSD` → `EURUSD=X` |

**Special cases — Commodities**: `XAUUSD` and `XAGUSD` are in the Currencies category but Yahoo lists them as futures, not forex. Map explicitly: `XAUUSD` → `GC=F`, `XAGUSD` → `SI=F`.

> **Validated**: All 620 symbols confirmed to have market data (4 delisted Indian stocks + 2 delisted EOS pairs removed). See `scripts/validate_symbols.py`.

### Symbol-to-Category Lookup

On cron startup, fetch the category for each symbol from the `symbols` collection:

```typescript
const symbolCategories = await db.collection("symbols")
  .find({}, { projection: { symbol: 1, category: 1 } })
  .toArray();

const categoryMap = new Map(symbolCategories.map(s => [s.symbol, s.category]));
```

Cache this for the duration of the cron execution (it doesn't change between runs).

### Binance API (Crypto)

```
GET https://api.binance.com/api/v3/klines
  ?symbol=BTCUSDT
  &interval=5m
  &startTime=1707260000000  (entryTime in ms)
  &endTime=1707350000000    (now in ms)
  &limit=1000
```

Returns array of arrays: `[openTime, open, high, low, close, ...]`

**Rate limit**: 1200 requests/minute (per IP). Well within limits for ~100 symbols.

**Pagination**: Max 1000 candles per request (1000 × 5min = ~3.5 days). For older setups, make multiple requests with sliding `startTime`.

### Yahoo Finance (Stocks / Forex / Commodities)

Use the `yahoo-finance2` npm package or direct REST:

```typescript
import yahooFinance from "yahoo-finance2";

const candles = await yahooFinance.chart("AAPL", {
  period1: entryTimeSec,   // Unix seconds
  period2: nowSec,
  interval: "5m"
});
```

**Data limits**: 5-minute candles go back ~60 days. No pagination needed — one request per symbol covers the full history of any running setup.

**Rate limit**: Unofficial API, no guaranteed limits. Use conservative concurrency (max 5 parallel requests).

**Fallback**: If Yahoo fails for a symbol, skip it and retry next cycle. Log the failure.

### Edge Case: Symbol Not Found

If a symbol doesn't exist on the price API (e.g., delisted stock, unusual forex pair):
1. Log a warning
2. Skip the symbol
3. After 3 consecutive failures for the same symbol across cron cycles, mark it as `"expired"` with a note

---

## 6. Database Schema

### `setup_messages` Collection (Existing — Minor Changes)

**Existing fields** (no changes):
| Field | Type | Description |
|-------|------|-------------|
| `_id` | ObjectId | Auto-generated |
| `symbol` | string | e.g., `"GBPAUD"` |
| `dedupKey` | string | `"{symbol}-{direction}-{label}"` e.g., `"GBPAUD-Buy-LTF"` |
| `direction` | string | `"Buy"` or `"Sell"` |
| `label` | string | `"LTF"` or `"HTF"` |
| `entryPrice` | number | Close price at setup detection |
| `stopLoss` | number | OB zone low (buy) or zone high (sell) |
| `takeProfit` | number | Entry ± 2 × |entry - SL| |
| `nweTf` | string | NWE timeframe: `"1H"` or `"H4"` |
| `obTf` | string | OB timeframe: `"H4"` or `"D1"` |
| `entryTime` | number | Unix ms — Pine Script `time` of the setup bar |
| `timestamp` | Date | When the webhook was received |
| `alertTimestamp` | number | `ts` field from the webhook payload |
| `outcome` | string | `"running"` \| `"tp_hit"` \| `"sl_hit"` |
| `outcomeTimestamp` | Date | When the outcome was resolved |
| `exitPrice` | number | TP or SL price that was hit |
| `durationMs` | number | `outcomeTimestamp - entryTime` |
| `signalSnapshot` | object | NWE + OB signals at setup time |
| `snapshotStatus` | string | Chart snapshot status |
| `snapshotUrl` | string | Chart snapshot image URL |

**New field**:
| Field | Type | Description |
|-------|------|-------------|
| `exitSource` | string | `"cron"` \| `"webhook"` — tracks how the exit was detected |

**Partial unique index** (existing, no change):
```
{ symbol: 1, dedupKey: 1 } where { outcome: "running" }
```

### `tte_live_signals` Collection (No Schema Changes)

Continues to store live signal + position state per symbol, upserted every 45s. The position objects in `buy`/`sell` arrays will no longer have `n`, `xt`, `xp`, `xts` fields (since the screener no longer sends them).

---

## 7. API Endpoints

### Existing (Modified)

**`POST /api/tte/combo`** — Webhook handler
- Update Zod schema: remove `n`, `xt`, `xp`, `xts` from position validation
- Remove `resolveSetupExit()` call from webhook processing
- Add check-first dedup logic for setup creation (replace `n: true` check)

### Existing (No Change)

**`GET /api/tte/combo/signals`** — Query live signals
**`GET /api/tte/snapshots/pending`** — Snapshot polling
**`POST /api/tte/snapshots/update`** — Snapshot result reporting

### New

**`GET /api/cron/check-exits`** — Vercel cron endpoint (exit checker)
- Protected by `CRON_SECRET` header
- Returns JSON summary: `{ checked, resolved, errors }`

---

## 8. Deployment Plan

### Phase 1: Database Reset

1. **Wipe collections**: Delete all documents from `setup_messages`, `tte_live_signals`, and any related collections (user messages, signals)
2. **Verify indexes**: Ensure the partial unique index on `setup_messages` still exists after wipe
### Phase 2: Stock Buddy Changes

1. **Update webhook handler** (`POST /api/tte/combo`):
   - Update Zod schema (remove exit fields from position, remove `n` field)
   - Replace `n: true` setup creation with check-first dedup
   - Remove `resolveSetupExit()` call from webhook processing
2. **Build exit checker cron** (`/api/cron/check-exits`):
   - Symbol category lookup
   - Binance candle fetcher
   - Yahoo Finance candle fetcher
   - TP/SL scanning logic
   - Cron security
3. **Add `CRON_SECRET` env var** in Vercel dashboard
4. **Configure cron** in `vercel.json`
5. **Deploy Stock Buddy** to Vercel

### Phase 3: Pine Script Changes

1. **Strip exit tracking** from `TTE Screener V2.txt`:
   - Delete position state vars, clearing, exit detection, exitSent flags
   - Rewrite setup detection to be stateless
   - Update `buildPosV2()` and `buildSymV2()` (remove exit/stale params)
   - Remove `n` field from position JSON
2. **Upload updated indicator** to TradingView (paste into Pine Editor, save)
3. **Recreate all alerts**: `python combo_main.py --fresh`

### Phase 4: Verification

1. Confirm webhooks arrive with new payload format (no exit fields)
2. Confirm `setup_messages` docs are created with `outcome: "running"`
3. Wait for cron to run → confirm exits are detected and setups resolved
4. Spot-check: manually verify a resolved setup against the TradingView chart
5. Monitor for 24 hours — check for: missed exits, false exits

---

## 9. Edge Cases

| Scenario | Handling |
|----------|----------|
| **Price API down** | Skip affected symbols, retry next cycle. Log warning. |
| **Symbol not found on API** | Skip, log. Retry next cycle. |
| **Multiple setups for same symbol** | Fetch candles once, check all setups against same data. |
| **Setup has no `entryTime`** | Fall back to `alertTimestamp` or `timestamp` field. |
| **Candle API returns >1000 results** | Paginate (Binance limit). Yahoo handles internally. |
| **Both TP and SL hit in same candle** | Check TP first (matches screener behavior). |
| **Cron timeout approaching (50s)** | Stop processing, log remaining. Next cycle picks up. |
| **Alert restarts mid-session** | Screener re-detects setup conditions. Stock Buddy dedup prevents duplicate. No data loss. |
| **`--fresh` recreates all alerts** | Same as alert restart — stateless screener, DB-level dedup. |
| **Setup conditions flicker** (align → disappear → re-align) | First detection creates the setup. Re-alignment is ignored by dedup (setup still running). |
| **Stock market closed** | Category-aware pairing ensures both symbols share market hours. Cron continues checking — no new candles means no exit detected. |

---

## 10. Resolved Questions

1. **Yahoo Finance reliability**: Not addressing now. Start with Yahoo/Binance, revisit if Yahoo breaks.
2. **Notification on exit resolution**: No — Stock Buddy UI showing "TP Hit" on next page load is sufficient.
3. **`tte_live_signals` position cleanup**: **Yes** — the cron nulls out the resolved position in `tte_live_signals` when it resolves a setup, keeping both collections consistent.
