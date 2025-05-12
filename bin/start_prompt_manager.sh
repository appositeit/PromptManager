#!/bin/bash
# Start script for the Prompt Manager
# This script handles virtual environment setup, path configuration, and server startup

set -e

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_ROOT"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Generate timestamp for logs
TIMESTAMP=$(date +'%Y%m%d%H%M%S')
LOG_FILE="$PROJECT_ROOT/logs/prompt_manager_${TIMESTAMP}.log"

# Create a symlink to the latest log file
if [ -L "$PROJECT_ROOT/logs/prompt_manager.log" ]; then
    rm "$PROJECT_ROOT/logs/prompt_manager.log"
fi
ln -s "$LOG_FILE" "$PROJECT_ROOT/logs/prompt_manager.log"

# Set up virtual environment if it doesn't exist
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "Setting up virtual environment..."
    python -m venv "$PROJECT_ROOT/venv"
    
    echo "Installing dependencies..."
    source "$PROJECT_ROOT/venv/bin/activate"
    pip install -r "$PROJECT_ROOT/requirements.txt"
else
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Check for existing server
if netstat -tuln | grep -q ":8081 "; then
    echo "Server is already running on port 8081."
    echo "To shut down the existing server, run: curl -X POST http://localhost:8081/api/shutdown"
    echo "Or use: lsof -i :8081 to find the process and kill it."
    exit 1
fi

# Create a timestamped version of the log file
echo "Logs will be written to $LOG_FILE"

# Start the server
echo "Starting Prompt Manager on http://localhost:8081"

# Use the main server.py instead of the temporary simple_run.py
PYTHONPATH="$PROJECT_ROOT" exec python -m src.server --host localhost --port 8081 --log-file "$LOG_FILE" 2>&1 | tee -a "$LOG_FILE"
