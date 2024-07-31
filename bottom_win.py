import curses

global win

def print(message):
    """Display a status bar with a message."""
    win.clear()
    height, width = win.getmaxyx()
    win.bkgd(' ', curses.color_pair(1))
    
    # Truncate message if it's too long
    if len(message) > width - 2:
        message = message[:width - 4] + '...'
    
    win.addstr(0, 0, message)
    win.refresh()

def getstr():
    """Get a string from the user input."""
    return win.getstr().decode('utf-8').strip()

def getch():
    """Get a single character from the user input."""
    return win.getch()
