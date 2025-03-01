#!/bin/bash

# This script checks and fixes the API keys file outside of Cursor's environment

# Set up path to the API keys file
API_KEYS_FILE="/home/verlyn13/.secrets/schmagent/api_keys.json"

# Check if the file exists
if [ ! -f "$API_KEYS_FILE" ]; then
    echo "API keys file not found at $API_KEYS_FILE"
    exit 1
fi

# Display file structure (without showing actual key)
echo "Current API keys file structure:"
cat "$API_KEYS_FILE" | sed -E 's/("api_key": *")[^"]*(")/"api_key": "***REDACTED***"/g'
echo ""

# Check if the OpenAI key structure is correct
if ! grep -q "\"openai\"" "$API_KEYS_FILE"; then
    echo "OpenAI configuration not found in API keys file. Adding it..."
    # Create temporary file with openai structure
    TMP_FILE=$(mktemp)
    echo "{\"openai\": {\"api_key\": \"\", \"organization_id\": \"\"}, \"anthropic\": {\"api_key\": \"\"}, \"google\": {\"api_key\": \"\", \"project_id\": \"\"}, \"openrouter\": {\"api_key\": \"\"}, \"perplexity\": {\"api_key\": \"\"}, \"elevenlabs\": {\"api_key\": \"\"}, \"local\": {\"api_key\": \"\", \"model_path\": \"\"}}" > $TMP_FILE
    mv $TMP_FILE "$API_KEYS_FILE"
    chmod 600 "$API_KEYS_FILE"
    echo "Created new API keys file with correct structure"
    
    echo "Please add your OpenAI API key manually to $API_KEYS_FILE"
    exit 1
fi

echo "API keys file structure looks good!"
echo "If you're still having issues, check:"
echo "1. The model name in .env (should be gpt-4o, gpt-4-turbo, etc.)"
echo "2. Make sure the API key is correctly entered (no extra spaces, etc.)"
echo "3. Check if your API key is valid and has access to the model you specified"

# Verify the file permissions
chmod 600 "$API_KEYS_FILE"
echo "Permissions set to 600 (owner read/write only)" 