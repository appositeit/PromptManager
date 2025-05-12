"""
Session management service.

This module provides functionality for managing sessions, which was previously
part of the coordinator project. For now it provides stub functionality for
compatibility until the session management can be properly integrated or removed.
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid
from loguru import logger

_session_service_instance = None

class SessionService:
    """Service for managing sessions."""
    
    def __init__(self):
        """Initialize the session service."""
        self.sessions = {}
        self.messages = {}
        logger.info("Initialized SessionService stub")
        
    def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new session (stub implementation).
        
        Args:
            session_data: Data for the new session
            
        Returns:
            The created session data
        """
        session_id = session_data.get('id', str(uuid.uuid4()))
        now = datetime.now(timezone.utc).isoformat()
        
        session = {
            'id': session_id,
            'name': session_data.get('name', 'Untitled Session'),
            'description': session_data.get('description', ''),
            'status': 'initialized',
            'created_at': now,
            'updated_at': now,
            'config': session_data.get('config', {}),
        }
        
        self.sessions[session_id] = session
        self.messages[session_id] = []
        
        logger.info(f"Created new session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a session by ID.
        
        Args:
            session_id: ID of the session to get
            
        Returns:
            The session data, or None if not found
        """
        return self.sessions.get(session_id)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all sessions.
        
        Returns:
            List of sessions
        """
        return list(self.sessions.values())
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Get active sessions (running or initialized).
        
        Returns:
            List of active sessions
        """
        return [s for s in self.sessions.values() 
                if s.get('status') in ('initialized', 'running')]
    
    def add_message(self, session_id: str, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a message to a session.
        
        Args:
            session_id: ID of the session
            message_data: Data for the new message
            
        Returns:
            The created message data, or None if session not found
        """
        if session_id not in self.sessions:
            logger.warning(f"Session not found: {session_id}")
            return None
            
        now = datetime.now(timezone.utc).isoformat()
        message_id = str(uuid.uuid4())
        
        message = {
            'id': message_id,
            'session_id': session_id,
            'timestamp': now,
            **message_data
        }
        
        if session_id not in self.messages:
            self.messages[session_id] = []
            
        self.messages[session_id].append(message)
        
        # Update session
        self.sessions[session_id]['updated_at'] = now
        
        logger.debug(f"Added message to session {session_id}")
        return message
    
    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get messages for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            List of messages
        """
        return self.messages.get(session_id, [])
    
    def update_session(self, session_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a session.
        
        Args:
            session_id: ID of the session to update
            update_data: Data to update
            
        Returns:
            The updated session data, or None if not found
        """
        if session_id not in self.sessions:
            logger.warning(f"Session not found: {session_id}")
            return None
            
        # Update session
        session = self.sessions[session_id]
        for key, value in update_data.items():
            if key not in ('id', 'created_at'):  # Don't allow changing these
                session[key] = value
                
        # Update timestamp
        session['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        logger.debug(f"Updated session: {session_id}")
        return session

def get_session_service() -> SessionService:
    """
    Get the singleton session service instance.
    
    Returns:
        The session service instance
    """
    global _session_service_instance
    if _session_service_instance is None:
        _session_service_instance = SessionService()
    return _session_service_instance
