"""
Simple integration test using only the test prompts directory.

This test should run completely isolated from the real prompt directories.
"""

import pytest
from fastapi.testclient import TestClient
from src.services.prompt_service import PromptService
from src.server import create_app
from .test_fixtures import IsolatedPromptService


def test_simple_integration_with_test_prompts():
    """Test basic functionality using only test prompts."""
    
    # Create an isolated PromptService with only the test directory
    test_prompts_dir = "/mnt/data/jem/development/prompt_manager/tests/test_prompts"
    
    # Create service with ONLY test directory, no config loading
    service = IsolatedPromptService(
        base_directories=[test_prompts_dir],
        auto_load=True,
        create_default_directory_if_empty=False
    )
    
    # Verify we have test prompts loaded
    prompts = service.get_all_prompts()
    test_prompt_names = [p['name'] for p in prompts]
    
    # Should have our test prompts
    expected_prompts = ['simple_test', 'test_composite', 'tagged_test', 'dependency_test', 'included_text']
    
    for expected in expected_prompts:
        assert expected in test_prompt_names, f"Missing test prompt: {expected}"
    
    # Test composite functionality
    composite_prompt = service.get_prompt('test_composite')
    assert composite_prompt is not None
    assert composite_prompt.is_composite  # Should be True because it contains [[included_text]]
    
    # Test expansion
    expanded_content, dependencies, warnings = service.expand_inclusions(
        composite_prompt.content, 
        parent_directory=composite_prompt.directory,
        parent_id=composite_prompt.id
    )
    
    assert 'included_text' in dependencies
    assert 'This is included text for testing' in expanded_content
    
    print(f"✅ Test passed with {len(prompts)} test prompts")
    print(f"   Test prompts found: {test_prompt_names}")
    print(f"   Composite prompt expanded successfully")
