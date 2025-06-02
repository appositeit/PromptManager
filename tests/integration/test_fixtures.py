"""
Test fixtures for integration tests using test prompts.

This module provides fixtures for setting up isolated test environments
that use the test_prompts directory instead of real prompt directories.
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from typing import Dict, Any
from fastapi.testclient import TestClient

from src.services.prompt_service import PromptService
from src.server import create_app


@pytest.fixture
def test_prompts_dir():
    """Path to the test prompts directory."""
    return str(Path(__file__).parent.parent / "test_prompts")


class IsolatedPromptService(PromptService):
    """A PromptService that doesn't load from config file."""
    
    def _load_directories_from_config_file(self):
        """Override to return empty list - don't load from config."""
        return []


@pytest.fixture
def isolated_prompt_service(test_prompts_dir):
    """Create an isolated PromptService instance using only test prompts."""
    # Create a temporary config to avoid interfering with real config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_config_path = f.name
    
    # Create service with test prompts directory
    service = IsolatedPromptService(
        base_directories=[test_prompts_dir],
        auto_load=True,
        create_default_directory_if_empty=False
    )
    
    # Override the config file path to prevent writes to real config
    service.CONFIG_FILE = temp_config_path
    service._allow_test_config_write = True
    
    yield service
    
    # Cleanup
    try:
        os.unlink(temp_config_path)
    except FileNotFoundError:
        pass


@pytest.fixture  
def test_client_with_test_prompts(test_prompts_dir):
    """Create a TestClient using the isolated prompt service."""
    # Create isolated service instance
    test_service = IsolatedPromptService(
        base_directories=[test_prompts_dir],
        auto_load=True,
        create_default_directory_if_empty=False
    )
    
    # Create app and override the prompt service
    app = create_app()
    
    # Override the dependency to use our test service
    def get_test_prompt_service():
        return test_service
        
    from src.api.router import get_prompt_service_dependency
    app.dependency_overrides[get_prompt_service_dependency] = get_test_prompt_service
    
    return TestClient(app)


@pytest.fixture
def sample_test_prompt_data():
    """Sample prompt data for creating test prompts."""
    return {
        "name": "integration_test_prompt",
        "directory": "/mnt/data/jem/development/prompt_manager/tests/test_prompts",
        "content": "# Integration Test Prompt\n\nThis is a test prompt for integration testing.",
        "description": "Test prompt for integration testing",
        "tags": ["test", "integration"]
    }


class TestPromptsHelper:
    """Helper class for working with test prompts in integration tests."""
    
    @staticmethod
    def get_test_prompt_ids():
        """Get list of test prompt IDs that should be available."""
        return [
            "simple_test",
            "test_composite", 
            "tagged_test",
            "dependency_test",
            "included_text"
        ]
    
    @staticmethod
    def get_composite_test_prompts():
        """Get list of composite test prompt IDs."""
        return [
            "test_composite",
            "dependency_test"
        ]
    
    @staticmethod
    def get_prompts_with_tags():
        """Get dictionary mapping prompt IDs to their tags."""
        return {
            "simple_test": ["test", "simple"],
            "test_composite": ["test", "copy"],
            "tagged_test": ["test", "integration", "api", "multiple-tags"],
            "dependency_test": ["test", "dependencies"]
        }
    
    @staticmethod
    def get_dependency_relationships():
        """Get dictionary mapping prompts to their dependencies."""
        return {
            "test_composite": ["included_text"],
            "dependency_test": ["tagged_test", "simple_test", "included_text", "test_composite"]  # includes transitive deps
        }
