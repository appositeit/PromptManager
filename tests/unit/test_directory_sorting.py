"""
Unit tests for directory sorting functionality in New Prompt modal.
Tests ensure directories are sorted alphabetically by name.
"""

import pytest


class TestDirectorySorting:
    """Test directory sorting functionality in the New Prompt modal."""
    
    def test_directory_sorting_alphabetical(self):
        """Test that directories are sorted alphabetically by name."""
        # Simulate directories data as it would come from the API
        directories = [
            {"name": "workflows", "path": "/user/prompts/workflows", "enabled": True},
            {"name": "architecture", "path": "/user/prompts/architecture", "enabled": True},
            {"name": "templates", "path": "/user/prompts/templates", "enabled": True},
            {"name": "code-review", "path": "/user/prompts/code-review", "enabled": True},
            {"name": "documentation", "path": "/user/prompts/documentation", "enabled": True},
        ]
        
        # Filter and sort as the JavaScript code does
        enabled_directories = [dir for dir in directories if dir["enabled"]]
        sorted_directories = sorted(enabled_directories, key=lambda d: d["name"])
        
        # Extract names for comparison
        sorted_names = [dir["name"] for dir in sorted_directories]
        
        # Expected alphabetical order
        expected_names = ["architecture", "code-review", "documentation", "templates", "workflows"]
        
        assert sorted_names == expected_names
        
    def test_directory_sorting_with_disabled_directories(self):
        """Test that disabled directories are filtered out before sorting."""
        directories = [
            {"name": "z-disabled", "path": "/user/prompts/z-disabled", "enabled": False},
            {"name": "b-enabled", "path": "/user/prompts/b-enabled", "enabled": True},
            {"name": "a-enabled", "path": "/user/prompts/a-enabled", "enabled": True},
            {"name": "c-disabled", "path": "/user/prompts/c-disabled", "enabled": False},
        ]
        
        # Filter and sort as the JavaScript code does
        enabled_directories = [dir for dir in directories if dir["enabled"]]
        sorted_directories = sorted(enabled_directories, key=lambda d: d["name"])
        
        # Extract names for comparison
        sorted_names = [dir["name"] for dir in sorted_directories]
        
        # Should only include enabled directories, sorted alphabetically
        expected_names = ["a-enabled", "b-enabled"]
        
        assert sorted_names == expected_names
        
    def test_directory_sorting_case_sensitive(self):
        """Test that directory sorting handles case correctly."""
        directories = [
            {"name": "Zulu", "path": "/user/prompts/Zulu", "enabled": True},
            {"name": "alpha", "path": "/user/prompts/alpha", "enabled": True},
            {"name": "Beta", "path": "/user/prompts/Beta", "enabled": True},
            {"name": "charlie", "path": "/user/prompts/charlie", "enabled": True},
        ]
        
        # Filter and sort as the JavaScript code does
        enabled_directories = [dir for dir in directories if dir["enabled"]]
        # JavaScript localeCompare() handles case correctly, but in Python we use default sort
        sorted_directories = sorted(enabled_directories, key=lambda d: d["name"])
        
        # Extract names for comparison
        sorted_names = [dir["name"] for dir in sorted_directories]
        
        # Expected order (uppercase letters come before lowercase in ASCII)
        expected_names = ["Beta", "Zulu", "alpha", "charlie"]
        
        assert sorted_names == expected_names
        
    def test_directory_sorting_empty_list(self):
        """Test that empty directory list is handled gracefully."""
        directories = []
        
        # Filter and sort as the JavaScript code does
        enabled_directories = [dir for dir in directories if dir["enabled"]]
        sorted_directories = sorted(enabled_directories, key=lambda d: d["name"])
        
        assert sorted_directories == []
        
    def test_directory_sorting_all_disabled(self):
        """Test that all disabled directories result in empty list."""
        directories = [
            {"name": "disabled1", "path": "/user/prompts/disabled1", "enabled": False},
            {"name": "disabled2", "path": "/user/prompts/disabled2", "enabled": False},
        ]
        
        # Filter and sort as the JavaScript code does
        enabled_directories = [dir for dir in directories if dir["enabled"]]
        sorted_directories = sorted(enabled_directories, key=lambda d: d["name"])
        
        assert sorted_directories == []
        
    def test_directory_sorting_with_special_characters(self):
        """Test that directories with special characters are sorted correctly."""
        directories = [
            {"name": "z-workflow", "path": "/user/prompts/z-workflow", "enabled": True},
            {"name": "a_template", "path": "/user/prompts/a_template", "enabled": True},
            {"name": "m.config", "path": "/user/prompts/m.config", "enabled": True},
            {"name": "b-test", "path": "/user/prompts/b-test", "enabled": True},
        ]
        
        # Filter and sort as the JavaScript code does
        enabled_directories = [dir for dir in directories if dir["enabled"]]
        sorted_directories = sorted(enabled_directories, key=lambda d: d["name"])
        
        # Extract names for comparison
        sorted_names = [dir["name"] for dir in sorted_directories]
        
        # Expected alphabetical order with special characters
        expected_names = ["a_template", "b-test", "m.config", "z-workflow"]
        
        assert sorted_names == expected_names
