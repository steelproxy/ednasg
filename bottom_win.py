import curses
import sys
import utils
import screen_manager
from message_win import print_buffer

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
                Example: {SKIP_HOTKEY: (lambda: None, "Skip")}
    """
    
    # Initialize input and cursor position
    input_str = ""
    cursor_pos = 0
    original_prompt = prompt

    while True:
        
        if callback: # Call callback if provided
            callback_result = callback()
            if callback_result is not None:
                return callback_result
            
        # Get window dimensions
        max_y, max_x = win.getmaxyx()
        if len(prompt) > max_x:
            prompt = "[]: "
        
        # Render input using the same method as get_rss_urls
        _render_input(prompt, input_str, cursor_pos, max_x)

        try: # Get input
            ch = win.getch()
        except KeyboardInterrupt:
            curses.endwin()
            sys.exit(0)

        if utils.IS_WINDOWS:
            if ch == curses.KEY_MOUSE and hasattr(utils, "MOUSE_UP") and hasattr(utils, "MOUSE_DOWN"): 
                try: # Handle mouse scroll
                    mouse_event = curses.getmouse()
                    button_state = mouse_event[4]
                    
                    # Debug logging
                    #with open('mouse_debug.log', 'a') as f:
                    #    f.write(f"Mouse event details:\n")
                    #    f.write(f"  id: {mouse_event[0]}\n")s
                    #    f.write(f"  x: {mouse_event[1]}\n")
                    #    f.write(f"  y: {mouse_event[2]}\n")
                    #    f.write(f"  z: {mouse_event[3]}\n")
                    #    f.write(f"  bstate: {bin(button_state)} ({button_state})\n")
                    #    f.write("---\n")
                    
                    # Standard curses scroll handling for other platforms
                    if (button_state & utils.MOUSE_UP or 
                        button_state & (1 << 3)):  # Alternative scroll up
                        ch = curses.KEY_UP
                    elif (button_state & utils.MOUSE_DOWN or 
                        button_state & (1 << 4)):  # Alternative scroll down
                        ch = curses.KEY_DOWN
                except curses.error:
                    return cursor_pos

        # Check for hotkeys first
        if hotkeys and ch in hotkeys:
            if ch == curses.KEY_RESIZE:
                max_y, max_x = screen_manager.handle_resize()
                if len(original_prompt) > max_x:
                    prompt = "[]: "
                else:
                    prompt = original_prompt
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
                if len(original_prompt) > max_x:
                    prompt = "[]: "
                else:
                    prompt = original_prompt
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

def bgetstr(prompt, hotkeys=None):
    """Get a single line of input from the user using our generic input handler."""
    return handle_input(prompt, callback=print_buffer, max_input_len=None, hotkeys=hotkeys)

def pause():
    """Prompt user to hit a key to continue."""
    print("Press any key to continue...")
    return win.getch()

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
    result = func()
    return result
