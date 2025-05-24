"""
Unit tests for API router functionality.
Tests individual route functions in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from datetime import datetime, timezone

# Import the router and models
from src.api.router import router, get_all_prompts, create_new_prompt, get_prompt_by_id, update_existing_prompt, delete_existing_prompt, rename_prompt_endpoint
from src.models.unified_prompt import Prompt
from src.services.prompt_service import PromptService


class TestAPIRouterUnits:
    """Unit tests for API router functions."""
    
    @pytest.fixture
    def mock_prompt_service(self):
        """Create a mock PromptService for testing."""
        service = Mock(spec=PromptService)
        return service
    
    @pytest.fixture
    def sample_prompt(self):
        """Create a sample prompt for testing."""
        return Prompt(
            id="test/sample_prompt",
            name="sample_prompt",
            filename="sample_prompt.md", 
            directory="/tmp/test",
            content="Test content",
            description="Test description",
            tags=["test", "sample"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    @pytest.mark.asyncio
    async def test_get_all_prompts_success(self, mock_prompt_service, sample_prompt):
        """Test successful retrieval of all prompts."""
        # Setup
        mock_prompt_service.prompts = {"test/sample_prompt": sample_prompt}
        
        with patch('src.api.router.get_directory_name', return_value="Test Directory"):
            # Execute
            result = await get_all_prompts(mock_prompt_service)
            
            # Verify
            assert len(result) == 1
            assert result[0]["id"] == "test/sample_prompt"
            assert result[0]["name"] == "sample_prompt"
            assert result[0]["description"] == "Test description"
            assert result[0]["tags"] == ["test", "sample"]
            assert result[0]["directory_name"] == "Test Directory"

    @pytest.mark.asyncio
    async def test_get_all_prompts_empty(self, mock_prompt_service):
        """Test retrieval when no prompts exist."""
        # Setup
        mock_prompt_service.prompts = {}
        
        # Execute
        result = await get_all_prompts(mock_prompt_service)
        
        # Verify
        assert result == []

    @pytest.mark.asyncio
    async def test_create_new_prompt_success(self, mock_prompt_service, sample_prompt):
        """Test successful prompt creation."""
        from src.api.router import PromptCreate
        
        # Setup
        prompt_data = PromptCreate(
            name="new_prompt",
            content="New content",
            directory="/tmp/test",
            description="New description",
            tags=["new", "test"]
        )
        
        mock_prompt_service.get_prompt.return_value = None  # Prompt doesn't exist
        mock_prompt_service.create_prompt.return_value = sample_prompt
        
        with patch('src.api.router.get_directory_name', return_value="Test Directory"):
            # Execute
            result = await create_new_prompt(prompt_data, mock_prompt_service)
            
            # Verify
            mock_prompt_service.create_prompt.assert_called_once_with(
                name="new_prompt",
                content="New content", 
                directory="/tmp/test",
                description="New description",
                tags=["new", "test"]
            )
            assert result["id"] == "test/sample_prompt"
            assert result["directory_name"] == "Test Directory"

    @pytest.mark.asyncio
    async def test_create_new_prompt_duplicate(self, mock_prompt_service, sample_prompt):
        """Test prompt creation when duplicate exists."""
        from src.api.router import PromptCreate
        
        # Setup
        prompt_data = PromptCreate(
            name="existing_prompt",
            content="Content",
            directory="/tmp/test"
        )
        
        mock_prompt_service.get_prompt.return_value = sample_prompt  # Prompt exists
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await create_new_prompt(prompt_data, mock_prompt_service)
        
        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_new_prompt_sanitization(self, mock_prompt_service, sample_prompt):
        """Test prompt creation with name sanitization."""
        from src.api.router import PromptCreate
        
        # Setup
        prompt_data = PromptCreate(
            name="prompt with spaces",
            content="Content",
            directory="/tmp/test"
        )
        
        mock_prompt_service.get_prompt.return_value = None
        mock_prompt_service.create_prompt.return_value = sample_prompt
        
        with patch('src.api.router.get_directory_name', return_value="Test Directory"):
            # Execute
            result = await create_new_prompt(prompt_data, mock_prompt_service)
            
            # Verify sanitization occurred
            mock_prompt_service.create_prompt.assert_called_once()
            call_args = mock_prompt_service.create_prompt.call_args[1]
            assert call_args["name"] == "prompt_with_spaces"
            assert "sanitized_message" in result

    @pytest.mark.asyncio
    async def test_get_prompt_by_id_success(self, mock_prompt_service, sample_prompt):
        """Test successful prompt retrieval by ID."""
        # Setup
        mock_prompt_service.get_prompt.return_value = sample_prompt
        mock_prompt_service.expand_inclusions.return_value = (
            "expanded content", 
            set(["dep1", "dep2"]), 
            ["warning1"]
        )
        
        with patch('src.api.router.get_directory_by_path', return_value={"name": "Test Dir", "path": "/tmp/test"}):
            # Execute
            result = await get_prompt_by_id("test/sample_prompt", None, mock_prompt_service)
            
            # Verify
            # Note: get_prompt is called multiple times - once for main prompt, once for each dependency
            assert mock_prompt_service.get_prompt.call_count >= 1
            first_call = mock_prompt_service.get_prompt.call_args_list[0]
            assert first_call.args == ("test/sample_prompt", None)
            
            assert result["id"] == "test/sample_prompt"
            assert result["name"] == "sample_prompt"
            assert "directory_info" in result
            assert result["directory_info"]["name"] == "Test Dir"
            assert len(result["dependencies"]) == 2
            assert result["warnings"] == ["warning1"]

    @pytest.mark.asyncio
    async def test_get_prompt_by_id_not_found(self, mock_prompt_service):
        """Test prompt retrieval when prompt doesn't exist.""" 
        # Setup
        mock_prompt_service.get_prompt.return_value = None
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await get_prompt_by_id("nonexistent", None, mock_prompt_service)
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_existing_prompt_success(self, mock_prompt_service, sample_prompt):
        """Test successful prompt update."""
        from src.api.router import PromptUpdate
        
        # Setup
        update_data = PromptUpdate(
            content="Updated content",
            description="Updated description",
            tags=["updated", "test"]
        )
        
        mock_prompt_service.get_prompt.return_value = sample_prompt
        mock_prompt_service.save_prompt.return_value = True
        
        with patch('src.api.router.get_directory_name', return_value="Test Directory"):
            # Execute
            result = await update_existing_prompt("test/sample_prompt", update_data, mock_prompt_service)
            
            # Verify
            mock_prompt_service.save_prompt.assert_called_once()
            assert result["content"] == "Updated content"
            assert result["description"] == "Updated description"
            assert result["tags"] == ["updated", "test"]

    @pytest.mark.asyncio
    async def test_update_existing_prompt_not_found(self, mock_prompt_service):
        """Test prompt update when prompt doesn't exist."""
        from src.api.router import PromptUpdate
        
        # Setup
        update_data = PromptUpdate(content="Updated content")
        mock_prompt_service.get_prompt.return_value = None
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await update_existing_prompt("nonexistent", update_data, mock_prompt_service)
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_existing_prompt_success(self, mock_prompt_service):
        """Test successful prompt deletion."""
        # Setup
        mock_prompt_service.delete_prompt.return_value = True
        
        # Execute
        result = await delete_existing_prompt("test/sample_prompt", mock_prompt_service)
        
        # Verify
        mock_prompt_service.delete_prompt.assert_called_once_with("test/sample_prompt")
        assert "deleted successfully" in result["message"]

    @pytest.mark.asyncio 
    async def test_delete_existing_prompt_not_found(self, mock_prompt_service):
        """Test prompt deletion when prompt doesn't exist."""
        # Setup
        mock_prompt_service.delete_prompt.return_value = False
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await delete_existing_prompt("nonexistent", mock_prompt_service)
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_rename_prompt_success(self, mock_prompt_service, sample_prompt):
        """Test successful prompt rename."""
        from src.api.router import PromptRenameRequest
        
        # Setup  
        rename_data = PromptRenameRequest(
            old_id="test/old_prompt",
            new_name="new_prompt_name",
            content="Updated content"
        )
        
        old_prompt = sample_prompt
        new_prompt = Prompt(
            id="test/new_prompt_name",
            name="new_prompt_name",
            filename="new_prompt_name.md",
            directory="/tmp/test",
            content="Updated content",
            description="Test description",
            tags=["test", "sample"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        mock_prompt_service.get_prompt.side_effect = [old_prompt, None, new_prompt]  # old exists, new doesn't exist, return new after rename
        mock_prompt_service.rename_prompt.return_value = True
        
        with patch('src.api.router.get_directory_name', return_value="Test Directory"):
            # Execute
            result = await rename_prompt_endpoint(rename_data, mock_prompt_service)
            
            # Verify
            mock_prompt_service.rename_prompt.assert_called_once_with(
                old_identifier="test/old_prompt",
                new_name="new_prompt_name",
                content="Updated content",
                description=None,
                tags=None
            )
            assert result["id"] == "test/new_prompt_name"
            assert result["name"] == "new_prompt_name"

    @pytest.mark.asyncio
    async def test_rename_prompt_old_not_found(self, mock_prompt_service):
        """Test rename when old prompt doesn't exist."""
        from src.api.router import PromptRenameRequest
        
        # Setup
        rename_data = PromptRenameRequest(old_id="nonexistent", new_name="new_name")
        mock_prompt_service.get_prompt.return_value = None
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await rename_prompt_endpoint(rename_data, mock_prompt_service)
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_rename_prompt_new_exists(self, mock_prompt_service, sample_prompt):
        """Test rename when new prompt name already exists."""
        from src.api.router import PromptRenameRequest
        
        # Setup
        rename_data = PromptRenameRequest(old_id="test/old_prompt", new_name="existing_name")
        
        old_prompt = sample_prompt
        existing_prompt = sample_prompt
        
        mock_prompt_service.get_prompt.side_effect = [old_prompt, existing_prompt]  # old exists, new also exists
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await rename_prompt_endpoint(rename_data, mock_prompt_service)
        
        assert exc_info.value.status_code == 409  # Conflict

    @pytest.mark.asyncio
    async def test_rename_prompt_sanitization(self, mock_prompt_service, sample_prompt):
        """Test rename with name sanitization."""
        from src.api.router import PromptRenameRequest
        
        # Setup
        rename_data = PromptRenameRequest(
            old_id="test/old_prompt",
            new_name="name with spaces"
        )
        
        mock_prompt_service.get_prompt.side_effect = [sample_prompt, None, sample_prompt]
        mock_prompt_service.rename_prompt.return_value = True
        
        with patch('src.api.router.get_directory_name', return_value="Test Directory"):
            # Execute
            result = await rename_prompt_endpoint(rename_data, mock_prompt_service)
            
            # Verify sanitization
            mock_prompt_service.rename_prompt.assert_called_once()
            call_args = mock_prompt_service.rename_prompt.call_args[1]
            assert call_args["new_name"] == "name_with_spaces"


class TestAPIRouterValidation:
    """Test API router input validation and error handling."""
    
    @pytest.fixture
    def mock_prompt_service(self):
        return Mock(spec=PromptService)

    @pytest.mark.asyncio
    async def test_create_prompt_validation_error(self, mock_prompt_service):
        """Test prompt creation with validation error."""
        from src.api.router import PromptCreate
        
        # Setup
        prompt_data = PromptCreate(
            name="",  # Empty name should cause validation error
            directory="/tmp/test"
        )
        
        mock_prompt_service.create_prompt.side_effect = ValueError("Prompt name cannot be empty")
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await create_new_prompt(prompt_data, mock_prompt_service)
        
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_prompt_save_failure(self, mock_prompt_service, sample_prompt):
        """Test prompt update when save fails."""
        from src.api.router import PromptUpdate
        
        # Setup
        update_data = PromptUpdate(content="Updated content")
        mock_prompt_service.get_prompt.return_value = sample_prompt
        mock_prompt_service.save_prompt.return_value = False  # Save fails
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await update_existing_prompt("test/prompt", update_data, mock_prompt_service)
        
        assert exc_info.value.status_code == 500

    @pytest.fixture
    def sample_prompt(self):
        """Create a sample prompt for testing."""
        return Prompt(
            id="test/sample_prompt",
            name="sample_prompt", 
            filename="sample_prompt.md",
            directory="/tmp/test",
            content="Test content",
            description="Test description",
            tags=["test", "sample"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
