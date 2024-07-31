import curses
import bottom_win
import message_win
import re
import config
import time
from setup_windows import setup_windows

def sanitize_input_char(ch):
    """Sanitize the input character to avoid unwanted control characters."""
    if 32 <= ch < 127 or ch == ord('\n'):
        return chr(ch)
    return ''

def wrap_text(text, width):
    """Wrap text to fit within the given width."""
    wrapped_lines = []
    for line in text.split('\n'):
        while len(line) > width:
            wrapped_lines.append(line[:width])
            line = line[width:]
        wrapped_lines.append(line)
    return wrapped_lines

def get_multiline_input(stdscr, prompt, end_key=4):
    """Get multiline input from the user with scroll and cursor support."""
    input_str = [""]
    cursor_x = 0
    cursor_y = 0
    scroll_offset = 0

    while True:
        max_y, max_x = message_win.win.getmaxyx()
        bottom_win.print(prompt)
        
        message_win.clear()
        for y, line in enumerate(input_str):
            wrapped_lines = wrap_text(line, max_x)
            for i, wrapped_line in enumerate(wrapped_lines):
                if y + i >= max_y - 1 + scroll_offset:
                    break
                if y + i >= scroll_offset:
                    message_win.win.addstr(y + i - scroll_offset, 0, wrapped_line)
        message_win.win.move(cursor_y - scroll_offset, cursor_x)
        message_win.win.refresh()

        ch = message_win.getch()
        sanitized_ch = sanitize_input_char(ch)

        if ch == end_key:  # End of input (Ctrl+D)
            break
        elif ch in (curses.KEY_BACKSPACE, 127):  # Handle backspace
            if cursor_x > 0:
                input_str[cursor_y] = input_str[cursor_y][:cursor_x - 1] + input_str[cursor_y][cursor_x:]
                cursor_x -= 1
            elif cursor_y > 0:
                cursor_x = len(input_str[cursor_y - 1])
                input_str[cursor_y - 1] += input_str.pop(cursor_y)
                cursor_y -= 1
                if cursor_y < scroll_offset:
                    scroll_offset -= 1
        elif ch == curses.KEY_LEFT:  # Move cursor left
            if cursor_x > 0:
                cursor_x -= 1
            elif cursor_y > 0:
                cursor_y -= 1
                cursor_x = len(input_str[cursor_y])
                if cursor_y < scroll_offset:
                    scroll_offset -= 1
        elif ch == curses.KEY_RIGHT:  # Move cursor right
            if cursor_x < len(input_str[cursor_y]):
                cursor_x += 1
            elif cursor_y < len(input_str) - 1:
                cursor_y += 1
                cursor_x = 0
                if cursor_y >= max_y + scroll_offset - 1:
                    scroll_offset += 1
        elif ch == curses.KEY_UP:  # Move cursor up
            if cursor_y > 0:
                cursor_y -= 1
                cursor_x = min(cursor_x, len(input_str[cursor_y]))
                if cursor_y < scroll_offset:
                    scroll_offset -= 1
        elif ch == curses.KEY_DOWN:  # Move cursor down
            if cursor_y < len(input_str) - 1:
                cursor_y += 1
                cursor_x = min(cursor_x, len(input_str[cursor_y]))
                if cursor_y >= max_y + scroll_offset - 1:
                    scroll_offset += 1
        elif ch == curses.KEY_RESIZE:  # Resize handling
            max_y, max_x = message_win.win.getmaxyx()
            setup_windows(stdscr)
            cursor_x = 0
            cursor_y = 0
            scroll_offset = 0
            continue
        elif ch == ord('\n'):  # Handle newline
            input_str.insert(cursor_y + 1, input_str[cursor_y][cursor_x:])
            input_str[cursor_y] = input_str[cursor_y][:cursor_x]
            cursor_y += 1
            cursor_x = 0
            if cursor_y >= max_y + scroll_offset - 1:
                scroll_offset += 1
        else:  # Handle regular character input
            input_str[cursor_y] = input_str[cursor_y][:cursor_x] + sanitized_ch + input_str[cursor_y][cursor_x:]
            cursor_x += 1

        # Add a new line if it doesn't exist
        if cursor_y == len(input_str):
            input_str.append("")

        # Handle cursor wrapping at line boundaries
        if cursor_x >= max_x:
            cursor_x = 0
            cursor_y += 1
            input_str.insert(cursor_y, "")
            if cursor_y >= max_y + scroll_offset - 1:
                scroll_offset += 1

    curses.curs_set(0)
    return '\n'.join(input_str).strip()

def get_rss_urls(stdscr, feeds):
    """Prompt the user to input one or multiple new RSS feed URLs."""
    
    def is_valid_url(url):
        """Basic URL validation using regex."""
        return re.match(r'^(https?|ftp)://[^\s/$.?#].[^\s]*$', url) is not None

    def add_feeds(feeds, urls):
        """Add multiple feeds to the configuration."""
        for url in urls:
            url = url.strip()
            if is_valid_url(url):
                # Check if URL is already in the config
                if not any(feed['url'] == url for feed in feeds.values()):
                    bottom_win.print(f"Enter a nickname for the new feed '{url}': ")
                    while not (nickname := bottom_win.getstr()):
                        bottom_win.print("Invalid nickname. Press any key to continue...")
                        bottom_win.getch()
                        bottom_win.print(f"Enter a nickname for the new feed '{url}': ")
                    feeds = config.update_config(url, nickname)
                else:
                    bottom_win.print(f"Feed URL '{url}' already exists. Skipping...")
            else:
                bottom_win.print(f"Invalid URL '{url}'. Skipping...")
            time.sleep(0.1)  # Short delay to prevent rapid input issues
        return feeds

    while True:
        bottom_win.print("Select a feed number, enter a single URL, or enter multiple URLs (ctrl+n to skip): ")
        
        feed_scroll_idx = 0
        selected_option = ""
        while True:
            message_win.display_feeds(feeds, feed_scroll_idx)
            
            ch = bottom_win.getch()
            bottom_win.print("Select a feed number, enter a single URL, or enter multiple URLs (ctrl+n to skip): " + selected_option)
            
            if ch == curses.KEY_DOWN and feed_scroll_idx < len(feeds.items()) - 1:  # Scroll down
                feed_scroll_idx += 1
            elif ch == curses.KEY_UP and feed_scroll_idx > 0:  # Scroll up
                feed_scroll_idx -= 1
            elif ch == ord('\n'):  # Newline
                break
            elif ch == 127:  # Backspace key
                selected_option = selected_option[:-1]
                bottom_win.print("Select a feed number, enter a single URL, or enter multiple URLs (ctrl+n to skip): " + selected_option)
            elif ch == curses.KEY_RESIZE:  # Resize
                stdscr.clear()
                stdscr.refresh()
                setup_windows(stdscr)
                feed_scroll_idx = 0
                bottom_win.print("Select a feed number, enter a single URL, or enter multiple URLs (ctrl+n to skip): " + selected_option)
            elif ch == 14:  # Ctrl+N
                return None
            elif ch != curses.KEY_UP and ch != curses.KEY_DOWN and ch != ord('\n'):  # Valid character
                selected_option += chr(ch)
                bottom_win.print("Select a feed number, enter a single URL, or enter multiple URLs (ctrl+n to skip): " + selected_option)
        
        if selected_option.isdigit() and selected_option in feeds:
            # Valid feed number
            return feeds[selected_option]['url']
        
        elif selected_option:
            # Either a single URL or multiple URLs
            urls = [url.strip() for url in selected_option.split(',')]
            feeds = add_feeds(feeds, urls)
        
        else:
            # Prompt the user again if the input is invalid
            bottom_win.print("Invalid selection. Press any key to continue...")
            bottom_win.getch()
