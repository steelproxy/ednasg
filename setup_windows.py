import curses
import message_win
import bottom_win

global stdscr

def setup_windows():
    """Initialize the curses windows."""
    term_height, term_width = setup_windows.stdscr.getmaxyx()
    
    # Initialize the message window
    message_win.win = curses.newwin(term_height - 1, term_width, 0, 0)
    
    # Initialize the bottom window
    bottom_win.win = curses.newwin(1, term_width, term_height - 1, 0)
    bottom_win.win.scrollok(False)  # Prevent line wrapping
    
    # Enable keypad input for both windows
    bottom_win.win.keypad(1)
    message_win.win.keypad(1)
