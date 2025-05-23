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
        # Create a sample prompt
        self.sample_prompt = Prompt(
            id="test_prompt",
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
            id="test_composite",
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
        
        # Check if unique ID contains both directory and prompt ID
        self.assertIn("dir", unique_id)
        self.assertIn("test_prompt", unique_id)
        
        # Test with predefined unique ID
        prompt_with_unique_id = Prompt(
            id="test_prompt",
            filename="test_prompt.md",
            directory="/test/dir",
            content="# Test Prompt\n\nThis is a test prompt.",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            unique_id="custom_unique_id"
        )
        
        # get_unique_id should return the predefined unique ID
        self.assertEqual(prompt_with_unique_id.get_unique_id, "custom_unique_id")
        
    def test_nested_directory_unique_id(self):
        """Test unique ID generation with nested directories"""
        # Create a prompt with a nested directory path
        nested_prompt = Prompt(
            id="nested_prompt",
            filename="nested_prompt.md",
            directory="/test/nested/sub/dir",
            content="# Nested Prompt\n\nThis is a nested prompt.",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Generate a unique ID
        unique_id = nested_prompt.get_unique_id
        
        # Check if unique ID contains the last two parts of the directory path
        self.assertIn("sub_dir", unique_id)
        self.assertIn("nested_prompt", unique_id)
        
    def test_special_characters_in_directory(self):
        """Test unique ID generation with special characters in directory path"""
        # Create a prompt with special characters in directory path
        special_prompt = Prompt(
            id="special_prompt",
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
        self.assertIn("special-chars_special_prompt", unique_id)  # Hyphens preserved


if __name__ == "__main__":
    unittest.main() 