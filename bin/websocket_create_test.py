import asyncio
import httpx
import websockets
import json
import uuid
from pathlib import Path
import sys
from typing import Optional # Added Optional

# --- Configuration ---
BASE_HTTP_URL = "http://localhost:8081"
BASE_WS_URL = "ws://localhost:8081"
CREATE_PROMPT_ENDPOINT = "/api/prompts/"
WS_PROMPT_ENDPOINT_TEMPLATE = "/ws/prompts/{prompt_id}"

# Determine the default prompts directory
# Assuming the script is run from the project root, so ../prompts if script is in bin/
DEFAULT_PROMPT_DIRECTORY = str(Path(__file__).resolve().parent.parent / "prompts")

async def create_prompt_http(client: httpx.AsyncClient, prompt_id: str, content: str, directory: str) -> tuple[bool, str, Optional[str]]: # Return actual_id
    """Creates a new prompt via HTTP POST request. Returns (success, message, actual_prompt_id)."""
    url = f"{BASE_HTTP_URL}{CREATE_PROMPT_ENDPOINT}"
    payload = {
        "id": prompt_id,
        "content": content,
        "directory": directory,
        "description": f"Test prompt {prompt_id}",
        "tags": ["test", "websocket_tool"] # Corrected: Python list for JSON serialization
    }
    print(f"Attempting to create prompt '{prompt_id}' via HTTP POST to {url} with payload: {json.dumps(payload)}")
    try:
        response = await client.post(url, json=payload) # Ensure json=payload is used
        if response.status_code == 201: # Assuming 201 Created for new prompts
            response_data = response.json()
            actual_id = response_data.get("id")
            if not actual_id:
                print(f"HTTP: Prompt creation reported success (Status {response.status_code}) but 'id' missing in response.")
                return False, "Prompt creation successful but 'id' missing in response.", None
            print(f"HTTP: Prompt '{prompt_id}' created successfully (Status {response.status_code}). Actual ID: '{actual_id}'.")
            return True, f"Prompt created. Status: {response.status_code}", actual_id
        else:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = json.dumps(error_json, indent=2)
            except json.JSONDecodeError:
                pass # Keep raw text if not JSON
            print(f"HTTP: Failed to create prompt '{prompt_id}'. Status: {response.status_code}\nResponse:\n{error_detail}")
            return False, f"HTTP Error {response.status_code}: {error_detail}", None
    except httpx.RequestError as e:
        print(f"HTTP: Request error while creating prompt '{prompt_id}': {e}")
        return False, f"HTTP RequestError: {e}", None

async def test_websocket_connection(prompt_id: str) -> tuple[bool, str]:
    """Attempts to connect to the WebSocket endpoint for the given prompt_id."""
    # The prompt_id passed here should already be the (potentially sanitized) one from the server
    ws_url = f"{BASE_WS_URL}{WS_PROMPT_ENDPOINT_TEMPLATE.format(prompt_id=prompt_id)}"
    print(f"Attempting WebSocket connection to: {ws_url}")

    try:
        async with websockets.connect(ws_url, open_timeout=10) as websocket:
            print(f"WebSocket: Connection to '{ws_url}' established successfully.")
            try:
                initial_server_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"WebSocket: Received initial message from server: {initial_server_message[:200]}...")
            except asyncio.TimeoutError:
                print("WebSocket: Timeout waiting for initial message from server.")
            except websockets.exceptions.ConnectionClosed as e:
                print(f"WebSocket: Connection closed while waiting for initial server message. Code: {e.code}, Reason: '{e.reason}'")
                return False, f"WebSocket ConnectionClosed (during initial recv) Error Code {e.code}: {e.reason}"

            await websocket.close(code=1000, reason="Test finished")
            print(f"WebSocket: Connection to '{ws_url}' closed gracefully.")
            return True, "WebSocket connection successful and closed."

    except websockets.exceptions.InvalidStatusCode as e:
        reject_reason = ""
        if hasattr(e, 'headers') and e.headers: # Starlette/FastAPI might send custom headers
             reject_reason = e.headers.get('x-websocket-reject-reason', '') # Check for custom reject reason
        print(f"WebSocket: Failed to connect to '{ws_url}'. Invalid status code: {e.status_code} {reject_reason}")
        return False, f"WebSocket Handshake Error {e.status_code} {reject_reason}"
    except websockets.exceptions.ConnectionClosed as e:
        print(f"WebSocket: Connection to '{ws_url}' closed unexpectedly. Code: {e.code}, Reason: '{e.reason}'")
        return False, f"WebSocket ConnectionClosed Error Code {e.code}: {e.reason}"
    except ConnectionRefusedError:
        print(f"WebSocket: Connection to '{ws_url}' refused. Is the server running at {BASE_WS_URL}?")
        return False, "WebSocket ConnectionRefusedError"
    except asyncio.TimeoutError:
        print(f"WebSocket: Connection attempt to '{ws_url}' timed out.")
        return False, "WebSocket Connection Timeout"
    except Exception as e:
        print(f"WebSocket: An unexpected error occurred with '{ws_url}': {type(e).__name__} - {e}")
        return False, f"WebSocket Unexpected Error: {type(e).__name__} - {e}"

async def main():
    prompt_id_base = f"test_tool_{str(uuid.uuid4())[:8]}"
    # Submit an ID with a space to test sanitization
    original_prompt_id_to_submit = f"{prompt_id_base} with space" 
    prompt_content = f"# Test Prompt (Original ID: {original_prompt_id_to_submit})\nThis prompt was created by the automated WebSocket test tool."

    print(f"--- Starting WebSocket Test for New Prompt (attempting original ID: '{original_prompt_id_to_submit}') ---")

    async with httpx.AsyncClient() as client:
        # create_prompt_http now returns the actual_id from the server
        http_success, http_message, actual_prompt_id_from_server = await create_prompt_http(
            client, original_prompt_id_to_submit, prompt_content, DEFAULT_PROMPT_DIRECTORY
        )
        
        if not http_success or not actual_prompt_id_from_server:
            print(f"Prompt creation failed or actual ID not returned. Aborting WebSocket test. Details: {http_message}")
            return

        print(f"Server used prompt ID: '{actual_prompt_id_from_server}'. Original submitted: '{original_prompt_id_to_submit}'")
        
        await asyncio.sleep(0.2) 

        # Use the actual_prompt_id_from_server for the WebSocket test
        ws_success, ws_message = await test_websocket_connection(actual_prompt_id_from_server)
        
        if ws_success:
            print(f"SUCCESS: WebSocket test for prompt (original: '{original_prompt_id_to_submit}', actual: '{actual_prompt_id_from_server}') passed.")
        else:
            print(f"FAILURE: WebSocket test for prompt (original: '{original_prompt_id_to_submit}', actual: '{actual_prompt_id_from_server}') failed. Details: {ws_message}")

    print(f"--- Test Finished for Prompt (original: '{original_prompt_id_to_submit}', actual: '{actual_prompt_id_from_server}') ---")

if __name__ == "__main__":
    # Ensure the script can find modules in src if run from bin/
    current_script_path = Path(__file__).resolve()
    project_root = current_script_path.parent.parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    asyncio.run(main()) 