#!/bin/bash

# Restart script for Prompt Manager MCP Server
# AI-generated on 2025-06-07

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Restarting Prompt Manager MCP Server..."

# Stop the server
"$SCRIPT_DIR/stop_mcp_server.sh"

# Wait a moment
sleep 1

# Start the server
"$SCRIPT_DIR/start_mcp_server.sh"
