#!/bin/bash

# =============================================================================
# TTE Orchestrator - Production Stop Script
# =============================================================================
# Usage: ./stop_prod.sh [--force]

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FORCE=false
if [ "$1" == "--force" ]; then
    FORCE=true
fi

echo -e "${YELLOW}Stopping TTE Orchestrator...${NC}"

# Check if PID file exists
if [ -f "logs/orchestrator.pid" ]; then
    PID=$(cat logs/orchestrator.pid)

    if ps -p $PID > /dev/null 2>&1; then
        if [ "$FORCE" = true ]; then
            echo "Force killing process $PID..."
            kill -9 $PID
        else
            echo "Gracefully stopping process $PID..."
            kill -SIGTERM $PID

            # Wait for process to exit
            for i in {1..30}; do
                if ! ps -p $PID > /dev/null 2>&1; then
                    break
                fi
                echo -n "."
                sleep 1
            done
            echo ""

            # Force kill if still running
            if ps -p $PID > /dev/null 2>&1; then
                echo -e "${YELLOW}Process didn't stop gracefully, force killing...${NC}"
                kill -9 $PID
            fi
        fi

        rm -f logs/orchestrator.pid
        echo -e "${GREEN}Orchestrator stopped.${NC}"
    else
        echo -e "${YELLOW}Process $PID not found (already stopped?)${NC}"
        rm -f logs/orchestrator.pid
    fi
else
    # Try to find process
    PID=$(pgrep -f "tiered_main.py" 2>/dev/null)

    if [ -n "$PID" ]; then
        echo "Found process $PID"
        if [ "$FORCE" = true ]; then
            kill -9 $PID
        else
            kill -SIGTERM $PID
        fi
        echo -e "${GREEN}Orchestrator stopped.${NC}"
    else
        echo -e "${YELLOW}No running orchestrator found.${NC}"
    fi
fi
