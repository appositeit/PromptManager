#!/usr/bin/env python3
"""
Test script to verify that integration tests create files in the correct location.
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add project root to path so we can import src modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

def test_prompt_service_config():
    """Test that PromptService respects the test environment variable."""
    
    # Set up test environment
    test_config_fd, test_config_path = tempfile.mkstemp(suffix='.json', prefix='test_prompt_config_')
    
    try:
        # Create test config
        test_prompts_dir = str(Path(__file__).parent / "test_prompts")
        test_directories = [
            {
                "path": test_prompts_dir,
                "name": "Test Prompts", 
                "description": "Test prompts directory",
                "enabled": True
            }
        ]
        
        with os.fdopen(test_config_fd, 'w') as f:
            json.dump(test_directories, f, indent=2)
        
        # Set environment variable
        os.environ['PROMPT_MANAGER_CONFIG_FILE'] = test_config_path
        
        # Import and test PromptService
        from src.services.prompt_service import PromptService
        
        print(f"PromptService.CONFIG_FILE = {PromptService.CONFIG_FILE}")
        print(f"Expected: {test_config_path}")
        
        assert PromptService.CONFIG_FILE == test_config_path, f"Config file not set correctly"
        
        # Test creating a service
        service = PromptService(auto_load=False)
        directories = service._load_directories_from_config_file()
        
        print(f"Loaded directories: {directories}")
        assert len(directories) == 1, f"Expected 1 directory, got {len(directories)}"
        assert directories[0]['path'] == test_prompts_dir, f"Wrong directory path: {directories[0]['path']}"
        
        print("✅ PromptService configuration test passed!")
        
    finally:
        # Cleanup
        try:
            os.unlink(test_config_path)
        except FileNotFoundError:
            pass
        
        if 'PROMPT_MANAGER_CONFIG_FILE' in os.environ:
            del os.environ['PROMPT_MANAGER_CONFIG_FILE']


def test_directory_exists():
    """Test that the test prompts directory exists."""
    test_prompts_dir = Path(__file__).parent / "test_prompts"
    
    print(f"Checking directory: {test_prompts_dir}")
    print(f"Directory exists: {test_prompts_dir.exists()}")
    print(f"Is directory: {test_prompts_dir.is_dir()}")
    
    if test_prompts_dir.exists():
        files = list(test_prompts_dir.glob("*.md"))
        print(f"Markdown files in directory: {len(files)}")
        for file in files[:5]:  # Show first 5 files
            print(f"  - {file.name}")
    
    assert test_prompts_dir.exists(), f"Test prompts directory does not exist: {test_prompts_dir}"
    assert test_prompts_dir.is_dir(), f"Test prompts path is not a directory: {test_prompts_dir}"


if __name__ == "__main__":
    print("🧪 Testing prompt manager test configuration...")
    
    test_directory_exists()
    test_prompt_service_config()
    
    print("✅ All tests passed!")
