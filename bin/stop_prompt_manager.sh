#!/bin/bash

# Script to gracefully stop the Prompt Manager server
# If it doesn't exit within the timeout, it will be forcefully killed

PORT=8081
TIMEOUT=5 # seconds
SERVER_PID=""

# Get the server PID
get_server_pid() {
    # SERVER_PID=$(pgrep -f "uvicorn server:app.*:$PORT")
    SERVER_PID=$(lsof -t -i :8081)
    if [ -z "$SERVER_PID" ]; then
        echo "No Prompt Manager server found running on port $PORT"
        exit 0
    fi
    echo "Found Prompt Manager server running with PID $SERVER_PID"
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
    echo "Waiting for server to terminate (timeout: $TIMEOUT seconds)..."
    
    while kill -0 $SERVER_PID 2>/dev/null; do
        sleep 1
        waited=$((waited + 1))
        
        if [ $waited -ge $TIMEOUT ]; then
            echo "Server did not terminate within timeout period ($TIMEOUT seconds)"
            echo "This may indicate a bug in the graceful shutdown process"
            echo "Forcefully killing server process..."
            kill -9 $SERVER_PID
            echo "Server process forcefully terminated"
            return 1
        fi
    done
    
    echo "Server terminated gracefully"
    return 0
}

# Main execution
get_server_pid

if [ -n "$SERVER_PID" ]; then
    if graceful_shutdown; then
        wait_for_termination
    else
        echo "Falling back to normal termination signal"
        kill $SERVER_PID
        wait_for_termination
    fi
fi

# Final check to make sure no server processes are left
# REMAINING_PIDS=$(pgrep -f "uvicorn server:app.*:$PORT")
REMAINING_PIDS=$(lsof -t -i :8081)
if [ -n "$REMAINING_PIDS" ]; then
    echo "WARNING: Some server processes still running. Forcefully terminating them..."
    echo $REMAINING_PIDS | xargs kill -9
    echo "All server processes terminated"
fi

echo "Prompt Manager server shutdown complete"
