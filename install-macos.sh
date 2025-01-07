#!/bin/bash

# Check for Homebrew and install if not found
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Update Homebrew
echo "Updating Homebrew..."
brew update

# Install Python 3 if not already installed
echo "Installing Python 3..."
brew install python

# Check if the installation was successful
if ! command -v python3 &> /dev/null; then
    echo "Python installation failed!"
    exit 1
fi

# Create a virtual environment
echo "Creating a virtual environment..."
python3 -m venv .venv

# Activate the virtual environment
echo "Activating the virtual environment..."
source .venv/bin/activate

# Create requirements.txt if it doesn't exist
cat <<EOL > requirements.txt
jsonschema
feedparser
openai
keyring
requests
packaging
pygooglenews
EOL

# Install required packages
echo "Installing required packages..."
pip install --upgrade pip
pip install -r requirements.txt

cat <<EOL > start.sh
source .venv/bin/activate
python ./ednasg.py
EOL

chmod +x ./start.sh

# Print completion message
echo "Installation complete!"
echo "You can run your program now!"
echo "Run these commands: source .venv/bin/activate"
echo "                    python ./ednasg.py"
echo "You may also just be able to run ./start.sh"
