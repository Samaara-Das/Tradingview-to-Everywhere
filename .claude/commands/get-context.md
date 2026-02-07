---
description: Get context about what was done in previous sessions
allowed-tools: Read, TaskList, TaskGet, Bash
---

Get context about what you did last by:

1. Reading the `.claude/task-context.md` file for session notes and implementation details
2. Running `TaskList` to see all current tasks and their statuses and using the task master ai MCP. Use whichever task system is being used currently.
3. Looking at recent git commits with `git log --oneline -10`

After gathering this context, provide a summary of:
- What tasks are completed, in progress, and pending
- Key decisions and patterns discovered
- What to work on next
