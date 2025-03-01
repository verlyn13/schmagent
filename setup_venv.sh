#!/bin/bash
# Setup script for Schmagent development environment

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Schmagent development environment...${NC}"

# Check if Python 3.13 is installed
if ! command -v python3.13 &> /dev/null; then
    echo -e "${RED}Python 3.13 is not installed. Please install it first.${NC}"
    echo -e "On Fedora: ${YELLOW}sudo dnf install python3.13${NC}"
    echo -e "On Ubuntu: ${YELLOW}sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt update && sudo apt install python3.13 python3.13-venv python3.13-dev${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${GREEN}Creating virtual environment with Python 3.13...${NC}"
    python3.13 -m venv .venv
else
    echo -e "${YELLOW}Virtual environment already exists.${NC}"
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source .venv/bin/activate

# Upgrade pip
echo -e "${GREEN}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -r requirements.txt

# Install development dependencies if requested
if [ "$1" == "--dev" ]; then
    echo -e "${GREEN}Installing development dependencies...${NC}"
    pip install -r requirements.txt[dev]
fi

# Create necessary directories
echo -e "${GREEN}Creating necessary directories...${NC}"
mkdir -p ~/.config/schmagent
mkdir -p ~/.local/share/schmagent
mkdir -p ~/.secrets/schmagent

# Create API keys file if it doesn't exist
if [ ! -f ~/.secrets/schmagent/api_keys.json ]; then
    echo -e "${GREEN}Creating API keys file...${NC}"
    echo '{}' > ~/.secrets/schmagent/api_keys.json
    chmod 600 ~/.secrets/schmagent/api_keys.json
fi

# Create symbolic link to system GTK libraries
echo -e "${GREEN}Creating symbolic link to system GTK libraries...${NC}"
if [ ! -d ".venv/lib/python3.13/site-packages/gi" ]; then
    ln -s /usr/lib/python3/dist-packages/gi .venv/lib/python3.13/site-packages/
fi

echo -e "${GREEN}Setup complete!${NC}"
echo -e "To activate the virtual environment, run: ${YELLOW}source .venv/bin/activate${NC}"
echo -e "To run the application, run: ${YELLOW}python -m schmagent${NC}" 