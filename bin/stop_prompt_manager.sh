#!/bin/bash

# Script to gracefully stop the Prompt Manager server
# If it doesn't exit within the timeout, it will be forcefully killed

PORT=8081
TIMEOUT=5 # seconds
SERVER_PID=""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_ROOT/logs/server.pid"

# Get the server PID
get_server_pid() {
    SERVER_PID="" # Reset SERVER_PID
    if [ -f "$PID_FILE" ]; then
        CANDIDATE_PID=$(cat "$PID_FILE")
        if ps -p "$CANDIDATE_PID" > /dev/null; then
            # Check if this PID is actually our server process
            if ps -o cmd= -p "$CANDIDATE_PID" | grep -q "python -m src.server.*--port $PORT"; then
                 echo "Found server PID $CANDIDATE_PID from $PID_FILE (verified process)"
                 SERVER_PID="$CANDIDATE_PID"
                 return
            else
                echo "PID $CANDIDATE_PID from $PID_FILE is running but command does not match. Stale/incorrect PID file?"
                # Not removing PID file here, pgrep will be tried next.
            fi
        else
            echo "Stale PID file found ($PID_FILE for PID $CANDIDATE_PID). Process not running. Removing PID file."
            rm -f "$PID_FILE"
        fi
    fi

    echo "PID file not used or process not verified. Trying to find server by process name and port $PORT using pgrep..."
    SERVER_PIDS_PGREP=$(pgrep -f "python -m src.server.*--port $PORT")

    if [ -n "$SERVER_PIDS_PGREP" ]; then
        SERVER_PID=$(echo "$SERVER_PIDS_PGREP" | head -n1)
        echo "Found Prompt Manager server running with PID $SERVER_PID (via pgrep)"
        return
    fi

    echo "pgrep failed. Trying to find server by port $PORT using lsof (less precise)..."
    SERVER_PID=$(lsof -t -i :$PORT 2>/dev/null)
    if [ -z "$SERVER_PID" ]; then
        echo "No Prompt Manager server found running on port $PORT (via any method)."
        exit 0
    fi
    echo "Found Prompt Manager server running with PID $SERVER_PID (via lsof)"
}

# Try to gracefully shut down the server
graceful_shutdown() {
    echo "Sending shutdown request to server..."
    RESPONSE=$(curl -s -X POST http://127.0.0.1:$PORT/api/shutdown)
    if [[ "$RESPONSE" == *"shutdown initiated"* ]]; then
        echo "Server shutdown initiated successfully"
        return 0
    else
        echo "Failed to initiate server shutdown via API"
        return 1
    fi
}

# Wait for server to terminate
wait_for_termination() {
    local waited=0
    local initial_pid_exists_and_matches=false
    if [ -f "$PID_FILE" ] && [ "$(cat $PID_FILE)" == "$SERVER_PID" ]; then
        initial_pid_exists_and_matches=true
    fi

    echo "Waiting for server process PID $SERVER_PID to terminate (timeout: $TIMEOUT seconds)..."
    
    while kill -0 "$SERVER_PID" 2>/dev/null; do
        sleep 1
        waited=$((waited + 1))
        
        if [ $waited -ge $TIMEOUT ]; then
            echo "Server PID $SERVER_PID did not terminate within timeout period ($TIMEOUT seconds)"
            echo "Forcefully killing server process PID $SERVER_PID..."
            kill -9 "$SERVER_PID"
            if [ "$initial_pid_exists_and_matches" = true ]; then
                 rm -f "$PID_FILE"
                 echo "PID file $PID_FILE removed after forceful kill."
            fi
            echo "Server process PID $SERVER_PID forcefully terminated"
            return 1 # Indicate forceful kill
        fi
    done
    
    if [ "$initial_pid_exists_and_matches" = true ]; then
        rm -f "$PID_FILE"
        echo "PID file $PID_FILE removed after graceful termination."
    fi
    echo "Server process PID $SERVER_PID terminated gracefully"
    return 0 # Indicate graceful or normal termination
}

# Main execution
get_server_pid # Sets SERVER_PID or exits if not found

if [ -n "$SERVER_PID" ]; then
    if graceful_shutdown; then
        wait_for_termination
    else
        echo "Graceful shutdown via API failed. Falling back to TERM signal for PID $SERVER_PID"
        kill "$SERVER_PID" # Send TERM signal
        wait_for_termination
    fi
fi

# Final check to make sure no server processes are left on the port
REMAINING_PIDS_LSOF=$(lsof -t -i :$PORT 2>/dev/null)
if [ -n "$REMAINING_PIDS_LSOF" ]; then
    echo "WARNING: Server process (PIDs $REMAINING_PIDS_LSOF) still running on port $PORT after shutdown attempt. Forcefully terminating..."
    # Use xargs to handle multiple PIDs if lsof returns them
    echo "$REMAINING_PIDS_LSOF" | xargs kill -9 2>/dev/null
    # Attempt to remove PID file again if it somehow wasn't or if it matches one of the killed PIDs
    if [ -f "$PID_FILE" ] && echo "$REMAINING_PIDS_LSOF" | grep -q "$(cat $PID_FILE)"; then
        echo "Removing PID file $PID_FILE as it matched a forcefully killed process."
        rm -f "$PID_FILE"
    fi
    echo "All server processes on port $PORT forcefully terminated."
else
    # If lsof finds nothing, ensure PID file is gone if it exists (e.g. process died before kill could remove it)
    if [ -f "$PID_FILE" ]; then
        echo "Final check: Server not running on port $PORT. Removing PID file $PID_FILE."
        rm -f "$PID_FILE"
    fi
fi

echo "Prompt Manager server shutdown sequence complete."
