#!/bin/bash

# =============================================================================
# TTE Orchestrator - Status Check Script
# =============================================================================
# Usage: ./status_prod.sh

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "=========================================="
echo "TTE System Status"
echo "=========================================="
echo -e "${NC}"

# Load environment for API URL
if [ -f ".env.production" ]; then
    source .env.production
fi

# Check orchestrator
echo -e "${BLUE}Orchestrator:${NC}"
if [ -f "logs/orchestrator.pid" ]; then
    PID=$(cat logs/orchestrator.pid)
    if ps -p $PID > /dev/null 2>&1; then
        UPTIME=$(ps -p $PID -o etime= 2>/dev/null | tr -d ' ')
        echo -e "  Status: ${GREEN}Running${NC}"
        echo "  PID: $PID"
        echo "  Uptime: $UPTIME"
    else
        echo -e "  Status: ${RED}Stopped${NC} (stale PID file)"
    fi
else
    PID=$(pgrep -f "tiered_main.py" 2>/dev/null)
    if [ -n "$PID" ]; then
        echo -e "  Status: ${GREEN}Running${NC}"
        echo "  PID: $PID"
    else
        echo -e "  Status: ${RED}Stopped${NC}"
    fi
fi

# Check API
echo ""
echo -e "${BLUE}Stock Buddy API:${NC}"
if [ -n "$STOCK_BUDDY_API_URL" ]; then
    API_RESPONSE=$(curl -sf "${STOCK_BUDDY_API_URL}/health" 2>/dev/null)
    if [[ "$API_RESPONSE" == *"healthy"* ]]; then
        echo -e "  Status: ${GREEN}Healthy${NC}"
        echo "  URL: $STOCK_BUDDY_API_URL"
    else
        echo -e "  Status: ${RED}Unhealthy${NC}"
        echo "  URL: $STOCK_BUDDY_API_URL"
    fi

    # Check DB
    DB_RESPONSE=$(curl -sf "${STOCK_BUDDY_API_URL}/health/db" 2>/dev/null)
    if [[ "$DB_RESPONSE" == *"connected"* ]]; then
        echo -e "  Database: ${GREEN}Connected${NC}"
    else
        echo -e "  Database: ${RED}Disconnected${NC}"
    fi
else
    echo -e "  Status: ${YELLOW}Not configured${NC}"
    echo "  Set STOCK_BUDDY_API_URL in .env.production"
fi

# Check stats
echo ""
echo -e "${BLUE}Signal Statistics:${NC}"
if [ -n "$STOCK_BUDDY_API_URL" ]; then
    STATS=$(curl -sf "${STOCK_BUDDY_API_URL}/stats" 2>/dev/null)
    if [ -n "$STATS" ]; then
        TODAY=$(echo $STATS | grep -o '"today":[0-9]*' | cut -d: -f2)
        WEEK=$(echo $STATS | grep -o '"week":[0-9]*' | cut -d: -f2)
        PENDING=$(echo $STATS | grep -o '"pending":[0-9]*' | cut -d: -f2)
        echo "  Signals Today: ${TODAY:-0}"
        echo "  Signals This Week: ${WEEK:-0}"
        echo "  Hot List Pending: ${PENDING:-0}"
    else
        echo "  Unable to fetch stats"
    fi
fi

# Check logs
echo ""
echo -e "${BLUE}Recent Log Activity:${NC}"
if [ -f "logs/orchestrator.log" ]; then
    LOG_SIZE=$(du -h logs/orchestrator.log | cut -f1)
    LAST_MODIFIED=$(stat -c %y logs/orchestrator.log 2>/dev/null || stat -f %Sm logs/orchestrator.log 2>/dev/null)
    echo "  Log file: logs/orchestrator.log ($LOG_SIZE)"
    echo "  Last modified: $LAST_MODIFIED"
    echo ""
    echo "  Last 5 lines:"
    tail -5 logs/orchestrator.log | sed 's/^/    /'

    # Count recent errors
    ERRORS=$(grep -c "ERROR" logs/orchestrator.log 2>/dev/null || echo 0)
    if [ "$ERRORS" -gt 0 ]; then
        echo ""
        echo -e "  ${YELLOW}Errors in log: $ERRORS${NC}"
    fi
else
    echo "  No log file found"
fi

echo ""
echo -e "${BLUE}Commands:${NC}"
echo "  Start: ./start_prod.sh"
echo "  Stop:  ./stop_prod.sh"
echo "  Logs:  tail -f logs/orchestrator.log"
