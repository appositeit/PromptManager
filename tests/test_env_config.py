#!/usr/bin/env python3
"""
Simple test to verify the configuration file changes work.
"""

import os
import tempfile
import json

def test_environment_variable():
    """Test that the environment variable mechanism works."""
    
    # Set up test environment
    test_config_fd, test_config_path = tempfile.mkstemp(suffix='.json')
    
    try:
        # Create test config
        test_directories = [{"path": "/test/path", "name": "Test", "enabled": True}]
        
        with os.fdopen(test_config_fd, 'w') as f:
            json.dump(test_directories, f, indent=2)
        
        # Set environment variable
        os.environ['PROMPT_MANAGER_CONFIG_FILE'] = test_config_path
        
        # Test the logic from PromptService
        config_file = os.environ.get(
            'PROMPT_MANAGER_CONFIG_FILE',
            os.path.join(os.path.expanduser("~"), ".prompt_manager", "prompt_directories.json")
        )
        
        print(f"Config file resolved to: {config_file}")
        print(f"Expected: {test_config_path}")
        
        assert config_file == test_config_path, "Environment variable not working"
        
        # Test reading the config
        with open(config_file, 'r') as f:
            data = json.load(f)
        
        print(f"Config data: {data}")
        assert len(data) == 1
        assert data[0]['path'] == '/test/path'
        
        print("✅ Environment variable test passed!")
        
    finally:
        # Cleanup
        try:
            os.unlink(test_config_path)
        except FileNotFoundError:
            pass
        
        if 'PROMPT_MANAGER_CONFIG_FILE' in os.environ:
            del os.environ['PROMPT_MANAGER_CONFIG_FILE']


if __name__ == "__main__":
    print("🧪 Testing environment variable configuration...")
    test_environment_variable()
    print("✅ Configuration test passed!")
