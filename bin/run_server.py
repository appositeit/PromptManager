#!/usr/bin/env python
"""
Script to run the Prompt Manager server.

This script initializes and runs the Prompt Manager server.
"""

import os
import sys
import argparse
import uvicorn
from pathlib import Path

# Add project directory to Python path for imports to work
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Set up argument parser
parser = argparse.ArgumentParser(description="Run Prompt Manager Server")
parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address")
parser.add_argument("--port", type=int, default=8081, help="Port number")
parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
parser.add_argument("--log-level", type=str, default="info", help="Log level")

# Parse command line arguments
args = parser.parse_args()

# Make sure log directory exists
log_dir = os.path.join(project_root, "logs")
os.makedirs(log_dir, exist_ok=True)

# Set up and run the server
if __name__ == "__main__":
    print(f"Starting Prompt Manager server on {args.host}:{args.port}")
    uvicorn.run(
        "src.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )
