"""
API routes for session management in the Coordinator system.
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["sessions"])

# Models
class SessionConfig(BaseModel):
    """Configuration for a session."""
    name: str
    description: Optional[str] = None
    directory: Optional[str] = None
    architect: Dict[str, Any]
    workers: List[Dict[str, Any]]
    mcp_servers: Optional[List[str]] = None
    intervention_enabled: Optional[bool] = True


class SessionResponse(BaseModel):
    """Response model for a session."""
    id: str
    name: str
    description: Optional[str] = None
    status: str
    config: SessionConfig
    created_at: str
    updated_at: str


class MessageContent(BaseModel):
    """Content of a message."""
    text: str
    additional_data: Optional[Dict[str, Any]] = None


class Message(BaseModel):
    """Message model."""
    id: str
    session_id: str
    from_agent: str
    to_agent: str
    message_type: str
    content: MessageContent
    timestamp: str


class CreateMessageRequest(BaseModel):
    """Request to create a message."""
    content: MessageContent


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool
    message: str


# Session storage directory
def get_data_dir() -> Path:
    base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = base_dir.parent.parent / "data" / "sessions"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


# Session management functions
def get_all_sessions() -> List[Dict]:
    """Get all sessions."""
    data_dir = get_data_dir()
    sessions = []
    
    for session_file in data_dir.glob("*.json"):
        try:
            with open(session_file, "r") as f:
                session = json.load(f)
                sessions.append(session)
        except Exception as e:
            print(f"Error loading session {session_file}: {e}")
    
    return sessions


def get_session(session_id: str) -> Optional[Dict]:
    """Get a session by ID."""
    data_dir = get_data_dir()
    session_file = data_dir / f"{session_id}.json"
    
    if not session_file.exists():
        return None
    
    try:
        with open(session_file, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading session {session_id}: {e}")
        return None


def create_session(config: SessionConfig) -> Dict:
    """Create a new session and save it to disk."""
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Get data directory
    data_dir = get_data_dir()
    
    # Create session directory
    session_dir_name = config.directory if config.directory else session_id
    session_dir = data_dir.parent / session_dir_name
    session_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (session_dir / "logs").mkdir(exist_ok=True)
    (session_dir / "artifacts").mkdir(exist_ok=True)
    (session_dir / "configs").mkdir(exist_ok=True)
    
    # Create session data
    now = datetime.now().isoformat()
    session: Dict[str, Any] = {
        "id": session_id,
        "name": config.name,
        "description": config.description,
        "status": "initialized",
        "config": config.dict(),
        "created_at": now,
        "updated_at": now,
        "messages": []
    }
    
    # Save session data
    session_file = data_dir / f"{session_id}.json"
    with open(session_file, "w") as f:
        json.dump(session, f, indent=2)
    
    # Save config in the session directory
    config_file = session_dir / "configs" / "session_config.json"
    with open(config_file, "w") as f:
        json.dump(config.dict(), f, indent=2)
    
    return session


def update_session_status(session_id: str, status: str) -> Dict:
    """Update the status of a session."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    session["status"] = status
    session["updated_at"] = datetime.now().isoformat()
    
    # Save session data
    data_dir = get_data_dir()
    session_file = data_dir / f"{session_id}.json"
    with open(session_file, "w") as f:
        json.dump(session, f, indent=2)
    
    return session


def add_message(session_id: str, from_agent: str, to_agent: str, message_type: str, content: Dict) -> Dict:
    """Add a message to a session."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    # Create message
    message_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    message = {
        "id": message_id,
        "session_id": session_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "message_type": message_type,
        "content": content,
        "timestamp": now
    }
    
    # Add to session messages
    if "messages" not in session:
        session["messages"] = []
    
    session["messages"].append(message)
    session["updated_at"] = now
    
    # Save session data
    data_dir = get_data_dir()
    session_file = data_dir / f"{session_id}.json"
    with open(session_file, "w") as f:
        json.dump(session, f, indent=2)
    
    # Save message to log file
    session_dir = data_dir.parent / session_id
    log_file = session_dir / "logs" / "messages.jsonl"
    
    with open(log_file, "a") as f:
        f.write(json.dumps(message) + "\n")
    
    return message


def get_session_messages(session_id: str) -> List[Dict]:
    """Get all messages for a session."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return session.get("messages", [])


def get_worker_data(session_id: str, worker_id: int) -> Dict:
    """Get worker data."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    if "config" not in session or "workers" not in session["config"]:
        raise HTTPException(status_code=404, detail="Worker configuration not found")
    
    if worker_id < 0 or worker_id >= len(session["config"]["workers"]):
        raise HTTPException(status_code=404, detail=f"Worker with ID {worker_id} not found")
    
    worker = session["config"]["workers"][worker_id]
    
    # Add worker ID
    worker["id"] = worker_id
    
    # Add worker messages
    worker_messages = []
    for message in session.get("messages", []):
        if (message["from_agent"] == f"worker{worker_id}" or
            message["to_agent"] == f"worker{worker_id}"):
            worker_messages.append(message)
    
    worker["messages"] = worker_messages
    
    return worker


# API Routes
@router.get("/sessions", response_model=List[Dict])
async def list_sessions():
    """List all sessions."""
    return get_all_sessions()


@router.get("/sessions/active", response_model=List[Dict])
async def get_active_sessions():
    """Get active sessions."""
    sessions = get_all_sessions()
    return [s for s in sessions if s.get("status") in ["initialized", "running"]]


@router.post("/sessions", response_model=Dict)
async def create_new_session(config: SessionConfig):
    """Create a new session."""
    return create_session(config)


@router.get("/sessions/{session_id}", response_model=Dict)
async def get_session_by_id(session_id: str):
    """Get a session by ID."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return session


@router.post("/sessions/{session_id}/start", response_model=Dict)
async def start_session(session_id: str):
    """Start a session."""
    return update_session_status(session_id, "running")


@router.post("/sessions/{session_id}/stop", response_model=Dict)
async def stop_session(session_id: str):
    """Stop a session."""
    return update_session_status(session_id, "stopped")


@router.post("/sessions/{session_id}/pause", response_model=Dict)
async def pause_session(session_id: str):
    """Pause a session."""
    return update_session_status(session_id, "paused")


@router.post("/sessions/{session_id}/resume", response_model=Dict)
async def resume_session(session_id: str):
    """Resume a paused session."""
    return update_session_status(session_id, "running")


@router.get("/sessions/{session_id}/messages", response_model=List[Dict])
async def get_messages(session_id: str):
    """Get all messages for a session."""
    return get_session_messages(session_id)


@router.post("/sessions/{session_id}/messages", response_model=Dict)
async def create_message(session_id: str, message_request: CreateMessageRequest):
    """Create a new message in a session."""
    # For now, messages are always from the user to the architect
    return add_message(
        session_id=session_id,
        from_agent="user",
        to_agent="architect",
        message_type="user_input",
        content=message_request.content.dict()
    )


@router.post("/sessions/{session_id}/messages/worker/{worker_id}", response_model=Dict)
async def create_worker_message(session_id: str, worker_id: int, message_request: CreateMessageRequest):
    """Create a new message to a specific worker."""
    # Direct message to a worker
    return add_message(
        session_id=session_id,
        from_agent="user",
        to_agent=f"worker{worker_id}",
        message_type="user_input",
        content=message_request.content.dict()
    )


@router.get("/sessions/{session_id}/workers/{worker_id}", response_model=Dict)
async def get_worker(session_id: str, worker_id: int):
    """Get worker data."""
    return get_worker_data(session_id, worker_id)
