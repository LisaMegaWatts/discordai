"""
Performance optimization utilities for Discord bot.

Provides helper functions for batching operations, preloading data,
and optimizing message processing.
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PerformanceUtils:
    """Collection of performance optimization utilities."""
    
    # Maximum message length to prevent excessive API costs
    MAX_MESSAGE_LENGTH = 2000
    
    # Maximum context messages to retrieve
    MAX_CONTEXT_MESSAGES = 10
    
    @staticmethod
    async def batch_db_operations(
        operations: List[Callable],
        batch_size: int = 10
    ) -> List[Any]:
        """
        Batch multiple database operations for efficient execution.
        
        Args:
            operations: List of async callable operations to execute
            batch_size: Number of operations to run concurrently
            
        Returns:
            List of results from all operations
        """
        results = []
        
        for i in range(0, len(operations), batch_size):
            batch = operations[i:i + batch_size]
            try:
                batch_results = await asyncio.gather(*[op() for op in batch])
                results.extend(batch_results)
            except Exception as e:
                logger.error(f"Error in batch DB operations: {e}")
                # Continue with remaining batches
                results.extend([None] * len(batch))
        
        return results
    
    @staticmethod
    async def preload_user_data(
        db_session,
        user_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Preload commonly accessed user data to reduce repeated queries.
        
        Args:
            db_session: Database session
            user_ids: List of Discord user IDs to preload
            
        Returns:
            Dictionary mapping user_id to user data
        """
        user_data = {}
        
        try:
            from crud import get_user_preferences
            
            # Load preferences for all users concurrently
            tasks = [
                get_user_preferences(user_id)
                for user_id in user_ids
            ]
            
            preferences = await asyncio.gather(*tasks, return_exceptions=True)
            
            for user_id, prefs in zip(user_ids, preferences):
                if isinstance(prefs, Exception):
                    logger.warning(f"Failed to load preferences for {user_id}: {prefs}")
                    user_data[user_id] = {"preferences": None}
                else:
                    user_data[user_id] = {"preferences": prefs}
        
        except Exception as e:
            logger.error(f"Error preloading user data: {e}")
        
        return user_data
    
    @staticmethod
    def truncate_long_messages(
        message: str,
        max_length: int = None
    ) -> str:
        """
        Truncate long messages to reduce API costs and processing time.
        
        Args:
            message: Message text to truncate
            max_length: Maximum length (defaults to MAX_MESSAGE_LENGTH)
            
        Returns:
            Truncated message with ellipsis if needed
        """
        if max_length is None:
            max_length = PerformanceUtils.MAX_MESSAGE_LENGTH
        
        if len(message) <= max_length:
            return message
        
        # Truncate and add ellipsis
        return message[:max_length - 3] + "..."
    
    @staticmethod
    async def parallel_operations(
        *operations: Callable
    ) -> tuple:
        """
        Run multiple async operations in parallel.
        
        Args:
            *operations: Variable number of async callable operations
            
        Returns:
            Tuple of results from all operations
        """
        try:
            results = await asyncio.gather(*[op() for op in operations])
            return tuple(results)
        except Exception as e:
            logger.error(f"Error in parallel operations: {e}")
            raise
    
    @staticmethod
    def limit_context_window(
        messages: List[Any],
        max_messages: int = None
    ) -> List[Any]:
        """
        Limit conversation context to most recent messages.
        
        Args:
            messages: List of messages
            max_messages: Maximum number to keep (defaults to MAX_CONTEXT_MESSAGES)
            
        Returns:
            Truncated list of most recent messages
        """
        if max_messages is None:
            max_messages = PerformanceUtils.MAX_CONTEXT_MESSAGES
        
        if len(messages) <= max_messages:
            return messages
        
        # Return most recent messages
        return messages[-max_messages:]
    
    @staticmethod
    async def with_timeout(
        operation: Callable,
        timeout_seconds: float = 10.0,
        default_value: Any = None
    ) -> Any:
        """
        Execute operation with timeout fallback.
        
        Args:
            operation: Async operation to execute
            timeout_seconds: Maximum time to wait
            default_value: Value to return on timeout
            
        Returns:
            Operation result or default value on timeout
        """
        try:
            result = await asyncio.wait_for(operation(), timeout=timeout_seconds)
            return result
        except asyncio.TimeoutError:
            logger.warning(f"Operation timed out after {timeout_seconds}s")
            return default_value
        except Exception as e:
            logger.error(f"Error in timed operation: {e}")
            return default_value
    
    @staticmethod
    def get_quick_response_template(intent: str) -> Optional[str]:
        """
        Get template response for common intents to bypass full Claude call.
        
        Args:
            intent: Intent classification
            
        Returns:
            Template response if available, None otherwise
        """
        templates = {
            "get_help": (
                "I can help you with:\n"
                "• **General conversation** - Just chat with me naturally!\n"
                "• **Image generation** - Ask me to create or generate an image\n"
                "• **Status checks** - Ask about my status or capabilities\n"
                "• **Feature suggestions** - Submit ideas for new features\n"
                "• **GitHub issues** - Query and search GitHub issues\n\n"
                "What would you like to do?"
            ),
            "get_status": (
                "🟢 Bot is online and operational!\n\n"
                "All systems are functioning normally. I'm ready to help you with "
                "conversations, image generation, and more."
            )
        }
        
        return templates.get(intent)
    
    @staticmethod
    def should_use_quick_response(intent: str, message_length: int = 0) -> bool:
        """
        Determine if a quick template response should be used.
        
        Args:
            intent: Intent classification
            message_length: Length of user message
            
        Returns:
            True if quick response should be used
        """
        # Use quick response for help/status if message is short
        quick_response_intents = {"get_help", "get_status"}
        
        return (
            intent in quick_response_intents and
            message_length < 50  # Short messages likely don't need context
        )
    
    @staticmethod
    async def measure_operation_time(
        operation: Callable,
        operation_name: str = "operation"
    ) -> tuple[Any, float]:
        """
        Measure execution time of an operation.
        
        Args:
            operation: Async operation to measure
            operation_name: Name for logging
            
        Returns:
            Tuple of (result, execution_time_ms)
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            result = await operation()
            end_time = asyncio.get_event_loop().time()
            execution_time = (end_time - start_time) * 1000  # Convert to ms
            
            logger.debug(f"{operation_name} took {execution_time:.2f}ms")
            
            return result, execution_time
        
        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            execution_time = (end_time - start_time) * 1000
            
            logger.error(f"{operation_name} failed after {execution_time:.2f}ms: {e}")
            raise


class CacheWarmer:
    """Utility for warming up cache with common queries."""
    
    COMMON_QUERIES = [
        "help",
        "what can you do",
        "status",
        "hello",
        "hi",
        "how are you",
        "what is this bot",
        "commands"
    ]
    
    @staticmethod
    async def warm_cache(cache_service, intent_service, response_service):
        """
        Pre-populate cache with responses to common queries.
        
        Args:
            cache_service: ResponseCache instance
            intent_service: IntentService instance
            response_service: ResponseService instance
        """
        logger.info("Warming up response cache...")
        
        for query in CacheWarmer.COMMON_QUERIES:
            try:
                # Detect intent
                intent = await intent_service.detect_intent(query)
                
                # Get quick response if available
                quick_response = PerformanceUtils.get_quick_response_template(intent)
                
                if quick_response:
                    # Cache the quick response
                    await cache_service.set(query, quick_response, intent)
                    logger.debug(f"Cached quick response for: {query}")
            
            except Exception as e:
                logger.warning(f"Failed to warm cache for '{query}': {e}")
        
        logger.info(f"Cache warming complete. Cached {len(CacheWarmer.COMMON_QUERIES)} queries.")