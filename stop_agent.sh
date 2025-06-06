#!/bin/bash

# AI Agent Stop Script
# This script stops the AI agent running in silent mode

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project directory
cd "$SCRIPT_DIR"

# Check if PID file exists
if [ -f "ai_agent.pid" ]; then
    PID=$(cat ai_agent.pid)
    
    # Check if process is still running
    if kill -0 $PID > /dev/null 2>&1; then
        echo "Stopping AI Agent (PID: $PID)..."
        kill $PID
        
        # Wait a moment and check if it's really stopped
        sleep 2
        if kill -0 $PID > /dev/null 2>&1; then
            echo "Process didn't stop gracefully, forcing kill..."
            kill -9 $PID
        fi
        
        echo "AI Agent stopped."
    else
        echo "AI Agent is not running (PID $PID not found)."
    fi
    
    # Remove PID file
    rm ai_agent.pid
else
    echo "No PID file found. AI Agent might not be running or wasn't started with run_silent.sh"
    
    # Try to find and kill any running app.py processes
    PIDS=$(pgrep -f "python.*app.py")
    if [ ! -z "$PIDS" ]; then
        echo "Found running app.py processes, stopping them..."
        echo $PIDS | xargs kill
        echo "Processes stopped."
    else
        echo "No running app.py processes found."
    fi
fi
