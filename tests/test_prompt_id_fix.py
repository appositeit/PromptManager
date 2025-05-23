"""
Test script to verify the Prompt ID uniqueness fix works correctly.
This can be run to validate the implementation before full testing.
"""

import os
import tempfile
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_prompt_id_uniqueness():
    """Test that prompts with same name in different directories get unique IDs."""
    from models.unified_prompt import Prompt
    from datetime import datetime
    
    print("🧪 Testing Prompt ID Uniqueness...")
    
    # Test ID generation
    id1 = Prompt.generate_id("/path/to/general", "restart")
    id2 = Prompt.generate_id("/path/to/specific", "restart")
    
    print(f"✅ ID 1: {id1}")
    print(f"✅ ID 2: {id2}")
    
    assert id1 != id2, "IDs should be unique!"
    assert id1 == "general/restart", f"Expected 'general/restart', got '{id1}'"
    assert id2 == "specific/restart", f"Expected 'specific/restart', got '{id2}'"
    
    # Test ID parsing
    dir_name, prompt_name = Prompt.parse_id("general/restart")
    assert dir_name == "general", f"Expected 'general', got '{dir_name}'"
    assert prompt_name == "restart", f"Expected 'restart', got '{prompt_name}'"
    
    print("✅ Prompt model tests passed!")

def test_service_integration():
    """Test that the service layer handles the new ID schema correctly."""
    from services.prompt_service import PromptService
    from models.unified_prompt import Prompt
    import json
    
    print("\n🧪 Testing Service Integration...")
    
    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        general_dir = os.path.join(temp_dir, "general")
        specific_dir = os.path.join(temp_dir, "specific")
        os.makedirs(general_dir)
        os.makedirs(specific_dir)
        
        # Create test files with same name in different directories
        general_restart = os.path.join(general_dir, "restart.md")
        specific_restart = os.path.join(specific_dir, "restart.md")
        
        with open(general_restart, 'w') as f:
            f.write("---\ndescription: General restart\ntags: [general]\n---\n\n# General Restart\n\nGeneral restart procedure.")
        
        with open(specific_restart, 'w') as f:
            f.write("---\ndescription: Specific restart\ntags: [specific]\n---\n\n# Specific Restart\n\nSpecific restart procedure.")
        
        # Test service loading
        service = PromptService(base_directories=[temp_dir], auto_load=False, create_default_directory_if_empty=False)
        
        # Load prompts manually to avoid config writes
        general_prompt = service.load_prompt(general_restart)
        specific_prompt = service.load_prompt(specific_restart)
        
        assert general_prompt is not None, "Failed to load general prompt"
        assert specific_prompt is not None, "Failed to load specific prompt"
        
        print(f"✅ General prompt ID: {general_prompt.id}")
        print(f"✅ Specific prompt ID: {specific_prompt.id}")
        
        # Verify IDs are unique
        assert general_prompt.id != specific_prompt.id, "Prompt IDs should be unique!"
        
        # Verify names are the same (both "restart")
        assert general_prompt.name == specific_prompt.name == "restart", "Names should be the same"
        
        # Add to service and test retrieval
        service.prompts[general_prompt.id] = general_prompt
        service.prompts[specific_prompt.id] = specific_prompt
        
        # Test get_prompt with full ID
        found_general = service.get_prompt(general_prompt.id)
        found_specific = service.get_prompt(specific_prompt.id)
        
        assert found_general == general_prompt, "Should find general prompt by full ID"
        assert found_specific == specific_prompt, "Should find specific prompt by full ID"
        
        # Test get_prompt by name with directory context
        found_by_name_general = service.get_prompt("restart", directory=general_dir)
        found_by_name_specific = service.get_prompt("restart", directory=specific_dir)
        
        assert found_by_name_general == general_prompt, "Should find general prompt by name with directory"
        assert found_by_name_specific == specific_prompt, "Should find specific prompt by name with directory"
        
        print("✅ Service integration tests passed!")

def test_inclusion_resolution():
    """Test that inclusion resolution works with directory context."""
    from services.prompt_service import PromptService
    
    print("\n🧪 Testing Inclusion Resolution...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create directory structure
        shared_dir = os.path.join(temp_dir, "shared")
        project_dir = os.path.join(temp_dir, "project")
        os.makedirs(shared_dir)
        os.makedirs(project_dir)
        
        # Create shared prompt
        shared_prompt = os.path.join(shared_dir, "common.md")
        with open(shared_prompt, 'w') as f:
            f.write("# Common Utilities\n\nShared utilities for all projects.")
        
        # Create project prompt that includes shared
        project_prompt = os.path.join(project_dir, "main.md")
        with open(project_prompt, 'w') as f:
            f.write("# Main Project\n\n[[common]]\n\nProject specific content.")
        
        # Test service
        service = PromptService(base_directories=[temp_dir], auto_load=False, create_default_directory_if_empty=False)
        
        # Load prompts
        shared = service.load_prompt(shared_prompt)
        main = service.load_prompt(project_prompt)
        
        # Add to service
        service.prompts[shared.id] = shared
        service.prompts[main.id] = main
        
        print(f"✅ Shared prompt ID: {shared.id}")
        print(f"✅ Main prompt ID: {main.id}")
        
        # Test inclusion expansion
        expanded, dependencies, warnings = service.expand_inclusions(
            main.content,
            parent_directory=main.directory,
            parent_id=main.id
        )
        
        print(f"✅ Expanded content preview: {expanded[:100]}...")
        print(f"✅ Dependencies: {dependencies}")
        print(f"✅ Warnings: {warnings}")
        
        # Should resolve [[common]] to the shared prompt
        assert "Shared utilities" in expanded, "Should expand the common prompt content"
        assert "common" in dependencies, "Should list common as a dependency"
        
        print("✅ Inclusion resolution tests passed!")

def test_api_compatibility():
    """Test that API changes work with new schema."""
    print("\n🧪 Testing API Compatibility...")
    
    from api.router import PromptCreate, PromptRenameRequest
    from models.unified_prompt import Prompt
    
    # Test new PromptCreate model
    create_data = PromptCreate(
        name="test_prompt",
        content="# Test\n\nTest content",
        directory="/test/dir",
        description="Test description",
        tags=["test"]
    )
    
    assert create_data.name == "test_prompt", "Name field should work"
    assert hasattr(create_data, 'name'), "Should have name field"
    assert not hasattr(create_data, 'id'), "Should not have id field in create"
    
    # Test rename model
    rename_data = PromptRenameRequest(
        old_id="old_prompt",
        new_name="new_prompt",
        description="Updated description"
    )
    
    assert rename_data.old_id == "old_prompt", "Old ID should work"
    assert rename_data.new_name == "new_prompt", "New name should work"
    assert hasattr(rename_data, 'new_name'), "Should have new_name field"
    
    print("✅ API compatibility tests passed!")

def run_all_tests():
    """Run all tests to verify the implementation."""
    print("🚀 Running Prompt ID Uniqueness Fix Tests\n")
    
    try:
        test_prompt_id_uniqueness()
        test_service_integration()
        test_inclusion_resolution()
        test_api_compatibility()
        
        print("\n🎉 All tests passed! The Prompt ID uniqueness fix is working correctly.")
        print("\n📋 Summary:")
        print("   ✅ Unique ID generation working")
        print("   ✅ Service layer integration working")
        print("   ✅ Inclusion resolution with directory context working")
        print("   ✅ API schema changes working")
        print("\n✨ Ready for production deployment!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
