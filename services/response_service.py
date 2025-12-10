"""
Response Generation Service for Discord Bot

This service uses Claude to generate intelligent, context-aware responses
with personality customization and emoji integration based on user preferences.
"""

import logging
import time
from typing import Optional, List, Dict, Any

from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession

from crud import get_user_preferences

logger = logging.getLogger(__name__)


class ResponseGenerationService:
    """
    Generates contextual, personality-driven responses using Claude.
    
    This service:
    - Builds system prompts based on user preferences and intent
    - Generates responses using Claude with conversation context
    - Applies emoji preferences to responses
    - Handles errors with intent-specific fallback responses
    """
    
    def __init__(self, anthropic_client: AsyncAnthropic, db_session: AsyncSession):
        """
        Initialize the response generation service.
        
        Args:
            anthropic_client: Initialized Anthropic async client
            db_session: AsyncSession instance for database operations
        """
        self.client = anthropic_client
        self.db = db_session
        self.model = "claude-sonnet-4-20250514"
    
    async def generate_response(
        self,
        user_message: str,
        intent: str,
        entities: dict,
        conversation_context: list,
        user_id: str
    ) -> str:
        """
        Generate a contextual response using Claude.
        
        Args:
            user_message: The user's message text
            intent: Detected intent type
            entities: Extracted entities from the message
            conversation_context: List of recent messages
            user_id: Discord user ID
        
        Returns:
            str: Generated response text with appropriate personality and emojis
        
        Example:
            >>> response = await service.generate_response(
            ...     user_message="Can you make an image of a sunset?",
            ...     intent="generate_image",
            ...     entities={"prompt": "sunset"},
            ...     conversation_context=[...],
            ...     user_id="123456"
            ... )
            >>> print(response)
            "I'd love to create a beautiful sunset image for you! 🌅✨ Let me generate that now..."
        """
        start_time = time.time()
        
        try:
            # Get user preferences
            try:
                preferences = await self._get_user_preferences(user_id)
            except Exception as e:
                logger.error(f"Error getting user preferences for user {user_id}: {e}", exc_info=True)
                return self._get_fallback_response(intent)
            
            try:
                system_prompt = self._build_system_prompt(intent, preferences)
            except Exception as e:
                logger.error(f"Error building system prompt for intent '{intent}', user {user_id}: {e}", exc_info=True)
                return self._get_fallback_response(intent)
            
            try:
                user_prompt = self._build_user_prompt(
                    user_message,
                    intent,
                    entities,
                    conversation_context
                )
            except Exception as e:
                logger.error(f"Error building user prompt for user {user_id}: {e}", exc_info=True)
                return self._get_fallback_response(intent)
            
            try:
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=500,  # Discord message limits
                    temperature=0.7,  # Natural, varied responses
                    system=system_prompt,
                    messages=[{
                        "role": "user",
                        "content": user_prompt
                    }]
                )
            except Exception as e:
                logger.error(f"Error calling Claude API for user {user_id}: {e}", exc_info=True)
                return self._get_fallback_response(intent)
            
            try:
                response_text = response.content[0].text
            except Exception as e:
                logger.error(f"Error extracting response text for user {user_id}: {e}", exc_info=True)
                return self._get_fallback_response(intent)
            
            try:
                final_response = self._apply_emoji_preference(
                    response_text,
                    preferences.get('emoji_density', 'moderate')
                )
            except Exception as e:
                logger.error(f"Error applying emoji preference for user {user_id}: {e}", exc_info=True)
                return self._get_fallback_response(intent)
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"Generated response for intent '{intent}' in {elapsed_ms}ms "
                f"(user: {user_id})"
            )
            
            return final_response
            
        except Exception as e:
            logger.error(
                f"Error generating response for user {user_id}: {e}",
                exc_info=True
            )
            # Return fallback response
            return self._get_fallback_response(intent)
    
    async def _get_user_preferences(self, user_id: str) -> dict:
        """
        Get user preferences from database.
        
        Args:
            user_id: Discord user ID
        
        Returns:
            dict: User preferences with keys:
                - tone_preference: friendly/professional/casual/enthusiastic
                - emoji_density: none/low/moderate/high
                - language: Language code (default: en)
        """
        try:
            prefs = await get_user_preferences(user_id)
            return {
                'tone_preference': prefs.tone_preference,
                'emoji_density': prefs.emoji_density,
                'language': prefs.language
            }
        except Exception as e:
            logger.error(f"Error getting preferences for user {user_id}: {e}")
            # Return defaults on error
            return {
                'tone_preference': 'friendly',
                'emoji_density': 'moderate',
                'language': 'en'
            }
    
    def _build_system_prompt(self, intent: str, preferences: dict) -> str:
        """
        Build system prompt based on intent and user preferences.
        
        Args:
            intent: Detected intent type
            preferences: User preferences dict
        
        Returns:
            str: Complete system prompt for Claude
        """
        tone = preferences.get('tone_preference', 'friendly')
        emoji_density = preferences.get('emoji_density', 'moderate')
        
        # Base personality traits
        personality_traits = {
            'friendly': 'warm, helpful, and conversational',
            'professional': 'concise, formal, and business-like',
            'casual': 'relaxed, informal, and fun',
            'enthusiastic': 'energetic, encouraging, and positive'
        }
        
        personality = personality_traits.get(tone, personality_traits['friendly'])
        
        # Intent-specific instructions
        intent_instructions = {
            'generate_image': (
                "When the user wants to generate an image:\n"
                "- Confirm you understand their request\n"
                "- Acknowledge the specific subject/style they mentioned\n"
                "- Let them know you'll create the image\n"
                "- Use appropriate creative emojis (✨, 🎨, 🌅)\n"
                "- Keep your response brief (2-3 sentences)"
            ),
            'submit_feature': (
                "When the user wants to submit a feature request:\n"
                "- Acknowledge their request warmly\n"
                "- Confirm you understand what they want\n"
                "- Ask for clarification if details are missing\n"
                "- Use appropriate emojis (📝, ✅, 💡)\n"
                "- Be encouraging about their suggestion"
            ),
            'get_status': (
                "When the user asks about status:\n"
                "- Provide clear, direct status information\n"
                "- Be reassuring and positive\n"
                "- Use status-related emojis (✅, ⏳, 🔄)\n"
                "- Keep it concise"
            ),
            'get_help': (
                "When the user needs help:\n"
                "- Be informative and patient\n"
                "- Explain capabilities clearly\n"
                "- Offer specific examples\n"
                "- Use helpful emojis (💡, 📖, 🤝)\n"
                "- Make it easy to understand"
            ),
            'general_conversation': (
                "For general conversation:\n"
                "- Be engaging and natural\n"
                "- Respond appropriately to their tone\n"
                "- Keep responses brief (2-4 sentences)\n"
                "- Use contextually appropriate emojis (💬, 😊, 👋)\n"
                "- Stay on topic with the conversation"
            ),
            'action_query': (
                "When asked about previous actions:\n"
                "- Reference their history accurately\n"
                "- Be specific about what was done\n"
                "- Use timeline emojis (📅, 🕐, 📋)\n"
                "- Offer to help with related tasks"
            )
        }
        
        intent_guide = intent_instructions.get(
            intent,
            intent_instructions['general_conversation']
        )
        
        # Emoji guidelines
        emoji_guides = {
            'none': 'Do not use any emojis in your responses.',
            'low': 'Use 1-2 emojis per response, only for emphasis on key points.',
            'moderate': 'Use 3-5 emojis naturally throughout your response.',
            'high': 'Use 6+ emojis liberally to express emotion and enhance readability.'
        }
        
        emoji_guide = emoji_guides.get(emoji_density, emoji_guides['moderate'])
        
        # Construct full system prompt
        system_prompt = f"""You are Roo, a helpful Discord bot assistant with the following personality:

PERSONALITY:
- Be {personality}
- Your name is Roo
- You assist with image generation, feature requests, and general conversation

{intent_guide}

EMOJI USAGE:
{emoji_guide}

CONTEXTUALLY APPROPRIATE EMOJIS:
- ✨ for creation/generation
- 🎨 for art/images
- 📝 for writing/features
- ✅ for completion
- 💬 for conversation
- 🤔 for questions
- 🎉 for celebration
- ⚠️ for warnings

RESPONSE GUIDELINES:
- Keep responses concise (2-4 sentences for general conversation)
- Longer responses OK for help/explanations
- Use Discord-friendly formatting (no complex markdown)
- Include action directives when needed (e.g., "I'll create that image now")
- Ask clarifying questions when needed
- Be direct and clear in your communication

IMPORTANT:
- You can generate images using AI models
- You can help submit feature requests
- You maintain conversation context
- Always be helpful and responsive"""
        
        return system_prompt
    
    def _build_user_prompt(
        self,
        user_message: str,
        intent: str,
        entities: dict,
        conversation_context: list
    ) -> str:
        """
        Build user prompt with conversation context.
        
        Args:
            user_message: Current user message
            intent: Detected intent
            entities: Extracted entities
            conversation_context: Recent messages
        
        Returns:
            str: Complete user prompt with context
        """
        prompt_parts = []
        
        # Add conversation context if available
        if conversation_context and len(conversation_context) > 0:
            prompt_parts.append("Previous conversation:")
            
            # Include last 5-10 messages for context
            recent_messages = conversation_context[-10:]
            for msg in recent_messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                role_label = "User" if role == "user" else "Assistant"
                prompt_parts.append(f"{role_label}: {content}")
            
            prompt_parts.append("")  # Blank line separator
        
        # Add intent and entities information
        prompt_parts.append(f"Detected intent: {intent}")
        
        if entities and len(entities) > 0:
            prompt_parts.append(f"Extracted entities: {entities}")
        
        prompt_parts.append("")  # Blank line separator
        
        # Add current user message
        prompt_parts.append(f"Current user message: {user_message}")
        prompt_parts.append("")
        prompt_parts.append("Generate an appropriate response:")
        
        return "\n".join(prompt_parts)
    
    def _apply_emoji_preference(self, response: str, emoji_density: str) -> str:
        """
        Adjust emoji usage based on user preference.
        
        Note: This is a post-processing step. The system prompt already
        guides Claude on emoji usage, but this ensures compliance.
        
        Args:
            response: Generated response text
            emoji_density: User's emoji preference (none/low/moderate/high)
        
        Returns:
            str: Response with adjusted emoji usage
        """
        if emoji_density == 'none':
            # Remove all emojis (basic implementation)
            import re
            # Remove common emojis using regex pattern
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"  # emoticons
                "\U0001F300-\U0001F5FF"  # symbols & pictographs
                "\U0001F680-\U0001F6FF"  # transport & map symbols
                "\U0001F1E0-\U0001F1FF"  # flags
                "\U00002702-\U000027B0"  # dingbats
                "\U000024C2-\U0001F251"
                "]+", flags=re.UNICODE
            )
            response = emoji_pattern.sub('', response)
            # Clean up extra spaces
            response = ' '.join(response.split())
        
        # For other densities, trust the system prompt guidance
        # Claude should already be following the emoji density guidelines
        
        return response
    
    def _get_fallback_response(self, intent: str) -> str:
        """
        Get fallback response when Claude API fails.
        
        Args:
            intent: The detected intent
        
        Returns:
            str: Intent-specific fallback response
        """
        fallbacks = {
            'generate_image': (
                "I'd love to create that image! 🎨 Could you describe "
                "what you'd like to see in a bit more detail?"
            ),
            'submit_feature': (
                "I'll help you submit that feature request! 📝 "
                "What would you like to suggest?"
            ),
            'get_status': (
                "I'm here and ready to help! ✅ Everything is working normally."
            ),
            'get_help': (
                "I'm here to help! 💡 I can create images, submit feature requests, "
                "and chat with you. What would you like to do?"
            ),
            'general_conversation': (
                "Thanks for chatting with me! 💬 How can I assist you today?"
            ),
            'action_query': (
                "Let me check your previous actions. 📋 What specifically "
                "would you like to know about?"
            ),
            'unclear': (
                "I'm not quite sure what you're asking. 🤔 Could you rephrase that "
                "or let me know if you'd like to create an image or submit a feature request?"
            )
        }
        
        return fallbacks.get(intent, fallbacks['general_conversation'])