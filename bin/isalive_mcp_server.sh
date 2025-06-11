#!/bin/bash

# Check if Prompt Manager MCP Server is running
# Fixed for MCP STDIO communication - AI-generated on 2025-06-07

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Find MCP server processes by command pattern
PIDS=$(pgrep -f "python.*src\.mcp_server\.server" 2>/dev/null || true)

if [ -z "$PIDS" ]; then
    echo "✗ MCP server is not running"
    exit 1
fi

# Check if we have multiple processes (shouldn't happen normally)
PID_COUNT=$(echo "$PIDS" | wc -w)
if [ "$PID_COUNT" -gt 1 ]; then
    echo "! Multiple MCP server processes found: $PIDS"
    echo "Consider stopping and restarting the server"
    exit 2
fi

PID="$PIDS"
echo "✓ MCP server is running (PID: $PID)"

# Verify it's actually responding (optional - requires nc/netcat)
if command -v nc >/dev/null 2>&1; then
    # Try a quick connection test to see if it's listening
    if timeout 2 nc -z localhost 8083 2>/dev/null; then
        echo "  Server is accepting connections on port 8083"
    else
        echo "  Warning: Server process exists but may not be listening on port 8083"
    fi
fi

exit 0