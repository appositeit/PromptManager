"""
Comprehensive unit tests for session routes and views
Tests session management API and web UI functionality
"""

import pytest
import json
import uuid
from unittest.mock import Mock, patch, AsyncMock, mock_open
from datetime import datetime
from pathlib import Path
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.api.session_routes import (
    router as session_routes_router,
    get_session,
    get_active_sessions,
    create_session,
    start_session,
    stop_session,
    send_message,
    generate_response,
    list_sessions,
    list_active_sessions,
    get_session_messages,
    get_session_page_ui,
    get_home_page
)

from src.api.session_views import (
    router as session_views_router,
    SessionConfig,
    SessionResponse,
    MessageContent,
    Message,
    CreateMessageRequest,
    get_data_dir,
    get_all_sessions,
    get_session as get_session_view,
    create_session as create_session_view,
    update_session_status,
    add_message,
    get_session_messages as get_session_messages_view,
    get_worker_data
)


class TestSessionRoutesHelpers:
    """Test session routes helper functions"""
    
    @pytest.mark.asyncio
    async def test_get_session_success(self):
        """Test get_session with successful API response"""
        mock_response = Mock()
        mock_response.json.return_value = {"id": "test_session", "name": "Test Session"}
        mock_response.raise_for_status.return_value = None
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await get_session("test_session")
            
            assert result == {"id": "test_session", "name": "Test Session"}
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        """Test get_session when session not found"""
        mock_response = Mock()
        mock_response.status_code = 404
        
        from httpx import HTTPStatusError, Request
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = HTTPStatusError(
                "Not found", request=Mock(), response=mock_response
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await get_session("nonexistent_session")
            
            assert exc_info.value.status_code == 404
            assert "Session not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_session_api_error(self):
        """Test get_session with API error"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        from httpx import HTTPStatusError
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = HTTPStatusError(
                "Server error", request=Mock(), response=mock_response
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await get_session("test_session")
            
            assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_get_session_general_error(self):
        """Test get_session with general exception"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Connection error")
            
            with pytest.raises(HTTPException) as exc_info:
                await get_session("test_session")
            
            assert exc_info.value.status_code == 500
            assert "Error" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_active_sessions_success(self):
        """Test get_active_sessions with successful response"""
        mock_response = Mock()
        mock_response.json.return_value = [{"id": "session1"}, {"id": "session2"}]
        mock_response.raise_for_status.return_value = None
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await get_active_sessions()
            
            assert result == [{"id": "session1"}, {"id": "session2"}]
    
    @pytest.mark.asyncio
    async def test_get_active_sessions_error(self):
        """Test get_active_sessions with error returns empty list"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("API error")
            
            result = await get_active_sessions()
            
            assert result == []


class TestSessionRoutesAPI:
    """Test session routes API endpoints"""
    
    def setup_method(self):
        """Set up test fixtures"""
        from fastapi import FastAPI
        self.app = FastAPI()
        self.app.include_router(session_routes_router)
        self.client = TestClient(self.app)
        self.mock_session_service = Mock()
    
    def test_create_session_success(self):
        """Test create session endpoint success"""
        mock_session = {"id": "test_session", "name": "Test Session"}
        
        with patch('src.api.session_routes.get_session_service') as mock_get_service:
            mock_get_service.return_value = self.mock_session_service
            self.mock_session_service.create_session.return_value = mock_session
            
            response = self.client.post("/api/sessions", json={"name": "Test Session"})
            
            assert response.status_code == 201
            assert response.json() == mock_session
    
    def test_create_session_error(self):
        """Test create session endpoint error"""
        with patch('src.api.session_routes.get_session_service') as mock_get_service:
            mock_get_service.side_effect = Exception("Service error")
            
            response = self.client.post("/api/sessions", json={"name": "Test Session"})
            
            assert response.status_code == 500
            assert "Error creating session" in response.json()["detail"]
    
    def test_start_session_success(self):
        """Test start session endpoint success"""
        mock_session = {"id": "test_session", "status": "running"}
        
        with patch('src.api.session_routes.get_session_service') as mock_get_service:
            mock_get_service.return_value = self.mock_session_service
            self.mock_session_service.update_session.return_value = mock_session
            
            response = self.client.post("/api/sessions/test_session/start")
            
            assert response.status_code == 200
            assert response.json() == mock_session
    
    def test_start_session_not_found(self):
        """Test start session when session not found"""
        with patch('src.api.session_routes.get_session_service') as mock_get_service:
            mock_get_service.return_value = self.mock_session_service
            self.mock_session_service.update_session.return_value = None
            
            response = self.client.post("/api/sessions/nonexistent/start")
            
            assert response.status_code == 404
            assert "Session not found" in response.json()["detail"]
    
    def test_stop_session_success(self):
        """Test stop session endpoint success"""
        mock_session = {"id": "test_session", "status": "completed"}
        
        with patch('src.api.session_routes.get_session_service') as mock_get_service:
            mock_get_service.return_value = self.mock_session_service
            self.mock_session_service.update_session.return_value = mock_session
            
            response = self.client.post("/api/sessions/test_session/stop")
            
            assert response.status_code == 200
            assert response.json() == mock_session
    
    def test_send_message_user_to_architect(self):
        """Test send message from user to architect"""
        mock_message = {"id": "msg1", "content": {"text": "Hello"}}
        mock_response = {"id": "msg2", "content": {"text": "Hi there!"}}
        
        with patch('src.api.session_routes.get_session_service') as mock_get_service:
            mock_get_service.return_value = self.mock_session_service
            self.mock_session_service.add_message.side_effect = [mock_message, mock_response]
            self.mock_session_service.get_session.return_value = {"name": "Test Session"}
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                response = self.client.post(
                    "/api/sessions/test_session/messages",
                    json={
                        "from_agent": "user",
                        "to_agent": "architect",
                        "content": {"text": "Hello"}
                    }
                )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "response" in data
    
    def test_send_message_regular(self):
        """Test send regular message (not user to architect)"""
        mock_message = {"id": "msg1", "content": {"text": "Hello"}}
        
        with patch('src.api.session_routes.get_session_service') as mock_get_service:
            mock_get_service.return_value = self.mock_session_service
            self.mock_session_service.add_message.return_value = mock_message
            
            response = self.client.post(
                "/api/sessions/test_session/messages",
                json={
                    "from_agent": "worker1",
                    "to_agent": "user",
                    "content": {"text": "Hello"}
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data == {"message": mock_message}
    
    def test_list_sessions_success(self):
        """Test list sessions endpoint"""
        mock_sessions = [{"id": "session1"}, {"id": "session2"}]
        
        with patch('src.api.session_routes.get_session_service') as mock_get_service:
            mock_get_service.return_value = self.mock_session_service
            self.mock_session_service.list_sessions.return_value = mock_sessions
            
            response = self.client.get("/api/sessions")
            
            assert response.status_code == 200
            assert response.json() == mock_sessions
    
    def test_list_active_sessions_success(self):
        """Test list active sessions endpoint"""
        mock_sessions = [{"id": "session1", "status": "running"}]
        
        with patch('src.api.session_routes.get_session_service') as mock_get_service:
            mock_get_service.return_value = self.mock_session_service
            self.mock_session_service.get_active_sessions.return_value = mock_sessions
            
            response = self.client.get("/api/sessions/active")
            
            assert response.status_code == 200
            assert response.json() == mock_sessions
    
    def test_get_session_messages_success(self):
        """Test get session messages endpoint"""
        mock_messages = [{"id": "msg1"}, {"id": "msg2"}]
        
        with patch('src.api.session_routes.get_session_service') as mock_get_service:
            mock_get_service.return_value = self.mock_session_service
            self.mock_session_service.get_session_messages.return_value = mock_messages
            
            response = self.client.get("/api/sessions/test_session/messages")
            
            assert response.status_code == 200
            assert response.json() == mock_messages


class TestSessionRoutesUI:
    """Test session routes web UI endpoints"""
    
    def setup_method(self):
        """Set up test fixtures"""
        from fastapi import FastAPI
        self.app = FastAPI()
        self.app.include_router(session_routes_router)
        self.client = TestClient(self.app)
    
    @pytest.mark.asyncio
    async def test_get_session_page_ui_success(self):
        """Test session page UI rendering success"""
        mock_request = Mock()
        mock_session = {
            "id": "test_session",
            "name": "Test Session",
            "status": "running",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T01:00:00Z"
        }
        
        with patch('src.api.session_routes.get_session', AsyncMock(return_value=mock_session)):
            with patch('src.api.session_routes.templates') as mock_templates:
                mock_templates.TemplateResponse.return_value = Mock()
                
                result = await get_session_page_ui(mock_request, "test_session")
                
                mock_templates.TemplateResponse.assert_called_once()
                call_args = mock_templates.TemplateResponse.call_args
                assert "session.html" in call_args[0]
                context = call_args[0][1]
                assert context["session"]["status_class"] == "success"
    
    @pytest.mark.asyncio
    async def test_get_session_page_ui_not_found(self):
        """Test session page UI when session not found"""
        mock_request = Mock()
        
        with patch('src.api.session_routes.get_session', AsyncMock(side_effect=HTTPException(404, "Not found"))):
            with pytest.raises(HTTPException) as exc_info:
                await get_session_page_ui(mock_request, "nonexistent")
            
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_home_page_redirect(self):
        """Test home page redirects to manage prompts"""
        mock_request = Mock()
        
        result = await get_home_page(mock_request)
        
        assert result.status_code == 307  # FastAPI uses 307 for RedirectResponse by default
        assert result.headers["location"] == "/manage/prompts"


class TestGenerateResponse:
    """Test response generation function"""
    
    def test_generate_response_hello(self):
        """Test response generation for greeting"""
        session = {"name": "Test Session"}
        
        result = generate_response("Hello", session)
        
        assert "Hello" in result
        assert "Architect AI" in result
        assert "Test Session" in result
    
    def test_generate_response_help(self):
        """Test response generation for help request"""
        session = {"name": "Test Session"}
        
        result = generate_response("I need help", session)
        
        assert "help" in result.lower()
        assert "coordinate" in result.lower()
    
    def test_generate_response_thanks(self):
        """Test response generation for thanks"""
        session = {"name": "Test Session"}
        
        result = generate_response("Thank you", session)
        
        assert "welcome" in result.lower()
    
    def test_generate_response_code_with_workers(self):
        """Test response generation for coding request with workers"""
        session = {
            "name": "Test Session",
            "config": {
                "workers": [
                    {"name": "CodeWorker", "capabilities": ["coding", "programming"]}
                ]
            }
        }
        
        result = generate_response("I need help with code", session)
        
        assert "CodeWorker" in result
        assert "coding" in result.lower()
    
    def test_generate_response_code_without_workers(self):
        """Test response generation for coding request without workers"""
        session = {
            "name": "Test Session",
            "config": {"workers": []}
        }
        
        result = generate_response("I need help with programming", session)
        
        assert "coding" in result.lower()
        assert "break it down" in result.lower()
    
    def test_generate_response_default(self):
        """Test default response generation"""
        session = {"name": "Test Session"}
        
        result = generate_response("Random message", session)
        
        assert "Random message" in result
        assert "step-by-step" in result.lower()
    
    def test_generate_response_empty_message(self):
        """Test response generation for empty message"""
        session = {"name": "Test Session"}
        
        result = generate_response("", session)
        
        assert "help" in result.lower()


class TestSessionViewsModels:
    """Test session views Pydantic models"""
    
    def test_session_config_model(self):
        """Test SessionConfig model validation"""
        config_data = {
            "name": "Test Session",
            "description": "A test session",
            "architect": {"type": "architect"},
            "workers": [{"name": "worker1"}]
        }
        
        config = SessionConfig(**config_data)
        
        assert config.name == "Test Session"
        assert config.description == "A test session"
        assert config.architect == {"type": "architect"}
        assert config.workers == [{"name": "worker1"}]
        assert config.intervention_enabled is True  # Default value
    
    def test_message_content_model(self):
        """Test MessageContent model validation"""
        content_data = {
            "text": "Hello world",
            "additional_data": {"key": "value"}
        }
        
        content = MessageContent(**content_data)
        
        assert content.text == "Hello world"
        assert content.additional_data == {"key": "value"}
    
    def test_create_message_request_model(self):
        """Test CreateMessageRequest model validation"""
        request_data = {
            "content": {"text": "Test message"}
        }
        
        request = CreateMessageRequest(**request_data)
        
        assert request.content.text == "Test message"


class TestSessionViewsHelpers:
    """Test session views helper functions"""
    
    def test_get_data_dir(self):
        """Test get_data_dir function"""
        with patch('os.path.dirname'), \
             patch('pathlib.Path') as mock_path:
            
            mock_data_dir = Mock()
            mock_data_dir.mkdir = Mock()
            mock_path.return_value.parent.parent = mock_data_dir
            
            result = get_data_dir()
            
            mock_data_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    
    def test_get_all_sessions_success(self):
        """Test get_all_sessions with successful file reading"""
        mock_session = {"id": "test_session", "name": "Test Session"}
        
        with patch('src.api.session_views.get_data_dir') as mock_get_dir:
            mock_data_dir = Mock()
            mock_file = Mock()
            mock_file.name = "test_session.json"
            mock_data_dir.glob.return_value = [mock_file]
            mock_get_dir.return_value = mock_data_dir
            
            with patch('builtins.open', mock_open(read_data=json.dumps(mock_session))):
                result = get_all_sessions()
            
            assert result == [mock_session]
    
    def test_get_all_sessions_file_error(self):
        """Test get_all_sessions with file reading error"""
        with patch('src.api.session_views.get_data_dir') as mock_get_dir:
            mock_data_dir = Mock()
            mock_file = Mock()
            mock_file.name = "test_session.json"
            mock_data_dir.glob.return_value = [mock_file]
            mock_get_dir.return_value = mock_data_dir
            
            with patch('builtins.open', side_effect=Exception("File error")):
                with patch('builtins.print') as mock_print:
                    result = get_all_sessions()
                
                assert result == []
                mock_print.assert_called()
    
    def test_get_session_view_success(self):
        """Test get_session_view with existing session"""
        mock_session = {"id": "test_session", "name": "Test Session"}
        
        with patch('src.api.session_views.get_data_dir') as mock_get_dir:
            mock_data_dir = Mock()
            mock_file = Mock()
            mock_file.exists.return_value = True
            mock_data_dir.__truediv__.return_value = mock_file
            mock_get_dir.return_value = mock_data_dir
            
            with patch('builtins.open', mock_open(read_data=json.dumps(mock_session))):
                result = get_session_view("test_session")
            
            assert result == mock_session
    
    def test_get_session_view_not_found(self):
        """Test get_session_view with non-existent session"""
        with patch('src.api.session_views.get_data_dir') as mock_get_dir:
            mock_data_dir = Mock()
            mock_file = Mock()
            mock_file.exists.return_value = False
            mock_data_dir.__truediv__.return_value = mock_file
            mock_get_dir.return_value = mock_data_dir
            
            result = get_session_view("nonexistent")
            
            assert result is None
    
    def test_get_session_view_file_error(self):
        """Test get_session_view with file reading error"""
        with patch('src.api.session_views.get_data_dir') as mock_get_dir:
            mock_data_dir = Mock()
            mock_file = Mock()
            mock_file.exists.return_value = True
            mock_data_dir.__truediv__.return_value = mock_file
            mock_get_dir.return_value = mock_data_dir
            
            with patch('builtins.open', side_effect=Exception("File error")):
                with patch('builtins.print') as mock_print:
                    result = get_session_view("test_session")
                
                assert result is None
                mock_print.assert_called()


class TestSessionViewsAPI:
    """Test session views API endpoints"""
    
    def setup_method(self):
        """Set up test fixtures"""
        from fastapi import FastAPI
        self.app = FastAPI()
        self.app.include_router(session_views_router)
        self.client = TestClient(self.app)
    
    def test_list_sessions_endpoint(self):
        """Test list sessions API endpoint"""
        mock_sessions = [{"id": "session1"}, {"id": "session2"}]
        
        with patch('src.api.session_views.get_all_sessions', return_value=mock_sessions):
            response = self.client.get("/api/sessions")
            
            assert response.status_code == 200
            assert response.json() == mock_sessions
    
    def test_get_active_sessions_endpoint(self):
        """Test get active sessions API endpoint"""
        mock_sessions = [
            {"id": "session1", "status": "running"},
            {"id": "session2", "status": "completed"},
            {"id": "session3", "status": "initialized"}
        ]
        
        with patch('src.api.session_views.get_all_sessions', return_value=mock_sessions):
            response = self.client.get("/api/sessions/active")
            
            assert response.status_code == 200
            active_sessions = response.json()
            assert len(active_sessions) == 2
            assert all(s["status"] in ["running", "initialized"] for s in active_sessions)
    
    def test_create_new_session_endpoint(self):
        """Test create new session API endpoint"""
        config_data = {
            "name": "Test Session",
            "description": "A test session",
            "architect": {"type": "architect"},
            "workers": [{"name": "worker1"}]
        }
        
        with patch('src.api.session_views.create_session_view') as mock_create:
            mock_create.return_value = {"id": "new_session", **config_data}
            
            response = self.client.post("/api/sessions", json=config_data)
            
            assert response.status_code == 200
            mock_create.assert_called_once()
    
    def test_get_session_by_id_success(self):
        """Test get session by ID success"""
        mock_session = {"id": "test_session", "name": "Test Session"}
        
        with patch('src.api.session_views.get_session_view', return_value=mock_session):
            response = self.client.get("/api/sessions/test_session")
            
            assert response.status_code == 200
            assert response.json() == mock_session
    
    def test_get_session_by_id_not_found(self):
        """Test get session by ID when not found"""
        with patch('src.api.session_views.get_session_view', return_value=None):
            response = self.client.get("/api/sessions/nonexistent")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
    
    def test_start_session_endpoint(self):
        """Test start session endpoint"""
        mock_session = {"id": "test_session", "status": "running"}
        
        with patch('src.api.session_views.update_session_status', return_value=mock_session):
            response = self.client.post("/api/sessions/test_session/start")
            
            assert response.status_code == 200
            assert response.json() == mock_session
    
    def test_stop_session_endpoint(self):
        """Test stop session endpoint"""
        mock_session = {"id": "test_session", "status": "stopped"}
        
        with patch('src.api.session_views.update_session_status', return_value=mock_session):
            response = self.client.post("/api/sessions/test_session/stop")
            
            assert response.status_code == 200
            assert response.json() == mock_session


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
