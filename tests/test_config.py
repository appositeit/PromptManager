"""
Test configuration utilities to ensure tests use the correct directories.
"""

import os
import tempfile
import json
from pathlib import Path


def setup_test_environment():
    """
    Set up test environment with isolated configuration.
    This should be called at the start of any integration test that creates prompts.
    """
    # Create a temporary config file for tests
    test_config_dir = Path(__file__).parent / "temp_config"
    test_config_dir.mkdir(exist_ok=True)
    
    test_config_file = test_config_dir / "test_prompt_directories.json"
    
    # Configure only the test directory
    test_directories = [
        {
            "path": str(Path(__file__).parent / "test_prompts"),
            "name": "Test Prompts",
            "description": "Test prompts directory",
            "enabled": True
        }
    ]
    
    with open(test_config_file, 'w') as f:
        json.dump(test_directories, f, indent=2)
    
    # Set environment variable to override config file location
    os.environ['PROMPT_MANAGER_CONFIG_FILE'] = str(test_config_file)
    
    return str(test_config_file)


def cleanup_test_environment():
    """Clean up test environment."""
    if 'PROMPT_MANAGER_CONFIG_FILE' in os.environ:
        config_file = os.environ['PROMPT_MANAGER_CONFIG_FILE']
        try:
            os.unlink(config_file)
        except FileNotFoundError:
            pass
        del os.environ['PROMPT_MANAGER_CONFIG_FILE']


def get_test_prompts_directory():
    """Get the path to the test prompts directory."""
    return str(Path(__file__).parent / "test_prompts")
