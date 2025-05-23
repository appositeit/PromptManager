#!/usr/bin/env python
"""
Debug script for WebSocket API testing.
"""

import asyncio
import logging
import sys
import requests
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

async def test_debug_connection():
    """Test the debug WebSocket endpoint."""
    uri = "ws://localhost:8081/api/ws/test"
    
    logger.info(f"Connecting to {uri}")
    
    # Add browser-like headers
    extra_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        "Origin": "http://localhost:8081",
        "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
        "Sec-WebSocket-Version": "13"
    }
    
    try:
        async with websockets.connect(uri, extra_headers=extra_headers) as websocket:
            logger.info("Connected to test WebSocket")
            
            # Receive welcome message
            response = await websocket.recv()
            logger.info(f"Received welcome: {response}")
            
            # Send a message
            test_message = "Debug test message"
            logger.info(f"Sending message: {test_message}")
            await websocket.send(test_message)
            
            # Receive echo
            response = await websocket.recv()
            logger.info(f"Received response: {response}")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

async def test_prompt_connection(prompt_id):
    """Test connecting to a prompt WebSocket."""
    uri = f"ws://localhost:8081/api/prompts/ws/{prompt_id}"
    
    logger.info(f"Connecting to {uri}")
    
    # Try with different headers
    extra_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        "Origin": "http://localhost:8081",
        "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
        "Sec-WebSocket-Version": "13",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "Upgrade",
        "Host": "localhost:8081",
        "Pragma": "no-cache",
        "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
        "Upgrade": "websocket"
    }
    
    try:
        async with websockets.connect(uri, extra_headers=extra_headers) as websocket:
            logger.info("Connected to prompt WebSocket")
            
            # Receive initial data
            response = await websocket.recv()
            logger.info(f"Received initial data: {response}")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

async def create_test_prompt():
    """Create a test prompt."""
    import uuid
    
    prompt_id = f"ws_test_{uuid.uuid4().hex[:8]}"
    
    try:
        response = requests.post(
            "http://localhost:8081/api/prompts/",
            json={
                "id": prompt_id,
                "content": "Test prompt for WebSocket API testing",
                "description": "Created by automated test",
                "tags": ["test", "websocket", "automated"],
                "directory": "/home/jem/development/prompt_manager/prompts"
            }
        )
        
        if response.status_code == 200:
            logger.info(f"Created test prompt: {prompt_id}")
            logger.info(f"Response: {response.text}")
            return prompt_id
        else:
            logger.error(f"Failed to create test prompt: {response.status_code} {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error creating test prompt: {str(e)}")
        return None

async def main():
    """Run the test script."""
    # Test debug connection
    try:
        await test_debug_connection()
        logger.info("Debug connection test passed")
    except Exception as e:
        logger.error(f"Debug connection test failed: {str(e)}")
    
    # Create a test prompt
    prompt_id = await create_test_prompt()
    
    if prompt_id:
        # Test prompt connection
        try:
            await test_prompt_connection(prompt_id)
            logger.info("Prompt connection test passed")
        except Exception as e:
            logger.error(f"Prompt connection test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
