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

APP_NAME = "ednasg"
APP_VERSION = "v0.5"
APP_REPO = "https://api.github.com/repos/steelproxy/ednasg/releases/latest"

# Mouse scroll constants
WINDOWS_SCROLL_UP = 65536           # Windows-specific scroll up value
WINDOWS_SCROLL_DOWN = 2097152       # Windows-specific scroll down value

# Determine if we're on Windows
IS_WINDOWS = platform.system().lower() == 'windows'

# Constants
# Pattern for validating URLs
URL_PATTERN = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
CTRL_D = 4                                           # ASCII value for Ctrl+D
CTRL_N = 14                                          # ASCII value for Ctrl+N
# Set CTRL_O to the value for CTRL+W (23) on macOS
if platform.system().lower() == 'darwin':
    CTRL_O = 23  # ASCII value for Ctrl+W
else:
    CTRL_O = 15  # Default ASCII value for Ctrl+O
CTRL_R = 18                                          # ASCII value for Ctrl+R
if hasattr(curses, 'BUTTON5_PRESSED'):
    MOUSE_DOWN = curses.BUTTON5_PRESSED if not IS_WINDOWS else WINDOWS_SCROLL_DOWN # Scroll down, scroll values vary between platforms
if hasattr(curses, 'BUTTON4_PRESSED'):
    MOUSE_UP = curses.BUTTON4_PRESSED if not IS_WINDOWS else WINDOWS_SCROLL_UP     # Scroll up, scroll values vary between platforms
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
    message_win.print("Checking for updates...")
    # determine if application is a script file or frozen exe
    if getattr(sys, 'frozen', False):
        try:
            _do_binary_update()
        except Exception as e:
            message_win.print(
                f"Unexpected exception occurred while updating: {e}")
            message_win.print("Proceeding with current version...")
    else:
        try:
            subprocess.run(["git", "--version"],
                           check=True, capture_output=True)  # Verify git installation
            # Pull latest changes
            subprocess.run(["git", "pull"], check=True, capture_output=True)
            message_win.print("Repository updated successfully.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            message_win.print("Git not found in PATH. Skipping update...")
            message_win.print("Proceeding with the current version...")
        except Exception as e:
            message_win.print(
                f"Unexpected exception occured while updating: {e}")


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
        message_win.print("Binary update is only supported on Windows right now, sorry.")
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
        message_win.print(f"Already running latest version {current_version}")
        return

    # Find matching asset for current platform
    asset = None
    for a in release_data['assets']:
        if system in a['name'].lower():
            asset = a
            break

    if not asset:
        message_win.print(f"No release was found for platform: {system}! Skipping update...")
        return

    # Download new version
    message_win.print(f"Downloading update {latest_version}...")
    try:
        response = requests.get(asset['browser_download_url'], stream=True)
        if response.status_code != 200:
            message_win.print(f"Failed to download update! Response code: {response.status_code}. Skipping update...")
            return
    except requests.exceptions.RequestException as e:
        message_win.print(f"Failed to download update! Exception occurred: {e}. Skipping update...")
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
        message_win.print(f"Failed to download update! Exception occurred: {e}. Skipping update...")
        return
        
    message_win.print("Update downloaded! Restarting application...")
    sys.exit(0)


def _wait_for_exit():
    """Wait for user input before exiting."""
    bottom_win.print("Press any button to exit...")
    bottom_win.getch()


def _handle_exit():
    """Handle application exit."""
    curses.endwin()
    sys.exit(0)


def _fatal_error(message):
    """Display error message and exit"""
    message_win.clear()
    message_win.print(message)
    _wait_for_exit()
    _handle_exit()