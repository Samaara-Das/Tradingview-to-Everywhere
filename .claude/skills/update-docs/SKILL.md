---
name: update-docs
description: "Use this skill after adding, removing, or changing features in TTE (TradingView to Everywhere) to update all project documentation. Triggers: 'update docs', 'sync docs', 'refresh docs', 'clean up docs', 'docs are outdated', 'update documentation', or when prompted to update docs after a feature change. Audits all doc files for accuracy, removes outdated content, adds missing info, and ensures cross-doc consistency."
---

# TTE — Documentation Updater

Keep all TradingView to Everywhere documentation accurate, consistent, and free of outdated information after feature changes.

## Execution Mode

**IMPORTANT: Enter plan mode immediately when this skill is invoked.** Use `EnterPlanMode` before doing any work. The planning phase should complete Phase 1 (Gather Current State) and Phase 2 (Audit Each Doc) — presenting the user with a clear summary of what will be added, updated, removed, and flagged. Only after the user approves the plan should Phase 3 (Apply Updates) and beyond proceed.

## When to Run

Run this skill:
- After completing a feature, refactor, or significant bug fix
- After fixing TradingView UI selector breakages
- When the user says docs need updating
- When reminded by post-task prompts to update documentation

## Document Categories

All documentation files are organized into tiers. Every tier must be audited.

### Tier 1: Primary Docs (always audit)
| File | Purpose | Content Guidelines |
|------|---------|-------------------|
| `CLAUDE.md` | AI assistant codebase guide | Architecture overview, package structure, key code locations, settings table, dev commands. Keep concise — loaded every session. |
| `README.md` | Project overview for GitHub | Tech stack, features, quick start, project structure. Public-facing. |

### Tier 2: Architecture & Combo Docs (audit when features change)
| File | Purpose | Content Guidelines |
|------|---------|-------------------|
| `docs/combo/ARCHITECTURE.md` | Complete V2 architecture — system overview, data flows, component breakdown | Mermaid diagrams, payload format, V1 vs V2 comparison. Developer audience. |
| `docs/combo/PRD.md` | Product requirements, implementation plan | Milestones, feature specs, production config. Stakeholder audience. |

### Tier 3: Setup & Reference Docs (audit when relevant)
| File | Purpose | Content Guidelines |
|------|---------|-------------------|
| `docs/SETUP.md` | Installation and environment setup | Step-by-step for new developers. Update when dependencies or config change. |
| `docs/API.md` | Stock Buddy API integration | Endpoint reference, payload format, webhook details. Update when API changes. |
| `docs/DATABASE.md` | MongoDB collections and schemas | Collection schemas, field descriptions. Update when data model changes. |
| `docs/TROUBLESHOOTING.md` | Common issues and solutions | Add new issues as discovered. Remove resolved ones. |
| `docs/CONTRIBUTING.md` | Contribution guidelines | Rarely updated. |

### Tier 4: Technical Reference (audit when indicators/Pine Script change)
| File | Purpose |
|------|---------|
| `docs/indicators/nadaraya-watson-envelope.md` | NWE indicator logic (core signal type) |
| `docs/indicators/order-block-fvg.md` | OB/FVG indicator logic (core signal type) |
| `docs/indicators/kernel-ao-divergence-logic2.md` | Divergence indicator logic (removed in V2, kept for reference) |
| `docs/STOCK_BUDDY_TECHNICAL_ARCHITECTURE.md` | Stock Buddy integration architecture |
| `docs/prds/backfill-snapshots.md` | Backfill snapshots PRD |

### Tier 5: Agent & Session Docs (audit for staleness)
| File | Purpose |
|------|---------|
| `.claude/task-context.md` | Session progress tracker — update each session |
| `.claude/skills/update-docs/references/doc-inventory.md` | Documentation inventory — update after doc changes |

## Workflow

### Phase 1: Gather Current State (PLAN MODE)

1. Read `references/doc-inventory.md` to get the full list of documentation files
2. Read the git log for recent commits to understand what changed:
   ```
   git log --oneline -20
   ```
3. Read the current codebase state for areas that changed — check:
   - `tte/` for new/removed/renamed Python modules
   - `tte/browser/` for Selenium automation changes (selectors, flows)
   - `tte/data/` for data layer changes
   - `tte/main.py` for orchestrator changes
   - `tte/config.py` for configuration changes
   - `combo_settings.yaml` for settings changes
   - `Pine Script Code/` for indicator changes
   - `Pipfile` for dependency changes
   - `.env` for environment variable changes

### Phase 2: Audit Each Doc (PLAN MODE)

Audit **all tiers** of documentation. For each doc file, compare the documented state against the actual codebase.

#### Things to ADD
- New Python modules, classes, or functions not yet documented
- New CLI flags or entry points
- New environment variables or settings
- Changed TradingView selectors or UI flows
- New alert creation/maintenance patterns
- New Pine Script features or payload fields

#### Things to REMOVE or UPDATE
- References to deleted files or renamed modules
- Outdated TradingView selector references (these break frequently)
- Old architecture descriptions that don't match current V2 flow
- Stale settings tables that don't match `combo_settings.yaml`
- Removed Pine Script fields or deprecated features (e.g., V1-only stuff still described as current)
- Old API endpoints or payload formats

#### Things to FLAG
- Selector references in docs that may not match TradingView's current UI (high churn area)
- `task-context.md` sections that reference completed/outdated work
- Architecture diagrams that show removed components

#### Sync Checks
Perform these cross-document consistency checks:

1. **CLAUDE.md ↔ combo_settings.yaml**: Verify the settings table in CLAUDE.md matches the actual YAML file. Check defaults, descriptions, and YAML paths.
2. **CLAUDE.md ↔ actual package structure**: Verify the package structure section lists all current files under `tte/`.
3. **ARCHITECTURE.md ↔ PRD.md**: Ensure both describe the same V2 architecture (symbol count, batch size, alert count, payload format).
4. **ARCHITECTURE.md ↔ Pine Script**: Verify payload field descriptions match what the Pine Script actually emits.
5. **API.md ↔ actual webhook URL**: Verify the documented webhook URL and payload format match `.env` and Pine Script output.
6. **Doc inventory completeness**: Verify `references/doc-inventory.md` lists ALL `.md` files that actually exist. Run:
   ```bash
   find . -name "*.md" -not -path "./.git/*" -not -path "./node_modules/*"
   ```
   Flag any files missing from the inventory.

### Present Plan and Exit Plan Mode

After completing Phase 1 and Phase 2, write a plan summarizing:
- **Files to update** with specific changes per file
- **Content to add** (new modules, settings, selectors, etc.)
- **Content to remove** (outdated references, deleted files, stale descriptions)
- **Content to flag** (potentially outdated selectors, stale diagrams)
- **Sync issues** (cross-document discrepancies)
- **Files to potentially delete** (stale docs for removed features)

Use `ExitPlanMode` to present this plan for user approval. Only proceed to Phase 3 after approval.

### Phase 3: Apply Updates (AFTER PLAN APPROVAL)

Update docs in this priority order:

1. **`CLAUDE.md`** — Most critical. This is what Claude reads every session.
   - Update the package structure section to match actual `tte/` contents
   - Update the settings table to match `combo_settings.yaml`
   - Update key code locations table if functions moved/renamed
   - Update environment variables section
   - Update running commands section if CLI flags changed
   - Keep the file well-organized — don't let sections bloat

2. **`docs/combo/ARCHITECTURE.md`** — V2 system architecture.
   - Update component descriptions and data flows
   - Update payload format if Pine Script fields changed
   - Update Mermaid diagrams if system topology changed
   - Update selector references if TradingView UI changed

3. **`docs/combo/PRD.md`** — Product requirements.
   - Mark completed milestones
   - Update production configuration numbers (symbol count, alert count)
   - Update feature descriptions
   - Adjust roadmap if scope changed

4. **`README.md`** — Public overview.
   - Update feature list and quick start
   - Update project structure if new files added
   - Keep concise — details go in architecture docs

5. **Setup & reference docs** — Only if the change is relevant:
   - `docs/SETUP.md`: Dependency or config changes
   - `docs/API.md`: API endpoint or payload changes
   - `docs/DATABASE.md`: Schema changes
   - `docs/TROUBLESHOOTING.md`: New issues or resolved issues

6. **Indicator docs** — Only if Pine Script changed.

### Phase 4: Clean Up Stale Docs

Check for docs that should be cleaned or deleted:
- Archived docs (`docs/combo/IMPLEMENTATION.md`) — leave but verify the "archived" label is clear
- `task-context.md` — trim completed task history if it exceeds 200 lines (keep only current/recent tasks and verified patterns/selectors)
- PRDs for completed features (`docs/prds/backfill-snapshots.md`) — mark as complete if not already

Before deleting any file, confirm with the user.

### Phase 5: Update Inventory

After all updates, ensure `references/doc-inventory.md` reflects the current state:
- Add any new doc files created
- Remove deleted doc files
- Update "Last updated" date
- Update status and notes for modified docs

### Phase 6: Report and Remind

After all updates, provide a summary:

```
## Docs Updated
- CLAUDE.md: [what changed]
- ARCHITECTURE.md: [what changed]
- PRD.md: [what changed]
- ...

## Flagged for Manual Action
- [ ] [Any manual items — e.g., selector verification needed after TradingView update]

## Sync Issues Found
- [ ] [Any cross-document discrepancies]

## Docs Reviewed (No Changes Needed)
- [list unchanged docs]
```

Always remind the user to:
1. **Review the diff** before committing doc changes
2. **Verify TradingView selectors** if any selector-related docs were updated (selectors change frequently)
3. **Update `task-context.md`** if the current session's work isn't reflected

## Content Guidelines by Doc Type

### CLAUDE.md
- Keep it concise and scannable — this is loaded into every Claude session
- Use tables for settings, key code locations, and environment variables
- Describe WHAT each file does, not HOW (implementation details go in ARCHITECTURE.md)
- The settings table must mirror `combo_settings.yaml` exactly
- Keep running commands section up to date with all CLI flags

### docs/combo/ARCHITECTURE.md
- Use Mermaid diagrams for system topology and data flows
- Include the full payload format with field descriptions
- Document the alert lifecycle: creation → webhook → API → MongoDB
- Keep V1 vs V2 comparison table for historical context
- Document selector patterns only in `task-context.md` (they change too often for architecture docs)

### docs/combo/PRD.md
- Production configuration numbers must be accurate (symbol count, alert count, batch size)
- Mark completed milestones clearly
- Feature specs should describe current behavior, not aspirational plans
- Include the component details table with versions and tech stack

### docs/API.md
- Document all Stock Buddy API endpoints TTE interacts with
- Include request/response payload examples
- Note authentication requirements (currently none)
- Document webhook format and delivery behavior

### docs/TROUBLESHOOTING.md
- Group by category: Chrome/Selenium, TradingView, Alerts, Network
- Include root cause AND fix for each issue
- Remove issues that have been permanently resolved in code
- Add common TradingView UI breakage patterns

## Important Rules

- Never fabricate documentation — only document what actually exists in the codebase
- When unsure whether something changed, read the actual source file before documenting it
- Keep `CLAUDE.md` concise — it's loaded into every session, so bloat wastes context
- Preserve the existing structure and formatting conventions of each doc
- Don't add version history or changelogs to individual doc files
- If a doc section is accurate, leave it alone — don't rewrite for style
- TradingView selectors are HIGH CHURN — document them in `task-context.md`, not in architecture docs
- When updating symbol/alert counts, verify against `tte/data/symbols.py` and `combo_settings.yaml`, not from memory
