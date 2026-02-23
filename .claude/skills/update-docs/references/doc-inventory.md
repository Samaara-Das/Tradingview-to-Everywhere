# Stock Buddy Documentation Inventory

This is the canonical list of all documentation files in Stock Buddy. The `/update-docs` skill uses this to know what exists and what each file covers.

Last updated: February 2026

---

## Tier 1: Primary Docs (always audit)

| File | Purpose | Audience | Update Frequency |
|------|---------|----------|-----------------|
| `CLAUDE.md` | Architecture, file org, conventions, dev commands | Claude / developers | Every feature change |
| `STOCK_BUDDY_PRD.md` | Product requirements, milestones, roadmap | Stakeholders, devs | New features, scope changes |
| `docs/USER_MANUAL.md` | End-user how-to guide with screenshots | End users | Every UI/feature change |

## Tier 2: Architecture & Feature Docs (audit when features change)

| File | Purpose | Audience | Update Frequency |
|------|---------|----------|-----------------|
| `docs/FEATURES.md` | Feature catalog with implementation details | Developers | New features, removed features |
| `docs/UI_COMPONENTS.md` | Component inventory with props and relationships | Developers | Component adds/removes/renames |
| `docs/DATA_FLOWS.md` | End-to-end data flows with Mermaid diagrams | Developers | Service/API/store changes |
| `docs/LIMITATIONS.md` | Known limitations and placeholder features | Developers, testers | When limitations are resolved or new ones added |

## Tier 3: Knowledge Base (audit when signal system changes)

| File | Purpose | Notes |
|------|---------|-------|
| `docs/Nadaraya Watson.md` | NW signal type explanation | RAG knowledge base source |
| `docs/Order Block.md` | OB signal type explanation | RAG knowledge base source |
| `docs/Structure Break.md` | SB signal type explanation | RAG knowledge base source |
| `docs/Signal documents in Mongodb.md` | MongoDB signal document schema | Reference for combo + legacy signals |
| `docs/indicators/nadaraya-watson-envelope.md` | NWE indicator logic | TTE combo system |
| `docs/indicators/order-block-fvg.md` | OB/FVG indicator logic | TTE combo system |
| `docs/indicators/kernel-ao-divergence-logic2.md` | Divergence indicator logic | TTE combo system |

### Knowledge Base Copies (in `src/lib/knowledge-base/`)

These are copies or derivatives used by the RAG system. They should stay in sync with the `docs/` originals:

| File | Mirrors |
|------|---------|
| `src/lib/knowledge-base/Nadaraya Watson.md` | `docs/Nadaraya Watson.md` |
| `src/lib/knowledge-base/Order Block.md` | `docs/Order Block.md` |
| `src/lib/knowledge-base/Structure Break.md` | `docs/Structure Break.md` |
| `src/lib/knowledge-base/Signal documents in Mongodb.md` | `docs/Signal documents in Mongodb.md` |
| `src/lib/knowledge-base/TTE-Integration.md` | TTE combo system overview (no docs/ mirror) |
| `src/lib/knowledge-base/OB-SB-NW-Strategy.md` | Trading strategy guide (no docs/ mirror) |
| `src/lib/knowledge-base/signal-interpretation.md` | Signal interpretation guide (no docs/ mirror) |
| `src/lib/knowledge-base/stock_buddy_prd.md` | PRD copy for RAG (mirrors `STOCK_BUDDY_PRD.md`) |
| `src/lib/knowledge-base/README.md` | Knowledge base index file |

## Tier 4: Secondary / Reference Docs (audit when relevant)

| File | Purpose | Notes |
|------|---------|-------|
| `src/components/watchlist/README.md` | Watchlist component architecture | Developer reference |
| `docs/google-doc-migration-summary.md` | Signal system migration reference | Historical — rarely changes |
| `docs/google-doc-content.md` | Google Doc content mirror | Sync with Google Doc |
| `docs/doc-inventory.md` | Documentation inventory and audit trail | Update after each docs audit |

## Configuration & Templates (not audited for content)

| File | Purpose |
|------|---------|
| `.claude/commands/post-commands.md` | Claude Code post-command hooks |
| `.claude/skills/update-docs/SKILL.md` | Update-docs skill definition |
| `.claude/skills/update-docs/references/doc-inventory.md` | This file |
| `.cursor/commands/create-new-branch.md` | Cursor branch creation command |
| `.github/pull_request_template.md` | PR template |
| `CLAUDE.local.md` | User's private project instructions (not committed) |

## External Doc (sync manually)

| Location | Purpose |
|----------|---------|
| [Google Doc](https://docs.google.com/document/d/1Ocg1M-zuMg4hDtpjzIsuhc5lJzaA93-ydvcbGErurcc/edit?tab=t.0) | Shared with Rahul uncle for stakeholder visibility |

## Screenshots

`docs/manual-screenshots/` contains numbered screenshots for the User Manual. Several have been deleted as outdated — see `docs/doc-inventory.md` for the list of screenshots needing re-capture.
