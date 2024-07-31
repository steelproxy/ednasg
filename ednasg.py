import feedparser
import curses
import time
from openai import OpenAI
import config
import bottom_win
import message_win
import gpt
import input
from setup_windows import setup_windows

def setup_curses(stdscr):
    """Initialize curses settings."""
    curses.curs_set(1)
    curses.echo()
    stdscr.keypad(1)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    stdscr.clear()


def main(stdscr):
    # Setup windows
    setup_curses(stdscr)
    setup_windows(stdscr)
    
    # Get credentials and connect to API
    message_win.print("Finding API key...")
    api_key = config.get_api_key()
    message_win.print(f"API KEY: {'*' * len(api_key)}")
    client = OpenAI(api_key=api_key)
    
    # Load or create the configuration file
    message_win.print("Loading RSS config...")
    feeds = config.load_or_create_config()
    
    # Print error if feed list doesn't exist
    if not feeds:
        message_win.print("No RSS config loaded!")

    # Get selected option
    rss_url = input.get_rss_urls(stdscr, feeds)

    # refresh window info if resize occurred in get_rss_urls
    stdscr.clear()
    stdscr.refresh()
    setup_windows(stdscr)
    
    if rss_url is None: # manual input
        message_win.print("Manual input selected.")
        bottom_win.print("Enter the title of the article:")
        title = bottom_win.getstr()
        message_win.print(f"Title: {title}")
        summary = input.get_multiline_input(stdscr, "Enter the summary of the article (ctrl + d to end input):")
        date = time.localtime()  # Current date
        selected_articles = [{'title': title, 'summary': summary, 'date': date}]
        setup_windows(stdscr)
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
            articles = [{'date': entry.updated_parsed, 'title': entry.title, 'summary': entry.summary} for entry in feed.entries]
            
            # Ensure there are articles in the feed
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
            return  1 # Exit or handle the error as needed

        bottom_win.print("Enter the numbers of articles to include (comma-separated): ")
        
        article_scroll_idx = 0
        choices = ""
        while True:
            message_win.display_articles(articles, article_scroll_idx)
            bottom_win.print("Enter the numbers of articles to include (comma-separated): " + choices)
            
            ch = bottom_win.getch()
            
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
                setup_windows(stdscr)
                article_scroll_idx = 0
            elif ch != curses.KEY_UP and ch != curses.KEY_DOWN and ch != ord('\n'):
                choices += chr(ch)

        # Get user's input for article selection
        selected_indices = [int(num.strip()) - 1 for num in choices.split(',') if num.strip().isdigit()]
        selected_articles = [articles[i] for i in selected_indices]

    # Get custom prompt
    custom_prompt = input.get_multiline_input(stdscr, "Enter custom prompt for ChatGPT (ctrl+d for default):")
    bottom_win.print("Generating news anchor script...")
    script = gpt.get_script(client, selected_articles, custom_prompt)
    bottom_win.print("Use UP/DOWN keys to scroll, 'q' to quit.")
    
    # Display the script in a scrollable manner
    script_scroll_idx = 0
    while True:
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
            setup_windows(stdscr)
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
