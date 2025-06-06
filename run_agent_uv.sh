#!/bin/bash

# AI Agent Silent Runner (UV Version)
# This script runs the AI agent system without any logging output using UV

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project directory
cd "$SCRIPT_DIR"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "UV is not installed. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Run the application silently using uv
echo "Starting AI Agent with UV (silent mode)..."
uv run python app.py > /dev/null 2>&1 &

# Get the process ID
PID=$!

# Create a PID file to track the process
echo $PID > ai_agent.pid

echo "AI Agent started silently with PID: $PID"
echo "To stop the agent, run: kill $PID"
echo "Or use the stop script: ./stop_agent.sh"
