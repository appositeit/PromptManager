#!/bin/bash

cd /home/jem/development/prompt_manager
# Restart the prompt management system after changes
./bin/stop_prompt_manager.sh

# # Kill any existing prompt server processes

# echo "Stopping existing prompt server processes..."
# pkill -f "uvicorn server:app" || true
# pkill -f "src.server" || true
# pkill -f "prompt_manager" || true

# # Check if port 8081 is still in use
# if lsof -i :8081 > /dev/null; then
    # echo "Port 8081 is still in use. Attempting to kill processes..."
    # kill -9 $(lsof -t -i :8081) || true
    # sleep 1
# fi

# # Double check port availability
# if lsof -i :8081 > /dev/null; then
    # echo "ERROR: Unable to free port 8081. Please check manually."
    # exit 1
# fi

# # Wait a moment for the processes to terminate
# sleep 2

# Start the server with the new changes
echo "Starting prompt server with new changes..."
cd /home/jem/development/prompt_manager
./bin/start_prompt_manager.sh
