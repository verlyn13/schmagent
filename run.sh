#!/bin/bash
# Run script for Schmagent

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Running setup script..."
    ./setup_venv.sh
fi

# Activate virtual environment
source .venv/bin/activate

# Run the application
python -m schmagent 