# DiscordAI Repository

## Overview
DiscordAI is an intelligent, conversational Discord bot powered by Claude AI. It features natural language understanding, semantic intent detection, conversation memory, and seamless integrations with GitHub and image generation APIs. The bot can understand what you want through natural conversation while maintaining backward compatibility with traditional slash commands.

## 🌟 Conversational Features (v2.0)

### Talk Naturally to Your Bot
No more memorizing command syntax! Just talk to the bot like you would to a person:

**Before (v1.x)**:
```
/generate-image create a photorealistic sunset over mountains
```

**Now (v2.0)**:
```
"Can you create an image of a sunset over mountains? Make it photorealistic."
```

### Key Features

- **🧠 Semantic Intent Detection**: Understands what you want through natural language powered by Claude AI
- **💬 Conversation Memory**: Remembers context from your previous messages (30-minute sessions)
- **😊 Natural Responses**: Engages in friendly conversation with appropriate emoji usage
- **🎯 Intent-Based Actions**: Automatically routes requests to the right functionality
- **⚡ Performance Optimized**: Response caching, parallel processing, and quick templates
- **📊 Analytics & Logging**: Tracks intent detection accuracy and usage patterns
- **🔄 Backward Compatible**: All original slash commands still work perfectly

### Supported Intents

| Intent | Description | Example |
|--------|-------------|---------|
| **Generate Image** | Create AI-generated images | "draw me a cat wearing a wizard hat" |
| **Submit Feature** | Request new features with automatic GitHub PR creation | "I'd like to add dark mode support" |
| **Get Status** | Check bot and request status | "are you working?" |
| **Get Help** | Learn about capabilities | "what can you do?" |
| **General Conversation** | Natural chat interaction | "hello!", "thanks!" |
| **Action Query** | Retrieve previous results | "show me my last image" |

### Natural Language Examples

```
✨ Image Generation:
"create a cyberpunk cityscape at night with neon lights"
"draw a cute robot in anime style"
"generate a professional logo with a mountain theme"

💡 Feature Requests:
"add support for voice message transcription"
"I want to be able to schedule reminders"
"feature request: export conversation history"

💬 Conversations:
"hello! what can you help me with?"
"that's awesome, thanks!"
"show me what you created yesterday"
```

### Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete guide to interacting with the bot
- **[Testing Guide](docs/TESTING_GUIDE.md)** - Comprehensive testing instructions
- **[Architecture Documentation](docs/conversational_bot_architecture.md)** - Technical implementation details
- **[Changelog](CHANGELOG.md)** - Version history and updates

## Architecture

### Core Components

- **[`discord_bot.py`](discord_bot.py)**: Main entry point with conversational message processing
- **[`github_integration.py`](github_integration.py)**: GitHub API interactions for feature requests
- **[`models.py`](models.py)**: Database models including conversation tables
- **[`crud.py`](crud.py)**: Database CRUD operations
- **[`setup_db.py`](setup_db.py)**: Automated database initialization script
- **`migrations/`**: SQL migration scripts
  - [`001_create_tables.sql`](migrations/001_create_tables.sql) - Original tables
  - [`002_add_conversation_tables.sql`](migrations/002_add_conversation_tables.sql) - Conversational features

### Persistent Memory & Session Management

- **[`services/conversation_service.py`](services/conversation_service.py)**: Manages persistent memory, session state, and context retention using Redis and database fallback.
- **[`services/redis_utils.py`](services/redis_utils.py)**: Handles Redis integration for fast session and message history storage.
- **Session Management**: Sessions are tracked and reliably maintained across bot restarts, Redis flushes, and multi-instance deployments. Session timeouts and context windows are enforced for consistent user experience.
- **Bot Reliability**: Recovery logic ensures seamless operation during failures. The bot is resilient to Redis outages and database reconnections.

### Security & History Rewrite

- **Secrets Removal**: All secrets have been removed from history and configuration files. Only environment variables are used for sensitive data.
- **History Rewrite**: Git history was rewritten to remove secrets. If you previously cloned the repository, re-pull or re-clone to ensure secrets are not present.

### New Services (v2.0)

- **[`services/intent_service.py`](services/intent_service.py)**: Semantic intent detection using Claude
- **[`services/conversation_service.py`](services/conversation_service.py)**: Conversation context and session management
- **[`services/response_service.py`](services/response_service.py)**: Intelligent response generation
- **[`services/cache_service.py`](services/cache_service.py)**: Response caching for performance
- **[`services/performance_utils.py`](services/performance_utils.py)**: Performance optimization utilities

### Database Schema

**Original Tables**:
- `feature_requests` - User feature submissions
- `generated_images` - AI-generated image metadata
- `scheduled_tasks` - Task scheduling
- `reflection_logs` - Daily reflection summaries

**New Tables (v2.0)**:
- `conversation_sessions` - User conversation sessions
- `conversation_history` - Message history for context
- `user_preferences` - User customization settings
- `intent_logs` - Intent detection analytics

## Prerequisites

Before installing DiscordAI, ensure you have the following installed on your system:

- **Docker** (required for PostgreSQL database)
  - [Download Docker Desktop](https://docs.docker.com/get-docker/)
  - Verify installation: `docker --version`
  - Ensure Docker is running before setup

- **Python 3.8 or higher** (required)
  - [Download Python](https://www.python.org/downloads/)
  - Verify installation: `python --version` or `python3 --version`

- **Git** (for cloning the repository)
  - [Download Git](https://git-scm.com/downloads/)

## Quick Start (Recommended)

The fastest way to get DiscordAI up and running is using our automated setup scripts:

### For Unix/Linux/Mac:

```bash
# Clone the repository
git clone https://github.com/yourusername/discordai.git
cd discordai

# Run the automated setup script
chmod +x setup.sh
./setup.sh
```

### For Windows:

```cmd
REM Clone the repository
git clone https://github.com/yourusername/discordai.git
cd discordai

REM Run the automated setup script
setup.bat
```

### What the Setup Script Does:

1. ✓ Verifies Docker and Python are installed and running
2. ✓ Creates a Python virtual environment
3. ✓ Installs all required dependencies from [`requirements.txt`](requirements.txt)
4. ✓ Creates a [`.env`](.env) file from [`.env.example`](.env.example)
5. ✓ Starts PostgreSQL database using Docker Compose
6. ✓ Initializes database tables automatically
7. ✓ Provides clear next steps

### After Setup:

1. **Configure your environment variables** by editing the [`.env`](.env) file:
   ```bash
   DISCORD_TOKEN=your_discord_token_here
   GITHUB_TOKEN=your_github_token_here
   IMAGE_API_KEY=your_image_api_key_here
   ```

2. **Activate the virtual environment** (if not already active):
   ```bash
   # Unix/Linux/Mac:
   source venv/bin/activate
   
   # Windows:
   venv\Scripts\activate.bat
   ```

3. **Start the Discord bot**:
   ```bash
   python discord_bot.py
   ```

## Manual Installation (Alternative)

If you prefer more control over the installation process, follow these manual steps:

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/discordai.git
cd discordai
```

### 2. Create and Activate Virtual Environment

```bash
# Unix/Linux/Mac:
python3 -m venv venv
source venv/bin/activate

# Windows:
python -m venv venv
venv\Scripts\activate.bat
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a [`.env`](.env) file by copying the example:

```bash
# Unix/Linux/Mac:
cp .env.example .env

# Windows:
copy .env.example .env
```

Then edit the [`.env`](.env) file and add your configuration values.

### 5. Start PostgreSQL with Docker Compose

```bash
docker-compose up -d
```

### 6. Initialize the Database

Wait a few seconds for PostgreSQL to start, then run:

```bash
python setup_db.py
```

### 7. Start the Bot

```bash
python discord_bot.py
```

## Database Setup

### Automatic Initialization

The database is automatically initialized when you run [`setup_db.py`](setup_db.py) or use the automated setup scripts. The initialization process:

1. **Validates configuration**: Checks that `DATABASE_URL` is properly set
2.  **Waits for PostgreSQL**: Automatically retries connection for up to 30 seconds
3. **Tests connection**: Verifies connectivity and displays database version
4. **Creates tables**: Uses SQLAlchemy models to create all necessary tables
5. **Confirms success**: Lists all created tables

### Database Configuration

The database connection is configured through the `DATABASE_URL` environment variable in your [`.env`](.env) file:

```bash
DATABASE_URL=postgresql+asyncpg://ai_ide_user:ai_ide_password@localhost:5432/ai_ide_db
```

**Connection String Format:**
```
postgresql+asyncpg://[username]:[password]@[host]:[port]/[database_name]
```

**Default Credentials** (from [`docker-compose.yml`](docker-compose.yml)):
- **Username**: `ai_ide_user`
- **Password**: `ai_ide_password`
- **Database**: `ai_ide_db`
- **Host**: `localhost`
- **Port**: `5432`

> **Security Note**: Change the default password in production environments by modifying [`docker-compose.yml`](docker-compose.yml) and updating your [`.env`](.env) file accordingly.

### Verifying Database Status

**Check if PostgreSQL is running:**
```bash
docker ps
```

You should see a container named `ai_ide_postgres` with status "Up".

**View PostgreSQL logs:**
```bash
docker-compose logs postgres
```

**Test database connection:**
```bash
python setup_db.py
```

This will validate the connection and display database information.

### Accessing PostgreSQL Directly

If you need to access the PostgreSQL database directly for debugging or manual queries:

**Using Docker:**
```bash
docker exec -it ai_ide_postgres psql -U ai_ide_user -d ai_ide_db
```

**Using psql client (if installed locally):**
```bash
psql -h localhost -p 5432 -U ai_ide_user -d ai_ide_db
```

**Common PostgreSQL Commands:**
- `\dt` - List all tables
- `\d table_name` - Describe table structure
- `\q` - Exit psql

## Docker Compose Usage

### Starting the Database

```bash
# Start PostgreSQL in detached mode (background)
docker-compose up -d

# Start PostgreSQL in foreground (see logs)
docker-compose up
```

### Stopping the Database

```bash
# Stop containers (keeps data)
docker-compose down

# Stop and remove volumes (deletes all data)
docker-compose down -v
```

### Viewing Logs

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View only PostgreSQL logs
docker-compose logs postgres

# Tail last 50 lines
docker-compose logs --tail=50
```

### Restarting the Database

```bash
docker-compose restart
```

## Environment Variables

See [`.env.example`](.env.example) for all required variables:

### Required Variables

- **`DISCORD_TOKEN`**: Your Discord bot token from the [Discord Developer Portal](https://discord.com/developers/applications)
- **`ANTHROPIC_API_KEY`**: Anthropic API key for Claude AI (conversational features) - [Get API Key](https://console.anthropic.com/)
- **`DATABASE_URL`**: PostgreSQL connection string (set automatically by Docker Compose)

### Optional Variables

- **`OPENROUTER_API_KEY`**: API key for OpenRouter image generation service
- **`OPENROUTER_IMAGE_MODEL`**: Image generation model (default: `stabilityai/stable-diffusion-xl`)
- **`ANTHROPIC_MODEL`**: Claude model to use (default: `claude-3-5-sonnet-20241022`)
- **`GITHUB_TOKEN`**: Personal access token from [GitHub Settings](https://github.com/settings/tokens) for feature request PRs
- **`GITHUB_REPO`**: Repository in format `owner/repo` for feature requests
- **`REFLECTION_CHANNEL_ID`**: Discord channel ID for daily reflection messages

### Example `.env` File

```bash
# Required
DISCORD_TOKEN=your_discord_bot_token_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DATABASE_URL=postgresql+asyncpg://ai_ide_user:ai_ide_password@localhost:5432/ai_ide_db

# Optional - Image Generation
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_IMAGE_MODEL=stabilityai/stable-diffusion-xl

# Optional - GitHub Integration
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=username/repository

# Optional - Advanced
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
REFLECTION_CHANNEL_ID=123456789012345678
```

## Usage

- **Start Bot**: `python discord_bot.py`
- **Initialize Database**: `python setup_db.py`
- **GitHub Integration**: Configure your GitHub token in [`.env`](.env)
- **Image API**: Set your image API key in [`.env`](.env)

## Commands & Interactions

### Natural Language (Primary Method)

Just talk to the bot naturally:
- "create an image of a sunset"
- "I'd like to request a new feature"
- "what can you do?"
- "show me my last image"

See the **[User Guide](docs/USER_GUIDE.md)** for complete examples.

### Slash Commands (Backward Compatible)

| Command | Description | Example |
|---------|-------------|---------|
| `/generate-image <prompt>` | Generate an AI image | `/generate-image a mountain landscape` |
| `/submit-feature <title> \| <desc>` | Submit feature request | `/submit-feature Dark Mode \| Add theme support` |
| `/get-image [id]` | Retrieve generated image | `/get-image` or `/get-image 123` |
| `/status` | Check bot status | `/status` |
| `/request-feature` | Alternative feature submission | `/request-feature` |

## Troubleshooting

### Docker Issues

**Problem**: "Docker is not running"
```bash
# Solution: Start Docker Desktop application
# On Windows/Mac: Open Docker Desktop from Start Menu/Applications
# On Linux: sudo systemctl start docker
```

**Problem**: "Port 5432 is already in use"
```bash
# Solution: Stop other PostgreSQL instances or change the port
# Check what's using the port:
# Windows: netstat -ano | findstr :5432
# Unix/Linux/Mac: lsof -i :5432

# Change port in docker-compose.yml from "5432:5432" to "5433:5432"
# Then update DATABASE_URL to use port 5433
```

### Database Connection Issues

**Problem**: "Database connection timeout"
```bash
# Solutions:
# 1. Ensure Docker container is running: docker ps
# 2. Wait a few more seconds for PostgreSQL to initialize
# 3. Check logs: docker-compose logs postgres
# 4. Verify DATABASE_URL in .env matches docker-compose.yml credentials
```

**Problem**: "Could not connect to database"
```bash
# Solution: Restart PostgreSQL container
docker-compose restart

# If that doesn't work, rebuild:
docker-compose down
docker-compose up -d
```

### Python/Dependency Issues

**Problem**: "Module not found" errors
```bash
# Solution: Ensure virtual environment is activated and dependencies installed
source venv/bin/activate  # Unix/Linux/Mac
venv\Scripts\activate.bat  # Windows
pip install -r requirements.txt
```

**Problem**: "Permission denied" on setup.sh
```bash
# Solution: Make the script executable
chmod +x setup.sh
```

### Environment Variable Issues

**Problem**: "DATABASE_URL environment variable is not set"
```bash
# Solution: Ensure .env file exists and is properly formatted
# 1. Copy from example: cp .env.example .env
# 2. Verify DATABASE_URL is uncommented and properly set
# 3. Restart your terminal or re-activate virtual environment
```

### Getting Help

If you encounter issues not covered here:

1. Check Docker logs: `docker-compose logs`
2. Verify all prerequisites are installed and up-to-date
3. Ensure [`.env`](.env) file is properly configured
4. Review error messages carefully - they often indicate the specific issue

## Development

- Use VSCode for development
- Python 3.8+ recommended
- All main modules are importable and tested for sanity
- Database models are defined using SQLAlchemy ORM

## License

MIT