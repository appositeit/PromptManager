"""
Unit tests for the Prompt model.

These tests verify the functionality of the Prompt data model,
including its properties like `full_path`, `is_composite`,
and the generation of `unique_id`.

Modules/Classes Tested:
- src.models.unified_prompt.Prompt
"""

import unittest
from datetime import datetime, timezone
from pathlib import Path

from src.models.unified_prompt import Prompt


class TestUnifiedPrompt(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Create a sample prompt with properly generated ID
        self.sample_prompt = Prompt(
            id=Prompt.generate_id("/test/dir", "test_prompt"),
            name="test_prompt",
            filename="test_prompt.md",
            directory="/test/dir",
            content="# Test Prompt\n\nThis is a test prompt.",
            description="Test prompt description",
            tags=["test", "sample"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Create a sample composite prompt
        self.sample_composite_prompt = Prompt(
            id=Prompt.generate_id("/test/dir", "test_composite"),
            name="test_composite",
            filename="test_composite.md",
            directory="/test/dir",
            content="# Test Composite Prompt\n\nThis includes another prompt: [[test_prompt]]",
            description="Test composite prompt",
            tags=["test", "composite"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
    def test_full_path(self):
        """Test the full_path property"""
        expected_path = str(Path("/test/dir") / "test_prompt.md")
        self.assertEqual(self.sample_prompt.full_path, expected_path)
        
    def test_is_composite(self):
        """Test the is_composite property"""
        # Standard prompt should not be composite
        self.assertFalse(self.sample_prompt.is_composite)
        
        # Composite prompt should be identified as composite
        self.assertTrue(self.sample_composite_prompt.is_composite)
        
    def test_unique_id_generation(self):
        """Test unique ID generation"""
        # Generate a unique ID
        unique_id = self.sample_prompt.get_unique_id
        
        # Check if unique ID contains both directory and prompt name  
        # In the new schema, get_unique_id returns the full ID 
        self.assertEqual(unique_id, "dir/test_prompt")  # The generated ID format
        
        # Test with predefined unique ID
        prompt_with_unique_id = Prompt(
            id=Prompt.generate_id("/test/dir", "test_prompt"),
            name="test_prompt",
            filename="test_prompt.md",
            directory="/test/dir",
            content="# Test Prompt\n\nThis is a test prompt.",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            unique_id="custom_unique_id"
        )
        
        # get_unique_id should return the ID (unique_id field is deprecated)
        self.assertEqual(prompt_with_unique_id.get_unique_id, "dir/test_prompt")
        
    def test_nested_directory_unique_id(self):
        """Test unique ID generation with nested directories"""
        # Create a prompt with a nested directory path using proper ID generation
        nested_prompt = Prompt(
            id=Prompt.generate_id("/test/nested/sub/dir", "nested_prompt"),
            name="nested_prompt",
            filename="nested_prompt.md",
            directory="/test/nested/sub/dir",
            content="# Nested Prompt\n\nThis is a nested prompt.",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Generate a unique ID
        unique_id = nested_prompt.get_unique_id
        
        # Check if unique ID contains the directory name and prompt name
        self.assertEqual(unique_id, "dir/nested_prompt")  # Last directory component is "dir"
        
    def test_special_characters_in_directory(self):
        """Test unique ID generation with special characters in directory path"""
        # Create a prompt with special characters in directory path using proper ID generation
        special_prompt = Prompt(
            id=Prompt.generate_id("/test/with space/and/special-chars", "special_prompt"),
            name="special_prompt",
            filename="special_prompt.md",
            directory="/test/with space/and/special-chars",
            content="# Special Prompt\n\nThis is a special prompt.",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Generate a unique ID
        unique_id = special_prompt.get_unique_id
        
        # Check if unique ID handles special characters correctly
        self.assertNotIn(" ", unique_id)  # No spaces
        self.assertEqual(unique_id, "special-chars/special_prompt")  # Special chars normalized


if __name__ == "__main__":
    unittest.main() 