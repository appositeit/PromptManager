"""
Comprehensive unit tests for API router endpoints
Tests all router functionality including directories, filesystem, and error handling
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from fastapi import HTTPException
from typing import List, Dict

from src.api.router import (
    router,
    get_prompt_service_dependency,
    get_directory_name,
    PromptCreate,
    PromptUpdate,
    DirectoryCreate,
    DirectoryUpdate,
    DirectoryStatusToggle,
    PromptExpandRequest,
    PromptRenameRequest,
    FilesystemPathRequest
)
from src.models.unified_prompt import Prompt
from src.models.prompt import PromptDirectory
from src.services.prompt_service import PromptService


class TestRouterHelperFunctions:
    """Test helper functions in the router"""
    
    def test_get_directory_name_with_config(self):
        """Test get_directory_name when directory config exists"""
        with patch('src.api.router.get_directory_by_path') as mock_get_dir:
            mock_get_dir.return_value = {"name": "Test Directory", "path": "/test/path"}
            
            result = get_directory_name("/test/path")
            assert result == "Test Directory"
            mock_get_dir.assert_called_once_with("/test/path")
    
    def test_get_directory_name_without_config(self):
        """Test get_directory_name when directory config doesn't exist"""
        with patch('src.api.router.get_directory_by_path') as mock_get_dir:
            mock_get_dir.return_value = None
            
            result = get_directory_name("/test/path/subdir")
            assert result == "subdir"
            mock_get_dir.assert_called_once_with("/test/path/subdir")


class TestRouterModels:
    """Test router Pydantic models"""
    
    def test_prompt_create_model(self):
        """Test PromptCreate model validation"""
        data = {
            "name": "test_prompt",
            "content": "Test content",
            "directory": "/test/dir",
            "description": "Test description",
            "tags": ["test", "example"]
        }
        prompt = PromptCreate(**data)
        assert prompt.name == "test_prompt"
        assert prompt.content == "Test content"
        assert prompt.directory == "/test/dir"
        assert prompt.description == "Test description"
        assert prompt.tags == ["test", "example"]
    
    def test_prompt_create_minimal(self):
        """Test PromptCreate with minimal required fields"""
        data = {
            "name": "test_prompt",
            "directory": "/test/dir"
        }
        prompt = PromptCreate(**data)
        assert prompt.name == "test_prompt"
        assert prompt.content == ""
        assert prompt.directory == "/test/dir"
        assert prompt.description is None
        assert prompt.tags is None
    
    def test_prompt_update_model(self):
        """Test PromptUpdate model validation"""
        data = {
            "content": "Updated content",
            "description": "Updated description",
            "tags": ["updated", "test"]
        }
        update = PromptUpdate(**data)
        assert update.content == "Updated content"
        assert update.description == "Updated description"
        assert update.tags == ["updated", "test"]
    
    def test_directory_create_model(self):
        """Test DirectoryCreate model validation"""
        data = {
            "path": "/test/directory",
            "name": "Test Directory",
            "description": "A test directory"
        }
        directory = DirectoryCreate(**data)
        assert directory.path == "/test/directory"
        assert directory.name == "Test Directory"
        assert directory.description == "A test directory"
    
    def test_prompt_expand_request_model(self):
        """Test PromptExpandRequest model validation"""
        data = {
            "prompt_id": "test_prompt",
            "directory": "/test/dir"
        }
        expand_req = PromptExpandRequest(**data)
        assert expand_req.prompt_id == "test_prompt"
        assert expand_req.directory == "/test/dir"
    
    def test_prompt_rename_request_model(self):
        """Test PromptRenameRequest model validation"""
        data = {
            "old_id": "old_prompt",
            "new_name": "new_prompt",
            "content": "New content",
            "description": "New description",
            "tags": ["new", "tags"]
        }
        rename_req = PromptRenameRequest(**data)
        assert rename_req.old_id == "old_prompt"
        assert rename_req.new_name == "new_prompt"
        assert rename_req.content == "New content"
        assert rename_req.description == "New description"
        assert rename_req.tags == ["new", "tags"]
    
    def test_filesystem_path_request_model(self):
        """Test FilesystemPathRequest model validation"""
        data = {"partial_path": "/partial/path"}
        fs_req = FilesystemPathRequest(**data)
        assert fs_req.partial_path == "/partial/path"


class TestRouterEndpoints:
    """Test router endpoint functionality with mocked dependencies"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_prompt_service = Mock(spec=PromptService)
        self.mock_prompt = Mock(spec=Prompt)
        self.mock_prompt.id = "test_prompt"
        self.mock_prompt.name = "Test Prompt"
        self.mock_prompt.content = "Test content"
        self.mock_prompt.description = "Test description"
        self.mock_prompt.tags = ["test"]
        self.mock_prompt.directory = "/test/dir"
        self.mock_prompt.unique_id = "test_dir/test_prompt"
        self.mock_prompt.updated_at = datetime.now(timezone.utc)
        self.mock_prompt.created_at = datetime.now(timezone.utc)
        self.mock_prompt.model_dump = Mock(return_value={
            "id": "test_prompt",
            "name": "Test Prompt",
            "content": "Test content",
            "description": "Test description",
            "tags": ["test"],
            "directory": "/test/dir",
            "unique_id": "test_dir/test_prompt",
            "updated_at": "2023-01-01T00:00:00Z",
            "created_at": "2023-01-01T00:00:00Z"
        })
    
    @pytest.mark.asyncio
    async def test_get_all_prompts_empty(self):
        """Test get_all_prompts when no prompts exist"""
        self.mock_prompt_service.prompts = {}
        
        with patch('src.api.router.get_directory_name', return_value="Test Dir"):
            from src.api.router import get_all_prompts
            result = await get_all_prompts(self.mock_prompt_service)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_all_prompts_with_data(self):
        """Test get_all_prompts with existing prompts"""
        self.mock_prompt_service.prompts = {"test_prompt": self.mock_prompt}
        
        with patch('src.api.router.get_directory_name', return_value="Test Dir"):
            from src.api.router import get_all_prompts
            result = await get_all_prompts(self.mock_prompt_service)
        
        assert len(result) == 1
        assert result[0]["id"] == "test_prompt"
        assert result[0]["name"] == "Test Prompt"
        assert result[0]["directory_name"] == "Test Dir"
    
    @pytest.mark.asyncio
    async def test_get_prompt_suggestions_success(self):
        """Test get_prompt_suggestions successful search"""
        mock_suggestions = [
            {"id": "prompt1", "name": "Prompt 1"},
            {"id": "prompt2", "name": "Prompt 2"}
        ]
        self.mock_prompt_service.search_prompt_suggestions.return_value = mock_suggestions
        
        from src.api.router import get_prompt_suggestions
        result = await get_prompt_suggestions("test", "exclude_me", self.mock_prompt_service)
        
        assert result == mock_suggestions
        self.mock_prompt_service.search_prompt_suggestions.assert_called_once_with("test", "exclude_me")
    
    @pytest.mark.asyncio
    async def test_get_prompt_suggestions_error(self):
        """Test get_prompt_suggestions with service error"""
        self.mock_prompt_service.search_prompt_suggestions.side_effect = Exception("Search failed")
        
        from src.api.router import get_prompt_suggestions
        with pytest.raises(HTTPException) as exc_info:
            await get_prompt_suggestions("test", None, self.mock_prompt_service)
        
        assert exc_info.value.status_code == 500
        assert "Internal server error" in exc_info.value.detail


class TestRouterDependencyEdgeCases:
    """Test router dependency injection edge cases"""
    
    @pytest.mark.asyncio
    async def test_get_prompt_service_dependency_not_implemented(self):
        """Test get_prompt_service_dependency raises NotImplementedError"""
        with pytest.raises(NotImplementedError) as exc_info:
            await get_prompt_service_dependency()
        
        assert "PromptService dependency not configured" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
