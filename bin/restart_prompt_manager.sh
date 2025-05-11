#!/bin/bash

# Restart the prompt management system after changes

# Kill any existing prompt server processes
echo "Stopping existing prompt server..."
pkill -f "uvicorn server:app"

# Wait a moment for the process to terminate
sleep 2

# Start the server with the new changes
echo "Starting prompt server with new changes..."
cd /home/jem/development/prompt_manager
source venv/bin/activate 2>/dev/null || echo "Virtual environment not activated, using system Python"
python3 bin/run_prompt_manager.py --reload
