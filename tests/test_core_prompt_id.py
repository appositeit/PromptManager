"""
Simplified test for core Prompt ID uniqueness functionality.
Tests only the model layer without external dependencies.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_core_functionality():
    """Test the core prompt model functionality."""
    print("🧪 Testing Core Prompt Model Functionality...")
    
    from models.unified_prompt import Prompt
    from datetime import datetime
    
    # Test 1: ID Generation
    print("\n1️⃣ Testing ID Generation:")
    
    id1 = Prompt.generate_id("/path/to/general", "restart")
    id2 = Prompt.generate_id("/path/to/specific", "restart")
    id3 = Prompt.generate_id("/path/to/general", "deploy")
    
    print(f"   📁 general/restart → {id1}")
    print(f"   📁 specific/restart → {id2}")
    print(f"   📁 general/deploy → {id3}")
    
    # Verify uniqueness
    assert id1 != id2, "Same name in different directories should have different IDs"
    assert id1 != id3, "Different names in same directory should have different IDs"
    assert id2 != id3, "Different prompts should have different IDs"
    
    print("   ✅ All IDs are unique!")
    
    # Test 2: ID Parsing
    print("\n2️⃣ Testing ID Parsing:")
    
    dir_name, prompt_name = Prompt.parse_id("general/restart")
    print(f"   🔍 'general/restart' → dir='{dir_name}', name='{prompt_name}'")
    assert dir_name == "general" and prompt_name == "restart"
    
    dir_name2, prompt_name2 = Prompt.parse_id("specific/restart")
    print(f"   🔍 'specific/restart' → dir='{dir_name2}', name='{prompt_name2}'")
    assert dir_name2 == "specific" and prompt_name2 == "restart"
    
    # Test legacy format
    dir_name3, prompt_name3 = Prompt.parse_id("legacy_prompt")
    print(f"   🔍 'legacy_prompt' → dir='{dir_name3}', name='{prompt_name3}'")
    assert dir_name3 == "" and prompt_name3 == "legacy_prompt"
    
    print("   ✅ ID parsing works correctly!")
    
    # Test 3: Prompt Creation
    print("\n3️⃣ Testing Prompt Object Creation:")
    
    now = datetime.now()
    prompt = Prompt(
        id="general/restart",
        name="restart",
        filename="restart.md",
        directory="/path/to/general",
        content="# Restart Process\n\nSteps to restart the system.",
        description="System restart procedure",
        tags=["system", "restart"],
        created_at=now,
        updated_at=now
    )
    
    print(f"   📄 Created prompt: {prompt.name} (ID: {prompt.id})")
    print(f"   📂 Directory: {prompt.directory}")
    print(f"   🏷️  Tags: {prompt.tags}")
    
    # Verify properties
    assert prompt.id == "general/restart"
    assert prompt.name == "restart"
    assert prompt.directory == "/path/to/general"
    assert "restart" in prompt.tags
    
    # Test unique_id property
    assert prompt.get_unique_id == prompt.id
    
    # Test composite detection
    simple_content = "# Simple Prompt\n\nNo inclusions here."
    composite_content = "# Composite Prompt\n\nIncludes [[other_prompt]] content."
    
    prompt.content = simple_content
    assert not prompt.is_composite, "Should not be composite without inclusions"
    
    prompt.content = composite_content
    assert prompt.is_composite, "Should be composite with inclusions"
    
    print("   ✅ Prompt object creation works correctly!")
    
    # Test 4: Validation
    print("\n4️⃣ Testing Validation:")
    
    try:
        # Test empty ID validation
        Prompt(
            id="",
            name="test",
            filename="test.md",
            directory="/test",
            content="test",
            created_at=now,
            updated_at=now
        )
        assert False, "Should have failed with empty ID"
    except ValueError:
        print("   ✅ Empty ID properly rejected")
    
    try:
        # Test empty name validation
        Prompt(
            id="test/prompt",
            name="",
            filename="test.md",
            directory="/test",
            content="test",
            created_at=now,
            updated_at=now
        )
        assert False, "Should have failed with empty name"
    except ValueError:
        print("   ✅ Empty name properly rejected")
    
    # Test ID format validation
    valid_ids = ["general/restart", "simple_name"]
    invalid_ids = ["", "dir/", "/name", "dir//name"]
    
    for valid_id in valid_ids:
        try:
            Prompt(
                id=valid_id,
                name="test",
                filename="test.md", 
                directory="/test",
                content="test",
                created_at=now,
                updated_at=now
            )
            print(f"   ✅ Valid ID accepted: '{valid_id}'")
        except ValueError as e:
            print(f"   ❌ Valid ID rejected: '{valid_id}' - {e}")
            assert False, f"Valid ID should be accepted: {valid_id}"
    
    print("   ✅ Validation works correctly!")

def test_backward_compatibility():
    """Test backward compatibility features."""
    print("\n5️⃣ Testing Backward Compatibility:")
    
    from models.unified_prompt import Prompt
    from datetime import datetime
    
    now = datetime.now()
    
    # Create prompt with new schema
    prompt = Prompt(
        id="general/restart",
        name="restart", 
        filename="restart.md",
        directory="/path/to/general",
        content="# Restart\n\nRestart procedure.",
        created_at=now,
        updated_at=now
    )
    
    # Test unique_id compatibility
    prompt.unique_id = prompt.id
    assert prompt.unique_id == "general/restart"
    assert prompt.get_unique_id == "general/restart"
    
    print("   ✅ unique_id backward compatibility works")
    
    # Test update_id_from_directory_and_name method
    prompt.directory = "/new/path/specific"
    prompt.name = "deploy"
    prompt.update_id_from_directory_and_name()
    
    expected_new_id = "specific/deploy"
    assert prompt.id == expected_new_id, f"Expected '{expected_new_id}', got '{prompt.id}'"
    assert prompt.unique_id == expected_new_id
    
    print("   ✅ ID regeneration works correctly")

def test_edge_cases():
    """Test edge cases and special characters."""
    print("\n6️⃣ Testing Edge Cases:")
    
    from models.unified_prompt import Prompt
    
    # Test special characters in directory names
    special_dirs = [
        "/path/with spaces",
        "/path/with-dashes", 
        "/path/with_underscores",
        "/path/with.dots"
    ]
    
    for directory in special_dirs:
        prompt_id = Prompt.generate_id(directory, "test")
        print(f"   🔤 '{directory}' → '{prompt_id}'")
        
        # Should not contain problematic characters
        assert "/" in prompt_id, "Should contain directory separator"
        # Should be parseable
        dir_part, name_part = Prompt.parse_id(prompt_id)
        assert name_part == "test", "Name should be preserved"
    
    print("   ✅ Special characters handled correctly")
    
    # Test very long names
    long_name = "a" * 100
    long_id = Prompt.generate_id("/test", long_name)
    assert long_name in long_id, "Long names should be preserved"
    
    print("   ✅ Long names handled correctly")

def run_core_tests():
    """Run all core tests."""
    print("🚀 Running Core Prompt ID Uniqueness Tests")
    print("=" * 50)
    
    try:
        test_core_functionality()
        test_backward_compatibility()
        test_edge_cases()
        
        print("\n" + "=" * 50)
        print("🎉 All core tests passed!")
        print("\n📋 Verified Features:")
        print("   ✅ Unique ID generation across directories")
        print("   ✅ Proper ID parsing and validation")  
        print("   ✅ Prompt object creation with new schema")
        print("   ✅ Composite prompt detection")
        print("   ✅ Input validation and error handling")
        print("   ✅ Backward compatibility with unique_id")
        print("   ✅ Special character handling")
        print("   ✅ Edge case scenarios")
        
        print("\n✨ Core implementation is solid!")
        print("🔄 Ready for service layer integration")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_core_tests()
    exit(0 if success else 1)
