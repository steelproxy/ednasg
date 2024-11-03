import curses
import time
import bottom_win
import message_win
import config
from screen_manager import setup_windows
import utils

def display_feeds(feeds, start_idx):
    """Display a paginated list of RSS feeds in the window."""
    height, width = message_win.win.getmaxyx()
    max_lines = height - 1  # Reserve space for status bar and input prompt
    max_width = width - 2  # Side margins

    message_win.win.clear()
    message_win.win.addstr(0, 0, "Available RSS Feeds:")
    line_number = 1
    for idx in range(start_idx, min(start_idx + max_lines - 1, len(feeds.items()))):
        # Get feed info
        key, details = list(feeds.items())[idx]
        nickname = details['nickname']
        url = details['url']
        
        # Truncate feed nickname if needed
        if len(nickname) > max_width:
            nickname = nickname[:max_width - 3] + "..."

        try:
            message_win.win.addstr(line_number, 0, f"{key}: {nickname} ({url})")
            line_number += 1
        except curses.error:
            pass

    message_win.win.refresh()

# Feed Input Processing
def get_rss_urls(feeds):
    """Prompt the user to input one or multiple new RSS feed URLs."""
    prompt = "Select a feed number or enter URLs (Ctrl+C to quit, Ctrl+N to skip): "
    feed_scroll_idx = 0
    
    def display_callback():
        """Callback to display feeds and handle feed scrolling."""
        nonlocal feed_scroll_idx
        feeds = config.load_config()
        display_feeds(feeds, feed_scroll_idx)
        return None
    
    def handle_scroll(key):
        """Handle feed scrolling."""
        nonlocal feed_scroll_idx
        if key == curses.KEY_DOWN and feed_scroll_idx < len(feeds) - 1:
            feed_scroll_idx += 1
        elif key == curses.KEY_UP and feed_scroll_idx > 0:
            feed_scroll_idx -= 1
            
    def resize_callback():
        """Callback to handle resize."""
        nonlocal feed_scroll_idx
        feed_scroll_idx = 0
        return None
    
    def skip_callback():
        """Callback to skip."""
        return utils.CTRL_N
    
    hotkeys = {
        utils.CTRL_N: (lambda: skip_callback, "break"),
        curses.KEY_DOWN: (lambda: handle_scroll(curses.KEY_DOWN), "scroll down"),
        curses.KEY_UP: (lambda: handle_scroll(curses.KEY_UP), "scroll up"),
        curses.KEY_RESIZE: (resize_callback, "resize")
    }
    
    while True:
        selected_option = bottom_win.handle_input(prompt, callback=display_callback, hotkeys=hotkeys)
        
        if selected_option is None:  # User pressed Ctrl+N
            return None
            
        feed_url = handle_feed_input(selected_option, feeds)
        feeds = config.load_config() # Reload config after adding new feeds
        if feed_url:
            return feed_url

def handle_feed_input(selected_option, feeds):
    """Process the selected option and determine if it's a valid feed number or add new URLs."""
    if selected_option.isdigit():
        return _handle_feed_number(selected_option, feeds)
    
    if ',' in selected_option:
        add_multiple_feeds(selected_option.split(','), feeds)
        return None
    
    if utils.is_valid_url(selected_option):
        add_single_feed(selected_option, feeds)
        return None
        
    bottom_win.print("Invalid URL format. URL must start with ftp:// or http:// or https://")
    time.sleep(2)
    return None

# Feed Management
def add_single_feed(url, feeds):
    """Add a single feed URL to the configuration."""
    url = url.strip()
    if not utils.is_valid_url(url):
        bottom_win.print(f"Invalid URL '{url}'. Skipping...")
        return feeds

    if any(feed['url'] == url for feed in feeds.values()):
        bottom_win.print(f"Feed URL '{url}' already exists. Skipping...")
        return feeds

    nickname = get_feed_nickname(url, feeds)
    updated_config = config.update_config(url, nickname)
    bottom_win.print(f"Added feed '{url}' with nickname '{nickname}'.")
    time.sleep(2)
    return updated_config

def add_multiple_feeds(urls, feeds):
    """Process and add multiple feed URLs."""
    for url in urls:
        feeds = add_single_feed(url.strip(), feeds)
    return feeds

def get_feed_nickname(url, feeds):
    """Prompt user for a nickname for the new feed."""
    def display_callback():
        """Callback to display feeds and handle feed scrolling."""
        display_feeds(feeds, 0)
        return None
    
    while True: 
        nickname = bottom_win.handle_input(f"Enter a nickname for the new feed {url}: ", callback=display_callback).strip() 
        if nickname:
            return nickname
        bottom_win.print("Invalid nickname. Try again.")

# Helper Functions
def _handle_feed_number(selected_option, feeds):
    """Process a numeric feed selection."""
    if selected_option in feeds:
        return feeds[selected_option]['url']
    bottom_win.print(f"Invalid feed number: {selected_option}")
    time.sleep(1)
    return None


