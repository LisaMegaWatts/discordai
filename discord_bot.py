import discord
from discord.ext import commands
import os
import openai
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Base
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime
import asyncio
import sys

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/ai_ide_db")
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Load Discord token from environment variable or config file
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="/", intents=intents)
scheduler = AsyncIOScheduler()

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

@bot.event
async def on_message(message):
    # Respond to @mentions and DMs
    if message.author == bot.user:
        return
    if bot.user in message.mentions or isinstance(message.channel, discord.DMChannel):
        await message.channel.send("Hello! Use `/request-feature`, `/generate-image`, or `/status`.")
    await bot.process_commands(message)

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
        await create_reflection_log(session, "system", summary)

    # Post to Discord channel (stub: channel_id from env)
    channel_id = int(os.getenv("REFLECTION_CHANNEL_ID", "0"))
    if channel_id:
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(summary)

@bot.command(name="request-feature")
async def request_feature(ctx):
    # Example: extract title/description from user message (MVP: prompt for input)
    feature_title = "Sample Feature"
    feature_description = "Sample description from Discord request."
    discord_link = ctx.message.jump_url

    from github_integration import create_feature_branch_and_pr

    pr_url = create_feature_branch_and_pr(feature_title, feature_description, discord_link)
    await ctx.send(f"Feature request received. PR created: {pr_url}")

@bot.command(name="generate-image")
async def generate_image(ctx, *, prompt: str = None):
    if not prompt:
        await ctx.send("Please provide a prompt. Usage: `/generate-image <prompt>`")
        return

    await ctx.send(f"Generating image for prompt: `{prompt}` ...")
    try:
        # Call DALL-E API
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="512x512"
        )
        image_url = response['data'][0]['url']

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
                    await ctx.send(f"Image generated and saved: {filepath}")
                    await ctx.send(file=discord.File(filepath))
                else:
                    await ctx.send("Failed to download generated image.")
    except Exception as e:
        await ctx.send(f"Image generation failed: {e}")

@bot.command(name="get-image")
async def get_image(ctx, image_id: int = None):
    """Retrieve a generated image by ID or latest for the user."""
    async with AsyncSessionLocal() as db_session:
        from crud import get_generated_image
        user_id = str(ctx.author.id)
        if image_id:
            img = await get_generated_image(db_session, image_id)
            if not img or img.user_id != user_id:
                await ctx.send("Image not found or access denied.")
                return
        else:
            # Get latest image for user
            from sqlalchemy.future import select
            from models import GeneratedImage
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
    await ctx.send("Bot is running and ready. (MVP stub)")

@bot.command(name="submit-feature")
async def submit_feature(ctx, *, arg: str = None):
    """
    Usage: /submit-feature <title> | <description>
    """
    if not arg or "|" not in arg:
        await ctx.send("Usage: `/submit-feature <title> | <description>`")
        return
    title, description = [x.strip() for x in arg.split("|", 1)]
    discord_link = ctx.message.jump_url
    user_id = str(ctx.author.id)

    # Store feature request in PostgreSQL
    from crud import create_feature_request
    async with AsyncSessionLocal() as session:
        fr = await create_feature_request(session, user_id, title, description)

    # Create GitHub PR
    from github_integration import create_feature_branch_and_pr
    pr_url = create_feature_branch_and_pr(title, description, discord_link)

    # Notify Discord channel
    await ctx.send(f"Feature request submitted and stored. PR created: {pr_url}")

if __name__ == "__main__":
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
        
        # Schedule daily reflection at 8:00 AM America/New_York
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
        bot.run(DISCORD_TOKEN)