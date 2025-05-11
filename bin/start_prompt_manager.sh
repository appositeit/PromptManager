#!/bin/bash

# Wrapper script to start the Prompt Manager
# Checks for the existence of the venv, creates it if it doesn't exist,
# then runs the server

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Prompt Manager...${NC}"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    echo -e "${YELLOW}Upgrading pip...${NC}"
    pip install --upgrade pip
    
    # Install dependencies
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}Virtual environment setup complete!${NC}"
else
    # Activate virtual environment
    source venv/bin/activate
    echo -e "${GREEN}Using existing virtual environment.${NC}"
fi

# Ensure data directories exist
mkdir -p data/prompts
mkdir -p data/sessions
mkdir -p logs

# Create user config directory if it doesn't exist
USER_CONFIG_DIR=~/.prompt_manager
if [ ! -d "$USER_CONFIG_DIR" ]; then
    echo -e "${YELLOW}Creating user config directory...${NC}"
    mkdir -p "$USER_CONFIG_DIR/prompts"
    echo -e "${GREEN}User config directory created.${NC}"
fi

# Set up Python path
export PYTHONPATH=$PROJECT_ROOT:$PROJECT_ROOT/src:$PYTHONPATH

# Run the server
echo -e "${GREEN}Starting server...${NC}"
exec python3 bin/run_prompt_manager.py "$@"
