#!/bin/bash
#
# Setup script for Schmagent
# This script installs dependencies and configures the environment

set -e  # Exit immediately if a command fails

echo "=== Schmagent Setup ==="
echo "This script will set up Schmagent with all required dependencies."
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d '.' -f 1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d '.' -f 2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "ERROR: Python 3.8 or higher is required."
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

echo "Found Python $PYTHON_VERSION"

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Make scripts executable
echo "Making scripts executable..."
chmod +x run_unified.sh
chmod +x set_api_key.sh
chmod +x migrate_api_keys.sh

# Run the migration script to set up API keys structure
echo "Setting up API keys structure..."
./migrate_api_keys.sh

# Prompt for OpenAI API key
echo ""
echo "Would you like to set up your OpenAI API key now? (yes/no)"
read -r response
if [[ "$response" == "yes" ]]; then
    echo "Please enter your OpenAI API key:"
    read -r api_key
    ./set_api_key.sh openai "$api_key"
else
    echo "You can set up your API key later using:"
    echo "  ./set_api_key.sh openai your_api_key_here"
fi

echo ""
echo "=== Setup Complete ==="
echo "You can now run Schmagent using:"
echo "  ./run_unified.sh"
echo ""
echo "For more information, see the README.md file."
