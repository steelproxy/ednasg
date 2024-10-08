import curses
import setup_windows
import input

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

def getstr(prompt):
    """Get a string from the user input."""
    curses.curs_set(1)  # Make the cursor visible
    curses.noecho()
    
    input_str = []
    cursor_x = 0
    cursor_y = 0

    while True:
        win.clear()
        
        max_y, max_x = win.getmaxyx()
        print(prompt + ''.join(input_str))
        win.move(cursor_y, cursor_x + len(prompt))

        ch = win.getch()
        sanitized_ch = input.sanitize_input_char(ch)

        if ch == ord('\n'):  # Handle newline
            break
        elif ch in (curses.KEY_BACKSPACE, 127, '\b'):  # Handle backspace
            if cursor_x > 0:
                input_str.pop(cursor_x - 1)
                cursor_x -= 1
        elif ch in (curses.KEY_LEFT, 452):  # Move cursor left
            if cursor_x > 0:
                cursor_x -= 1
        elif ch in (curses.KEY_RIGHT, 454):  # Move cursor right
            if cursor_x < len(input_str):
                cursor_x += 1
        elif ch == curses.KEY_RESIZE:  # Resize handling
            setup_windows.setup_windows()
            cursor_x = 0
            cursor_y = 0
            continue
        else:  # Handle regular character input
            input_str.insert(cursor_x, sanitized_ch)
            cursor_x += 1

    curses.curs_set(0)
    return ''.join(input_str)

def getch():
    """Get a single character from the user input."""
    return win.getch()
