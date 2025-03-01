#!/bin/bash
#
# Unified run script for Schmagent
# Works in both regular and Cursor environments
# Handles API keys consistently with application design

set -e  # Exit immediately if a command fails

# -- CONFIGURATION --
# Location where API keys are stored
SECRETS_PATH="${SECRETS_PATH:-$HOME/.secrets/schmagent}"
API_KEYS_FILE="${API_KEYS_FILE:-api_keys.json}"
FULL_API_KEYS_PATH="$SECRETS_PATH/$API_KEYS_FILE"

# Path setup - ensures Python can find the schmagent package
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$PYTHONPATH:$SCRIPT_DIR"

# Development settings
export LOG_LEVEL="${LOG_LEVEL:-DEBUG}"

# -- CURSOR ENVIRONMENT FIXES --
# Disable Vulkan renderer for GTK to avoid MESA-INTEL warnings
export GSK_RENDERER=cairo
export GTK_A11Y=none

# -- API KEY HANDLING --

if [ ! -f "$FULL_API_KEYS_PATH" ]; then
    mkdir -p "$SECRETS_PATH"
    chmod 700 "$SECRETS_PATH"

    echo '{
  "openai": {"api_key": ""},
  "anthropic": {"api_key": ""},
  "google": {"api_key": "", "project_id": ""},
  "openrouter": {"api_key": ""},
  "perplexity": {"api_key": ""},
  "elevenlabs": {"api_key": ""},
  "local": {"api_key": "", "model_path": ""}
}' > "$FULL_API_KEYS_PATH"
    chmod 600 "$FULL_API_KEYS_PATH"

    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    EXTRACTED_API_KEY=$(grep -o '"api_key": *"[^"]*"' "$FULL_API_KEYS_PATH" | grep -m1 -o '"[^"]*"$' | tr -d '"')

    if [ -z "$EXTRACTED_API_KEY" ] || [ "$EXTRACTED_API_KEY" == "" ]; then
        exit 1
    fi

    export OPENAI_API_KEY="$EXTRACTED_API_KEY"
fi

OPENAI_MODEL="${OPENAI_MODEL:-gpt-4o}"
export OPENAI_MODEL

echo "Using model: $OPENAI_MODEL"

# -- VIRTUAL ENVIRONMENT HANDLING --
# Check if .venv directory exists
if [ -d ".venv" ]; then
    # Activate the virtual environment
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "WARNING: No .venv directory found. Running with system Python."
fi

# -- RUN THE APPLICATION --
echo "Starting Schmagent..."
python run.py
