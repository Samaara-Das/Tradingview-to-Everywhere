---
description: Update the task-context.md file with current progress and notes
argument-hint: [what to update]
allowed-tools: Read, Write, Edit, TaskList
---

You are updating the task context file to maintain session continuity.

Update instructions: $ARGUMENTS

## Task

1. Read the current `.claude/task-context.md` file
2. Run `TaskList` or task master ai mcp get to get current task statuses. Use the task system that is being used currently
3. Update the context file based on the instructions: $ARGUMENTS
4. If no specific instructions provided, ask what should be updated:
   - Completed tasks?
   - New accomplishments?
   - Current challenges/blockers?
   - Bugs that were fixed?
   - Important decisions made?
   - Next steps?

5. Update the "Last Updated" timestamp to today's date
6. Sync the Task Progress Summary with the actual TaskList status
7. Keep the format consistent and organized
8. Preserve all existing information unless explicitly asked to remove it

## Format Guidelines

Maintain these sections:
- **Current Task**: The active task being worked on
- **Task Progress Summary**: Completed/In Progress/Pending tasks
- **Session History**: Chronological log of what was done and how
- **Important Decisions Made**: Architectural/design choices
- **Key Reference Files**: Important files for the project
- **Verified Patterns**: Working selectors, commands, patterns discovered
- **Test Commands**: Commands to run/test the project

## Important guidelines
- Do NOT hallucinate or make up information
- Only document what actually happened in conversations
- Include actual error messages and code snippets where relevant
- Reference specific file paths when applicable
- Keep the documentation concise but comprehensive
