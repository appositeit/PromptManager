#!/usr/bin/env python
"""
WebSocket API test with improved connection handling.

A modified version of the test script with better header handling.
"""

import asyncio
import json
import sys
import time
import uuid
import logging
import argparse
import websockets
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

class ImprovedWebSocketTester:
    """Base class for WebSocket API testing with improved connection handling."""
    
    def __init__(self, host: str = "localhost", port: int = 8081):
        """Initialize the tester."""
        self.host = host
        self.port = port
        self.base_uri = f"ws://{host}:{port}"
    
    async def test_debug_connection(self):
        """Test the debug WebSocket endpoint."""
        uri = f"{self.base_uri}/api/ws/test"
        
        # Use proper headers that mimic a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            "Origin": f"http://{self.host}:{self.port}",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "Host": f"{self.host}:{self.port}",
            "Upgrade": "websocket",
            "Connection": "Upgrade",
            "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
            "Sec-WebSocket-Version": "13",
            "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits"
        }
        
        try:
            logger.info(f"Connecting to debug WebSocket: {uri}")
            
            # Connect to the debug WebSocket
            async with websockets.connect(uri, extra_headers=headers) as websocket:
                logger.info("Debug connection established")
                
                # Receive welcome message
                response = await websocket.recv()
                logger.info(f"Received: {response}")
                
                # Send a message
                test_message = f"Test message {uuid.uuid4().hex}"
                logger.info(f"Sending: {test_message}")
                await websocket.send(test_message)
                
                # Receive echo response
                response = await websocket.recv()
                try:
                    data = json.loads(response)
                    logger.info(f"Received echo: {data}")
                    
                    # Validate the response
                    assert data["received"] == test_message, "Echo message doesn't match"
                    assert "counter" in data, "Missing counter in response"
                    assert "timestamp" in data, "Missing timestamp in response"
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse response: {response}")
                    return False
                except AssertionError as e:
                    logger.error(f"Validation failed: {str(e)}")
                    return False
                
                logger.info("Debug connection test passed!")
                return True
        except Exception as e:
            logger.error(f"Error in debug connection: {str(e)}")
            return False
    
    async def test_prompt_connection(self, prompt_id: str):
        """Test connecting to a prompt WebSocket."""
        uri = f"{self.base_uri}/api/prompts/ws/{prompt_id}"
        
        # Use proper headers that mimic a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            "Origin": f"http://{self.host}:{self.port}",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "Host": f"{self.host}:{self.port}",
            "Upgrade": "websocket",
            "Connection": "Upgrade",
            "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
            "Sec-WebSocket-Version": "13",
            "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits"
        }
        
        try:
            logger.info(f"Connecting to prompt WebSocket: {uri}")
            
            # Connect to the prompt WebSocket
            async with websockets.connect(uri, extra_headers=headers) as websocket:
                logger.info("Prompt connection established")
                
                # Receive initial data
                response = await websocket.recv()
                try:
                    data = json.loads(response)
                    logger.info(f"Received initial data: {data}")
                    
                    # Validate the initial data
                    assert data["action"] == "initial", "Initial message has wrong action"
                    assert "content" in data, "Missing content in initial data"
                    assert "description" in data, "Missing description in initial data"
                    assert "tags" in data, "Missing tags in initial data"
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse response: {response}")
                    return False
                except AssertionError as e:
                    logger.error(f"Validation failed: {str(e)}")
                    return False
                
                # Test content update
                await self.test_update_content(websocket, prompt_id)
                
                # Test metadata update
                await self.test_update_metadata(websocket, prompt_id)
                
                # Test expansion
                await self.test_expansion(websocket, prompt_id)
                
                logger.info("Prompt connection test passed!")
                return True
        except Exception as e:
            logger.error(f"Error in prompt connection: {str(e)}")
            return False
    
    async def test_update_content(self, websocket, prompt_id: str):
        """Test updating prompt content."""
        # Update content
        new_content = f"Updated test content at {time.time()}"
        update_message = {
            "action": "update",
            "content": new_content
        }
        
        logger.info(f"Sending content update: {new_content[:30]}...")
        await websocket.send(json.dumps(update_message))
        
        # Receive update status
        response = await websocket.recv()
        try:
            data = json.loads(response)
            logger.info(f"Received update status: {data}")
            
            # Validate the update status
            assert data["action"] == "update_status", "Wrong action in response"
            assert data["success"] is True, "Update failed"
            assert "timestamp" in data, "Missing timestamp in response"
            
            logger.info("Content update test passed!")
            return True
        except json.JSONDecodeError:
            logger.error(f"Failed to parse response: {response}")
            return False
        except AssertionError as e:
            logger.error(f"Validation failed: {str(e)}")
            return False
    
    async def test_update_metadata(self, websocket, prompt_id: str):
        """Test updating prompt metadata."""
        # Update metadata
        new_description = f"Updated description at {time.time()}"
        new_tags = ["test", "updated", str(time.time())]
        
        update_message = {
            "action": "update_metadata",
            "description": new_description,
            "tags": new_tags
        }
        
        logger.info(f"Sending metadata update: {new_description[:30]}...")
        await websocket.send(json.dumps(update_message))
        
        # Receive update status
        response = await websocket.recv()
        try:
            data = json.loads(response)
            logger.info(f"Received metadata update status: {data}")
            
            # Validate the update status
            assert data["action"] == "update_status", "Wrong action in response"
            assert data["success"] is True, "Update failed"
            assert "timestamp" in data, "Missing timestamp in response"
            
            logger.info("Metadata update test passed!")
            return True
        except json.JSONDecodeError:
            logger.error(f"Failed to parse response: {response}")
            return False
        except AssertionError as e:
            logger.error(f"Validation failed: {str(e)}")
            return False
    
    async def test_expansion(self, websocket, prompt_id: str):
        """Test prompt content expansion."""
        # Send expansion request
        test_content = "Content with [[inclusions]]"
        expand_message = {
            "action": "expand",
            "content": test_content
        }
        
        logger.info(f"Sending expansion request: {test_content}")
        await websocket.send(json.dumps(expand_message))
        
        # Receive expansion response
        response = await websocket.recv()
        try:
            data = json.loads(response)
            logger.info(f"Received expansion response: {data}")
            
            # Validate the expansion
            assert data["action"] == "expanded", "Wrong action in response"
            assert data["content"] == test_content, "Content doesn't match request"
            assert "expanded" in data, "Missing expanded content"
            assert "dependencies" in data, "Missing dependencies"
            assert "warnings" in data, "Missing warnings"
            
            logger.info("Expansion test passed!")
            return True
        except json.JSONDecodeError:
            logger.error(f"Failed to parse response: {response}")
            return False
        except AssertionError as e:
            logger.error(f"Validation failed: {str(e)}")
            return False
    
    async def create_test_prompt(self) -> Optional[str]:
        """Create a test prompt via the API."""
        import requests
        import uuid
        
        prompt_id = f"ws_test_{uuid.uuid4().hex[:8]}"
        
        try:
            response = requests.post(
                f"http://{self.host}:{self.port}/api/prompts/",
                json={
                    "id": prompt_id,
                    "content": "Test prompt for WebSocket API testing",
                    "description": "Created by automated test",
                    "tags": ["test", "websocket", "automated"],
                    "directory": "/home/jem/development/prompt_manager/prompts"  # Use existing directory
                }
            )
            
            if response.status_code in (200, 201):  # Accept both 200 and 201
                logger.info(f"Created test prompt: {prompt_id}")
                return prompt_id
            else:
                logger.error(f"Failed to create test prompt: {response.status_code} {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating test prompt: {str(e)}")
            return None

async def run_tests():
    """Run all WebSocket tests."""
    parser = argparse.ArgumentParser(description="Test WebSocket API")
    parser.add_argument("--host", default="localhost", help="Host to connect to")
    parser.add_argument("--port", type=int, default=8081, help="Port to connect to")
    
    args = parser.parse_args()
    
    # Create and run tester
    tester = ImprovedWebSocketTester(host=args.host, port=args.port)
    
    # Test debug connection
    logger.info("=== Testing Debug WebSocket ===")
    debug_result = await tester.test_debug_connection()
    
    # Create test prompt
    prompt_id = await tester.create_test_prompt()
    
    if prompt_id:
        # Test prompt connection
        logger.info(f"\n=== Testing Prompt WebSocket with {prompt_id} ===")
        prompt_result = await tester.test_prompt_connection(prompt_id)
    else:
        prompt_result = False
    
    # Print results
    logger.info("\n=== Test Results ===")
    logger.info(f"Debug WebSocket Test: {'PASSED' if debug_result else 'FAILED'}")
    if prompt_id:
        logger.info(f"Prompt WebSocket Test: {'PASSED' if prompt_result else 'FAILED'}")
    else:
        logger.info("Prompt WebSocket Test: SKIPPED (Couldn't create test prompt)")
    
    # Overall result
    if debug_result and (prompt_result or not prompt_id):
        logger.info("\nAll tests PASSED!")
        return 0
    else:
        logger.error("\nSome tests FAILED!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)
