"""
Debug endpoints for WebSocket testing.
"""

from fastapi import APIRouter, WebSocket, Request
from loguru import logger

router = APIRouter(tags=["debug"])

@router.websocket("/api/ws/test")
async def websocket_test(websocket: WebSocket):
    """Test WebSocket endpoint for direct testing at '/api/ws/test'."""
    try:
        await websocket.accept()
        logger.info(f"WebSocket test connection established from {websocket.client}")
        await websocket.send_text("WebSocket test connection successful")
        
        counter = 0
        while True:
            # Wait for a message
            message = await websocket.receive_text()
            counter += 1
            
            # Echo back with timestamp
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            await websocket.send_json({
                "received": message,
                "counter": counter,
                "timestamp": timestamp,
                "message": "WebSocket echo test"
            })
            
            logger.info(f"Echoed message {counter}: {message}")
    except Exception as e:
        logger.error(f"Error in WebSocket test: {str(e)}")
    finally:
        logger.info("WebSocket test connection closed")

@router.websocket("/api/debug/ws/test")
async def test_websocket(websocket: WebSocket):
    """Test WebSocket endpoint for connection diagnosis."""
    logger.info(f"WebSocket test connection from {websocket.client}")
    
    try:
        await websocket.accept()
        await websocket.send_text("WebSocket connection successful")
        
        # Keep connection open for a short time to test
        await websocket.receive_text()
    except Exception as e:
        logger.error(f"Error in test WebSocket: {str(e)}")
    finally:
        logger.info("WebSocket test connection closed")

@router.get("/api/debug/websocket-check")
async def check_websocket_support(request: Request):
    """Check if WebSocket support is properly configured."""
    cors_headers = request.headers.get("sec-fetch-mode", "")
    sec_websocket = request.headers.get("sec-websocket-version", "")
    
    return {
        "server_supports_websocket": True,
        "server_version": "FastAPI/0.95+",
        "client_headers": dict(request.headers),
        "client_appears_to_support_websocket": sec_websocket != "",
        "cors_mode": cors_headers,
        "remote_addr": request.client.host if request.client else "unknown",
        "base_url": str(request.base_url)
    }
