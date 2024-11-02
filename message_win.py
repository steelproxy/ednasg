import curses
import time 
import utils
import sys
import bottom_win
import screen_manager
global win

def print(message):
    """Display a message in the window."""
    win.addstr(message + '\n')
    win.refresh()

def clear():
    """Clear the window."""
    win.clear()
    win.refresh()

    
def get_multiline_input(prompt, end_key=4):
    """Get multiline input from the user with scroll and cursor support."""
    input_str = [""]
    cursor_x = cursor_y = scroll_offset = 0
    curses.noecho()
    curses.curs_set(2)  # Show cursor

    while True:
        max_y, max_x = win.getmaxyx()
        bottom_win.print(prompt)
        
        # Display current input text
        win.clear()
        _display_lines(input_str, scroll_offset, max_y, max_x)

        # Position cursor
        try:
            win.move(cursor_y - scroll_offset, cursor_x)
            win.refresh()  # Make sure to refresh after moving cursor
        except curses.error:
            win.refresh()

        # Get and handle input
        try:
            ch = win.getch()
        except KeyboardInterrupt:
            curses.endwin()
            sys.exit(0)

        # Handle different input cases
        if ch == end_key:  # Ctrl+D to finish
            break

        elif ch == curses.KEY_RESIZE:
            max_y, max_x = win.getmaxyx()
            screen_manager.handle_resize()
            cursor_x, cursor_y, scroll_offset = 0, 0, 0
            continue

        # Update cursor position and text based on input
        cursor_x, cursor_y, scroll_offset = handle_input(
            ch, cursor_x, cursor_y, scroll_offset,
            input_str, max_x, max_y
        )

    curses.curs_set(0)
    curses.echo()
    return '\n'.join(input_str).strip()

def _display_lines(input_str, scroll_offset, max_y, max_x):
    """Display the input lines with scrolling."""
    # For each line in the input string array
    for y, line in enumerate(input_str):
        # Only display lines that are within the visible window area
        if y >= scroll_offset and y < max_y + scroll_offset - 1:
            try:
                # Calculate the correct position and display the line
                # y - scroll_offset: adjusts the line position based on scroll
                # 0: starts at the leftmost column
                # line[:max_x]: truncates line if longer than window width
                win.addstr(y - scroll_offset, 0, line[:max_x])
            except curses.error:
                pass
    
    win.refresh()  # Ensure window is refreshed

def handle_input(ch, cursor_x, cursor_y, scroll_offset, input_str, max_x, max_y):
    """Handle different types of input and return updated cursor positions."""
    if ch in utils.BACKSPACE_KEYS:
        return handle_backspace(cursor_x, cursor_y, scroll_offset, input_str)
        
    elif ch == ord('\n'):
        return handle_newline(cursor_x, cursor_y, scroll_offset, input_str, max_y)
        
    elif ch in utils.ARROW_LEFT:
        return handle_left_arrow(cursor_x, cursor_y, scroll_offset, input_str)
        
    elif ch in utils.ARROW_RIGHT:
        return handle_right_arrow(cursor_x, cursor_y, scroll_offset, input_str, max_y)
        
    elif ch == curses.KEY_UP and cursor_y > 0:
        return handle_up_arrow(cursor_x, cursor_y, scroll_offset, input_str)
        
    elif ch == curses.KEY_DOWN and cursor_y < len(input_str) - 1:
        return handle_down_arrow(cursor_x, cursor_y, scroll_offset, input_str, max_y)
        
    else:
        return handle_regular_input(ch, cursor_x, cursor_y, scroll_offset, input_str, max_x, max_y)

def handle_backspace(cursor_x, cursor_y, scroll_offset, input_str):
    """Handle backspace key input."""
    if cursor_x > 0:
        input_str[cursor_y] = input_str[cursor_y][:cursor_x-1] + input_str[cursor_y][cursor_x:]
        return cursor_x - 1, cursor_y, scroll_offset
    elif cursor_y > 0:
        cursor_x = len(input_str[cursor_y-1])
        input_str[cursor_y-1] += input_str.pop(cursor_y)
        cursor_y -= 1
        if cursor_y < scroll_offset:
            scroll_offset = cursor_y
        return cursor_x, cursor_y, scroll_offset
    return cursor_x, cursor_y, scroll_offset

def handle_newline(cursor_x, cursor_y, scroll_offset, input_str, max_y):
    """Handle newline/enter key input."""
    input_str.insert(cursor_y + 1, input_str[cursor_y][cursor_x:])
    input_str[cursor_y] = input_str[cursor_y][:cursor_x]
    cursor_y += 1
    if cursor_y >= max_y + scroll_offset - 1:
        scroll_offset += 1
    return 0, cursor_y, scroll_offset

def handle_left_arrow(cursor_x, cursor_y, scroll_offset, input_str):
    """Handle left arrow key input."""
    if cursor_x > 0:
        return cursor_x - 1, cursor_y, scroll_offset
    elif cursor_y > 0:
        cursor_y -= 1
        cursor_x = len(input_str[cursor_y])
        if cursor_y < scroll_offset:
            scroll_offset -= 1
        return cursor_x, cursor_y, scroll_offset
    return cursor_x, cursor_y, scroll_offset

def handle_right_arrow(cursor_x, cursor_y, scroll_offset, input_str, max_y):
    """Handle right arrow key input."""
    if cursor_x < len(input_str[cursor_y]):
        return cursor_x + 1, cursor_y, scroll_offset
    elif cursor_y < len(input_str) - 1:
        cursor_y += 1
        if cursor_y >= max_y + scroll_offset - 1:
            scroll_offset += 1
        return 0, cursor_y, scroll_offset
    return cursor_x, cursor_y, scroll_offset

def handle_up_arrow(cursor_x, cursor_y, scroll_offset, input_str):
    """Handle up arrow key input."""
    cursor_y -= 1
    cursor_x = min(cursor_x, len(input_str[cursor_y]))
    if cursor_y < scroll_offset:
        scroll_offset -= 1
    return cursor_x, cursor_y, scroll_offset

def handle_down_arrow(cursor_x, cursor_y, scroll_offset, input_str, max_y):
    """Handle down arrow key input."""
    cursor_y += 1
    cursor_x = min(cursor_x, len(input_str[cursor_y]))
    if cursor_y >= max_y + scroll_offset - 1:
        scroll_offset += 1
    return cursor_x, cursor_y, scroll_offset

def handle_regular_input(ch, cursor_x, cursor_y, scroll_offset, input_str, max_x, max_y):
    """Handle regular character input."""
    sanitized_ch = utils.sanitize_input_char(ch)
    if sanitized_ch:
        input_str[cursor_y] = (input_str[cursor_y][:cursor_x] + 
                             sanitized_ch + 
                             input_str[cursor_y][cursor_x:])
        cursor_x += 1

        if cursor_x >= max_x:  # Handle line wrapping
            if cursor_y == len(input_str) - 1:
                input_str.append("")
            cursor_y += 1
            cursor_x = 0
            if cursor_y >= max_y + scroll_offset - 1:
                scroll_offset += 1
                
    return cursor_x, cursor_y, scroll_offset