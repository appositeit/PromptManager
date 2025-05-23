#!/usr/bin/env python
"""
WebSocket request header debug script.

This script adds detailed logging of the request headers in the WebSocket endpoint
to help diagnose CORS or security issues.
"""

import asyncio
import json
import sys
from websockets import connect
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("websocket_debug")

async def test_connection(host, port, endpoint, headers=None):
    """Test WebSocket connection with the given headers."""
    uri = f"ws://{host}:{port}{endpoint}"
    logger.info(f"Connecting to {uri}")
    
    # Default headers to emulate a browser
    if not headers:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            "Origin": f"http://{host}:{port}",
            "Host": f"{host}:{port}",
            "Connection": "Upgrade",
            "Upgrade": "websocket",
            "Sec-WebSocket-Version": "13",
            "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
            "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",  # Example value, will be replaced by websockets
            "Pragma": "no-cache",
            "Cache-Control": "no-cache"
        }
    
    logger.info(f"Using headers: {json.dumps(headers, indent=2)}")
    
    try:
        async with connect(uri, extra_headers=headers) as websocket:
            logger.info("Connection established! Waiting for first message...")
            response = await websocket.recv()
            logger.info(f"Received: {response}")
            
            # Send a test message if connected
            test_message = "WebSocket debug test message"
            logger.info(f"Sending: {test_message}")
            await websocket.send(test_message)
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                logger.info(f"Received: {response}")
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for response")
    except Exception as e:
        logger.error(f"Connection failed: {str(e)}")
        return False
    
    return True

async def test_cors_headers(host, port, endpoint, origins):
    """Test WebSocket connection with different Origin headers."""
    success = False
    
    # Test each origin
    for origin in origins:
        logger.info(f"Testing Origin: {origin}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            "Origin": origin,
            "Host": f"{host}:{port}",
            "Connection": "Upgrade",
            "Upgrade": "websocket",
            "Sec-WebSocket-Version": "13",
            "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits"
        }
        
        if await test_connection(host, port, endpoint, headers):
            logger.info(f"SUCCESS: Connection with Origin={origin} worked!")
            success = True
        else:
            logger.warning(f"FAILED: Connection with Origin={origin} failed")
    
    return success

async def test_no_origin(host, port, endpoint):
    """Test WebSocket connection without Origin header."""
    logger.info("Testing connection without Origin header")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        "Host": f"{host}:{port}",
        "Connection": "Upgrade",
        "Upgrade": "websocket",
        "Sec-WebSocket-Version": "13",
        "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits"
    }
    
    if await test_connection(host, port, endpoint, headers):
        logger.info("SUCCESS: Connection without Origin header worked!")
        return True
    else:
        logger.warning("FAILED: Connection without Origin header failed")
        return False

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="WebSocket request header debug script")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8081, help="Server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug endpoint test")
    parser.add_argument("--prompt", default="ws_test_d9d721f6", help="Prompt ID to test")
    
    args = parser.parse_args()
    
    # Test endpoints
    endpoints = []
    if args.debug:
        endpoints.append("/api/ws/test")
    
    # Add prompt endpoint
    endpoints.append(f"/api/prompts/ws/{args.prompt}")
    
    # Origins to test
    origins = [
        f"http://{args.host}:{args.port}",
        f"https://{args.host}:{args.port}",
        f"http://{args.host}",
        f"https://{args.host}",
        "null"
    ]
    
    # Test each endpoint
    for endpoint in endpoints:
        logger.info(f"Testing endpoint: {endpoint}")
        logger.info("=" * 60)
        
        # Test with different origins
        await test_cors_headers(args.host, args.port, endpoint, origins)
        
        # Test without Origin header
        await test_no_origin(args.host, args.port, endpoint)
        
        logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
