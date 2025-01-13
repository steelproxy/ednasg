import curses
import utils
import sys
import bottom_win
import screen_manager
global win

message_buffer = []

def print(message, wrap=False):    # Display message in window
    """Display a message in the window, with option to wrap or truncate lines that exceed window width.
    
    Args:
        message: The message to display
        wrap: If True, wrap long lines. If False, truncate with ellipsis.
    """
    max_y, max_x = win.getmaxyx()
    available_width = max_x - 2  # Subtract 2 for safe padding
    
    try:
        current_y, current_x = win.getyx()  # Get current cursor position
        
        if wrap:
            # Split message into wrapped lines
            lines = []
            remaining = message
            while remaining:
                if len(remaining) <= available_width:
                    lines.append(remaining)
                    break
                # Find last space before width limit
                split_point = remaining[:available_width].rfind(' ')
                if split_point == -1:  # No space found, force split
                    split_point = available_width
                lines.append(remaining[:split_point])
                remaining = remaining[split_point:].lstrip()
                
            # Print wrapped lines
            for line in lines:
                if current_y >= max_y - 1:  # Check window bounds
                    return
                # Print as much of line as will fit
                chars_that_fit = min(len(line), available_width)
                win.addstr(current_y, 0, line[:chars_that_fit])
                win.addstr('\n')
                current_y += 1
        else:
            # Truncate with ellipsis
            if len(message) > available_width:
                message = message[:available_width - 3] + "..."
            if current_y >= max_y - 1:  # Check window bounds
                return
            win.addstr(current_y, 0, message)
            win.addstr('\n')
            
    except curses.error:
        return
    
    win.refresh()

def clear():          # Clear window contents
    """Clear the window."""
    win.erase()
    win.refresh()

def print_buffer():
    """Print the buffer."""
    erase()
    max_y, max_x = win.getmaxyx()
    available_width = max_x - 2  # Subtract 2 for safe padding
    
    # Calculate lines needed for each message
    messages_with_lines = []
    for message in message_buffer:
        lines = []
        remaining = message
        while remaining:
            if len(remaining) <= available_width:
                lines.append(remaining)
                break
            split_point = remaining[:available_width].rfind(' ')
            if split_point == -1:
                split_point = available_width
            lines.append(remaining[:split_point])
            remaining = remaining[split_point:].lstrip()
        messages_with_lines.append((message, len(lines)))
    
    # Calculate total lines needed and determine starting message
    total_lines = 0
    start_idx = len(messages_with_lines) - 1
    while start_idx >= 0:
        total_lines += messages_with_lines[start_idx][1]
        if total_lines > max_y - 1:  # Leave 1 line for padding
            start_idx += 1  # Go back one message since we exceeded the space
            break
        start_idx -= 1
    start_idx = max(0, start_idx)
    
    # Print messages from the calculated starting point
    for message, _ in messages_with_lines[start_idx:]:
        print(message, wrap=True)

def print_msg(message):
    """Print a message and add it to the buffer."""
    message_buffer.append(message)
    print_buffer()

def clear_buffer():
    """Clear the buffer."""
    message_buffer.clear()

def erase():
    """Erase the window."""
    win.erase()

def error(message):
    win.erase()
    print(message, wrap=True)
    bottom_win.pause()
    
def get_multiline_input(prompt, end_key=4):    # Get multi-line user input
    """Get multiline input from the user with scroll and cursor support."""
    input_str = [""]                           # Initialize empty input
    cursor_x = cursor_y = scroll_offset = 0    # Set initial positions

    while True:
        max_y, max_x = win.getmaxyx()          # Get window dimensions
        bottom_win.print(prompt)               # Show input prompt
        
        win.erase()                            # Clear display
        _display_lines(input_str, scroll_offset, max_y, max_x)

        try:
            win.move(cursor_y - scroll_offset, cursor_x)    # Position cursor
            win.refresh()
        except curses.error:
            win.refresh()

        try:
            ch = win.getch()                   # Get user input
        except KeyboardInterrupt:              # Handle Ctrl+C
            curses.endwin()
            sys.exit(0)

        if ch == end_key:                      # Check for end input (Ctrl+D)
            break

        elif ch == curses.KEY_RESIZE:          # Handle window resize
            max_y, max_x = win.getmaxyx()
            screen_manager.handle_resize()
            cursor_x, cursor_y, scroll_offset = 0, 0, 0
            continue

        cursor_x, cursor_y, scroll_offset = handle_input(    # Process input
            ch, cursor_x, cursor_y, scroll_offset,
            input_str, max_x, max_y
        )
    
    return '\n'.join(input_str).strip()

def handle_input(ch, cursor_x, cursor_y, scroll_offset, input_str, max_x, max_y):    # Process input
    """Handle different types of input and return updated cursor positions."""
    match ch:
        case curses.KEY_MOUSE:                         # Handle mouse events
            try:
                mouse_event = curses.getmouse()
                button_state = mouse_event[4]
                
                # Standard curses scroll handling for other platforms
                if button_state & utils.MOUSE_UP:
                    ch = curses.KEY_UP
                elif button_state & utils.MOUSE_DOWN:
                    ch = curses.KEY_DOWN
            except curses.error:
                return cursor_x, cursor_y, scroll_offset
            
            # Fall through to handle the updated ch value in other cases
            
        case _ if ch in utils.BACKSPACE_KEYS:             # Handle backspace
            return _handle_backspace(cursor_x, cursor_y, scroll_offset, input_str)
            
        case _ if ch == ord('\n'):                      # Handle enter key
            return _handle_newline(cursor_x, cursor_y, scroll_offset, input_str, max_y)
            
        case _ if ch in utils.ARROW_LEFT:               # Handle left arrow
            return _handle_left_arrow(cursor_x, cursor_y, scroll_offset, input_str)
            
        case _ if ch in utils.ARROW_RIGHT:              # Handle right arrow
            return _handle_right_arrow(cursor_x, cursor_y, scroll_offset, input_str, max_y)
            
        case curses.KEY_UP if cursor_y > 0:    # Handle up arrow
            return _handle_up_arrow(cursor_x, cursor_y, scroll_offset, input_str)
            
        case curses.KEY_DOWN if cursor_y < len(input_str) - 1:    # Handle down arrow
            return _handle_down_arrow(cursor_x, cursor_y, scroll_offset, input_str, max_y)
            
        case _:                                         # Handle regular input
            return _handle_regular_input(ch, cursor_x, cursor_y, scroll_offset, input_str, max_x, max_y)
        
def _display_lines(input_str, scroll_offset, max_y, max_x):    # Show input lines
    """Display the input lines with scrolling."""
    for y, line in enumerate(input_str):       # Process each line
        if y >= scroll_offset and y < max_y + scroll_offset - 1:
            try:
                # Calculate the correct position and display the line
                # y - scroll_offset: adjusts the line position based on scroll
                # 0: starts at the leftmost column
                # line[:max_x]: truncates line if longer than window width
                win.addstr(y - scroll_offset, 0, line[:max_x])
            except curses.error:
                pass
    
    win.refresh()

def _handle_backspace(cursor_x, cursor_y, scroll_offset, input_str):    # Process backspace
    """Handle backspace key input."""
    if cursor_x > 0:                          # Delete character
        input_str[cursor_y] = input_str[cursor_y][:cursor_x-1] + input_str[cursor_y][cursor_x:]
        return cursor_x - 1, cursor_y, scroll_offset
    elif cursor_y > 0:                        # Join with previous line
        cursor_x = len(input_str[cursor_y-1])
        input_str[cursor_y-1] += input_str.pop(cursor_y)
        cursor_y -= 1
        if cursor_y < scroll_offset:
            scroll_offset = cursor_y
        return cursor_x, cursor_y, scroll_offset
    return cursor_x, cursor_y, scroll_offset

def _handle_newline(cursor_x, cursor_y, scroll_offset, input_str, max_y):    # Process enter key
    """Handle newline/enter key input."""
    input_str.insert(cursor_y + 1, input_str[cursor_y][cursor_x:])    # Split line
    input_str[cursor_y] = input_str[cursor_y][:cursor_x]
    cursor_y += 1
    if cursor_y >= max_y + scroll_offset - 1:    # Scroll if needed
        scroll_offset += 1
    return 0, cursor_y, scroll_offset

def _handle_left_arrow(cursor_x, cursor_y, scroll_offset, input_str):    # Move cursor left
    """Handle left arrow key input."""
    if cursor_x > 0:                          # Move within line
        return cursor_x - 1, cursor_y, scroll_offset
    elif cursor_y > 0:                        # Move to previous line
        cursor_y -= 1
        cursor_x = len(input_str[cursor_y])
        if cursor_y < scroll_offset:
            scroll_offset -= 1
        return cursor_x, cursor_y, scroll_offset
    return cursor_x, cursor_y, scroll_offset

def _handle_right_arrow(cursor_x, cursor_y, scroll_offset, input_str, max_y):    # Move cursor right
    """Handle right arrow key input."""
    if cursor_x < len(input_str[cursor_y]):    # Move within line
        return cursor_x + 1, cursor_y, scroll_offset
    elif cursor_y < len(input_str) - 1:        # Move to next line
        cursor_y += 1
        if cursor_y >= max_y + scroll_offset - 1:
            scroll_offset += 1
        return 0, cursor_y, scroll_offset
    return cursor_x, cursor_y, scroll_offset

def _handle_up_arrow(cursor_x, cursor_y, scroll_offset, input_str):    # Move cursor up
    """Handle up arrow key input."""
    cursor_y -= 1                             # Move up one line
    cursor_x = min(cursor_x, len(input_str[cursor_y]))
    if cursor_y < scroll_offset:              # Adjust scroll if needed
        scroll_offset -= 1
    return cursor_x, cursor_y, scroll_offset

def _handle_down_arrow(cursor_x, cursor_y, scroll_offset, input_str, max_y):    # Move cursor down
    """Handle down arrow key input."""
    cursor_y += 1                             # Move down one line
    cursor_x = min(cursor_x, len(input_str[cursor_y]))
    if cursor_y >= max_y + scroll_offset - 1:    # Adjust scroll if needed
        scroll_offset += 1
    return cursor_x, cursor_y, scroll_offset

def _handle_regular_input(ch, cursor_x, cursor_y, scroll_offset, input_str, max_x, max_y):    # Handle typing
    """Handle regular character input."""
    sanitized_ch = utils.sanitize_input_char(ch)    # Clean input character
    if sanitized_ch:
        input_str[cursor_y] = (input_str[cursor_y][:cursor_x] + 
                             sanitized_ch + 
                             input_str[cursor_y][cursor_x:])
        cursor_x += 1

        if cursor_x >= max_x:                      # Handle line wrapping
            if cursor_y == len(input_str) - 1:
                input_str.append("")
            cursor_y += 1
            cursor_x = 0
            if cursor_y >= max_y + scroll_offset - 1:
                scroll_offset += 1
                
    return cursor_x, cursor_y, scroll_offset