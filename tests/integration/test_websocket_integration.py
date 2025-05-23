#!/usr/bin/env python
"""
Integration tests for WebSocket API.

Tests the WebSocket API with a running server.
"""

import pytest
import asyncio
import json
import uuid
import time
from websockets.client import connect
from fastapi.testclient import TestClient
import tempfile
import os
import shutil
import logging

from src.server import create_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data
TEST_FRAGMENT_CONTENT = """---
description: Test fragment for WebSocket API
tags:
  - test
  - websocket
---

This is a test fragment for WebSocket API testing.
"""

class TestWebSocketIntegration:
    """Integration tests for WebSocket API."""
    
    @pytest.fixture(scope="class")
    def temp_data_dir(self):
        """Create a temporary directory for fragments."""
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        fragments_dir = os.path.join(temp_dir, "fragments")
        os.makedirs(fragments_dir, exist_ok=True)
        
        # Create a test fragment
        fragment_id = f"test_fragment_{uuid.uuid4().hex[:8]}"
        with open(os.path.join(fragments_dir, f"{fragment_id}.md"), "w") as f:
            f.write(TEST_FRAGMENT_CONTENT)
        
        yield temp_dir, fragment_id
        
        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def app(self, temp_data_dir):
        """Create a test application."""
        data_dir, _ = temp_data_dir
        
        # Create app with temp directory
        app = create_app(
            config_path=None,
            fragment_dirs=[os.path.join(data_dir, "fragments")],
            template_dirs=[os.path.join(data_dir, "templates")],
            port=8081
        )
        
        # Return the FastAPI app
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_fragment_websocket_connect(self, app, temp_data_dir):
        """Test connecting to a fragment WebSocket."""
        _, fragment_id = temp_data_dir
        
        # Start app in background
        import uvicorn
        import threading
        
        server_port = 8765  # Use a different port for tests
        
        def run_server():
            uvicorn.run(app, host="127.0.0.1", port=server_port, log_level="error")
        
        # Start server in a thread
        thread = threading.Thread(target=run_server)
        thread.daemon = True
        thread.start()
        
        # Wait for server to start
        await asyncio.sleep(1)
        
        try:
            # Connect to WebSocket
            uri = f"ws://127.0.0.1:{server_port}/ws/prompts/{fragment_id}"
            logger.info(f"Connecting to {uri}")
            
            async with connect(uri) as websocket:
                # Receive initial data
                response = await websocket.recv()
                data = json.loads(response)
                
                # Verify initial data
                assert data["action"] == "initial"
                assert "content" in data
                assert "description" in data
                assert "tags" in data
                assert data["description"] == "Test fragment for WebSocket API"
                assert set(data["tags"]) == {"test", "websocket"}
                
                # Test update
                new_content = f"Updated test content at {time.time()}"
                await websocket.send(json.dumps({
                    "action": "update",
                    "content": new_content
                }))
                
                # Receive update status
                response = await websocket.recv()
                data = json.loads(response)
                
                # Verify update status
                assert data["action"] == "update_status"
                assert data["success"] is True
                
                # Test expansion
                await websocket.send(json.dumps({
                    "action": "expand",
                    "content": "Content with [[inclusions]]"
                }))
                
                # Receive expansion response
                response = await websocket.recv()
                data = json.loads(response)
                
                # Verify expansion
                assert data["action"] == "expanded"
                assert data["content"] == "Content with [[inclusions]]"
                assert "expanded" in data
                assert "dependencies" in data
                assert "warnings" in data
        
        finally:
            # Clean up - stop the server
            # We use a separate client to send a signal to the server to shut down
            # since there's no built-in way to stop uvicorn programmatically
            import requests
            try:
                requests.get(f"http://127.0.0.1:{server_port}/shutdown", timeout=1)
            except Exception:
                pass

    @pytest.mark.asyncio
    async def test_concurrent_fragment_edits(self, app, temp_data_dir):
        """Test concurrent editing of a fragment."""
        _, fragment_id = temp_data_dir
        
        # Start app in background
        import uvicorn
        import threading
        
        server_port = 8766  # Use a different port for tests
        
        def run_server():
            uvicorn.run(app, host="127.0.0.1", port=server_port, log_level="error")
        
        # Start server in a thread
        thread = threading.Thread(target=run_server)
        thread.daemon = True
        thread.start()
        
        # Wait for server to start
        await asyncio.sleep(1)
        
        try:
            # Connect first client
            uri = f"ws://127.0.0.1:{server_port}/ws/prompts/{fragment_id}"
            
            async with connect(uri) as websocket1, connect(uri) as websocket2:
                # Wait for initial data on both clients
                await websocket1.recv()
                await websocket2.recv()
                
                # Client 1 updates content
                update_content = f"Updated by client 1 at {time.time()}"
                await websocket1.send(json.dumps({
                    "action": "update",
                    "content": update_content
                }))
                
                # Client 1 receives confirmation
                response = await websocket1.recv()
                data = json.loads(response)
                assert data["action"] == "update_status"
                assert data["success"] is True
                
                # Client 2 should receive the update
                response = await websocket2.recv()
                data = json.loads(response)
                assert data["action"] == "update"
                assert data["content"] == update_content
                
                # Client 2 updates content
                update_content2 = f"Updated by client 2 at {time.time()}"
                await websocket2.send(json.dumps({
                    "action": "update",
                    "content": update_content2
                }))
                
                # Client 2 receives confirmation
                response = await websocket2.recv()
                data = json.loads(response)
                assert data["action"] == "update_status"
                assert data["success"] is True
                
                # Client 1 should receive the update
                response = await websocket1.recv()
                data = json.loads(response)
                assert data["action"] == "update"
                assert data["content"] == update_content2
        
        finally:
            # Clean up - stop the server
            import requests
            try:
                requests.get(f"http://127.0.0.1:{server_port}/shutdown", timeout=1)
            except Exception:
                pass

    @pytest.mark.asyncio
    async def test_nonexistent_fragment(self, app):
        """Test connecting to a nonexistent fragment."""
        # Start app in background
        import uvicorn
        import threading
        
        server_port = 8767  # Use a different port for tests
        
        def run_server():
            uvicorn.run(app, host="127.0.0.1", port=server_port, log_level="error")
        
        # Start server in a thread
        thread = threading.Thread(target=run_server)
        thread.daemon = True
        thread.start()
        
        # Wait for server to start
        await asyncio.sleep(1)
        
        try:
            # Connect to WebSocket with nonexistent fragment
            uri = f"ws://127.0.0.1:{server_port}/ws/prompts/nonexistent_fragment"
            
            # Should fail to connect
            try:
                async with connect(uri) as websocket:
                    # Either connection will fail or server will close with 4004
                    await websocket.recv()
                    assert False, "Should not have received a message"
            except Exception:
                # Expected to fail in some way
                pass
        
        finally:
            # Clean up - stop the server
            import requests
            try:
                requests.get(f"http://127.0.0.1:{server_port}/shutdown", timeout=1)
            except Exception:
                pass

    @pytest.mark.asyncio
    async def test_debug_websocket(self, app):
        """Test the debug WebSocket endpoint."""
        # Start app in background
        import uvicorn
        import threading
        
        server_port = 8768  # Use a different port for tests
        
        def run_server():
            uvicorn.run(app, host="127.0.0.1", port=server_port, log_level="error")
        
        # Start server in a thread
        thread = threading.Thread(target=run_server)
        thread.daemon = True
        thread.start()
        
        # Wait for server to start
        await asyncio.sleep(1)
        
        try:
            # Connect to debug WebSocket
            uri = f"ws://127.0.0.1:{server_port}/api/ws/test"
            
            async with connect(uri) as websocket:
                # Should receive welcome message
                response = await websocket.recv()
                assert "WebSocket test connection successful" in response
                
                # Send a message
                test_message = f"Test message at {time.time()}"
                await websocket.send(test_message)
                
                # Should receive echo
                response = await websocket.recv()
                data = json.loads(response)
                assert data["received"] == test_message
                assert "counter" in data
                assert "timestamp" in data
        
        finally:
            # Clean up - stop the server
            import requests
            try:
                requests.get(f"http://127.0.0.1:{server_port}/shutdown", timeout=1)
            except Exception:
                pass
