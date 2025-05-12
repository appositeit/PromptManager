#!/usr/bin/env python
"""
Corrected script to run the prompt manager with proper imports.
"""

import os
import sys
import argparse
from pathlib import Path
import uvicorn
import logging
import multiprocessing
from datetime import datetime

# Add freeze support for multiprocessing
multiprocessing.freeze_support()

# Get the absolute path to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
print(f"Project root: {PROJECT_ROOT}")

# Add project root to Python path
sys.path.insert(0, str(PROJECT_ROOT))

# Set up the argument parser
parser = argparse.ArgumentParser(description="Run the Prompt Manager")
parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
parser.add_argument("--port", type=int, default=8081, help="Port to bind to")
parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
parser.add_argument("--log-level", choices=["debug", "info", "warning", "error"], default="info", help="Log level")
args = parser.parse_args()

# Set up logging
log_dir = PROJECT_ROOT / "logs"
os.makedirs(log_dir, exist_ok=True)

# Create a timestamped log file
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
log_file = log_dir / f"prompt_manager_{timestamp}.log"

# Create a symlink to the latest log
latest_log = log_dir / "prompt_manager.log"
if os.path.exists(latest_log):
    os.unlink(latest_log)
os.symlink(log_file, latest_log)

# Configure logging
logging.basicConfig(
    level=getattr(logging, args.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Main function
def main():
    # Run the server
    print(f"Starting Prompt Manager on {args.host}:{args.port}")
    uvicorn.run(
        "src.simple_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )

if __name__ == "__main__":
    main()
