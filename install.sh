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

# Create a directory for the project
PROJECT_DIR="ednasg"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Creating project directory: $PROJECT_DIR"
    mkdir $PROJECT_DIR
fi

cd $PROJECT_DIR

# Create a virtual environment
echo "Creating a virtual environment..."
python3 -m venv venv

# Activate the virtual environment
echo "Activating the virtual environment..."
source venv/bin/activate

# Create requirements.txt if it doesn't exist
cat <<EOL > requirements.txt
feedparser
openai
keyring
EOL

# Install required packages
echo "Installing required packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Print completion message
echo "Installation complete! Your virtual environment is ready."
echo "Activate it with: source venv/bin/activate"
echo "You can run your program now!"
echo "Run with: python ./ednasg.py"
