import curses

global win

def print(message):
    """Display a status bar with a message."""
    win.clear()
    height, width = win.getmaxyx()
    win.bkgd(' ', curses.color_pair(1))
    if len(message) > width - 2:  # Truncate message
        message = message[:width - 4] + '...'
    win.addstr(0, 0, message)
    win.refresh()
    
def getstr():
    return win.getstr().decode('utf-8').strip()

def getch():
    return win.getch()