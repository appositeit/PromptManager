#!/usr/bin/env python
"""
Unit tests for WebSocket connection manager.

Tests the ConnectionManager class which handles WebSocket connections.
"""

import pytest
import unittest.mock as mock
from src.api.websocket_routes import ConnectionManager
from fastapi import WebSocket


class TestConnectionManager:
    """Tests for ConnectionManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConnectionManager()

    @pytest.mark.asyncio
    async def test_connect(self):
        """Test connecting a client."""
        # Create mock
        websocket = mock.AsyncMock(spec=WebSocket)
        fragment_id = "test_fragment"

        # Execute
        await self.manager.connect(websocket, fragment_id)

        # Verify
        websocket.accept.assert_called_once()
        assert fragment_id in self.manager.connections
        assert websocket in self.manager.connections[fragment_id]

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting a client."""
        # Create mock
        websocket = mock.AsyncMock(spec=WebSocket)
        fragment_id = "test_fragment"

        # Setup - connect first
        await self.manager.connect(websocket, fragment_id)
        assert fragment_id in self.manager.connections
        assert websocket in self.manager.connections[fragment_id]

        # Execute
        self.manager.disconnect(websocket, fragment_id)

        # Verify
        assert fragment_id not in self.manager.connections

    @pytest.mark.asyncio
    async def test_disconnect_multiple_clients(self):
        """Test disconnecting one client when multiple are connected."""
        # Create mocks
        websocket1 = mock.AsyncMock(spec=WebSocket)
        websocket2 = mock.AsyncMock(spec=WebSocket)
        fragment_id = "test_fragment"

        # Setup - connect both
        await self.manager.connect(websocket1, fragment_id)
        await self.manager.connect(websocket2, fragment_id)
        assert len(self.manager.connections[fragment_id]) == 2

        # Execute - disconnect one
        self.manager.disconnect(websocket1, fragment_id)

        # Verify
        assert fragment_id in self.manager.connections
        assert websocket1 not in self.manager.connections[fragment_id]
        assert websocket2 in self.manager.connections[fragment_id]

    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting a message to clients."""
        # Create mocks
        websocket1 = mock.AsyncMock(spec=WebSocket)
        websocket2 = mock.AsyncMock(spec=WebSocket)
        fragment_id = "test_fragment"
        message = {"action": "update", "content": "test"}

        # Setup - connect both
        await self.manager.connect(websocket1, fragment_id)
        await self.manager.connect(websocket2, fragment_id)

        # Execute - broadcast to all
        await self.manager.broadcast(message, fragment_id)

        # Verify
        websocket1.send_json.assert_called_once_with(message)
        websocket2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_with_exclude(self):
        """Test broadcasting a message excluding one client."""
        # Create mocks
        websocket1 = mock.AsyncMock(spec=WebSocket)
        websocket2 = mock.AsyncMock(spec=WebSocket)
        fragment_id = "test_fragment"
        message = {"action": "update", "content": "test"}

        # Setup - connect both
        await self.manager.connect(websocket1, fragment_id)
        await self.manager.connect(websocket2, fragment_id)

        # Execute - broadcast excluding websocket1
        await self.manager.broadcast(message, fragment_id, exclude=websocket1)

        # Verify
        websocket1.send_json.assert_not_called()
        websocket2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_error_handling(self):
        """Test error handling during broadcast."""
        # Create mocks
        websocket1 = mock.AsyncMock(spec=WebSocket)
        websocket2 = mock.AsyncMock(spec=WebSocket)
        websocket1.send_json.side_effect = Exception("Test error")
        fragment_id = "test_fragment"
        message = {"action": "update", "content": "test"}

        # Setup - connect both
        await self.manager.connect(websocket1, fragment_id)
        await self.manager.connect(websocket2, fragment_id)

        # Execute - broadcast to all
        await self.manager.broadcast(message, fragment_id)

        # Verify - the exception is caught and second client still gets message
        websocket1.send_json.assert_called_once_with(message)
        websocket2.send_json.assert_called_once_with(message)
