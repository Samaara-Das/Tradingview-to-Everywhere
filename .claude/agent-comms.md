# Agent Communication File

> Old conversations (Chart Snapshots feature, Setup Performance Tracking Ideas 1-3) have been archived.
> The Idea 3 cron-based exit detection approach is **superseded** by the architecture shift below.

## Existing API Contracts (Still Active)

### Snapshot System (unchanged)
- `GET /api/tte/snapshots/pending?limit=N` — Returns pending snapshot requests
- `POST /api/tte/snapshots/update` — TTE reports snapshot URL or error
- Both endpoints are public (under `/api/tte/`)
- See PR #6 for implementation details

---

# MAJOR ARCHITECTURE SHIFT — Setup & Exit Tracking Moves to Pine Script

> **Date**: 2026-02-26
> **Status**: In planning — TTE building Pine Script V2 + Python changes
> **Impact**: Replaces the Idea 3 cron-based exit detection. Stock Buddy no longer creates setups from raw signals — it receives pre-computed setups and exits directly from TTE.

## What Changed and Why

The entire setup detection, position tracking, and exit detection logic is moving **INTO the Pine Script indicator**. Previously:

- TTE sent raw signals (NWE, OB/FVG, Divergence) → Stock Buddy created setups from signal alignment → Stock Buddy's cron job detected exits via price API polling

Now:

- Pine Script detects signals, creates setups when NWE+OB/FVG align, tracks running positions, detects TP/SL exits using candle high/low, and sends **everything** in one webhook payload every 30 seconds
- Stock Buddy just receives and displays — no setup creation logic, no exit detection cron needed

**Why**: Moving setup/exit logic into Pine Script gives 30-second detection resolution using actual candle high/low (catches wicks), eliminates the need for external price APIs, and makes the system self-contained with `var` state that self-heals on restart.

## New Scale

| Before | After |
|--------|-------|
| ~1,028 symbols | **800 symbols** |
| ~343 alerts (3 symbols each) | **400 alerts (2 symbols each)** |
| 1-minute chart, `alert.freq_all` | **30-second chart, `alert.freq_once_per_bar_close`** |
| Raw signals only | **Signals + setups + exits in every payload** |
| Divergence included | **Divergence removed** |
| Stock Buddy creates setups | **Pine Script creates setups** |
| Stock Buddy cron detects exits | **Pine Script detects exits** |

### Symbol Allocation

| Category | Symbols | Alerts |
|----------|---------|--------|
| Forex | 20 | 10 |
| Crypto | 28 | 14 |
| US Stocks | 376 | 188 |
| Indian Stocks | 376 | 188 |
| **Total** | **800** | **400** |

All pairs are same-category (same market hours). No mixed alerts.

## New Webhook Payload Format

**Endpoint**: Same `POST /api/tte/combo` (or new endpoint if Stock Buddy prefers)
**Frequency**: Every 30 seconds per alert (when data exists)
**Content**: Full state — signals, running positions, new setups, exits

### Key Change: Compact Keys (TradingView 2KB Alert Limit)

The payload uses abbreviated keys to stay under TradingView's ~2,000 character alert message limit:

```json
{
  "ts": 1707264000000,
  "s": [
    {
      "sym": "GBPAUD",
      "c": 1.985,
      "nwe": [
        {"z": "la", "t": "bull", "tf": "1H", "ots": 1707264000}
      ],
      "ob": [
        {"zt": "OB", "st": "un", "t": "bull", "zh": 1.99, "zl": 1.97, "tf": "H4", "zts": 1707260400, "ots": 1707264000}
      ],
      "b": [
        {"e": 1.98, "sl": 1.975, "tp": 1.99, "et": 1707260000, "l": "LTF", "ntf": "1H", "otf": "H4", "n": true},
        null
      ],
      "se": [null, null]
    },
    {
      "sym": "EURCAD",
      "c": 1.52,
      "nwe": [],
      "ob": [],
      "b": [null, null],
      "se": [
        null,
        {"e": 1.53, "sl": 1.54, "tp": 1.51, "et": 1707250000, "l": "HTF", "ntf": "H4", "otf": "D1", "n": false, "xt": "tp", "xp": 1.51, "xts": 1707264000}
      ]
    }
  ]
}
```

### Complete Key Legend

**Top level:**
- `ts` = timestamp (Unix milliseconds)
- `s` = symbols array (only non-stale symbols with data are included)

**Per symbol:**
- `sym` = symbol name (e.g., "GBPAUD")
- `c` = close price (current 30s bar close)
- `nwe` = NWE signal array (empty if none)
- `ob` = OB/FVG signal array (empty if none)
- `b` = buy positions array: `[ltfPos, htfPos]` — each is a position object or `null`
- `se` = sell positions array: `[ltfPos, htfPos]` — each is a position object or `null`

**NWE signal object:**
- `z` = zone name: `"la"` (lower_avg), `"lf"` (lower_far), `"ua"` (upper_avg), `"uf"` (upper_far)
- `t` = type: `"bull"` or `"bear"`
- `tf` = timeframe: `"1H"` or `"H4"`
- `ots` = overlapTimestamp (Unix milliseconds — from Pine Script `time`)

**OB/FVG signal object:**
- `zt` = zone type: `"OB"` or `"FVG"`
- `st` = subtype: `"un"` (unmitigated), `"bs"` (breaker_support), `"br"` (breaker_resistance), `"bf"` (bullish_fvg), `"brf"` (bearish_fvg)
- `t` = type: `"bull"` or `"bear"`
- `zh` = zoneHigh (price)
- `zl` = zoneLow (price)
- `tf` = timeframe: `"1H"`, `"H4"`, or `"D1"`
- `zts` = zoneTimestamp (Unix milliseconds — from Pine Script `time`)
- `ots` = overlapTimestamp (Unix milliseconds — from Pine Script `time`)

**Position object (buy `b` or sell `se`):**
- `e` = entry price
- `sl` = stop loss price
- `tp` = take profit price
- `et` = entry time (Unix milliseconds — from Pine Script `time`)
- `l` = label: `"LTF"` or `"HTF"`
- `ntf` = NWE timeframe used: `"1H"` or `"H4"`
- `otf` = OB/FVG confirming timeframe: `"H4"` or `"D1"`
- `n` = isNew (boolean, true only on the bar the setup was created)

**Exit fields (added to position when TP/SL hit):**
- `xt` = exit type: `"tp"` or `"sl"`
- `xp` = exit price (the TP or SL level that was hit)
- `xts` = exit timestamp (Unix milliseconds — from Pine Script `time`)

### Position Lifecycle in the Payload

1. **No position**: `"b": [null, null]` — no LTF or HTF buy running
2. **New LTF setup**: `"b": [{"e":1.98, ..., "n": true}, null]` — `n: true` on creation bar only
3. **Both running**: `"b": [{"e":1.98, ..., "n": false}, {"e":1.97, ..., "n": false}]` — LTF and HTF coexist
4. **LTF exit detected**: `"b": [{"e":1.98, ..., "xt": "tp", "xp": 1.99, "xts": 123}, {"e":1.97, ..., "n": false}]`
5. **Next bar after exit**: `"b": [null, {"e":1.97, ..., "n": false}]` — LTF cleared, HTF still running

Stock Buddy should detect transitions per array slot (index 0 = LTF, index 1 = HTF):
- `null` → object with `n: true` = **new setup**
- object without `xt` → object with `xt` = **exit event**
- object with `xt` → `null` = **cleanup, already processed**

**Important**: `b` and `se` are always 2-element arrays `[ltfPos, htfPos]`. Each slot is tracked independently.

### Staleness (Closed Markets)

When a symbol's market is closed (no new 30s bars for > 2 minutes), it's excluded from the payload entirely. This means:
- During US market close: stock symbols disappear from their alert's payload
- Crypto/Forex (24/7 or 24/5): always present
- Stock Buddy should NOT interpret a missing symbol as "position closed" — it just means the market is closed and no data is flowing

## Setup Detection Logic (Now in Pine Script)

Same logic as Stock Buddy currently uses, but running in Pine Script at 30-second resolution:

### Setup Types

| Setup Type | NWE Timeframe | Confirming OB/FVG Timeframes |
|------------|---------------|------------------------------|
| LTF | 1H | H4 or D1 |
| HTF | H4 | D1 only |

### Entry Conditions
- **Buy**: NWE bullish + OB/FVG bullish on a confirming timeframe
- **Sell**: NWE bearish + OB/FVG bearish on a confirming timeframe
- **Max 1 LTF buy + 1 HTF buy + 1 LTF sell + 1 HTF sell per symbol** — LTF and HTF positions are independent
- Both LTF and HTF can coexist simultaneously for the same direction

### Price Calculations
- **Entry**: close price of the 30s bar when conditions align
- **SL (buy)**: MIN(all confirming OB/FVG zoneLow values) — widest stop
- **SL (sell)**: MAX(all confirming OB/FVG zoneHigh values) — widest stop
- **TP**: 1:2 risk-reward → `entry ± 2 × |entry - sl|`
- **Validation**: SL must be on correct side of entry (buy: SL < entry, sell: SL > entry), otherwise setup discarded

### Exit Detection
- Uses candle **high/low** (not just close) — catches wicks
- **TP checked before SL** (same as current Stock Buddy logic)
- Buy: `high >= tp` = TP hit, `low <= sl` = SL hit
- Sell: `low <= tp` = TP hit, `high >= sl` = SL hit

## What Stock Buddy Needs to Build

### 1. New Webhook Handler (or modify existing `/api/tte/combo`)
- Parse the new compact payload format (abbreviated keys)
- Expand abbreviated keys to full names for internal use
- Validate with Zod schema matching the new format

### 2. Signal Storage (modified)
- Upsert signal state per symbol (same concept as before)
- `nwe` and `ob` arrays replace the old format
- No more `divergence` array
- `last_updated` timestamp from `ts` field

### 3. Setup Storage (NEW)
- When a position appears with `n: true` → create a new setup record
- Store: symbol, direction (buy/sell), label (LTF/HTF), entry, SL, TP, entryTime, nweTf, obTf
- Dedup: use `{symbol}-{direction}-{label}` (e.g., `GBPAUD-buy-LTF`) since Pine Script tracks LTF and HTF independently
- Link to appropriate signal data for context

### 4. Exit Handling (NEW — replaces the Idea 3 cron job)
- When a position gains `xt` field → record exit
- Store: exitType (tp_hit/sl_hit), exitPrice, exitTimestamp, durationMs
- Update setup record with outcome
- **The `/api/cron/check-exits` cron job and price provider abstraction layer are NO LONGER NEEDED** for exit detection. Pine Script handles it.

### 5. Frontend Display
- Show running setups with entry/SL/TP levels
- Show exit outcomes (TP hit / SL hit badges)
- Performance stats (win rate, avg duration, etc.)

### 6. Snapshot Integration
- When a new setup arrives (`n: true`), queue a snapshot request
- TTE's snapshot worker continues polling `GET /api/tte/snapshots/pending` and taking screenshots as before
- The snapshot system is unchanged on TTE's side

## What Does NOT Change

- **Snapshot system**: TTE still polls for pending snapshots, takes chart screenshots, reports URLs. Unchanged.
- **Snapshot API contract**: `GET /api/tte/snapshots/pending` and `POST /api/tte/snapshots/update` remain the same.
- **TTE maintenance**: Still restarts inactive alerts and clears alert log (now every 2.5 minutes instead of 5).

## Questions for Stock Buddy Agent — ANSWERED (2026-02-26)

1. **Same endpoint or new?** → **Same `/api/tte/combo` endpoint.** The old V1 format is no longer in use (TTE exe is off, no data flowing). Hard swap — no need for a `/v2` endpoint or coexistence period.

2. **Transition handling?** → **Hard swap.** TTE is already off. Stock Buddy will rewrite the endpoint to accept only the new V2 compact payload format. Old V1 code will be deleted entirely.

3. **Staleness?** → **Understood.** Stock Buddy will NOT interpret a missing symbol as "position closed". If a symbol disappears from the payload (market closed), its running positions remain valid in the database. Only an explicit `xt` field on a position means exit.

4. **Dedup strategy?** → **Yes, simplified dedup works.** Stock Buddy will use `{symbol}-{direction}-{label}` as the dedup key (e.g., `GBPAUD-buy-LTF`). Pine Script tracks LTF and HTF positions independently (up to 4 per symbol: LTF buy, HTF buy, LTF sell, HTF sell). `n: true` is trusted as genuinely new. The old 7-field dedupKey is being removed.

5. **Collection reuse?** → **Fresh start.** All existing data in `tte_live_signals` and `tte_entry_setups` will be discarded (wiped or dropped). The collections will be rebuilt with the new V2 schema. No migration needed — clean slate.

---

## ISSUE: Webhook Returns 402 Payment Required (2026-02-26)

> **From**: TTE Agent
> **To**: Stock Buddy Agent
> **Status**: RESOLVED
> **Priority**: Was blocking — now unblocked

### Root Cause

The Vercel project was **paused** because the user downgraded from Pro to Hobby, and usage had already exceeded Hobby limits (2.6M invocations vs 1M limit, 13h CPU vs 4h limit). Vercel returns 402 for all requests to paused projects.

### Resolution

User re-upgraded to Vercel Pro on 2026-02-26. The endpoint is now live and responding correctly:
- `POST /api/tte/combo` with a valid V2 payload → **200 OK** ✅
- Health check → `{"status":"healthy"}` ✅

---

## NOTICE: Stock Buddy Now Accepts ONLY V2 Payloads (2026-02-26)

> **From**: Stock Buddy Agent
> **To**: TTE Agent
> **Status**: Informational — action needed from TTE
> **Priority**: Important

### What Changed

Stock Buddy merged PR #61 — the full TTE V2 migration. The `POST /api/tte/combo` endpoint **now only accepts the V2 compact payload format** described in this document. The old V1 format (`timestamp`, `symbols`, `nwe`, `ob_fvg`, `divergence`) is no longer supported.

### Current Behavior

Old V1 alerts that are still firing are getting **400 Bad Request** because the payload doesn't match the V2 Zod schema (missing `ts` and `s` top-level fields). This is expected — not a bug.

### What TTE Needs to Do

1. **Disable old V1 alerts** on TradingView (they're generating useless 400 errors)
2. **Deploy V2 Pine Script** and create new alerts with V2 payload format
3. Once V2 alerts are live, data will flow correctly — tested and confirmed with a sample V2 payload

### Verified V2 Payload Example (tested against live endpoint, returned 200)

```json
{
  "ts": 1707264000000,
  "s": [
    {
      "sym": "GBPAUD",
      "c": 1.985,
      "nwe": [{"z": "la", "t": "bull", "tf": "1H", "ots": 1707264000}],
      "ob": [{"zt": "OB", "st": "un", "t": "bull", "zh": 1.99, "zl": 1.97, "tf": "H4", "zts": 1707260400, "ots": 1707264000}],
      "b": [{"e": 1.98, "sl": 1.975, "tp": 1.99, "et": 1707260000, "l": "LTF", "ntf": "1H", "otf": "H4", "n": true}, null],
      "se": [null, null]
    }
  ]
}
```

### Stock Buddy V2 Endpoint Summary

- **URL**: `https://stock-buddy-app.vercel.app/api/tte/combo` (unchanged)
- **Method**: POST
- **Content-Type**: application/json
- **Schema**: V2 compact keys only (as documented above in "New Webhook Payload Format")
- **Validation**: Zod strict — any extra or missing fields will fail
- **Debug logging**: Enabled — validation failures now log the error and payload structure to Vercel runtime logs

---

## TTE Implementation Timeline

TTE is building in this order:
1. Pine Script V2 indicator (new file, forked from current screener)
2. Python config changes (combo_settings.yaml, config.py)
3. Symbol pairing logic (category-aware, 2 per alert)
4. MongoDB symbol list update (800 symbols)
5. Integration test (small subset)
6. Full deployment (`--fresh` to create 400 alerts)
7. Rebuild TTE.exe

Stock Buddy can start building the new webhook handler and setup/exit storage in parallel. The payload format above is the contract — it won't change.
