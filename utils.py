import curses
import os
import subprocess
import sys
import message_win
import re
import requests
import platform
import bottom_win
from packaging import version
import openai

# Application Constants
APP_NAME = "ednasg"
APP_VERSION = "v0.5"
APP_REPO = "https://api.github.com/repos/steelproxy/ednasg/releases/latest"

# Mouse scroll constants
WINDOWS_SCROLL_UP = 65536           # Windows-specific scroll up value
WINDOWS_SCROLL_DOWN = 2097152       # Windows-specific scroll down value

# Platform detection
IS_WINDOWS = platform.system().lower() == 'windows'

# Input Constants
URL_PATTERN = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'  # Pattern for validating URLs
BREAK_HOTKEY = 4                                           # ASCII value for Ctrl+D
SKIP_HOTKEY = 14                                          # ASCII value for Ctrl+N
# Set CTRL_O to the value for CTRL+W (23) on macOS
if platform.system().lower() == 'darwin':
    PGN_HOTKEY = 23  # ASCII value for Ctrl+W
else:
    PGN_HOTKEY = 15  # Default ASCII value for Ctrl+O
RESET_HOTKEY = 18                                          # ASCII value for Ctrl+R
if hasattr(curses, 'BUTTON5_PRESSED'):
    MOUSE_DOWN = curses.BUTTON5_PRESSED if not IS_WINDOWS else WINDOWS_SCROLL_DOWN # Scroll down, scroll values vary between platforms
if hasattr(curses, 'BUTTON4_PRESSED'):
    MOUSE_UP = curses.BUTTON4_PRESSED if not IS_WINDOWS else WINDOWS_SCROLL_UP     # Scroll up, scroll values vary between platforms
BACKSPACE_KEYS = (curses.KEY_BACKSPACE, 127, '\b', 8)  # Various backspace key codes
ARROW_LEFT = (curses.KEY_LEFT, 452)                    # Left arrow key codes
ARROW_RIGHT = (curses.KEY_RIGHT, 454)                  # Right arrow key codes

def wrap_text(text, width):
    """Wrap text to fit within the given width.
    
    Args:
        text: The text to wrap
        width: Maximum width for each line
        
    Returns:
        list: A list of wrapped text lines
    """
    wrapped_lines = []
    for line in text.split('\n'):  # Process each line separately
        while len(line) > width:   # Split lines longer than width
            wrapped_lines.append(line[:width])
            line = line[width:]
        wrapped_lines.append(line)
    return wrapped_lines

def sanitize_input_char(ch):
    """Convert special characters to their string representation.
    
    Args:
        ch: The character code to sanitize
        
    Returns:
        str: The sanitized character or empty string if invalid
    """
    if 32 <= ch <= 126:  # Only allow printable ASCII characters
        return chr(ch)
    return ''

def sanitize_output(str):
    """Sanitize output to ensure it is a valid string.
    
    Args:
        str: The string to sanitize
        
    Returns:   
        str: The sanitized string
    """
    return ''.join(
        sanitize_input_char(ord(char))
        for char in str
    )

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
    message_win.print_msg("Checking for updates...")
    try:
        subprocess.run(["git", "--version"],
                        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # Verify git installation
        # Pull latest changes
        result = subprocess.run(["git", "pull"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        message_win.print_msg(f"GIT OUTPUT: \"{result.stdout.strip()}\"")
        if "Already up to date." not in result.stdout:
            message_win.print_msg("Repository updated successfully.")
            # Update or install dependencies
            message_win.print_msg("Updating dependencies...")
            pip_result = subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            message_win.print_msg(f"PIP OUTPUT: \"{pip_result.stdout.strip()}\"")  # Echo pip install output
            message_win.print_msg("Dependencies updated successfully.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        message_win.print_msg("Git not found in PATH. Skipping update...")
        message_win.print_msg("Proceeding with the current version...")
    except Exception as e:
        message_win.error(f"Unexpected exception occured while updating: {e}")


def wait_for_exit():
    """Wait for user input before exiting."""
    bottom_win.print("Press any button to exit...")
    bottom_win.getch()

def _handle_exit():
    """Clean up curses and exit the application."""
    curses.endwin()
    sys.exit(0)

def _fatal_error(message):
    """Display error message and exit application.
    
    Args:
        message: The error message to display
    """
    message_win.clear()
    message_win.print(message, wrap=True)
    wait_for_exit()
    _handle_exit()

def handle_openai_error(e, prompt):
    """Handle OpenAI API errors."""
    if isinstance(e, openai.RateLimitError):
        message_win.print_msg(f"{prompt}: Rate limit reached. Please wait before trying again.")
    elif isinstance(e, openai.AuthenticationError):
        message_win.print_msg(f"{prompt}: Authentication error. Please check your API key.")
    elif isinstance(e, openai.PermissionDeniedError):
        message_win.print_msg(f"{prompt}: Permission error. Your API key may not have access to this resource.")
    elif isinstance(e, openai.BadRequestError):
        message_win.print_msg(f"{prompt}: Invalid request: {str(e)}")
    elif isinstance(e, (openai.APIError, openai.Timeout, openai.APIConnectionError)):
        message_win.print_msg(f"{prompt}: API error occurred: {str(e)}. Please try again.")
    elif isinstance(e, openai.APIStatusError):
        message_win.print_msg(f"{prompt}: OpenAI service is currently unavailable. Please try again later.")
    else:
        message_win.print_msg(f"{prompt}: An unexpected error occurred: {str(e)}")
    return