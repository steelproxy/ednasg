import curses
import time
import bottom_win
import message_win
import config
from screen_manager import setup_windows
import utils
import api_keyring
from pgn import pgn_search

# Display Functions
def display_feeds(feeds, start_idx):  # Main function to show RSS feeds
    """Display a paginated list of RSS feeds in the window."""
    height, width = message_win.win.getmaxyx()
    max_lines = height - 1      # Reserve space for status bar
    max_width = width - 2       # Account for side margins

    message_win.erase()
    message_win.print(f"Available RSS Feeds: [CTRL+C to quit, CTRL+N manual input, {"CTRL+O" if utils.IS_WINDOWS else "CTRL+W"} google news, CTRL+R to reset credentials]")
    _display_feed_list(feeds, start_idx, max_lines, max_width)

def _display_feed_list(feeds, start_idx, max_lines, max_width):  # Helper for feed display
    line_number = 1
    for idx in range(start_idx, min(start_idx + max_lines - 1, len(feeds.items()))):
        key, details = list(feeds.items())[idx]    # Extract feed details
        nickname = details['nickname']
        url = details['url']
        
        if len(nickname) > max_width:              # Handle long nicknames
            nickname = nickname[:max_width - 3] + "..."

        try:
            message_win.print(f"{key}: {nickname} ({url})")
            line_number += 1
        except curses.error:
            pass

# Input Handling Functions
def get_rss_urls(feeds):        # Main input handler for RSS URLs
    prompt = "Select a feed number or enter URL(s): "
    feed_scroll_idx = 0
    
    def display_callback():     # Updates feed display
        feeds = config.load_config()
        display_feeds(feeds, feed_scroll_idx)
        return None
    
    def handle_scroll(key):     # Handles scroll navigation
        nonlocal feed_scroll_idx
        if key == curses.KEY_DOWN and feed_scroll_idx < len(feeds) - 1:
            feed_scroll_idx += 1
        elif key == curses.KEY_UP and feed_scroll_idx > 0:
            feed_scroll_idx -= 1
            
    def resize_callback():      # Handles window resize
        nonlocal feed_scroll_idx
        feed_scroll_idx = 0
        return None
    
    def skip_callback():        # Handles skip action
        return utils.SKIP_HOTKEY
    
    def pgn_callback():
        return utils.PGN_HOTKEY
    
    
    hotkeys = {                 # Define keyboard shortcuts
        utils.SKIP_HOTKEY: (skip_callback, "break"),
        curses.KEY_DOWN: (lambda: handle_scroll(curses.KEY_DOWN), "scroll down"),
        curses.KEY_UP: (lambda: handle_scroll(curses.KEY_UP), "scroll up"),
        curses.KEY_RESIZE: (resize_callback, "resize"),
        utils.PGN_HOTKEY: (pgn_callback, "pgn"),
        utils.RESET_HOTKEY: (api_keyring.reset_credentials, "reset")
    }
    
    while True:
        selected_option = bottom_win.handle_input(prompt, callback=display_callback, hotkeys=hotkeys)
        if selected_option in [utils.SKIP_HOTKEY, utils.PGN_HOTKEY]:
            return selected_option
        
        if selected_option is None:      # Handle skip action
            return None
        
        display_callback()     # Refresh feed list
        feed_urls, feeds = _handle_feed_input(selected_option, feeds)
        if feed_urls:
            return feed_urls
        

# Feed Processing Functions
def _handle_feed_input(selected_option, feeds):    # Process user input for feeds
    if selected_option.isdigit():                  # Handle numeric selection
        return (_handle_feed_number(selected_option, feeds), feeds)
    
    if ',' in selected_option:                     # Handle multiple URLs
        return (None, _add_multiple_feeds(selected_option.split(','), feeds))
    
    if utils.is_valid_url(selected_option):        # Handle single URL
        return (None, _add_single_feed(selected_option, feeds))

    bottom_win.print("Invalid URL format. URL must start with ftp:// or http:// or https://")
    time.sleep(2)
    return (None, feeds)

def _handle_feed_number(selected_option, feeds):    # Process numeric feed selection
    if selected_option in feeds:
        return feeds[selected_option]['url']
    bottom_win.print(f"Invalid feed number: {selected_option}")
    time.sleep(2)
    return None

# Feed Management Functions
def _add_single_feed(url, feeds):    # Add one feed to config
    url = url.strip()
    if not _validate_feed_url(url, feeds):
        return feeds

    nickname = _get_feed_nickname(url, feeds)
    updated_config = config.update_config(url, nickname)
    bottom_win.print(f"Added feed '{url}' with nickname '{nickname}'.")
    time.sleep(2)
    return updated_config

def _validate_feed_url(url, feeds):   # Validate feed URL format and uniqueness
    if not utils.is_valid_url(url):
        bottom_win.print(f"Invalid URL '{url}'. Skipping...")
        time.sleep(2)
        return False

    if any(feed['url'] == url for feed in feeds.values()):
        bottom_win.print(f"Feed URL '{url}' already exists. Skipping...")
        time.sleep(2)
        return False
    
    return True

def _add_multiple_feeds(urls, feeds):  # Process multiple feed URLs
    for url in urls:
        feeds = _add_single_feed(url.strip(), feeds)
    return feeds

def _get_feed_nickname(url, feeds):    # Get user-defined nickname for feed
    def display_callback():            # Update feed display during input
        display_feeds(feeds, 0)
        return None
    
    while True: 
        nickname = bottom_win.handle_input(f"Enter a nickname for the new feed {url}: ", callback=display_callback).strip() 
        if nickname:
            return nickname
        bottom_win.print("Invalid nickname. Try again.")
        time.sleep(2)
