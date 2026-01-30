# Changelog
# TTE Tiered Screener Architecture

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Dashboard notifications for new signals
- Signal distribution chart
- Mobile-responsive card grid
- Push notifications via service worker
- User authentication for dashboard

---

## [2.0.0] - 2026-01-29

### Added
- **Tiered Screener Architecture** - New webhook-based architecture for scalable multi-symbol screening
  - Tier 1: TTE NWE Screener (20 symbols, H4+D1)
  - Tier 2: TTE OBDIV Screener (8 symbols, dynamic)
- **Stock Buddy API** - New API endpoints for webhook processing
  - `POST /api/nwe` - Receive NWE webhooks
  - `POST /api/obdiv` - Receive OBDIV webhooks
  - `GET /api/signals` - Fetch signals for dashboard
  - `PATCH /api/signals/:id` - Update signal with screenshot
  - `GET /api/hot-symbols` - Get pending hot symbols
- **MongoDB Integration** - Database storage for signals and hot list
  - `hot_list` collection for pending symbols
  - `signals` collection for confirmed signals
- **Stock Buddy Dashboard** - Web-based signal display
  - Statistics cards (today, level 3, bullish/bearish)
  - Filter bar with sorting and search
  - Signals table with expandable details
  - Screenshot modal viewer
- **Python Orchestrator Updates** - New tiered workflow
  - Poll API for hot symbols
  - Dynamic symbol updates via Selenium
  - Screenshot capture and upload

### Changed
- Architecture shifted from single screener to tiered approach
- Alert delivery changed from scraping to webhooks
- Signal display moved from Pine Script table to web dashboard
- Python role reduced to screenshot capture only

### Technical Details
- Webhooks provide instant delivery vs polling-based scraping
- NWE removed from Tier 2 (redundant after Tier 1 confirmation)
- OBDIV reports both directions, API matches with hot list
- Signal levels: 1=NWE, 2=NWE+OB, 3=NWE+OB+DIV

---

## [1.9.0] - 2026-01-27

### Added
- **Regime 1 Reversal Signal Logic** - Complete signal detection chain
  - Level 1: NWE zone entry (H4 or D1)
  - Level 2: OB/FVG overlap (H4, D1, or W1)
  - Level 3: Divergence confirmation (H4 or D1)
- **Signal table with tooltips** - Hover for detailed zone information
- **Alert JSON format** - Structured alerts for Python processing

### Fixed
- NWE zone detection using correct boundary lines
- Missing `upper_avg` and `lower_avg` calculations
- Zone overlap logic for accurate signal detection

---

## [1.8.0] - 2026-01-26

### Added
- **Logic 1 Divergence Detection** - Traditional divergence patterns
- **Internal Divergence Detection** - Within single AO range
- **Logic 2 Divergence Detection** - Cross-range divergence

### Fixed
- Array index -1 out of bounds in divergence detection
- Added guards for edge cases in swing point scanning

---

## [1.7.0] - 2026-01-17

### Added
- **Multi Oscillator Same Side Divergence** - Cross-oscillator confirmation

### Fixed
- Swing point overwrite bug in range tracking
- Guards added to prevent range value updates after finding 2 ranges

---

## [1.6.0] - 2026-01-16

### Added
- **Kernel AO Divergence** - Custom oscillator divergence detection
- **Range-based divergence scanning** - Negative and positive range identification

### Fixed
- NaN kernel AO values due to insufficient history
- Start offset calculation for valid bar scanning

---

## [1.5.0] - 2026-01-15

### Added
- **OB & FVG Indicator Integration** - Order blocks and fair value gaps
- **Weekly timeframe support** - W1 OB/FVG detection

### Fixed
- Reversed OB detection with lifecycle depth limit
- Continuation loop for breaker detection

---

## [1.4.0] - 2026-01-14

### Added
- **NWE Indicator Integration** - Nadaraya-Watson Envelope zones
- **Multi-timeframe support** - H4 and D1 NWE detection

### Fixed
- False overlap on FVG formation bar
- Added `i >= 4` guard for overlap checks

---

## [1.3.0] - 2026-01-13

### Added
- **Symbol Expansion** - Increased from 5 to 20 symbols
- **Batch processing** - Symbols grouped for request.security limits

### Fixed
- Pine Script runtime error with negative historical reference
- Loop boundary handling for i=2 case

---

## [1.2.0] - 2026-01-10

### Added
- **TTE Screener Base** - Initial multi-symbol screener
- **Request.security optimization** - Efficient data fetching
- **Table display** - Visual signal presentation

---

## [1.1.0] - 2026-01-05

### Added
- **Core Infrastructure**
  - Selenium browser automation
  - TradingView integration
  - Alert handling system
  - Social media distribution

---

## [1.0.0] - 2025-12-15

### Added
- **Initial Release**
  - TradingView alert monitoring
  - Screenshot capture
  - Discord distribution
  - Firebase storage

---

## Migration Notes

### Upgrading to 2.0.0

**Breaking Changes:**
1. New architecture requires Stock Buddy deployment
2. Python orchestrator configuration changed
3. TradingView screeners need recreation

**Migration Steps:**
1. Deploy Stock Buddy to Vercel
2. Set up MongoDB Atlas database
3. Create new TTE NWE Screener v2 in TradingView
4. Create new TTE OBDIV Screener in TradingView
5. Update Python `.env` with new API URL
6. Update Python orchestrator code

**Rollback:**
- Keep old screener alerts active during migration
- Can run both systems in parallel temporarily
- Old system still functional if rollback needed

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 2.0.0 | 2026-01-29 | Tiered architecture, webhooks, dashboard |
| 1.9.0 | 2026-01-27 | Regime 1 Reversal logic, tooltips |
| 1.8.0 | 2026-01-26 | Logic 1, Internal, Logic 2 divergence |
| 1.7.0 | 2026-01-17 | Multi oscillator divergence |
| 1.6.0 | 2026-01-16 | Kernel AO divergence |
| 1.5.0 | 2026-01-15 | OB & FVG integration |
| 1.4.0 | 2026-01-14 | NWE integration |
| 1.3.0 | 2026-01-13 | 20 symbol expansion |
| 1.2.0 | 2026-01-10 | Base screener |
| 1.1.0 | 2026-01-05 | Core infrastructure |
| 1.0.0 | 2025-12-15 | Initial release |

---

*This changelog is maintained as part of the TTE project documentation.*
