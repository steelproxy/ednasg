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


def main(stdscr):
    """Main application entry point."""
    _setup_environment(stdscr)

    try:
        # Initialize API and configuration
        client = _initialize_api()
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
    """Setup initial environment and signal handlers."""
    signal.signal(signal.SIGINT, utils.signal_handler)
    screen_manager.stdscr = stdscr
    screen_manager.setup_curses()
    screen_manager.setup_windows()
    utils.update_repo()  # Optional repo update


def _initialize_api():
    """Initialize API connection."""
    message_win.print("Finding API key...")
    api_key = config.get_api_key()
    message_win.print(f"API KEY: {'*' * len(api_key)}")
    try:
        client = OpenAI(api_key=api_key)
        # Test the client with a simple API call
        client.models.list()
        return client
    except Exception as e:
        utils._fatal_error(f"Error initializing OpenAI client: {str(e)}!")


def _initialize_config():
    """Initialize feed configuration."""
    message_win.print("Loading RSS config...")
    feeds = config.load_config()
    _display_welcome_message()
    return feeds

# Content Collection Functions


def _get_article_content(feeds):
    """Get articles either from RSS or manual input."""
    rss_url = rss_feeds.get_rss_urls(feeds)
    if rss_url is None:  # Manual input
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
    """Generate news script from selected articles."""
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
    message_win.print("Welcome to ednasg!")
    bottom_win.print("Press any button to continue...")
    if bottom_win.getch() == curses.KEY_RESIZE:
        screen_manager.handle_resize()


if __name__ == "__main__":
    curses.wrapper(main)
