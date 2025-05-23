"""
Command-line integration testing tool for Prompt Manager WebSocket endpoints.

This script connects to and interacts with various WebSocket endpoints
provided by the Prompt Manager server to verify their basic functionality,
including connection, receiving initial data, and message exchange.

It can be run from the command line to manually test:
- Prompt-specific WebSockets (e.g., /ws/prompts/{prompt_id})
- Fragment-specific WebSockets (e.g., /ws/prompts/fragments/{fragment_id}) - If applicable
- Debug WebSockets (e.g., /api/ws/test) - If applicable

While this is a command-line tool, its functions can be adapted for
use within an automated pytest integration testing suite.

Endpoints Tested (examples, adjust host/port and paths as per actual server):
- ws://localhost:8081/ws/prompts/{prompt_id}
- ws://localhost:8081/ws/prompts/fragments/{fragment_id}
- ws://localhost:8081/api/ws/test

Usage:
    python test_websocket_tool.py --type [prompt|fragment|debug] --id [prompt_id_or_fragment_id] [--host HOST] [--port PORT]

Examples:
    python tests/integration/api/test_websocket_tool.py --type prompt --id my_prompt
    python tests/integration/api/test_websocket_tool.py --type debug --port 8081
"""

__test__ = False # Tell pytest not to collect tests from this file

import argparse
import asyncio
import json
import sys
import time
import websockets
import logging
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

async def test_prompt_websocket(prompt_id: str, host: str, port: int):
    """Test a connection to a prompt WebSocket endpoint."""
    # Use the `name` parameter from the WebSocket router for consistency if possible
    # For now, using the known path structure.
    uri = f"ws://{host}:{port}/ws/prompts/{prompt_id}"
    logger.info(f"Connecting to prompt WebSocket at {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info(f"Connected successfully to {uri}")
            
            # Wait for initial data (if server sends any upon connection)
            # This part is application-specific
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                logger.info(f"Received initial data: {json.dumps(data, indent=2)}")
            except asyncio.TimeoutError:
                logger.info("No initial data received within timeout, or server doesn't send one.")
            except json.JSONDecodeError:
                logger.warning(f"Received initial non-JSON response: {response!r}")
            except websockets.exceptions.ConnectionClosed:
                logger.error(f"Connection closed unexpectedly after connecting to {uri}")
                return False

            # Example: Test sending a generic message or a specific action
            # This needs to align with what your WebSocket endpoint expects
            test_message = {"action": "get_details"} # Example action
            logger.info(f"Sending test message: {json.dumps(test_message)}")
            await websocket.send(json.dumps(test_message))
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                logger.info(f"Received response: {json.dumps(data, indent=2)}")
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for response from server.")
                return False
            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON response: {response!r}")
            except websockets.exceptions.ConnectionClosed:
                logger.error(f"Connection closed while waiting for response from {uri}")
                return False
            
            logger.info(f"Test for prompt {prompt_id} completed successfully")
            
    except websockets.exceptions.InvalidStatus as e:
        logger.error(f"Failed to connect to {uri}. Status code: {e.response.status_code}. Headers: {e.response.headers}")
        if e.response.status_code == 403:
            logger.error("Received 403 Forbidden. This might indicate an authentication/authorization issue, or the prompt ID is not recognized by the WebSocket endpoint immediately after creation.")
        return False
    except ConnectionRefusedError:
        logger.error(f"Connection refused for {uri}. Is the server running on {host}:{port}?")
        return False
    except Exception as e:
        logger.error(f"Error testing prompt WebSocket {uri}: {type(e).__name__} - {str(e)}")
        return False
    
    return True

async def test_generic_websocket(endpoint_path: str, host: str, port: int, initial_message: Optional[dict] = None):
    """Test a generic WebSocket connection, send a message, and await a response."""
    uri = f"ws://{host}:{port}{endpoint_path}" # Ensure endpoint_path starts with /
    logger.info(f"Connecting to generic WebSocket at {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            logger.info(f"Connected successfully to {uri}")

            if initial_message:
                logger.info(f"Sending initial message: {json.dumps(initial_message)}")
                await websocket.send(json.dumps(initial_message))
            
            # Wait for a response (or initial unsolicited message)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0) # Increased timeout for general use
                try:
                    data = json.loads(response)
                    logger.info(f"Received response: {json.dumps(data, indent=2)}")
                except json.JSONDecodeError:
                    logger.info(f"Received non-JSON response: {response!r}")
            except asyncio.TimeoutError:
                logger.warning(f"Timeout waiting for response from {uri}. This might be normal if the endpoint only responds to specific messages.")
            except websockets.exceptions.ConnectionClosed as e:
                logger.error(f"Connection to {uri} closed: {e}")
                return False

            logger.info(f"Test for {uri} completed.")

    except websockets.exceptions.InvalidStatus as e:
        logger.error(f"Failed to connect to {uri}. Status code: {e.response.status_code}")
        return False
    except ConnectionRefusedError:
        logger.error(f"Connection refused for {uri}. Is the server running on {host}:{port}?")
        return False
    except Exception as e:
        logger.error(f"Error testing generic WebSocket {uri}: {type(e).__name__} - {str(e)}")
        return False
    return True


async def main():
    """Main function to parse arguments and run tests."""
    # prog_name = "test_websocket_tool.py" # Can be set if %(prog)s doesn't work as expected
    epilog_text = """Examples:
  Test a specific prompt WebSocket:
    python %(prog)s --type prompt --id my_prompt_id
  Test a debug WebSocket endpoint (if available at /api/ws/test):
    python %(prog)s --type debug
  Test a fragment WebSocket (if available at /ws/prompts/fragments/my_fragment_id):
    python %(prog)s --type fragment --id my_fragment_id
"""
    parser = argparse.ArgumentParser(
        description="Command-line tool for testing WebSocket connections to Prompt Manager.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=epilog_text
    )
    parser.add_argument("--type", choices=["prompt", "fragment", "debug", "generic"], 
                        required=True, help="Type of WebSocket to test. 'generic' requires --path.")
    parser.add_argument("--id", help="ID of prompt or fragment to test (for --type prompt/fragment). Example: my_prompt")
    parser.add_argument("--path", help="Full WebSocket path for --type generic (e.g., /ws/some/other/endpoint). Example: /api/ws/test")
    parser.add_argument("--host", default="localhost", help="Host of the Prompt Manager server (default: localhost)")
    parser.add_argument("--port", type=int, default=8081, help="Port of the Prompt Manager server (default: 8081)")
    parser.add_argument("--message", help="JSON string to send as an initial message for 'generic' type. Example: '{\"action\":\"ping\"}'")
    parser.add_argument("--count", type=int, default=1, help="Number of messages to send/expect for stream tests")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between sending messages")
    
    args = parser.parse_args()
    
    success = False
    if args.type == "prompt":
        if not args.id:
            logger.error("You must provide an --id for --type 'prompt'")
            sys.exit(1)
        success = await test_prompt_websocket(args.id, args.host, args.port)
    elif args.type == "fragment": # Assuming fragments might have a different path structure or dedicated test
        if not args.id:
            logger.error("You must provide an --id for --type 'fragment'")
            sys.exit(1)
        # Modify path for fragments if it's different, e.g.:
        fragment_path = f"/ws/prompts/fragments/{args.id}" 
        logger.info(f"Note: Treating 'fragment' type as a generic test for path: {fragment_path}")
        success = await test_generic_websocket(fragment_path, args.host, args.port)
    elif args.type == "debug": # Assuming a debug endpoint exists, e.g., /api/ws/test
        debug_path = "/api/ws/test" # Make this configurable if needed
        logger.info(f"Note: Treating 'debug' type as a generic test for path: {debug_path}")
        initial_debug_message = {"message": f"Debug test from tool at {time.time()}"}
        success = await test_generic_websocket(debug_path, args.host, args.port, initial_message=initial_debug_message)
    elif args.type == "generic":
        if not args.path:
            logger.error("You must provide --path for --type 'generic'")
            sys.exit(1)
        initial_msg_dict = None
        if args.message:
            try:
                initial_msg_dict = json.loads(args.message)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON string for --message: {args.message}")
                sys.exit(1)
        success = await test_generic_websocket(args.path, args.host, args.port, initial_message=initial_msg_dict)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    # Ensure sys.path is set up if this script is run directly and needs src imports
    # This is more relevant if the script itself tries to import from src, less so for websockets client.
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent.parent # Assuming tests/integration/api/test_websocket_tool.py
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        # print(f"Adjusted sys.path to include {project_root} for potential src.* imports.")

    asyncio.run(main()) 