#!/bin/bash

# Stop script for Prompt Manager MCP Server
# Fixed for MCP STDIO communication - AI-generated on 2025-06-07

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Stopping Prompt Manager MCP Server..."

# Find MCP server processes by command pattern
PIDS=$(pgrep -f "python.*src\.mcp_server\.server" 2>/dev/null || true)

if [ -z "$PIDS" ]; then
    echo "No MCP server processes found"
    exit 0
fi

echo "Found MCP server process(es): $PIDS"

for PID in $PIDS; do
    echo "Stopping MCP server (PID: $PID)..."
    
    # Send TERM signal for graceful shutdown
    kill "$PID" 2>/dev/null || continue
    
    # Wait for graceful shutdown (up to 10 seconds)
    for i in {1..10}; do
        if ! kill -0 "$PID" 2>/dev/null; then
            echo "✓ MCP server (PID: $PID) stopped gracefully"
            break
        fi
        sleep 1
    done
    
    # Force kill if still running
    if kill -0 "$PID" 2>/dev/null; then
        echo "Forcing termination of MCP server (PID: $PID)..."
        kill -9 "$PID" 2>/dev/null || true
        echo "✓ MCP server (PID: $PID) forcefully terminated"
    fi
done

# Clean up any stale PID files
rm -f "$PROJECT_DIR/.mcp_server.pid"

echo "✓ All MCP server processes stopped"