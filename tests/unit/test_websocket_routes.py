"""
Unit tests for WebSocket routes functionality
Tests all WebSocket routes and connection management
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

from src.api.websocket_routes import (
    ConnectionManager, 
    get_ws_prompt_service, 
    websocket_prompt_service_store,
    websocket_endpoint,
    manager
)
from src.models.unified_prompt import Prompt
from src.services.prompt_service import PromptService


class TestConnectionManager:
    """Test WebSocket connection management"""
    
    def test_connection_manager_init(self):
        """Test ConnectionManager initialization"""
        cm = ConnectionManager()
        assert cm.connections == {}
    
    @pytest.mark.asyncio
    async def test_connect_websocket(self):
        """Test connecting a WebSocket"""
        cm = ConnectionManager()
        websocket_mock = Mock(spec=WebSocket)
        websocket_mock.accept = AsyncMock()
        
        await cm.connect(websocket_mock, "test_prompt")
        
        websocket_mock.accept.assert_called_once()
        assert "test_prompt" in cm.connections
        assert websocket_mock in cm.connections["test_prompt"]
    
    @pytest.mark.asyncio 
    async def test_connect_multiple_websockets_same_prompt(self):
        """Test connecting multiple WebSockets to same prompt"""
        cm = ConnectionManager()
        websocket1 = Mock(spec=WebSocket)
        websocket1.accept = AsyncMock()
        websocket2 = Mock(spec=WebSocket)
        websocket2.accept = AsyncMock()
        
        await cm.connect(websocket1, "test_prompt")
        await cm.connect(websocket2, "test_prompt")
        
        assert len(cm.connections["test_prompt"]) == 2
        assert websocket1 in cm.connections["test_prompt"]
        assert websocket2 in cm.connections["test_prompt"]
    
    def test_disconnect_websocket(self):
        """Test disconnecting a WebSocket"""
        cm = ConnectionManager()
        websocket_mock = Mock(spec=WebSocket)
        
        # Set up initial connection
        cm.connections["test_prompt"] = [websocket_mock]
        
        cm.disconnect(websocket_mock, "test_prompt")
        
        assert "test_prompt" not in cm.connections
    
    def test_disconnect_websocket_multiple_clients(self):
        """Test disconnecting one WebSocket when multiple are connected"""
        cm = ConnectionManager()
        websocket1 = Mock(spec=WebSocket)
        websocket2 = Mock(spec=WebSocket)
        
        # Set up initial connections
        cm.connections["test_prompt"] = [websocket1, websocket2]
        
        cm.disconnect(websocket1, "test_prompt")
        
        assert "test_prompt" in cm.connections
        assert len(cm.connections["test_prompt"]) == 1
        assert websocket2 in cm.connections["test_prompt"]
        assert websocket1 not in cm.connections["test_prompt"]
    
    def test_disconnect_nonexistent_prompt(self):
        """Test disconnecting from non-existent prompt"""
        cm = ConnectionManager()
        websocket_mock = Mock(spec=WebSocket)
        
        # Should not raise error
        cm.disconnect(websocket_mock, "nonexistent_prompt")
        assert cm.connections == {}
    
    def test_disconnect_nonexistent_websocket(self):
        """Test disconnecting non-existent WebSocket"""
        cm = ConnectionManager()
        websocket1 = Mock(spec=WebSocket)
        websocket2 = Mock(spec=WebSocket)
        
        # Set up connection with only websocket1
        cm.connections["test_prompt"] = [websocket1]
        
        # Try to disconnect websocket2 (not connected)
        cm.disconnect(websocket2, "test_prompt")
        
        # websocket1 should still be connected
        assert websocket1 in cm.connections["test_prompt"]
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        """Test broadcasting message to connected clients"""
        cm = ConnectionManager()
        websocket1 = Mock(spec=WebSocket)
        websocket1.send_json = AsyncMock()
        websocket2 = Mock(spec=WebSocket)  
        websocket2.send_json = AsyncMock()
        
        # Set up connections
        cm.connections["test_prompt"] = [websocket1, websocket2]
        
        message = {"action": "test", "data": "test_data"}
        
        await cm.broadcast(message, "test_prompt")
        
        websocket1.send_json.assert_called_once_with(message)
        websocket2.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_broadcast_with_exclude(self):
        """Test broadcasting message excluding specific client"""
        cm = ConnectionManager()
        websocket1 = Mock(spec=WebSocket)
        websocket1.send_json = AsyncMock()
        websocket2 = Mock(spec=WebSocket)
        websocket2.send_json = AsyncMock()
        
        # Set up connections
        cm.connections["test_prompt"] = [websocket1, websocket2]
        
        message = {"action": "test", "data": "test_data"}
        
        await cm.broadcast(message, "test_prompt", exclude=websocket1)
        
        websocket1.send_json.assert_not_called()
        websocket2.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_broadcast_to_nonexistent_prompt(self):
        """Test broadcasting to non-existent prompt"""
        cm = ConnectionManager()
        message = {"action": "test", "data": "test_data"}
        
        # Should not raise error
        await cm.broadcast(message, "nonexistent_prompt")
    
    @pytest.mark.asyncio
    async def test_broadcast_error_handling(self):
        """Test broadcast error handling when send fails"""
        cm = ConnectionManager()
        websocket1 = Mock(spec=WebSocket)
        websocket1.send_json = AsyncMock(side_effect=Exception("Send failed"))
        websocket2 = Mock(spec=WebSocket)
        websocket2.send_json = AsyncMock()
        
        # Set up connections
        cm.connections["test_prompt"] = [websocket1, websocket2]
        
        message = {"action": "test", "data": "test_data"}
        
        # Should not raise error, just log it
        await cm.broadcast(message, "test_prompt")
        
        websocket1.send_json.assert_called_once_with(message)
        websocket2.send_json.assert_called_once_with(message)


class TestWebSocketPromptService:
    """Test WebSocket prompt service integration"""
    
    @pytest.mark.asyncio
    async def test_get_ws_prompt_service_success(self):
        """Test successful prompt service retrieval"""
        mock_service = Mock(spec=PromptService)
        
        with patch('src.api.websocket_routes.websocket_prompt_service_store', mock_service):
            service = await get_ws_prompt_service()
            assert service == mock_service
    
    @pytest.mark.asyncio
    async def test_get_ws_prompt_service_none(self):
        """Test prompt service retrieval when None"""
        with patch('src.api.websocket_routes.websocket_prompt_service_store', None):
            with pytest.raises(NotImplementedError) as exc_info:
                await get_ws_prompt_service()
            assert "PromptService instance not provided" in str(exc_info.value)


class TestWebSocketEndpoint:
    """Test WebSocket endpoint functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_websocket = Mock(spec=WebSocket)
        self.mock_websocket.accept = AsyncMock()
        self.mock_websocket.send_json = AsyncMock()
        self.mock_websocket.receive_json = AsyncMock()
        self.mock_websocket.close = AsyncMock()
        
        self.mock_prompt_service = Mock(spec=PromptService)
        self.mock_prompt = Mock(spec=Prompt)
        self.mock_prompt.id = "test_prompt"
        self.mock_prompt.unique_id = "test_dir/test_prompt"
        self.mock_prompt.name = "Test Prompt"
        self.mock_prompt.content = "Test content"
        self.mock_prompt.description = "Test description"
        self.mock_prompt.tags = ["test"]
        self.mock_prompt.is_composite = False
        self.mock_prompt.updated_at = datetime.now(timezone.utc)
        
        # Clear manager connections
        manager.connections.clear()
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_prompt_not_found(self):
        """Test WebSocket endpoint when prompt not found"""
        self.mock_prompt_service.get_prompt.return_value = None
        
        with patch('src.api.websocket_routes.get_ws_prompt_service', AsyncMock(return_value=self.mock_prompt_service)):
            await websocket_endpoint(self.mock_websocket, "nonexistent_prompt")
        
        self.mock_websocket.close.assert_called_once_with(code=4004, reason="Prompt 'nonexistent_prompt' not found")
        self.mock_websocket.accept.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_prompt_service_none(self):
        """Test WebSocket endpoint when prompt service is None"""
        with patch('src.api.websocket_routes.get_ws_prompt_service', AsyncMock(return_value=None)):
            await websocket_endpoint(self.mock_websocket, "test_prompt")
        
        self.mock_websocket.close.assert_called_once_with(code=1011, reason="Server configuration error: Prompt service unavailable")
        self.mock_websocket.accept.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_successful_connection(self):
        """Test successful WebSocket connection and initial data send"""
        self.mock_prompt_service.get_prompt.return_value = self.mock_prompt
        
        # Make receive_json raise WebSocketDisconnect after initial data is sent
        self.mock_websocket.receive_json.side_effect = WebSocketDisconnect(code=1000)
        
        with patch('src.api.websocket_routes.get_ws_prompt_service', AsyncMock(return_value=self.mock_prompt_service)):
            await websocket_endpoint(self.mock_websocket, "test_prompt")
        
        # Verify connection was accepted
        self.mock_websocket.accept.assert_called_once()
        
        # Verify initial data was sent
        expected_initial_data = {
            "action": "initial",
            "content": self.mock_prompt.content,
            "description": self.mock_prompt.description,
            "tags": self.mock_prompt.tags,
            "is_composite": self.mock_prompt.is_composite,
            "updated_at": self.mock_prompt.updated_at.isoformat()
        }
        self.mock_websocket.send_json.assert_called_with(expected_initial_data)
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_update_action(self):
        """Test WebSocket update action"""
        self.mock_prompt_service.get_prompt.return_value = self.mock_prompt
        self.mock_prompt_service.save_prompt.return_value = True
        
        # Set up message sequence: update action, then disconnect
        update_message = {"action": "update", "content": "Updated content"}
        self.mock_websocket.receive_json.side_effect = [update_message, WebSocketDisconnect(code=1000)]
        
        with patch('src.api.websocket_routes.get_ws_prompt_service', AsyncMock(return_value=self.mock_prompt_service)):
            await websocket_endpoint(self.mock_websocket, "test_prompt")
        
        # Verify prompt was updated
        assert self.mock_prompt.content == "Updated content"
        assert isinstance(self.mock_prompt.updated_at, datetime)
        
        # Verify save was called
        self.mock_prompt_service.save_prompt.assert_called_with(self.mock_prompt)
        
        # Verify update status was sent (call count should be 2: initial + update_status)
        assert self.mock_websocket.send_json.call_count == 2
        
        # Check the update status message
        status_call_args = self.mock_websocket.send_json.call_args_list[1][0][0]
        assert status_call_args["action"] == "update_status"
        assert status_call_args["success"] is True
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_update_metadata_action(self):
        """Test WebSocket update_metadata action"""
        self.mock_prompt_service.get_prompt.return_value = self.mock_prompt
        self.mock_prompt_service.save_prompt.return_value = True
        
        # Set up message sequence: update_metadata action, then disconnect
        update_message = {
            "action": "update_metadata", 
            "description": "Updated description",
            "tags": ["updated", "tags"]
        }
        self.mock_websocket.receive_json.side_effect = [update_message, WebSocketDisconnect(code=1000)]
        
        with patch('src.api.websocket_routes.get_ws_prompt_service', AsyncMock(return_value=self.mock_prompt_service)):
            await websocket_endpoint(self.mock_websocket, "test_prompt")
        
        # Verify prompt metadata was updated
        assert self.mock_prompt.description == "Updated description"
        assert self.mock_prompt.tags == ["updated", "tags"]
        assert isinstance(self.mock_prompt.updated_at, datetime)
        
        # Verify save was called
        self.mock_prompt_service.save_prompt.assert_called_with(self.mock_prompt)
        
        # Verify update status was sent
        assert self.mock_websocket.send_json.call_count == 2
        status_call_args = self.mock_websocket.send_json.call_args_list[1][0][0]
        assert status_call_args["action"] == "update_status"
        assert status_call_args["success"] is True
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_expand_action(self):
        """Test WebSocket expand action"""
        self.mock_prompt_service.get_prompt.return_value = self.mock_prompt
        self.mock_prompt_service.expand_inclusions.return_value = (
            "Expanded content", 
            {"dep1", "dep2"}, 
            ["warning1"]
        )
        
        # Set up message sequence: expand action, then disconnect
        expand_message = {"action": "expand", "content": "Content with [[inclusion]]"}
        self.mock_websocket.receive_json.side_effect = [expand_message, WebSocketDisconnect(code=1000)]
        
        with patch('src.api.websocket_routes.get_ws_prompt_service', AsyncMock(return_value=self.mock_prompt_service)):
            await websocket_endpoint(self.mock_websocket, "test_prompt")
        
        # Verify expand_inclusions was called
        self.mock_prompt_service.expand_inclusions.assert_called_with(
            "Content with [[inclusion]]", 
            parent_id=self.mock_prompt.id
        )
        
        # Verify expanded response was sent
        assert self.mock_websocket.send_json.call_count == 2
        expand_call_args = self.mock_websocket.send_json.call_args_list[1][0][0]
        assert expand_call_args["action"] == "expanded"
        assert expand_call_args["content"] == "Content with [[inclusion]]"
        assert expand_call_args["expanded"] == "Expanded content"
        assert expand_call_args["dependencies"] == ["dep1", "dep2"]
        assert expand_call_args["warnings"] == ["warning1"]
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_unknown_action(self):
        """Test WebSocket unknown action handling"""
        self.mock_prompt_service.get_prompt.return_value = self.mock_prompt
        
        # Set up message sequence: unknown action, then disconnect
        unknown_message = {"action": "unknown_action", "data": "test"}
        self.mock_websocket.receive_json.side_effect = [unknown_message, WebSocketDisconnect(code=1000)]
        
        with patch('src.api.websocket_routes.get_ws_prompt_service', AsyncMock(return_value=self.mock_prompt_service)):
            await websocket_endpoint(self.mock_websocket, "test_prompt")
        
        # Should only send initial data, no response to unknown action
        assert self.mock_websocket.send_json.call_count == 1
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_connection_error_during_accept(self):
        """Test WebSocket connection error during accept"""
        self.mock_prompt_service.get_prompt.return_value = self.mock_prompt
        
        # Mock manager.connect to raise an exception
        with patch('src.api.websocket_routes.manager.connect', AsyncMock(side_effect=Exception("Accept failed"))):
            with patch('src.api.websocket_routes.get_ws_prompt_service', AsyncMock(return_value=self.mock_prompt_service)):
                await websocket_endpoint(self.mock_websocket, "test_prompt")
        
        # Should try to close websocket with error code
        self.mock_websocket.close.assert_called_once_with(code=1011, reason="Server error during connection setup")
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_websocket_disconnect_during_accept(self):
        """Test WebSocket disconnect during accept"""
        self.mock_prompt_service.get_prompt.return_value = self.mock_prompt
        
        # Mock manager.connect to raise WebSocketDisconnect
        with patch('src.api.websocket_routes.manager.connect', AsyncMock(side_effect=WebSocketDisconnect(code=1001))):
            with patch('src.api.websocket_routes.get_ws_prompt_service', AsyncMock(return_value=self.mock_prompt_service)):
                await websocket_endpoint(self.mock_websocket, "test_prompt")
        
        # Should not try to close websocket, just return
        self.mock_websocket.close.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_error_during_initial_send(self):
        """Test error during initial data send"""
        self.mock_prompt_service.get_prompt.return_value = self.mock_prompt
        self.mock_websocket.send_json.side_effect = Exception("Send failed")
        
        with patch('src.api.websocket_routes.get_ws_prompt_service', AsyncMock(return_value=self.mock_prompt_service)):
            await websocket_endpoint(self.mock_websocket, "test_prompt")
        
        # Should accept connection but then handle send error gracefully
        self.mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_websocket_disconnect_during_initial_send(self):
        """Test WebSocket disconnect during initial data send"""
        self.mock_prompt_service.get_prompt.return_value = self.mock_prompt
        self.mock_websocket.send_json.side_effect = WebSocketDisconnect(code=1001)
        
        with patch('src.api.websocket_routes.get_ws_prompt_service', AsyncMock(return_value=self.mock_prompt_service)):
            await websocket_endpoint(self.mock_websocket, "test_prompt")
        
        # Should accept connection and handle disconnect gracefully
        self.mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_save_failure(self):
        """Test WebSocket update when save fails"""
        self.mock_prompt_service.get_prompt.return_value = self.mock_prompt
        self.mock_prompt_service.save_prompt.return_value = False
        
        # Set up message sequence: update action, then disconnect
        update_message = {"action": "update", "content": "Updated content"}
        self.mock_websocket.receive_json.side_effect = [update_message, WebSocketDisconnect(code=1000)]
        
        with patch('src.api.websocket_routes.get_ws_prompt_service', AsyncMock(return_value=self.mock_prompt_service)):
            await websocket_endpoint(self.mock_websocket, "test_prompt")
        
        # Verify update status shows failure
        assert self.mock_websocket.send_json.call_count == 2
        status_call_args = self.mock_websocket.send_json.call_args_list[1][0][0]
        assert status_call_args["action"] == "update_status"
        assert status_call_args["success"] is False
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_update_action_none_content(self):
        """Test WebSocket update action with None content"""
        self.mock_prompt_service.get_prompt.return_value = self.mock_prompt
        
        # Set up message sequence: update action with None content, then disconnect
        update_message = {"action": "update", "content": None}
        self.mock_websocket.receive_json.side_effect = [update_message, WebSocketDisconnect(code=1000)]
        
        with patch('src.api.websocket_routes.get_ws_prompt_service', AsyncMock(return_value=self.mock_prompt_service)):
            await websocket_endpoint(self.mock_websocket, "test_prompt")
        
        # Should not save or send update status for None content
        self.mock_prompt_service.save_prompt.assert_not_called()
        # Only initial data should be sent
        assert self.mock_websocket.send_json.call_count == 1
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_update_metadata_partial(self):
        """Test WebSocket update_metadata with partial data"""
        self.mock_prompt_service.get_prompt.return_value = self.mock_prompt
        self.mock_prompt_service.save_prompt.return_value = True
        original_description = self.mock_prompt.description
        original_tags = self.mock_prompt.tags
        
        # Set up message sequence: update only description, then disconnect
        update_message = {"action": "update_metadata", "description": "New description only"}
        self.mock_websocket.receive_json.side_effect = [update_message, WebSocketDisconnect(code=1000)]
        
        with patch('src.api.websocket_routes.get_ws_prompt_service', AsyncMock(return_value=self.mock_prompt_service)):
            await websocket_endpoint(self.mock_websocket, "test_prompt")
        
        # Verify only description was updated
        assert self.mock_prompt.description == "New description only"
        assert self.mock_prompt.tags == original_tags  # Should remain unchanged
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_expand_action_none_content(self):
        """Test WebSocket expand action with None content"""
        self.mock_prompt_service.get_prompt.return_value = self.mock_prompt
        
        # Set up message sequence: expand action with None content, then disconnect
        expand_message = {"action": "expand", "content": None}
        self.mock_websocket.receive_json.side_effect = [expand_message, WebSocketDisconnect(code=1000)]
        
        with patch('src.api.websocket_routes.get_ws_prompt_service', AsyncMock(return_value=self.mock_prompt_service)):
            await websocket_endpoint(self.mock_websocket, "test_prompt")
        
        # Should not call expand_inclusions for None content
        self.mock_prompt_service.expand_inclusions.assert_not_called()
        # Only initial data should be sent
        assert self.mock_websocket.send_json.call_count == 1
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_prompt_updated_at_none(self):
        """Test WebSocket endpoint when prompt.updated_at is None"""
        self.mock_prompt_service.get_prompt.return_value = self.mock_prompt
        self.mock_prompt.updated_at = None  # Set to None
        
        # Make receive_json raise WebSocketDisconnect after initial data is sent
        self.mock_websocket.receive_json.side_effect = WebSocketDisconnect(code=1000)
        
        with patch('src.api.websocket_routes.get_ws_prompt_service', AsyncMock(return_value=self.mock_prompt_service)):
            await websocket_endpoint(self.mock_websocket, "test_prompt")
        
        # Verify initial data was sent with updated_at as None
        expected_initial_data = {
            "action": "initial",
            "content": self.mock_prompt.content,
            "description": self.mock_prompt.description,
            "tags": self.mock_prompt.tags,
            "is_composite": self.mock_prompt.is_composite,
            "updated_at": None
        }
        self.mock_websocket.send_json.assert_called_with(expected_initial_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
