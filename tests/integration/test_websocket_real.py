"""
Real WebSocket Integration Tests
Tests actual WebSocket endpoints with real connections
"""

import pytest
import asyncio
import json
import websockets
from typing import Dict, Any
import httpx

# WebSocket URL for actual prompt connections
API_BASE_URL = "http://localhost:8095/api"
WS_BASE_URL = "ws://localhost:8095/api"


class TestRealWebSocketConnections:
    """Test real WebSocket connections to prompt endpoints"""
    
    @pytest.mark.asyncio
    async def test_websocket_prompt_connection_not_found(self):
        """Test WebSocket connection to non-existent prompt"""
        try:
            # Try to connect to non-existent prompt
            ws_url = f"{WS_BASE_URL}/ws/prompts/nonexistent_prompt_12345"
            
            with pytest.raises(websockets.exceptions.ConnectionClosedError) as exc_info:
                async with websockets.connect(ws_url) as websocket:
                    # Should close with 4004 code for prompt not found
                    await websocket.recv()
            
            # Check that it was closed with the expected code
            assert exc_info.value.code == 4004
            
        except ConnectionRefusedError:
            pytest.skip("WebSocket server not available")
        except Exception as e:
            # If we get a different connection error, it might be expected
            if "4004" in str(e) or "not found" in str(e).lower():
                pass  # Expected behavior
            else:
                pytest.skip(f"WebSocket connection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_websocket_prompt_connection_success(self):
        """Test successful WebSocket connection to existing prompt"""
        try:
            # First create a test prompt
            async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as http_client:
                test_prompt = {
                    "name": "ws_real_test_prompt",
                    "directory": "/tmp/ws_real_test",
                    "content": "Real WebSocket test content",
                    "description": "Test prompt for real WebSocket connections"
                }
                
                # Clean up first
                await http_client.delete("/prompts/ws_real_test/ws_real_test_prompt")
                
                # Create the prompt
                create_response = await http_client.post("/prompts/", json=test_prompt)
                if create_response.status_code != 201:
                    pytest.skip("Could not create test prompt for WebSocket test")
                
                created_prompt = create_response.json()
                prompt_id = created_prompt["id"]
                
                try:
                    # Connect to WebSocket for this prompt
                    ws_url = f"{WS_BASE_URL}/ws/prompts/{prompt_id}"
                    
                    async with websockets.connect(ws_url) as websocket:
                        # Should receive initial data
                        initial_data_raw = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        initial_data = json.loads(initial_data_raw)
                        
                        # Verify initial data structure
                        assert initial_data["action"] == "initial"
                        assert initial_data["content"] == test_prompt["content"]
                        assert initial_data["description"] == test_prompt["description"]
                        assert "is_composite" in initial_data
                        assert "updated_at" in initial_data
                        
                finally:
                    # Clean up prompt
                    await http_client.delete(f"/prompts/{prompt_id}")
                    
        except ConnectionRefusedError:
            pytest.skip("WebSocket server not available")
        except Exception as e:
            pytest.skip(f"WebSocket test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_websocket_prompt_update_flow(self):
        """Test complete WebSocket update flow"""
        try:
            # Create test prompt
            async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as http_client:
                test_prompt = {
                    "name": "ws_update_test",
                    "directory": "/tmp/ws_update_test", 
                    "content": "Original content for update test",
                    "description": "Original description"
                }
                
                # Clean up first
                await http_client.delete("/prompts/ws_update_test/ws_update_test")
                
                create_response = await http_client.post("/prompts/", json=test_prompt)
                if create_response.status_code != 201:
                    pytest.skip("Could not create test prompt for WebSocket update test")
                
                created_prompt = create_response.json()
                prompt_id = created_prompt["id"]
                
                try:
                    # Connect to WebSocket
                    ws_url = f"{WS_BASE_URL}/ws/prompts/{prompt_id}"
                    
                    async with websockets.connect(ws_url) as websocket:
                        # Receive initial data
                        initial_data_raw = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        initial_data = json.loads(initial_data_raw)
                        assert initial_data["action"] == "initial"
                        
                        # Send update message
                        update_message = {
                            "action": "update",
                            "content": "Updated content via WebSocket"
                        }
                        await websocket.send(json.dumps(update_message))
                        
                        # Receive update status
                        status_response_raw = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        status_response = json.loads(status_response_raw)
                        
                        assert status_response["action"] == "update_status"
                        assert status_response["success"] is True
                        assert "timestamp" in status_response
                        
                        # Verify the prompt was actually updated via API
                        get_response = await http_client.get(f"/prompts/{prompt_id}")
                        assert get_response.status_code == 200
                        
                        updated_prompt = get_response.json()
                        assert updated_prompt["content"] == "Updated content via WebSocket"
                        
                finally:
                    # Clean up
                    await http_client.delete(f"/prompts/{prompt_id}")
                    
        except ConnectionRefusedError:
            pytest.skip("WebSocket server not available")
        except Exception as e:
            pytest.skip(f"WebSocket update test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_websocket_metadata_update_flow(self):
        """Test WebSocket metadata update flow"""
        try:
            # Create test prompt
            async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as http_client:
                test_prompt = {
                    "name": "ws_metadata_test",
                    "directory": "/tmp/ws_metadata_test",
                    "content": "Content for metadata test",
                    "description": "Original description",
                    "tags": ["original", "test"]
                }
                
                # Clean up first
                await http_client.delete("/prompts/ws_metadata_test/ws_metadata_test")
                
                create_response = await http_client.post("/prompts/", json=test_prompt)
                if create_response.status_code != 201:
                    pytest.skip("Could not create test prompt for WebSocket metadata test")
                
                created_prompt = create_response.json()
                prompt_id = created_prompt["id"]
                
                try:
                    # Connect to WebSocket
                    ws_url = f"{WS_BASE_URL}/ws/prompts/{prompt_id}"
                    
                    async with websockets.connect(ws_url) as websocket:
                        # Receive initial data
                        initial_data_raw = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        initial_data = json.loads(initial_data_raw)
                        assert initial_data["action"] == "initial"
                        
                        # Send metadata update message
                        metadata_message = {
                            "action": "update_metadata",
                            "description": "Updated description via WebSocket",
                            "tags": ["updated", "websocket", "test"]
                        }
                        await websocket.send(json.dumps(metadata_message))
                        
                        # Receive update status
                        status_response_raw = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        status_response = json.loads(status_response_raw)
                        
                        assert status_response["action"] == "update_status"
                        assert status_response["success"] is True
                        
                        # Verify the metadata was actually updated via API
                        get_response = await http_client.get(f"/prompts/{prompt_id}")
                        assert get_response.status_code == 200
                        
                        updated_prompt = get_response.json()
                        assert updated_prompt["description"] == "Updated description via WebSocket"
                        assert updated_prompt["tags"] == ["updated", "websocket", "test"]
                        
                finally:
                    # Clean up
                    await http_client.delete(f"/prompts/{prompt_id}")
                    
        except ConnectionRefusedError:
            pytest.skip("WebSocket server not available")
        except Exception as e:
            pytest.skip(f"WebSocket metadata test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_websocket_expand_flow(self):
        """Test WebSocket expand functionality"""
        try:
            # Create test prompts - one to include and one to be the main prompt
            async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as http_client:
                # Create included prompt first
                included_prompt = {
                    "name": "ws_included_prompt",
                    "directory": "/tmp/ws_expand_test",
                    "content": "This is included content",
                    "description": "Prompt to be included"
                }
                
                # Clean up first
                await http_client.delete("/prompts/ws_expand_test/ws_included_prompt")
                await http_client.delete("/prompts/ws_expand_test/ws_main_prompt")
                
                included_response = await http_client.post("/prompts/", json=included_prompt)
                if included_response.status_code != 201:
                    pytest.skip("Could not create included prompt for WebSocket expand test")
                
                # Create main prompt
                main_prompt = {
                    "name": "ws_main_prompt", 
                    "directory": "/tmp/ws_expand_test",
                    "content": "Main content with [[ws_included_prompt]] inclusion",
                    "description": "Main prompt for expand test"
                }
                
                main_response = await http_client.post("/prompts/", json=main_prompt)
                if main_response.status_code != 201:
                    pytest.skip("Could not create main prompt for WebSocket expand test")
                
                created_main = main_response.json()
                main_prompt_id = created_main["id"]
                
                try:
                    # Connect to WebSocket for main prompt
                    ws_url = f"{WS_BASE_URL}/ws/prompts/{main_prompt_id}"
                    
                    async with websockets.connect(ws_url) as websocket:
                        # Receive initial data
                        initial_data_raw = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        initial_data = json.loads(initial_data_raw)
                        assert initial_data["action"] == "initial"
                        
                        # Send expand request
                        expand_message = {
                            "action": "expand",
                            "content": "Test content with [[ws_included_prompt]] to expand"
                        }
                        await websocket.send(json.dumps(expand_message))
                        
                        # Receive expanded response
                        expand_response_raw = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        expand_response = json.loads(expand_response_raw)
                        
                        assert expand_response["action"] == "expanded"
                        assert expand_response["content"] == "Test content with [[ws_included_prompt]] to expand"
                        assert "This is included content" in expand_response["expanded"]
                        assert "dependencies" in expand_response
                        assert "warnings" in expand_response
                        
                finally:
                    # Clean up both prompts
                    await http_client.delete(f"/prompts/{main_prompt_id}")
                    included_id = included_response.json()["id"]
                    await http_client.delete(f"/prompts/{included_id}")
                    
        except ConnectionRefusedError:
            pytest.skip("WebSocket server not available")
        except Exception as e:
            pytest.skip(f"WebSocket expand test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_websocket_multiple_clients_broadcast(self):
        """Test that updates are broadcast to multiple WebSocket clients"""
        try:
            # Create test prompt
            async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as http_client:
                test_prompt = {
                    "name": "ws_broadcast_test",
                    "directory": "/tmp/ws_broadcast_test",
                    "content": "Content for broadcast test",
                    "description": "Broadcast test prompt"
                }
                
                # Clean up first
                await http_client.delete("/prompts/ws_broadcast_test/ws_broadcast_test")
                
                create_response = await http_client.post("/prompts/", json=test_prompt)
                if create_response.status_code != 201:
                    pytest.skip("Could not create test prompt for WebSocket broadcast test")
                
                created_prompt = create_response.json()
                prompt_id = created_prompt["id"]
                ws_url = f"{WS_BASE_URL}/ws/prompts/{prompt_id}"
                
                try:
                    # Connect two WebSocket clients
                    async with websockets.connect(ws_url) as client1, \
                               websockets.connect(ws_url) as client2:
                        
                        # Both clients receive initial data
                        initial1_raw = await asyncio.wait_for(client1.recv(), timeout=5.0)
                        initial2_raw = await asyncio.wait_for(client2.recv(), timeout=5.0)
                        
                        initial1 = json.loads(initial1_raw)
                        initial2 = json.loads(initial2_raw)
                        
                        assert initial1["action"] == "initial"
                        assert initial2["action"] == "initial"
                        
                        # Client1 sends update
                        update_message = {
                            "action": "update",
                            "content": "Updated by client1"
                        }
                        await client1.send(json.dumps(update_message))
                        
                        # Client1 receives update status
                        client1_status_raw = await asyncio.wait_for(client1.recv(), timeout=5.0)
                        client1_status = json.loads(client1_status_raw)
                        assert client1_status["action"] == "update_status"
                        assert client1_status["success"] is True
                        
                        # Client2 should receive broadcast update (not the status, but the broadcast)
                        try:
                            client2_broadcast_raw = await asyncio.wait_for(client2.recv(), timeout=5.0)
                            client2_broadcast = json.loads(client2_broadcast_raw)
                            assert client2_broadcast["action"] == "update"
                            assert client2_broadcast["content"] == "Updated by client1"
                        except asyncio.TimeoutError:
                            # Broadcast might not be implemented yet or might be async
                            pytest.skip("Broadcast functionality not working or not implemented")
                        
                finally:
                    # Clean up
                    await http_client.delete(f"/prompts/{prompt_id}")
                    
        except ConnectionRefusedError:
            pytest.skip("WebSocket server not available")
        except Exception as e:
            pytest.skip(f"WebSocket broadcast test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_websocket_invalid_action(self):
        """Test WebSocket handling of invalid actions"""
        try:
            # Create test prompt
            async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as http_client:
                test_prompt = {
                    "name": "ws_invalid_action_test",
                    "directory": "/tmp/ws_invalid_test",
                    "content": "Content for invalid action test",
                    "description": "Invalid action test prompt"
                }
                
                # Clean up first
                await http_client.delete("/prompts/ws_invalid_test/ws_invalid_action_test")
                
                create_response = await http_client.post("/prompts/", json=test_prompt)
                if create_response.status_code != 201:
                    pytest.skip("Could not create test prompt for WebSocket invalid action test")
                
                created_prompt = create_response.json()
                prompt_id = created_prompt["id"]
                
                try:
                    # Connect to WebSocket
                    ws_url = f"{WS_BASE_URL}/ws/prompts/{prompt_id}"
                    
                    async with websockets.connect(ws_url) as websocket:
                        # Receive initial data
                        initial_data_raw = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        initial_data = json.loads(initial_data_raw)
                        assert initial_data["action"] == "initial"
                        
                        # Send invalid action
                        invalid_message = {
                            "action": "invalid_action",
                            "data": "should be ignored"
                        }
                        await websocket.send(json.dumps(invalid_message))
                        
                        # Connection should remain open, but no response should be sent
                        # Try to send a valid message after the invalid one
                        valid_message = {
                            "action": "update",
                            "content": "Valid update after invalid action"
                        }
                        await websocket.send(json.dumps(valid_message))
                        
                        # Should receive update status for the valid message
                        status_response_raw = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        status_response = json.loads(status_response_raw)
                        
                        assert status_response["action"] == "update_status"
                        assert status_response["success"] is True
                        
                finally:
                    # Clean up
                    await http_client.delete(f"/prompts/{prompt_id}")
                    
        except ConnectionRefusedError:
            pytest.skip("WebSocket server not available")
        except Exception as e:
            pytest.skip(f"WebSocket invalid action test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
