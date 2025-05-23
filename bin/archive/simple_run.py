#!/usr/bin/env python
"""
Simple script to run the prompt manager with fixed HTTP methods.
"""

import sys
from pathlib import Path
import uvicorn

# Get the absolute path to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
print(f"Project root: {PROJECT_ROOT}")

# Add project root to Python path
sys.path.insert(0, str(PROJECT_ROOT))

if __name__ == "__main__":
    # Run the server without reload
    print("Starting Prompt Manager on 127.0.0.1:8082")
    uvicorn.run(
        "src.simple_server:app",
        host="127.0.0.1",
        port=8082,  # Using a different port to avoid conflicts
        reload=False  # Disable auto-reload to avoid multiprocessing issues
    )
