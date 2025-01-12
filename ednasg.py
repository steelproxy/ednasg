import curses
import signal
from openai import OpenAI
import config
import bottom_win
import rss_feeds
import screen_manager
import utils
import articles
import news_script
import api_keyring
import time
import scrape
import dalle
from message_win import print_msg
from message_win import clear_buffer
from message_win import get_multiline_input
from bottom_win import bgetstr

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

        # DALL-E generation
        use_dalle = _dalle_prompt(client, script)

        utils.wait_for_exit()

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

    print_msg("Finding OpenAI API key...")
    api_key = api_keyring.get_openai_api_key()
    print_msg(f"API KEY: {api_key[:4]}{'*' * (len(api_key)-4)}")
    try:
        print_msg("Initializing OpenAI client...")
        client = OpenAI(api_key=api_key)
        # Test the client with a simple API call
        client.models.list()
        print_msg("OpenAI client initialized successfully!")
        return client
    except Exception as e:
        print_msg(f"Error initializing OpenAI client: {str(e)}!")
        choice = bgetstr("Would you like to reset your credentials? [y/n]: ")
        if choice == "y":
            api_keyring.reset_credentials()
        else:
            utils._fatal_error(f"Unable to initialize OpenAI client. Please check your credentials and try again.")

def _initialize_config():
    """Initialize feed configuration."""
    print_msg("Loading RSS config...")
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

    if rss_url is utils.SKIP_HOTKEY:  # Manual input
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
    clear_buffer()
    print_msg("HINT: if you have manually inputted an article, just hit enter.")
    print_msg("There are multiple ways to use the content from your selected articles. They both have their pros and cons.")
    print_msg("1: Summary (DEFAULT): The summary of these articles will be fed to ChatGPT for usage, this is by far the fastest, but may miss context.")
    print_msg("2: Newspaper4k Scraping: Each article will be scraped by url for it's content, some more complicated sites may not work with this method and it is slower.")
    print_msg("3: Headless browser: Still not implemented.")

    while True:
        scrape_method = bgetstr("Please input your method [1]: ")
        match scrape_method:
            case "":
                break
            case "1":
                break
            case "2":
                selected_articles = scrape.scrape_article_content(selected_articles)
                break
            case "3":
                bottom_win.print("STILL NOT IMPLEMENTED! Sorry :(")
                time.sleep(2)
                continue
            case _:
                bottom_win.print("Invalid selection!")
                time.sleep(2)
            
    custom_prompt = get_multiline_input(
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

def _dalle_prompt(client, script):
    clear_buffer()
    print_msg("WARNING!! STILL IN DEVELOPMENT!")
    print_msg("Using OpenAI's DALL-E 3 AI photo generation tool this program can generate pictures to use in your news script.")
    print_msg("The program will first ask ChatGPT to analyse any keywords in your generated script and then use those as context for the photo generation.")
    print_msg("The results may not always be what you are looking for, but the functionality is here.")
    while True:
        choice = bgetstr("Would you like to generate photos? (y/n) [n]: ")
        if choice == "y":
            dalle.generate_photos(client, script)
            break
        elif choice in ["n", ""]:
            break
        else:
            bottom_win.print("Invalid selection!")
            time.sleep(2)

# Display Functions

def _display_welcome_message():
    """Display welcome message and wait for user input."""
    print_msg("Welcome to ednasg!")
    bottom_win.print("Press any button to continue...")
    if bottom_win.getch() == curses.KEY_RESIZE:
        screen_manager.handle_resize()
    clear_buffer()


if __name__ == "__main__":
    curses.wrapper(main)
