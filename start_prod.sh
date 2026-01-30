#!/bin/bash

# =============================================================================
# TTE Orchestrator - Production Start Script
# =============================================================================
# Usage: ./start_prod.sh [--foreground]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check for foreground flag
FOREGROUND=false
if [ "$1" == "--foreground" ]; then
    FOREGROUND=true
fi

echo -e "${BLUE}"
echo "=========================================="
echo "TTE Orchestrator - Production Mode"
echo "=========================================="
echo -e "${NC}"

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo -e "${RED}Error: .env.production not found!${NC}"
    echo "Copy .env.production.example and fill in your values."
    exit 1
fi

# Load environment variables
echo -e "${BLUE}Loading production environment...${NC}"
set -a
source .env.production
set +a

# Validate required variables
REQUIRED_VARS=("STOCK_BUDDY_API_URL" "CHROME_PROFILE_PATH")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}Error: $var is not set in .env.production${NC}"
        exit 1
    fi
done

# Create directories
echo -e "${BLUE}Creating directories...${NC}"
mkdir -p logs
mkdir -p screenshots

# Check if already running
if pgrep -f "tiered_main.py" > /dev/null; then
    echo -e "${YELLOW}Warning: Orchestrator is already running!${NC}"
    echo "PID: $(pgrep -f tiered_main.py)"
    read -p "Kill existing process and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "tiered_main.py"
        sleep 2
    else
        echo "Exiting."
        exit 0
    fi
fi

# Test API connection
echo -e "${BLUE}Testing API connection...${NC}"
API_HEALTH=$(curl -sf "${STOCK_BUDDY_API_URL}/health" 2>/dev/null || echo "FAILED")
if [[ "$API_HEALTH" == *"healthy"* ]]; then
    echo -e "${GREEN}API connection successful!${NC}"
else
    echo -e "${RED}API connection failed!${NC}"
    echo "URL: ${STOCK_BUDDY_API_URL}/health"
    echo "Response: $API_HEALTH"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python
echo -e "${BLUE}Checking Python environment...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 not found!${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Check dependencies
echo -e "${BLUE}Checking dependencies...${NC}"
python3 -c "import selenium; import requests" 2>/dev/null || {
    echo -e "${YELLOW}Missing dependencies. Installing...${NC}"
    pip install -r requirements.txt
}

# Start orchestrator
if [ "$FOREGROUND" = true ]; then
    echo -e "${GREEN}Starting orchestrator in foreground...${NC}"
    echo "Press Ctrl+C to stop"
    echo ""
    python3 tiered_main.py
else
    echo -e "${GREEN}Starting orchestrator in background...${NC}"
    nohup python3 tiered_main.py > logs/orchestrator_stdout.log 2>&1 &
    PID=$!

    # Wait a moment and check if still running
    sleep 3
    if ps -p $PID > /dev/null; then
        echo -e "${GREEN}Orchestrator started successfully!${NC}"
        echo ""
        echo "PID: $PID"
        echo "Main log: logs/orchestrator.log"
        echo "Stdout log: logs/orchestrator_stdout.log"
        echo ""
        echo -e "${YELLOW}Commands:${NC}"
        echo "  View logs: tail -f logs/orchestrator.log"
        echo "  Stop: kill $PID"
        echo "  Status: ps aux | grep tiered_main.py"

        # Save PID to file
        echo $PID > logs/orchestrator.pid
    else
        echo -e "${RED}Orchestrator failed to start!${NC}"
        echo "Check logs/orchestrator_stdout.log for errors"
        cat logs/orchestrator_stdout.log
        exit 1
    fi
fi
