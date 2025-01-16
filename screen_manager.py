import curses
import message_win
import bottom_win
from utils import IS_WINDOWS

global stdscr

# Main Setup Functions
def setup_curses():
    """Initialize curses settings."""
    _setup_cursor_and_input()
    _setup_colors()
    _setup_main_screen()

def _setup_cursor_and_input():
    """Configure cursor and input settings."""
    curses.curs_set(1)      # Make cursor visible (1 = visible, 0 = invisible)
    curses.noecho()         # Disable character echoing to screen
    stdscr.keypad(1)        # Enable special key handling
    if IS_WINDOWS:
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)

def _setup_colors():
    """Initialize color settings."""
    curses.start_color()    # Initialize color support
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Define black on white
    curses.use_default_colors()  # Allow using default terminal colors

def _setup_main_screen():
    """Initialize main screen."""
    stdscr.clear()          # Clear the entire screen
    stdscr.refresh()        # Update physical screen to match buffer

# Window Management Functions
def setup_windows():
    """Initialize the curses windows."""
    term_height, term_width = stdscr.getmaxyx()
    _setup_message_window(term_height, term_width)
    _setup_bottom_window(term_height, term_width)
    _apply_window_colors()

def _setup_message_window(term_height, term_width):
    """Configure the main message window."""
    message_win.win = curses.newwin(term_height - 1, term_width, 0, 0)  # height, width, y, x
    message_win.win.scrollok(False)  # Disable automatic scrolling
    message_win.win.leaveok(False)   # Update cursor position after write
    message_win.win.idlok(False)     # Disable cursor blinking
    message_win.win.keypad(True)     # Enable special key handling

def _setup_bottom_window(term_height, term_width):
    """Configure the bottom input window."""
    bottom_win.win = curses.newwin(1, term_width, term_height - 1, 0)  # 1-line window at bottom
    bottom_win.win.scrollok(False)   # Disable automatic scrolling
    bottom_win.win.leaveok(False)    # Update cursor position after write
    bottom_win.win.idlok(False)      # Disable cursor blinking
    bottom_win.win.keypad(True)      # Enable special key handling

def _apply_window_colors():
    """Apply background colors to windows."""
    message_win.win.bkgd(' ', curses.color_pair(0))  # Default color for message window
    bottom_win.win.bkgd(' ', curses.color_pair(1))   # Black-on-white for bottom window

# Resize Handling Functions
def handle_resize():
    """Handle terminal resize event."""
    _refresh_main_screen()
    setup_windows()
    _refresh_sub_windows()
    return bottom_win.win.getmaxyx()

def _refresh_main_screen():
    """Refresh the main screen."""
    stdscr.clear()
    stdscr.refresh()

def _refresh_sub_windows():
    """Refresh message and bottom windows."""
    message_win.win.clear()
    message_win.win.refresh()
    bottom_win.win.clear() 
    bottom_win.win.refresh()