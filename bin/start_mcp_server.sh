#!/bin/bash

# Start script for Prompt Manager MCP Server
# Fixed for MCP STDIO communication - AI-generated on 2025-06-07

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR" >&2
    echo "Please create the virtual environment first:" >&2
    echo "  python -m venv $VENV_DIR" >&2
    echo "  source $VENV_DIR/bin/activate" >&2
    echo "  pip install -r requirements.txt" >&2
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Change to project directory
cd "$PROJECT_DIR"

# For MCP servers, we must NOT:
# - Background the process (no & or nohup)
# - Redirect stdout/stderr (MCP uses STDIO for communication)
# - Print anything to stdout (breaks MCP protocol)

# All user messages go to stderr so they don't interfere with MCP protocol
echo "Starting Prompt Manager MCP Server..." >&2
echo "Virtual environment: $VENV_DIR" >&2
echo "Working directory: $PROJECT_DIR" >&2
echo "Note: MCP server will communicate via STDIO" >&2

# Start the MCP server in foreground with clean STDIO
exec python -m src.mcp_server.server