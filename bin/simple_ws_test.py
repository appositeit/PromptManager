#!/usr/bin/env python3
"""
Simple WebSocket test script.

This script tests WebSocket connections with minimal dependencies.
"""

import asyncio
import json
import websockets
import sys
import argparse

async def test_websocket(url, verbose=False):
    """Test a WebSocket connection with verbose output."""
    print(f"Connecting to {url}...")
    
    # Prepare headers
    extra_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Origin": "http://localhost:8081",
        "Host": "localhost:8081"
    }
    
    if verbose:
        print(f"Using headers: {extra_headers}")
    
    try:
        async with websockets.connect(url, extra_headers=extra_headers) as ws:
            print("Connection established!")
            
            # Wait for initial message
            initial_msg = await ws.recv()
            print(f"Received: {initial_msg}")
            
            # Send a test message
            test_msg = json.dumps({"type": "test", "message": "Hello from test script"})
            print(f"Sending: {test_msg}")
            await ws.send(test_msg)
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print(f"Received response: {response}")
            except asyncio.TimeoutError:
                print("No response received (timeout)")
            
            print("Test completed successfully")
            return True
    except Exception as e:
        print(f"Error: {str(e)}")
        if verbose and hasattr(e, 'status_code'):
            print(f"HTTP Status: {e.status_code}")
        return False

async def main():
    parser = argparse.ArgumentParser(description="Test WebSocket connections")
    parser.add_argument("--host", default="localhost", help="Host to connect to")
    parser.add_argument("--port", type=int, default=8081, help="Port to connect to")
    parser.add_argument("--debug", action="store_true", help="Test debug endpoint")
    parser.add_argument("--prompt", default="ws_test_84b4bf6d", help="Prompt ID to test")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Determine endpoints to test
    endpoints = []
    
    if args.debug:
        endpoints.append(f"ws://{args.host}:{args.port}/api/ws/test")
    
    endpoints.append(f"ws://{args.host}:{args.port}/api/prompts/ws/{args.prompt}")
    
    # Test each endpoint
    success = True
    for url in endpoints:
        print(f"\n=== Testing {url} ===")
        result = await test_websocket(url, args.verbose)
        if not result:
            success = False
    
    # Return appropriate exit code
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
