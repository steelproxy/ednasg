import curses
import os
import subprocess
import sys
import message_win
import re

# Constants
URL_PATTERN = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'  # Pattern for validating URLs
CTRL_D = 4                                           # ASCII value for Ctrl+D
CTRL_N = 14                                          # ASCII value for Ctrl+N
BACKSPACE_KEYS = (curses.KEY_BACKSPACE, 127, '\b', 8)  # Various backspace key codes
ARROW_LEFT = (curses.KEY_LEFT, 452)                    # Left arrow key codes
ARROW_RIGHT = (curses.KEY_RIGHT, 454)                  # Right arrow key codes

# Input handling functions
def wrap_text(text, width):  # Wraps text to fit window width
    """Wrap text to fit within the given width."""
    wrapped_lines = []
    for line in text.split('\n'):  # Process each line separately
        while len(line) > width:   # Split lines longer than width
            wrapped_lines.append(line[:width])
            line = line[width:]
        wrapped_lines.append(line)
    return wrapped_lines

def sanitize_input_char(ch):  # Convert special chars to strings
    """Convert special characters to their string representation."""
    if 32 <= ch <= 126:      # Check if char is printable ASCII
        return chr(ch)
    return ''

def is_valid_url(url):  # Check if URL format is valid
    """Basic URL validation using regex."""
    return re.match(URL_PATTERN, url) is not None

# System operation functions
def signal_handler(sig, frame):  # Handle program termination
    """Handle Ctrl+C gracefully."""
    curses.endwin()            # Restore terminal settings
    sys.exit(0)                # Exit cleanly

def update_repo():  # Update code from GitHub
    """Run the update script to fetch the latest code from GitHub."""
        # determine if application is a script file or frozen exe
    if getattr(sys, 'frozen', False):
        return # TODO: add binary updater 
    else:
        try:
            subprocess.run(["git", "--version"], 
                        check=True, capture_output=True)  # Verify git installation
            subprocess.run(["git", "pull"], check=True)     # Pull latest changes
            message_win.print("Repository updated successfully.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            message_win.print("Git not found in PATH. Skipping update...")
            message_win.print("Proceeding with the current version...")