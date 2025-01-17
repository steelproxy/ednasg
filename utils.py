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
    # determine if application is a script file or frozen exe
    if getattr(sys, 'frozen', False):
        try:
            _do_binary_update()
        except Exception as e:
            message_win.error(f"Unexpected exception occurred while updating: {e}")
            message_win.print_msg("Proceeding with current version...")
    else:
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


def _replace_binary(temp_dir, temp_path, current_exe):
    # Create batch script to replace exe after this process exits
    batch_path = os.path.join(temp_dir, 'update.bat')
    with open(batch_path, 'w') as f:
        f.write('@echo off\n')
        f.write(':wait\n')
        f.write(f'tasklist | find /i "{os.path.basename(current_exe)}" >nul\n')
        f.write('if errorlevel 1 (\n')
        f.write(f'  move /y "{temp_path}" "{current_exe}"\n')
        f.write('  rmdir /s /q "%~dp0"\n')
        f.write('  exit\n')
        f.write(') else (\n')
        f.write('  timeout /t 1 /nobreak >nul\n')
        f.write('  goto wait\n')
        f.write(')\n')

    # Launch updater script and exit
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    subprocess.Popen(['cmd', '/c', batch_path],
                     startupinfo=startupinfo,
                     creationflags=subprocess.CREATE_NEW_CONSOLE)


def _do_binary_update():
    if not IS_WINDOWS:
        message_win.error("Binary update is only supported on Windows right now, sorry.")
        return

    # Get current executable path and version
    current_exe = sys.executable
    current_version = version.parse(APP_VERSION)
    system = platform.system().lower()

    # Get latest release from GitHub
    response = requests.get(APP_REPO)
    if response.status_code != 200:
        raise Exception("Failed to fetch release info")

    # Parse release data
    release_data = response.json()
    latest_version = version.parse(release_data['tag_name'].lstrip('v'))

    # Check if update is needed
    if latest_version <= current_version:
        message_win.print_msg(f"Already running latest version {current_version}")
        return

    # Find matching asset for current platform
    asset = None
    for a in release_data['assets']:
        if system in a['name'].lower():
            asset = a
            break

    if not asset:
        message_win.print_msg(f"No release was found for platform: {system}! Skipping update...")
        return

    # Download new version
    message_win.print_msg(f"Downloading update {latest_version}...")
    try:
        response = requests.get(asset['browser_download_url'], stream=True)
        if response.status_code != 200:
            message_win.print_msg(f"Failed to download update! Response code: {response.status_code}. Skipping update...")
            return
    except requests.exceptions.RequestException as e:
        message_win.error(f"Failed to download update! Exception occurred: {e}. Skipping update...")
        return

    try:
        # Save to temporary file
        import tempfile
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, 'update.exe')

        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        if os.system == "nt":
            _replace_binary(temp_dir, temp_path, current_exe)
        else:
            os.replace(temp_path, current_exe)
    except Exception as e:
        message_win.error(f"Failed to download update! Exception occurred: {e}. Skipping update...")
        return
        
    message_win.print_msg("Update downloaded! Restarting application...")
    sys.exit(0)

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
    message_win.print(message)
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