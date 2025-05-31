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
            id=Prompt.generate_id_from_directory_and_name("/test/dir", "test_prompt"),
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
            id=Prompt.generate_id_from_directory_and_name("/test/dir", "test_composite"),
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
        
        # In the new schema, get_unique_id returns the full path ID 
        self.assertEqual(unique_id, "/test/dir/test_prompt")  # Full path format
        
        # Test with predefined unique ID
        prompt_with_unique_id = Prompt(
            id=Prompt.generate_id_from_directory_and_name("/test/dir", "test_prompt"),
            name="test_prompt",
            filename="test_prompt.md",
            directory="/test/dir",
            content="# Test Prompt\n\nThis is a test prompt.",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            unique_id="custom_unique_id"
        )
        
        # get_unique_id should return the ID (unique_id field is deprecated)
        self.assertEqual(prompt_with_unique_id.get_unique_id, "/test/dir/test_prompt")
        
    def test_nested_directory_unique_id(self):
        """Test unique ID generation with nested directories"""
        # Create a prompt with a nested directory path using proper ID generation
        nested_prompt = Prompt(
            id=Prompt.generate_id_from_directory_and_name("/test/nested/sub/dir", "nested_prompt"),
            name="nested_prompt",
            filename="nested_prompt.md",
            directory="/test/nested/sub/dir",
            content="# Nested Prompt\n\nThis is a nested prompt.",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Generate a unique ID
        unique_id = nested_prompt.get_unique_id
        
        # Check if unique ID contains the full path
        self.assertEqual(unique_id, "/test/nested/sub/dir/nested_prompt")  # Full path format
        
    def test_special_characters_in_directory(self):
        """Test unique ID generation with special characters in directory path"""
        # Create a prompt with special characters in directory path using proper ID generation
        special_prompt = Prompt(
            id=Prompt.generate_id_from_directory_and_name("/test/with space/and/special-chars", "special_prompt"),
            name="special_prompt",
            filename="special_prompt.md",
            directory="/test/with space/and/special-chars",
            content="# Special Prompt\n\nThis is a special prompt.",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Generate a unique ID
        unique_id = special_prompt.get_unique_id
        
        # In the new schema, we preserve the full path including spaces
        self.assertEqual(unique_id, "/test/with space/and/special-chars/special_prompt")

    def test_display_name_calculation_unique_filename(self):
        """Test display name calculation when filename is unique"""
        # When filename is globally unique, should return just the filename
        all_prompts = ["/project1/docs/readme", "/project2/prompts/start"]
        display_name = Prompt.calculate_display_name("/project1/docs/readme", all_prompts)
        self.assertEqual(display_name, "readme")

    def test_display_name_calculation_filename_conflict(self):
        """Test display name calculation when filenames conflict"""
        # When filenames conflict, should return shortest unique path
        all_prompts = [
            "/project1/prompts/restart", 
            "/project2/prompts/restart",
            "/project3/docs/readme"
        ]
        
        # Should use directory name to disambiguate
        display_name1 = Prompt.calculate_display_name("/project1/prompts/restart", all_prompts)
        display_name2 = Prompt.calculate_display_name("/project2/prompts/restart", all_prompts)
        
        self.assertEqual(display_name1, "project1:restart")
        self.assertEqual(display_name2, "project2:restart")

    def test_display_name_calculation_deep_conflict(self):
        """Test display name calculation with deeper directory conflicts"""
        all_prompts = [
            "/home/user1/development/project1/prompts/restart",
            "/home/user2/development/project1/prompts/restart", 
            "/home/user1/development/project2/prompts/start"
        ]
        
        # Should find the first unique directory segment
        display_name1 = Prompt.calculate_display_name("/home/user1/development/project1/prompts/restart", all_prompts)
        display_name2 = Prompt.calculate_display_name("/home/user2/development/project1/prompts/restart", all_prompts)
        
        # The first unique segment is "user1" vs "user2"
        self.assertEqual(display_name1, "user1:restart")
        self.assertEqual(display_name2, "user2:restart")

    def test_calculate_all_display_names(self):
        """Test bulk display name calculation"""
        prompt_data = [
            {"id": "/project1/prompts/restart", "name": "restart"},
            {"id": "/project2/prompts/restart", "name": "restart"},
            {"id": "/project1/docs/readme", "name": "readme"}
        ]
        
        display_names = Prompt.calculate_all_display_names(prompt_data)
        
        expected = {
            "/project1/prompts/restart": "project1:restart",
            "/project2/prompts/restart": "project2:restart", 
            "/project1/docs/readme": "readme"
        }
        
        self.assertEqual(display_names, expected)

    def test_display_name_cache(self):
        """Test display name caching functionality"""
        # Test setting and getting cached display name
        self.sample_prompt.set_display_name_cache("cached_name")
        self.assertEqual(self.sample_prompt.display_name, "cached_name")
        
        # Test clearing cache
        self.sample_prompt.display_name_cache = None
        self.assertEqual(self.sample_prompt.display_name, "test_prompt")  # Falls back to name

    def test_generate_id_from_file_path(self):
        """Test generating ID from complete file path"""
        # Test with .md extension
        file_path = "/home/user/projects/myproject/prompts/restart.md"
        generated_id = Prompt.generate_id(file_path)
        self.assertEqual(generated_id, "/home/user/projects/myproject/prompts/restart")
        
        # Test without .md extension
        file_path_no_ext = "/home/user/projects/myproject/prompts/restart"
        generated_id_no_ext = Prompt.generate_id(file_path_no_ext)
        self.assertEqual(generated_id_no_ext, "/home/user/projects/myproject/prompts/restart")

    def test_parse_id(self):
        """Test parsing full path ID back to directory and name"""
        full_id = "/home/user/projects/myproject/prompts/restart"
        directory, name = Prompt.parse_id(full_id)
        
        self.assertEqual(directory, "/home/user/projects/myproject/prompts")
        self.assertEqual(name, "restart")


if __name__ == "__main__":
    unittest.main() 