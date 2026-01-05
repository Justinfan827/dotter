#!/bin/bash

# Pull latest code
git pull

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv and install pygame if needed
source venv/bin/activate
pip install pygame --quiet

# Run the game
python game.py
