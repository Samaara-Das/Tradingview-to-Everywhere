---
name: prd
description: "Use this skill whenever the user wants to create, update, review, or work with Product Requirements Documents (PRDs). Triggers include: any mention of 'PRD', 'product requirements', 'requirements document', 'spec', 'product spec', 'feature spec', or requests to plan/document a product or feature. Also use when the user wants to: define project scope, document user stories, outline technical requirements, create acceptance criteria, or prepare documentation for development teams. If the user mentions Task Master, taskmaster, or wants to generate tasks from requirements, this skill integrates directly with that workflow. Use this skill proactively when users discuss new projects, features, or products—even if they don't explicitly ask for a PRD."
---

# PRD Creation and Management

Create professional, actionable Product Requirements Documents that translate ideas into clear development roadmaps.

## Quick Reference

| Task | Action |
|------|--------|
| New PRD from idea | Interview → Draft → Review → Finalize |
| Update existing PRD | Load → Identify changes → Integrate → Validate |
| PRD for Task Master | Create PRD → Save to `.taskmaster/docs/prd.txt` → Parse |

## When to Use This Skill

- User describes a new product, feature, or project idea
- User asks for "requirements", "spec", or "PRD"
- User wants to plan development work
- User mentions integrating with Task Master
- User has scattered notes/ideas to consolidate into actionable requirements

---

## PRD Creation Workflow

### Phase 1: Discovery Interview (Iterative — Do NOT Skip)

**CRITICAL**: Never assume UI behavior, interaction logic, or business rules. Ask first. The goal is to leave ZERO ambiguity before drafting. This phase is **iterative** — ask questions in rounds until every detail is nailed down. Do NOT batch all questions at once; group them into focused rounds of 3-5 questions max using the AskUserQuestion tool.

**Round 1 — Problem & Scope** (always ask):
1. **Problem Statement**: What problem does this solve? Who experiences it?
2. **Scope**: What's in v1 vs future versions?
3. **Existing Features**: Does this modify, replace, or extend anything that already exists in the app? If so, what exactly changes vs stays the same?

**Round 2 — Behavior & Logic** (always ask, tailored to the feature):
Before asking these, read the relevant existing code/components to understand what currently exists. Then ask pin-pointed questions about:

4. **Exact Interaction**: Walk through the user's action step by step. What does the user click/tap? What happens visually? What happens to the data?
5. **State & Defaults**: What is the default state? What options are available? Can the user reset/clear?
6. **Business Rules**: What are the exact rules? (e.g., "What makes two setups 'different'?", "When should X appear vs be hidden?", "What order should items sort in?")
7. **Edge Cases**: What happens when the list is empty? When there's only 1 item? When the user has no data? When the data is stale?

**Round 3 — UI & Visual Specifics** (ask for any feature with a visual component):
8. **Layout**: Where exactly does this appear? Left/right/top/bottom? Inside which panel? What size?
9. **Existing UI Elements**: Are there buttons, labels, or components that already exist in this area that should be kept, removed, or moved? (e.g., "The 'View Analysis' button already exists — should it stay?")
10. **Visual Treatment**: Colors, icons, hover states, active states? Does it match an existing pattern in the app or is it new?
11. **Responsive Behavior**: Does it change on mobile vs desktop?

**Round 4 — Data & Integration** (ask when backend/data is involved):
12. **Data Source**: Where does the data come from? Existing collection, new collection, API?
13. **Data Shape**: What fields are needed? What are the types? Any computed/derived values?
14. **Uniqueness/Dedup**: How do we tell if two items are the "same"? What fields form the unique key?
15. **Persistence**: Is this stored permanently, cached, or ephemeral? What collection? What indexes?
16. **Performance**: How many items could there be? Do we need pagination, batching, or limits?

**Round 5 — Confirmation** (always do before drafting):
17. **Summarize back** your understanding of the feature in 3-5 bullet points and ask the user to confirm or correct.
18. **List any assumptions** you're making and explicitly ask the user to validate each one.

**Rules for the Discovery Interview**:
- **NEVER assume a behavior** — if the user says "add a dropdown" and doesn't specify what happens when an option is selected, ASK.
- **NEVER assume UI layout** — if the user says "show pinned items first", ask whether pinned items should be visually separated, highlighted, or just sorted to the top.
- **ALWAYS audit existing features** — before asking questions, read the relevant components/code to understand what currently exists. Ask whether existing elements (buttons, labels, sections) should be kept, modified, or removed.
- **Ask about EACH interaction**, not just the happy path. What happens on hover? On click? On long-press? On deselect?
- **Use concrete examples** in your questions: "If the user has EURUSD pinned and filters by 'US Stocks', should EURUSD still show in the pinned section?"

### Phase 2: Draft Structure

Use this template structure, adapting sections based on project complexity:

```markdown
# [Product/Feature Name] - Product Requirements Document

## Document Info
- **Version**: 1.0
- **Last Updated**: [Date]
- **Author**: [Name]
- **Status**: Draft | In Review | Approved

---

## 1. Overview

### 1.1 Problem Statement
[2-3 sentences describing the problem this solves]

### 1.2 Proposed Solution
[Brief description of what we're building]

### 1.3 Goals & Success Metrics
| Goal | Metric | Target |
|------|--------|--------|
| [Goal 1] | [How measured] | [Target value] |

### 1.4 Out of Scope
- [Explicit exclusions to prevent scope creep]

---

## 2. User Stories & Requirements

### 2.1 User Personas
**[Persona Name]**
- Role: [Their role]
- Goals: [What they want to achieve]
- Pain Points: [Current frustrations]

### 2.2 User Stories

#### Epic: [Epic Name]

| ID | Story | Priority | Acceptance Criteria |
|----|-------|----------|---------------------|
| US-001 | As a [persona], I want to [action] so that [benefit] | P0/P1/P2 | - [ ] Criterion 1<br>- [ ] Criterion 2 |

---

## 3. Functional Requirements

### 3.1 [Feature Area 1]

**FR-001: [Requirement Name]**
- **Description**: [What it does]
- **Input**: [What it receives]
- **Output**: [What it produces]
- **Business Rules**: [Constraints and logic]
- **Error Handling**: [What happens when things fail]

---

## 4. Non-Functional Requirements

### 4.1 Performance
- [Response time requirements]
- [Throughput requirements]

### 4.2 Security
- [Authentication/Authorization]
- [Data protection]

### 4.3 Scalability
- [Expected load]
- [Growth projections]

### 4.4 Compatibility
- [Browsers/Devices/Platforms]
- [Integration requirements]

---

## 5. Technical Considerations

### 5.1 Architecture Overview
[High-level technical approach]

### 5.2 Dependencies
| Dependency | Purpose | Risk |
|------------|---------|------|
| [System/Library] | [Why needed] | [What if unavailable] |

### 5.3 Data Model
[Key entities and relationships]

---

## 6. UX/UI Requirements

### 6.1 User Flows
[Key user journeys]

### 6.2 Wireframes/Mockups
[Links or descriptions]

### 6.3 Design Constraints
[Brand guidelines, accessibility standards]

---

## 7. Release Planning

### 7.1 Milestones
| Phase | Deliverables | Target Date |
|-------|--------------|-------------|
| MVP | [Core features] | [Date] |
| v1.1 | [Enhancements] | [Date] |

### 7.2 Rollout Strategy
[How this will be deployed/released]

---

## 8. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [Risk] | High/Med/Low | High/Med/Low | [Strategy] |

---

## 9. Open Questions
- [ ] [Question 1]
- [ ] [Question 2]

---

## Appendix

### A. Glossary
| Term | Definition |
|------|------------|
| [Term] | [Definition] |

### B. References
- [Link to related docs]
```

### Phase 3: Adapt to Project Scale

**Micro PRD** (small features, 1-2 days work):
- Sections 1, 2.2, 3 only
- Single page, ~200-400 words

**Standard PRD** (medium features, 1-2 weeks):
- Sections 1-5, 7-9
- 2-4 pages

**Comprehensive PRD** (large projects, sprints/quarters):
- All sections
- May split into multiple documents

---

## PRD Quality Checklist

Before finalizing, verify:

**Clarity**
- [ ] No ambiguous language ("should", "might", "could" → use "must", "will")
- [ ] Technical terms defined in glossary
- [ ] Each requirement is testable

**Completeness**
- [ ] All user stories have acceptance criteria
- [ ] Edge cases documented
- [ ] Error states specified
- [ ] Out-of-scope items listed

**Actionability**
- [ ] Requirements are sized appropriately (not too large)
- [ ] Dependencies identified
- [ ] Priorities assigned (P0 = must have, P1 = should have, P2 = nice to have)

**Consistency**
- [ ] IDs are unique and sequential
- [ ] Formatting is consistent throughout
- [ ] Cross-references are accurate

---

## Updating Existing PRDs

When updating a PRD:

1. **Read the existing document completely** before making changes
2. **Increment the version number** (1.0 → 1.1 for minor, 1.0 → 2.0 for major)
3. **Update the "Last Updated" date**
4. **Add a changelog entry** at the top or bottom:

```markdown
## Changelog
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.1 | 2025-02-11 | [Name] | Added FR-015, updated US-003 acceptance criteria |
```

5. **Preserve existing IDs** — don't renumber; add new items with new IDs
6. **Mark deprecated requirements** instead of deleting:
   ```markdown
   ~~**FR-005: [Old Requirement]**~~ *Deprecated in v1.1 - replaced by FR-015*
   ```

---

## Task Master Integration

PRDs work seamlessly with Task Master for automated task generation.

### Workflow

1. **Create PRD** using this skill
2. **Save to Task Master location**:
   ```
   .taskmaster/docs/prd.txt
   ```
3. **Parse with Task Master**:
   ```
   Use task-master-ai:parse_prd with:
   - input: .taskmaster/docs/prd.txt
   - projectRoot: [absolute path]
   - numTasks: [appropriate for complexity, usually 10-20]
   ```

### PRD Format for Task Master

Task Master parses PRDs effectively when they:

- Use clear section headers (## and ###)
- Have explicit user stories with acceptance criteria
- Include prioritization (P0/P1/P2)
- List functional requirements with IDs
- Specify dependencies between features

### Recommended Task Count by PRD Size

| PRD Complexity | Sections | Suggested Tasks |
|---------------|----------|-----------------|
| Micro | 1-3 | 3-5 |
| Standard | 4-6 | 8-15 |
| Comprehensive | 7+ | 15-30 |

---

## Writing Tips

**Be Specific, Not Vague**
- ❌ "The system should be fast"
- ✅ "API responses must return within 200ms for 95th percentile"

**Use Active Voice**
- ❌ "The data will be validated"
- ✅ "The system validates input data against schema before processing"

**Quantify When Possible**
- ❌ "Support many users"
- ✅ "Support 10,000 concurrent users"

**Include Examples**
When a requirement could be interpreted multiple ways, add an example:
```markdown
**FR-010: Date Formatting**
Dates must display in user's locale format.
- Example (US): "02/11/2025"
- Example (UK): "11/02/2025"
- Example (ISO): "2025-02-11"
```

---

## Common Patterns by Domain

### Web Applications
Focus on: Routes, state management, responsive breakpoints, browser support, SEO requirements

### APIs
Focus on: Endpoints, request/response schemas, authentication, rate limiting, versioning strategy

### Mobile Apps
Focus on: Platform differences (iOS/Android), offline behavior, push notifications, app store requirements

### Trading/Finance Systems
Focus on: Data accuracy, latency requirements, regulatory compliance, audit trails, risk limits

### AI/ML Features
Focus on: Model inputs/outputs, accuracy targets, training data requirements, fallback behavior

---

## Example: Micro PRD

Here's a complete micro PRD for reference:

```markdown
# Dark Mode Toggle - PRD

## Overview
Add a dark mode toggle to the settings page, allowing users to switch between light and dark themes.

**Goal**: Reduce eye strain for users working in low-light environments
**Success Metric**: 30% adoption within 30 days of launch

## User Stories

| ID | Story | Priority | Acceptance Criteria |
|----|-------|----------|---------------------|
| US-001 | As a user, I want to toggle dark mode so I can reduce eye strain | P0 | - [ ] Toggle visible in settings<br>- [ ] Preference persists across sessions<br>- [ ] Transition is smooth (no flash) |

## Requirements

**FR-001: Theme Toggle**
- Toggle switch in Settings → Appearance
- Default: Follow system preference
- Options: Light, Dark, System

**FR-002: Theme Persistence**
- Store preference in localStorage
- Apply on page load before render (prevent flash)

**NFR-001: Performance**
- Theme switch must complete in <100ms
- No layout shift during transition

## Out of Scope
- Custom color themes
- Scheduled automatic switching
```

---

## Handling Ambiguity

When user requirements are unclear:

1. **ASK the user directly** — do NOT assume and move on. Use the AskUserQuestion tool with specific options.
2. **Present concrete alternatives** with examples of how each would look/behave.
3. **Only flag for review in the PRD** if the user explicitly says "decide later" or "I'm not sure yet."

**WRONG approach** (do not do this):
```
Assuming CSV export is sufficient for v1.
> ⚠️ Confirm with stakeholder before development
```

**RIGHT approach** (ask immediately):
```
"For the export feature, which format do you need?"
- Option A: CSV (simple, opens in Excel)
- Option B: Excel (.xlsx) (formatted, with headers)
- Option C: JSON (for programmatic use)
- Option D: Multiple formats (user picks at export time)
```

Never write a PRD with unresolved assumptions. Every "I assumed X" is a question you should have asked.
