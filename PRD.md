# Product Requirements Document (PRD)
# TTE Tiered Screener Architecture

**Version**: 1.1
**Created**: 2026-01-29
**Updated**: 2026-01-30
**Status**: ✅ Deployed to Production
**Owner**: Poolsifi Team

---

## Current Production Status

| Component | Status | Details |
|-----------|--------|--------|
| Stock Buddy API | ✅ Live | https://stock-buddy-app.vercel.app/api/tte |
| TTE Dashboard | ✅ Live | https://stock-buddy-app.vercel.app/tte |
| TradingView Alerts | ✅ Configured | NWE + OBDIV webhooks active |
| Symbols Database | ✅ Seeded | **1000+ symbols** in MongoDB |
| Python Orchestrator | ⏳ Ready | Not yet started |

---

## Overview

### Problem Statement

TradingView to Everywhere (TTE) is an automated trading signals distribution system. The current implementation faces a critical scaling limitation:

**Pine Script Memory Limit**: TradingView limits each script to **40 `request.security()` calls** (64 with Ultimate plan). The full TTE Screener with 3 indicators (NWE, OB & FVG, Divergence) uses ~24 calls for just 8 symbols (8 symbols × 3 timeframes). This makes it impossible to:

1. Scale beyond ~10 symbols per screener
2. Add additional indicators to the signal chain
3. Monitor the 40+ forex pairs needed for comprehensive coverage

### Solution

A **Tiered Screener Architecture** that separates concerns:

- **Tier 1 (NWE Screener)**: Lightweight screener monitoring 40 symbols per batch (with rotation through 1000+) for initial signal (NWE zone entry)
- **Tier 2 (OBDIV Screener)**: Focused screener checking only "hot" symbols for confluence (OB + Divergence)
- **Stock Buddy Dashboard**: Web application displaying signals with filtering, sorting, and screenshots

This architecture enables scaling to **1000+ symbols** (currently 1000+ seeded in production) through batch rotation while maintaining signal quality through multi-indicator confluence detection.

### Target Users

| User Type | Description | Needs |
|-----------|-------------|-------|
| **Traders** | Active forex traders looking for high-probability setups | Real-time signals, screenshots for proof, filtering by symbol/direction |
| **Signal Subscribers** | Followers receiving signals via Discord/social media | Clear entry signals with supporting evidence |
| **System Operators** | Team managing the TTE system | Monitoring dashboard, error handling, scalability |

### Value Proposition

1. **Scalability**: Monitor unlimited symbols (vs. current 8-symbol limit)
2. **Efficiency**: Only perform expensive OB/DIV calculations when NWE triggers (~5-10% of time)
3. **Quality**: Multi-indicator confluence (NWE + OB + DIV) reduces false signals
4. **Transparency**: Screenshots provide visual proof of each signal
5. **Accessibility**: Web dashboard accessible from any device

---

## Core Features

### Feature 1: Tier 1 NWE Screening

**What it does**: Continuously monitors **1000+ symbols** (via batch rotation of 40 symbols at a time) for Nadaraya-Watson Envelope (NWE) zone entries on H4 and D1 timeframes.

**Why it's important**: NWE zone entry is the first filter in the signal chain. By detecting this separately, we can monitor many more symbols efficiently.

**How it works**:
1. Pine Script indicator runs on TradingView chart
2. Checks if current bar overlaps NWE lower zones (bullish) or upper zones (bearish)
3. When detected, fires webhook to Stock Buddy API with JSON payload
4. Symbol added to "hot list" for Tier 2 checking

**Signal Detection Logic**:
- **Bullish**: Price overlaps lower_avg zone OR lower_far zone
- **Bearish**: Price overlaps upper_avg zone OR upper_far zone
- Must trigger on at least one timeframe (H4 or D1)

### Feature 2: Tier 2 OB+DIV Confirmation

**What it does**: Checks hot symbols for Order Block overlap and Divergence confluence.

**Why it's important**: Reduces false signals by requiring multiple indicator confirmation. Only symbols with NWE trigger are checked, saving computational resources.

**How it works**:
1. Python orchestrator polls API for pending hot symbols
2. Updates OBDIV Screener with hot symbols via Selenium
3. Screener checks for OB/FVG overlap and divergence
4. Fires webhook with findings (both bullish and bearish)
5. API combines with NWE direction to create final signal

**Confirmation Logic**:
- **Level 1**: NWE only (weakest signal)
- **Level 2**: NWE + OB/FVG overlap
- **Level 3**: NWE + OB/FVG + Divergence (strongest signal)

### Feature 3: Stock Buddy Dashboard

**What it does**: Web application displaying all signals with real-time updates, filtering, sorting, and screenshot viewing.

**Why it's important**: Replaces Pine Script table display which doesn't scale. Provides better UX with filtering, mobile support, and historical view.

**How it works**:
1. Fetches signals from MongoDB via API
2. Displays in sortable, filterable table (desktop) or card grid (mobile)
3. Shows statistics cards for quick overview
4. Provides screenshot modal for visual proof
5. Real-time updates via polling or WebSocket

### Feature 4: Screenshot Capture

**What it does**: Automatically captures TradingView chart screenshots for each signal.

**Why it's important**: Provides visual proof of signal conditions. Required for social media distribution and historical reference.

**How it works**:
1. Python monitors signals with status "pending_screenshot"
2. Navigates to symbol/timeframe via Selenium
3. Captures screenshot using TradingView's snapshot feature
4. Updates signal with screenshot URL

### Feature 5: Webhook-Based Alert Delivery

**What it does**: TradingView sends alerts directly to Stock Buddy API via HTTP webhooks.

**Why it's important**: Faster and more reliable than Selenium-based alert scraping. Instant delivery without browser overhead.

**How it works**:
1. TradingView alert configured with webhook URL
2. Pine Script builds JSON payload with signal details
3. Alert fires HTTP POST to Stock Buddy API
4. API processes payload and stores in MongoDB

---

## User Experience

### User Personas

#### Persona 1: Active Trader (Primary)
- **Name**: Alex
- **Role**: Part-time forex trader
- **Goals**: Find high-probability trade setups without watching charts all day
- **Pain Points**: Too many false signals, missing good setups, information overload
- **Needs**: Filtered signals by quality (Level 3), quick screenshot verification, mobile access

#### Persona 2: Signal Provider (Secondary)
- **Name**: Jordan
- **Role**: Runs trading signal Discord server
- **Goals**: Provide quality signals to subscribers, maintain track record
- **Pain Points**: Manual chart analysis is time-consuming, need proof of signals
- **Needs**: Automated signal generation, screenshot proof, historical performance

#### Persona 3: System Administrator
- **Name**: Sam
- **Role**: Technical team member managing TTE
- **Goals**: Keep system running smoothly, add new symbols, troubleshoot issues
- **Pain Points**: Current system doesn't scale, difficult to add indicators
- **Needs**: Clear architecture, error monitoring, easy configuration

### Key User Flows

#### Flow 1: Viewing New Signals
```
1. Open Stock Buddy dashboard
2. See notification badge showing new signals
3. View signals table sorted by time (newest first)
4. Filter by Level 3 for high-quality signals only
5. Click screenshot icon to view chart
6. Decide whether to take trade
```

#### Flow 2: Researching a Symbol
```
1. Open Stock Buddy dashboard
2. Search for symbol (e.g., "GBPAUD")
3. View all historical signals for that symbol
4. Analyze pattern of signal quality
5. Check screenshots for visual confirmation
```

#### Flow 3: System Monitoring (Admin)
```
1. Check statistics cards for daily signal count
2. Review Level 3 vs Level 1 distribution
3. Check for pending screenshots
4. Monitor hot list size
5. Review error logs if issues
```

### UI/UX Considerations

1. **Mobile-First**: Dashboard must work well on mobile (traders check signals on phone)
2. **Quick Scanning**: Use color coding (green=bullish, red=bearish, gold=Level 3)
3. **Progressive Disclosure**: Show summary first, details on click
4. **Real-Time**: Auto-refresh or live updates for new signals
5. **Accessibility**: Clear contrast, readable fonts, screen reader support

---

## Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SYSTEM ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 1: TTE NWE Screener (TradingView)                             │   │
│  │  - Pine Script indicator                                            │   │
│  │  - 20 symbols × 2 timeframes = 40 request.security() calls          │   │
│  │  - Webhook output to Stock Buddy API                                │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                                  │ POST /api/nwe                            │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STOCK BUDDY (Vercel + MongoDB)                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │ /api/nwe    │  │ /api/obdiv  │  │ /api/signals│                  │   │
│  │  │ Add to hot  │  │ Create sig  │  │ Fetch sigs  │                  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │   │
│  │  ┌─────────────────────────────────────────────────┐                │   │
│  │  │ MongoDB: hot_list, signals collections          │                │   │
│  │  └─────────────────────────────────────────────────┘                │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                                  │ GET /api/hot-symbols                     │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PYTHON ORCHESTRATOR (Local Machine)                                │   │
│  │  - Polls API for hot symbols                                        │   │
│  │  - Updates OBDIV Screener via Selenium                              │   │
│  │  - Captures screenshots                                             │   │
│  │  - Updates signals with screenshot URLs                             │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                                  │ Selenium automation                      │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 2: TTE OBDIV Screener (TradingView)                           │   │
│  │  - Pine Script indicator (no NWE, no table)                         │   │
│  │  - 8 symbols dynamically set by Python                              │   │
│  │  - Webhook output to Stock Buddy API                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Models

#### Hot List Document (MongoDB: `hot_list`)
```javascript
{
  _id: ObjectId,
  symbol: String,           // "GBPAUD"
  direction: String,        // "bullish" | "bearish"
  nwe_timeframes: [String], // ["H4", "D1"]
  nwe_timestamp: Number,    // Unix timestamp when NWE triggered
  status: String,           // "pending_tier2" | "tier2_complete" | "expired"
  updated_at: Date,
  last_checked: Date
}

// Indexes
{ symbol: 1 }              // Unique - one entry per symbol
{ status: 1, updated_at: 1 } // For querying pending symbols
```

#### Signal Document (MongoDB: `signals`)
```javascript
{
  _id: ObjectId,
  symbol: String,           // "GBPAUD"
  direction: String,        // "bullish" | "bearish"
  level: Number,            // 1, 2, or 3
  nwe_tf: [String],         // ["H4", "D1"]
  ob_tf: String,            // "W1" or null
  ob_type: String,          // "OB", "FVG", "Breaker" or null
  div_tf: String,           // "H4" or null
  div_type: String,         // "Logic2", "Internal" or null
  timestamp: Number,        // Unix timestamp from alert
  screenshot_url: String,   // TradingView snapshot URL or null
  status: String,           // "pending_screenshot" | "complete"
  created_at: Date
}

// Indexes
{ created_at: -1 }         // For time-sorted queries
{ status: 1 }              // For pending screenshot queries
{ level: 1 }               // For level filtering
{ symbol: 1 }              // For symbol search
```

### APIs and Integrations

#### Stock Buddy API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/nwe` | POST | Receive Tier 1 webhooks, add to hot list |
| `/api/obdiv` | POST | Receive Tier 2 webhooks, create signals |
| `/api/signals` | GET | Fetch signals for dashboard |
| `/api/signals/[id]` | PATCH | Update signal with screenshot |
| `/api/hot-symbols` | GET | Get pending symbols for Python |

#### Webhook Payloads

**Tier 1 (NWE → /api/nwe)**:
```json
{
  "tier": "nwe",
  "symbol": "GBPAUD",
  "direction": "bullish",
  "timeframes": ["H4", "D1"],
  "timestamp": 1672531200
}
```

**Tier 2 (OBDIV → /api/obdiv)**:
```json
{
  "tier": "obdiv",
  "symbol": "GBPAUD",
  "bull_ob": {"found": true, "tf": "W1", "type": "OB"},
  "bull_div": {"found": true, "tf": "H4", "type": "Logic2"},
  "bear_ob": {"found": false},
  "bear_div": {"found": false},
  "timestamp": 1672531200
}
```

### Infrastructure Requirements

| Component | Technology | Hosting |
|-----------|------------|---------|
| Tier 1 Screener | Pine Script | TradingView |
| Tier 2 Screener | Pine Script | TradingView |
| Stock Buddy API | Next.js API Routes | Vercel |
| Stock Buddy Dashboard | Next.js + React | Vercel |
| Database | MongoDB | MongoDB Atlas |
| Python Orchestrator | Python + Selenium | Local machine |
| Browser Automation | Selenium + Chrome | Local machine |

---

## Development Roadmap

### Phase 1: Symbol Selection
**Scope**: Finalize the 20 forex pairs for initial deployment.

**Deliverables**:
- Confirmed list of 20 symbols
- Symbol configuration for Pine Script

**Symbol Categories (1000+ Total)**:

| Category | Count | Priority | Scan Frequency |
|----------|-------|----------|----------------|
| Currencies (FX) | 30 | A | Every batch |
| Crypto | 19 | A/B/C | Mixed |
| Indices | 8 | A/B | Every 1-3 batches |
| Indian Stocks (NSE) | 500+ | A/B/C | Mixed |
| US Stocks | 400+ | A/B/C | Mixed |

**Priority System:**
- **Priority A**: Scanned every batch (~100 symbols)
- **Priority B**: Scanned every 3rd batch (~300 symbols)
- **Priority C**: Scanned every 10th batch (~600 symbols)

### Phase 2: TTE NWE Screener (Tier 1)
**Scope**: Create lightweight NWE-only screener with webhook output.
**Status**: ✅ Complete

**Deliverables**:
- Pine Script indicator file (`TTE NWE Screener v2.txt`)
- Webhook alert configuration
- Testing on TradingView

**Technical Specifications**:
- 40 symbols per batch × 2 timeframes (H4, D1) = 80 request.security() calls
- Batch rotation through 1000+ symbols via Python orchestrator
- NWE zone detection using kernel regression
- JSON webhook payload on zone entry
- State tracking to fire only on changes

### Phase 3: TTE OBDIV Screener (Tier 2)
**Scope**: Create focused OB+DIV screener without NWE calculation.

**Deliverables**:
- Pine Script indicator file (`TTE OBDIV Screener.txt`)
- Webhook alert configuration
- Testing on TradingView

**Technical Specifications**:
- 8 symbols (dynamically configurable)
- OB/FVG detection on H4, D1, W1
- Divergence detection on H4, D1
- Reports both bullish and bearish findings
- No table display (webhook only)

### Phase 4: Stock Buddy API Endpoints
**Scope**: Create 5 API endpoints for webhook reception and dashboard data.

**Deliverables**:
- `/api/nwe` - Hot list management
- `/api/obdiv` - Signal creation
- `/api/signals` - Signal retrieval
- `/api/signals/[id]` - Signal update
- `/api/hot-symbols` - Python polling

**Technical Specifications**:
- Next.js API routes
- MongoDB connection via client library
- Input validation
- Error handling and logging

### Phase 5: MongoDB Setup
**Scope**: Create database collections with proper schema and indexes.

**Deliverables**:
- `hot_list` collection with indexes
- `signals` collection with indexes
- Connection configuration

**Technical Specifications**:
- MongoDB Atlas cluster
- Indexes for query performance
- TTL index for hot list expiry (optional)

### Phase 6: Python Orchestrator
**Scope**: Update orchestrator for webhook-based flow.

**Deliverables**:
- Updated `tiered_orchestrator.py`
- API polling logic
- Selenium symbol input updates
- Screenshot capture and upload

**Technical Specifications**:
- Poll `/api/hot-symbols` every 60 seconds
- Update OBDIV Screener symbols via Selenium
- Process pending screenshots
- Update signals via API

### Phase 7: Stock Buddy Dashboard
**Scope**: Create web dashboard for signal display.

**Deliverables**:
- Statistics cards component
- Filter bar component
- Signals table (desktop)
- Signal cards (mobile)
- Screenshot modal
- Notifications system
- Real-time updates
- Distribution chart
- Main page assembly

**Technical Specifications**:
- Next.js 14 App Router
- Tailwind CSS styling
- shadcn/ui components
- React Query for data fetching
- Recharts for visualization

### Phase 8: Integration Testing
**Scope**: End-to-end testing of complete signal flow.

**Deliverables**:
- Test Level 1 signal flow
- Test Level 2 signal flow
- Test Level 3 signal flow
- Test screenshot capture
- Test dashboard updates

### Phase 9: Production Deployment
**Scope**: Deploy all components to production.

**Deliverables**:
- Deploy Stock Buddy to Vercel
- Configure TradingView alerts
- Start Python orchestrator
- Monitor for issues

---

## Logical Dependency Chain

### Foundation Layer (Can Start Immediately)
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Phase 1         │  │ Phase 4         │  │ Phase 5         │
│ Symbol Selection│  │ API Endpoints   │  │ MongoDB Setup   │
│ (no deps)       │  │ (no deps)       │  │ (no deps)       │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         ▼                    └─────────┬──────────┘
┌─────────────────┐                     │
│ Phase 2         │                     │
│ NWE Screener    │                     │
│ (needs symbols) │                     │
└────────┬────────┘                     │
         │                              │
         │           ┌──────────────────┘
         ▼           ▼
┌─────────────────┐  ┌─────────────────┐
│ Phase 3         │  │ Phase 6         │
│ OBDIV Screener  │  │ Python Orch.    │
│ (needs symbols) │  │ (needs API+DB)  │
└────────┬────────┘  └────────┬────────┘
         │                    │
         └─────────┬──────────┘
                   │
                   ▼
         ┌─────────────────┐
         │ Phase 8         │
         │ Integration Test│
         │ (needs all)     │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Phase 9         │
         │ Deployment      │
         └─────────────────┘
```

### Dashboard Development (Parallel Track)
```
Phase 4 (API) ───► Phase 7a (Stats Cards) ───┐
                                              │
              ┌── Phase 7b (Filter Bar) ──────┤
              │                               │
              ├── Phase 7c (Signals Table) ───┤
              │                               │
              ├── Phase 7d (Mobile Cards) ────┤
              │                               │
              ├── Phase 7e (Screenshot Modal)─┤
              │                               │
              ├── Phase 7f (Notifications) ───┤
              │                               │
              ├── Phase 7g (Real-time) ───────┤
              │                               │
              └── Phase 7h (Distribution) ────┤
                                              │
                                              ▼
                               Phase 7i (Main Page Assembly)
```

### Recommended Execution Order

**Week 1: Parallel Foundation**
1. Phase 1: Symbol Selection (quick)
2. Phase 4: API Endpoints (start)
3. Phase 5: MongoDB Setup (quick)

**Week 2: Core Screeners**
4. Phase 2: NWE Screener (after Phase 1)
5. Phase 3: OBDIV Screener (after Phase 1)
6. Phase 4: API Endpoints (complete)

**Week 3: Integration**
7. Phase 6: Python Orchestrator (after Phase 4, 5)
8. Phase 7a-7e: Dashboard core components (parallel)

**Week 4: Polish & Deploy**
9. Phase 7f-7i: Dashboard remaining components
10. Phase 8: Integration Testing
11. Phase 9: Production Deployment

---

## Risks and Mitigations

### Risk 1: TradingView Webhook Reliability
**Risk**: Webhooks may fail silently or be delayed.
**Impact**: Missed signals, stale hot list.
**Mitigation**:
- Implement retry logic in TradingView alert
- Add health check endpoint to detect delivery issues
- Monitor webhook delivery rate
- Fallback: Alert scraping via Selenium (existing code)

### Risk 2: Selenium Brittleness
**Risk**: TradingView UI changes break Selenium automation.
**Impact**: Cannot update OBDIV symbols or capture screenshots.
**Mitigation**:
- Use robust selectors (data attributes over classes)
- Add retry logic with exponential backoff
- Implement health monitoring
- Document manual intervention procedures

### Risk 3: MongoDB Atlas Latency
**Risk**: Database queries slow down signal creation.
**Impact**: Delayed signals, poor UX.
**Mitigation**:
- Create appropriate indexes
- Use connection pooling
- Cache frequently accessed data
- Monitor query performance

### Risk 4: Hot List Overflow
**Risk**: Too many hot symbols exceed OBDIV screener capacity (8).
**Impact**: Symbols not checked, signals missed.
**Mitigation**:
- Prioritize by NWE signal strength
- Implement batching (process 8 at a time)
- Add expiry to hot list entries (24hr)
- Monitor hot list size

### Risk 5: Screenshot Capture Failures
**Risk**: Chart doesn't load, screenshot fails.
**Impact**: Signals without visual proof.
**Mitigation**:
- Add wait conditions for chart load
- Implement retry logic
- Mark signals as "screenshot_failed" for retry
- Allow manual screenshot upload

### MVP Definition
**Minimum Viable Product includes**:
1. NWE Screener with 40 symbols per batch, 1000+ total via rotation (Tier 1)
2. OBDIV Screener with 8 symbols (Tier 2)
3. API endpoints for webhook reception
4. Basic dashboard with signals table
5. Screenshot capture

**Can be added later**:
- Real-time WebSocket updates
- Push notifications
- Distribution chart
- Mobile app
- Social media distribution
- Historical performance analytics

---

## Appendix

### A. Signal Logic Reference

#### Bullish Signal Conditions (Sequential)
1. **NWE Zone**: Price overlaps lower_avg or lower_far zone on H4 OR D1
2. **OB/FVG**: Price overlaps bullish OB, bullish FVG, or breaker support on H4, D1, OR W1
3. **Divergence**: Bullish divergence (Internal, Logic 1, or Logic 2) completes on current bar on H4 OR D1

#### Bearish Signal Conditions (Sequential)
1. **NWE Zone**: Price overlaps upper_avg or upper_far zone on H4 OR D1
2. **OB/FVG**: Price overlaps bearish OB, bearish FVG, or breaker resistance on H4, D1, OR W1
3. **Divergence**: Bearish divergence (Internal, Logic 1, or Logic 2) completes on current bar on H4 OR D1

#### Signal Levels
| Level | Conditions Met | Quality |
|-------|----------------|---------|
| 1 | NWE only | Low |
| 2 | NWE + OB/FVG | Medium |
| 3 | NWE + OB/FVG + DIV | High |

### B. NWE Zone Structure

```
upper_far   ─────  (highest red line)
              UPPER FAR ZONE (bearish)
upper_avg   ─────  (middle red line)
              UPPER AVG ZONE (bearish)
upper_near  ─────  (bottom red line)
yhat        ═════  (regression line - NOT a zone boundary)
lower_near  ─────  (top green line)
              LOWER AVG ZONE (bullish)
lower_avg   ─────  (middle green line)
              LOWER FAR ZONE (bullish)
lower_far   ─────  (lowest green line)
```

### C. Technology Stack

| Category | Technology | Purpose |
|----------|------------|---------|
| Pine Script | TradingView v5 | Screener indicators |
| Frontend | Next.js 14 | Dashboard framework |
| Styling | Tailwind CSS | UI styling |
| Components | shadcn/ui | Pre-built components |
| Data Fetching | React Query | API state management |
| Charts | Recharts | Data visualization |
| Database | MongoDB Atlas | Signal storage |
| Hosting | Vercel | Dashboard hosting |
| Automation | Python + Selenium | Browser control |
| Notifications | react-hot-toast | Toast messages |

### D. Environment Variables

**Stock Buddy (Vercel)**:
```
MONGODB_URI=mongodb+srv://...
```

**Python Orchestrator**:
```
STOCK_BUDDY_API_URL=https://stock-buddy-app.vercel.app/api
CHROME_PROFILE_PATH=...
```

**TradingView**:
```
Webhook URL: https://stock-buddy-app.vercel.app/api/nwe
Webhook URL: https://stock-buddy-app.vercel.app/api/obdiv
```

### E. Related Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Implementation Plan | `.claude/TIERED_ARCHITECTURE_IMPLEMENTATION_PLAN.md` | Detailed implementation guide |
| Task Context | `.claude/task-context.md` | Session progress tracking |
| Signal Logic | `Pine Script Code/logic/Regime 1 Reversal logic for SB.md` | Original requirements |
| Project Overview | `CLAUDE.md` | Project documentation |

---

*This PRD is the source of truth for the TTE Tiered Screener Architecture project.*
