#!/bin/bash

# Setup script for Prompt Manager
# Creates virtual environment and installs dependencies

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

# Determine host-specific venv
HOST=$(hostname)
case "$HOST" in
    "mie")
        VENV_DIR="$PROJECT_ROOT/mie_venv"
        ;;
    "nara")
        VENV_DIR="$PROJECT_ROOT/nara_venv"
        ;;
    *)
        # Fallback for unknown hosts
        VENV_DIR="$PROJECT_ROOT/venv"
        echo "Warning: Unknown host '$HOST', using generic venv directory"
        ;;
esac

# Create host-specific virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating host-specific virtual environment for $HOST: $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setup complete! You can now run the prompt manager using:"
echo "  bin/run_prompt_manager.py"
