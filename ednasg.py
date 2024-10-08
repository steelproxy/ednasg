import subprocess
import feedparser
import curses
import time
from openai import OpenAI
import config
import bottom_win
import message_win
import gpt
import input
import os
from setup_windows import setup_windows

def update_repo():
    """Run the update script to fetch the latest code from GitHub."""
    if (os.name == 'nt'): # Windows
        return

    try:
        result = subprocess.run(["python", "update_script.py"], check=True)
        if result.returncode == 0:
            message_win.print("Repository updated successfully.")
        else:
            message_win.print("Update script failed. Proceeding with the current version...")
    except subprocess.CalledProcessError as e:
        message_win.print(f"Failed to run update script: {e}")
        message_win.print("Proceeding with the current version...")

def setup_curses():
    """Initialize curses settings."""
    curses.curs_set(1)
    curses.echo()
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    setup_windows.stdscr.keypad(1)
    setup_windows.stdscr.clear()

def main(stdscr):
    # Setup windows
    setup_windows.stdscr = stdscr
    
    setup_curses()
    setup_windows()
    
    # Update the repo before starting the main application
    update_repo()
    
    # Get credentials and connect to API
    message_win.print("Finding API key...")
    api_key = config.get_api_key()
    message_win.print(f"API KEY: {'*' * len(api_key)}")
    client = OpenAI(api_key=api_key)
    
    # Load or create the configuration file
    message_win.print("Loading RSS config...")
    feeds = config.load_or_create_config()

    message_win.print("Welcome to ednasg!")
    bottom_win.print("Press any button to continue...")
    bottom_win.getch()

    # Refresh window info if resize occurred in get_rss_urls
    stdscr.clear()
    stdscr.refresh()
    setup_windows()

    # Get selected option
    rss_url = input.get_rss_urls(feeds)

    # Refresh window info if resize occurred in get_rss_urls
    stdscr.clear()
    stdscr.refresh()
    setup_windows()
    
    if rss_url is None:  # Manual input
        message_win.print("Manual input selected.")
        title = bottom_win.getstr("Enter the title of the article:")
        message_win.print(f"Title: {title}")
        summary = input.get_multiline_input("Enter the summary of the article (ctrl + d to end input):")
        date = time.localtime()  # Current date
        selected_articles = [{'title': title, 'summary': summary, 'date': date}]
        setup_windows()
    else:
        # Get articles from RSS
        bottom_win.print("Fetching RSS feed...")
        try:
            feed = feedparser.parse(rss_url)
            
            # Check for feed parsing errors
            if feed.bozo:
                message_win.print("Error parsing RSS feed. The feed may be invalid or improperly formatted.")
                bottom_win.print("Press any key to exit...")
                bottom_win.getch()
                return 1

            # Extract articles from feed
            articles = [
                {'date': entry.updated_parsed, 'title': entry.title, 'summary': entry.summary}
                for entry in feed.entries
            ]
            if not articles:
                message_win.print("No articles found in the RSS feed.")
                bottom_win.print("Press any key to exit...")
                bottom_win.getch()
                return 1

        except Exception as e:
            # Handle different types of exceptions (e.g., network errors, URL errors)
            message_win.print(f"Error fetching RSS feed: {e}.")
            bottom_win.print("Press any key to exit...")
            bottom_win.getch()  # Wait for user input before proceeding
            return 1  # Exit or handle the error as needed

        bottom_win.print("Enter the numbers of articles to include (comma-separated): ")
        
        article_scroll_idx = 0
        cursor_pos = 0  # Tracks cursor position in the input string
        choices = ""
        while True:
            message_win.display_articles(articles, article_scroll_idx)
            bottom_win.print("Enter the numbers of articles to include (comma-separated): " + choices)
            
            ch = bottom_win.getch()
            
            if ch == curses.KEY_DOWN and article_scroll_idx < len(articles) - 1:
                article_scroll_idx += 1
            elif ch == curses.KEY_UP and article_scroll_idx > 0:
                article_scroll_idx -= 1
            elif ch in (curses.KEY_LEFT, 452) and cursor_pos > 0:
                cursor_pos -= 1  # Move cursor left
            elif ch in (curses.KEY_RIGHT, 454) and cursor_pos < len(choices):
                cursor_pos += 1  # Move cursor right
            elif ch in (curses.KEY_BACKSPACE, 127, '\b'):  # Backspace key
                if cursor_pos > 0:
                    choices = choices[:cursor_pos - 1] + choices[cursor_pos:]
                    cursor_pos -= 1
            elif ch == ord('\n'):
                break
            elif ch == curses.KEY_RESIZE:
                # Resize handling
                stdscr.clear()
                stdscr.refresh()
                setup_windows()
                article_scroll_idx = 0
            elif ch not in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, 452, curses.KEY_RIGHT, 454, ord('\n')):
                choices = choices[:cursor_pos] + chr(ch) + choices[cursor_pos:]
                cursor_pos += 1

        # Get user's input for article selection
        selected_numbers = [num.strip() for num in choices.split(',')]
        selected_indices = []
        invalid_input = False

        for num in selected_numbers:
            if num.isdigit():
                index = int(num) - 1
                if 0 <= index < len(articles):
                    selected_indices.append(index)
                else:
                    invalid_input = True
            else:
                invalid_input = True

        if invalid_input:
            bottom_win.print("Invalid input. Ensure you enter valid article numbers. Press any key to exit...")
            bottom_win.getch()  # Wait for user input before exiting
            return  # Exit the current function or handle the error as needed

        selected_articles = [articles[i] for i in selected_indices]

    # Get custom prompt
    custom_prompt = input.get_multiline_input("Enter custom prompt for ChatGPT (ctrl+d to end, empty for default):")
    bottom_win.print("Generating news anchor script...")
    script = gpt.get_script(client, selected_articles, custom_prompt)
    
    # Display the script in a scrollable manner
    script_scroll_idx = 0
    while True:
        bottom_win.print("Use UP/DOWN keys to scroll, 'q' to quit.")
        message_win.display_script(script, script_scroll_idx)
        
        ch = bottom_win.getch()
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
            setup_windows()
            script_scroll_idx = 0
    
    bottom_win.print("Filename to save to (default: news_script.txt): ")
    filename = bottom_win.getstr()
    
    if filename == "":
        filename = "news_script.txt"
   
    with open(filename, 'w') as f:
        f.write(script)
        
    message_win.clear()
    message_win.print(f"Script written to file: {filename}")
    
    bottom_win.print("Press any button to exit...")
    bottom_win.getch()

if __name__ == "__main__":
    curses.wrapper(main)
