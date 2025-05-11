"""
Debug endpoints for WebSocket testing.
"""

from fastapi import APIRouter, WebSocket, Request
from loguru import logger

router = APIRouter(prefix="/api/debug", tags=["debug"])

@router.websocket("/ws/test")
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

@router.get("/websocket-check")
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
