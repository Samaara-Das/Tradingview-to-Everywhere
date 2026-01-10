#!/usr/bin/env python3
"""
Updates the task-context.md file after each Claude Code response.
This hook is triggered on 'Stop' event.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

def update_task_context():
    """Update task context with information from the latest interaction"""

    # Get the project root (assumes script is in .claude/scripts/)
    project_root = Path(__file__).parent.parent.parent
    context_file = project_root / ".claude" / "task-context.md"

    # Read stdin for hook data (optional - can be used for more sophisticated updates)
    try:
        hook_data = json.load(sys.stdin)
    except:
        hook_data = {}

    # Read existing context
    if context_file.exists():
        content = context_file.read_text(encoding='utf-8')
    else:
        return  # File doesn't exist yet

    # Update the "Last Updated" timestamp
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('**Last Updated**:'):
            lines[i] = f'**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            break

    # Write updated content
    context_file.write_text('\n'.join(lines), encoding='utf-8')

if __name__ == "__main__":
    update_task_context()
