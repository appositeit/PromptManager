#!/bin/bash

# Get the script directory to reliably find other scripts in the same directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Ensure we are in the project root for commands like start/stop that might assume it.
cd "$PROJECT_ROOT"

echo "Attempting to restart Prompt Manager server..."

# 1. Stop the server
echo "Stopping server (if running)..."
if ! "$SCRIPT_DIR/stop_prompt_manager.sh"; then
    # stop_prompt_manager.sh exits 0 if server not found, non-zero for other errors.
    # We can treat most stop issues as non-fatal for a restart attempt, 
    # as start_prompt_manager.sh has its own checks.
    echo "Warning: stop_prompt_manager.sh indicated an issue or server was not running. Proceeding with start attempt."
fi

# Brief pause to ensure port can be reused if it was just freed
sleep 1

# 2. Start the server in the background
echo "Starting server in background mode..."
# Pass along the port from this script if we want to make restart configurable, e.g. restart -p 8082
# For now, start_prompt_manager.sh will use its default or its own -p if set.
if ! "$SCRIPT_DIR/start_prompt_manager.sh" -b; then
    echo "ERROR: Failed to initiate server start with start_prompt_manager.sh -b."
    echo "Please check output from start_prompt_manager.sh or logs."
    exit 1
fi

# 3. Check if it's alive
# Allow a few seconds for the server to initialize fully before intensive checking.
echo "Waiting a few seconds for server to initialize..."
sleep 3 # Adjust as needed, start_prompt_manager.sh -b already sleeps for 1s.

echo "Checking server liveness..."
# isalive can take a -p PORT argument if needed, mirroring start_prompt_manager.sh
if ! "$SCRIPT_DIR/isalive_prompt_manager.sh" -t 5; then # 15-second timeout for liveness
    echo "ERROR: Server did not become alive within the timeout after restart."
    echo "Please check logs in $PROJECT_ROOT/artifacts/logs/prompt_manager.log (or the latest timestamped log)."
    exit 1
fi

echo "Prompt Manager server restarted successfully and is alive."
exit 0
