#!/bin/bash

# AI Agent Silent Runner
# This script runs the AI agent system without any logging output

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project directory
cd "$SCRIPT_DIR"

# Check if virtual environment exists, if not create one
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies if needed
if [ ! -f ".venv/installed" ]; then
    echo "Installing dependencies..."
    pip install -e . > /dev/null 2>&1
    touch .venv/installed
fi

# Run the application silently (no output)
echo "Starting AI Agent (silent mode)..."
python app.py > /dev/null 2>&1 &

# Get the process ID
PID=$!

# Create a PID file to track the process
echo $PID > ai_agent.pid

echo "AI Agent started silently with PID: $PID"
echo "To stop the agent, run: kill $PID"
echo "Or use the stop script: ./stop_agent.sh"
