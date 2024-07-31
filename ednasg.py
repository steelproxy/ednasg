import feedparser
from openai import OpenAI
import curses
import keyring
import json
import os
import re
import time

CONFIG_FILE = 'rss_feeds.json'

## TODO add options to delete feeds

def print_bottom_bar(win, message):
    """Display a status bar with a message."""
    win.clear()
    height, width = win.getmaxyx()
    win.bkgd(' ', curses.color_pair(1))
    if len(message) > width - 2:  # Truncate message
        message = message[:width - 4] + '...'
    win.addstr(0, 0, message)
    win.refresh()

def get_custom_prompt(win):
    """Prompt the user to enter a custom ChatGPT prompt."""
    print_bottom_bar(win, "Enter custom prompt for ChatGPT (leave empty for default): ")
    return win.getstr().decode('utf-8').strip()

def get_chatgpt_script(client, articles, custom_prompt):
    """Generate a news anchor script using ChatGPT based on the provided articles."""
    # Error checking for 'articles'
    if not isinstance(articles, list):
        raise ValueError("Expected 'articles' to be a list")
    for article in articles:
        if not isinstance(article, dict) or 'title' not in article or 'summary' not in article:
            raise ValueError("Each article should be a dictionary with 'title' and 'summary' keys")

    if not custom_prompt:
        custom_prompt = "Create a 99-second news anchor script for the following articles:"

    messages = [
        {"role": "system", "content": "You are a helpful assistant that writes news anchor scripts."},
        {"role": "user", "content": f"{custom_prompt}\n\n" +
         "\n".join(f"- {article['title']}: {article['summary']}" for article in articles)}
    ]
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7
    )

    # Error checking for 'response'
    if not hasattr(response, 'choices') or not response.choices:
        raise ValueError("API response does not contain 'choices'")
    if not hasattr(response.choices[0], 'message') or not hasattr(response.choices[0].message, 'content'):
        raise ValueError("API response does not contain expected content")

    return response.choices[0].message.content.strip()

def get_api_key(win):
    """Fetch the OpenAI API key from the system keyring or prompt the user to enter it."""
    # keyring request
    service_id = "ednasg"
    key_id = "api_key"
    api_key = keyring.get_password(service_id, key_id)
    
    # get key if nonexistent
    while not api_key:
        print_bottom_bar(win, "Enter OpenAI API Key: ")
        api_key = win.getstr().decode('utf-8')

    keyring.set_password(service_id, key_id, api_key)
    return api_key

def display_articles(win, articles, start_idx):
    """Display a paginated list of articles in the window."""
    height, width = win.getmaxyx()
    max_lines = height - 1  # Reserve space for status bar and input prompt
    max_width = width - 2

    win.clear()
    win.addstr(0, 0, "Available Articles:")
    line_number = 1
    for idx in range(start_idx, min(start_idx + max_lines - 1, len(articles))):
        # get article info
        article = articles[idx]
        title = article['title']
        date = article['date']
        date_str = time.strftime("%m,%d,%y", date)

        # truncate title
        if len(title) > max_width:
            title = title[:max_width - 3] + "..."

        try:
            win.addstr(line_number, 0, f"({date_str}) {idx + 1}. {title[:max_width]}")
            line_number += 1
        except curses.error:
            pass

    win.refresh()

def display_feeds(win, feeds, start_idx):
    """Display a paginated list of RSS feeds in the window."""
    height, width = win.getmaxyx()
    max_lines = height - 1  # Reserve space for status bar and input prompt
    max_width = width - 2  # Side margins

    win.clear()
    win.addstr(0, 0, "Available RSS Feeds:")
    line_number = 1
    for idx in range(start_idx, min(start_idx + max_lines - 1, len(feeds.items()))):
        # get feed info
        key, details = list(feeds.items())[idx]
        nickname = details['nickname']
        url = details['url']
        
        # truncate feed
        if len(nickname) > max_width:
            nickname = nickname[:max_width - 3] + "..."

        try:
            win.addstr(line_number, 0, f"{key}: {nickname} ({url})")
            line_number += 1
        except curses.error:
            pass

    win.refresh()

def load_or_create_config(win):
    """Load configuration from file or create a new one if not found or invalid."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                feeds = json.load(f)
                # Check if loaded data is a dictionary
                if not isinstance(feeds, dict):
                    raise ValueError("Configuration file is not in expected format")
        except (json.JSONDecodeError, ValueError) as e:
            # Handle empty or invalid JSON file
            print_bottom_bar(win, f"Error reading configuration file: {e}. Press any key to create a new one...")
            win.getch()
            feeds = {}
        except Exception as e:
            # Handle other potential file errors
            print_bottom_bar(win, f"Unexpected error: {e}. Press any key to create a new one...")
            win.getch()
            feeds = {}
    else:
        # Prompt the user to create a config file
        print_bottom_bar(win, "No configuration file found. Press any key to create one...")
        win.getch()
        open(CONFIG_FILE, 'w').close()  # Create an empty file
        feeds = {}

    return feeds

def update_config(url, nickname):
    """Update the configuration file with a new URL and nickname."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                try:
                    feeds = json.load(f)
                    # Ensure feeds is a dictionary
                    if not isinstance(feeds, dict):
                        raise ValueError("Configuration file is not in expected format")
                except (json.JSONDecodeError, ValueError) as e:
                    # Handle empty or invalid JSON file
                    feeds = {}
        else:
            feeds = {}

        # Avoid duplicate URLs
        if not any(feed['url'] == url for feed in feeds.values()):
            new_key = str(len(feeds) + 1)
            feeds[new_key] = {"url": url, "nickname": nickname}
            with open(CONFIG_FILE, 'w') as f:
                json.dump(feeds, f, indent=4)
    except Exception as e:
        # Handle any exceptions that occur during file operations
        print(f"Error updating configuration: {e}")
    return feeds

def setup_windows(stdscr):
    """Initialize the curses windows."""
    term_height, term_width = stdscr.getmaxyx()
    message_area_win = curses.newwin(term_height - 1, term_width, 0, 0)
    bottom_bar_win = curses.newwin(1, term_width, term_height - 1, 0)
    bottom_bar_win.keypad(1)
    return message_area_win, bottom_bar_win

def get_rss_urls(stdscr, bottom_bar_win, message_area_win, feeds):
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
                    print_bottom_bar(bottom_bar_win, f"Enter a nickname for the new feed '{url}': ")
                    while not (nickname := bottom_bar_win.getstr().decode('utf-8').strip()):
                        print_bottom_bar(bottom_bar_win, "Invalid nickname. Press any key to continue...")
                        bottom_bar_win.getch()
                        print_bottom_bar(bottom_bar_win, f"Enter a nickname for the new feed '{url}': ")
                    feeds = update_config(url, nickname)
                else:
                    print_bottom_bar(bottom_bar_win, f"Feed URL '{url}' already exists. Skipping...")
            else:
                print_bottom_bar(bottom_bar_win, f"Invalid URL '{url}'. Skipping...")
            time.sleep(0.1)  # Short delay to prevent rapid input issues
        return feeds
    
    while True:
        print_bottom_bar(bottom_bar_win, "Select a feed number, enter a single URL, or enter multiple URLs (ctrl+n to skip): ")
        
        feed_scroll_idx = 0
        selected_option = ""
        while True:
            display_feeds(message_area_win, feeds, feed_scroll_idx)
            
            ch = bottom_bar_win.getch()
            print_bottom_bar(bottom_bar_win, "Select a feed number, enter a single URL, or enter multiple URLs (ctrl+n to skip): " + selected_option)
            
            if ch == curses.KEY_DOWN and feed_scroll_idx < len(feeds.items()) - 1: # scroll down
                feed_scroll_idx += 1
            elif ch == curses.KEY_UP and feed_scroll_idx > 0: # scroll up
                feed_scroll_idx -= 1
            elif ch == ord('\n'): # newline
                break
            elif ch == 127:  # Backspace key
                selected_option = selected_option[:-1]
                print_bottom_bar(bottom_bar_win, "Select a feed number, enter a single URL, or enter multiple URLs (ctrl+n to skip): " + selected_option)
            elif ch == curses.KEY_RESIZE: # resize
                # Resize handling
                stdscr.clear()
                stdscr.refresh()
                message_area_win, bottom_bar_win = setup_windows(stdscr)
                feed_scroll_idx = 0
                print_bottom_bar(bottom_bar_win, "Select a feed number, enter a single URL, or enter multiple URLs (ctrl+n to skip): " + selected_option)
            elif ch == 14: # ctrl+n
                return None
            elif ch != curses.KEY_UP and ch != curses.KEY_DOWN and ch != ord('\n'): # valid character
                selected_option += chr(ch)
                print_bottom_bar(bottom_bar_win, "Select a feed number, enter a single URL, or enter multiple URLs (ctrl+n to skip): " + selected_option)
        
        if selected_option.isdigit() and selected_option in feeds:
            # Valid feed number
            return feeds[selected_option]['url']
        
        elif selected_option:
            # Either a single URL or multiple URLs
            urls = [url.strip() for url in selected_option.split(',')]
            feeds = add_feeds(feeds, urls)
        
        else:
            # Prompt the user again if the input is invalid
            print_bottom_bar(bottom_bar_win, "Invalid selection. Press any key to continue...")
            bottom_bar_win.getch()

def setup_curses(stdscr):
    """Initialize curses settings."""
    curses.curs_set(1)
    curses.echo()
    stdscr.keypad(1)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    stdscr.clear()

def display_script(message_win, script, start_idx=0):
    """Display the script in a scrollable manner."""
    height, width = message_win.getmaxyx()
    max_lines = height - 1  # Reserve space for status bar
    lines = script.split('\n')

    # Calculate the range of lines to display
    end_idx = min(start_idx + max_lines, len(lines))

    # Clear the window and display the lines
    message_win.clear()
    for i in range(start_idx, end_idx):
        message_win.addstr(i - start_idx, 0, lines[i])
    
    message_win.refresh()

def main(stdscr):
    # Setup windows
    setup_curses(stdscr)
    message_area_win, bottom_bar_win = setup_windows(stdscr)
    
    # Get credentials and connect to API
    message_area_win.addstr("Finding API key...\n")
    api_key = get_api_key(bottom_bar_win)
    message_area_win.addstr(f"API KEY: {'*' * len(api_key)}\n")
    client = OpenAI(api_key=api_key)
    
    # Load or create the configuration file
    message_area_win.addstr("Loading RSS config...\n")
    feeds = load_or_create_config(bottom_bar_win)
    
    # Print error if feed list doesn't exist
    if not feeds:
        message_area_win.addstr("No RSS config loaded!\n")
        message_area_win.refresh()

    # Get selected option
    rss_url = get_rss_urls(stdscr, bottom_bar_win, message_area_win, feeds)

    # refresh window info if resize occurred in get_rss_urls
    stdscr.clear()
    stdscr.refresh()
    message_area_win, bottom_bar_win = setup_windows(stdscr)
    
    if rss_url is None:
        print_bottom_bar(bottom_bar_win, "Enter the title of the article:")
        title = bottom_bar_win.getstr().decode('utf-8').strip()
        print_bottom_bar(bottom_bar_win, "Enter the summary of the article:")
        summary = bottom_bar_win.getstr().decode('utf-8').strip()
        date = time.localtime()  # Current date
        selected_articles = [{'title': title, 'summary': summary, 'date': date}]
    else:
        # Get articles from RSS
        print_bottom_bar(bottom_bar_win, "Fetching RSS feed...")
        try:
            feed = feedparser.parse(rss_url)
            
            # Check for feed parsing errors
            if feed.bozo:
                message_area_win.addstr("Error parsing RSS feed. The feed may be invalid or improperly formatted.\n")
                message_area_win.refresh()
                print_bottom_bar(bottom_bar_win, "Press any key to exit...")
                bottom_bar_win.getch()
                return 1

            # Extract articles from feed
            articles = [{'date': entry.updated_parsed, 'title': entry.title, 'summary': entry.summary} for entry in feed.entries]
            
            # Ensure there are articles in the feed
            if not articles:
                message_area_win.addstr("No articles found in the RSS feed.\n")
                message_area_win.refresh()
                print_bottom_bar(bottom_bar_win, "Press any key to exit...")
                bottom_bar_win.getch()
                return 1

        except Exception as e:
            # Handle different types of exceptions (e.g., network errors, URL errors)
            message_area_win.addstr(f"Error fetching RSS feed: {e}.")
            message_area_win.refresh()
            print_bottom_bar(bottom_bar_win, "Press any key to exit...")
            bottom_bar_win.getch()  # Wait for user input before proceeding
            return  1 # Exit or handle the error as needed

        print_bottom_bar(bottom_bar_win, "Enter the numbers of articles to include (comma-separated): ")
        
        article_scroll_idx = 0
        choices = ""
        while True:
            display_articles(message_area_win, articles, article_scroll_idx)
            print_bottom_bar(bottom_bar_win, "Enter the numbers of articles to include (comma-separated): " + choices)
            
            ch = bottom_bar_win.getch()
            
            if ch == curses.KEY_DOWN and article_scroll_idx < len(articles) - 1:
                article_scroll_idx += 1
            elif ch == curses.KEY_UP and article_scroll_idx > 0:
                article_scroll_idx -= 1
            elif ch == 127:  # Backspace key
                choices = choices[:-1]
            elif ch == ord('\n'):
                break
            elif ch == curses.KEY_RESIZE:
                # Resize handling
                stdscr.clear()
                stdscr.refresh()
                message_area_win, bottom_bar_win = setup_windows(stdscr)
                article_scroll_idx = 0
            elif ch != curses.KEY_UP and ch != curses.KEY_DOWN and ch != ord('\n'):
                choices += chr(ch)

        # Get user's input for article selection
        selected_indices = [int(num.strip()) - 1 for num in choices.split(',') if num.strip().isdigit()]
        selected_articles = [articles[i] for i in selected_indices]

    # Get custom prompt
    custom_prompt = get_custom_prompt(bottom_bar_win)
    print_bottom_bar(bottom_bar_win, "Generating news anchor script...")
    script = get_chatgpt_script(client, selected_articles, custom_prompt)
    print_bottom_bar(bottom_bar_win, "Use UP/DOWN keys to scroll, 'q' to quit.")
    
    # Display the script in a scrollable manner
    script_scroll_idx = 0
    while True:
        display_script(message_area_win, script, script_scroll_idx)
        
        ch = bottom_bar_win.getch()
        if ch == curses.KEY_DOWN and script_scroll_idx < len(script.split('\n')) - 1:
            script_scroll_idx += 1
        elif ch == curses.KEY_UP and script_scroll_idx > 0:
            script_scroll_idx -= 1
        elif ch == ord('q'):
            break
        elif ch == curses.KEY_RESIZE:
            # Resize handling
            stdscr.clear()
            stdscr.refresh()
            message_area_win, bottom_bar_win = setup_windows(stdscr)
            script_scroll_idx = 0
    
    print_bottom_bar(bottom_bar_win, "Filename to save to (default: news_script.txt): ")
    filename = bottom_bar_win.getstr().decode('utf-8').strip()
    
    if filename == "":
        filename = "news_script.txt"
   
    with open(filename, 'w') as f:
        f.write(script)
        
    message_area_win.clear()
    message_area_win.addstr(f"Script written to file: {filename}")
    message_area_win.refresh()
    
    print_bottom_bar(bottom_bar_win, "Press any button to exit...")
    message_area_win.getch()

if __name__ == "__main__":
    curses.wrapper(main)
