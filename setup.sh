#!/bin/bash

# Discord AI Bot Setup Script for Unix/Linux/Mac
# This script automates the setup process for the Discord AI Bot

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

echo "================================================"
echo "  Discord AI Bot - Automated Setup"
echo "================================================"
echo ""

# Check if Docker is installed
print_info "Checking if Docker is installed..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first:"
    echo "  Visit: https://docs.docker.com/get-docker/"
    exit 1
fi
print_success "Docker is installed"

# Check if Docker is running
print_info "Checking if Docker is running..."
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi
print_success "Docker is running"

# Check if Python 3.8+ is installed
print_info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher:"
    echo "  Visit: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python $PYTHON_VERSION is installed, but Python 3.8 or higher is required."
    exit 1
fi
print_success "Python $PYTHON_VERSION is installed"

# Create virtual environment
print_info "Creating Python virtual environment..."
if [ -d "venv" ]; then
    print_info "Virtual environment already exists, skipping creation"
else
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
print_success "pip upgraded"

# Install dependencies
print_info "Installing dependencies from requirements.txt..."
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found!"
    exit 1
fi
pip install -r requirements.txt > /dev/null 2>&1
print_success "Dependencies installed"

# Copy .env.example to .env if .env doesn't exist
print_info "Setting up environment configuration..."
if [ -f ".env" ]; then
    print_info ".env file already exists, skipping copy"
else
    if [ ! -f ".env.example" ]; then
        print_error ".env.example not found!"
        exit 1
    fi
    cp .env.example .env
    print_success ".env file created from .env.example"
    print_info "IMPORTANT: Please edit .env file and add your configuration values"
fi

# Start Docker Compose
print_info "Starting PostgreSQL with Docker Compose..."
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found!"
    exit 1
fi
docker-compose up -d
print_success "PostgreSQL container started"

# Wait for PostgreSQL to be ready
print_info "Waiting for PostgreSQL to be ready..."
sleep 5
print_success "PostgreSQL should be ready"

# Run database setup script
print_info "Initializing database..."
if [ ! -f "setup_db.py" ]; then
    print_error "setup_db.py not found!"
    exit 1
fi
python setup_db.py
print_success "Database initialized"

echo ""
echo "================================================"
print_success "Setup completed successfully!"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Edit the .env file and add your configuration:"
echo "     - DISCORD_BOT_TOKEN (from Discord Developer Portal)"
echo "     - OPENAI_API_KEY (from OpenAI)"
echo "     - GITHUB_TOKEN (from GitHub Settings)"
echo ""
echo "  2. Activate the virtual environment (if not already active):"
echo "     source venv/bin/activate"
echo ""
echo "  3. Start the Discord bot:"
echo "     python discord_bot.py"
echo ""
echo "  4. To stop PostgreSQL later:"
echo "     docker-compose down"
echo ""
print_info "For more information, see README.md"