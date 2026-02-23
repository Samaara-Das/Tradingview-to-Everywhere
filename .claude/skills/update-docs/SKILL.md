---
name: update-docs
description: "Use this skill after adding, removing, or changing features in Stock Buddy to update all project documentation. Triggers: 'update docs', 'sync docs', 'refresh docs', 'clean up docs', 'docs are outdated', 'update documentation', or when prompted to update docs after a feature change. Audits all doc files for accuracy, removes outdated content, adds missing info, and reminds about external doc sync."
---

# Stock Buddy — Documentation Updater

Keep all Stock Buddy documentation accurate, consistent, and free of outdated information after feature changes.

## Execution Mode

**IMPORTANT: Enter plan mode immediately when this skill is invoked.** Use `EnterPlanMode` before doing any work. The planning phase should complete Phase 1 (Gather Current State) and Phase 2 (Audit Each Doc) — presenting the user with a clear summary of what will be added, updated, removed, and flagged. Only after the user approves the plan should Phase 3 (Apply Updates) and beyond proceed.

## When to Run

Run this skill:
- After completing a feature, refactor, or significant bug fix
- When the user says docs need updating
- When reminded by post-task prompts to update documentation

## Document Categories

All documentation files are organized into tiers. Every tier must be audited.

### Tier 1: Primary Docs (always audit)
| File | Purpose | Content Guidelines |
|------|---------|-------------------|
| `CLAUDE.md` | AI assistant codebase guide | Architecture overview, file org tree, conventions, dev commands. Keep concise — loaded every session. |
| `README.md` | Project overview for GitHub | Tech stack, API endpoints, getting started. Public-facing. |
| `docs/USER_MANUAL.md` | End-user how-to guide | Step-by-step instructions with screenshots. Write for non-technical users. |
| `STOCK_BUDDY_PRD.md` | Product requirements | Milestones, roadmap, feature specs. Stakeholder audience. |

### Tier 2: Architecture & Feature Docs (audit when features change)
| File | Purpose | Content Guidelines |
|------|---------|-------------------|
| `docs/FEATURES.md` | Feature catalog with implementation details | One section per feature. Include: what it does, key files, data flow summary. |
| `docs/UI_COMPONENTS.md` | Component inventory with props and relationships | Group by view. Include component name, file path, key props, parent-child relationships. |
| `docs/DATA_FLOWS.md` | End-to-end data flow documentation | Mermaid sequence diagrams for each major flow. Trace: MongoDB -> Service -> API -> RTK Query -> Component. |
| `docs/LIMITATIONS.md` | Known limitations and placeholder features | What the app does NOT do yet. Verify each limitation against actual code before documenting. |

### Tier 3: Knowledge Base (audit when signal system changes)
| File | Purpose |
|------|---------|
| `docs/Nadaraya Watson.md` | NW signal type explanation (RAG source) |
| `docs/Order Block.md` | OB signal type explanation (RAG source) |
| `docs/Structure Break.md` | SB signal type explanation (RAG source) |
| `docs/Signal documents in Mongodb.md` | MongoDB signal document schema |
| `docs/indicators/nadaraya-watson-envelope.md` | NWE indicator logic |
| `docs/indicators/order-block-fvg.md` | OB/FVG indicator logic |
| `docs/indicators/kernel-ao-divergence-logic2.md` | Divergence indicator logic |

### Tier 4: Secondary / Reference Docs (audit when relevant)
| File | Purpose |
|------|---------|
| `src/components/watchlist/README.md` | Watchlist component architecture |
| `docs/google-doc-migration-summary.md` | Signal system migration reference |
| `docs/google-doc-content.md` | Google Doc content mirror |
| `docs/doc-inventory.md` | Documentation inventory and audit trail |

### External (sync manually)
| Location | Purpose |
|----------|---------|
| [Google Doc](https://docs.google.com/document/d/1Ocg1M-zuMg4hDtpjzIsuhc5lJzaA93-ydvcbGErurcc/edit?tab=t.0) | Shared with Rahul uncle for stakeholder visibility |

## Workflow

### Phase 1: Gather Current State (PLAN MODE)

1. Read `references/doc-inventory.md` to get the full list of documentation files
2. Read the git log for recent commits to understand what changed:
   ```
   git log --oneline -20
   ```
3. Read the current codebase state for areas that changed — check:
   - `src/app/` for new/removed pages and API routes
   - `src/components/` for new/removed/renamed components
   - `src/store/api/` for new/changed RTK Query APIs
   - `src/lib/` for new/changed services
   - `src/types/` for type changes
   - `src/hooks/` for new/changed hooks
   - `package.json` for dependency changes

### Phase 2: Audit Each Doc (PLAN MODE)

Audit **all tiers** of documentation. For each doc file, compare the documented state against the actual codebase.

#### Things to ADD
- New components, pages, API routes, services, hooks not yet documented
- New features or UI flows
- New environment variables
- New collections or data structures
- Changed file paths or renamed files

#### Things to REMOVE or UPDATE
- References to deleted files, components, or routes
- Descriptions of old behavior that no longer matches the code
- Outdated architecture descriptions
- Stale file trees that don't match actual structure
- Old feature descriptions that have been replaced
- References to deprecated or removed dependencies

#### Things to FLAG
- Screenshots in `docs/manual-screenshots/` that may show outdated UI
- Sections where the doc is ambiguous about current behavior
- Component READMEs (`src/components/*/README.md`, `src/lib/README-*.md`) that describe a structure different from what exists

#### Sync Checks
Perform these cross-document consistency checks:

1. **Knowledge Base PRD sync**: Compare signal-related content in `STOCK_BUDDY_PRD.md` with `docs/google-doc-content.md` — flag any discrepancies
2. **Doc inventory completeness**: Verify that `docs/doc-inventory.md` and `references/doc-inventory.md` list ALL `.md` files that actually exist in the repo. Run:
   ```
   find . -name "*.md" -not -path "./node_modules/*" -not -path "./.next/*"
   ```
   Flag any files missing from the inventory.
3. **Undocumented code**: Check for components, hooks, API routes, or services that are not mentioned in any documentation:
   - Components in `src/components/` not listed in `docs/UI_COMPONENTS.md`
   - Hooks in `src/hooks/` not mentioned in `CLAUDE.md` or `docs/FEATURES.md`
   - API routes in `src/app/api/` not listed in `CLAUDE.md`
   - Services in `src/lib/` not described in `CLAUDE.md`

### Present Plan and Exit Plan Mode

After completing Phase 1 and Phase 2, write a plan summarizing:
- **Files to update** with specific changes per file
- **Content to add** (new features, components, routes, etc.)
- **Content to remove** (outdated references, deleted files, stale descriptions)
- **Content to flag** (outdated screenshots, ambiguous sections)
- **Sync issues** (cross-document discrepancies)
- **Files to potentially delete** (stale docs for removed code)

Use `ExitPlanMode` to present this plan for user approval. Only proceed to Phase 3 after approval.

### Phase 3: Apply Updates (AFTER PLAN APPROVAL)

Update docs in this priority order:

1. **`CLAUDE.md`** — Most critical. This is what Claude reads every session.
   - Update the Architecture Overview if high-level structure changed
   - Update the File Organization tree to match actual files
   - Update component/service descriptions
   - Add/remove environment variables
   - Update any code patterns or conventions that changed
   - Keep the file well-organized — don't let sections bloat

2. **`docs/USER_MANUAL.md`** — User-facing guide.
   - Update step-by-step instructions for changed workflows
   - Add sections for new features
   - Remove sections for removed features
   - Flag screenshots that need re-capturing (add `<!-- SCREENSHOT OUTDATED: [reason] -->` comment)

3. **`STOCK_BUDDY_PRD.md`** — Product requirements.
   - Mark completed milestones
   - Update feature descriptions
   - Adjust roadmap if scope changed

4. **Architecture docs** (`FEATURES.md`, `UI_COMPONENTS.md`, `DATA_FLOWS.md`, `LIMITATIONS.md`)
   - `FEATURES.md`: Add/remove feature sections, update key files and data flow summaries
   - `UI_COMPONENTS.md`: Add/remove components, update props and relationships
   - `DATA_FLOWS.md`: Update Mermaid diagrams if service layer, API routes, or data paths changed. Use actual file names and function names.
   - `LIMITATIONS.md`: Remove limitations that have been resolved. Add new placeholder features. Verify each limitation against actual code.

5. **Knowledge base docs** — Only if signal types, indicators, or RAG system changed.

6. **Secondary docs** — Only if the change is relevant to that specific doc.

### Phase 4: Clean Up Stale Docs

Check for docs that should be deleted entirely:
- Component READMEs for components that no longer exist
- Migration docs for migrations that are long complete and no longer useful
- Any `.md` file in `src/` that describes code that has been removed

Before deleting, confirm with the user.

### Phase 5: Update Inventory

After all updates, ensure `references/doc-inventory.md` and `docs/doc-inventory.md` reflect the current state:
- Add any new doc files created
- Remove deleted doc files
- Update status and notes for modified docs

### Phase 6: Report and Remind

After all updates, provide a summary:

```
## Docs Updated
- CLAUDE.md: [what changed]
- USER_MANUAL.md: [what changed]
- FEATURES.md: [what changed]
- ...

## Flagged for Manual Action
- [ ] Screenshot XX needs re-capturing because [reason]
- [ ] Google Doc needs updating: [link] — sync these changes with Rahul uncle
- [ ] [Any other manual items]

## Sync Issues Found
- [ ] [Any cross-document discrepancies]

## Docs Reviewed (No Changes Needed)
- [list unchanged docs]
```

Always remind the user to:
1. **Update the Google Doc** shared with Rahul uncle: https://docs.google.com/document/d/1Ocg1M-zuMg4hDtpjzIsuhc5lJzaA93-ydvcbGErurcc/edit?tab=t.0
2. **Re-capture screenshots** if any were flagged as outdated
3. **Review the diff** before committing doc changes

## Content Guidelines by Doc Type

### CLAUDE.md
- Keep it concise and scannable — this is loaded into every Claude session
- Use tables for collections, API routes, and file listings
- Describe WHAT each file does, not HOW (implementation details go in architecture docs)
- Always include the File Organization tree and keep it accurate

### USER_MANUAL.md
- Write for non-technical users who have never used the app
- Use numbered steps for procedures
- Include screenshots where they help (mark outdated ones with HTML comments)
- Group by the 3-view navigation: Watchlist, Groups, Signals

### FEATURES.md
- One section per feature with: description, key files, data flow summary
- Group features by the view they belong to
- Include cross-feature interactions where relevant

### UI_COMPONENTS.md
- Group by view/area (Watchlist, Groups, Signals, Layout, etc.)
- For each component: file path, purpose, key props, parent components
- Include component hierarchy diagrams where helpful

### DATA_FLOWS.md
- Use Mermaid sequence diagrams with actual file names as participants
- Trace the full path: MongoDB -> Service -> API Route -> RTK Query -> Component
- Include flowcharts for branching logic (entry setup detection, cascade deletes, etc.)
- Document edge cases in text below each diagram

### LIMITATIONS.md
- For each limitation: current status, what exists, what's missing
- Reference actual file paths and line numbers where UI placeholders exist
- Categorize: Placeholder (UI exists, no backend) vs. Not Implemented (nothing exists)

## Important Rules

- Never fabricate documentation — only document what actually exists in the codebase
- When unsure whether something changed, read the actual source file before documenting it
- Keep `CLAUDE.md` concise — it's loaded into every session, so bloat wastes context
- Preserve the existing structure and formatting conventions of each doc
- Don't add version history or changelogs to individual doc files
- If a doc section is accurate, leave it alone — don't rewrite for style
- Use Mermaid diagrams in DATA_FLOWS.md — they render natively in GitHub and VS Code
