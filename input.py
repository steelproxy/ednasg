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

def get_multiline_input(prompt, end_key=4):
    """Get multiline input from the user with scroll and cursor support."""
    input_str = [""]
    cursor_x = 0
    cursor_y = 0
    scroll_offset = 0
    curses.noecho()
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
        elif ch in (curses.KEY_BACKSPACE, 127, '\b'):  # Handle backspace
            if cursor_x > 0:
                input_str[cursor_y] = input_str[cursor_y][:cursor_x - 1] + input_str[cursor_y][cursor_x:]
                cursor_x -= 1
            elif cursor_y > 0:
                cursor_x = len(input_str[cursor_y - 1])
                input_str[cursor_y - 1] += input_str.pop(cursor_y)
                cursor_y -= 1
                if cursor_y < scroll_offset:
                    scroll_offset -= 1
        elif ch in (curses.KEY_LEFT, 452):  # Move cursor left
            if cursor_x > 0:
                cursor_x -= 1
            elif cursor_y > 0:
                cursor_y -= 1
                cursor_x = len(input_str[cursor_y])
                if cursor_y < scroll_offset:
                    scroll_offset -= 1
        elif ch in (curses.KEY_RIGHT, 454):  # Move cursor right
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
            setup_windows()
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
    curses.echo()
    return '\n'.join(input_str).strip()

def get_rss_urls(feeds):
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
                    while not (nickname := bottom_win.getstr(f"Enter a nickname for the new feed '{url}': ")):
                        bottom_win.print("Invalid nickname. Press any key to continue...")
                        bottom_win.getch()
                        bottom_win.print(f"Enter a nickname for the new feed '{url}': ")
                    feeds = config.update_config(url, nickname)
                else:
                    bottom_win.print(f"Feed URL '{url}' already exists. Skipping...")
            else:
                bottom_win.print(f"Invalid URL '{url}'. Skipping...")
            time.sleep(1)  # Short delay to prevent rapid input issues
        return feeds

    prompt = "Select a feed number, enter a single URL, or enter multiple URLs (ctrl-c to quit ctrl+n to skip): "
    while True:
        feed_scroll_idx = 0
        selected_option = ""
        cursor_pos = 0  # Tracks cursor position in the input string
        while True:
            message_win.display_feeds(feeds, feed_scroll_idx)
            bottom_win.print(prompt + selected_option)
            bottom_win.win.move(0, len(prompt) + cursor_pos + 1)
            bottom_win.win.refresh()
            ch = bottom_win.getch()
            
            if ch == curses.KEY_DOWN and feed_scroll_idx < len(feeds.items()) - 1:  # Scroll down
                feed_scroll_idx += 1
            elif ch == curses.KEY_UP and feed_scroll_idx > 0:  # Scroll up
                feed_scroll_idx -= 1
            elif ch in (curses.KEY_LEFT, 452) and cursor_pos > 0:
                cursor_pos -= 1  # Move cursor left
            elif ch in (curses.KEY_RIGHT, 454) and cursor_pos < len(selected_option):
                cursor_pos += 1  # Move cursor right
            elif ch == ord('\n'):  # Newline
                break
            elif ch in (curses.KEY_BACKSPACE, 127, '\b', 546):  # Backspace
                if cursor_pos > 0:
                    # Remove the character before the cursor
                    selected_option = selected_option[:cursor_pos - 1] + selected_option[cursor_pos:]
                    cursor_pos -= 1
            elif ch == curses.KEY_RESIZE:  # Resize
                setup_windows.stdscr.clear()
                setup_windows.stdscr.refresh()
                setup_windows()
                feed_scroll_idx = 0
            elif ch == 14:  # Ctrl+N
                return None
            elif ch not in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, 452, curses.KEY_RIGHT, 454, ord('\n'), curses.KEY_BACKSPACE, 127, '\b'):
                selected_option = selected_option[:cursor_pos] + chr(ch) + selected_option[cursor_pos:]
                cursor_pos += 1
            else:
                continue
        if selected_option.isdigit() and selected_option in feeds:
            # Valid feed number
            return feeds[selected_option]['url']
        
        elif selected_option:
            # Either a single URL or multiple URLs
            urls = [url.strip() for url in selected_option.split(',')]
            feeds = add_feeds(feeds, urls)
