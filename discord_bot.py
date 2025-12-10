import asyncio
# Utility to check if event loop is running and not closed
def is_event_loop_running():
    try:
        loop = asyncio.get_running_loop()
        return not loop.is_closed()
    except RuntimeError:
        return False
from dotenv import load_dotenv
load_dotenv()

import discord
from discord.ext import commands
import os
import requests
import anthropic
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Base
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime
import asyncio
import sys

# Import new conversational services
from services.intent_service import IntentDetectionService
from services.conversation_service import ConversationContextManager
from services.response_service import ResponseGenerationService
from services.cache_service import ResponseCache
from services.performance_utils import PerformanceUtils, CacheWarmer
from crud import create_intent_log

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/ai_ide_db")
from db import AsyncSessionLocal, engine

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/ai_ide_db")

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Load Discord token from environment variable or config file
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_IMAGE_MODEL = os.getenv("OPENROUTER_IMAGE_MODEL", "stabilityai/stable-diffusion-xl")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# Initialize Anthropic client for bot/coding AI
anthropic_client = None
if ANTHROPIC_API_KEY:
    anthropic_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="/", intents=intents)
scheduler = AsyncIOScheduler()

# Track background tasks for explicit shutdown
background_tasks = set()
shutdown_event = asyncio.Event()

# Centralized deduplication using Redis
from services.redis_utils import RedisClient
redis_client = RedisClient()

# Initialize conversational services
intent_service = IntentDetectionService(anthropic_client)
response_cache = ResponseCache(ttl_seconds=300, max_size=1000)

# Background task to clear expired cache entries
async def cache_cleanup_task():
    """Periodically clear expired cache entries."""
    while True:
        if not is_event_loop_running():
            print("[DIAG] Event loop closed detected in cache_cleanup_task. Exiting task.")
            break
        await asyncio.sleep(300)  # Run every 5 minutes
        await response_cache.clear_expired()
        stats = response_cache.get_stats()
        print(f"Cache stats: {stats}")

async def setup_scheduler():
    """Initialize and start the scheduler with the bot's event loop."""
    from pytz import timezone
    scheduler.add_job(
        daily_reflection_task,
        "cron",
        hour=8,
        minute=0,
        timezone=timezone("America/New_York"),
        id="daily_reflection"
    )
    scheduler.start()
    print("Scheduler started successfully.")

@bot.event
async def setup_hook():
    """Called when the bot is starting up and the event loop is ready."""
    await setup_scheduler()
    
    # Start cache cleanup background task and track it
    task = asyncio.create_task(cache_cleanup_task())
    background_tasks.add(task)
    def _task_done_callback(t):
        background_tasks.discard(t)
    task.add_done_callback(_task_done_callback)
    
    # Cache warming removed - cache will populate naturally during use
    # This prevents startup errors with unhashable dict types

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    print("\n=== API Configuration Status ===")
    
    # Validate OpenRouter API Key and Image Model
    if OPENROUTER_API_KEY:
        print("[LOG] OpenRouter API Key: Configured")
        print("[LOG] OpenRouter Image Model: " + str(OPENROUTER_IMAGE_MODEL))
    else:
        print("[WARN] OPENROUTER_API_KEY not set - Image generation will not work")
        print("  Please set OPENROUTER_API_KEY in your environment variables")
    
    # Validate Anthropic API Key and Model
    if ANTHROPIC_API_KEY:
        print("[LOG] Anthropic API Key: Configured")
        print("[LOG] Anthropic Model: " + str(ANTHROPIC_MODEL))
        if anthropic_client:
            print("[LOG] Anthropic Client: Initialized successfully")
    else:
        print("[WARN] ANTHROPIC_API_KEY not set - Bot/coding AI features will be limited")
        print("  Please set ANTHROPIC_API_KEY in your environment variables")
    
    print("================================\n")

@bot.event
async def on_message(message):
    """Process all messages through semantic intent detection pipeline."""
    # Logging for event handler registration and triggering
    print(f"[LOG] on_message event triggered for message id: {getattr(message, 'id', None)} author: {getattr(message.author, 'id', None)}")
    # Ignore bot's own messages
    if message.author == bot.user:
        return

    # Process commands first (for backward compatibility)
    await bot.process_commands(message)

    # If message was a command, skip conversational processing
    ctx = await bot.get_context(message)
    if ctx.valid:
        return

    # Ensure only one reply per message (no parallel/concurrent calls)
    msg_id = getattr(message, "id", None)
    dedup_key = f"dedup:msg:{msg_id}"
    acquired = False
    if msg_id is not None:
        # Atomic deduplication with Redis
        dedup_result = await redis_client.set_if_not_exists(dedup_key, "1", expire_seconds=600)
        if not dedup_result:
            print(f"[LOG] Duplicate reply prevented for message id: {msg_id}")
            return
        acquired = True

    try:
        if message.channel is not None and is_event_loop_running():
            async with message.channel.typing():
                response_text = await process_conversational_message(message)
                if response_text and is_event_loop_running():
                    await message.channel.send(response_text)
        else:
            print("Error: message.channel is None or event loop is closed. Cannot send response.")
    except Exception as e:
        print(f"Error processing conversational message: {e}")
        if message.channel is not None and is_event_loop_running():
            await message.channel.send("I encountered an error processing your message. Please try again or use a slash command.")
        else:
            print("Error: message.channel is None or event loop is closed. Cannot send error message.")
    finally:
        # Remove deduplication key to allow future replies if needed (optional, or let expire)
        if msg_id is not None and acquired:
            await redis_client.delete(f"dedup:msg:{msg_id}")

async def process_conversational_message(message: discord.Message) -> str:
    """Process message through semantic intent detection pipeline with caching and optimizations."""
    try:
        user_id = str(message.author.id)
        message_text = message.content
        
        # Truncate extremely long messages
        message_text = PerformanceUtils.truncate_long_messages(message_text)
        
        # Check cache first for quick responses
        cached_response = await response_cache.get(message_text)
        if cached_response:
            print(f"Cache hit for message: {message_text[:50]}...")
            return cached_response
        
        # Initialize services with Redis for dedup/session state
        conversation_manager = ConversationContextManager(AsyncSessionLocal, redis_client=redis_client)
        response_service = ResponseGenerationService(anthropic_client, None)
        
        # Parallel operations: Get session and detect intent concurrently
        session_task = conversation_manager.get_or_create_session(user_id)
        intent_task = intent_service.detect_intent(message_text)
        
        session, intent_result = await asyncio.gather(session_task, intent_task)

        if session is None:
            print(f"Error: Session object is None after get_or_create_session for user {user_id}.")
            return "Session error: Unable to create or retrieve a valid session. Please try again later."

        intent = intent_result['intent']

        # Check if we can use a quick template response
        if PerformanceUtils.should_use_quick_response(intent, len(message_text)):
            quick_response = PerformanceUtils.get_quick_response_template(intent)
            if quick_response:
                # Cache the quick response
                await response_cache.set(message_text, quick_response, intent)

                # Still log intent and store messages for analytics
                await create_intent_log(
                    user_id,
                    message_text,
                    intent,
                    intent_result.get('confidence', 0.0),
                    intent_result.get('entities', {})
                )

                await conversation_manager.add_message(session.id, user_id, message_text, "user", intent, intent_result.get('confidence', 0.0))
                await conversation_manager.add_message(session.id, user_id, quick_response, "assistant")

                return quick_response
        
        # Log intent detection
        await create_intent_log(
            user_id,
            message_text,
            intent,
            intent_result.get('confidence', 0.0),
            intent_result.get('entities', {})
        )
        
        # Get conversation context with limited window (last 10 messages)
        context = await conversation_manager.get_conversation_context(session.id, max_messages=10)
        
        # Handle intent-specific actions
        action_result = None
        entities = intent_result.get('entities', {})
        
        if intent in ['generate_image', 'submit_feature']:
            action_result = await handle_intent_action(intent, entities, message)
        
        # Generate response based on intent and context
        response_text = await response_service.generate_response(
            user_message=message_text,
            intent=intent,
            entities=intent_result.get('entities', {}),
            conversation_context=context,
            user_id=user_id
        )
        
        # Store messages in conversation history (parallel)
        store_user_msg = conversation_manager.add_message(session.id, user_id, message_text, "user", intent, intent_result.get('confidence', 0.0))
        store_assistant_msg = conversation_manager.add_message(session.id, user_id, response_text, "assistant")
        
        await asyncio.gather(store_user_msg, store_assistant_msg)
        
        # Cache response if intent is cacheable
        if response_cache.is_cacheable_intent(intent):
            await response_cache.set(message_text, response_text, intent)
        
        return response_text
            
    except Exception as e:
        raise

async def handle_intent_action(intent: str, entities: dict, message: discord.Message) -> str:
    """Execute actions based on detected intent."""
    user_id = str(message.author.id)
    
    try:
        if intent == 'generate_image':
            prompt = entities.get('image_prompt', entities.get('prompt', ''))
            if not prompt:
                return "I couldn't extract a prompt for image generation. Please provide a description."
            result = await generate_image_from_prompt(prompt, user_id, message)
            return result
            
        elif intent == 'submit_feature':
            title = entities.get('feature_title', 'Feature Request')
            description = entities.get('feature_description', entities.get('description', ''))
            if not description:
                return "I couldn't extract a feature description. Please provide more details."
            result = await submit_feature_from_text(title, description, user_id, message)
            return result
            
        return None
        
    except Exception as e:
        print(f"Error handling intent action: {e}")
        return f"I encountered an error while processing your request: {str(e)}"

async def generate_image_from_prompt(prompt: str, user_id: str, message: discord.Message) -> str:
    """Generate image from prompt (extracted from /generate-image command)."""
    if not OPENROUTER_API_KEY:
        return "Error: OpenRouter API key not configured. Please contact the administrator."
    
    try:
        # Call OpenRouter API for image generation
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://discord-ai-bot",
            "X-Title": "Discord AI Bot"
        }
        
        payload = {
            "model": OPENROUTER_IMAGE_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        # Extract image URL from response
        if 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content']
            image_url = content.strip()
        else:
            return "Error: Unexpected response format from OpenRouter API."

        # Download image
        import aiohttp
        import uuid

        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    img_bytes = await resp.read()
                    # Save locally
                    os.makedirs("generated_images", exist_ok=True)
                    filename = f"{uuid.uuid4().hex}_{int(datetime.datetime.utcnow().timestamp())}.png"
                    filepath = os.path.join("generated_images", filename)
                    with open(filepath, "wb") as f:
                        f.write(img_bytes)
                    # Store metadata in DB
                    async with AsyncSessionLocal() as db_session:
                        from crud import create_generated_image
                        db_image = await create_generated_image(db_session, user_id, filepath, prompt)
                        if db_image is None:
                            print(f"Error: Failed to store generated image metadata in DB for user {user_id}, prompt '{prompt}'.")
                    # Send image to channel
                    if message.channel is not None and is_event_loop_running():
                        await message.channel.send(file=discord.File(filepath))
                    else:
                        print("Error: message.channel is None or event loop is closed. Cannot send generated image.")
                    return f"I've generated an image for: '{prompt}'"
                else:
                    return "Failed to download generated image."
    except Exception as e:
        return f"Image generation failed: {str(e)}"

async def submit_feature_from_text(title: str, description: str, user_id: str, message: discord.Message) -> str:
    """Submit feature request from extracted text."""
    try:
        discord_link = message.jump_url
        
        # Store feature request in PostgreSQL
        from crud import create_feature_request
        async with AsyncSessionLocal() as session:
            fr = await create_feature_request(session, user_id, title, description)
            if fr is None:
                print(f"Error: Failed to create feature request for user {user_id}, title '{title}'.")
        
            # Create GitHub PR
            from github_integration import create_feature_branch_and_pr
            pr_url = create_feature_branch_and_pr(title, description, discord_link)
        
            return f"I've submitted your feature request: '{title}'. GitHub PR: {pr_url}"
        
    except Exception as e:
        return f"Failed to submit feature request: {str(e)}"

async def daily_reflection_task():
    # Analyze codebase changes (stub: count lines changed in migrations/001_create_tables.sql)
    try:
        with open("migrations/001_create_tables.sql", "r") as f:
            migration_lines = f.readlines()
        migration_summary = f"Migration file has {len(migration_lines)} lines."
    except Exception:
        migration_summary = "Could not read migration file."

    # Review feature requests (stub: count pending requests)
    from crud import FeatureRequest
    async with AsyncSessionLocal() as session:
        from sqlalchemy.future import select
        result = await session.execute(select(FeatureRequest).where(FeatureRequest.status == "pending"))
        pending_count = len(result.scalars().all())
    feature_summary = f"{pending_count} pending feature requests."

    # Generate summary
    summary = f"Daily Reflection ({datetime.datetime.utcnow().strftime('%Y-%m-%d')}):\n{migration_summary}\n{feature_summary}"

    # Log to PostgreSQL (ReflectionLog, user_id='system')
    from crud import create_reflection_log
    async with AsyncSessionLocal() as session:
        result = await create_reflection_log(session, "system", summary)
        if result is None:
            print("Error: Failed to create reflection log in DB for daily reflection.")

    # Post to Discord channel (stub: channel_id from env)
    channel_id = int(os.getenv("REFLECTION_CHANNEL_ID", "0"))
    if channel_id:
        channel = bot.get_channel(channel_id)
        if channel is not None:
            await channel.send(summary)
        else:
            print(f"Error: Could not find channel with id {channel_id}. Cannot send summary.")

@bot.command(name="request-feature")
async def request_feature(ctx):
    # Example: extract title/description from user message (MVP: prompt for input)
    feature_title = "Sample Feature"
    feature_description = "Sample description from Discord request."
    discord_link = ctx.message.jump_url

    from github_integration import create_feature_branch_and_pr

    pr_url = create_feature_branch_and_pr(feature_title, feature_description, discord_link)
    try:
        if hasattr(ctx, 'channel') and ctx.channel is not None and is_event_loop_running():
            await ctx.send(f"Feature request received. PR created: {pr_url}")
        else:
            print("Error: ctx.channel is None or event loop is closed. Cannot send feature request response.")
    except (AttributeError, RuntimeError) as e:
        print(f"Error sending feature request response: {e}")

@bot.command(name="generate-image")
async def generate_image(ctx, *, prompt: str = None):
    # Deduplication logic for commands
    global _reply_in_progress_message_ids, _reply_in_progress_lock
    msg_id = getattr(ctx.message, "id", None)
    acquired = False
    if msg_id is not None:
        async with _reply_in_progress_lock:
            if msg_id in _reply_in_progress_message_ids:
                print(f"[LOG] Duplicate reply prevented for message id: {msg_id}")
                return
            _reply_in_progress_message_ids.add(msg_id)
            acquired = True

    try:
        if not prompt:
            try:
                if hasattr(ctx, 'channel') and ctx.channel is not None and is_event_loop_running():
                    await ctx.send("Please provide a prompt. Usage: `/generate-image <prompt>`")
                else:
                    print("Error: ctx.channel is None or event loop is closed. Cannot send prompt error.")
            except (AttributeError, RuntimeError) as e:
                print(f"Error sending prompt error: {e}")
            return

        await ctx.send(f"Generating image for prompt: `{prompt}` ...")
        
        if not OPENROUTER_API_KEY:
                try:
                    if hasattr(ctx, 'channel') and ctx.channel is not None and is_event_loop_running():
                        await ctx.send("Error: OpenRouter API key not configured. Please contact the administrator.")
                    else:
                        print("Error: ctx.channel is None or event loop is closed. Cannot send API key error.")
                except (AttributeError, RuntimeError) as e:
                    print(f"Error sending API key error: {e}")
                return
        
        try:
            # Call OpenRouter API for image generation
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://discord-ai-bot",
                "X-Title": "Discord AI Bot"
            }
            
            payload = {
                "model": OPENROUTER_IMAGE_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            # Extract image URL from response - format may vary by model
            # For image generation models, the response typically contains the image URL
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                # The image URL might be in the content or we need to parse it
                # For now, assume the model returns a URL or base64 encoded image
                image_url = content.strip()
            else:
                await ctx.send("Error: Unexpected response format from OpenRouter API.")
                return

            # Download image
            import aiohttp
            import datetime
            import uuid

            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        img_bytes = await resp.read()
                        # Save locally
                        os.makedirs("generated_images", exist_ok=True)
                        filename = f"{uuid.uuid4().hex}_{int(datetime.datetime.utcnow().timestamp())}.png"
                        filepath = os.path.join("generated_images", filename)
                        with open(filepath, "wb") as f:
                            f.write(img_bytes)
                        # Store metadata in DB
                        async with AsyncSessionLocal() as db_session:
                            from crud import create_generated_image
                            user_id = str(ctx.author.id)
                            db_image = await create_generated_image(db_session, user_id, filepath, prompt)
                            if db_image is None:
                                print(f"Error: Failed to store generated image metadata in DB for user {user_id}, prompt '{prompt}'.")
                        await ctx.send(f"Image generated and saved: {filepath}")
                        await ctx.send(file=discord.File(filepath))
                    else:
                        await ctx.send("Failed to download generated image.")
        except Exception as e:
            await ctx.send(f"Image generation failed: {e}")
    finally:
        if msg_id is not None and acquired:
            async with _reply_in_progress_lock:
                _reply_in_progress_message_ids.discard(msg_id)

@bot.command(name="get-image")
async def get_image(ctx, image_id: int = None):
    """Retrieve a generated image by ID or latest for the user."""
    async with AsyncSessionLocal() as db_session:
        from crud import get_generated_image
        user_id = str(ctx.author.id)
        if image_id:
            img = await get_generated_image(db_session, image_id)
            if not img or img.user_id != user_id:
                try:
                    if hasattr(ctx, 'channel') and ctx.channel is not None and is_event_loop_running():
                        await ctx.send("Image not found or access denied.")
                    else:
                        print("Error: ctx.channel is None or event loop is closed. Cannot send image not found.")
                except (AttributeError, RuntimeError) as e:
                    print(f"Error sending image not found: {e}")
                return
        else:
            from sqlalchemy import select
            result = await db_session.execute(
                select(GeneratedImage)
                .where(GeneratedImage.user_id == user_id)
                .order_by(GeneratedImage.created_at.desc())
                .limit(1)
            )
            img = result.scalar_one_or_none()
            if not img:
                await ctx.send("No images found for you.")
                return
        # Send image file
        if os.path.exists(img.image_url):
            await ctx.send(f"Prompt: {img.prompt}\nCreated: {img.created_at}")
            await ctx.send(file=discord.File(img.image_url))
        else:
            await ctx.send("Image file not found on server.")

@bot.command(name="status")
async def status(ctx):
    try:
        if hasattr(ctx, 'channel') and ctx.channel is not None and is_event_loop_running():
            await ctx.send("Bot is running and ready. (MVP stub)")
        else:
            print("Error: ctx.channel is None or event loop is closed. Cannot send status.")
    except (AttributeError, RuntimeError) as e:
        print(f"Error sending status: {e}")

@bot.command(name="generate")
async def generate(ctx, *, prompt: str = None):
    """Generate content based on a prompt (stub handler)."""
    if not prompt:
        await ctx.send("Please provide a prompt. Usage: `/generate <prompt>`")
        return
    await ctx.send(f"Generating content for prompt: `{prompt}` ... (feature not implemented)")

@bot.command(name="Get")
async def get(ctx, *, arg: str = None):
    """Get information or resource (stub handler)."""
    print("[DIAG] /Get command handler triggered with arg:", arg)
    await ctx.send("Get command received. (feature not implemented)")

@bot.command(name="submit-feature")
async def submit_feature(ctx, *, arg: str = None):
    # Deduplication logic for commands
    global _reply_in_progress_message_ids, _reply_in_progress_lock
    msg_id = getattr(ctx.message, "id", None)
    acquired = False
    if msg_id is not None:
        async with _reply_in_progress_lock:
            if msg_id in _reply_in_progress_message_ids:
                print(f"[LOG] Duplicate reply prevented for message id: {msg_id}")
                return
            _reply_in_progress_message_ids.add(msg_id)
            acquired = True

    try:
        """
        Usage: /submit-feature <title> | <description>
        """
        if not arg or "|" not in arg:
                try:
                    if hasattr(ctx, 'channel') and ctx.channel is not None and is_event_loop_running():
                        await ctx.send("Usage: `/submit-feature <title> | <description>`")
                    else:
                        print("Error: ctx.channel is None or event loop is closed. Cannot send submit-feature usage.")
                except (AttributeError, RuntimeError) as e:
                    print(f"Error sending submit-feature usage: {e}")
                return
        title, description = [x.strip() for x in arg.split("|", 1)]
        discord_link = ctx.message.jump_url
        user_id = str(ctx.author.id)

        # Store feature request in PostgreSQL
        from crud import create_feature_request
        async with AsyncSessionLocal() as session:
            fr = await create_feature_request(session, user_id, title, description)
            if fr is None:
                print(f"Error: Failed to create feature request for user {user_id}, title '{title}'.")

        # Create GitHub PR
        from github_integration import create_feature_branch_and_pr
        pr_url = create_feature_branch_and_pr(title, description, discord_link)

        # Notify Discord channel
        try:
            if hasattr(ctx, 'channel') and ctx.channel is not None and is_event_loop_running():
                await ctx.send(f"Feature request submitted and stored. PR created: {pr_url}")
            else:
                print("Error: ctx.channel is None or event loop is closed. Cannot send feature request submitted.")
        except (AttributeError, RuntimeError) as e:
            print(f"Error sending feature request submitted: {e}")
    finally:
        if msg_id is not None and acquired:
            async with _reply_in_progress_lock:
                _reply_in_progress_message_ids.discard(msg_id)

import atexit

def create_lock_file_atomic(lock_path):
    """
    Atomically create a lock file. If it already exists, another process is running.
    Returns True if lock acquired, False otherwise.
    """
    import os
    import errno
    try:
        # O_EXCL + O_CREAT ensures atomic creation
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w") as f:
            f.write(str(os.getpid()))
        return True
    except OSError as e:
        if e.errno == errno.EEXIST:
            return False
        raise

def remove_lock_file(lock_path):
    import os
    try:
        if os.path.exists(lock_path):
            os.remove(lock_path)
    except Exception as e:
        print(f"Error removing lock file: {e}")

LOCK_FILE_PATH = "discord_bot.lock"

def enforce_single_process():
    if not create_lock_file_atomic(LOCK_FILE_PATH):
        print("[ERROR] Another discord_bot.py process is already running (lock file exists).")
        sys.exit(1)
    # Register cleanup for normal exit
    atexit.register(remove_lock_file, LOCK_FILE_PATH)
    # Register cleanup for SIGINT/SIGTERM
    import signal
    def _cleanup_handler(*_):
        remove_lock_file(LOCK_FILE_PATH)
        sys.exit(0)
    signal.signal(signal.SIGINT, _cleanup_handler)
    signal.signal(signal.SIGTERM, _cleanup_handler)

if __name__ == "__main__":
    enforce_single_process()
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN not set in environment.")
    else:
        # Initialize database tables before starting the bot
        # This ensures all required tables exist before any bot operations
        try:
            print("Initializing database tables...")
            asyncio.run(init_db())
            print("Database tables initialized successfully.")
        except Exception as e:
            print(f"Error initializing database: {e}")
            print("Bot startup aborted due to database initialization failure.")
            sys.exit(1)

        # Patch bot.close to ensure background tasks are cancelled and DB engine disposed
        orig_close = bot.close
        async def safe_close():
            print("[SHUTDOWN] Initiating shutdown sequence...")
            shutdown_event.set()
            # Cancel all background tasks
            print(f"[SHUTDOWN] Cancelling {len(background_tasks)} background tasks...")
            for task in list(background_tasks):
                if not task.done():
                    print(f"[SHUTDOWN] Cancelling background task: {task}")
                    task.cancel()
            try:
                await asyncio.gather(*background_tasks, return_exceptions=True)
                print("[DIAG] Background tasks cancelled and awaited successfully.")
            except Exception as e:
                print(f"[DIAG] Exception during background task cancellation: {e}")
            
            # Log pending asyncio tasks/coroutines before engine disposal
            pending_tasks = [t for t in asyncio.all_tasks() if not t.done()]
            print(f"[SHUTDOWN] Pending asyncio tasks before engine disposal: {len(pending_tasks)}")
            for t in pending_tasks:
                print(f"[SHUTDOWN] Pending task: {t}")
            
            # Explicitly close/await all AsyncSession objects before engine disposal
            import gc
            session_objs = []
            for obj in gc.get_objects():
                if type(obj).__name__ == "AsyncSession":
                    session_objs.append(obj)
            if session_objs:
                print(f"[SHUTDOWN] Closing {len(session_objs)} AsyncSession objects before engine disposal...")
                close_tasks = []
                for session in session_objs:
                    try:
                        print(f"[SHUTDOWN] Closing AsyncSession: {session}")
                        close_tasks.append(session.close())
                    except Exception as e:
                        print(f"[SHUTDOWN] Error closing AsyncSession: {e}")
                if close_tasks:
                    try:
                        await asyncio.gather(*close_tasks, return_exceptions=True)
                        print("[DIAG] AsyncSession objects closed and awaited successfully.")
                    except Exception as e:
                        print(f"[DIAG] Exception during AsyncSession close: {e}")
                print("[SHUTDOWN] All AsyncSession objects closed and awaited.")
            
            # Wait for all DB-related tasks to finish before disposing engine
            db_tasks = [t for t in pending_tasks if hasattr(t, "_coro") and "sqlalchemy" in str(t._coro)]
            if db_tasks:
                print(f"[SHUTDOWN] Awaiting {len(db_tasks)} unfinished DB tasks before engine disposal...")
                try:
                    await asyncio.gather(*db_tasks, return_exceptions=True)
                    print("[DIAG] DB tasks awaited successfully.")
                except Exception as e:
                    print(f"[DIAG] Exception during DB task await: {e}")
                print("[SHUTDOWN] All DB tasks awaited.")
            
            # Dispose SQLAlchemy engine before closing event loop
            try:
                print("[SHUTDOWN] Disposing SQLAlchemy engine before shutdown...")
                await engine.dispose()
                print("[SHUTDOWN] Engine disposed successfully.")
            except Exception as e:
                print(f"[SHUTDOWN] Error disposing engine: {e}")
            
            # Explicitly delete references and run garbage collection
            try:
                print("[SHUTDOWN] Deleting references to AsyncSession/engine...")
                for session in session_objs:
                    del session
                del session_objs
                del engine
            except Exception as e:
                print(f"[SHUTDOWN] Error deleting references: {e}")
            
            gc.collect()
            print("[SHUTDOWN] Garbage collected. Checking for lingering AsyncSession/engine references...")
            lingering_sessions = 0
            lingering_engines = 0
            for obj in gc.get_objects():
                if type(obj).__name__ == "AsyncSession":
                    print(f"[WARNING] Lingering AsyncSession detected after shutdown: {obj}")
                    lingering_sessions += 1
                if type(obj).__name__ == "AsyncEngine":
                    print(f"[WARNING] Lingering AsyncEngine detected after shutdown: {obj}")
                    lingering_engines += 1
            print(f"[SHUTDOWN] Lingering AsyncSession objects: {lingering_sessions}, AsyncEngine objects: {lingering_engines}")
            
            print("[SHUTDOWN] Shutdown sequence complete. Closing bot...")
            try:
                await orig_close()
                print("[DIAG] orig_close() completed without event loop error.")
            except Exception as e:
                print(f"[DIAG] Exception during bot close: {e}")
        bot.close = safe_close

        # Handle SIGTERM for graceful shutdown
        import signal
        def handle_sigterm(*_):
            print("SIGTERM received: shutting down Discord bot gracefully...")
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                loop.create_task(bot.close())
        signal.signal(signal.SIGTERM, handle_sigterm)

        try:
            bot.run(DISCORD_TOKEN)
        finally:
            # Remove lock file on shutdown
            remove_lock_file(LOCK_FILE_PATH)