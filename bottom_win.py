import curses
import sys
import utils
import screen_manager
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

def render_input(prompt, selected_option, cursor_pos, max_x):
    """Render the feed input interface with horizontal scrolling."""
    win.erase()
    win.bkgd(' ', curses.color_pair(1))
    win.leaveok(0)
    win.idlok(0)
    win.scrollok(0)
    
    available_width = max_x - len(prompt)
    display_start = max(0, cursor_pos - available_width + 1)
    
    try:
        win.addstr(0, 0, prompt + selected_option[display_start:], curses.A_NORMAL)
    except curses.error:
        pass
        
    screen_cursor_pos = min(max_x - 1, len(prompt) + cursor_pos - display_start)
    win.move(0, screen_cursor_pos)
    win.refresh()

def handle_input(prompt, callback=None, max_input_len=None, hotkeys=None):
    """Generic input handler with scrolling, cursor support, and custom hotkeys.
    
    Args:
        prompt: The prompt to display
        callback: Optional function to call on each iteration
        max_input_len: Optional maximum input length
        hotkeys: Optional dict of {key: (function, description)} for special keys
                Example: {CTRL_N: (lambda: None, "Skip")}
    """
    curses.curs_set(2)
    curses.noecho()
    
    max_y, max_x = win.getmaxyx()
    input_str = ""
    cursor_pos = 0
    
    while True:
        if callback:
            callback_result = callback()
            if callback_result is not None:
                return callback_result
            
        # Render input using the same method as get_rss_urls
        render_input(prompt, input_str, cursor_pos, max_x)

        try:
            ch = win.getch()
        except KeyboardInterrupt:
            curses.endwin()
            sys.exit(0)

        # Check for hotkeys first
        if hotkeys and ch in hotkeys:
            func, _ = hotkeys[ch]
            if _ == "break":
                return None
            if ch == curses.KEY_RESIZE:  # Handle extra resize callback
                max_y, max_x = screen_manager.handle_resize()
            result = func()
            if result is not None:
                return result
            continue

        if ch == ord('\n'):
            break
            
        elif ch in utils.BACKSPACE_KEYS and cursor_pos > 0:
            input_str = (input_str[:cursor_pos - 1] + 
                        input_str[cursor_pos:])
            cursor_pos -= 1
            
        elif ch in utils.ARROW_LEFT and cursor_pos > 0:
            cursor_pos -= 1
            
        elif ch in utils.ARROW_RIGHT and cursor_pos < len(input_str):
            cursor_pos += 1
            
        elif ch == curses.KEY_RESIZE:
            max_y, max_x = screen_manager.handle_resize()
            continue
            
        elif 32 <= ch <= 126:
            if not max_input_len or len(input_str) < max_input_len:
                input_str = (input_str[:cursor_pos] + 
                            chr(ch) + 
                            input_str[cursor_pos:])
                cursor_pos += 1

        cursor_pos = max(0, min(cursor_pos, len(input_str)))

    curses.curs_set(0)
    return input_str

def getch():
    """Get a single character from the user input."""
    return win.getch()

def getstr(prompt):
    """Get a single line of input from the user using our generic input handler."""
    return handle_input(prompt)
