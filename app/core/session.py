"""Session management for user authentication."""

from datetime import datetime, timedelta
from typing import Dict, Optional
import secrets

# In-memory session store (use Redis in production)
sessions: Dict[str, dict] = {}

SESSION_TIMEOUT = timedelta(hours=24)

def create_session(user_email: str) -> str:
    """Create a new session for user."""
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        "email": user_email,
        "created_at": datetime.utcnow(),
        "last_activity": datetime.utcnow()
    }
    return session_id

def get_session(session_id: str) -> Optional[dict]:
    """Get session data if valid."""
    if session_id not in sessions:
        return None
    
    session = sessions[session_id]
    
    # Check if session expired
    if datetime.utcnow() - session["last_activity"] > SESSION_TIMEOUT:
        del sessions[session_id]
        return None
    
    # Update last activity
    session["last_activity"] = datetime.utcnow()
    return session

def delete_session(session_id: str):
    """Delete a session (logout)."""
    if session_id in sessions:
        del sessions[session_id]

def cleanup_expired_sessions():
    """Remove expired sessions."""
    expired = []
    for session_id, session in sessions.items():
        if datetime.utcnow() - session["last_activity"] > SESSION_TIMEOUT:
            expired.append(session_id)
    
    for session_id in expired:
        del sessions[session_id]
