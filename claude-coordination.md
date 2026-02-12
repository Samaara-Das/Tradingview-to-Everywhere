# TTE ↔ Stock Buddy Coordination

Shared contract between TTE Claude and Stock Buddy Claude for the entry setup feature.

---

## Webhook Payload Format (v2)

### New fields added to Pine Script payload

**OB/FVG entry** — two new fields: `zoneHigh`, `zoneLow`
```json
{
  "zonetype": "OB",
  "subtype": "unmitigated",
  "type": "bullish",
  "zoneTimestamp": 1707753600000,
  "zoneHigh": 1.9300,
  "zoneLow": 1.9200,
  "overlapTimestamp": 1707757200000,
  "timeframe": "H4"
}
```

**Symbol entry** — new field: `close`
```json
{
  "symbol": "GBPAUD",
  "close": 1.9234,
  "nwe": [...],
  "ob_fvg": [...],
  "divergence": [...]
}
```

### Full payload example
```json
{
  "timestamp": 1707757200000,
  "signals": [
    {
      "symbol": "GBPAUD",
      "close": 1.9234,
      "nwe": [
        {"zone": "lower_avg", "type": "bullish", "overlapTimestamp": 1707757200000, "timeframe": "1H"}
      ],
      "ob_fvg": [
        {"zonetype": "OB", "subtype": "unmitigated", "type": "bullish", "zoneTimestamp": 1707753600000, "zoneHigh": 1.9300, "zoneLow": 1.9200, "overlapTimestamp": 1707757200000, "timeframe": "H4"}
      ],
      "divergence": [
        {"divType": "Logic 2", "type": "bullish", "timestamp": 1707750000000, "timeframe": "1H"}
      ]
    }
  ]
}
```

### Backward compatibility
- `close` may be missing from old alerts (treat as `undefined`)
- `zoneHigh`/`zoneLow` may be missing from old OB entries (treat as `undefined`)
- Entry setup detection should return empty array if `close` is missing

---

## Entry Setup Schema

Stored in TWO places:

### 1. `tte_live_signals` (overwritten each webhook — for grid display)
```typescript
{
  close?: number,
  setups: EntrySetup[]  // 0-2 items
}
```

### 2. `tte_entry_setups` (append-only — NEVER overwritten)
```typescript
{
  symbol: string,
  label: "LTF" | "HTF",
  direction: "Buy" | "Sell",
  entryPrice: number,       // close from payload
  stopLoss: number,          // zone boundary (widest across confirming OBs)
  takeProfit: number,        // 1:2 RR
  nweTf: string,             // "1H" or "H4"
  obTf: string,              // confirming OB timeframe
  obZonetype: string,        // "OB" or "FVG"
  obSubtype: string,         // "unmitigated", "breaker_support", etc.
  detected_at: Date,
  alert_timestamp: number
}
```

### Entry Setup Detection Rules
- **LTF**: NWE on 1H + OB/FVG on H4 or D1 (same direction)
- **HTF**: NWE on H4 + OB/FVG on D1 (same direction)
- Stop Loss: widest OB zone boundary (Buy = min(zoneLow), Sell = max(zoneHigh))
- Take Profit: 1:2 risk-reward
  - Buy: `entry + 2 * (entry - SL)`
  - Sell: `entry - 2 * (SL - entry)`

---

## Grid Timeframe Columns (Fixed)

| Signal Type | Timeframes | Columns |
|-------------|-----------|---------|
| NWE | 1H, H4 | 2 |
| OB/FVG | 1H, H4, D1 | 3 |
| Divergence | 1H, H4 | 2 |
| **Total signal cols** | | **7** |

Plus: Symbol (1) + Entry (1) + Entry Price (1) + Stop Loss (1) + Take Profit (1) + Last Updated (1) = **13 total columns**

---

## Task Status

### TTE Claude (Pine Script)
- [x] Task 1A: `buildObEntry()` — added `zoneHigh`/`zoneLow` params and JSON output
- [x] Task 1B: `buildObArray()` — added 12 float params for zone prices
- [x] Task 1C: Updated all 4 `buildObArray()` call sites with zone price variables
- [x] Task 1D: Added 3 `request.security()` calls for close price (s01-s03)
- [x] Task 1E: `buildSymbolJson()` — added `closePrice` param and JSON output
- [ ] Task 6: Alert recreation (waiting for user to save Pine Script in TradingView)

### Stock Buddy Claude
- [x] Task A: Schema updates (zoneHigh, zoneLow, close, EntrySetup, EntrySetupRecord)
- [x] Task B: Entry setup logic (computeEntrySetups) — new file src/lib/tte/entry-setup.ts
- [x] Task C: Database layer (upsert + insert + aggregation) — tte_entry_setups append-only collection added
- [x] Task D: Webhook handler updates — dual writes (upsert live + insert history)
- [x] Task E: Grid UI changes — NWE 1H/H4, OB 1H/H4/D1, DIV 1H/H4, + Entry/Price/SL/TP columns
- [x] Task F: Tests — 41 tests passing across 3 suites (combo-schemas + entry-setup + entry-setup-edge)

### UAT Testing (3 rounds completed 2026-02-12)
- [x] Round 1 (code-level): Found 3 bugs, all fixed:
  - Critical: SL validation — skip setups where SL is on wrong side of entry (added guards in entry-setup.ts)
  - Minor: Stale close in DB — changed `close` to `close ?? null` in upsertLiveSignal
  - Minor: ESLint/Prettier formatting fixes
- [x] Round 2 (API curl): 6 endpoint tests, backward compat verified, production build passed
- [x] Round 3 (Playwright browser): Webhook API, grid columns verified (13 cols), no horizontal scroll at 1366px, 0 console errors, entry setup rendering confirmed (AAPL: Buy 232.50, SL 230.00, TP 237.50)

### Status: ALL STOCK BUDDY TASKS COMPLETE — awaiting commit + TTE alert recreation (Task 6)
