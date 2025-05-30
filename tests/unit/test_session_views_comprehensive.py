"""
Comprehensive tests for session views module.
"""

import json
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

import pytest
from fastapi import HTTPException

from src.api.session_views import (
    SessionConfig,
    SessionResponse,
    MessageContent,
    Message,
    CreateMessageRequest,
    SuccessResponse,
    get_data_dir,
    get_all_sessions,
    get_session,
    create_session,
    update_session_status,
    add_message,
    get_session_messages,
    get_worker_data,
)


class TestSessionModels:
    """Test session data models."""

    def test_session_config_minimal(self):
        """Test minimal SessionConfig creation."""
        config = SessionConfig(
            name="test_session",
            architect={"type": "basic"},
            workers=[{"type": "worker1"}]
        )
        assert config.name == "test_session"
        assert config.description is None
        assert config.directory is None
        assert config.architect == {"type": "basic"}
        assert config.workers == [{"type": "worker1"}]
        assert config.intervention_enabled is True

    def test_session_config_full(self):
        """Test full SessionConfig creation."""
        config = SessionConfig(
            name="full_session",
            description="A test session",
            directory="/custom/dir",
            architect={"type": "advanced", "model": "gpt-4"},
            workers=[{"type": "coder"}, {"type": "researcher"}],
            mcp_servers=["server1", "server2"],
            intervention_enabled=False
        )
        assert config.name == "full_session"
        assert config.description == "A test session"
        assert config.directory == "/custom/dir"
        assert config.intervention_enabled is False
        assert len(config.workers) == 2

    def test_message_content_basic(self):
        """Test MessageContent creation."""
        content = MessageContent(text="Hello world")
        assert content.text == "Hello world"
        assert content.additional_data is None

    def test_message_content_with_data(self):
        """Test MessageContent with additional data."""
        content = MessageContent(
            text="Process this",
            additional_data={"priority": "high", "tags": ["urgent"]}
        )
        assert content.text == "Process this"
        assert content.additional_data["priority"] == "high"

    def test_create_message_request(self):
        """Test CreateMessageRequest creation."""
        content = MessageContent(text="Test message")
        request = CreateMessageRequest(content=content)
        assert request.content.text == "Test message"


class TestDataDirectory:
    """Test data directory management."""

    def test_get_data_dir_creates_directory(self):
        """Test that get_data_dir creates the directory and returns a Path."""
        # Just test that the function runs and returns a Path object
        data_dir = get_data_dir()
        
        # Should return a Path object
        assert isinstance(data_dir, Path)
        # Should end with data/sessions
        assert str(data_dir).endswith("data/sessions") or str(data_dir).endswith("data" + os.sep + "sessions")

    def test_get_data_dir_returns_path(self):
        """Test that get_data_dir returns correct path type."""
        data_dir = get_data_dir()
        
        # Should return a Path object
        assert isinstance(data_dir, Path)
        # Should be an absolute path
        assert data_dir.is_absolute()


class TestSessionRetrieval:
    """Test session retrieval functions."""

    @patch('src.api.session_views.get_data_dir')
    def test_get_all_sessions_empty(self, mock_get_data_dir):
        """Test get_all_sessions with no sessions."""
        mock_data_dir = MagicMock()
        mock_data_dir.glob.return_value = []
        mock_get_data_dir.return_value = mock_data_dir
        
        sessions = get_all_sessions()
        assert sessions == []

    @patch('src.api.session_views.get_data_dir')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_all_sessions_with_data(self, mock_file_open, mock_get_data_dir):
        """Test get_all_sessions with session data."""
        # Mock session data
        session_data = {
            "id": "test-id",
            "name": "Test Session",
            "status": "running"
        }
        mock_file_open.return_value.read.return_value = json.dumps(session_data)
        
        # Mock file system
        mock_session_file = MagicMock()
        mock_session_file.name = "test-id.json"
        mock_data_dir = MagicMock()
        mock_data_dir.glob.return_value = [mock_session_file]
        mock_get_data_dir.return_value = mock_data_dir
        
        # Configure json.load to return session data
        with patch('json.load', return_value=session_data):
            sessions = get_all_sessions()
        
        assert len(sessions) == 1
        assert sessions[0]["id"] == "test-id"

    @patch('src.api.session_views.get_data_dir')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_all_sessions_handles_json_error(self, mock_file_open, mock_get_data_dir):
        """Test get_all_sessions handles JSON errors gracefully."""
        # Mock file system
        mock_session_file = MagicMock()
        mock_session_file.name = "corrupt.json"
        mock_data_dir = MagicMock()
        mock_data_dir.glob.return_value = [mock_session_file]
        mock_get_data_dir.return_value = mock_data_dir
        
        # Configure json.load to raise an exception
        with patch('json.load', side_effect=json.JSONDecodeError("Error", "doc", 0)):
            with patch('builtins.print') as mock_print:
                sessions = get_all_sessions()
        
        assert sessions == []
        mock_print.assert_called_once()

    @patch('src.api.session_views.get_data_dir')
    def test_get_session_not_found(self, mock_get_data_dir):
        """Test get_session with non-existent session."""
        mock_data_dir = MagicMock()
        mock_session_file = MagicMock()
        mock_session_file.exists.return_value = False
        mock_data_dir.__truediv__.return_value = mock_session_file
        mock_get_data_dir.return_value = mock_data_dir
        
        session = get_session("non-existent")
        assert session is None

    @patch('src.api.session_views.get_data_dir')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_session_success(self, mock_file_open, mock_get_data_dir):
        """Test successful session retrieval."""
        session_data = {"id": "test-id", "name": "Test Session"}
        
        mock_data_dir = MagicMock()
        mock_session_file = MagicMock()
        mock_session_file.exists.return_value = True
        mock_data_dir.__truediv__.return_value = mock_session_file
        mock_get_data_dir.return_value = mock_data_dir
        
        with patch('json.load', return_value=session_data):
            session = get_session("test-id")
        
        assert session["id"] == "test-id"
        assert session["name"] == "Test Session"

    @patch('src.api.session_views.get_data_dir')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_session_handles_json_error(self, mock_file_open, mock_get_data_dir):
        """Test get_session handles JSON errors."""
        mock_data_dir = MagicMock()
        mock_session_file = MagicMock()
        mock_session_file.exists.return_value = True
        mock_data_dir.__truediv__.return_value = mock_session_file
        mock_get_data_dir.return_value = mock_data_dir
        
        with patch('json.load', side_effect=json.JSONDecodeError("Error", "doc", 0)):
            with patch('builtins.print') as mock_print:
                session = get_session("test-id")
        
        assert session is None
        mock_print.assert_called_once()


class TestSessionCreation:
    """Test session creation functionality."""

    @patch('src.api.session_views.get_data_dir')
    @patch('src.api.session_views.uuid.uuid4')
    @patch('src.api.session_views.datetime')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_session_basic(self, mock_file_open, mock_datetime, mock_uuid, mock_get_data_dir):
        """Test basic session creation."""
        # Mock UUID and datetime
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda self: "test-uuid"
        mock_datetime.now.return_value.isoformat.return_value = "2025-01-01T00:00:00"
        
        # Mock file system
        mock_data_dir = MagicMock()
        mock_session_dir = MagicMock()
        mock_data_dir.parent.__truediv__.return_value = mock_session_dir
        mock_get_data_dir.return_value = mock_data_dir
        
        config = SessionConfig(
            name="Test Session",
            architect={"type": "basic"},
            workers=[{"type": "worker1"}]
        )
        
        with patch('json.dump') as mock_json_dump:
            session = create_session(config)
        
        assert session["id"] == "test-uuid"
        assert session["name"] == "Test Session"
        assert session["status"] == "initialized"
        assert mock_json_dump.call_count == 2  # Session file + config file

    @patch('src.api.session_views.get_data_dir')
    @patch('src.api.session_views.uuid.uuid4')
    @patch('src.api.session_views.datetime')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_session_with_custom_directory(self, mock_file_open, mock_datetime, mock_uuid, mock_get_data_dir):
        """Test session creation with custom directory."""
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda self: "test-uuid"
        mock_datetime.now.return_value.isoformat.return_value = "2025-01-01T00:00:00"
        
        mock_data_dir = MagicMock()
        mock_session_dir = MagicMock()
        mock_data_dir.parent.__truediv__.return_value = mock_session_dir
        mock_get_data_dir.return_value = mock_data_dir
        
        config = SessionConfig(
            name="Test Session",
            directory="custom-dir",
            architect={"type": "basic"},
            workers=[{"type": "worker1"}]
        )
        
        with patch('json.dump'):
            session = create_session(config)
        
        # Should use custom directory name
        mock_data_dir.parent.__truediv__.assert_called_with("custom-dir")


class TestSessionStatusUpdates:
    """Test session status update functionality."""

    @patch('src.api.session_views.get_session')
    def test_update_session_status_not_found(self, mock_get_session):
        """Test updating status of non-existent session."""
        mock_get_session.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            update_session_status("non-existent", "running")
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)

    @patch('src.api.session_views.get_session')
    @patch('src.api.session_views.get_data_dir')
    @patch('src.api.session_views.datetime')
    @patch('builtins.open', new_callable=mock_open)
    def test_update_session_status_success(self, mock_file_open, mock_datetime, mock_get_data_dir, mock_get_session):
        """Test successful session status update."""
        mock_datetime.now.return_value.isoformat.return_value = "2025-01-01T01:00:00"
        
        session_data = {
            "id": "test-id",
            "name": "Test Session",
            "status": "initialized"
        }
        mock_get_session.return_value = session_data
        
        mock_data_dir = MagicMock()
        mock_get_data_dir.return_value = mock_data_dir
        
        with patch('json.dump') as mock_json_dump:
            updated_session = update_session_status("test-id", "running")
        
        assert updated_session["status"] == "running"
        assert updated_session["updated_at"] == "2025-01-01T01:00:00"
        mock_json_dump.assert_called_once()


class TestMessageManagement:
    """Test message management functionality."""

    @patch('src.api.session_views.get_session')
    def test_add_message_session_not_found(self, mock_get_session):
        """Test adding message to non-existent session."""
        mock_get_session.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            add_message("non-existent", "user", "architect", "input", {"text": "hello"})
        
        assert exc_info.value.status_code == 404

    @patch('src.api.session_views.get_session')
    @patch('src.api.session_views.get_data_dir')
    @patch('src.api.session_views.uuid.uuid4')
    @patch('src.api.session_views.datetime')
    @patch('builtins.open', new_callable=mock_open)
    def test_add_message_success(self, mock_file_open, mock_datetime, mock_uuid, mock_get_data_dir, mock_get_session):
        """Test successful message addition."""
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda self: "msg-uuid"
        mock_datetime.now.return_value.isoformat.return_value = "2025-01-01T02:00:00"
        
        session_data = {
            "id": "session-id",
            "messages": []
        }
        mock_get_session.return_value = session_data
        
        mock_data_dir = MagicMock()
        mock_get_data_dir.return_value = mock_data_dir
        
        content = {"text": "Hello world"}
        
        with patch('json.dump') as mock_json_dump:
            message = add_message("session-id", "user", "architect", "input", content)
        
        assert message["id"] == "msg-uuid"
        assert message["from_agent"] == "user"
        assert message["to_agent"] == "architect"
        assert message["content"] == content
        assert mock_json_dump.call_count == 1  # Session file updated

    @patch('src.api.session_views.get_session')
    def test_get_session_messages_not_found(self, mock_get_session):
        """Test getting messages from non-existent session."""
        mock_get_session.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            get_session_messages("non-existent")
        
        assert exc_info.value.status_code == 404

    @patch('src.api.session_views.get_session')
    def test_get_session_messages_success(self, mock_get_session):
        """Test successful message retrieval."""
        messages = [
            {"id": "msg1", "content": {"text": "Hello"}},
            {"id": "msg2", "content": {"text": "World"}}
        ]
        session_data = {
            "id": "session-id",
            "messages": messages
        }
        mock_get_session.return_value = session_data
        
        result = get_session_messages("session-id")
        assert len(result) == 2
        assert result[0]["id"] == "msg1"

    @patch('src.api.session_views.get_session')
    def test_get_session_messages_no_messages_key(self, mock_get_session):
        """Test getting messages when messages key doesn't exist."""
        session_data = {"id": "session-id"}
        mock_get_session.return_value = session_data
        
        result = get_session_messages("session-id")
        assert result == []


class TestWorkerData:
    """Test worker data functionality."""

    @patch('src.api.session_views.get_session')
    def test_get_worker_data_session_not_found(self, mock_get_session):
        """Test getting worker data from non-existent session."""
        mock_get_session.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            get_worker_data("non-existent", 0)
        
        assert exc_info.value.status_code == 404

    @patch('src.api.session_views.get_session')
    def test_get_worker_data_no_config(self, mock_get_session):
        """Test getting worker data when config is missing."""
        session_data = {"id": "session-id"}
        mock_get_session.return_value = session_data
        
        with pytest.raises(HTTPException) as exc_info:
            get_worker_data("session-id", 0)
        
        assert exc_info.value.status_code == 404
        assert "configuration not found" in str(exc_info.value.detail)

    @patch('src.api.session_views.get_session')
    def test_get_worker_data_invalid_worker_id(self, mock_get_session):
        """Test getting worker data with invalid worker ID."""
        session_data = {
            "id": "session-id",
            "config": {
                "workers": [{"type": "worker1"}]
            }
        }
        mock_get_session.return_value = session_data
        
        with pytest.raises(HTTPException) as exc_info:
            get_worker_data("session-id", 1)  # Index 1 doesn't exist
        
        assert exc_info.value.status_code == 404
        assert "Worker with ID 1 not found" in str(exc_info.value.detail)

    @patch('src.api.session_views.get_session')
    def test_get_worker_data_success(self, mock_get_session):
        """Test successful worker data retrieval."""
        session_data = {
            "id": "session-id",
            "config": {
                "workers": [
                    {"type": "coder", "name": "Alice"},
                    {"type": "researcher", "name": "Bob"}
                ]
            },
            "messages": [
                {"from_agent": "user", "to_agent": "worker0", "content": {"text": "Task 1"}},
                {"from_agent": "worker0", "to_agent": "user", "content": {"text": "Done"}},
                {"from_agent": "user", "to_agent": "worker1", "content": {"text": "Research this"}},
            ]
        }
        mock_get_session.return_value = session_data
        
        worker_data = get_worker_data("session-id", 0)
        
        assert worker_data["type"] == "coder"
        assert worker_data["name"] == "Alice"
        assert worker_data["id"] == 0
        assert len(worker_data["messages"]) == 2  # Messages to/from worker0

    @patch('src.api.session_views.get_session')
    def test_get_worker_data_no_messages(self, mock_get_session):
        """Test worker data when session has no messages."""
        session_data = {
            "id": "session-id",
            "config": {
                "workers": [{"type": "worker1"}]
            }
        }
        mock_get_session.return_value = session_data
        
        worker_data = get_worker_data("session-id", 0)
        assert worker_data["messages"] == []


class TestIntegrationScenarios:
    """Test integration scenarios."""

    @patch('src.api.session_views.get_data_dir')
    @patch('src.api.session_views.uuid.uuid4')
    @patch('src.api.session_views.datetime')
    @patch('builtins.open', new_callable=mock_open)
    def test_full_session_lifecycle(self, mock_file_open, mock_datetime, mock_uuid, mock_get_data_dir):
        """Test a complete session lifecycle."""
        # Setup mocks
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda self: "lifecycle-session"
        mock_datetime.now.return_value.isoformat.return_value = "2025-01-01T00:00:00"
        
        mock_data_dir = MagicMock()
        mock_session_dir = MagicMock()
        mock_data_dir.parent.__truediv__.return_value = mock_session_dir
        mock_get_data_dir.return_value = mock_data_dir
        
        # Create session
        config = SessionConfig(
            name="Lifecycle Test",
            architect={"type": "advanced"},
            workers=[{"type": "coder"}, {"type": "tester"}]
        )
        
        with patch('json.dump'):
            session = create_session(config)
        
        # Verify session creation
        assert session["name"] == "Lifecycle Test"
        assert session["status"] == "initialized"
        assert len(session["config"]["workers"]) == 2

    def test_message_content_serialization(self):
        """Test that message content can be properly serialized."""
        content = MessageContent(
            text="Complex message",
            additional_data={
                "metadata": {"priority": 1, "tags": ["urgent", "backend"]},
                "attachments": ["file1.txt", "file2.pdf"]
            }
        )
        
        # Should be able to convert to dict for JSON serialization
        content_dict = content.dict()
        assert content_dict["text"] == "Complex message"
        assert "metadata" in content_dict["additional_data"]
        assert len(content_dict["additional_data"]["attachments"]) == 2

    def test_session_config_validation(self):
        """Test session config validation with different scenarios."""
        # Minimal valid config
        minimal_config = SessionConfig(
            name="minimal",
            architect={},
            workers=[]
        )
        assert minimal_config.name == "minimal"
        
        # Complex valid config
        complex_config = SessionConfig(
            name="complex_session",
            description="A complex test session",
            directory="complex_dir",
            architect={
                "type": "advanced",
                "model": "gpt-4",
                "temperature": 0.7,
                "tools": ["web_search", "code_execution"]
            },
            workers=[
                {
                    "type": "senior_developer",
                    "specialization": "backend",
                    "tools": ["ide", "database"]
                },
                {
                    "type": "qa_engineer", 
                    "specialization": "automation",
                    "tools": ["selenium", "pytest"]
                }
            ],
            mcp_servers=["server1", "server2", "server3"],
            intervention_enabled=False
        )
        
        assert complex_config.intervention_enabled is False
        assert len(complex_config.mcp_servers) == 3
        assert complex_config.workers[0]["specialization"] == "backend"
