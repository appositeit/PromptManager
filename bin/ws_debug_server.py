#!/usr/bin/env python
"""
Simple WebSocket debugging tool with improved CORS debugging.

This is a standalone server that helps diagnose CORS/WebSocket connection issues.
"""

import sys
import argparse
import logging
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

# Add CORS middleware with verbose logging
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Simple HTML page for testing
@app.get("/", response_class=HTMLResponse)
async def get_html():
    """Return a simple HTML page with WebSocket testing UI."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            pre { background-color: #f5f5f5; padding: 10px; border-radius: 5px; }
            button { margin: 5px; padding: 8px 15px; }
            input { padding: 8px; margin: 5px; width: 300px; }
            .log { height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin-top: 20px; }
        </style>
    </head>
    <body>
        <h1>WebSocket Test Server</h1>
        
        <h2>Connection</h2>
        <div>
            <input id="wsUrl" type="text" value="ws://localhost:8081/api/ws/test" placeholder="WebSocket URL">
            <button onclick="connect()">Connect</button>
            <button onclick="disconnect()">Disconnect</button>
            <span id="status">Disconnected</span>
        </div>
        
        <h2>Send Message</h2>
        <div>
            <input id="message" type="text" placeholder="Message to send">
            <button onclick="sendMessage()">Send</button>
        </div>
        
        <h2>Headers</h2>
        <div>
            <label>
                <input type="checkbox" id="useOrigin" checked> 
                Include Origin header
            </label>
            <input id="originValue" type="text" value="http://localhost:8081" placeholder="Origin value">
        </div>
        
        <h2>Connection Log</h2>
        <div class="log" id="log"></div>
        
        <script>
            let ws = null;
            const log = document.getElementById('log');
            const status = document.getElementById('status');
            
            function logMessage(message, isError = false) {
                const line = document.createElement('div');
                line.textContent = new Date().toISOString() + ': ' + message;
                if (isError) {
                    line.style.color = 'red';
                }
                log.appendChild(line);
                log.scrollTop = log.scrollHeight;
            }
            
            function connect() {
                if (ws) {
                    logMessage('Already connected, disconnecting first');
                    ws.close();
                }
                
                const url = document.getElementById('wsUrl').value;
                logMessage(`Connecting to ${url}`);
                
                try {
                    // Create WebSocket with optional headers
                    if (document.getElementById('useOrigin').checked) {
                        // We can't actually set headers in browser WebSocket,
                        // but we log what we would send for debugging
                        const origin = document.getElementById('originValue').value;
                        logMessage(`Using Origin: ${origin} (browser controls this)`);
                    }
                    
                    ws = new WebSocket(url);
                    
                    ws.onopen = () => {
                        logMessage('Connection established');
                        status.textContent = 'Connected';
                        status.style.color = 'green';
                    };
                    
                    ws.onmessage = (event) => {
                        try {
                            // Try to parse as JSON
                            const data = JSON.parse(event.data);
                            logMessage(`Received: ${JSON.stringify(data, null, 2)}`);
                        } catch (e) {
                            // Not JSON, treat as string
                            logMessage(`Received: ${event.data}`);
                        }
                    };
                    
                    ws.onerror = (error) => {
                        logMessage(`Error: ${error}`, true);
                    };
                    
                    ws.onclose = (event) => {
                        logMessage(`Connection closed: ${event.code} ${event.reason}`);
                        status.textContent = 'Disconnected';
                        status.style.color = 'red';
                        ws = null;
                    };
                } catch (error) {
                    logMessage(`Failed to create WebSocket: ${error}`, true);
                }
            }
            
            function disconnect() {
                if (ws) {
                    logMessage('Disconnecting');
                    ws.close();
                } else {
                    logMessage('Not connected');
                }
            }
            
            function sendMessage() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    const message = document.getElementById('message').value;
                    logMessage(`Sending: ${message}`);
                    ws.send(message);
                } else {
                    logMessage('Not connected', true);
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content

# Debug endpoint to get all request headers
@app.get("/debug/headers")
async def get_headers(request: Request):
    """Get all request headers for debugging."""
    return {
        "headers": dict(request.headers),
        "client": request.client.host if request.client else None,
        "method": request.method,
        "url": str(request.url)
    }

# Simple echo WebSocket endpoint
@app.websocket("/ws/echo")
async def websocket_echo(websocket: WebSocket):
    """Echo WebSocket endpoint."""
    # Log connection info
    client = websocket.client
    headers = websocket.headers
    logger.info(f"New connection from {client}")
    logger.info(f"Headers: {headers}")
    
    try:
        await websocket.accept()
        await websocket.send_text("Connected to echo WebSocket server")
        
        while True:
            message = await websocket.receive_text()
            logger.info(f"Received message: {message}")
            echo_response = {
                "echo": message,
                "timestamp": None,  # Can add a timestamp if desired
                "headers": dict(headers)
            }
            await websocket.send_json(echo_response)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")

# Test WebSocket endpoint that matches the actual API
@app.websocket("/api/ws/test")
async def websocket_test(websocket: WebSocket):
    """Test WebSocket endpoint that matches the prompt manager's debug endpoint."""
    # Log connection info
    client = websocket.client
    headers = websocket.headers
    logger.info(f"New connection from {client}")
    logger.info(f"Headers: {headers}")
    
    try:
        await websocket.accept()
        logger.info("Connection accepted")
        await websocket.send_text("WebSocket test connection successful")
        
        counter = 0
        while True:
            try:
                # Receive message - this will handle both text and binary
                message = await websocket.receive()
                
                # Check message type
                if "text" in message:
                    data = message["text"]
                    logger.info(f"Received text message: {data}")
                elif "bytes" in message:
                    data = message["bytes"]
                    logger.info(f"Received binary message: {len(data)} bytes")
                else:
                    data = str(message)
                    logger.info(f"Received message: {data}")
                
                counter += 1
                
                # Echo back with some info
                from datetime import datetime
                timestamp = datetime.now().isoformat()
                await websocket.send_json({
                    "received": data,
                    "counter": counter,
                    "timestamp": timestamp,
                    "message": "WebSocket echo test",
                    "headers": dict(websocket.headers)
                })
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                break
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        logger.info("WebSocket connection closed")

# Mock API endpoint for prompts WebSocket
@app.websocket("/api/prompts/ws/{prompt_id}")
async def mock_prompt_websocket(websocket: WebSocket, prompt_id: str):
    """Mock WebSocket endpoint for prompts that mimics the functionality."""
    # Log connection info
    client = websocket.client
    headers = websocket.headers
    logger.info(f"New connection to prompt {prompt_id} from {client}")
    logger.info(f"Headers: {headers}")
    
    try:
        await websocket.accept()
        logger.info(f"Connection to prompt {prompt_id} accepted")
        
        # Send initial data
        await websocket.send_json({
            "action": "initial",
            "content": f"Test content for prompt {prompt_id}",
            "description": "Test prompt",
            "tags": ["test", "debug", "websocket"],
            "is_composite": False,
            "updated_at": None
        })
        
        # Handle messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_json()
                action = data.get("action")
                logger.info(f"Received action: {action}")
                
                # Handle different actions
                if action == "update":
                    content = data.get("content")
                    logger.info(f"Update content: {content[:50]}...")
                    
                    # Send status
                    await websocket.send_json({
                        "action": "update_status",
                        "success": True,
                        "timestamp": None  # Can add timestamp if desired
                    })
                
                elif action == "update_metadata":
                    description = data.get("description")
                    tags = data.get("tags")
                    logger.info(f"Update metadata: {description}, tags: {tags}")
                    
                    # Send status
                    await websocket.send_json({
                        "action": "update_status",
                        "success": True,
                        "timestamp": None
                    })
                
                elif action == "expand":
                    content = data.get("content")
                    logger.info(f"Expand content: {content[:50]}...")
                    
                    # Mock expansion
                    await websocket.send_json({
                        "action": "expanded",
                        "content": content,
                        "expanded": content.replace("[[", "").replace("]]", "") + " (expanded)",
                        "dependencies": [],
                        "warnings": []
                    })
                
                else:
                    logger.warning(f"Unknown action: {action}")
                    await websocket.send_json({
                        "action": "error",
                        "message": f"Unknown action: {action}"
                    })
            
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        logger.info(f"WebSocket connection to prompt {prompt_id} closed")

def main():
    """Run the debug server."""
    parser = argparse.ArgumentParser(description="WebSocket Debug Server")
    parser.add_argument("--host", default="localhost", help="Host to listen on")
    parser.add_argument("--port", type=int, default=8082, help="Port to listen on")
    
    args = parser.parse_args()
    
    logger.info(f"Starting debug server on {args.host}:{args.port}")
    logger.info("Access the test page at http://localhost:8082/")
    
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
