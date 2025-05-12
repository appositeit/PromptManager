#!/usr/bin/env python
"""
WebSocket Testing Tool for Prompt Manager

This script tests WebSocket connectivity to the Prompt Manager server.
It can be used to verify that WebSocket endpoints are working correctly.

Usage:
    python test_websocket.py --type [prompt|fragment] --id [prompt_id or fragment_id]
    python test_websocket.py --type debug

Examples:
    python test_websocket.py --type prompt --id my_prompt
    python test_websocket.py --type fragment --id my_fragment
    python test_websocket.py --type debug
"""

import argparse
import asyncio
import json
import sys
import time
import websockets
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

async def test_prompt_websocket(prompt_id):
    """Test a connection to a prompt WebSocket endpoint."""
    uri = f"ws://localhost:8081/api/prompts/ws/{prompt_id}"
    logger.info(f"Connecting to prompt WebSocket at {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected successfully")
            
            # Wait for initial data
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received initial data: {json.dumps(data, indent=2)}")
            
            # Test expansion
            logger.info("Sending expansion request...")
            await websocket.send(json.dumps({
                "action": "expand",
                "content": "Test content for expansion"
            }))
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received expansion response: {json.dumps(data, indent=2)}")
            
            # Test update
            logger.info("Sending update request...")
            await websocket.send(json.dumps({
                "action": "update",
                "content": f"Updated test content at {time.time()}"
            }))
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received update response: {json.dumps(data, indent=2)}")
            
            # Done
            logger.info("Tests completed successfully")
            
    except Exception as e:
        logger.error(f"Error testing prompt WebSocket: {str(e)}")
        return False
    
    return True

async def test_fragment_websocket(fragment_id):
    """Test a connection to a fragment WebSocket endpoint."""
    uri = f"ws://localhost:8081/api/prompts/ws/fragments/{fragment_id}"
    logger.info(f"Connecting to fragment WebSocket at {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected successfully")
            
            # Wait for initial data
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received initial data: {json.dumps(data, indent=2)}")
            
            # Test expansion
            logger.info("Sending expansion request...")
            await websocket.send(json.dumps({
                "action": "expand",
                "content": "Test content for expansion"
            }))
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received expansion response: {json.dumps(data, indent=2)}")
            
            # Test update
            logger.info("Sending update request...")
            await websocket.send(json.dumps({
                "action": "update",
                "content": f"Updated test content at {time.time()}"
            }))
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received update response: {json.dumps(data, indent=2)}")
            
            # Done
            logger.info("Tests completed successfully")
            
    except Exception as e:
        logger.error(f"Error testing fragment WebSocket: {str(e)}")
        return False
    
    return True

async def test_debug_websocket():
    """Test a connection to the debug WebSocket endpoint."""
    uri = f"ws://localhost:8081/api/ws/test"
    logger.info(f"Connecting to debug WebSocket at {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected successfully")
            
            # Wait for welcome message
            response = await websocket.recv()
            logger.info(f"Received message: {response}")
            
            # Send a test message
            test_message = f"Test message at {time.time()}"
            logger.info(f"Sending message: {test_message}")
            await websocket.send(test_message)
            
            # Wait for echo
            response = await websocket.recv()
            try:
                data = json.loads(response)
                logger.info(f"Received echo: {json.dumps(data, indent=2)}")
            except:
                logger.info(f"Received echo: {response}")
            
            # Done
            logger.info("Tests completed successfully")
            
    except Exception as e:
        logger.error(f"Error testing debug WebSocket: {str(e)}")
        return False
    
    return True

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test WebSocket connections to Prompt Manager")
    parser.add_argument("--type", choices=["prompt", "fragment", "debug"], 
                        required=True, help="Type of WebSocket to test")
    parser.add_argument("--id", help="ID of prompt or fragment to test")
    parser.add_argument("--host", default="localhost", help="Host to connect to")
    parser.add_argument("--port", type=int, default=8081, help="Port to connect to")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.type in ["prompt", "fragment"] and not args.id:
        logger.error(f"You must provide an ID for {args.type} WebSocket tests")
        sys.exit(1)
    
    # Run the appropriate test
    success = False
    if args.type == "prompt":
        success = await test_prompt_websocket(args.id)
    elif args.type == "fragment":
        success = await test_fragment_websocket(args.id)
    elif args.type == "debug":
        success = await test_debug_websocket()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
