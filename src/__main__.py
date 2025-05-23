#!/usr/bin/env python3
"""
Command line entry point for the Prompt Manager server.
Handles argument parsing and delegates to server.main()
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.server import main

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Prompt Manager Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8081, help='Port to bind to')
    parser.add_argument('--log-level', default='info', help='Log level')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    main(args)
