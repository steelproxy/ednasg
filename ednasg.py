import curses
import signal
from openai import OpenAI
import config
import bottom_win
import message_win
import rss_feeds
import screen_manager
import utils
import articles
import news_script
import api_keyring

def main(stdscr):
    """Main application entry point."""
    _setup_environment(stdscr)

    try:
        # Initialize OpenAI API and configuration
        client = _initialize_openai_api()
        feeds = _initialize_config()

        # Get article content
        selected_articles = _get_article_content(feeds)

        # Generate and display script
        script = _generate_script(client, selected_articles)
        news_script.display_scrollable_script(script)
        news_script.save_script_to_file(script)

        utils._wait_for_exit()

    except KeyboardInterrupt:
        utils._handle_exit()

# Initialization Functions

def _setup_environment(stdscr):
    """Setup initial environment and signal handlers.
    
    Args:
        stdscr: The main curses window object
    """
    signal.signal(signal.SIGINT, utils.signal_handler)
    screen_manager.stdscr = stdscr
    screen_manager.setup_curses()
    screen_manager.setup_windows()
    utils.update_repo()  # Optional repo update

def _initialize_openai_api():
    """Initialize OpenAI API connection.
    
    Returns:
        OpenAI: Configured OpenAI client instance
        
    Raises:
        Exception: If API initialization fails
    """

    message_win.baprint("Finding OpenAI API key...")
    api_key = api_keyring.get_openai_api_key()
    message_win.baprint(f"API KEY: {api_key[:4]}{'*' * (len(api_key)-4)}")
    try:
        message_win.baprint("Initializing OpenAI client...")
        client = OpenAI(api_key=api_key)
        # Test the client with a simple API call
        client.models.list()
        message_win.baprint("OpenAI client initialized successfully!")
        return client
    except Exception as e:
        message_win.baprint(f"Error initializing OpenAI client: {str(e)}!")
        choice = bottom_win.handle_input("Would you like to reset your credentials? [y/n]: ", callback=message_win.print_buffer)
        if choice == "y":
            api_keyring.reset_credentials()
        else:
            utils._fatal_error(f"Unable to initialize OpenAI client. Please check your credentials and try again.")

def _initialize_config():
    """Initialize feed configuration."""
    message_win.baprint("Loading RSS config...")
    feeds = config.load_config()
    _display_welcome_message()
    return feeds

# Content Collection Functions

def _get_article_content(feeds):
    """Get articles either from RSS or manual input.
    
    Args:
        feeds: Dictionary of RSS feeds and their configurations
    
    Returns:
        list: Selected articles with their content
    """
    rss_url = rss_feeds.get_rss_urls(feeds)
    if rss_url is utils.CTRL_N:  # Manual input
        return articles.get_manual_article()
        
    while True:
        selected_articles = articles.get_rss_articles(rss_url)
        if selected_articles is not None:
            return selected_articles

        rss_url = rss_feeds.get_rss_urls(feeds)
        feeds = config.load_config()  # Reload config after adding new feeds
        if rss_url is None:  # User chose manual input
            return articles.get_manual_article()


def _generate_script(client, selected_articles):
    """Generate news script from selected articles.
    
    Args:
        client: OpenAI client instance
        selected_articles: List of articles to generate script from
        
    Raises:
        Exception: If script generation fails
    """
    custom_prompt = message_win.get_multiline_input(
        "Enter custom prompt for ChatGPT (ctrl+d to end, empty for default):"
    )
    bottom_win.print("Generating news anchor script...")
    try:
        script = news_script.get_script(
            client, selected_articles, custom_prompt)
        return script
    except Exception as e:
        utils._fatal_error(
            f"Unable to generate news script! caught exception: {str(e)}")

# Display Functions

def _display_welcome_message():
    """Display welcome message and wait for user input."""
    message_win.baprint("Welcome to ednasg!")
    bottom_win.print("Press any button to continue...")
    if bottom_win.getch() == curses.KEY_RESIZE:
        screen_manager.handle_resize()
    message_win.clear_buffer()


if __name__ == "__main__":
    curses.wrapper(main)
