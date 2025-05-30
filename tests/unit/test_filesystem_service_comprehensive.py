"""
Comprehensive unit tests for FilesystemService
Tests path completion functionality and security checks
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from typing import List

from src.services.filesystem_service import FilesystemService, FilesystemCompletionResponseData


class TestFilesystemCompletionResponseData:
    """Test FilesystemCompletionResponseData model"""
    
    def test_response_data_creation(self):
        """Test creating FilesystemCompletionResponseData"""
        response = FilesystemCompletionResponseData(
            completed_path="/test/path",
            suggestions=["file1.txt", "file2.txt"],
            is_directory=True
        )
        
        assert response.completed_path == "/test/path"
        assert response.suggestions == ["file1.txt", "file2.txt"]
        assert response.is_directory is True


class TestFilesystemServiceInitialization:
    """Test FilesystemService initialization"""
    
    def test_init_with_allowed_paths(self):
        """Test initialization with custom allowed paths"""
        allowed_paths = ["/custom/path1", "/custom/path2"]
        service = FilesystemService(allowed_base_paths=allowed_paths)
        
        # Paths should be converted to absolute
        expected_paths = [os.path.abspath(p) for p in allowed_paths]
        assert service.allowed_base_paths == expected_paths
    
    def test_init_without_allowed_paths(self):
        """Test initialization with default allowed paths"""
        service = FilesystemService()
        
        expected_paths = [
            os.path.expanduser("~"),
            os.getcwd()
        ]
        assert service.allowed_base_paths == expected_paths
    
    def test_init_with_empty_allowed_paths(self):
        """Test initialization with empty allowed paths list"""
        service = FilesystemService(allowed_base_paths=[])
        
        expected_paths = [
            os.path.expanduser("~"),
            os.getcwd()
        ]
        assert service.allowed_base_paths == expected_paths


class TestFilesystemServicePathValidation:
    """Test FilesystemService path validation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.service = FilesystemService(allowed_base_paths=[self.test_dir])
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_is_path_allowed_within_base_path(self):
        """Test path validation for path within allowed base"""
        test_path = os.path.join(self.test_dir, "subdir")
        assert self.service._is_path_allowed(test_path) is True
    
    def test_is_path_allowed_exact_base_path(self):
        """Test path validation for exact base path"""
        assert self.service._is_path_allowed(self.test_dir) is True
    
    def test_is_path_allowed_outside_base_path(self):
        """Test path validation for path outside allowed base"""
        outside_path = "/completely/different/path"
        assert self.service._is_path_allowed(outside_path) is False
    
    def test_is_path_allowed_with_tilde_expansion(self):
        """Test path validation with tilde expansion"""
        # Create service with home directory allowed
        service = FilesystemService(allowed_base_paths=[os.path.expanduser("~")])
        assert service._is_path_allowed("~/Documents") is True
    
    def test_is_path_allowed_relative_path(self):
        """Test path validation with relative paths"""
        # Create a subdirectory for testing
        subdir = os.path.join(self.test_dir, "subdir")
        os.makedirs(subdir, exist_ok=True)
        
        # Change to test directory temporarily
        original_cwd = os.getcwd()
        try:
            os.chdir(self.test_dir)
            assert self.service._is_path_allowed("./subdir") is True
        finally:
            os.chdir(original_cwd)
    
    def test_is_path_allowed_parent_path_traversal(self):
        """Test path validation prevents parent path traversal"""
        # Try to access parent of allowed path
        parent_path = os.path.dirname(self.test_dir)
        assert self.service._is_path_allowed(parent_path) is False


class TestFilesystemServicePathCompletion:
    """Test FilesystemService path completion functionality"""
    
    def setup_method(self):
        """Set up test fixtures with directory structure"""
        self.test_dir = tempfile.mkdtemp()
        self.service = FilesystemService(allowed_base_paths=[self.test_dir])
        
        # Create test directory structure
        self.test_files = [
            "documents/file1.txt",
            "documents/file2.txt", 
            "downloads/archive.zip",
            "downloads/image.jpg",
            "development/project1/main.py",
            "development/project2/app.js",
            "desktop/shortcut.lnk"
        ]
        
        for file_path in self.test_files:
            full_path = os.path.join(self.test_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write("test content")
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_get_path_completions_directory_listing(self):
        """Test path completion for directory listing"""
        result = self.service.get_path_completions(self.test_dir + "/")
        
        expected_suggestions = ["desktop/", "development/", "documents/", "downloads/"]
        assert sorted(result.suggestions) == expected_suggestions
        assert result.completed_path == self.test_dir + "/"
    
    def test_get_path_completions_partial_match_single(self):
        """Test path completion with single partial match"""
        partial_path = os.path.join(self.test_dir, "desk")
        result = self.service.get_path_completions(partial_path)
        
        # Should complete to "desktop/"
        expected_completed = os.path.join(self.test_dir, "desktop/")
        assert result.completed_path == expected_completed
        assert result.suggestions == []
        assert result.is_directory is True
    
    def test_get_path_completions_partial_match_multiple(self):
        """Test path completion with multiple partial matches"""
        partial_path = os.path.join(self.test_dir, "d")
        result = self.service.get_path_completions(partial_path)
        
        expected_suggestions = ["esktop/", "evelopment/", "ocuments/", "ownloads/"]
        assert sorted(result.suggestions) == expected_suggestions
    
    def test_get_path_completions_common_prefix(self):
        """Test path completion with common prefix"""
        partial_path = os.path.join(self.test_dir, "do")
        result = self.service.get_path_completions(partial_path)
        
        # Should have "documents/" and "downloads/" as suggestions
        expected_suggestions = ["cuments/", "wnloads/"]
        assert sorted(result.suggestions) == expected_suggestions
    
    def test_get_path_completions_nonexistent_directory(self):
        """Test path completion for non-existent directory"""
        nonexistent_path = os.path.join(self.test_dir, "nonexistent", "path")
        result = self.service.get_path_completions(nonexistent_path)
        
        assert result.completed_path == nonexistent_path
        assert result.suggestions == []
        assert result.is_directory is False
    
    def test_get_path_completions_empty_path(self):
        """Test path completion with empty path"""
        with patch('os.getcwd', return_value=self.test_dir):
            with patch('os.listdir', return_value=["desktop", "development", "documents", "downloads"]):
                with patch('os.path.isdir', return_value=True):
                    # Mock current directory to test directory
                    service = FilesystemService(allowed_base_paths=[self.test_dir])
                    result = service.get_path_completions("")
                    
                    # Should list contents of current directory
                    expected_suggestions = ["desktop/", "development/", "documents/", "downloads/"]
                    assert sorted(result.suggestions) == expected_suggestions
    
    def test_get_path_completions_with_tilde(self):
        """Test path completion with tilde expansion"""
        # Mock expanduser to return our test directory for both initialization and method calls
        with patch('os.path.expanduser') as mock_expanduser:
            # Configure the mock to return appropriate values
            def side_effect(path):
                if path == "~":
                    return self.test_dir
                elif path.startswith("~/"):
                    return path.replace("~", self.test_dir, 1)
                return path
            
            mock_expanduser.side_effect = side_effect
            
            service = FilesystemService(allowed_base_paths=[self.test_dir])
            result = service.get_path_completions("~/d")
            
            # Should expand ~ and find matches starting with 'd'
            expected_suggestions = ["esktop/", "evelopment/", "ocuments/", "ownloads/"]
            assert sorted(result.suggestions) == expected_suggestions
    
    def test_get_path_completions_no_matches(self):
        """Test path completion with no matches"""
        partial_path = os.path.join(self.test_dir, "xyz")
        result = self.service.get_path_completions(partial_path)
        
        assert result.suggestions == []
        assert result.completed_path == partial_path
    
    def test_get_path_completions_hidden_files_ignored(self):
        """Test that hidden files are ignored in completion"""
        # Create hidden files
        hidden_dir = os.path.join(self.test_dir, ".hidden")
        os.makedirs(hidden_dir, exist_ok=True)
        
        result = self.service.get_path_completions(self.test_dir + "/")
        
        # Should not include .hidden/ in suggestions
        assert ".hidden/" not in result.suggestions
        expected_suggestions = ["desktop/", "development/", "documents/", "downloads/"]
        assert sorted(result.suggestions) == expected_suggestions
    
    def test_get_path_completions_permission_error(self):
        """Test path completion with permission error"""
        with patch('os.listdir', side_effect=PermissionError("Permission denied")):
            result = self.service.get_path_completions(self.test_dir + "/")
            
            assert result.completed_path == self.test_dir + "/"
            assert result.suggestions == []
            assert result.is_directory is False
    
    def test_get_path_completions_file_not_found_error(self):
        """Test path completion with FileNotFoundError"""
        with patch('os.listdir', side_effect=FileNotFoundError("Directory not found")):
            result = self.service.get_path_completions(self.test_dir + "/")
            
            assert result.completed_path == self.test_dir + "/"
            assert result.suggestions == []
            assert result.is_directory is False
    
    def test_get_path_completions_general_exception(self):
        """Test path completion with general exception"""
        with patch('os.listdir', side_effect=Exception("General error")):
            result = self.service.get_path_completions(self.test_dir + "/")
            
            assert result.completed_path == self.test_dir + "/"
            assert result.suggestions == []
            assert result.is_directory is False
    
    def test_get_path_completions_unauthorized_path(self):
        """Test path completion for unauthorized path"""
        unauthorized_path = "/unauthorized/path"
        result = self.service.get_path_completions(unauthorized_path)
        
        assert result.completed_path == unauthorized_path
        assert result.suggestions == []
        assert result.is_directory is False
    
    def test_get_path_completions_nested_directories(self):
        """Test path completion in nested directories"""
        nested_path = os.path.join(self.test_dir, "development/")
        result = self.service.get_path_completions(nested_path)
        
        expected_suggestions = ["project1/", "project2/"]
        assert sorted(result.suggestions) == expected_suggestions
        assert result.completed_path == nested_path
    
    def test_get_path_completions_exact_directory_match(self):
        """Test path completion for exact directory match"""
        exact_path = os.path.join(self.test_dir, "documents")
        result = self.service.get_path_completions(exact_path)
        
        # Should complete to documents/
        expected_completed = os.path.join(self.test_dir, "documents/")
        assert result.completed_path == expected_completed
        assert result.suggestions == []
        assert result.is_directory is True


class TestFilesystemServiceEdgeCases:
    """Test FilesystemService edge cases and error conditions"""
    
    def test_get_path_completions_relative_path_fallback(self):
        """Test path completion with relative path fallback"""
        # Test when current directory is not in allowed paths
        service = FilesystemService(allowed_base_paths=["/some/other/path"])
        
        with patch('os.getcwd', return_value="/different/path"):
            with patch.object(service, '_is_path_allowed', return_value=False):
                result = service.get_path_completions("relative/path")
                
                # Should return empty result when path not allowed
                assert result.suggestions == []
    
    def test_get_path_completions_no_allowed_paths(self):
        """Test path completion when no allowed paths configured"""
        service = FilesystemService(allowed_base_paths=[])
        
        # Should fall back to default paths
        assert len(service.allowed_base_paths) > 0
    
    def test_get_path_completions_current_dir_not_allowed(self):
        """Test path completion when current directory not in allowed paths"""
        service = FilesystemService(allowed_base_paths=["/allowed/path"])
        
        with patch.object(service, '_is_path_allowed', side_effect=[False, False]):
            result = service.get_path_completions("relative")
            
            assert result.suggestions == []
            assert result.is_directory is False
    
    def test_get_path_completions_with_allowed_base_paths_fallback(self):
        """Test path completion falls back to first allowed base path"""
        allowed_path = tempfile.mkdtemp()
        try:
            # Create some test directories in the allowed path
            os.makedirs(os.path.join(allowed_path, "testdir"), exist_ok=True)
            
            service = FilesystemService(allowed_base_paths=[allowed_path])
            
            # Test the case where user provides an empty string and current dir is not allowed
            # This should fall back to the first allowed base path
            with patch('os.getcwd', return_value="/some/disallowed/path"):
                result = service.get_path_completions("")
                
                # Should use the allowed base path as fallback and complete to testdir/
                # Since there's only one match, it should complete the path and clear suggestions
                assert result.completed_path.endswith("testdir/")
                assert result.is_directory is True
        finally:
            shutil.rmtree(allowed_path, ignore_errors=True)


class TestFilesystemServiceIntegration:
    """Integration tests for FilesystemService"""
    
    def test_real_filesystem_interaction(self):
        """Test real filesystem interaction (uses actual home directory)"""
        # Use actual home directory for integration test
        home_dir = os.path.expanduser("~")
        service = FilesystemService(allowed_base_paths=[home_dir])
        
        # Test completion in home directory
        result = service.get_path_completions("~/")
        
        # Should return actual directories in home (this test is environment-dependent)
        assert isinstance(result.suggestions, list)
        assert result.completed_path == home_dir + "/"
        
        # All suggestions should end with / for directories
        for suggestion in result.suggestions:
            assert suggestion.endswith("/")
    
    def test_security_boundary_enforcement(self):
        """Test that security boundaries are properly enforced"""
        # Create a restricted service
        temp_dir = tempfile.mkdtemp()
        try:
            service = FilesystemService(allowed_base_paths=[temp_dir])
            
            # Try to access parent directory
            parent_dir = os.path.dirname(temp_dir)
            result = service.get_path_completions(parent_dir)
            
            # Should be blocked
            assert result.suggestions == []
            assert not result.is_directory
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
