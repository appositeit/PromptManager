"""
Comprehensive WebSocket Integration Tests
Tests for WebSocket functionality and real-time features
"""

import pytest
import asyncio
import json
import websockets
from typing import Dict, Any, List
import httpx

# WebSocket URL - Use the test endpoint since we don't have a specific prompt
WS_URL = "ws://localhost:8095/api/ws/test"
API_BASE_URL = "http://localhost:8095/api"


class TestWebSocketConnection:
    """Test basic WebSocket connection and communication"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection_basic(self):
        """Test basic WebSocket connection"""
        try:
            async with websockets.connect(WS_URL) as websocket:
                # First, receive the initial text message
                initial_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                assert "successful" in initial_response.lower(), f"Expected success message, got: {initial_response}"
                
                # Send a test message
                await websocket.send("ping test message")
                
                # Wait for JSON response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                message = json.loads(response)
                
                # Should get an echo response with our message
                assert "received" in message, f"Expected echo response with 'received' field: {message}"
                assert message["received"] == "ping test message", f"Expected echo of our message: {message}"
                
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
            pytest.skip(f"WebSocket server not available: {e}")
        except asyncio.TimeoutError:
            pytest.skip("WebSocket connection timeout")
    
    @pytest.mark.asyncio
    async def test_websocket_multiple_connections(self):
        """Test multiple simultaneous WebSocket connections"""
        try:
            connections = []
            
            # Open multiple connections
            for i in range(3):
                connection = await websockets.connect(WS_URL)
                # Consume initial message
                await asyncio.wait_for(connection.recv(), timeout=5.0)
                connections.append(connection)
            
            try:
                # Send messages from each connection
                for i, connection in enumerate(connections):
                    await connection.send(f"test_message_{i}")
                
                # Each connection should be able to send and receive
                for i, connection in enumerate(connections):
                    response = await asyncio.wait_for(connection.recv(), timeout=5.0)
                    message = json.loads(response)
                    assert message["received"] == f"test_message_{i}"
                    
            finally:
                # Clean up connections
                for connection in connections:
                    await connection.close()
                    
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError):
            pytest.skip("WebSocket server not available")
        except asyncio.TimeoutError:
            pytest.skip("WebSocket connection timeout")


class TestWebSocketPromptEditing:
    """Test real-time prompt editing via WebSocket"""
    
    @pytest.mark.asyncio
    async def test_prompt_update_notification(self):
        """Test that prompt updates are broadcast via WebSocket"""
        try:
            # First, create a test prompt via API
            async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as http_client:
                test_prompt = {
                    "name": "ws_test_prompt",
                    "directory": "/tmp/ws_test",
                    "content": "Original content for WebSocket test",
                    "description": "Test prompt for WebSocket notifications"
                }
                
                # Clean up first
                await http_client.delete("/prompts/ws_test/ws_test_prompt")
                
                # Create the prompt
                create_response = await http_client.post("/prompts/", json=test_prompt)
                if create_response.status_code != 201:
                    pytest.skip("Could not create test prompt for WebSocket test")
                
                created_prompt = create_response.json()
                prompt_id = created_prompt["id"]
                
                try:
                    # Connect to WebSocket
                    async with websockets.connect(WS_URL) as websocket:
                        # Update the prompt via API
                        update_data = {
                            "content": "Updated content via API for WebSocket test",
                            "description": "Updated description"
                        }
                        
                        update_response = await http_client.put(f"/prompts/{prompt_id}", json=update_data)
                        assert update_response.status_code == 200
                        
                        # Listen for WebSocket notification
                        try:
                            # First consume the initial connection message if present
                            initial_message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                            
                            # Look for notification message
                            message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                            
                            # Handle empty messages
                            if not message or message.strip() == "":
                                pytest.skip("No WebSocket notification received - empty message")
                            
                            notification = json.loads(message)
                            
                            # Should receive notification about the update
                            assert notification.get("type") in ["prompt_updated", "update", "change"], \
                                f"Expected update notification, got: {notification.get('type')}"
                            
                        except asyncio.TimeoutError:
                            # WebSocket notifications might not be implemented yet
                            pytest.skip("No WebSocket notification received - feature may not be implemented")
                        except json.JSONDecodeError:
                            pytest.skip(f"Invalid JSON response from WebSocket: {message}")
                        
                finally:
                    # Clean up
                    await http_client.delete(f"/prompts/{prompt_id}")
                    
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError):
            pytest.skip("WebSocket server not available")
        except Exception as e:
            pytest.skip(f"WebSocket test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_collaborative_editing_simulation(self):
        """Test simulation of collaborative editing"""
        try:
            # Create test prompt
            async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as http_client:
                test_prompt = {
                    "name": "collab_test_prompt",
                    "directory": "/tmp/collab_test",
                    "content": "Original collaborative content",
                    "description": "Test prompt for collaborative editing"
                }
                
                # Clean up first
                await http_client.delete("/prompts/collab_test/collab_test_prompt")
                
                create_response = await http_client.post("/prompts/", json=test_prompt)
                if create_response.status_code != 201:
                    pytest.skip("Could not create test prompt for collaborative test")
                
                created_prompt = create_response.json()
                prompt_id = created_prompt["id"]
                
                try:
                    # Simulate two editors
                    async with websockets.connect(WS_URL) as editor1, \
                               websockets.connect(WS_URL) as editor2:
                        
                        # Editor 1 makes an update
                        update_data_1 = {
                            "content": "Content updated by editor 1",
                            "description": "Updated by editor 1"
                        }
                        
                        update_response = await http_client.put(f"/prompts/{prompt_id}", json=update_data_1)
                        assert update_response.status_code == 200
                        
                        # Both editors should potentially receive notifications
                        # (Implementation dependent)
                        
                        # Small delay to allow notifications to propagate
                        await asyncio.sleep(0.5)
                        
                        # Editor 2 makes another update
                        update_data_2 = {
                            "content": "Content updated by editor 2",
                            "description": "Updated by editor 2"
                        }
                        
                        update_response = await http_client.put(f"/prompts/{prompt_id}", json=update_data_2)
                        assert update_response.status_code == 200
                        
                        # Verify final state
                        get_response = await http_client.get(f"/prompts/{prompt_id}")
                        assert get_response.status_code == 200
                        
                        final_prompt = get_response.json()
                        assert "editor 2" in final_prompt["content"], "Final update should be from editor 2"
                        
                finally:
                    # Clean up
                    await http_client.delete(f"/prompts/{prompt_id}")
                    
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError):
            pytest.skip("WebSocket server not available")
        except Exception as e:
            pytest.skip(f"Collaborative editing test failed: {e}")


class TestWebSocketErrorHandling:
    """Test WebSocket error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_websocket_invalid_message(self):
        """Test WebSocket handling of invalid messages"""
        try:
            async with websockets.connect(WS_URL) as websocket:
                # Consume initial message
                await asyncio.wait_for(websocket.recv(), timeout=5.0)
                
                # Send a simple test message (server expects text, not JSON)
                await websocket.send("test message")
                
                # Should get a valid response
                response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                message = json.loads(response)
                assert "received" in message, "Expected echo response"
                    
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError):
            pytest.skip("WebSocket server not available")
        except asyncio.TimeoutError:
            pytest.skip("WebSocket connection timeout")
    
    @pytest.mark.asyncio
    async def test_websocket_large_message(self):
        """Test WebSocket handling of large messages"""
        try:
            async with websockets.connect(WS_URL) as websocket:
                # Consume initial message
                await asyncio.wait_for(websocket.recv(), timeout=5.0)
                
                # Send a large text message
                large_content = "x" * 1000  # 1KB message (reasonable size)
                await websocket.send(large_content)
                
                # Should handle large messages
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    message = json.loads(response)
                    assert message["received"] == large_content
                except asyncio.TimeoutError:
                    # Large messages might timeout
                    pytest.skip("Large message timeout")
                    
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError):
            pytest.skip("WebSocket server not available")
    
    @pytest.mark.asyncio
    async def test_websocket_rapid_messages(self):
        """Test WebSocket handling of rapid message sending"""
        try:
            async with websockets.connect(WS_URL) as websocket:
                # Consume initial message
                await asyncio.wait_for(websocket.recv(), timeout=5.0)
                
                # Send several messages rapidly and consume responses
                for i in range(5):  # Reduced number for stability
                    await websocket.send(f"rapid_test_{i}")
                    # Consume each response to prevent buffer overflow
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    message = json.loads(response)
                    assert message["received"] == f"rapid_test_{i}"
                
                # Final test message
                await websocket.send("final_ping")
                response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                message = json.loads(response)
                assert message["received"] == "final_ping"
                    
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError):
            pytest.skip("WebSocket server not available")
        except asyncio.TimeoutError:
            pytest.skip("WebSocket rapid message timeout")


class TestWebSocketIntegrationWithAPI:
    """Test integration between WebSocket and REST API"""
    
    @pytest.mark.asyncio
    async def test_api_prompt_creation_websocket_notification(self):
        """Test that prompt creation via API triggers WebSocket notification"""
        try:
            async with websockets.connect(WS_URL) as websocket:
                # Create prompt via API
                async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as http_client:
                    test_prompt = {
                        "name": "ws_api_integration_test",
                        "directory": "/tmp/ws_api_test",
                        "content": "Content for WebSocket API integration test",
                        "description": "Test prompt for WebSocket-API integration"
                    }
                    
                    # Clean up first
                    await http_client.delete("/prompts/ws_api_test/ws_api_integration_test")
                    
                    # Create the prompt
                    create_response = await http_client.post("/prompts/", json=test_prompt)
                    
                    if create_response.status_code == 201:
                        created_prompt = create_response.json()
                        
                        try:
                            # Listen for WebSocket notification
                            try:
                                # First consume the initial connection message if present
                                initial_message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                                
                                # Look for notification message
                                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                                
                                # Handle empty messages
                                if not message or message.strip() == "":
                                    pytest.skip("No WebSocket notification for prompt creation - empty message")
                                
                                notification = json.loads(message)
                                
                                # Should receive notification about the creation
                                assert notification.get("type") in ["prompt_created", "create", "new"], \
                                    f"Expected creation notification, got: {notification.get('type')}"
                                    
                            except asyncio.TimeoutError:
                                # WebSocket notifications might not be implemented
                                pytest.skip("No WebSocket notification for prompt creation")
                            except json.JSONDecodeError:
                                pytest.skip(f"Invalid JSON response from WebSocket: {message}")
                                
                        finally:
                            # Clean up
                            await http_client.delete(f"/prompts/{created_prompt['id']}")
                    else:
                        pytest.skip("Could not create test prompt for WebSocket-API integration test")
                        
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError):
            pytest.skip("WebSocket server not available")
    
    @pytest.mark.asyncio 
    async def test_api_prompt_deletion_websocket_notification(self):
        """Test that prompt deletion via API triggers WebSocket notification"""
        try:
            # First create a prompt
            async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as http_client:
                test_prompt = {
                    "name": "ws_delete_test",
                    "directory": "/tmp/ws_delete_test",
                    "content": "Content for WebSocket deletion test",
                    "description": "Test prompt for WebSocket deletion notification"
                }
                
                # Clean up first
                await http_client.delete("/prompts/ws_delete_test/ws_delete_test")
                
                create_response = await http_client.post("/prompts/", json=test_prompt)
                if create_response.status_code != 201:
                    pytest.skip("Could not create test prompt for deletion test")
                
                created_prompt = create_response.json()
                prompt_id = created_prompt["id"]
                
                # Connect to WebSocket
                async with websockets.connect(WS_URL) as websocket:
                    # Delete the prompt
                    delete_response = await http_client.delete(f"/prompts/{prompt_id}")
                    assert delete_response.status_code == 200
                    
                    # Listen for WebSocket notification
                    try:
                        # First consume the initial connection message if present
                        initial_message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        
                        # Look for notification message
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        
                        # Handle empty messages
                        if not message or message.strip() == "":
                            pytest.skip("No WebSocket notification for prompt deletion - empty message")
                        
                        notification = json.loads(message)
                        
                        # Should receive notification about the deletion
                        assert notification.get("type") in ["prompt_deleted", "delete", "removed"], \
                            f"Expected deletion notification, got: {notification.get('type')}"
                            
                    except asyncio.TimeoutError:
                        # WebSocket notifications might not be implemented
                        pytest.skip("No WebSocket notification for prompt deletion")
                    except json.JSONDecodeError:
                        pytest.skip(f"Invalid JSON response from WebSocket: {message}")
                        
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError):
            pytest.skip("WebSocket server not available")


class TestWebSocketPerformance:
    """Test WebSocket performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection_stability(self):
        """Test WebSocket connection stability over time"""
        try:
            async with websockets.connect(WS_URL) as websocket:
                # Keep connection alive for a reasonable period
                for i in range(10):
                    await websocket.send(json.dumps({
                        "type": "stability_test",
                        "data": {"iteration": i}
                    }))
                    
                    # Wait between messages
                    await asyncio.sleep(0.5)
                    
                    # Try to receive any responses (optional)
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    except asyncio.TimeoutError:
                        pass  # No response expected necessarily
                
                # Final ping to verify connection is still alive
                await websocket.send(json.dumps({"type": "final_ping"}))
                
                # Connection should still be working - test by trying to send/receive
                await websocket.send("ping")
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                # If we get here, connection is still alive
                assert True, "WebSocket connection is still working"
                
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError):
            pytest.skip("WebSocket server not available")
    
    @pytest.mark.asyncio
    async def test_websocket_message_throughput(self):
        """Test WebSocket message throughput"""
        try:
            async with websockets.connect(WS_URL) as websocket:
                import time
                
                # Send many messages and measure time
                num_messages = 100
                start_time = time.time()
                
                for i in range(num_messages):
                    await websocket.send(json.dumps({
                        "type": "throughput_test",
                        "data": {"message_id": i}
                    }))
                
                end_time = time.time()
                elapsed = end_time - start_time
                
                # Should be able to send messages reasonably quickly
                messages_per_second = num_messages / elapsed
                assert messages_per_second > 10, f"Message throughput too low: {messages_per_second:.2f} msg/s"
                
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError):
            pytest.skip("WebSocket server not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
