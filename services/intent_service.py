"""
Intent Detection Service for Discord Bot

This service uses Claude to analyze user messages and determine their intent
with confidence scores and entity extraction.
"""

import json
import logging
import time
from typing import Optional

from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)


class IntentDetectionService:
    """
    Service for detecting user intent from natural language messages.
    
    Uses Claude to classify messages into predefined intent categories
    and extract relevant entities from the message content.
    """
    
    # Intent categories as defined in the architecture
    INTENTS = {
        'generate_image': 'User wants to create an image using AI',
        'submit_feature': 'User wants to submit a feature request',
        'get_status': 'User asking about bot or request status',
        'get_help': 'User needs help or information',
        'general_conversation': 'Casual conversation',
        'unclear': 'Intent cannot be determined',
        'action_query': 'User asking about previous actions/results'
    }
    
    def __init__(self, anthropic_client: AsyncAnthropic):
        """
        Initialize the intent detection service.
        
        Args:
            anthropic_client: Initialized Anthropic async client
        """
        self.client = anthropic_client
        self.model = "claude-sonnet-4-20250514"
    
    async def detect_intent(
        self, 
        message: str, 
        user_history: Optional[list] = None
    ) -> dict:
        """
        Detect the intent of a user message.
        
        Args:
            message: The user's message text
            user_history: Optional list of recent conversation messages
                         Format: [{"role": "user/assistant", "content": "..."}]
        
        Returns:
            dict: {
                "intent": str,           # Intent category
                "confidence": float,     # Confidence score 0.0-1.0
                "entities": dict,        # Extracted entities specific to intent
                "reasoning": str         # Explanation of the classification
            }
        
        Example:
            >>> result = await service.detect_intent("Can you create an image of a sunset?")
            >>> print(result)
            {
                "intent": "generate_image",
                "confidence": 0.95,
                "entities": {"prompt": "sunset", "style": null, "modifiers": []},
                "reasoning": "User explicitly requests image creation"
            }
        """
        start_time = time.time()
        
        try:
            # Build the prompt for Claude
            prompt = self._build_intent_prompt(message, user_history)
            
            # Call Anthropic API
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.3,  # Lower temperature for more consistent classification
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Extract the text content from the response
            response_text = response.content[0].text
            
            # Parse the response
            result = self._parse_intent_response(response_text)
            
            # Add timing information
            elapsed_ms = int((time.time() - start_time) * 1000)
            result['processing_time_ms'] = elapsed_ms
            
            logger.info(
                f"Intent detected: {result['intent']} "
                f"(confidence: {result['confidence']:.2f}, time: {elapsed_ms}ms)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting intent: {e}", exc_info=True)
            # Return unclear intent on failure
            return {
                "intent": "unclear",
                "confidence": 0.0,
                "entities": {},
                "reasoning": f"Error during intent detection: {str(e)}",
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
    
    def _build_intent_prompt(
        self, 
        message: str, 
        user_history: Optional[list] = None
    ) -> str:
        """
        Build the prompt for Claude to classify intent.
        
        Args:
            message: The user's message
            user_history: Optional conversation history
        
        Returns:
            str: The complete prompt for Claude
        """
        # Start with the base instruction
        prompt = """You are an intent classification system for a Discord bot. Analyze the user's message and determine their intent.

AVAILABLE INTENTS:

1. **generate_image** - User wants to create an image
   Examples:
   - "create an image of a sunset"
   - "draw me a cat"
   - "can you generate a picture of mountains?"
   - "make me a cyberpunk cityscape"

2. **submit_feature** - User wants to submit a feature request
   Examples:
   - "I'd like to request a new feature"
   - "add support for voice messages"
   - "feature request: add dark mode"
   - "can you add the ability to schedule tasks?"

3. **get_status** - User asking about bot or request status
   Examples:
   - "what's the status of my request?"
   - "are you working?"
   - "how are you doing?"
   - "is the bot online?"

4. **get_help** - User needs help or information
   Examples:
   - "help"
   - "what can you do?"
   - "how do I use this bot?"
   - "show me the commands"

5. **general_conversation** - Casual conversation
   Examples:
   - "hello!"
   - "thanks for your help"
   - "that's cool"
   - "good morning"

6. **action_query** - User asking about previous actions/results
   Examples:
   - "show me my last image"
   - "what did I request yesterday?"
   - "get my previous generations"
   - "did my feature request get approved?"

7. **unclear** - Intent cannot be determined
   Examples:
   - "hmm"
   - "..." 
   - Very ambiguous or incomplete messages

ENTITY EXTRACTION GUIDELINES:

For **generate_image**, extract:
- "prompt": The main subject/description
- "style": Any mentioned artistic style (e.g., "photorealistic", "anime", "watercolor")
- "modifiers": List of additional requirements (e.g., ["4k", "detailed", "sunset lighting"])

For **submit_feature**, extract:
- "title": Short title for the feature
- "description": Detailed description

For **get_status**, extract:
- "request_type": "feature", "image", or "general"
- "request_id": Any specific ID mentioned (if any)

For **general_conversation**, extract:
- "topic": Main topic of conversation

For **action_query**, extract:
- "action_type": "image", "feature", or "general"
- "timeframe": Any time reference (e.g., "yesterday", "last week")

CONFIDENCE SCORING:
- 0.9-1.0: Very clear intent with explicit keywords
- 0.75-0.89: Clear intent with strong indicators
- 0.6-0.74: Probable intent but some ambiguity
- 0.4-0.59: Uncertain, multiple possible intents
- 0.0-0.39: Very unclear, default to "unclear" intent

"""

        # Add conversation history if provided
        if user_history and len(user_history) > 0:
            prompt += "\nRECENT CONVERSATION CONTEXT:\n"
            for msg in user_history[-5:]:  # Include last 5 messages for context
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                prompt += f"{role.upper()}: {content}\n"
            prompt += "\n"
        
        # Add the current message
        prompt += f"""USER MESSAGE TO CLASSIFY:
"{message}"

RESPONSE FORMAT:
Respond with ONLY a JSON object (no other text) in this exact format:
{{
    "intent": "intent_name",
    "confidence": 0.85,
    "entities": {{}},
    "reasoning": "Brief explanation of why this intent was chosen"
}}

Analyze the message and respond now:"""
        
        return prompt
    
    def _parse_intent_response(self, response: str) -> dict:
        """
        Parse Claude's response into structured format.
        
        Args:
            response: Raw response text from Claude
        
        Returns:
            dict: Parsed intent result
        """
        try:
            # Claude should return JSON, but let's handle edge cases
            # Try to find JSON in the response
            response = response.strip()
            
            # If response starts with markdown code block, extract JSON
            if response.startswith('```'):
                # Find JSON between code blocks
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end > start:
                    response = response[start:end]
            
            # Parse the JSON
            result = json.loads(response)
            
            # Validate the structure
            intent = result.get('intent', 'unclear')
            confidence = float(result.get('confidence', 0.0))
            entities = result.get('entities', {})
            reasoning = result.get('reasoning', 'No reasoning provided')
            
            # Ensure intent is valid
            if intent not in self.INTENTS:
                logger.warning(f"Unknown intent '{intent}', defaulting to 'unclear'")
                intent = 'unclear'
                confidence = 0.0
            
            # Clamp confidence to valid range
            confidence = max(0.0, min(1.0, confidence))
            
            return {
                "intent": intent,
                "confidence": confidence,
                "entities": entities,
                "reasoning": reasoning
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response}")
            return {
                "intent": "unclear",
                "confidence": 0.0,
                "entities": {},
                "reasoning": f"Failed to parse response: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error parsing intent response: {e}")
            return {
                "intent": "unclear",
                "confidence": 0.0,
                "entities": {},
                "reasoning": f"Error parsing response: {str(e)}"
            }