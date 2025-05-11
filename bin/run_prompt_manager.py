#!/usr/bin/env python3
"""
Run the prompt management system as a standalone server.

This script starts the prompt management system, which can be used to
create, manage, and utilize prompts for AI interactions.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Add src to the path
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# Import the main function from server.py
from server import main

if __name__ == "__main__":
    # Create default directories if needed
    config_dir = os.path.expanduser("~/.prompt_manager")
    os.makedirs(os.path.join(config_dir, "prompts"), exist_ok=True)
    
    # Create project data directories
    data_dir = os.path.join(project_root, "data")
    os.makedirs(os.path.join(data_dir, "prompts"), exist_ok=True)
    
    # Ensure logs directory exists
    os.makedirs(os.path.join(project_root, "logs"), exist_ok=True)
    
    # Run the server
    main()
