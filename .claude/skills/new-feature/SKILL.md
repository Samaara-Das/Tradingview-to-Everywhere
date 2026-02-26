---
name: new-feature
description: >
  This skill should be used when the user wants to plan and implement one or more new features in TTE
  (TradingView to Everywhere). It guides Claude through a structured pre-implementation workflow: reading
  relevant existing docs, asking clarifying questions, and producing a mini PRD with specific test scenarios
  before any code is written. Triggers on: 'new feature', 'add feature', 'implement feature', 'let's build',
  'I want to add', 'let's do this task' or any feature request that hasn't been designed yet.
---

# New Feature Workflow

This skill orchestrates the pre-implementation planning process for new features in TTE. The goal is to ensure
nothing is built until the "what" and "how" are fully defined — producing a mini PRD that serves as the source
of truth for both implementation and testing.

## Phase 1: Orientation — Read the Docs

Before anything else, enter **plan mode** (`EnterPlanMode`).

Read the existing TTE documentation to build an accurate, up-to-date understanding of what is already
implemented in the areas related to the requested features. Do not rely on memory — read the actual files.

Docs to read (always):
- `CLAUDE.md` — architecture, package structure, key code locations, conventions
- `docs/combo/ARCHITECTURE.md` — combo mode architecture and workflow
- `docs/combo/PRD.md` — existing combo mode product requirements
- `combo_settings.yaml` — current configuration options

Then read any additional docs that are directly relevant to the feature area. Examples:
- Browser automation → `tte/browser/tradingview.py`, `tte/browser/chart.py`, `tte/browser/helpers.py`
- Alerts/webhooks → `tte/main.py`, `docs/API.md`
- Pine Script/indicators → `docs/indicators/`, `Pine Script Code/`
- Snapshots → `tte/browser/chart.py`, snapshot-related sections in `tte/main.py`
- Configuration → `tte/config.py`, `combo_settings.yaml`
- Database/symbols → `tte/data/symbols.py`, `docs/DATABASE.md`
- Stock Buddy integration → `docs/STOCK_BUDDY_TECHNICAL_ARCHITECTURE.md`, `docs/API.md`

The depth goal: know what is implemented in the affected area — code patterns, config, and behavior. Do not
skip this step — building on stale assumptions causes rework.

After reading, write a concise summary of the relevant current state (2-5 bullet points) so the user can
confirm the understanding is correct before proceeding.

## Phase 2: Clarification — Mini PRD

Ask the user clarifying questions to fill in any gaps. Keep questions focused and grouped — avoid drip-feeding
one question at a time. Use `AskUserQuestion` to present choices where applicable.

The mini PRD must leave no question unanswered on these axes:
1. **What to build** — scope, behavior, edge cases, constraints
2. **How it interacts with existing systems** — which TTE modules are affected, any Stock Buddy API changes needed, any Pine Script changes needed
3. **Configuration** — any new settings in `combo_settings.yaml` or `.env`
4. **Error handling & recovery** — what happens when things go wrong (Selenium failures, API errors, rate limits)

### Mini PRD Structure

```
## Feature: [Name]

### Overview
[1-2 sentence description]

### Scope
- In scope: ...
- Out of scope: ...

### Functional Requirements
[Numbered list of specific behaviors — FR-001, FR-002, etc.]

### Configuration Changes
[Any new settings in combo_settings.yaml, .env, or tte/config.py]

### Affected Modules
[Which files/modules are modified and how]

### Error Handling & Recovery
[What happens on failure — retries, logging, graceful degradation]

### Stock Buddy API Changes (if any)
[New endpoints, modified payloads, or schema changes needed on the Stock Buddy side]

### Pine Script Changes (if any)
[Indicator modifications, new alert conditions, or screener changes]

### Test Scenarios
[See Phase 3 below]
```

## Phase 3: Test Scenarios

Write test scenarios directly in the mini PRD. These should be concrete action/expectation pairs that can be
manually verified.

**Format each scenario as:**
```
Scenario [N]: [Short title]
- Given: [starting state — e.g., "TTE is running with 264 alerts active"]
- When: [action — e.g., "a webhook fires for AAPL with signal type 'buy'"]
- Then: [expected result — e.g., "Stock Buddy receives POST with correct payload, returns 200"]
```

**Coverage checklist** (write scenarios for all that apply):
- [ ] Happy path (feature works as expected)
- [ ] Error/failure state (Selenium error, API timeout, network issue)
- [ ] Recovery behavior (retry logic, re-upload indicator, alert restart)
- [ ] Edge cases called out in requirements
- [ ] Configuration variations (different settings produce different behavior)
- [ ] Interaction with maintenance cycle (does the feature survive alert restarts?)
- [ ] Rate limiting / TradingView constraints (15 triggers/3min per alert, 4-symbol limit)

Write the right number of scenarios — a focused feature needs 3-6; a complex multi-module change may need 8-12.

## Phase 4: Hand-off

Present the completed mini PRD to the user for approval. Do not begin implementation until the user explicitly
approves the PRD.

Once approved:
1. Save the PRD to `docs/prds/[feature-name].md`
2. Exit plan mode
3. Proceed to implementation

## Usage Template

When the user invokes `/new-feature`, expect input in this format:

```
/new-feature

Tasks:
[list of features to build]

Additional context:
[any constraints, background, or notes]
```

If the user's message does not include the tasks list, ask for it before proceeding.
