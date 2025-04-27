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
from message_win import swap_buffer
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
        _dalle_prompt(client, script)

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
            
    clear_buffer()
    print_msg("Your script will be generated using a prompt to ChatGPT.")
    print_msg("You can enter a custom prompt to use, or leave it blank to use the default prompt.")
    print_msg(f"The default prompt is: {news_script.DEFAULT_GPT_PROMPT}")
    print_msg("If you would like to use the default prompt, just press enter. Otherwise, answer 'y' to the prompt below.")
    print_msg("If you would like to export the articles, answer 'e' to the prompt below.")
    while True:
        choice = bgetstr("Would you like to make a custom prompt? (y/n/e) [n]: ")
        if choice == "e":
            _export_articles(selected_articles)
            continue
        elif choice in ["n", ""]:
            custom_prompt = news_script.DEFAULT_GPT_PROMPT
            break
        elif choice == "y":
            custom_prompt = get_multiline_input(
                "Enter custom prompt for ChatGPT (ctrl+d to end, empty for default):"
            )
            break
        else:
            bottom_win.print("Invalid selection!")
            time.sleep(2)
            continue

    bottom_win.print("Generating news anchor script...")
    try:
        script = news_script.get_script(
            client, selected_articles, custom_prompt)
        return script
    except Exception as e:
        utils._fatal_error(
            f"Unable to generate news script! caught exception: {str(e)}")

def _export_articles(selected_articles):
    """Export articles to a file."""
    saved_buffer = swap_buffer([])
    print_msg("Exporting articles...")
    for article in selected_articles:
        try:
            with open('articles_export.txt', 'a', encoding='utf-8', errors='ignore') as f:
                f.write(f"- {article['title']}\n")
                f.write(f"Link: {utils.sanitize_output(article['url'])}\n")
                f.write("\n")
        except IOError as e:
            print_msg(f"Error writing to file: {e}")
            bottom_win.bgetstr("Press any button to continue...")
            return
    print_msg("Articles exported successfully!")
    bottom_win.bgetstr("Press any button to continue...")
    swap_buffer(saved_buffer)

def _dalle_prompt(client, script):
    clear_buffer()
    print_msg("WARNING!! STILL IN DEVELOPMENT!")
    print_msg("Using OpenAI's DALL-E 3 AI photo generation tool this program can generate pictures to use in your news script.")
    print_msg("The program will first ask ChatGPT to analyse any keywords in your generated script and then use those as context for the photo generation.")
    print_msg("The results may not always be what you are looking for, but the functionality is here.")
    print_msg("The more photos you generate, the more expensive it will be.")
    while True:
        choice = bgetstr("Would you like to generate photos? (y/n) [n]: ")
        if choice == "y":
            while True:
                num_images = bgetstr("How many images would you like to generate? [3]: ")
                if num_images == "":
                    num_images = 3
                    break
                else:
                    try:
                        num_images = int(num_images)
                        break
                    except ValueError:
                        bottom_win.print("Invalid input! Please enter a number.")
                        time.sleep(2)
                        continue

            print_msg("There are two image quality options, standard and hd.")
            print_msg("Standard is the default and cheaper, but the images may not be as high quality.")
            print_msg("HD is more expensive and takes longer to generate, but the images will be of higher quality.")
            while True:
                image_quality = bgetstr("What quality would you like the images to be? (standard/hd) [standard]: ")
                if image_quality in ["standard", "hd"]:
                    break
                elif image_quality == "":
                    image_quality = "standard"
                    break
                else:
                    bottom_win.print("Invalid selection!")
                    time.sleep(2)
                    continue

            DALLE_RESOLUTIONS = {
                "1": {"size": "1024x1024", "description": "Square format"},
                "2": {"size": "1792x1024", "description": "Landscape format"},
                "3": {"size": "1024x1792", "description": "Portrait format"}
            }    
            print_msg("There are several image resolutions to choose from:")
            for key, value in DALLE_RESOLUTIONS.items():
                print_msg(f"{key}. {value['size']} - {value['description']}")
            
            while True:
                choice = bgetstr("Please select a resolution (higher cost, higher resolution) [1]: ")
                if choice == "" or choice in DALLE_RESOLUTIONS:
                    resolution = DALLE_RESOLUTIONS[choice or "1"]["size"]
                    break
                else:
                    bottom_win.print("Invalid selection!")
                    time.sleep(2)

            dalle.generate_photos(client, script, num_images, image_quality, resolution)
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
