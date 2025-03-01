#!/bin/bash
#
# Script to safely set API keys in the configuration file
# Usage: ./set_api_key.sh <provider> <key>
# Example: ./set_api_key.sh openai sk-abcdef123456

set -e  # Exit immediately if a command fails

# -- PATHS --
SECRETS_PATH="${SECRETS_PATH:-$HOME/.secrets/schmagent}"
API_KEYS_FILE="${API_KEYS_FILE:-api_keys.json}"
FULL_API_KEYS_PATH="$SECRETS_PATH/$API_KEYS_FILE"

# -- FUNCTIONS --
usage() {
    echo "Usage: $0 <provider> <api_key>"
    echo ""
    echo "Available providers:"
    echo "  openai     - OpenAI API (ChatGPT, DALL-E, etc.)"
    echo "  anthropic  - Anthropic API (Claude)"
    echo "  google     - Google AI API (Gemini)"
    echo "  openrouter - OpenRouter API"
    echo "  perplexity - Perplexity API"
    echo "  elevenlabs - ElevenLabs API (text-to-speech)"
    echo "  local      - Local model configuration"
    echo ""
    echo "Example:"
    echo "  $0 openai sk-abcdef123456"
    exit 1
}

# Check command line arguments
if [ $# -lt 2 ]; then
    usage
fi

PROVIDER="$1"
API_KEY="$2"

# Validate provider
VALID_PROVIDERS=("openai" "anthropic" "google" "openrouter" "perplexity" "elevenlabs" "local")
VALID=0
for p in "${VALID_PROVIDERS[@]}"; do
    if [ "$p" == "$PROVIDER" ]; then
        VALID=1
        break
    fi
done

if [ $VALID -eq 0 ]; then
    echo "Error: Invalid provider '$PROVIDER'"
    echo ""
    usage
fi

# Check if API keys file exists
if [ ! -f "$FULL_API_KEYS_PATH" ]; then
    echo "API keys file not found at: $FULL_API_KEYS_PATH"
    echo "Running migration script to create it..."
    ./migrate_api_keys.sh
fi

# Update the API key
echo "Setting $PROVIDER API key..."
# Use temporary file to avoid potential issues with in-place editing
TMP_FILE=$(mktemp)
jq ".$PROVIDER.api_key = \"$API_KEY\"" "$FULL_API_KEYS_PATH" > "$TMP_FILE"
mv "$TMP_FILE" "$FULL_API_KEYS_PATH"
chmod 600 "$FULL_API_KEYS_PATH"

echo "API key for $PROVIDER has been updated."
echo "You can now run the application with: ./run_unified.sh" 