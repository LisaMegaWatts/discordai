import asyncio

# Utility to check if event loop is running and not closed
def is_event_loop_running():
    try:
        loop = asyncio.get_running_loop()
        return not loop.is_closed()
    except RuntimeError:
        return False
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
    Implements persistent memory architecture: session state and message history
    are stored in Redis for speed and in the database for durability.
    Robust recovery logic ensures context is restored after bot restarts or Redis flushes.
    """
    def __init__(self, db_session_factory, redis_client=None):
        self.db_session_factory = db_session_factory
        self.max_context_messages = 20
        self.session_timeout_minutes = 30
        self.redis_client = redis_client

    async def recover_redis_state(self):
        """
        On bot restart or Redis flush, rehydrate Redis with active sessions and recent message history from DB.
        """
        try:
            from crud import get_all_active_sessions, get_conversation_history
            if not self.redis_client:
                return
            active_sessions = await get_all_active_sessions()
            for session in active_sessions:
                redis_key = f"session:active:{session.user_id}"
                await self.redis_client.set(redis_key, session.id, expire_seconds=self.session_timeout_minutes*60)
                # Optionally cache last N messages for each session
                messages = await get_conversation_history(session.id, limit=self.max_context_messages)
                msg_key = f"session:messages:{session.id}"
                msg_data = [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.message,
                        "intent": msg.intent,
                        "confidence": msg.confidence,
                        "created_at": msg.created_at.isoformat() if msg.created_at else None
                    }
                    for msg in messages
                ]
                await self.redis_client.set(msg_key, str(msg_data), expire_seconds=self.session_timeout_minutes*60)
            logger.info("Redis state recovered from DB.")
        except Exception as e:
            logger.error(f"Error recovering Redis state: {e}", exc_info=True)

    async def get_or_create_session(self, user_id: str):
        """
        Get active session for user or create a new one if expired/missing.
        Uses Redis for atomic session validity and fast lookup.
        Always persists session state to DB for durability.
        Recovers from DB if Redis is unavailable or flushed.
        """
        from discord_bot import is_shutting_down, is_event_loop_running
        if is_shutting_down() or not is_event_loop_running():
            logger.warning(f"Shutdown or closed event loop. Skipping get_or_create_session for user {user_id}.")
            return None
        redis_key = f"session:active:{user_id}"
        session_id = None
        session_obj = None
        # Try Redis first
        if self.redis_client:
            session_id = await self.redis_client.get(redis_key)
            if session_id:
                session_obj = await get_conversation_session(session_id)
                if session_obj and getattr(session_obj, "status", None) == "active":
                    logger.info(f"Retrieved active session {session_id} for user {user_id} (Redis)")
                    return session_obj
                else:
                    await self.redis_client.delete(redis_key)
        # Fallback to DB
        try:
            active_session = await get_active_session_for_user(user_id)
        except Exception as e:
            logger.error(f"Error retrieving active session for user {user_id}: {e}", exc_info=True)
            raise
        if active_session:
            try:
                if not await self.should_create_new_session(user_id):
                    logger.info(f"Retrieved active session {active_session.id} for user {user_id}")
                    if self.redis_client:
                        await self.redis_client.set(redis_key, active_session.id, expire_seconds=self.session_timeout_minutes*60)
                    return active_session
                else:
                    logger.info(f"Session {active_session.id} expired for user {user_id}")
                    await end_conversation_session(active_session.id)
                    if self.redis_client:
                        await self.redis_client.delete(redis_key)
            except Exception as e:
                logger.error(f"Error ending expired session {active_session.id} for user {user_id}: {e}", exc_info=True)
                raise
        # DB fallback: atomic session creation with retry to avoid duplicates
        from sqlalchemy.exc import IntegrityError
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                new_session = await create_conversation_session(user_id)
                logger.info(f"Created new session {new_session.id} for user {user_id}")
                if self.redis_client:
                    await self.redis_client.set(redis_key, new_session.id, expire_seconds=self.session_timeout_minutes*60)
                return new_session
            except IntegrityError:
                logger.warning(f"Session race detected for user {user_id}, retrying ({attempt+1}/{max_attempts})")
                active_session = await get_active_session_for_user(user_id)
                if active_session:
                    logger.info(f"Fetched concurrent active session {active_session.id} for user {user_id}")
                    if self.redis_client:
                        await self.redis_client.set(redis_key, active_session.id, expire_seconds=self.session_timeout_minutes*60)
                    return active_session
            except Exception as e:
                logger.error(f"Error creating new session for user {user_id}: {e}", exc_info=True)
                if attempt == max_attempts - 1:
                    raise
        raise RuntimeError("Failed to create or fetch session atomically")

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
        Store a message in both Redis (for speed) and DB (for durability).
        Robustly recovers if Redis is unavailable or flushed.
        """
        from discord_bot import is_shutting_down
        if is_shutting_down():
            logger.warning(f"Shutdown in progress. Skipping add_message for user {user_id}.")
            return
        if role not in ["user", "assistant"]:
            raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'")
        redis_key = f"session:active:{user_id}"
        msg_key = f"session:messages:{session_id}"
        # Check Redis session validity
        redis_valid = True
        if self.redis_client:
            session_id_redis = await self.redis_client.get(redis_key)
            if session_id_redis != session_id:
                logger.warning(
                    f"Session {session_id} not valid for user {user_id} (Redis check failed). Skipping operation."
                )
                redis_valid = False
        # Always persist to DB
        try:
            session_obj = await get_conversation_session(session_id)
        except Exception as e:
            logger.error(f"Error retrieving session {session_id} for user {user_id}: {e}", exc_info=True)
            return
        if not session_obj or getattr(session_obj, "status", None) != "active":
            logger.warning(
                f"Attempted to add message to closed or invalid session {session_id} (user {user_id}). Skipping operation."
            )
            if self.redis_client:
                await self.redis_client.delete(redis_key)
            return
        from sqlalchemy.exc import IntegrityError
        try:
            session_obj = await get_conversation_session(session_id)
            if not session_obj or getattr(session_obj, "status", None) != "active":
                logger.warning(
                    f"Session {session_id} became inactive before message add (user {user_id}). Skipping operation."
                )
                return
            await create_conversation_message(
                session_id=session_id,
                user_id=user_id,
                message=message,
                role=role,
                intent=intent,
                confidence=confidence
            )
        except IntegrityError:
            logger.error(f"Duplicate message detected for session {session_id}, user {user_id}. Skipping.")
            return
        except Exception as e:
            logger.error(f"Error creating conversation message for session {session_id}, user {user_id}: {e}", exc_info=True)
            return
        # Update Redis message cache (if enabled and session valid)
        if self.redis_client and redis_valid:
            try:
                # Get current cached messages
                cached = await self.redis_client.get(msg_key)
                import ast
                if cached:
                    cached_msgs = ast.literal_eval(cached)
                else:
                    cached_msgs = []
                # Append new message
                cached_msgs.append({
                    "id": None,  # Will be set by DB, but cache for context
                    "role": role,
                    "content": message,
                    "intent": intent,
                    "confidence": confidence,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                # Trim to max_context_messages
                if len(cached_msgs) > self.max_context_messages:
                    cached_msgs = cached_msgs[-self.max_context_messages:]
                await self.redis_client.set(msg_key, str(cached_msgs), expire_seconds=self.session_timeout_minutes*60)
            except Exception as e:
                logger.error(f"Error updating Redis message cache for session {session_id}: {e}", exc_info=True)
        try:
            await update_session_activity(session_id, message_count_increment=1)
            if self.redis_client:
                await self.redis_client.set(redis_key, session_id, expire_seconds=self.session_timeout_minutes*60)
        except Exception as e:
            logger.error(f"Error updating session activity for session {session_id}: {e}", exc_info=True)
            return
        logger.debug(
            f"Added {role} message to session {session_id} "
            f"(intent: {intent}, confidence: {confidence})"
        )
        """
        Alias for get_conversation_context for backward compatibility.

        Args:
            session_id: The conversation session ID
            limit: Optional maximum number of messages to retrieve

        Returns:
            List[Dict]: List of message dictionaries
        """
        # Fix: Ensure 'limit' is defined or passed as a parameter
        # This method should accept 'limit' as a parameter
        # If this is a method, add 'limit' to its signature
        # If not, remove this block or refactor as needed
        # Since this is not a method, this block is unreachable and can be removed.
        # If you need an alias, define a method:
        # async def get_conversation_context_with_limit(self, session_id: str, limit: Optional[int] = None):
        #     return await self.get_conversation_context(session_id, max_messages=limit)
        pass
    
    async def get_conversation_context(
        self,
        session_id: str,
        max_messages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent messages from conversation history.
        Each async task/coroutine creates its own AsyncSession.
        """
        if max_messages is None:
            max_messages = self.max_context_messages
        messages = await get_conversation_history(session_id, limit=max_messages)
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
    
    async def should_create_new_session(self, user_id: str) -> bool:
        """
        Check if the active session for a user is expired.

        Args:
            db: The AsyncSession instance
            user_id: The Discord user ID

        Returns:
            bool: True if a new session should be created, False otherwise
        """
        try:
            import asyncio
            logger.info(
                f"[START] should_create_new_session: user_id={user_id}, task={asyncio.current_task()}"
            )
            # Get active session
            active_session = await get_active_session_for_user(user_id)

            if not active_session:
                # No active session, should create new one
                logger.info(
                    f"[END] should_create_new_session: user_id={user_id}, "
                    f"task={asyncio.current_task()}, result=True"
                )
                return True

            # Check if session is expired
            if not active_session.last_active:
                # No last_active timestamp, consider expired
                logger.warning(f"Session {active_session.id} has no last_active timestamp")
                logger.info(
                    f"[END] should_create_new_session: user_id={user_id}, "
                    f"task={asyncio.current_task()}, result=True"
                )
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

            logger.info(
                f"[END] should_create_new_session: user_id={user_id}, "
                f"task={asyncio.current_task()}, result={is_expired}"
            )
            return is_expired

        except Exception as e:
            logger.error(f"Error checking session expiry for user {user_id}: {e}", exc_info=True)
            # On error, default to creating new session
            return True
    
    async def end_session(self, session_id: str, user_id: str = None) -> None:
        """
        End a conversation session and synchronize expiry/closure with Redis.
        Args:
            session_id: The conversation session ID
            user_id: The Discord user ID (optional, for Redis cleanup)
        """
        try:
            import asyncio
            logger.info(
                f"[START] end_session: session={session_id}, task={asyncio.current_task()}"
            )
            await end_conversation_session(session_id)
            logger.info(f"Ended session {session_id}")
            logger.info(
                f"[END] end_session: session={session_id}, task={asyncio.current_task()}"
            )
            # Remove session from Redis
            if self.redis_client and user_id:
                redis_key = f"session:active:{user_id}"
                await self.redis_client.delete(redis_key)
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
            session = await get_conversation_session(session_id)

            if not session:
                logger.warning(f"Session {session_id} not found (NoneType). Skipping summary operations.")
                return {
                    "total_messages": 0,
                    "last_messages": [],
                    "session_duration_minutes": 0,
                    "user_message_count": 0,
                    "assistant_message_count": 0
                }

            # Defensive: check for required session attributes
            started_at = getattr(session, "started_at", None)
            if started_at is None:
                logger.warning(f"Session {session_id} missing 'started_at'. Skipping duration calculation.")
                duration_minutes = 0
            else:
                now = datetime.now(timezone.utc)
                if started_at.tzinfo is None:
                    started_at = started_at.replace(tzinfo=timezone.utc)
                duration = now - started_at
                duration_minutes = duration.total_seconds() / 60

            # Get all messages for counting
            try:
                all_messages = await self.get_conversation_context(session_id, max_messages=1000)
            except Exception as e:
                logger.warning(f"Could not retrieve messages for session {session_id}: {e}")
                all_messages = []

            # Get last 5 messages
            last_messages = all_messages[-5:] if len(all_messages) > 5 else all_messages

            # Count message types
            user_count = sum(1 for msg in all_messages if msg.get("role") == "user")
            assistant_count = sum(1 for msg in all_messages if msg.get("role") == "assistant")

            return {
                "total_messages": len(all_messages),
                "last_messages": last_messages,
                "session_duration_minutes": round(duration_minutes, 2) if started_at else 0,
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
        from db import AsyncSessionLocal
        from sqlalchemy.future import select
        from models import ConversationSessions
        async with AsyncSessionLocal() as db:
            try:
                import asyncio
                logger.info(
                    f"[START] prune_old_sessions: session_id={id(db)}, "
                    f"task={asyncio.current_task()}"
                )
                # Calculate cutoff time
                now = datetime.now(timezone.utc)
                cutoff_time = now - timedelta(minutes=self.session_timeout_minutes)

                # Find expired active sessions
                result = await db.execute(
                    select(ConversationSessions)
                    .where(ConversationSessions.status == "active")
                    .where(ConversationSessions.last_active < cutoff_time)
                )
                expired_sessions = result.scalars().all()

                # End each expired session
                pruned_count = 0
                for session in expired_sessions:
                    try:
                        await end_conversation_session(session.id)
                        pruned_count += 1
                        logger.info(f"Pruned expired session {session.id}")
                    except Exception as e:
                        logger.error(f"Error pruning session {session.id}: {e}")

                if pruned_count > 0:
                    logger.info(f"Pruned {pruned_count} expired sessions")

                logger.info(
                    f"[END] prune_old_sessions: session_id={id(db)}, "
                    f"task={asyncio.current_task()}, pruned_count={pruned_count}"
                )
                return pruned_count

            except Exception as e:
                logger.error(f"Error during session pruning: {e}", exc_info=True)
                return 0