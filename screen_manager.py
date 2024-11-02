import curses
import message_win
import bottom_win

global stdscr

def setup_curses():
    """Initialize curses settings."""
    curses.curs_set(1)  # Show cursor
    curses.echo()  # Echo input characters
    curses.start_color()  # Enable color support
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Define color pair
    curses.use_default_colors()  # Allow using terminal's default colors
    stdscr.keypad(1)  # Enable keypad input (arrow keys etc)
    stdscr.clear()  # Clear screen
    stdscr.refresh()  # Refresh to show changes
    

def setup_windows():
    """Initialize the curses windows."""
    term_height, term_width = stdscr.getmaxyx()
    
    # Initialize the message window
    message_win.win = curses.newwin(term_height - 1, term_width, 0, 0)
    message_win.win.scrollok(False) # Prevent line wrapping
    message_win.win.leaveok(0)  # Update cursor position
    
    # Initialize the bottom window
    bottom_win.win = curses.newwin(1, term_width, term_height - 1, 0)
    bottom_win.win.scrollok(False)  # Prevent line wrapping
    bottom_win.win.leaveok(0)  # Update cursor position
    
    # Set background colors
    message_win.win.bkgd(' ', curses.color_pair(0))
    bottom_win.win.bkgd(' ', curses.color_pair(1))
    
    # Enable keypad input for both windows
    bottom_win.win.keypad(1)
    message_win.win.keypad(1)
    
def handle_resize():
    """Handle terminal resize event."""
    # Clear and refresh the main screen
    stdscr.clear()
    stdscr.refresh()
    
    # Reinitialize windows with new terminal dimensions
    setup_windows()
    
    # Refresh both windows after resize
    message_win.win.clear()
    message_win.win.refresh()
    bottom_win.win.clear() 
    bottom_win.win.refresh()
    
    # Return the new dimensions
    return bottom_win.win.getmaxyx()