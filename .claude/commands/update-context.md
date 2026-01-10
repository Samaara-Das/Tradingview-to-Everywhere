---
description: Update the task-context.md file with current progress and notes
argument-hint: [what to update]
allowed-tools: Read, Write, Edit
---

You are updating the task context file to maintain session continuity.

Update instructions: $ARGUMENTS

## Task

1. Read the current `.claude/task-context.md` file
2. Update it based on the instructions: $ARGUMENTS
3. If no specific instructions provided, ask what should be updated:
   - Completed subtasks?
   - New accomplishments?
   - Current challenges/blockers?
   - Bugs that were fixed?
   - Important decisions made?
   - Next steps?

4. Update the "Last Updated" timestamp
5. Keep the format consistent and organized
6. Preserve all existing information unless explicitly asked to remove it

## Format Guidelines

Maintain these sections:
- **Current Task Master Task**: High-level task
- **Task Progress Summary**: Completed/In Progress/Pending subtasks
- **Recent Accomplishments**: What's been done
- **Current Challenges / Blockers**: What's blocking progress
- **Bugs Fixed**: Issues resolved
- **Important Decisions Made**: Architectural/design choices
- **Next Steps**: What to do next
- **Notes**: Additional context

## Example Updates

If user says: "completed market data MCP server, now working on indicators"

Update:
- Move "market data MCP server" to Completed Subtasks
- Add "indicator calculations" to In Progress Subtasks
- Add to Recent Accomplishments: "Implemented market data MCP server with proper error handling"
- Update Next Steps: "Complete indicator calculation module"
