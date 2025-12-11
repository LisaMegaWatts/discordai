# Conversational Discord Bot Architecture

## Executive Summary

This document outlines the comprehensive architecture for transforming the Discord bot from a command-based system into an intelligent, conversational AI assistant with semantic intent detection, context-aware responses, and natural language understanding powered by Anthropic's Claude.

### Current State Analysis

**Existing Capabilities:**
- Prefix-based commands: `/request-feature`, `/generate-image`, `/status`, `/submit-feature`, `/get-image`
- PostgreSQL database with SQLAlchemy async ORM
- Anthropic Claude client initialized but completely unused
- OpenRouter integration for image generation
- GitHub integration for automated PR creation
- Scheduled daily reflection tasks
- Basic database models: FeatureRequest, GeneratedImage, ScheduledTask, ReflectionLog

**Critical Limitations:**
- No natural language processing or understanding
- Static hardcoded responses without personality
- No conversation history or context management
- No emoji usage or dynamic formatting
- No multi-turn conversation support
- Anthropic client integration exists but is dormant

---

## 1. System Architecture Overview

```mermaid
graph TB
    subgraph "Discord Layer"
        A[Discord Message Event]
        B[Command Processor]
        C[Message Router]
    end
    
    subgraph "Intelligence Layer"
        D[Intent Detector]
        E[Entity Extractor]
        F[Context Manager]
        G[Response Generator]
    end
    
    subgraph "Data Layer"
        H[(Conversation History)]
        I[(User Preferences)]
        J[(Intent Logs)]
        K[(Existing Tables)]
    end
    
    subgraph "Integration Layer"
        L[Claude API]
        M[OpenRouter API]
        N[GitHub API]
    end
    
    A --> C
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> L
    G --> M
    G --> N
    F --> H
    F --> I
    D --> J
    G --> K
    
    style D fill:#ff9999
    style G fill:#99ccff
    style F fill:#99ff99
```

### Architecture Principles

1. **Async-First**: All operations use async/await for non-blocking I/O
2. **Layered Design**: Clear separation between Discord, intelligence, data, and integration layers
3. **Backward Compatible**: Existing commands continue to work
4. **Graceful Degradation**: System functions even if Claude API is unavailable
5. **Extensible**: Easy to add new intents and capabilities

---

## 2. Semantic Intent Detection System

### Intent Classification Architecture

```mermaid
graph LR
    A[User Message] --> B[Preprocessor]
    B --> C[Intent Classifier]
    C --> D{Confidence > Threshold?}
    D -->|Yes| E[Execute Intent Handler]
    D -->|No| F[Ambiguity Resolver]
    F --> G[Ask Clarification]
    F --> H[General Conversation]
    
    style C fill:#ffcc99
    style F fill:#ff9999
```

### Intent Categories

| Intent Type | Description | Example Triggers | Confidence Threshold |
|------------|-------------|------------------|---------------------|
| `generate_image` | Create images using AI | "create", "generate", "draw", "make an image" | 0.75 |
| `submit_feature` | Request new features | "feature request", "I want", "add feature" | 0.70 |
| `get_status` | Check bot/system status | "status", "how are you", "are you working" | 0.80 |
| `get_image` | Retrieve generated images | "show me", "get my image", "latest picture" | 0.75 |
| `general_conversation` | Casual chat | Various conversational phrases | 0.60 |
| `help` | Request assistance | "help", "what can you do", "commands" | 0.85 |
| `schedule_task` | Set up scheduled tasks | "remind me", "schedule", "set up task" | 0.70 |

### Intent Detection Implementation

**Core Components:**

1. **Intent Classifier Service** (`services/intent_classifier.py`)
```python
class IntentClassifier:
    def __init__(self, anthropic_client, model):
        self.client = anthropic_client
        self.model = model
        self.intent_cache = LRUCache(maxsize=1000)
    
    async def classify_intent(self, message: str, context: dict) -> IntentResult:
        """
        Classifies user intent using Claude with context awareness.
        
        Returns:
            IntentResult with intent_type, confidence, entities, and reasoning
        """
        pass
```

2. **Entity Extractor** (`services/entity_extractor.py`)
```python
class EntityExtractor:
    async def extract_entities(self, message: str, intent: str) -> dict:
        """
        Extracts relevant entities based on detected intent.
        
        For generate_image: prompt text, style preferences, dimensions
        For submit_feature: title, description, priority
        For schedule_task: task_name, datetime, recurrence
        """
        pass
```

3. **Confidence Scoring Strategy**
   - Base confidence from Claude's classification
   - Boosted by keyword matching (+0.05 to +0.15)
   - Adjusted by conversation context (+0.10 if related to recent messages)
   - Penalized for ambiguous phrasing (-0.10 to -0.20)

### Fallback Handling

```mermaid
graph TB
    A[Low Confidence Intent] --> B{Confidence < 0.60?}
    B -->|Yes| C[Clarification Strategy]
    B -->|No| D{Confidence < 0.75?}
    D -->|Yes| E[Tentative Execution with Confirmation]
    D -->|No| F[Direct Execution]
    
    C --> G[Ask User to Clarify]
    C --> H[Suggest Similar Intents]
    C --> I[Offer Command Examples]
    
    style C fill:#ff9999
    style E fill:#ffcc99
    style F fill:#99ff99
```

**Ambiguity Resolution Strategies:**

1. **Clarification Questions**: "Did you want to generate an image or submit a feature request?"
2. **Intent Suggestions**: Present buttons/reactions for likely intents
3. **Context-Based Inference**: Use conversation history to make educated guesses
4. **Default to Conversation**: Treat as general conversation if truly ambiguous

---

## 3. Conversation Management System

### Database Schema for Conversation History

```sql
-- New conversation history table
CREATE TABLE conversation_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    guild_id VARCHAR,                    -- NULL for DMs
    channel_id VARCHAR NOT NULL,
    message_id VARCHAR NOT NULL,         -- Discord message ID
    role VARCHAR NOT NULL,               -- 'user' or 'assistant'
    content TEXT NOT NULL,
    intent_type VARCHAR,                 -- Detected intent for user messages
    intent_confidence FLOAT,
    tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexing for fast retrieval
    INDEX idx_user_channel (user_id, channel_id),
    INDEX idx_created_at (created_at DESC)
);

-- User preferences table
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR UNIQUE NOT NULL,
    preferred_name VARCHAR,              -- How user wants to be addressed
    tone_preference VARCHAR DEFAULT 'friendly',  -- 'formal', 'friendly', 'casual', 'technical'
    emoji_density VARCHAR DEFAULT 'medium',      -- 'none', 'low', 'medium', 'high'
    language VARCHAR DEFAULT 'en',
    context_window_size INTEGER DEFAULT 10,      -- Number of messages to include
    notification_preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Intent logs for analytics and improvement
CREATE TABLE intent_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    message_content TEXT NOT NULL,
    detected_intent VARCHAR NOT NULL,
    confidence FLOAT NOT NULL,
    entities JSONB,                      -- Extracted entities
    execution_success BOOLEAN,
    execution_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_intent_confidence (detected_intent, confidence),
    INDEX idx_created_at (created_at DESC)
);

-- Session tracking
CREATE TABLE conversation_sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    channel_id VARCHAR NOT NULL,
    session_start TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMPTZ,
    message_count INTEGER DEFAULT 0,
    intents_detected JSONB DEFAULT '[]',
    summary TEXT,                        -- Claude-generated session summary
    
    INDEX idx_user_active (user_id, session_end)
);
```

### SQLAlchemy Models

```python
# models.py additions

class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    guild_id = Column(String)
    channel_id = Column(String, nullable=False)
    message_id = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    intent_type = Column(String)
    intent_confidence = Column(Float)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)
    preferred_name = Column(String)
    tone_preference = Column(String, default='friendly')
    emoji_density = Column(String, default='medium')
    language = Column(String, default='en')
    context_window_size = Column(Integer, default=10)
    notification_preferences = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class IntentLog(Base):
    __tablename__ = "intent_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    message_content = Column(Text, nullable=False)
    detected_intent = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    entities = Column(JSON)
    execution_success = Column(Boolean)
    execution_time_ms = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ConversationSession(Base):
    __tablename__ = "conversation_sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    channel_id = Column(String, nullable=False)
    session_start = Column(DateTime(timezone=True), server_default=func.now())
    session_end = Column(DateTime(timezone=True))
    message_count = Column(Integer, default=0)
    intents_detected = Column(JSON, default=[])
    summary = Column(Text)
```

### Context Window Management

**Context Manager Service** (`services/context_manager.py`)

```python
class ContextManager:
    """Manages conversation context for Claude prompts."""
    
    def __init__(self, db_session, max_tokens=8000):
        self.db_session = db_session
        self.max_tokens = max_tokens
        self.token_buffer = 2000  # Reserve for response
    
    async def get_conversation_context(
        self, 
        user_id: str, 
        channel_id: str, 
        window_size: int = 10
    ) -> List[dict]:
        """
        Retrieves recent conversation history for context.
        
        Strategy:
        1. Fetch last N messages from conversation_history
        2. Format as Claude-compatible message list
        3. Estimate tokens and truncate if needed
        4. Always include system prompt and current message
        """
        pass
    
    async def add_to_context(
        self, 
        user_id: str, 
        channel_id: str,
        role: str,
        content: str,
        intent_type: str = None,
        confidence: float = None
    ):
        """Stores a message in conversation history."""
        pass
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 chars)."""
        return len(text) // 4
    
    async def get_user_preferences(self, user_id: str) -> UserPreferences:
        """Retrieves or creates user preferences."""
        pass
    
    async def summarize_old_context(self, messages: List[dict]) -> str:
        """
        Uses Claude to summarize older messages when context is too long.
        Replaces old messages with summary to save tokens.
        """
        pass
```

### Session Management

```python
class SessionManager:
    """Tracks and manages conversation sessions."""
    
    SESSION_TIMEOUT = 1800  # 30 minutes
    
    async def get_or_create_session(
        self, 
        user_id: str, 
        channel_id: str
    ) -> ConversationSession:
        """Get active session or create new one."""
        pass
    
    async def end_session(self, session_id: int):
        """End session and generate summary."""
        pass
    
    async def update_session_intent(self, session_id: int, intent: str):
        """Track intents used in session."""
        pass
```

---

## 4. Enhanced Response Generation

### Prompt Engineering Strategy

**System Prompt Template** (`prompts/system_prompt.py`)

```python
SYSTEM_PROMPT_TEMPLATE = """You are an intelligent Discord bot assistant with the following capabilities:

PERSONALITY:
- Friendly and helpful, but not overly chatty
- Use emojis naturally based on user preference ({emoji_density})
- Tone: {tone_preference}
- Address user as: {preferred_name}

CAPABILITIES:
1. Generate images using AI models (via OpenRouter)
2. Submit and track feature requests (creates GitHub PRs)
3. Retrieve previously generated images
4. Schedule tasks and reminders
5. Provide status updates and help
6. Engage in general conversation about technology, AI, and development

RESPONSE GUIDELINES:
- Keep responses concise but informative
- Use code blocks for technical content
- Suggest relevant commands when appropriate
- Ask clarifying questions if intent is unclear
- Use emojis to enhance communication: {emoji_guidelines}

CONTEXT:
- Current date/time: {current_datetime}
- User timezone: {user_timezone}
- Recent conversation: Available in message history

IMPORTANT:
- You can execute actions by responding with structured JSON when needed
- Always confirm destructive actions before proceeding
- If unsure about user intent, ask for clarification
"""

EMOJI_GUIDELINES = {
    'none': 'Do not use emojis',
    'low': 'Use 1-2 emojis per response, only for emphasis',
    'medium': 'Use 2-4 emojis naturally throughout responses',
    'high': 'Use emojis liberally to express emotion and enhance readability'
}
```

**Intent-Specific Prompts** (`prompts/intent_prompts.py`)

```python
INTENT_PROMPTS = {
    'generate_image': """
        The user wants to generate an image. Extract:
        - Main subject/prompt
        - Style preferences (if mentioned)
        - Any specific requirements
        
        Format your response with:
        1. Confirmation of what you'll generate
        2. Engaging description with appropriate emoji
        3. JSON action block to trigger generation
    """,
    
    'submit_feature': """
        The user wants to submit a feature request. Extract:
        - Feature title (concise)
        - Detailed description
        - Priority level (if mentioned)
        
        Respond with:
        1. Confirmation you understand the feature
        2. Summary of what will be created
        3. JSON action block to create GitHub PR
    """,
    
    'general_conversation': """
        Engage in natural conversation while:
        1. Being helpful and informative
        2. Subtly mentioning relevant bot capabilities
        3. Keeping responses focused and not too long
        4. Using appropriate emojis based on user preference
    """
}
```

### Response Generator Service

```python
class ResponseGenerator:
    """Generates context-aware responses using Claude."""
    
    def __init__(self, anthropic_client, model):
        self.client = anthropic_client
        self.model = model
    
    async def generate_response(
        self,
        user_message: str,
        intent: IntentResult,
        context: List[dict],
        user_prefs: UserPreferences
    ) -> ResponseResult:
        """
        Generates a response using Claude with full context.
        
        Returns:
            ResponseResult with text, actions, and metadata
        """
        
        # Build system prompt
        system_prompt = self._build_system_prompt(user_prefs)
        
        # Add intent-specific instructions
        intent_instructions = INTENT_PROMPTS.get(intent.intent_type, "")
        
        # Construct messages
        messages = context + [{
            'role': 'user',
            'content': f"{intent_instructions}\n\nUser message: {user_message}"
        }]
        
        # Call Claude API
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
            temperature=0.7
        )
        
        # Parse response
        return self._parse_response(response)
    
    def _build_system_prompt(self, user_prefs: UserPreferences) -> str:
        """Builds personalized system prompt."""
        pass
    
    def _parse_response(self, claude_response) -> ResponseResult:
        """
        Parses Claude response for:
        - Main text response
        - Action directives (JSON blocks)
        - Emoji insertion
        - Formatting
        """
        pass
```

### Action Directive System

Claude can include JSON action blocks in responses to trigger bot actions:

```python
ACTION_SCHEMA = {
    'generate_image': {
        'prompt': str,
        'model': str,  # optional
        'confirm': bool  # require user confirmation
    },
    'submit_feature': {
        'title': str,
        'description': str,
        'create_pr': bool
    },
    'schedule_task': {
        'task_name': str,
        'run_at': str,  # ISO format datetime
        'recurrence': str  # optional
    }
}
```

Example Claude response with action:

```
I'll generate that cyberpunk city image for you! 🌆✨

Creating a stunning neon-lit metropolis with flying cars...

```json
{
    "action": "generate_image",
    "params": {
        "prompt": "cyberpunk city at night with neon lights and flying cars, detailed, 4k",
        "confirm": false
    }
}
```

This will take about 30 seconds. I'll send it to you as soon as it's ready! 🎨
```

---

## 5. Message Processing Flow

### Complete Message Pipeline

```mermaid
sequenceDiagram
    participant U as User
    participant D as Discord Bot
    participant R as Message Router
    participant I as Intent Detector
    participant C as Context Manager
    participant G as Response Generator
    participant A as Action Executor
    participant DB as Database
    
    U->>D: Send Message
    D->>R: Route Message
    
    R->>I: Detect Intent
    I->>DB: Log Intent
    I-->>R: Intent Result
    
    R->>C: Get Context
    C->>DB: Fetch History
    C->>DB: Get User Prefs
    C-->>R: Context + Prefs
    
    R->>G: Generate Response
    Note over G: Typing indicator shown
    G->>External: Claude API Call
    External-->>G: Response
    G-->>R: Response + Actions
    
    R->>A: Execute Actions
    A->>DB: Update Data
    A->>External: External APIs
    A-->>R: Action Results
    
    R->>C: Store in History
    C->>DB: Save Message
    
    R->>D: Send Response
    D->>U: Display Response
```

### Router Implementation

```python
class MessageRouter:
    """Routes messages through the processing pipeline."""
    
    def __init__(
        self,
        intent_detector: IntentClassifier,
        context_manager: ContextManager,
        response_generator: ResponseGenerator,
        action_executor: ActionExecutor
    ):
        self.intent_detector = intent_detector
        self.context_manager = context_manager
        self.response_generator = response_generator
        self.action_executor = action_executor
    
    async def process_message(
        self,
        message: discord.Message
    ) -> ProcessingResult:
        """
        Main processing pipeline for all messages.
        
        Steps:
        1. Pre-filter (ignore bots, check permissions)
        2. Detect intent with confidence scoring
        3. Load conversation context
        4. Generate response with Claude
        5. Execute any actions
        6. Store in history
        7. Send response to Discord
        """
        
        # Step 1: Pre-filter
        if message.author.bot:
            return
        
        user_id = str(message.author.id)
        channel_id = str(message.channel.id)
        
        # Step 2: Detect intent
        start_time = time.time()
        intent = await self.intent_detector.classify_intent(
            message.content,
            {'user_id': user_id, 'channel_id': channel_id}
        )
        
        # Step 3: Load context
        context = await self.context_manager.get_conversation_context(
            user_id, channel_id
        )
        user_prefs = await self.context_manager.get_user_preferences(user_id)
        
        # Show typing indicator
        async with message.channel.typing():
            # Step 4: Generate response
            response = await self.response_generator.generate_response(
                message.content,
                intent,
                context,
                user_prefs
            )
            
            # Step 5: Execute actions
            if response.actions:
                action_results = await self.action_executor.execute_actions(
                    response.actions,
                    message,
                    user_prefs
                )
                response.merge_action_results(action_results)
        
        # Step 6: Store in history
        await self.context_manager.add_to_context(
            user_id, channel_id, 'user', message.content,
            intent.intent_type, intent.confidence
        )
        await self.context_manager.add_to_context(
            user_id, channel_id, 'assistant', response.text
        )
        
        # Step 7: Send response
        await message.channel.send(response.text)
        
        # Log metrics
        execution_time = int((time.time() - start_time) * 1000)
        await self._log_intent(
            user_id, message.content, intent, 
            execution_time, response.success
        )
        
        return ProcessingResult(
            intent=intent,
            response=response,
            execution_time_ms=execution_time
        )
```

---

## 6. Responsiveness Improvements

### Async Processing Architecture

```python
class AsyncMessageProcessor:
    """Handles async message processing with queue management."""
    
    def __init__(self, max_concurrent=10):
        self.queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.processing_tasks = set()
    
    async def enqueue_message(self, message: discord.Message):
        """Add message to processing queue."""
        await self.queue.put(message)
    
    async def process_queue(self):
        """Process messages from queue with concurrency control."""
        while True:
            message = await self.queue.get()
            
            async with self.semaphore:
                task = asyncio.create_task(
                    self._process_with_timeout(message)
                )
                self.processing_tasks.add(task)
                task.add_done_callback(self.processing_tasks.discard)
    
    async def _process_with_timeout(
        self, 
        message: discord.Message, 
        timeout=30
    ):
        """Process message with timeout."""
        try:
            await asyncio.wait_for(
                self.router.process_message(message),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            await message.channel.send(
                "⏱️ Sorry, that took too long. Please try again."
            )
```

### Typing Indicators

```python
class TypingIndicatorManager:
    """Manages typing indicators during processing."""
    
    @staticmethod
    async def show_typing(channel, duration_estimate=10):
        """
        Shows typing indicator for estimated duration.
        Discord typing indicators last 10 seconds, so refresh as needed.
        """
        iterations = (duration_estimate // 10) + 1
        for _ in range(iterations):
            await channel.trigger_typing()
            await asyncio.sleep(9)  # Refresh before expiry
```

### Response Caching Strategy

```python
class ResponseCache:
    """Caches responses for common queries."""
    
    def __init__(self, max_size=1000, ttl=3600):
        self.cache = {}  # Use Redis in production
        self.max_size = max_size
        self.ttl = ttl
    
    def _generate_cache_key(
        self, 
        message: str, 
        intent: str, 
        user_prefs: dict
    ) -> str:
        """Generates cache key from message + context."""
        # Hash of: message + intent + key preferences
        cache_str = f"{message}:{intent}:{user_prefs.get('tone_preference')}"
        return hashlib.sha256(cache_str.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[str]:
        """Retrieve cached response if exists and not expired."""
        pass
    
    async def set(self, key: str, value: str):
        """Cache response with TTL."""
        pass
    
    def should_cache(self, intent: str) -> bool:
        """Determine if intent type should be cached."""
        # Don't cache: generate_image, submit_feature (unique)
        # Do cache: help, status, general FAQs
        cacheable_intents = {'help', 'get_status', 'general_conversation'}
        return intent in cacheable_intents
```

### Rate Limiting

```python
class RateLimiter:
    """Rate limiting per user to prevent abuse."""
    
    def __init__(self):
        self.user_requests = {}  # user_id -> deque of timestamps
        self.limits = {
            'generate_image': (5, 3600),    # 5 per hour
            'submit_feature': (10, 3600),   # 10 per hour
            'general': (30, 60)             # 30 per minute
        }
    
    async def check_rate_limit(
        self, 
        user_id: str, 
        intent: str
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if user is within rate limits.
        
        Returns:
            (is_allowed, retry_after_seconds)
        """
        pass
    
    async def handle_rate_limit_exceeded(
        self, 
        message: discord.Message,
        retry_after: int
    ):
        """Send friendly rate limit message."""
        await message.channel.send(
            f"⏸️ Whoa there! You're going a bit fast. "
            f"Please wait {retry_after} seconds before trying again. 😊"
        )
```

### Error Handling Strategy

```python
class ErrorHandler:
    """Centralized error handling with user-friendly messages."""
    
    ERROR_MESSAGES = {
        'api_error': "🔧 Oops! My connection to the AI service is having issues. Try again in a moment?",
        'timeout': "⏱️ That took too long! Let's try something simpler?",
        'invalid_input': "🤔 I didn't quite understand that. Could you rephrase?",
        'permission_denied': "🔒 I don't have permission to do that here.",
        'rate_limited': "⏸️ Slow down a bit! You'll be able to try again soon.",
        'unknown': "😅 Something unexpected happened. My developers will look into it!"
    }
    
    async def handle_error(
        self,
        error: Exception,
        message: discord.Message,
        context: dict
    ):
        """Handle errors gracefully with logging."""
        error_type = self._classify_error(error)
        user_message = self.ERROR_MESSAGES.get(
            error_type, 
            self.ERROR_MESSAGES['unknown']
        )
        
        # Log error with context
        logger.error(
            f"Error processing message: {error}",
            extra={
                'user_id': message.author.id,
                'message_content': message.content[:100],
                'error_type': error_type,
                **context
            }
        )
        
        # Send user-friendly message
        await message.channel.send(user_message)
```

---

## 7. Integration Points

### Backward Compatibility with Existing Commands

```python
class HybridCommandHandler:
    """Handles both slash commands and natural language."""
    
    async def route_command(self, message: discord.Message):
        """
        Routes to appropriate handler:
        - Slash commands (/) -> Legacy command handler
        - Natural language -> New intent-based handler
        - Mentions/DMs -> Natural language processing
        """
        
        if message.content.startswith('/'):
            # Legacy command - process normally
            return await self.legacy_handler.process(message)
        else:
            # Natural language - use intent detection
            return await self.intent_handler.process(message)
```

### GitHub Integration Enhancement

```python
class EnhancedGitHubIntegration:
    """Enhanced GitHub integration with Claude-generated content."""
    
    async def create_feature_request_with_claude(
        self,
        user_message: str,
        extracted_entities: dict
    ) -> str:
        """
        Uses Claude to:
        1. Generate detailed feature description from user input
        2. Create structured GitHub issue/PR content
        3. Suggest implementation approach
        4. Generate acceptance criteria
        """
        
        prompt = f"""
        Based on this feature request: "{user_message}"
        
        Create a well-structured GitHub PR description with:
        - Clear title
        - Detailed description
        - User story format
        - Acceptance criteria
        - Technical considerations
        """
        
        # Use Claude to generate structured content
        pr_content = await self.claude_client.generate(prompt)
        
        # Create PR with enhanced content
        pr_url = create_feature_branch_and_pr(
            extracted_entities['title'],
            pr_content,
            extracted_entities['discord_link']
        )
        
        return pr_url
```

### OpenRouter Image Generation Integration

```python
class EnhancedImageGeneration:
    """Enhanced image generation with Claude prompt optimization."""
    
    async def generate_optimized_image(
        self,
        user_prompt: str,
        user_prefs: UserPreferences
    ) -> GeneratedImage:
        """
        Uses Claude to optimize the prompt before generation:
        1. Enhance vague prompts with details
        2. Add style specifications
        3. Optimize for the selected model
        4. Validate prompt safety
        """
        
        optimization_prompt = f"""
        Optimize this image generation prompt: "{user_prompt}"
        
        Make it:
        - More detailed and descriptive
        - Better structured for AI image generation
        - Include artistic style if not specified
        - Safe and appropriate
        
        Return ONLY the optimized prompt, nothing else.
        """
        
        optimized_prompt = await self.claude_client.generate(
            optimization_prompt
        )
        
        # Generate image with optimized prompt
        return await self.openrouter_client.generate_image(
            optimized_prompt.strip()
        )
```

---

## 8. Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Priority: Critical**

- [ ] Database schema migration
  - Create new tables: conversation_history, user_preferences, intent_logs, conversation_sessions
  - Add indexes for performance
  - Migration script with rollback support

- [ ] Core service infrastructure
  - Intent classifier service skeleton
  - Context manager basic implementation
  - Response generator foundation
  - Message router framework

- [ ] Basic Claude integration
  - Test Anthropic client connection
  - Implement simple intent detection
  - Create basic system prompts

**Success Criteria:**
- Database tables created and tested
- Bot can detect 3 basic intents with >70% accuracy
- Conversation history is stored
- Basic Claude responses work

### Phase 2: Intent Detection & Entity Extraction (Week 3-4)
**Priority: High**

- [ ] Complete intent classifier
  - Implement all 7 intent types
  - Entity extraction for each intent
  - Confidence scoring system
  - Intent logging and analytics

- [ ] Context management
  - Full conversation history retrieval
  - User preference system
  - Session tracking
  - Context window management

- [ ] Fallback handling
  - Ambiguity detection
  - Clarification question generation
  - Default conversation mode

**Success Criteria:**
- 90%+ intent detection accuracy on test set
- Entity extraction works for all intents
- Context includes last 10 messages
- Graceful handling of ambiguous queries

### Phase 3: Enhanced Response Generation (Week 5-6)
**Priority: High**

- [ ] Advanced prompt engineering
  - Intent-specific prompts
  - Personality customization
  - Emoji integration
  - Dynamic formatting

- [ ] Action directive system
  - JSON action parsing
  - Action execution framework
  - Confirmation workflows
  - Error handling

- [ ] Response optimization
  - Token usage optimization
  - Response caching
  - Streaming support (if applicable)

**Success Criteria:**
- Responses feel natural and personalized
- Actions execute correctly from Claude directives
- Emoji usage matches user preferences
- Response generation under 3 seconds average

### Phase 4: Responsiveness & Performance (Week 7)
**Priority: Medium**

- [ ] Async processing optimization
  - Message queue implementation
  - Concurrent processing
  - Timeout handling

- [ ] User experience improvements
  - Typing indicators
  - Progress updates for long operations
  - Inline feedback

- [ ] Caching & rate limiting
  - Response caching for common queries
  - Per-user rate limiting
  - Global rate limiting

**Success Criteria:**
- Handle 100+ concurrent users
- Response time under 5 seconds for 95th percentile
- Rate limiting prevents abuse
- Typing indicators show during processing

### Phase 5: Integration & Polish (Week 8)
**Priority: Medium**

- [ ] Enhanced integrations
  - Claude-optimized GitHub PRs
  - Improved image generation prompts
  - Better error messages

- [ ] User preferences UI
  - Commands to set preferences
  - Interactive preference setup
  - Preference templates

- [ ] Analytics & monitoring
  - Intent success tracking
  - Response quality metrics
  - User engagement analytics

**Success Criteria:**
- All integrations work with new system
- Users can customize their experience
- Comprehensive monitoring in place
- A/B testing framework ready

### Phase 6: Testing & Refinement (Week 9-10)
**Priority: High**

- [ ] Comprehensive testing
  - Unit tests for all services
  - Integration tests
  - Load testing
  - User acceptance testing

- [ ] Prompt refinement
  - A/B test different system prompts
  - Optimize intent detection prompts
  - Fine-tune response generation

- [ ] Documentation
  - API documentation
  - User guide
  - Admin documentation
  - Troubleshooting guide

**Success Criteria:**
- 95%+ test coverage
- All critical paths tested
- Documentation complete
- Ready for production launch

---

## 9. Performance Considerations

### Persistent Memory & Session Reliability

- **Redis Integration**: Session state and message history are stored in Redis for fast access. Automatic fallback to the database ensures durability and recovery after restarts or Redis failures.
- **Session Management**: Sessions are reliably tracked and maintained across bot restarts, Redis flushes, and multi-instance deployments. Session timeouts and context windows are enforced for consistent user experience.
- **Bot Reliability**: Recovery logic enables seamless operation during failures. The bot is resilient to Redis outages and database reconnections.

### Security & History Rewrite

- **Secrets Removal**: All secrets have been removed from history and configuration files. Only environment variables are used for sensitive data.
- **History Rewrite**: Git history was rewritten to remove secrets. If you previously cloned the repository, re-pull or re-clone to ensure secrets are not present.

### Token Usage Optimization

```python
TOKEN_LIMITS = {
    'context_window': 8000,     # Max tokens for context
    'response_max': 1024,       # Max tokens per response
    'reserved': 2000,           # Reserved for response
    'system_prompt': 500        # Typical system prompt size
}

def optimize_context(messages: List[dict], max_tokens: int) -> List[dict]:
    """
    Optimizes context to fit within token limit:
    1. Start with most recent messages
    2. Include summary of older messages if available
    3. Prioritize messages with detected intents
    4. Truncate oldest messages first
    """
    pass
```

### Database Indexing Strategy

```sql
-- High-priority indexes
CREATE INDEX idx_conv_history_lookup 
    ON conversation_history(user_id, channel_id, created_at DESC);

CREATE INDEX idx_intent_logs_analysis 
    ON intent_logs(detected_intent, confidence, created_at DESC);

CREATE INDEX idx_user_prefs_lookup 
    ON user_preferences(user_id);

CREATE INDEX idx_session_active 
    ON conversation_sessions(user_id, session_end) 
    WHERE session_end IS NULL;

-- Partial index for active sessions only
CREATE INDEX idx_active_sessions 
    ON conversation_sessions(user_id) 
    WHERE session_end IS NULL;
```

### Caching Strategy

| Data Type | Cache Duration | Invalidation Trigger |
|-----------|---------------|---------------------|
| User Preferences | 1 hour | User update command |
| Intent Detection (common) | 10 minutes | N/A |
| Help Responses | 1 hour | Bot restart |
| Status Responses | 5 minutes | Status change |
| Image Generation | None | Never cache |

### Monitoring Metrics

```python
METRICS_TO_TRACK = {
    'performance': [
        'intent_detection_time_ms',
        'response_generation_time_ms',
        'total_processing_time_ms',
        'tokens_per_request',
        'cache_hit_rate'
    ],
    'quality': [
        'intent_confidence_avg',
        'intent_accuracy',
        'user_satisfaction_rating',
        'conversation_completion_rate'
    ],
    'usage': [
        'messages_per_user_per_day',
        'intents_distribution',
        'active_users_daily',
        'api_calls_per_hour'
    ]
}
```

---

## 10. Security Considerations

### Input Validation

```python
class InputValidator:
    """Validates and sanitizes user input."""
    
    MAX_MESSAGE_LENGTH = 2000
    BLOCKED_PATTERNS = [
        r'<script>',
        r'javascript:',
        r'onerror=',
        # SQL injection patterns
        r"'; DROP TABLE",
        r"' OR '1'='1"
    ]
    
    async def validate_message(self, message: str) -> Tuple[bool, str]:
        """
        Validates message for:
        - Length limits
        - Blocked patterns
        - Malicious content
        """
        pass
    
    def sanitize_prompt(self, prompt: str) -> str:
        """Sanitizes image generation prompts."""
        # Remove attempts to break prompt injection
        # Filter NSFW content
        # Limit special characters
        pass
```

### API Key Protection

- Store API keys in environment variables only
- Use separate keys for dev/staging/prod
- Implement key rotation strategy
- Monitor for unusual API usage patterns
- Rate limit per API key

### Data Privacy

```python
PII_RETENTION = {
    'conversation_history': 90,  # days
    'intent_logs': 30,           # days
    'user_preferences': None,    # Keep until user deletion
    'session_data': 7            # days
}

async def anonymize_old_data():
    """
    Anonymizes or deletes old data per retention policy.
    Runs daily as scheduled task.
    """
    pass
```

---

## 11. Testing Strategy

### Test Coverage Requirements

```python
# Unit Tests
- Intent Classifier: 90%+ coverage
- Entity Extractor: 85%+ coverage
- Context Manager: 90%+ coverage
- Response Generator: 85%+ coverage
- Message Router: 90%+ coverage

# Integration Tests
- End-to-end message flow
- Database operations
- External API mocking
- Error scenarios

# Load Tests
- 100 concurrent users
- 1000 messages/minute
- Memory usage under load
- Database connection pooling
```

### Test Data Sets

```python
TEST_INTENTS = {
    'generate_image': [
        "create an image of a sunset",
        "draw me a cat",
        "can you make a picture of mountains?",
        "I want a cyberpunk cityscape"
    ],
    'submit_feature': [
        "I'd like to request a new feature",
        "add support for X",
        "feature request: add Y",
        "can you add the ability to Z?"
    ],
    'ambiguous': [
        "help",
        "what?",
        "cool",
        "thanks"
    ]
}
```

---

## 12. Deployment Checklist

### Pre-Deployment

- [ ] Database migration tested on staging
- [ ] All tests passing (unit, integration, load)
- [ ] API keys configured in production environment
- [ ] Monitoring and alerting configured
- [ ] Rollback plan documented
- [ ] Performance benchmarks established

### Deployment Steps

1. Database migration (during low-traffic period)
2. Deploy new code with feature flag OFF
3. Verify health checks pass
4. Enable feature flag for 10% of users
5. Monitor metrics for 24 hours
6. Gradually increase to 100%
7. Remove feature flag code

### Post-Deployment

- [ ] Monitor error rates
- [ ] Track intent detection accuracy
- [ ] Review user feedback
- [ ] Optimize based on real-world usage
- [ ] Document lessons learned

---

## 13. Future Enhancements

### Voice Message Support
- Transcribe voice messages using Anthropic's audio capabilities
- Process as regular messages through intent detection
- Generate audio responses

### Multi-Modal Understanding
- Process images in user messages
- Understand context from embedded images
- Generate descriptions or analysis

### Proactive Engagement
- Daily summaries for users
- Suggestions based on usage patterns
- Reminders for incomplete tasks
- Trend analysis and reports

### Advanced Personalization
- Learning user communication style
- Adaptive emoji usage based on reactions
- Time-of-day personality adjustments
- Context-aware greeting messages

### Integration Expansions
- Jira integration for task tracking
- Slack/Teams bridge
- Calendar integration for scheduling
- Email digest generation

---

## Appendix A: API Reference

### IntentResult Data Class

```python
@dataclass
class IntentResult:
    intent_type: str
    confidence: float
    entities: Dict[str, Any]
    reasoning: str
    alternative_intents: List[Tuple[str, float]]
```

### ResponseResult Data Class

```python
@dataclass
class ResponseResult:
    text: str
    actions: List[ActionDirective]
    metadata: Dict[str, Any]
    tokens_used: int
    success: bool
    error_message: Optional[str] = None
```

### ActionDirective Data Class

```python
@dataclass
class ActionDirective:
    action_type: str
    parameters: Dict[str, Any]
    confirm_required: bool
    priority: int
```

---

## Appendix B: Configuration Reference

### Environment Variables

```bash
# Required
DISCORD_TOKEN=your_discord_token
ANTHROPIC_API_KEY=your_anthropic_key
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Optional
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_IMAGE_MODEL=stabilityai/stable-diffusion-xl
GITHUB_TOKEN=your_github_token
GITHUB_REPO=owner/repo

# Performance
MAX_CONCURRENT_MESSAGES=10
CONTEXT_WINDOW_SIZE=10
RESPONSE_CACHE_TTL=3600
MAX_TOKENS_PER_REQUEST=8000

# Rate Limiting
RATE_LIMIT_IMAGE_GEN=5,3600
RATE_LIMIT_FEATURE_REQUEST=10,3600
RATE_LIMIT_GENERAL=30,60
```

---

## Summary

This architecture transforms the Discord bot from a simple command-based system into an intelligent, conversational assistant that:

1. **Understands natural language** through Claude-powered intent detection
2. **Maintains context** across conversations with session management
3. **Responds naturally** with personality and appropriate emoji usage
4. **Executes actions** based on conversational directives
5. **Performs efficiently** with async processing and caching
6. **Integrates seamlessly** with existing GitHub and image generation features

The phased implementation approach ensures steady progress while maintaining backward compatibility. The foundation prioritizes core functionality, followed by enhancements and optimizations.

**Key Success Metrics:**
- 90%+ intent detection accuracy
- <5 second average response time
- 95%+ user satisfaction rate
- Zero breaking changes to existing commands
- Scalable to 1000+ concurrent users

This architecture provides a robust foundation for building an intelligent, responsive, and engaging Discord bot that enhances user experience while maintaining the reliability of existing features.