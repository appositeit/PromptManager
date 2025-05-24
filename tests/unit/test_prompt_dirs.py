#!/usr/bin/env python3
"""
Unit tests for prompt directory management.

Tests the prompt_dirs module functionality for managing prompt directories.
"""

import os
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock
from src.services import prompt_dirs


class TestPromptDirectories:
    """Tests for prompt directory management functions."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_project_dir = os.path.join(self.temp_dir, "project", "data", "prompts")
        self.test_prompts_dir = os.path.join(self.temp_dir, "project", "prompts")
        self.test_user_dir = os.path.join(self.temp_dir, "user", ".prompt_manager", "prompts")

    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('src.services.prompt_dirs.os.path.dirname')
    @patch('src.services.prompt_dirs.os.path.expanduser')
    def test_initialize_prompt_directories_creates_missing_dirs(self, mock_expanduser, mock_dirname):
        """Test that initialize_prompt_directories creates missing directories."""
        # Mock paths to use our test directories
        def mock_dirname_side_effect(path):
            if "prompt_dirs.py" in path:
                return os.path.join(self.temp_dir, "project", "src", "services")
            return os.path.dirname(path)
        
        mock_dirname.side_effect = mock_dirname_side_effect
        mock_expanduser.return_value = os.path.join(self.temp_dir, "user")
        
        # Ensure directories don't exist initially
        assert not os.path.exists(self.test_project_dir)
        assert not os.path.exists(self.test_prompts_dir)
        assert not os.path.exists(self.test_user_dir)
        
        # Initialize directories
        result = prompt_dirs.initialize_prompt_directories()
        
        # Verify directories were created
        assert os.path.exists(self.test_project_dir)
        assert os.path.exists(self.test_prompts_dir)
        assert os.path.exists(self.test_user_dir)
        
        # Verify return value
        assert len(result) == 3
        assert self.test_project_dir in result
        assert self.test_prompts_dir in result
        assert self.test_user_dir in result

    @patch('src.services.prompt_dirs.os.path.dirname')
    @patch('src.services.prompt_dirs.os.path.expanduser')
    def test_initialize_prompt_directories_existing_dirs(self, mock_expanduser, mock_dirname):
        """Test that initialize_prompt_directories handles existing directories."""
        # Mock paths
        def mock_dirname_side_effect(path):
            if "prompt_dirs.py" in path:
                return os.path.join(self.temp_dir, "project", "src", "services")
            return os.path.dirname(path)
        
        mock_dirname.side_effect = mock_dirname_side_effect
        mock_expanduser.return_value = os.path.join(self.temp_dir, "user")
        
        # Create directories beforehand
        os.makedirs(self.test_project_dir, exist_ok=True)
        os.makedirs(self.test_prompts_dir, exist_ok=True)
        os.makedirs(self.test_user_dir, exist_ok=True)
        
        # Initialize directories - should not fail
        result = prompt_dirs.initialize_prompt_directories()
        
        # Verify directories still exist
        assert os.path.exists(self.test_project_dir)
        assert os.path.exists(self.test_prompts_dir)
        assert os.path.exists(self.test_user_dir)
        
        # Verify return value
        assert len(result) == 3

    @patch('src.services.prompt_dirs.os.path.dirname')
    @patch('src.services.prompt_dirs.os.path.expanduser')
    def test_get_prompt_directories_existing_only(self, mock_expanduser, mock_dirname):
        """Test that get_prompt_directories returns only existing directories."""
        # Mock paths
        def mock_dirname_side_effect(path):
            if "prompt_dirs.py" in path:
                return os.path.join(self.temp_dir, "project", "src", "services")
            return os.path.dirname(path)
        
        mock_dirname.side_effect = mock_dirname_side_effect
        mock_expanduser.return_value = os.path.join(self.temp_dir, "user")
        
        # Create only some directories
        os.makedirs(self.test_project_dir, exist_ok=True)
        os.makedirs(self.test_user_dir, exist_ok=True)
        # Don't create test_prompts_dir
        
        result = prompt_dirs.get_prompt_directories()
        
        # Should only return existing directories
        assert len(result) == 2
        assert self.test_project_dir in result
        assert self.test_user_dir in result
        assert self.test_prompts_dir not in result

    @patch('src.services.prompt_dirs.os.path.dirname')
    @patch('src.services.prompt_dirs.os.path.expanduser')
    def test_get_directory_by_path_existing_path(self, mock_expanduser, mock_dirname):
        """Test get_directory_by_path with existing path."""
        # Mock paths
        def mock_dirname_side_effect(path):
            if "prompt_dirs.py" in path:
                return os.path.join(self.temp_dir, "project", "src", "services")
            return os.path.dirname(path)
        
        mock_dirname.side_effect = mock_dirname_side_effect
        mock_expanduser.return_value = os.path.join(self.temp_dir, "user")
        
        # Test with project directory path
        result = prompt_dirs.get_directory_by_path(self.test_project_dir)
        
        assert result is not None
        assert result["path"] == self.test_project_dir
        assert result["name"] == "Project Data Prompts"
        assert result["type"] == "project"

    @patch('src.services.prompt_dirs.os.path.dirname')
    @patch('src.services.prompt_dirs.os.path.expanduser')
    def test_get_directory_by_path_user_path(self, mock_expanduser, mock_dirname):
        """Test get_directory_by_path with user directory path."""
        # Mock paths
        def mock_dirname_side_effect(path):
            if "prompt_dirs.py" in path:
                return os.path.join(self.temp_dir, "project", "src", "services")
            return os.path.dirname(path)
        
        mock_dirname.side_effect = mock_dirname_side_effect
        mock_expanduser.return_value = os.path.join(self.temp_dir, "user")
        
        # Test with user directory path
        result = prompt_dirs.get_directory_by_path(self.test_user_dir)
        
        assert result is not None
        assert result["path"] == self.test_user_dir
        assert result["name"] == "User Prompts"
        assert result["type"] == "user"

    def test_get_directory_by_path_nonexistent_path(self):
        """Test get_directory_by_path with non-existent path."""
        result = prompt_dirs.get_directory_by_path("/nonexistent/path")
        assert result is None

    @patch('src.services.prompt_dirs.os.path.expanduser')
    @patch('src.services.prompt_dirs.os.makedirs')
    def test_get_default_directory_creates_if_missing(self, mock_makedirs, mock_expanduser):
        """Test that get_default_directory creates user directory if missing."""
        mock_expanduser.return_value = os.path.join(self.temp_dir, "user")
        
        # Mock os.path.exists to return False for user dir
        with patch('src.services.prompt_dirs.os.path.exists', return_value=False):
            result = prompt_dirs.get_default_directory()
            
            # Should call makedirs
            mock_makedirs.assert_called_once_with(self.test_user_dir, exist_ok=True)
            assert result == self.test_user_dir

    @patch('src.services.prompt_dirs.os.path.expanduser')
    def test_get_default_directory_existing(self, mock_expanduser):
        """Test get_default_directory with existing user directory."""
        mock_expanduser.return_value = os.path.join(self.temp_dir, "user")
        
        # Create the directory
        os.makedirs(self.test_user_dir, exist_ok=True)
        
        # Mock os.path.exists to return True
        with patch('src.services.prompt_dirs.os.path.exists', return_value=True):
            result = prompt_dirs.get_default_directory()
            assert result == self.test_user_dir

    @patch('src.services.prompt_dirs.os.path.dirname')
    @patch('src.services.prompt_dirs.os.path.expanduser')
    def test_get_directory_by_path_normalization(self, mock_expanduser, mock_dirname):
        """Test that path normalization works correctly."""
        # Mock paths
        def mock_dirname_side_effect(path):
            if "prompt_dirs.py" in path:
                return os.path.join(self.temp_dir, "project", "src", "services")
            return os.path.dirname(path)
        
        mock_dirname.side_effect = mock_dirname_side_effect
        mock_expanduser.return_value = os.path.join(self.temp_dir, "user")
        
        # Test with path that needs normalization (extra slashes, etc.)
        unnormalized_path = self.test_project_dir + "///"
        result = prompt_dirs.get_directory_by_path(unnormalized_path)
        
        assert result is not None
        assert result["path"] == self.test_project_dir


class TestPromptDirectoriesEdgeCases:
    """Tests for edge cases in prompt directory management."""

    def test_path_handling_with_special_characters(self):
        """Test path handling with special characters."""
        # Test with paths containing special characters
        special_path = "/path/with spaces/and-dashes/and_underscores"
        result = prompt_dirs.get_directory_by_path(special_path)
        
        # Should handle gracefully (return None for non-matching path)
        assert result is None

    @patch('src.services.prompt_dirs.os.makedirs')
    def test_makedirs_error_handling(self, mock_makedirs):
        """Test error handling in directory creation."""
        # Mock makedirs to raise an exception
        mock_makedirs.side_effect = PermissionError("Permission denied")
        
        with patch('src.services.prompt_dirs.os.path.expanduser') as mock_expanduser:
            mock_expanduser.return_value = "/tmp/test"
            with patch('src.services.prompt_dirs.os.path.exists', return_value=False):
                # Should not crash, but let the exception propagate
                with pytest.raises(PermissionError):
                    prompt_dirs.get_default_directory()
