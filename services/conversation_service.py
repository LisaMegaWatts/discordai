"""
Conversation Context Manager Service

This service manages conversation sessions, tracks message history, and prepares
context for Claude API calls. It handles session lifecycle, context windowing,
and message formatting for the conversational bot.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

# Import CRUD functions
from crud import (
    create_conversation_session,
    get_active_session_for_user,
    update_session_activity,
    end_conversation_session,
    create_conversation_message,
    get_conversation_history,
    get_conversation_session
)

logger = logging.getLogger(__name__)


class ConversationContextManager:
    """
    Manages conversation sessions and context for Claude interactions.
    
    This class handles:
    - Creating and retrieving conversation sessions
    - Storing messages in conversation history
    - Retrieving conversation context for Claude
    - Managing session timeouts
    - Formatting messages for Claude API
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize the conversation context manager.
        
        Args:
            db_session: AsyncSession instance for database operations
        """
        self.db = db_session
        self.max_context_messages = 20  # From architecture
        self.session_timeout_minutes = 30
    
    async def get_or_create_session(self, user_id: str):
        """
        Get active session for user or create a new one if expired/missing.
        
        Args:
            user_id: The Discord user ID
        
        Returns:
            ConversationSession: The session object
        
        Example:
            >>> session = await manager.get_or_create_session("123456")
            >>> print(session.id)
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        """
        try:
            # Check for active session
            active_session = await get_active_session_for_user(self.db, user_id)
            
            if active_session:
                # Check if session is expired
                if not await self.should_create_new_session(user_id):
                    logger.info(f"Retrieved active session {active_session.id} for user {user_id}")
                    return active_session
                else:
                    # Session expired, end it
                    logger.info(f"Session {active_session.id} expired for user {user_id}")
                    await end_conversation_session(self.db, active_session.id)
            
            # Create new session
            new_session = await create_conversation_session(self.db, user_id)
            logger.info(f"Created new session {new_session.id} for user {user_id}")
            return new_session
            
        except Exception as e:
            logger.error(f"Error getting/creating session for user {user_id}: {e}", exc_info=True)
            raise
    
    async def add_message(
        self,
        session_id: str,
        user_id: str,
        message: str,
        role: str,
        intent: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> None:
        """
        Store a message in conversation history and update session activity.
        
        Args:
            session_id: The conversation session ID
            user_id: The Discord user ID
            message: The message content
            role: Either "user" or "assistant"
            intent: Optional detected intent (for user messages)
            confidence: Optional confidence score (for user messages)
        
        Raises:
            ValueError: If role is not "user" or "assistant"
        
        Example:
            >>> await manager.add_message(
            ...     session_id="abc123",
            ...     user_id="123456",
            ...     message="Hello bot!",
            ...     role="user",
            ...     intent="general_conversation",
            ...     confidence=0.92
            ... )
        """
        if role not in ["user", "assistant"]:
            raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'")
        
        try:
            # Store the message
            await create_conversation_message(
                self.db,
                session_id=session_id,
                user_id=user_id,
                message=message,
                role=role,
                intent=intent,
                confidence=confidence
            )
            
            # Update session activity
            await update_session_activity(self.db, session_id, message_count_increment=1)
            
            logger.debug(
                f"Added {role} message to session {session_id} "
                f"(intent: {intent}, confidence: {confidence})"
            )
            
        except Exception as e:
            logger.error(
                f"Error adding message to session {session_id}: {e}",
                exc_info=True
            )
            raise
    
    async def get_context(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Alias for get_conversation_context for backward compatibility.
        
        Args:
            session_id: The conversation session ID
            limit: Optional maximum number of messages to retrieve
        
        Returns:
            List[Dict]: List of message dictionaries
        """
        return await self.get_conversation_context(session_id, max_messages=limit)
    
    async def get_conversation_context(
        self,
        session_id: str,
        max_messages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent messages from conversation history.
        
        Retrieves messages in chronological order (oldest to newest) with
        message content, role, and metadata. Limits to max_messages or
        default max_context_messages.
        
        Args:
            session_id: The conversation session ID
            max_messages: Optional maximum number of messages to retrieve
                         (defaults to self.max_context_messages)
        
        Returns:
            List[Dict]: List of message dictionaries with keys:
                - id: Message ID
                - role: "user" or "assistant"
                - content: Message text
                - intent: Detected intent (may be None)
                - confidence: Confidence score (may be None)
                - created_at: Timestamp
        
        Example:
            >>> context = await manager.get_conversation_context("abc123", max_messages=10)
            >>> print(context)
            [
                {
                    "id": 1,
                    "role": "user",
                    "content": "Hello!",
                    "intent": "general_conversation",
                    "confidence": 0.95,
                    "created_at": "2024-01-01T12:00:00Z"
                },
                ...
            ]
        """
        if max_messages is None:
            max_messages = self.max_context_messages
        
        try:
            # Get conversation history from database
            messages = await get_conversation_history(
                self.db,
                session_id=session_id,
                limit=max_messages
            )
            
            # Convert to dict format with all relevant fields
            context = []
            for msg in messages:
                context.append({
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.message,
                    "intent": msg.intent,
                    "confidence": msg.confidence,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                })
            
            logger.debug(f"Retrieved {len(context)} messages for session {session_id}")
            return context
            
        except Exception as e:
            logger.error(
                f"Error retrieving context for session {session_id}: {e}",
                exc_info=True
            )
            # Return empty context on error rather than failing
            return []
    
    async def should_create_new_session(self, user_id: str) -> bool:
        """
        Check if the active session for a user is expired.
        
        A session is considered expired if last_active timestamp is older
        than session_timeout_minutes (default: 30 minutes).
        
        Args:
            user_id: The Discord user ID
        
        Returns:
            bool: True if a new session should be created, False otherwise
        
        Example:
            >>> should_create = await manager.should_create_new_session("123456")
            >>> print(should_create)
            False  # Active session exists and not expired
        """
        try:
            # Get active session
            active_session = await get_active_session_for_user(self.db, user_id)
            
            if not active_session:
                # No active session, should create new one
                return True
            
            # Check if session is expired
            if not active_session.last_active:
                # No last_active timestamp, consider expired
                logger.warning(f"Session {active_session.id} has no last_active timestamp")
                return True
            
            # Calculate time since last activity
            now = datetime.now(timezone.utc)
            
            # Ensure last_active is timezone-aware
            last_active = active_session.last_active
            if last_active.tzinfo is None:
                last_active = last_active.replace(tzinfo=timezone.utc)
            
            time_since_last = now - last_active
            timeout_delta = timedelta(minutes=self.session_timeout_minutes)
            
            is_expired = time_since_last > timeout_delta
            
            if is_expired:
                logger.info(
                    f"Session {active_session.id} expired "
                    f"(inactive for {time_since_last.total_seconds() / 60:.1f} minutes)"
                )
            
            return is_expired
            
        except Exception as e:
            logger.error(f"Error checking session expiry for user {user_id}: {e}", exc_info=True)
            # On error, default to creating new session
            return True
    
    async def end_session(self, session_id: str) -> None:
        """
        End a conversation session.
        
        Marks the session status as "ended" in the database.
        
        Args:
            session_id: The conversation session ID
        
        Example:
            >>> await manager.end_session("abc123")
        """
        try:
            await end_conversation_session(self.db, session_id)
            logger.info(f"Ended session {session_id}")
            
        except Exception as e:
            logger.error(f"Error ending session {session_id}: {e}", exc_info=True)
            raise
    
    def format_messages_for_claude(self, messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Convert database message objects to Claude API format.
        
        Transforms messages into the format expected by Claude's Messages API:
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        
        Only includes role and content fields, maintains chronological order.
        
        Args:
            messages: List of message dicts from get_conversation_context()
        
        Returns:
            List[Dict[str, str]]: Messages formatted for Claude API
        
        Example:
            >>> context = await manager.get_conversation_context("abc123")
            >>> claude_messages = manager.format_messages_for_claude(context)
            >>> print(claude_messages)
            [
                {"role": "user", "content": "Hello!"},
                {"role": "assistant", "content": "Hi there! How can I help?"},
                {"role": "user", "content": "Tell me a joke"}
            ]
        """
        claude_messages = []
        
        for msg in messages:
            claude_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return claude_messages
    
    async def get_context_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get a summary of the conversation session.
        
        Returns statistics and recent messages for the session.
        
        Args:
            session_id: The conversation session ID
        
        Returns:
            Dict containing:
                - total_messages: Total message count in session
                - last_messages: Last 5 messages
                - session_duration_minutes: Time since session start
                - user_message_count: Number of user messages
                - assistant_message_count: Number of assistant messages
        
        Example:
            >>> summary = await manager.get_context_summary("abc123")
            >>> print(summary)
            {
                "total_messages": 10,
                "last_messages": [...],
                "session_duration_minutes": 15.5,
                "user_message_count": 5,
                "assistant_message_count": 5
            }
        """
        try:
            # Get session info
            session = await get_conversation_session(self.db, session_id)
            
            if not session:
                logger.warning(f"Session {session_id} not found")
                return {
                    "total_messages": 0,
                    "last_messages": [],
                    "session_duration_minutes": 0,
                    "user_message_count": 0,
                    "assistant_message_count": 0
                }
            
            # Get all messages for counting
            all_messages = await get_conversation_context(session_id, max_messages=1000)
            
            # Get last 5 messages
            last_messages = all_messages[-5:] if len(all_messages) > 5 else all_messages
            
            # Count message types
            user_count = sum(1 for msg in all_messages if msg["role"] == "user")
            assistant_count = sum(1 for msg in all_messages if msg["role"] == "assistant")
            
            # Calculate session duration
            now = datetime.now(timezone.utc)
            started_at = session.started_at
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)
            
            duration = now - started_at
            duration_minutes = duration.total_seconds() / 60
            
            return {
                "total_messages": len(all_messages),
                "last_messages": last_messages,
                "session_duration_minutes": round(duration_minutes, 2),
                "user_message_count": user_count,
                "assistant_message_count": assistant_count
            }
            
        except Exception as e:
            logger.error(f"Error getting context summary for session {session_id}: {e}", exc_info=True)
            return {
                "total_messages": 0,
                "last_messages": [],
                "session_duration_minutes": 0,
                "user_message_count": 0,
                "assistant_message_count": 0
            }
    
    async def prune_old_sessions(self) -> int:
        """
        Mark sessions as "expired" if inactive for > 30 minutes.
        
        Can be called periodically for cleanup. Finds all active sessions
        with last_active older than session_timeout_minutes and ends them.
        
        Returns:
            int: Number of sessions pruned
        
        Example:
            >>> pruned = await manager.prune_old_sessions()
            >>> print(f"Pruned {pruned} old sessions")
        """
        try:
            from sqlalchemy.future import select
            from models import ConversationSessions
            
            # Calculate cutoff time
            now = datetime.now(timezone.utc)
            cutoff_time = now - timedelta(minutes=self.session_timeout_minutes)
            
            # Find expired active sessions
            result = await self.db.execute(
                select(ConversationSessions)
                .where(ConversationSessions.status == "active")
                .where(ConversationSessions.last_active < cutoff_time)
            )
            expired_sessions = result.scalars().all()
            
            # End each expired session
            pruned_count = 0
            for session in expired_sessions:
                try:
                    await end_conversation_session(self.db, session.id)
                    pruned_count += 1
                    logger.info(f"Pruned expired session {session.id}")
                except Exception as e:
                    logger.error(f"Error pruning session {session.id}: {e}")
            
            if pruned_count > 0:
                logger.info(f"Pruned {pruned_count} expired sessions")
            
            return pruned_count
            
        except Exception as e:
            logger.error(f"Error during session pruning: {e}", exc_info=True)
            return 0