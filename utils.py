import curses
import os
import subprocess
import sys
import message_win
import re

# Constants
URL_PATTERN = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
CTRL_D = 4
CTRL_N = 14
BACKSPACE_KEYS = (curses.KEY_BACKSPACE, 127, '\b', 546, 8)
ARROW_LEFT = (curses.KEY_LEFT, 452)
ARROW_RIGHT = (curses.KEY_RIGHT, 454)

# Input handling
def wrap_text(text, width):
    """Wrap text to fit within the given width."""
    wrapped_lines = []
    for line in text.split('\n'):
        while len(line) > width:
            wrapped_lines.append(line[:width])
            line = line[width:]
        wrapped_lines.append(line)
    return wrapped_lines

def sanitize_input_char(ch):
    """Convert special characters to their string representation."""
    if 32 <= ch <= 126:  # Handle printable ASCII characters
        return chr(ch)
    return ''

def is_valid_url(url):
    """Basic URL validation using regex."""
    return re.match(URL_PATTERN, url) is not None

# System operations
def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    curses.endwin()
    sys.exit(0)

def update_repo():
    """Run the update script to fetch the latest code from GitHub.
    
    On Windows, uses git.exe if available in PATH.
    On Unix systems, uses git directly.
    """
    
    if os.name == 'nt':  # Windows
        try:
            # Check if git is available in PATH
            subprocess.run(["git", "--version"], check=True, capture_output=True)
            # If git exists, proceed with git pull
            subprocess.run(["git", "pull"], check=True)
            message_win.print("Repository updated successfully.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            message_win.print("Git not found in PATH. Skipping update...")
            message_win.print("Proceeding with the current version...")
            return
    try:
        # Git pull to get latest code
        subprocess.run(["git", "pull"], check=True)
        message_win.print("Repository updated successfully.")
    except subprocess.CalledProcessError as e:
        message_win.print(f"Failed to update repository: {e}")
        message_win.print("Proceeding with the current version...")
