import curses
import sys
import utils
import screen_manager
global win

def print(message):
    """Display a status bar with a message and truncate if necessary."""
    # Clear the window and set background color
    win.erase()
    
    # Truncate message if it's too long
    height, width = win.getmaxyx()
    if len(message) > width - 2:
        message = message[:width - 4] + '...'
    
    # Display the message
    try:
        win.addstr(0, 0, message)
        win.refresh()
    except curses.error:
        return


def handle_input(prompt, callback=None, max_input_len=None, hotkeys=None):
    """Generic input handler with scrolling, cursor support, and custom hotkeys.
    
    Args:
        prompt: The prompt to display
        callback: Optional function to call on each iteration
        max_input_len: Optional maximum input length
        hotkeys: Optional dict of {key: (function, description)} for special keys
                Example: {CTRL_N: (lambda: None, "Skip")}
    """
    
    # Initialize input and cursor position
    input_str = ""
    cursor_pos = 0
    while True:
        
        if callback: # Call callback if provided
            callback_result = callback()
            if callback_result is not None:
                return callback_result
            
        # Get window dimensions
        max_y, max_x = win.getmaxyx()
        
        # Render input using the same method as get_rss_urls
        _render_input(prompt, input_str, cursor_pos, max_x)

        try: # Get input
            ch = win.getch()
        except KeyboardInterrupt:
            curses.endwin()
            sys.exit(0)

        # Check for hotkeys first
        if hotkeys and ch in hotkeys:
            result = _handle_hotkey(hotkeys, ch)
            if result is not None:
                if result == "break":
                    return None
                return result
            continue

        match ch: # Handle input
            case _ if ch == ord('\n'):
                break
            case _ if ch in utils.BACKSPACE_KEYS and cursor_pos > 0:
                input_str = (input_str[:cursor_pos - 1] + 
                            input_str[cursor_pos:])
                cursor_pos -= 1
            case _ if ch in utils.ARROW_LEFT and cursor_pos > 0:
                cursor_pos -= 1
            case _ if ch in utils.ARROW_RIGHT and cursor_pos < len(input_str):
                cursor_pos += 1
            case curses.KEY_RESIZE:
                max_y, max_x = screen_manager.handle_resize()
                continue
            case _ if 32 <= ch <= 126:
                if not max_input_len or len(input_str) < max_input_len:
                    input_str = (input_str[:cursor_pos] + 
                                chr(ch) + 
                                input_str[cursor_pos:])
                    cursor_pos += 1

        # Ensure cursor position is within bounds
        cursor_pos = max(0, min(cursor_pos, len(input_str)))

    return input_str

def getch():
    """Get a single character from the user input."""
    return win.getch()

def getstr(prompt, callback=None, hotkeys=None):
    """Get a single line of input from the user using our generic input handler."""
    return handle_input(prompt, callback=callback, max_input_len=None, hotkeys=hotkeys)

# Helpers

def _render_input(prompt, selected_option, cursor_pos, max_x):
    """Render the feed input interface with horizontal scrolling."""
    win.erase()
    
    # Calculate available width and ensure we don't exceed window bounds
    available_width = max(0, max_x - len(prompt))
    
    # Calculate display start position while respecting window width
    display_start = max(0, cursor_pos - available_width + 1)
    
    # Calculate visible portion of text
    visible_text = selected_option[display_start:display_start + available_width]
    
    try:
        win.addstr(0, 0, prompt + visible_text, curses.A_NORMAL)
    except curses.error:
        pass
        
    # Ensure cursor stays within window bounds
    screen_cursor_pos = min(max_x - 1, len(prompt) + cursor_pos - display_start)
    screen_cursor_pos = max(len(prompt), screen_cursor_pos)
    
    win.move(0, min(screen_cursor_pos, max_x - 1))
    win.refresh()
    
def _handle_hotkey(hotkeys, ch):
    """Process hotkey input and execute associated function."""
    func, action = hotkeys[ch]
    if action == "break":
        return "break"
    if ch == curses.KEY_RESIZE:  # Handle extra resize callback
        max_y, max_x = screen_manager.handle_resize()
    result = func()
    return result
