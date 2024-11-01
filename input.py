import curses
import bottom_win
import message_win
import re
import config
import time
from setup_windows import setup_windows
import signal
import sys

# Constants
CTRL_D = 4
CTRL_N = 14
BACKSPACE_KEYS = (curses.KEY_BACKSPACE, 127, '\b', 546, 8)
ARROW_LEFT = (curses.KEY_LEFT, 452)
ARROW_RIGHT = (curses.KEY_RIGHT, 454)
URL_PATTERN = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'

def is_valid_url(url):
    """Basic URL validation using regex."""
    return re.match(URL_PATTERN, url) is not None

def handle_feed_input(selected_option, feeds):
    """Process the selected option and determine if it's a valid feed number or add new URLs."""
    if selected_option.isdigit():
        if selected_option in feeds:
            return feeds[selected_option]['url']
        bottom_win.print(f"Invalid feed number: {selected_option}")
        time.sleep(1)
        return None
    
    if ',' in selected_option: # multiple URLs
        urls = [url.strip() for url in selected_option.split(',')]
        add_multiple_feeds(urls, feeds)
        return None
    
    if is_valid_url(selected_option):
        add_single_feed(selected_option, feeds)
        return None
        
    bottom_win.print("Invalid URL format. URL must start with http:// or https://")
    time.sleep(1)
    return None

def get_feed_nickname(url):
    """Prompt user for a nickname for the new feed."""
    while True: 
        nickname = bottom_win.getstr(f"Enter a nickname for the new feed {url}: ").strip() 
        if nickname:
            return nickname
        bottom_win.print("Invalid nickname. Try again.")

def add_single_feed(url, feeds):
    """Add a single feed URL to the configuration."""
    url = url.strip()
    if not is_valid_url(url):
        bottom_win.print(f"Invalid URL '{url}'. Skipping...")
        return feeds

    if any(feed['url'] == url for feed in feeds.values()):
        bottom_win.print(f"Feed URL '{url}' already exists. Skipping...")
        return feeds

    nickname = get_feed_nickname(url)
    return config.update_config(url, nickname)

def add_multiple_feeds(urls, feeds):
    """Process and add multiple feed URLs."""
    for url in urls:
        feeds = add_single_feed(url, feeds)
        time.sleep(1)  # Short delay to prevent rapid input issues
    return feeds

def render_feed_input(prompt, selected_option, cursor_pos, max_x):
    """Render the feed input interface with horizontal scrolling."""
    win = bottom_win.win
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

def handle_resize():
    """Handle terminal resize event."""
    setup_windows.stdscr.clear()
    setup_windows.stdscr.refresh()
    setup_windows()
    return bottom_win.win.getmaxyx()

def sanitize_input_char(ch):
    """Convert special characters to their string representation."""
    if 32 <= ch <= 126:  # Handle printable ASCII characters
        return chr(ch)
    return ''

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
        
        # Display current input text
        message_win.clear()
        for y, line in enumerate(input_str):
            if y >= scroll_offset and y < max_y + scroll_offset - 1:
                try:
                    message_win.win.addstr(y - scroll_offset, 0, line[:max_x])
                except curses.error:
                    pass

        # Position cursor
        try:
            message_win.win.move(cursor_y - scroll_offset, cursor_x)
        except curses.error:
            pass
        message_win.win.refresh()

        try:
            ch = message_win.getch()
        except KeyboardInterrupt:
            curses.endwin()
            sys.exit(0)

        if ch == end_key:  # Ctrl+D to finish
            break

        elif ch == curses.KEY_RESIZE:
            max_y, max_x = message_win.win.getmaxyx()
            setup_windows()
            scroll_offset = max(0, cursor_y - max_y + 1)
            continue

        elif ch in BACKSPACE_KEYS:  # Backspace
            if cursor_x > 0:
                input_str[cursor_y] = input_str[cursor_y][:cursor_x-1] + input_str[cursor_y][cursor_x:]
                cursor_x -= 1
            elif cursor_y > 0:
                cursor_x = len(input_str[cursor_y-1])
                input_str[cursor_y-1] += input_str.pop(cursor_y)
                cursor_y -= 1
                if cursor_y < scroll_offset:
                    scroll_offset = cursor_y

        elif ch == ord('\n'):  # Enter/newline
            input_str.insert(cursor_y + 1, input_str[cursor_y][cursor_x:])
            input_str[cursor_y] = input_str[cursor_y][:cursor_x]
            cursor_y += 1
            cursor_x = 0
            if cursor_y >= max_y + scroll_offset - 1:
                scroll_offset += 1

        elif ch in ARROW_LEFT:  # Left arrow
            if cursor_x > 0:
                cursor_x -= 1
            elif cursor_y > 0:
                cursor_y -= 1
                cursor_x = len(input_str[cursor_y])
                if cursor_y < scroll_offset:
                    scroll_offset -= 1

        elif ch in ARROW_RIGHT:  # Right arrow
            if cursor_x < len(input_str[cursor_y]):
                cursor_x += 1
            elif cursor_y < len(input_str) - 1:
                cursor_y += 1
                cursor_x = 0
                if cursor_y >= max_y + scroll_offset - 1:
                    scroll_offset += 1

        elif ch == curses.KEY_UP and cursor_y > 0:  # Up arrow
            cursor_y -= 1
            cursor_x = min(cursor_x, len(input_str[cursor_y]))
            if cursor_y < scroll_offset:
                scroll_offset -= 1

        elif ch == curses.KEY_DOWN and cursor_y < len(input_str) - 1:  # Down arrow
            cursor_y += 1
            cursor_x = min(cursor_x, len(input_str[cursor_y]))
            if cursor_y >= max_y + scroll_offset - 1:
                scroll_offset += 1

        else:  # Regular character input
            sanitized_ch = sanitize_input_char(ch)
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

    curses.curs_set(0)
    curses.echo()
    return '\n'.join(input_str).strip()
def get_rss_urls(feeds):
    """Prompt the user to input one or multiple new RSS feed URLs."""
    prompt = "Select a feed number or enter URLs (Ctrl+C to quit, Ctrl+N to skip): "
    max_y, max_x = bottom_win.win.getmaxyx()
    
    try:
        while True:
            feed_scroll_idx = 0
            selected_option = ""
            cursor_pos = 0
            
            while True:
                feeds = config.load_config()
                message_win.display_feeds(feeds, feed_scroll_idx)
                render_feed_input(prompt, selected_option, cursor_pos, max_x)
                
                try:
                    ch = bottom_win.getch()
                except KeyboardInterrupt:
                    curses.endwin()
                    sys.exit(0)
                
                if ch == CTRL_N:
                    curses.curs_set(0)
                    return None
                
                if ch == curses.KEY_RESIZE:
                    max_y, max_x = handle_resize()
                    feed_scroll_idx = 0
                    continue
                
                if ch == ord('\n'):
                    break
                
                if ch == curses.KEY_DOWN and feed_scroll_idx < len(feeds) - 1:
                    feed_scroll_idx += 1
                elif ch == curses.KEY_UP and feed_scroll_idx > 0:
                    feed_scroll_idx -= 1
                
                if ch in ARROW_LEFT and cursor_pos > 0:
                    cursor_pos -= 1
                elif ch in ARROW_RIGHT and cursor_pos < len(selected_option):
                    cursor_pos += 1
                
                if ch in BACKSPACE_KEYS and cursor_pos > 0:
                    selected_option = (selected_option[:cursor_pos - 1] + 
                                     selected_option[cursor_pos:])
                    cursor_pos -= 1
                elif 32 <= ch <= 126:
                    selected_option = (selected_option[:cursor_pos] + 
                                     chr(ch) + 
                                     selected_option[cursor_pos:])
                    cursor_pos += 1
                cursor_pos = max(0, min(cursor_pos, len(selected_option)))

            feed_url = handle_feed_input(selected_option, feeds)
            if feed_url:
                curses.curs_set(0)
                return feed_url
            
    except KeyboardInterrupt:
        curses.endwin()
        sys.exit(0)

def wrap_text(text, width):
    """Wrap text to fit within the given width."""
    wrapped_lines = []
    for line in text.split('\n'):
        while len(line) > width:
            wrapped_lines.append(line[:width])
            line = line[width:]
        wrapped_lines.append(line)
    return wrapped_lines
