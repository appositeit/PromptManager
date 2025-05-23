"""
Session management routes for the web interface.

This module provides FastAPI routes for the web interface to manage sessions,
including rendering session pages and connecting to the Coordinator API.
"""

from fastapi import APIRouter, HTTPException, Request, Depends, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from src.services.session import get_session_service
from src.services.prompt_service import PromptService

# Initialize templates
templates = Jinja2Templates(directory="src/templates")

# Create router
router = APIRouter()

# Constants
API_BASE_URL = "http://127.0.0.1:8081/api"  # Updated to use the local API


# Helper functions
async def get_session(session_id: str) -> Dict[str, Any]:
    """
    Get session data from the API.
    
    Args:
        session_id: Session ID
        
    Returns:
        Session data
    
    Raises:
        HTTPException: If session not found or API error
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/sessions/{session_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail="Session not found")
            else:
                raise HTTPException(status_code=e.response.status_code, 
                                   detail=f"API error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


async def get_active_sessions() -> Dict[str, Any]:
    """
    Get active sessions from the API.
    
    Returns:
        List of active sessions
    
    Raises:
        HTTPException: If API error
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/sessions/active")
            response.raise_for_status()
            return response.json()
        except Exception:
            # Just return empty list on error
            return []


# API Proxy routes - These proxy requests to the main API
@router.post("/api/sessions", status_code=201)
async def create_session(request: Request):
    """
    Proxy API endpoint to create a session.
    
    This forwards the request to the main API.
    """
    try:
        # Get request body
        body = await request.json()
        
        # Use the session service to create a session
        session_service = get_session_service()
        
        # Create the session
        session = session_service.create_session(body)
        
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")


@router.post("/api/sessions/{session_id}/start")
async def start_session(session_id: str):
    """
    Proxy API endpoint to start a session.
    
    This forwards the request to the main API.
    """
    try:
        # Use the session service to update session status
        session_service = get_session_service()
        
        # Update session status
        session = session_service.update_session(session_id, {"status": "running"})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
            
        return session
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting session: {str(e)}")


@router.post("/api/sessions/{session_id}/stop")
async def stop_session(session_id: str):
    """
    Proxy API endpoint to stop a session.
    
    This forwards the request to the main API.
    """
    try:
        # Use the session service to update session status
        session_service = get_session_service()
        
        # Update session status
        session = session_service.update_session(session_id, {"status": "completed"})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
            
        return session
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping session: {str(e)}")


@router.post("/api/sessions/{session_id}/messages")
async def send_message(session_id: str, request: Request):
    """
    Proxy API endpoint to send a message in a session.
    
    This forwards the request to the main API.
    """
    try:
        # Get request body
        body = await request.json()
        
        # Use the session service to add the message
        session_service = get_session_service()
        
        # Add the message
        message = session_service.add_message(session_id, body)
        if not message:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # For demo: add an architect response if user sent a message
        if body.get("from_agent") == "user" and body.get("to_agent") == "architect":
            # Get session to add realistic architect response
            session = session_service.get_session(session_id)
            
            # Create a mock response based on the user message
            user_text = body.get("content", {}).get("text", "")
            response_text = generate_response(user_text, session)
            
            architect_message = {
                "from_agent": "architect",
                "to_agent": "user",
                "message_type": "ai_response",
                "content": {
                    "text": response_text
                }
            }
            
            # Add the architect message with a slight delay (in real system this would happen asynchronously)
            import asyncio
            await asyncio.sleep(1)
            architect_response = session_service.add_message(session_id, architect_message)
            
            # Return both the user message and the AI response
            return {
                "message": message,
                "response": architect_response
            }
        
        return {"message": message}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")

# Helper function to generate responses for demo purposes
def generate_response(message: str, session: dict) -> str:
    """Generate a mock response based on the user's message."""
    if not message:
        return "I'm here to help. What would you like to work on?"
    
    # Check for common patterns
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["hello", "hi", "hey"]):
        return f"Hello! I'm the Architect AI for the \"{session['name']}\" session. How can I assist you today?"
    
    if "help" in message_lower:
        return "I'm here to help break down tasks and coordinate with specialized workers. What specific problem would you like assistance with?"
    
    if any(word in message_lower for word in ["thank", "thanks"]):
        return "You're welcome! Let me know if you need any further assistance."
    
    if any(word in message_lower for word in ["code", "programming", "software", "develop"]):
        workers = session.get("config", {}).get("workers", [])
        code_workers = [w for w in workers if "code" in "".join(w.get("capabilities", []))]
        
        if code_workers:
            return f"I can help with your coding task. I'll collaborate with {code_workers[0]['name']} who specializes in programming. Could you provide more details about what you're trying to build?"
        else:
            return "I can help with your coding task. Would you like me to break it down into manageable steps or do you need assistance with a specific part?"
    
    # Default response for other messages
    return f"I understand you're interested in: \"{message}\". Let me think about how to approach this...\n\nI can break this down into smaller tasks and coordinate the execution. Would you like me to create a step-by-step plan?"

@router.get("/api/sessions", status_code=200)
async def list_sessions():
    """List all sessions."""
    try:
        # Use the session service to list sessions
        session_service = get_session_service()
        
        # List all sessions
        sessions = session_service.list_sessions()
        
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")


@router.get("/api/sessions/active", status_code=200)
async def list_active_sessions():
    """List active sessions (running or initialized)."""
    try:
        # Use the session service to list active sessions
        session_service = get_session_service()
        
        # List active sessions
        active_sessions = session_service.get_active_sessions()
        
        return active_sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing active sessions: {str(e)}")


@router.get("/api/sessions/{session_id}/messages", status_code=200)
async def get_session_messages(session_id: str):
    """Get messages for a session."""
    try:
        # Use the session service to get session messages
        session_service = get_session_service()
        
        # Get session messages
        messages = session_service.get_session_messages(session_id)
        
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session messages: {str(e)}")


# Web UI Routes
@router.get("/sessions/{session_id}", response_class=HTMLResponse)
async def get_session_page_ui(request: Request, session_id: str):
    """
    Render the session page.
    
    Args:
        request: FastAPI request
        session_id: Session ID
    """
    try:
        # Get session data
        session_data = await get_session(session_id)
        
        # Add CSS classes for status
        status_classes = {
            "initialized": "secondary",
            "running": "success",
            "paused": "warning",
            "completed": "info",
            "error": "danger"
        }
        
        session_data["status_class"] = status_classes.get(
            session_data["status"], "secondary")
        
        # Format timestamps
        if "created_at" in session_data:
            created_at = datetime.fromisoformat(session_data["created_at"].replace("Z", "+00:00"))
            session_data["created_at"] = created_at.strftime("%Y-%m-%d %H:%M:%S")
            
        if "updated_at" in session_data:
            updated_at = datetime.fromisoformat(session_data["updated_at"].replace("Z", "+00:00"))
            session_data["updated_at"] = updated_at.strftime("%Y-%m-%d %H:%M:%S")
        
        # Render template
        return templates.TemplateResponse(
            "session.html",
            {
                "request": request,
                "session": session_data
            }
        )
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering session page: {str(e)}")


@router.get("/", response_class=HTMLResponse)
async def get_home_page(request: Request):
    """Redirect to the prompt management page."""
    return RedirectResponse(url="/manage/prompts")
