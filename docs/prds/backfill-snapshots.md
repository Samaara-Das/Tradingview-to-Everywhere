# Snapshot Backfill — Product Requirements Document

## Document Info
- **Version**: 1.0
- **Last Updated**: 2026-02-21
- **Status**: Approved

---

## 1. Overview

### 1.1 Problem Statement
Setup messages created before the chart snapshot feature was deployed (early Feb 2026) have no `snapshotStatus` field in MongoDB. The TTE snapshot worker only polls for documents where `snapshotStatus === "pending"` — so these old setups are permanently invisible to the worker. They will never receive a chart snapshot unless explicitly queued.

### 1.2 Proposed Solution
A one-time API endpoint (`POST /api/tte/snapshots/backfill`) in Stock Buddy that:
1. Finds all setup messages from the **last 30 days** where `snapshotStatus` is missing
2. Sets them to `snapshotStatus: "pending"`, `snapshotAttempts: 0`, `snapshotUpdatedAt: now`
3. Returns a count and list of queued setup IDs

Once queued, the existing TTE snapshot worker picks them up automatically in its next 60-second polling cycle. No changes to TTE are required.

### 1.3 Out of Scope
- Backfilling setup messages older than 30 days (assumed stale/irrelevant)
- Any changes to TTE snapshot worker or its polling logic
- A UI for triggering the backfill (curl is sufficient)
- Re-triggering backfill for already-`failed` setups (handled by existing retry logic, max 3 attempts)
- Scheduling or automating future backfills

---

## 2. Functional Requirements

### FR-001: Backfill API Endpoint

- **Endpoint**: `POST /api/tte/snapshots/backfill`
- **Auth**: None (consistent with existing `/api/tte/*` endpoints)
- **Trigger**: Called once manually via curl or browser

**Query filter** (MongoDB):
```js
{
  snapshotStatus: { $exists: false },   // Only docs with NO snapshot field
  timestamp: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) }  // Last 30 days
}
```

**Update applied** (single `updateMany` — atomic):
```js
{
  $set: {
    snapshotStatus: "pending",
    snapshotAttempts: 0,
    snapshotUpdatedAt: new Date()
  }
}
```

**Success response**:
```json
{
  "success": true,
  "queued": 847,
  "setupMessageIds": ["id1", "id2", "..."]
}
```

**Error response** (e.g., DB failure):
```json
{
  "success": false,
  "error": "Database error: ..."
}
```

---

### FR-002: Idempotency

Running the endpoint more than once must be a safe no-op.

- The query filter uses `{ snapshotStatus: { $exists: false } }` — any doc that already has `snapshotStatus` (in any state: `pending`, `processing`, `completed`, `failed`) is excluded from the update
- A second call returns `{ success: true, queued: 0, setupMessageIds: [] }`
- No data is overwritten or reset

---

### FR-003: TTE Worker Handles Processing (No Changes Required)

Once backfilled docs are marked `pending`, the **existing** TTE snapshot worker handles everything:

| What | How (existing behavior) |
|------|------------------------|
| Picks up pending docs | `GET /api/tte/snapshots/pending?limit=5` every 60s |
| Logs each setup being processed | `"Taking snapshot: {symbol} {tf} ({timeframe}) — Entry {price}, SL {sl}, TP {tp}"` |
| Reports success | `POST /api/tte/snapshots/update` with PNG + TV URLs |
| Reports failure | `POST /api/tte/snapshots/update` with error message |
| Summary each batch | `"Snapshot phase complete: X/Y succeeded"` |
| Retries | Up to 3 attempts per setup (`snapshotAttempts < 3`) |
| Stale recovery | `processing` docs > 10 min old reset to `pending` automatically |

The user can monitor progress live by watching TTE's terminal output.

---

### FR-004: Failed Setups Visibility

After TTE exhausts all 3 attempts for a setup, `snapshotStatus` becomes `"failed"` permanently. In Stock Buddy's UI, that setup message displays: **"Chart snapshot unavailable"** (italic gray text — existing behavior in `SetupMessageBubble.tsx`).

No additional UI or endpoint is required to surface failures — the existing UI handles it gracefully.

---

## 3. Technical Notes

### Implementation Location
- **File**: `src/app/api/tte/snapshots/backfill/route.ts` (new file in Stock Buddy)
- **Collection function**: `backfillPendingSnapshots()` in `src/lib/tte/collections.ts`

### Performance
- Uses `updateMany()` — single DB round-trip regardless of how many docs match
- Expected scale: up to ~1,000 docs in 30 days — completes in < 1 second
- No pagination or batching needed at the DB level

### Consistency with Existing Patterns
- Same structure as `pending/route.ts` and `update/route.ts`
- Returns JSON with `success` boolean on all paths (including errors)
- No auth (consistent with other `/api/tte/*` endpoints)

---

## 4. Test Scenarios

> These are the exact steps the UAT tester must follow. Each test is self-contained and includes the exact action, what to check, and the expected result.

---

### Test 1: Backfill Queues the Right Docs

**Precondition**: There are setup messages in MongoDB from the last 30 days with no `snapshotStatus` field.

**Steps**:
1. Open MongoDB Compass or run a query: `db.setup_messages.find({ snapshotStatus: { $exists: false }, timestamp: { $gte: new Date(Date.now() - 30*24*60*60*1000) } }).count()`
2. Note the count (e.g., 847)
3. Call the endpoint: `curl -X POST https://<host>/api/tte/snapshots/backfill`
4. Verify response: `{ "success": true, "queued": 847, "setupMessageIds": [...] }`
5. Query MongoDB again: `db.setup_messages.find({ snapshotStatus: "pending" })` — confirm 847 docs now have `snapshotStatus: "pending"` and `snapshotAttempts: 0`

**Expected**: `queued` in response matches the pre-call DB count. All those docs now have `snapshotStatus: "pending"`.

---

### Test 2: TTE Worker Picks Up Backfilled Setups

**Precondition**: Backfill has been run (Test 1 passed). TTE is not currently running.

**Steps**:
1. Start TTE: `python combo_main.py --maintain-only`
2. Watch the terminal output
3. Within 60 seconds, expect log: `"Fetched N pending snapshots"` (where N is up to 5)
4. Expect logs for each setup: `"Taking snapshot: {SYMBOL} {TF} ({timeframe}) — Entry {price}, SL {sl}, TP {tp}"`
5. Expect success logs: `"Snapshot completed for {SYMBOL}: https://www.tradingview.com/x/..."`
6. Expect batch summary: `"Snapshot phase complete: X/Y succeeded"`
7. Open Stock Buddy UI → navigate to one of the processed symbols' chat → the setup message now shows a chart image (not "Loading..." or "unavailable")

**Expected**: TTE processes the backfilled setups within 2 minutes of startup. Chart images appear in Stock Buddy.

---

### Test 3: Idempotency — Second Backfill Call is a No-Op

**Precondition**: Backfill has been called once and all matching docs are now `snapshotStatus: "pending"`.

**Steps**:
1. Call the endpoint again: `curl -X POST https://<host>/api/tte/snapshots/backfill`
2. Verify response: `{ "success": true, "queued": 0, "setupMessageIds": [] }`
3. Verify in MongoDB that no documents were modified (check `snapshotUpdatedAt` — no new timestamps)

**Expected**: Zero documents touched. Response confirms `queued: 0`.

---

### Test 4: 30-Day Cutoff Is Respected

**Precondition**: There exist setup messages in MongoDB older than 30 days that also have no `snapshotStatus`.

**Steps**:
1. Query MongoDB: `db.setup_messages.find({ snapshotStatus: { $exists: false }, timestamp: { $lt: new Date(Date.now() - 30*24*60*60*1000) } }).count()` — note the count (e.g., 200)
2. Run backfill: `curl -X POST https://<host>/api/tte/snapshots/backfill`
3. Re-run the same query — count must still be the same (e.g., 200 unchanged)

**Expected**: Setup messages older than 30 days are NOT touched by the backfill.

---

### Test 5: Failure Handling — TTE Cannot Take a Snapshot

**Precondition**: At least one setup message has been backfilled to `pending`.

**Steps**:
1. Simulate a failure by temporarily breaking the Trade Drawer indicator (or observe natural failures in TTE logs)
2. TTE attempts the snapshot, logs: `"Failed to take chart snapshot"` or similar
3. TTE calls `POST /api/tte/snapshots/update` with `{ error: "..." }`
4. MongoDB: that doc now has `snapshotStatus: "failed"`, `snapshotAttempts: 1`
5. On next poll (60s later), TTE picks it up again (`attempts < 3`) and retries
6. After 3 failures: `snapshotStatus: "failed"`, `snapshotAttempts: 3`
7. Open Stock Buddy UI for that symbol → the setup message shows **"Chart snapshot unavailable"** in italic gray text
8. TTE no longer picks up that doc (attempts >= 3)

**Expected**: Failed setups are retried up to 3 times, then shown as "unavailable" in UI. TTE does not retry beyond 3 attempts.

---

### Test 6: Already-Completed Setups Are Not Reset

**Precondition**: Some setup messages already have `snapshotStatus: "completed"` (new setups created after the feature was deployed).

**Steps**:
1. Note a setup message ID that has `snapshotStatus: "completed"` and a `snapshotUrl`
2. Run backfill: `curl -X POST https://<host>/api/tte/snapshots/backfill`
3. Re-check that document in MongoDB

**Expected**: The document is unchanged — `snapshotStatus` remains `"completed"`, `snapshotUrl` is preserved.

---

## 5. How to Trigger (Runbook)

```bash
# Production
curl -X POST https://stockbuddy.co/api/tte/snapshots/backfill

# Local dev
curl -X POST http://localhost:3000/api/tte/snapshots/backfill
```

Response confirms how many setups were queued. Then start TTE (`python combo_main.py --maintain-only`) and monitor its terminal for snapshot progress.
