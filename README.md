# DiscordAI Repository

## Overview
DiscordAI is a Python-based Discord bot with integrated GitHub and database support. It is designed for extensibility, automation, and image API integration.

## Architecture

- **discord_bot.py**: Main entry point for the Discord bot.
- **github_integration.py**: Handles GitHub API interactions.
- **models.py**: Database models.
- **crud.py**: Database CRUD operations.
- **migrations/**: SQL migration scripts.

## Setup

1. **Clone the repository:**
   ```sh
   git clone https://github.com/yourusername/discordai.git
   cd discordai
   ```

2. **Create and activate a virtual environment:**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   - Copy `.env.example` to `.env` and fill in your secrets.

5. **Run migrations:**
   - Apply SQL scripts in `migrations/` to your database.

6. **Start the bot:**
   ```sh
   python discord_bot.py
   ```

## Usage

- **Start Bot:** `python discord_bot.py`
- **Database Migration:** Apply scripts in `migrations/`
- **GitHub Integration:** Configure your GitHub token in `.env`
- **Image API:** Set your image API key in `.env`

## Commands

- Bot commands are defined in `discord_bot.py`.
- GitHub automation commands are in `github_integration.py`.

## Environment Variables

See `.env.example` for required variables:
- `DISCORD_TOKEN`
- `DATABASE_URI`
- `GITHUB_TOKEN`
- `IMAGE_API_KEY`
- Any other secrets required by integrations.

## Development

- Use VSCode for development.
- Python 3.8+ recommended.
- All main modules are importable and tested for sanity.

## License

MIT