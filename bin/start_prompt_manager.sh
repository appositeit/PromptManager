#!/bin/bash
# Start script for the Prompt Manager
# This script handles virtual environment setup, path configuration, and server startup

set -e

# Default mode is foreground
BACKGROUND_MODE=false
PORT="8095" # Default port

# Parse command-line arguments
while getopts ":bp:" opt; do
  case ${opt} in
    b )
      BACKGROUND_MODE=true
      ;;
    p )
      PORT=$OPTARG
      ;;
    \? )
      echo "Invalid option: -$OPTARG" 1>&2
      exit 1
      ;;
    : )
      echo "Invalid option: -$OPTARG requires an argument" 1>&2
      exit 1
      ;;
  esac
done
shift $((OPTIND -1))

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_ROOT/artifacts/logs/server.pid"

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

# Change to project directory
cd "$PROJECT_ROOT"

# Create artifacts/logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/artifacts/logs"

MAIN_LOG_FILE="$PROJECT_ROOT/artifacts/logs/prompt_manager.log" # Symlink target
TIMESTAMPED_LOG_FILE="$PROJECT_ROOT/artifacts/logs/prompt_manager_$(date +'%Y%m%d%H%M%S').log"

# Symlink management: 
# - If in foreground, always create/update symlink to new timestamped log.
# - If in background, only create symlink if it doesn't exist (points to MAIN_LOG_FILE where nohup appends).
if [ "$BACKGROUND_MODE" = false ]; then
    echo "Foreground mode: Creating/updating $MAIN_LOG_FILE symlink to $TIMESTAMPED_LOG_FILE"
    rm -f "$MAIN_LOG_FILE"
    ln -s "$TIMESTAMPED_LOG_FILE" "$MAIN_LOG_FILE"
else
    if [ ! -L "$MAIN_LOG_FILE" ]; then
        # If background mode and no symlink, it means nohup will create MAIN_LOG_FILE directly.
        # For consistency, we could touch it or symlink it to itself, but nohup handles creation.
        echo "Background mode: $MAIN_LOG_FILE will be used directly by nohup."
        # If you want a symlink even for background to a timestamped file initially, that needs more logic.
        # For now, background logs directly to MAIN_LOG_FILE if it becomes a regular file via nohup.
    fi
fi

# Set up host-specific virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Setting up host-specific virtual environment for $HOST: $VENV_DIR"
    python -m venv "$VENV_DIR"
    
    echo "Installing dependencies..."
    . "$VENV_DIR/bin/activate" # Using . for POSIX compliance
    pip install -r "$PROJECT_ROOT/requirements.txt"
else
    echo "Using existing host-specific virtual environment: $VENV_DIR"
    . "$VENV_DIR/bin/activate" # Using . for POSIX compliance
fi

# Check for existing server using the PID file first, then port
if [ -f "$PID_FILE" ]; then
    if ps -p $(cat "$PID_FILE") > /dev/null; then
        # Further check if the command matches what we expect for our server
        if ps -o cmd= -p $(cat "$PID_FILE") | grep -q "python -m src.server.*--port $PORT"; then
            echo "Server is already running (PID $(cat "$PID_FILE"), command matches). Exiting."
            exit 1
        else
            echo "PID $(cat "$PID_FILE") from $PID_FILE is running but command does not match. Stale/incorrect PID file?"
            # Consider removing stale PID file if command doesn't match, or proceed to port check
        fi
    else
        echo "Stale PID file found ($PID_FILE for PID $(cat "$PID_FILE")). Process not running. Removing $PID_FILE."
        rm -f "$PID_FILE"
    fi
fi

# Check for existing server by port as a fallback or if PID check was inconclusive
if netstat -tuln | grep -q ":$PORT "; then
    echo "Server is already running on port $PORT (found by netstat, PID check might have been inconclusive or PID file was missing/stale)."
    echo "To manage this server, please use stop_prompt_manager.sh or check manually."
    exit 1
fi

# Server starting logic
if [ "$BACKGROUND_MODE" = true ]; then
  echo "Starting Prompt Manager in background on http://0.0.0.0:$PORT"
  echo "Output will be logged to $MAIN_LOG_FILE"
  # Activate venv for nohup environment if not already inherited (though `.` above should suffice for current shell)
  # The `env PYTHONPATH=...` is good. `cd` to project root is also good.
  nohup env PYTHONPATH="$PROJECT_ROOT" "$VENV_DIR/bin/python" -m src.server --host 0.0.0.0 --port "$PORT" >> "$MAIN_LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  echo "Server started in background with PID $(cat "$PID_FILE")."
  sleep 1 # Give it a moment 
else
  echo "Starting Prompt Manager in foreground on http://0.0.0.0:$PORT"
  echo "Logging to $TIMESTAMPED_LOG_FILE (symlinked by $MAIN_LOG_FILE)"
  # Use exec to replace the shell process with the python process
  exec env PYTHONPATH="$PROJECT_ROOT" "$VENV_DIR/bin/python" -m src.server --host 0.0.0.0 --port "$PORT" 2>&1 | tee -a "$TIMESTAMPED_LOG_FILE"
fi
