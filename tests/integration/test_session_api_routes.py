"""
Comprehensive integration tests for session API routes.
"""

import json
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

from src.api.session_views import router


@pytest.fixture
def client():
    """Create test client."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestSessionAPIRoutes:
    """Test session API endpoints."""

    @patch('src.api.session_views.get_all_sessions')
    def test_list_sessions_empty(self, mock_get_all_sessions, client):
        """Test listing sessions when none exist."""
        mock_get_all_sessions.return_value = []
        
        response = client.get("/api/sessions")
        
        assert response.status_code == 200
        assert response.json() == []

    @patch('src.api.session_views.get_all_sessions')
    def test_list_sessions_with_data(self, mock_get_all_sessions, client):
        """Test listing sessions with data."""
        sessions = [
            {"id": "session1", "name": "Test Session 1", "status": "running"},
            {"id": "session2", "name": "Test Session 2", "status": "stopped"}
        ]
        mock_get_all_sessions.return_value = sessions
        
        response = client.get("/api/sessions")
        
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["name"] == "Test Session 1"

    @patch('src.api.session_views.create_session')
    def test_create_session_success(self, mock_create_session, client):
        """Test successful session creation."""
        session_data = {
            "id": "new-session",
            "name": "New Session",
            "status": "initialized"
        }
        mock_create_session.return_value = session_data
        
        payload = {
            "name": "New Session",
            "architect": {"type": "basic"},
            "workers": [{"type": "worker1"}]
        }
        
        response = client.post("/api/sessions", json=payload)
        
        assert response.status_code == 200
        assert response.json()["name"] == "New Session"

    @patch('src.api.session_views.create_session')
    def test_create_session_validation_error(self, mock_create_session, client):
        """Test session creation with validation error."""
        # Missing required fields
        payload = {
            "name": "Invalid Session"
            # Missing architect and workers
        }
        
        response = client.post("/api/sessions", json=payload)
        
        assert response.status_code == 422  # Validation error

    @patch('src.api.session_views.get_session')
    def test_get_session_by_id_success(self, mock_get_session, client):
        """Test successful session retrieval by ID."""
        session_data = {
            "id": "test-session",
            "name": "Test Session",
            "status": "running"
        }
        mock_get_session.return_value = session_data
        
        response = client.get("/api/sessions/test-session")
        
        assert response.status_code == 200
        assert response.json()["id"] == "test-session"

    @patch('src.api.session_views.get_session')
    def test_get_session_by_id_not_found(self, mock_get_session, client):
        """Test session retrieval when session doesn't exist."""
        mock_get_session.return_value = None
        
        response = client.get("/api/sessions/non-existent")
        
        assert response.status_code == 404

    @patch('src.api.session_views.update_session_status')
    def test_start_session_success(self, mock_update_status, client):
        """Test starting a session."""
        session_data = {
            "id": "test-session",
            "status": "running"
        }
        mock_update_status.return_value = session_data
        
        response = client.post("/api/sessions/test-session/start")
        
        assert response.status_code == 200
        assert response.json()["status"] == "running"
        mock_update_status.assert_called_with("test-session", "running")

    @patch('src.api.session_views.update_session_status')
    def test_stop_session_success(self, mock_update_status, client):
        """Test stopping a session."""
        session_data = {
            "id": "test-session",
            "status": "stopped"
        }
        mock_update_status.return_value = session_data
        
        response = client.post("/api/sessions/test-session/stop")
        
        assert response.status_code == 200
        assert response.json()["status"] == "stopped"
        mock_update_status.assert_called_with("test-session", "stopped")

    @patch('src.api.session_views.update_session_status')
    def test_pause_session_success(self, mock_update_status, client):
        """Test pausing a session."""
        session_data = {
            "id": "test-session",
            "status": "paused"
        }
        mock_update_status.return_value = session_data
        
        response = client.post("/api/sessions/test-session/pause")
        
        assert response.status_code == 200
        assert response.json()["status"] == "paused"
        mock_update_status.assert_called_with("test-session", "paused")

    @patch('src.api.session_views.update_session_status')
    def test_resume_session_success(self, mock_update_status, client):
        """Test resuming a session."""
        session_data = {
            "id": "test-session",
            "status": "running"
        }
        mock_update_status.return_value = session_data
        
        response = client.post("/api/sessions/test-session/resume")
        
        assert response.status_code == 200
        assert response.json()["status"] == "running"
        mock_update_status.assert_called_with("test-session", "running")

    @patch('src.api.session_views.update_session_status')
    def test_session_status_update_not_found(self, mock_update_status, client):
        """Test session status update when session doesn't exist."""
        mock_update_status.side_effect = HTTPException(status_code=404, detail="Session not found")
        
        response = client.post("/api/sessions/non-existent/start")
        
        assert response.status_code == 404

    @patch('src.api.session_views.get_session_messages')
    def test_get_messages_success(self, mock_get_messages, client):
        """Test getting session messages."""
        messages = [
            {"id": "msg1", "content": {"text": "Hello"}},
            {"id": "msg2", "content": {"text": "World"}}
        ]
        mock_get_messages.return_value = messages
        
        response = client.get("/api/sessions/test-session/messages")
        
        assert response.status_code == 200
        assert len(response.json()) == 2

    @patch('src.api.session_views.get_session_messages')
    def test_get_messages_session_not_found(self, mock_get_messages, client):
        """Test getting messages from non-existent session."""
        mock_get_messages.side_effect = HTTPException(status_code=404, detail="Session not found")
        
        response = client.get("/api/sessions/non-existent/messages")
        
        assert response.status_code == 404

    @patch('src.api.session_views.add_message')
    def test_create_message_success(self, mock_add_message, client):
        """Test creating a message."""
        message_data = {
            "id": "new-msg",
            "session_id": "test-session",
            "from_agent": "user",
            "to_agent": "architect"
        }
        mock_add_message.return_value = message_data
        
        payload = {
            "content": {
                "text": "Hello world"
            }
        }
        
        response = client.post("/api/sessions/test-session/messages", json=payload)
        
        assert response.status_code == 200
        assert response.json()["from_agent"] == "user"
        assert response.json()["to_agent"] == "architect"

    @patch('src.api.session_views.add_message')
    def test_create_worker_message_success(self, mock_add_message, client):
        """Test creating a message to a worker."""
        message_data = {
            "id": "worker-msg",
            "session_id": "test-session",
            "from_agent": "user",
            "to_agent": "worker1"
        }
        mock_add_message.return_value = message_data
        
        payload = {
            "content": {
                "text": "Do some work"
            }
        }
        
        response = client.post("/api/sessions/test-session/messages/worker/1", json=payload)
        
        assert response.status_code == 200
        assert response.json()["to_agent"] == "worker1"

    @patch('src.api.session_views.add_message')
    def test_create_message_session_not_found(self, mock_add_message, client):
        """Test creating message in non-existent session."""
        mock_add_message.side_effect = HTTPException(status_code=404, detail="Session not found")
        
        payload = {
            "content": {
                "text": "Hello"
            }
        }
        
        response = client.post("/api/sessions/non-existent/messages", json=payload)
        
        assert response.status_code == 404

    @patch('src.api.session_views.get_worker_data')
    def test_get_worker_success(self, mock_get_worker_data, client):
        """Test getting worker data."""
        worker_data = {
            "id": 0,
            "type": "coder",
            "name": "Alice",
            "messages": []
        }
        mock_get_worker_data.return_value = worker_data
        
        response = client.get("/api/sessions/test-session/workers/0")
        
        assert response.status_code == 200
        assert response.json()["type"] == "coder"
        assert response.json()["name"] == "Alice"

    @patch('src.api.session_views.get_worker_data')
    def test_get_worker_not_found(self, mock_get_worker_data, client):
        """Test getting non-existent worker."""
        mock_get_worker_data.side_effect = HTTPException(status_code=404, detail="Worker not found")
        
        response = client.get("/api/sessions/test-session/workers/999")
        
        assert response.status_code == 404

    @patch('src.api.session_views.get_all_sessions')
    def test_get_active_sessions_empty(self, mock_get_all_sessions, client):
        """Test getting active sessions when none are active."""
        mock_get_all_sessions.return_value = [
            {"id": "session1", "status": "stopped"},
            {"id": "session2", "status": "completed"}
        ]
        
        response = client.get("/api/sessions/active")
        
        assert response.status_code == 200
        assert response.json() == []

    @patch('src.api.session_views.get_all_sessions')
    def test_get_active_sessions_with_data(self, mock_get_all_sessions, client):
        """Test getting active sessions with some active."""
        mock_get_all_sessions.return_value = [
            {"id": "session1", "status": "running"},
            {"id": "session2", "status": "stopped"},
            {"id": "session3", "status": "initialized"},
            {"id": "session4", "status": "completed"}
        ]
        
        response = client.get("/api/sessions/active")
        
        assert response.status_code == 200
        active_sessions = response.json()
        assert len(active_sessions) == 2
        assert active_sessions[0]["status"] == "running"
        assert active_sessions[1]["status"] == "initialized"


class TestSessionAPIValidation:
    """Test API validation and error handling."""

    def test_create_session_invalid_json(self, client):
        """Test session creation with invalid JSON."""
        response = client.post(
            "/api/sessions", 
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422

    def test_create_message_invalid_content(self, client):
        """Test message creation with invalid content."""
        payload = {
            "content": "string instead of object"
        }
        
        response = client.post("/api/sessions/test-session/messages", json=payload)
        
        assert response.status_code == 422

    def test_worker_id_validation(self, client):
        """Test worker ID validation."""
        payload = {
            "content": {
                "text": "Hello"
            }
        }
        
        # Test with string worker ID (should work as FastAPI converts)
        response = client.post("/api/sessions/test-session/messages/worker/abc", json=payload)
        
        assert response.status_code == 422  # Should fail validation

    @patch('src.api.session_views.add_message')
    def test_complex_message_content(self, mock_add_message, client):
        """Test creating message with complex content."""
        message_data = {
            "id": "complex-msg",
            "session_id": "test-session",
            "content": {
                "text": "Complex message",
                "additional_data": {
                    "priority": "high",
                    "attachments": ["file1.txt", "file2.pdf"]
                }
            }
        }
        mock_add_message.return_value = message_data
        
        payload = {
            "content": {
                "text": "Complex message",
                "additional_data": {
                    "priority": "high",
                    "attachments": ["file1.txt", "file2.pdf"]
                }
            }
        }
        
        response = client.post("/api/sessions/test-session/messages", json=payload)
        
        assert response.status_code == 200


class TestSessionAPIIntegration:
    """Test integration scenarios."""

    @patch('src.api.session_views.create_session')
    def test_create_session_with_full_config(self, mock_create_session, client):
        """Test creating a session with full configuration."""
        session_data = {
            "id": "full-session",
            "name": "Full Configuration Session",
            "status": "initialized",
            "config": {
                "architect": {"type": "advanced", "model": "gpt-4"},
                "workers": [
                    {"type": "senior_developer", "specialization": "backend"},
                    {"type": "qa_engineer", "specialization": "automation"}
                ],
                "mcp_servers": ["server1", "server2"],
                "intervention_enabled": False
            }
        }
        mock_create_session.return_value = session_data
        
        payload = {
            "name": "Full Configuration Session",
            "description": "A comprehensive test session",
            "directory": "full-config-dir", 
            "architect": {
                "type": "advanced",
                "model": "gpt-4"
            },
            "workers": [
                {
                    "type": "senior_developer",
                    "specialization": "backend"
                },
                {
                    "type": "qa_engineer",
                    "specialization": "automation"
                }
            ],
            "mcp_servers": ["server1", "server2"],
            "intervention_enabled": False
        }
        
        response = client.post("/api/sessions", json=payload)
        
        assert response.status_code == 200
        assert response.json()["name"] == "Full Configuration Session"

    @patch('src.api.session_views.get_all_sessions')
    def test_session_status_filtering(self, mock_get_all_sessions, client):
        """Test that active sessions are properly filtered."""
        all_sessions = [
            {"id": "s1", "status": "initialized"},
            {"id": "s2", "status": "running"},
            {"id": "s3", "status": "paused"},
            {"id": "s4", "status": "stopped"},
            {"id": "s5", "status": "completed"},
            {"id": "s6", "status": "error"},
            {"id": "s7", "status": "running"}
        ]
        mock_get_all_sessions.return_value = all_sessions
        
        # Test all sessions
        response = client.get("/api/sessions")
        assert len(response.json()) == 7
        
        # Test active sessions only
        response = client.get("/api/sessions/active")
        active_sessions = response.json()
        assert len(active_sessions) == 3  # initialized, running, running
        
        active_statuses = [s["status"] for s in active_sessions]
        assert "initialized" in active_statuses
        assert "running" in active_statuses
        assert "stopped" not in active_statuses
        assert "completed" not in active_statuses

    @patch('src.api.session_views.update_session_status')
    def test_session_lifecycle_operations(self, mock_update_status, client):
        """Test complete session lifecycle through API."""
        # Mock different status updates
        def mock_status_update(session_id, status):
            return {"id": session_id, "status": status, "updated_at": "2025-01-01T00:00:00"}
        
        mock_update_status.side_effect = mock_status_update
        
        session_id = "lifecycle-session"
        
        # Start session
        response = client.post(f"/api/sessions/{session_id}/start")
        assert response.status_code == 200
        assert response.json()["status"] == "running"
        
        # Pause session
        response = client.post(f"/api/sessions/{session_id}/pause")
        assert response.status_code == 200
        assert response.json()["status"] == "paused"
        
        # Resume session
        response = client.post(f"/api/sessions/{session_id}/resume")
        assert response.status_code == 200
        assert response.json()["status"] == "running"
        
        # Stop session
        response = client.post(f"/api/sessions/{session_id}/stop")
        assert response.status_code == 200
        assert response.json()["status"] == "stopped"
