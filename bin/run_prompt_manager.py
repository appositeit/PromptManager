#!/usr/bin/env python3
"""
Run the prompt management system as a standalone server.

This script starts the prompt management system, which can be used to
create, manage, and utilize prompts for AI interactions.
"""

import os
import sys
import argparse

# Add the project to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Add src to the path
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# Import the main function from server.py
try:
    from src.server import main
except ImportError:
    try:
        from server import main
    except ImportError:
        print("Error: Cannot import main function from server.py")
        sys.exit(1)

if __name__ == "__main__":
    # Parse arguments and pass to main
    parser = argparse.ArgumentParser(description="Prompt Management System")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8081, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", type=str, 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
                        default="DEBUG", help="Log level")
    parser.add_argument("--log-file", type=str, default=None, 
                        help="Log file path (default: logs/prompt_manager.log)")
    
    args = parser.parse_args()
    
    # Create default directories if needed
    config_dir = os.path.expanduser("~/.prompt_manager")
    os.makedirs(os.path.join(config_dir, "prompts"), exist_ok=True)
    
    # Create project data directories
    data_dir = os.path.join(project_root, "data")
    os.makedirs(os.path.join(data_dir, "prompts"), exist_ok=True)
    
    # Ensure logs directory exists
    os.makedirs(os.path.join(project_root, "logs"), exist_ok=True)
    
    # Run the server with args
    main(args)
