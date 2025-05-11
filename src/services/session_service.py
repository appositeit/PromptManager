"""
Service for managing sessions in the Coordinator prompt system.

This module provides functionality for creating, retrieving, and managing
sessions, including storing session data and handling mock sessions for
demonstration purposes.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import shutil

class SessionService:
    """Service for managing sessions."""

    def __init__(self, data_dir: str = "data/sessions"):
        """
        Initialize the session service.
        
        Args:
            data_dir: Directory for storing session data
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
        """
        session_path = os.path.join(self.data_dir, f"{session_id}.json")
        if os.path.exists(session_path):
            with open(session_path, "r") as f:
                return json.load(f)
        
        return None
    
    def create_session(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new session.
        
        Args:
            config: Session configuration
            
        Returns:
            Created session data
        """
        # Generate session ID
        session_id = f"session-{uuid.uuid4().hex[:8]}"
        
        # Create session directory
        session_dir = os.path.join(self.data_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Create session data
        session = {
            "id": session_id,
            "name": config.get("name", "Unnamed Session"),
            "description": config.get("description"),
            "status": "initialized",
            "config": config,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Save session data
        session_path = os.path.join(self.data_dir, f"{session_id}.json")
        with open(session_path, "w") as f:
            json.dump(session, f, indent=2)
        
        return session
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a session.
        
        Args:
            session_id: Session ID
            updates: Session updates
            
        Returns:
            Updated session data or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Apply updates
        session.update(updates)
        session["updated_at"] = datetime.utcnow().isoformat()
        
        # Save session data
        session_path = os.path.join(self.data_dir, f"{session_id}.json")
        with open(session_path, "w") as f:
            json.dump(session, f, indent=2)
        
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful, False otherwise
        """
        session_path = os.path.join(self.data_dir, f"{session_id}.json")
        session_dir = os.path.join(self.data_dir, session_id)
        
        # Delete session file
        if os.path.exists(session_path):
            os.remove(session_path)
        
        # Delete session directory
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
        
        return True
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all sessions.
        
        Returns:
            List of session data
        """
        sessions = []
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.data_dir, filename)
                with open(file_path, "r") as f:
                    session = json.load(f)
                    sessions.append(session)
        
        # Sort by creation time (newest first)
        sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return sessions
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Get active sessions (running or initialized).
        
        Returns:
            List of active session data
        """
        sessions = self.list_sessions()
        active_sessions = [
            session for session in sessions
            if session.get("status") in ["running", "initialized"]
        ]
        
        return active_sessions
    
    def start_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Start a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Updated session data or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Update status
        session["status"] = "running"
        session["updated_at"] = datetime.utcnow().isoformat()
        
        # Save session data
        session_path = os.path.join(self.data_dir, f"{session_id}.json")
        with open(session_path, "w") as f:
            json.dump(session, f, indent=2)
        
        return session
    
    def stop_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Stop a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Updated session data or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Update status
        session["status"] = "paused"
        session["updated_at"] = datetime.utcnow().isoformat()
        
        # Save session data
        session_path = os.path.join(self.data_dir, f"{session_id}.json")
        with open(session_path, "w") as f:
            json.dump(session, f, indent=2)
        
        return session
    
    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get messages for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of message data
        """
        # In a real implementation, this would retrieve messages from a database
        # For now, return some mock messages for demonstration
        
        session = self.get_session(session_id)
        if not session:
            return []
        
        messages = []
        
        # Add system welcome message
        messages.append({
            "id": f"{session_id}-msg-1",
            "from_agent": "system",
            "to_agent": "user",
            "message_type": "welcome",
            "content": {
                "text": f"Welcome to session \"{session['name']}\". I'm the Coordinator system. How can I help you today?"
            },
            "timestamp": session["created_at"]
        })
        
        # Add architect welcome message
        messages.append({
            "id": f"{session_id}-msg-2",
            "from_agent": "architect",
            "to_agent": "user",
            "message_type": "ai_response",
            "content": {
                "text": f"Hello! I'm the Architect AI using the {session['config'].get('architect', {}).get('model', 'Claude')} model. I'm here to help coordinate this session and break down tasks into manageable steps. What would you like to work on today?"
            },
            "timestamp": session["created_at"]
        })
        
        return messages
    
    def add_message(self, session_id: str, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a message to a session.
        
        Args:
            session_id: Session ID
            message: Message data
            
        Returns:
            Added message data or None if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        # In a real implementation, this would store the message in a database
        # For now, just return the message with an ID
        
        message_id = f"{session_id}-msg-{uuid.uuid4().hex[:8]}"
        message["id"] = message_id
        message["timestamp"] = datetime.utcnow().isoformat()
        
        return message

# Create a singleton instance
_session_service = None

def get_session_service() -> SessionService:
    """
    Get the singleton session service instance.
    
    Returns:
        Session service instance
    """
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service
