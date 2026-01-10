#!/bin/bash

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Send Windows notification via PowerShell script
powershell.exe -ExecutionPolicy Bypass -File "$SCRIPT_DIR/scripts/notify.ps1" -Title "Claude Code" -Message "Response ready" &

exit 0
