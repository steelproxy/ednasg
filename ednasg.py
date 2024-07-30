import feedparser
from openai import OpenAI
import curses
import keyring
import json
import os
import re
import time

CONFIG_FILE = 'rss_feeds.json'

def print_bottom_bar(win, message):
    """Display a status bar and input prompt in the given window."""
    win.clear()
    win.bkgd(' ', curses.color_pair(1))
    win.addstr(0, 0, message)
    win.refresh()


def get_chatgpt_script(client, articles):
    """Generate a news anchor script using ChatGPT based on the provided articles."""
    # Error checking for 'articles'
    if not isinstance(articles, list):
        raise ValueError("Expected 'articles' to be a list")
    for article in articles:
        if not isinstance(article, dict) or 'title' not in article or 'summary' not in article:
            raise ValueError("Each article should be a dictionary with 'title' and 'summary' keys")

    messages = [
        {"role": "system", "content": "You are a helpful assistant that writes news anchor scripts."},
        {"role": "user", "content": "Create a 99-second news anchor script for the following articles:\n\n" +
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
    service_id = "ednasg"
    key_id = "api_key"
    api_key = keyring.get_password(service_id, key_id)
    
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
        article = articles[idx]
        title = article['title']
        date = article['date']
        date_str = time.strftime("%m,%d,%y", date)

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
    max_width = width - 2 # side margins

    win.clear()
    win.addstr(0, 0, "Available RSS Feeds:")
    line_number = 1
    for idx in range(start_idx, min(start_idx + max_lines - 1, len(feeds.items()))):
        key, details = list(feeds.items())[idx]
        nickname = details['nickname']
        url = details['url']
        
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

# Function to save configuration file
def update_config(url, nickname):
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

def setup_windows(stdscr):
    term_height, term_width = stdscr.getmaxyx()
    message_area_win = curses.newwin(term_height - 1, term_width, 0, 0)
    bottom_bar_win = curses.newwin(1, term_width, term_height - 1, 0)
    bottom_bar_win.keypad(1)
    return message_area_win, bottom_bar_win

def get_rss_url(stdscr, bottom_bar_win, message_area_win, feeds):
    """Prompt the user for a feed number or a new URL until a valid selection is provided."""
    
    def is_valid_url(url):
        """Basic URL validation using regex."""
        return re.match(r'^(https?|ftp)://[^\s/$.?#].[^\s]*$', url) is not None

    while True:   
        print_bottom_bar(bottom_bar_win, "Select a feed number or enter a new URL: ")   
        
        # Display available RSS feeds with scrolling
        feed_scroll_idx = 0
        selected_option = ""
        while True:   
            display_feeds(message_area_win, feeds, feed_scroll_idx)
            
            ch = bottom_bar_win.getch()
            print_bottom_bar(bottom_bar_win, "Select a feed number or enter a new URL: " + selected_option)
            
            if ch == curses.KEY_DOWN and feed_scroll_idx < len(feeds.items()):
                feed_scroll_idx += 1
            elif ch == curses.KEY_UP and feed_scroll_idx > 0:
                feed_scroll_idx -= 1
            elif ch == ord('\n'):
                break
            elif ch == 127:  # Backspace key
                selected_option = selected_option[:-1]
                print_bottom_bar(bottom_bar_win, "Select a feed number or enter a new URL: " + selected_option)
            elif ch == curses.KEY_RESIZE:
                # Resize handling
                stdscr.clear()
                stdscr.refresh()
                message_area_win, bottom_bar_win = setup_windows()
                feed_scroll_idx = 0
                print_bottom_bar(bottom_bar_win, "Select a feed number or enter a new URL: " + selected_option)
            elif ch != curses.KEY_UP and ch != curses.KEY_DOWN and ch != ord('\n'):
                selected_option += chr(ch)
                print_bottom_bar(bottom_bar_win, "Select a feed number or enter a new URL: " + selected_option)
                
        
        if selected_option.isdigit() and selected_option in feeds:
            # Valid feed number
            return feeds[selected_option]['url']
        
        elif selected_option and is_valid_url(selected_option):
            # Valid URL
            print_bottom_bar(bottom_bar_win, "Enter a nickname for the new feed: ")
            while not (nickname := bottom_bar_win.getstr().decode('utf-8').strip()):
                print_bottom_bar(bottom_bar_win, "Invalid nickname. Press any key to continue...")
                bottom_bar_win.getch()
                print_bottom_bar(bottom_bar_win, "Enter a nickname for the new feed: ")
            
            update_config(selected_option, nickname)
            return selected_option
        
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

def main(stdscr):
    # setup windows
    setup_curses(stdscr)
    message_area_win, bottom_bar_win = setup_windows()
    
    # get credentials and connect to API
    message_area_win.addstr("Finding API key...\n")
    api_key = get_api_key(bottom_bar_win)
    message_area_win.addstr(f"API KEY: {'*' * len(api_key)}\n")
    client = OpenAI(api_key=api_key)
    
    # Load or create the configuration file
    message_area_win.addstr("Loading RSS config...\n")
    feeds = load_or_create_config(bottom_bar_win)
    
    # Print error if feed list doesn't exist.
    if not feeds:
        message_area_win.addstr("No RSS config loaded!\n")
        message_area_win.refresh()

    # get selected option
    rss_url = get_rss_url(stdscr, bottom_bar_win, message_area_win, feeds)

    # get articles from rss
    print_bottom_bar(bottom_bar_win, "Fetching RSS feed...")
    feed = feedparser.parse(rss_url)
    articles = [{'date': entry.updated_parsed, 'title': entry.title, 'summary': entry.summary} for entry in feed.entries]

    print_bottom_bar(bottom_bar_win, "Enter the numbers of articles to include (comma-separated): ")

    # Display articles with arrow key scrolling
    article_scroll_idx = 0
    choices = ""
    while True:
        display_articles(message_area_win, articles, article_scroll_idx)
        print_bottom_bar(bottom_bar_win, "Enter the numbers of articles to include (comma-separated): " + choices)
        
        ch = bottom_bar_win.getch()
        
        if ch == curses.KEY_DOWN and article_scroll_idx < len(articles):
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
            message_area_win, bottom_bar_win = setup_windows()
            article_scroll_idx = 0
        elif ch != curses.KEY_UP and ch != curses.KEY_DOWN and ch != ord('\n'):
            choices += chr(ch)


    # Get user's input for article selection
    selected_indices = [int(num.strip()) - 1 for num in choices.split(',') if num.strip().isdigit()]
    selected_articles = [articles[i] for i in selected_indices]

    print_bottom_bar(bottom_bar_win, "Generating news anchor script...")

    script = get_chatgpt_script(client, selected_articles)

    message_area_win.clear()
    message_area_win.addstr(0, 0, "News script successfully generated!")
    message_area_win.refresh()
    
    print_bottom_bar(bottom_bar_win, "Filename to save to (default: news_script.txt): ")
    filename = bottom_bar_win.getstr().decode('utf-8').strip()
    
    if filename == "":
        filename = "news_script.txt"
   
    with open(filename, 'w') as f:
        f.write(script)
        
    message_area_win.addstr(1, 0, f"Script written to file: {filename}")
    message_area_win.refresh()
    
    print_bottom_bar(bottom_bar_win, "Press any button to exit...")
    message_area_win.getch()

if __name__ == "__main__":
    curses.wrapper(main)
