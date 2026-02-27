# TTE Documentation Inventory

This is the canonical list of all documentation files in TradingView to Everywhere. The docs-updater agent and `/update-docs` skill use this to know what exists and what each file covers.

Last updated: February 2026 (V2 production)

---

## Tier 1: Primary Docs (always audit)

| File | Purpose | Audience | Update Frequency |
|------|---------|----------|-----------------|
| `CLAUDE.md` | Architecture, package structure, conventions, dev commands | Claude / developers | Every feature change |
| `README.md` | Project overview, setup, usage | Public / developers | Major feature changes |

## Tier 2: Architecture & Combo Docs (audit when features change)

| File | Purpose | Audience | Update Frequency |
|------|---------|----------|-----------------|
| `docs/combo/ARCHITECTURE.md` | Complete architecture — V2 changes, system overview, data flows | Developers | Architecture changes |
| `docs/combo/PRD.md` | Product requirements, implementation plan | Developers, stakeholders | New features, scope changes |
| `docs/combo/IMPLEMENTATION.md` | Implementation details and task tracking — **Archived** (all tasks completed Feb 2026) | Developers | During active development |

## Tier 3: Setup & Reference Docs (audit when relevant)

| File | Purpose | Audience | Update Frequency |
|------|---------|----------|-----------------|
| `docs/SETUP.md` | Installation and environment setup | New developers | Dependency/config changes |
| `docs/API.md` | Stock Buddy API integration | Developers | API/payload changes |
| `docs/DATABASE.md` | MongoDB collections and schemas | Developers | Schema changes |
| `docs/TROUBLESHOOTING.md` | Common issues and solutions | Developers, users | When new issues discovered |
| `docs/CONTRIBUTING.md` | Contribution guidelines | Contributors | Rarely |

## Tier 4: Technical Reference (audit when indicators change)

| File | Purpose | Notes |
|------|---------|-------|
| `docs/indicators/nadaraya-watson-envelope.md` | NWE indicator logic | Core signal type |
| `docs/indicators/order-block-fvg.md` | OB/FVG indicator logic | Core signal type |
| `docs/indicators/kernel-ao-divergence-logic2.md` | Divergence indicator logic | Removed in V2, kept for reference |
| `docs/STOCK_BUDDY_TECHNICAL_ARCHITECTURE.md` | Stock Buddy integration architecture | Cross-project reference |
| `docs/prds/backfill-snapshots.md` | Backfill snapshots PRD | Feature PRD |

## Tier 5: Agent & Coordination Docs

| File | Purpose | Notes |
|------|---------|-------|
| `.claude/agent-comms.md` | Stock Buddy agent coordination | V2 payload format spec |
| `.claude/task-context.md` | Session progress tracker | Updated each session |

## Configuration & Templates (not audited for content)

| File | Purpose |
|------|---------|
| `.claude/agents/docs-updater.md` | Docs updater agent definition |
| `.claude/agents/deploy.md` | Deploy agent definition |
| `.claude/agents/python-code-guardian.md` | Python code quality agent |
| `.claude/agents/qa.md` | QA agent definition |
| `.claude/agents/selenium-patterns.md` | Selenium patterns agent |
| `.claude/commands/*.md` | Claude Code commands |
| `.claude/skills/*/SKILL.md` | Skill definitions |

## Pine Script Files (reference, not doc files)

| File | Purpose |
|------|---------|
| `Pine Script Code/TTE Screener V2.txt` | **Active** — V2 screener with setup/exit tracking |
| `Pine Script Code/TTE Screener.txt` | Archived — V1 screener |
| `Pine Script Code/Trade Drawer.txt` | Trade Drawer v6 for chart snapshots |
