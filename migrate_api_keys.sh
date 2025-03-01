#!/bin/bash
#
# Migration script for Schmagent API keys
# This script helps migrate API keys from the old setup to the new unified structure

set -e  # Exit immediately if a command fails

# -- PATHS --
SECRETS_PATH="${SECRETS_PATH:-$HOME/.secrets/schmagent}"
API_KEYS_FILE="${API_KEYS_FILE:-api_keys.json}"
FULL_API_KEYS_PATH="$SECRETS_PATH/$API_KEYS_FILE"

echo "=== Schmagent API Key Migration Tool ==="
echo "This script will help you migrate any existing API keys to the new unified structure."
echo ""

# Check if the secrets directory exists
if [ ! -d "$SECRETS_PATH" ]; then
    echo "Creating secrets directory at $SECRETS_PATH..."
    mkdir -p "$SECRETS_PATH"
    chmod 700 "$SECRETS_PATH"
fi

# Check if the API keys file already exists
if [ -f "$FULL_API_KEYS_PATH" ]; then
    echo "API keys file already exists at: $FULL_API_KEYS_PATH"
    echo "Would you like to overwrite it? (yes/no)"
    read -r response
    if [[ "$response" != "yes" ]]; then
        echo "Aborting migration. Your existing API keys file is unchanged."
        exit 0
    fi
fi

# Create a base API keys structure
echo "Creating API keys file structure..."
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

# Check for existing API keys in environment variables
if [ -n "$OPENAI_API_KEY" ]; then
    echo "Found OpenAI API key in environment variables. Migrating..."
    # Use sed to replace the empty OpenAI API key with the environment variable value
    sed -i "s/\"openai\": {\"api_key\": \"\"}/\"openai\": {\"api_key\": \"$OPENAI_API_KEY\"}/" "$FULL_API_KEYS_PATH"
fi

# Check for API keys in old shell scripts
OLD_SCRIPTS=("run_with_key.sh" "run_in_cursor.sh")
for script in "${OLD_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        echo "Checking $script for API keys..."
        # Look for OPENAI_API_KEY setting pattern
        KEY_LINE=$(grep -o "OPENAI_API_KEY=.*" "$script" 2>/dev/null || true)
        if [ -n "$KEY_LINE" ]; then
            # Extract the API key value
            API_KEY=$(echo "$KEY_LINE" | cut -d '=' -f2 | tr -d '"' | tr -d "'")
            if [ -n "$API_KEY" ] && [ "$API_KEY" != '$API_KEY' ]; then  # Skip if it's a variable reference
                echo "Found an API key in $script. Migrating..."
                sed -i "s/\"openai\": {\"api_key\": \"[^\"]*\"}/\"openai\": {\"api_key\": \"$API_KEY\"}/" "$FULL_API_KEYS_PATH"
            fi
        fi
    fi
done

echo ""
echo "Migration complete!"
echo "Your API keys are now stored in: $FULL_API_KEYS_PATH"
echo ""
echo "You can now use the unified run script:"
echo "  ./run_unified.sh"
echo ""
echo "Once you've confirmed everything is working correctly, you can safely delete the old script files:"
echo "  rm run_with_key.sh run_in_cursor.sh" 