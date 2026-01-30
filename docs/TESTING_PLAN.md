# Testing Plan
# TTE Tiered Screener Architecture

This document defines test cases, acceptance criteria, and QA procedures.

---

## Table of Contents

1. [Testing Strategy](#1-testing-strategy)
2. [Unit Tests](#2-unit-tests)
3. [Integration Tests](#3-integration-tests)
4. [End-to-End Tests](#4-end-to-end-tests)
5. [Performance Tests](#5-performance-tests)
6. [User Acceptance Tests](#6-user-acceptance-tests)
7. [Test Data](#7-test-data)
8. [Test Environments](#8-test-environments)

---

## 1. Testing Strategy

### 1.1 Testing Pyramid

```
        /\
       /  \      E2E Tests (Few)
      /----\     - Full signal flow
     /      \    - Dashboard interactions
    /--------\
   /          \   Integration Tests (Some)
  /            \  - API endpoints
 /--------------\ - Database operations
/                \ - Webhook delivery
/------------------\
        Unit Tests (Many)
        - Pine Script functions
        - API validation
        - Helper functions
```

### 1.2 Test Coverage Goals

| Component | Target Coverage |
|-----------|-----------------|
| API Endpoints | 90% |
| Python Orchestrator | 80% |
| Dashboard Components | 70% |
| Pine Script | Manual testing |

### 1.3 Testing Tools

| Tool | Purpose |
|------|---------|
| Jest | JavaScript/TypeScript unit tests |
| pytest | Python unit tests |
| Cypress | E2E browser tests |
| Postman/curl | API testing |
| TradingView | Pine Script manual testing |

---

## 2. Unit Tests

### 2.1 API Validation Tests

#### Test: NWE Payload Validation

```typescript
// __tests__/api/nwe.test.ts

describe('POST /api/nwe', () => {
  test('accepts valid payload', async () => {
    const payload = {
      tier: 'nwe',
      symbol: 'GBPAUD',
      direction: 'bullish',
      timeframes: ['H4', 'D1'],
      timestamp: 1672531200
    };

    const response = await fetch('/api/nwe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.success).toBe(true);
  });

  test('rejects invalid tier', async () => {
    const payload = { tier: 'invalid', symbol: 'GBPAUD', direction: 'bullish' };

    const response = await fetch('/api/nwe', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    expect(response.status).toBe(400);
    const data = await response.json();
    expect(data.code).toBe('INVALID_TIER');
  });

  test('rejects missing symbol', async () => {
    const payload = { tier: 'nwe', direction: 'bullish' };

    const response = await fetch('/api/nwe', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    expect(response.status).toBe(400);
    expect((await response.json()).code).toBe('MISSING_FIELD');
  });

  test('rejects invalid direction', async () => {
    const payload = { tier: 'nwe', symbol: 'GBPAUD', direction: 'sideways' };

    const response = await fetch('/api/nwe', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    expect(response.status).toBe(400);
    expect((await response.json()).code).toBe('INVALID_DIRECTION');
  });
});
```

#### Test: Signal Level Calculation

```typescript
// __tests__/utils/signalLevel.test.ts

describe('Signal Level Calculation', () => {
  test('Level 1: NWE only', () => {
    const ob = { found: false };
    const div = { found: false };
    expect(calculateLevel(ob, div)).toBe(1);
  });

  test('Level 2: NWE + OB', () => {
    const ob = { found: true, tf: 'W1', type: 'OB' };
    const div = { found: false };
    expect(calculateLevel(ob, div)).toBe(2);
  });

  test('Level 3: NWE + OB + DIV', () => {
    const ob = { found: true, tf: 'W1', type: 'OB' };
    const div = { found: true, tf: 'H4', type: 'Logic2' };
    expect(calculateLevel(ob, div)).toBe(3);
  });

  test('Level 1: DIV without OB', () => {
    const ob = { found: false };
    const div = { found: true, tf: 'H4', type: 'Logic2' };
    expect(calculateLevel(ob, div)).toBe(1); // DIV alone doesn't count
  });
});
```

### 2.2 Python Orchestrator Tests

```python
# tests/test_orchestrator.py

import pytest
from unittest.mock import Mock, patch
from tiered_orchestrator import TieredOrchestrator, HotSymbol, Config

class TestHotSymbolParsing:
    def test_parse_valid_response(self):
        data = {
            'data': [
                {
                    'symbol': 'GBPAUD',
                    'direction': 'bullish',
                    'nwe_timeframes': ['H4', 'D1'],
                    'status': 'pending_tier2'
                }
            ]
        }

        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = data
            mock_get.return_value.raise_for_status = Mock()

            orchestrator = TieredOrchestrator(Mock())
            symbols = orchestrator.get_hot_symbols()

            assert len(symbols) == 1
            assert symbols[0].symbol == 'GBPAUD'
            assert symbols[0].direction == 'bullish'

    def test_handle_empty_response(self):
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = {'data': []}
            mock_get.return_value.raise_for_status = Mock()

            orchestrator = TieredOrchestrator(Mock())
            symbols = orchestrator.get_hot_symbols()

            assert len(symbols) == 0

    def test_handle_network_error(self):
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")

            orchestrator = TieredOrchestrator(Mock())
            symbols = orchestrator.get_hot_symbols()

            assert len(symbols) == 0  # Should return empty, not crash


class TestBatchProcessing:
    def test_batch_size_limit(self):
        symbols = [HotSymbol(f'SYM{i}', 'bullish', [], 'pending') for i in range(20)]

        batches = list(batch_symbols(symbols, Config.BATCH_SIZE))

        assert len(batches) == 3  # 20 / 8 = 2.5 -> 3 batches
        assert len(batches[0]) == 8
        assert len(batches[1]) == 8
        assert len(batches[2]) == 4
```

---

## 3. Integration Tests

### 3.1 API Integration Tests

#### Test: NWE Webhook → Hot List

```bash
#!/bin/bash
# tests/integration/test_nwe_webhook.sh

echo "Test: NWE Webhook creates hot_list entry"

# Clean up
curl -s -X DELETE "http://localhost:3000/api/test/cleanup?symbol=TESTGBP"

# Send NWE webhook
RESPONSE=$(curl -s -X POST http://localhost:3000/api/nwe \
  -H "Content-Type: application/json" \
  -d '{
    "tier": "nwe",
    "symbol": "TESTGBP",
    "direction": "bullish",
    "timeframes": ["H4", "D1"],
    "timestamp": 1672531200
  }')

echo "Response: $RESPONSE"

# Verify success
SUCCESS=$(echo $RESPONSE | jq -r '.success')
if [ "$SUCCESS" != "true" ]; then
  echo "FAIL: Expected success=true"
  exit 1
fi

# Verify hot_list entry
HOT_SYMBOLS=$(curl -s "http://localhost:3000/api/hot-symbols?symbol=TESTGBP")
COUNT=$(echo $HOT_SYMBOLS | jq -r '.count')

if [ "$COUNT" -lt 1 ]; then
  echo "FAIL: Expected hot_list entry"
  exit 1
fi

echo "PASS: NWE webhook creates hot_list entry"
```

#### Test: OBDIV Webhook → Signal Creation

```bash
#!/bin/bash
# tests/integration/test_obdiv_webhook.sh

echo "Test: OBDIV Webhook creates signal"

# First, create hot_list entry
curl -s -X POST http://localhost:3000/api/nwe \
  -H "Content-Type: application/json" \
  -d '{"tier":"nwe","symbol":"TESTEUR","direction":"bullish","timeframes":["H4"]}'

# Send OBDIV webhook
RESPONSE=$(curl -s -X POST http://localhost:3000/api/obdiv \
  -H "Content-Type: application/json" \
  -d '{
    "tier": "obdiv",
    "symbol": "TESTEUR",
    "bull_ob": {"found": true, "tf": "W1", "type": "OB"},
    "bull_div": {"found": true, "tf": "H4", "type": "Logic2"},
    "bear_ob": {"found": false},
    "bear_div": {"found": false}
  }')

echo "Response: $RESPONSE"

# Verify signal created
SIGNAL_CREATED=$(echo $RESPONSE | jq -r '.signal_created')
LEVEL=$(echo $RESPONSE | jq -r '.level')

if [ "$SIGNAL_CREATED" != "true" ]; then
  echo "FAIL: Expected signal_created=true"
  exit 1
fi

if [ "$LEVEL" != "3" ]; then
  echo "FAIL: Expected level=3, got $LEVEL"
  exit 1
fi

echo "PASS: OBDIV webhook creates Level 3 signal"
```

### 3.2 Database Integration Tests

```typescript
// __tests__/integration/database.test.ts

describe('Database Operations', () => {
  beforeEach(async () => {
    // Clean test data
    await db.collection('hot_list').deleteMany({ symbol: /^TEST/ });
    await db.collection('signals').deleteMany({ symbol: /^TEST/ });
  });

  test('hot_list upsert creates new entry', async () => {
    await db.collection('hot_list').updateOne(
      { symbol: 'TESTSYM1' },
      { $set: { symbol: 'TESTSYM1', direction: 'bullish', status: 'pending_tier2' } },
      { upsert: true }
    );

    const entry = await db.collection('hot_list').findOne({ symbol: 'TESTSYM1' });
    expect(entry).not.toBeNull();
    expect(entry.direction).toBe('bullish');
  });

  test('hot_list upsert updates existing entry', async () => {
    // Create initial
    await db.collection('hot_list').insertOne({
      symbol: 'TESTSYM2',
      direction: 'bullish',
      status: 'pending_tier2'
    });

    // Update
    await db.collection('hot_list').updateOne(
      { symbol: 'TESTSYM2' },
      { $set: { direction: 'bearish' } }
    );

    const entry = await db.collection('hot_list').findOne({ symbol: 'TESTSYM2' });
    expect(entry.direction).toBe('bearish');
  });

  test('signals query with filters', async () => {
    // Insert test signals
    await db.collection('signals').insertMany([
      { symbol: 'TESTSYM3', level: 3, direction: 'bullish', created_at: new Date() },
      { symbol: 'TESTSYM4', level: 2, direction: 'bearish', created_at: new Date() },
      { symbol: 'TESTSYM5', level: 1, direction: 'bullish', created_at: new Date() }
    ]);

    // Query Level 3 only
    const level3 = await db.collection('signals')
      .find({ level: 3, symbol: /^TEST/ })
      .toArray();

    expect(level3.length).toBe(1);
    expect(level3[0].symbol).toBe('TESTSYM3');
  });
});
```

---

## 4. End-to-End Tests

### 4.1 Full Signal Flow Test

```gherkin
Feature: Complete Signal Flow
  As a trader
  I want signals to flow from TradingView to Dashboard
  So that I can see trading opportunities

  Scenario: Level 3 Bullish Signal
    Given NWE Screener detects GBPAUD in bullish zone on H4 and D1
    When the NWE webhook is received
    Then GBPAUD should be added to hot_list with status "pending_tier2"

    Given OBDIV Screener checks GBPAUD
    And finds bullish OB on W1
    And finds bullish divergence on H4
    When the OBDIV webhook is received
    Then a Level 3 signal should be created
    And the signal direction should be "bullish"

    Given the Python orchestrator runs
    When it captures a screenshot for GBPAUD
    Then the signal status should be "complete"
    And screenshot_url should be populated

    When I open the dashboard
    Then I should see the GBPAUD Level 3 signal
    And the signal should show NWE: H4,D1, OB: W1, DIV: H4
```

### 4.2 Cypress E2E Tests

```typescript
// cypress/e2e/dashboard.cy.ts

describe('Dashboard', () => {
  beforeEach(() => {
    cy.visit('/dashboard');
  });

  it('displays signals table', () => {
    cy.get('[data-testid="signals-table"]').should('be.visible');
    cy.get('[data-testid="signal-row"]').should('have.length.at.least', 1);
  });

  it('filters by level', () => {
    cy.get('[data-testid="filter-level"]').click();
    cy.get('[data-value="3"]').click();

    cy.get('[data-testid="signal-row"]').each(($row) => {
      cy.wrap($row).find('[data-testid="level"]').should('contain', '3');
    });
  });

  it('filters by direction', () => {
    cy.get('[data-testid="filter-direction"]').click();
    cy.get('[data-value="bullish"]').click();

    cy.get('[data-testid="signal-row"]').each(($row) => {
      cy.wrap($row).find('[data-testid="direction"]').should('contain', 'BUY');
    });
  });

  it('opens screenshot modal', () => {
    cy.get('[data-testid="signal-row"]').first()
      .find('[data-testid="screenshot-button"]').click();

    cy.get('[data-testid="screenshot-modal"]').should('be.visible');
    cy.get('[data-testid="screenshot-image"]').should('be.visible');
  });

  it('sorts by time', () => {
    cy.get('[data-testid="sort-time"]').click();

    cy.get('[data-testid="signal-row"]').then(($rows) => {
      const times = $rows.map((i, el) =>
        Cypress.$(el).find('[data-testid="time"]').text()
      ).get();

      const sortedTimes = [...times].sort().reverse();
      expect(times).to.deep.equal(sortedTimes);
    });
  });
});
```

### 4.3 Manual E2E Test Checklist

```markdown
## Manual E2E Test Checklist

### Pre-requisites
- [ ] TradingView logged in
- [ ] NWE Screener added to chart
- [ ] OBDIV Screener added to chart
- [ ] Webhook alerts configured
- [ ] Stock Buddy running
- [ ] Python orchestrator running

### Test 1: NWE Signal Detection
- [ ] Wait for market hours
- [ ] Observe NWE Screener for zone entry
- [ ] Verify alert fires in TradingView
- [ ] Check hot_list via API:
  ```
  curl https://stock-buddy-app.vercel.app/api/hot-symbols
  ```
- [ ] Verify symbol appears with correct direction

### Test 2: OBDIV Confirmation
- [ ] Python orchestrator detects hot symbol
- [ ] OBDIV Screener symbols updated (check TradingView)
- [ ] Wait for OBDIV webhook
- [ ] Check signals via API:
  ```
  curl https://stock-buddy-app.vercel.app/api/signals
  ```
- [ ] Verify signal level is correct

### Test 3: Screenshot Capture
- [ ] Python orchestrator captures screenshot
- [ ] Signal status changes to "complete"
- [ ] Screenshot URL is valid
- [ ] Image loads correctly

### Test 4: Dashboard Display
- [ ] Open dashboard: https://stock-buddy-app.vercel.app/dashboard
- [ ] Signal appears in table
- [ ] All fields populated correctly
- [ ] Screenshot modal works
- [ ] Filters work
- [ ] Sorting works

### Test 5: Edge Cases
- [ ] Bearish signal flow
- [ ] Level 2 signal (OB but no DIV)
- [ ] Level 1 signal (NWE only)
- [ ] Multiple signals same symbol
- [ ] Direction change (was bullish, now bearish)
```

---

## 5. Performance Tests

### 5.1 Load Test Scenarios

```yaml
# k6 load test configuration
scenarios:
  webhook_load:
    executor: constant-arrival-rate
    rate: 10  # 10 requests per second
    duration: '5m'
    preAllocatedVUs: 20

  dashboard_load:
    executor: ramping-vus
    startVUs: 1
    stages:
      - duration: '2m', target: 50
      - duration: '5m', target: 50
      - duration: '2m', target: 0
```

### 5.2 Performance Acceptance Criteria

| Metric | Target | Maximum |
|--------|--------|---------|
| Webhook response time (p95) | < 500ms | 2s |
| Dashboard load time | < 2s | 5s |
| API /signals response (p95) | < 200ms | 1s |
| Screenshot capture | < 10s | 30s |

### 5.3 Performance Test Script

```javascript
// k6/webhook-load.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 10,
  duration: '5m',
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const payload = JSON.stringify({
    tier: 'nwe',
    symbol: `TEST${__VU}${__ITER}`,
    direction: Math.random() > 0.5 ? 'bullish' : 'bearish',
    timeframes: ['H4'],
    timestamp: Date.now(),
  });

  const res = http.post('https://stock-buddy-app.vercel.app/api/nwe', payload, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });

  sleep(1);
}
```

---

## 6. User Acceptance Tests

### 6.1 UAT Scenarios

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| UAT-01 | View today's signals | 1. Open dashboard<br>2. Check "Today" stats card | Shows count of today's signals |
| UAT-02 | Filter Level 3 only | 1. Open dashboard<br>2. Select Level: 3 | Only Level 3 signals shown |
| UAT-03 | Search symbol | 1. Open dashboard<br>2. Type "GBP" in search | Shows only GBP pairs |
| UAT-04 | View screenshot | 1. Click screenshot icon on signal<br>2. Modal opens | Chart image displayed |
| UAT-05 | Sort by level | 1. Click Level column header | Signals sorted by level |
| UAT-06 | Mobile view | 1. Open dashboard on mobile | Card layout, readable |

### 6.2 UAT Sign-off Checklist

```markdown
## UAT Sign-off

**Tester:** _______________
**Date:** _______________
**Environment:** Production / Staging

### Functionality
- [ ] NWE signals appear within 2 minutes of zone entry
- [ ] Signal levels are calculated correctly
- [ ] Screenshots are captured for all signals
- [ ] Dashboard displays all signals

### Usability
- [ ] Dashboard is intuitive to use
- [ ] Filters work as expected
- [ ] Mobile experience is acceptable
- [ ] Page load time is acceptable

### Data Quality
- [ ] Symbol names are correct
- [ ] Timeframes are accurate
- [ ] Directions match actual chart
- [ ] No duplicate signals

### Issues Found
| Issue | Severity | Notes |
|-------|----------|-------|
| | | |

### Sign-off
- [ ] All critical issues resolved
- [ ] Ready for production

Signature: _______________
```

---

## 7. Test Data

### 7.1 Test Symbols

Use symbols prefixed with `TEST` for automated tests:
- `TESTGBP` - General testing
- `TESTEUR` - Level 3 scenarios
- `TESTUSD` - Level 2 scenarios
- `TESTJPY` - Bearish scenarios

### 7.2 Sample Payloads

```json
// NWE Bullish
{
  "tier": "nwe",
  "symbol": "GBPAUD",
  "direction": "bullish",
  "timeframes": ["H4", "D1"],
  "timestamp": 1672531200
}

// NWE Bearish
{
  "tier": "nwe",
  "symbol": "EURUSD",
  "direction": "bearish",
  "timeframes": ["D1"],
  "timestamp": 1672531200
}

// OBDIV Level 3
{
  "tier": "obdiv",
  "symbol": "GBPAUD",
  "bull_ob": {"found": true, "tf": "W1", "type": "OB"},
  "bull_div": {"found": true, "tf": "H4", "type": "Logic2"},
  "bear_ob": {"found": false},
  "bear_div": {"found": false}
}

// OBDIV Level 2 (no DIV)
{
  "tier": "obdiv",
  "symbol": "GBPAUD",
  "bull_ob": {"found": true, "tf": "D1", "type": "FVG"},
  "bull_div": {"found": false},
  "bear_ob": {"found": false},
  "bear_div": {"found": false}
}
```

---

## 8. Test Environments

### 8.1 Environment Matrix

| Environment | Purpose | URL |
|-------------|---------|-----|
| Local | Development testing | http://localhost:3000 |
| Preview | PR/branch testing | https://stock-buddy-*-vercel.app |
| Staging | Pre-production testing | https://staging.stock-buddy-app.vercel.app |
| Production | Live system | https://stock-buddy-app.vercel.app |

### 8.2 Test Database

- Use separate MongoDB database for tests: `tte_test`
- Clean up test data after each test run
- Never run tests against production database

---

*This testing plan should be updated as new features are added.*
