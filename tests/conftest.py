import sys
import os
import asyncio
import pytest
import nest_asyncio
import json
import tempfile
from pathlib import Path

# Ensure src/ is on sys.path for all tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Session-scoped event loop for pytest-asyncio 0.21.x compatibility
@pytest.fixture(scope="session")
def event_loop():
    """
    Creates a session-scoped event loop with nest_asyncio support.
    
    This fixes "RuntimeError: This event loop is already running" errors
    by allowing nested event loops using nest_asyncio.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Automatically set up test environment for all tests.
    This ensures tests use the test prompts directory instead of production directories.
    """
    # Check if we're running tests
    if "PYTEST_CURRENT_TEST" in os.environ:
        # Create temporary config file for tests
        test_config_fd, test_config_path = tempfile.mkstemp(suffix='.json', prefix='test_prompt_config_')
        
        try:
            # Configure only the test directory
            test_prompts_dir = str(Path(__file__).parent / "test_prompts")
            test_directories = [
                {
                    "path": test_prompts_dir,
                    "name": "Test Prompts",
                    "description": "Test prompts directory for integration tests",
                    "enabled": True
                }
            ]
            
            with os.fdopen(test_config_fd, 'w') as f:
                json.dump(test_directories, f, indent=2)
            
            # Set environment variable to override config file location
            original_config = os.environ.get('PROMPT_MANAGER_CONFIG_FILE')
            os.environ['PROMPT_MANAGER_CONFIG_FILE'] = test_config_path
            
            yield test_config_path
            
        finally:
            # Cleanup
            try:
                os.unlink(test_config_path)
            except FileNotFoundError:
                pass
            
            # Restore original config environment variable
            if original_config:
                os.environ['PROMPT_MANAGER_CONFIG_FILE'] = original_config
            elif 'PROMPT_MANAGER_CONFIG_FILE' in os.environ:
                del os.environ['PROMPT_MANAGER_CONFIG_FILE']
    else:
        # Not running tests, no setup needed
        yield None

# Import integration test fixtures
pytest_plugins = ["tests.integration.test_fixtures"] 