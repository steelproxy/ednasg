import time
import curses
import feedparser
import bottom_win
import message_win
import utils
from pgn import pgn_search

# Main Public Functions
def get_manual_article():
    """Get manual article input from user."""
    title = _get_article_title()
    message_win.print(f"Title: {title}")
    summary = _get_article_summary()
    return [{'title': title, 'summary': summary, 'date': time.localtime(), 'url': None}]

def get_rss_articles(rss_url):
    """Fetch and parse articles from RSS feed."""
    message_win.erase()
    if rss_url != utils.PGN_HOTKEY:
        message_win.print("Fetching RSS feed...")
        try:
            feed = _fetch_and_validate_feed(rss_url)
            if feed is None:
                return None
            message_win.print("RSS feed fetched successfully.")
            time.sleep(2)
                
            articles = _extract_articles(feed)
            if not articles:
                _handle_no_articles()
                return None
                
            return _select_articles(articles)
            
        except Exception as e:
            _handle_feed_error(e)
            return None
    else:
        return _select_articles({})
            

# Display Functions
def _display_articles(articles, start_idx, url_visible=False):
    """Display a paginated list of articles in the window."""
    height, width = message_win.win.getmaxyx()
    max_lines = height - 1
    max_width = width - 2

    message_win.erase()
    message_win.print("Available Articles [Input as comma-separated numbers] ['/' to search, '?' to view urls]:")
    
    for idx, line_number in _get_visible_articles(articles, start_idx, max_lines):
        article = articles[idx]
        title = _format_article_title(article['title'].replace('\n', ' ') if not url_visible else article['url'].replace('\n', ' '), max_width)
        date_str = time.strftime("%m,%d,%Y %H:%M:%S", article['date'])
        
        try:
            message_win.print(f"({date_str}) {idx + 1}. {title}")
        except curses.error:
            pass
# Input Functions
def _get_article_title():
    """Get article title from user."""
    def resize_callback():
        message_win.win.erase()
        message_win.print("Manual input selected.")
        return None
    
    resize_callback()
    return bottom_win.handle_input(
        "Enter the title of the article: ",
        callback=None,
        hotkeys={curses.KEY_RESIZE: (resize_callback, "resize")}
    )

def _get_article_summary():
    """Get article summary from user."""
    return message_win.get_multiline_input(
        "Enter the summary of the article (ctrl + d to end input):"
    )

# RSS Processing Functions
def _fetch_and_validate_feed(rss_url):
    """Fetch and validate RSS feed."""
    feed = feedparser.parse(rss_url)
    if feed.bozo:
        message_win.print("Error parsing RSS feed. The feed may be invalid or improperly formatted.")
        time.sleep(2)
        return None
    return feed

def _extract_articles(feed):
    """Extract article data from feed entries."""
    return [
        {'date': entry.updated_parsed, 'title': entry.title, 'summary': entry.summary, 'url': entry.link}
        for entry in feed.entries
    ]

# Selection Functions
def _select_articles(articles):
    """Let user select articles from the list."""
    article_scroll_idx = 0
    filtered_articles = articles  # New: Keep track of filtered articles
    search_term = ""  # New: Keep track of current search term
    view_url = False

    def scroll_down():
        nonlocal article_scroll_idx
        if article_scroll_idx < len(filtered_articles) - 1:  # Changed: Use filtered_articles
            article_scroll_idx += 1
        return None
        
    def scroll_up():
        nonlocal article_scroll_idx
        if article_scroll_idx > 0:
            article_scroll_idx -= 1
        return None
    
    def resize_callback():
        nonlocal article_scroll_idx
        article_scroll_idx = 0
        return None

    def search_callback():  # New: Handle search functionality
        nonlocal filtered_articles, article_scroll_idx, search_term
        search_term = bottom_win.handle_input(
            "Search: ",
            lambda: _display_articles(filtered_articles, article_scroll_idx),
            max_input_len=100,
            hotkeys={
                curses.KEY_DOWN: (scroll_down, "Scroll down"),
                curses.KEY_UP: (scroll_up, "Scroll up"),
            }
        )
        article_scroll_idx = 0
        if search_term:
            filtered_articles = [
                article for article in articles
                if search_term.lower() in article['title'].lower()
            ]
        else:
            filtered_articles = articles
        return None
    
    def view_url_callback():
        nonlocal view_url
        view_url = True
        return None
    
    if not filtered_articles:
        resize_callback()
        filtered_articles = pgn_search()
        articles = filtered_articles
        if not articles:
            _handle_no_articles()
            return None
    
    choices = bottom_win.handle_input(
        "Enter your article selection: ",
        lambda: _display_articles(filtered_articles, article_scroll_idx, view_url),  # Changed: Use filtered_articles
        max_input_len=100,
        hotkeys={
            curses.KEY_DOWN: (scroll_down, "Scroll down"),
            curses.KEY_UP: (scroll_up, "Scroll up"),
            curses.KEY_RESIZE: (resize_callback, "Resize"),
            ord('/'): (search_callback, "Search"),  # New: Add search hotkey
            ord('?'): (view_url_callback, "url callback")
        }
    )
    
    selected_indices = _parse_article_selection(choices, len(filtered_articles))  # Changed: Use filtered_articles length
    if not selected_indices:
        return None
        
    # New: Map filtered indices back to original article indices
    if filtered_articles != articles:
        original_indices = []
        for filtered_idx in selected_indices:
            filtered_article = filtered_articles[filtered_idx]
            original_idx = articles.index(filtered_article)
            original_indices.append(original_idx)
        selected_indices = original_indices

    filtered_articles = [articles[i] for i in selected_indices]
    article_scroll_idx = 0
    while True:
        confirmation = bottom_win.handle_input(
            "Is your selection OK? (y/n) [y]: ",
            lambda: _display_articles(filtered_articles, article_scroll_idx, view_url),
            max_input_len=100,
            hotkeys={
                curses.KEY_DOWN: (scroll_down, "Scroll down"),
                curses.KEY_UP: (scroll_up, "Scroll up"),
                curses.KEY_RESIZE: (resize_callback, "Resize"),
                ord('?'): (view_url_callback, "url callback")
            }
        )
        if confirmation == "n":
            return None
        elif confirmation == "y" or confirmation == "":
            break
        bottom_win.print("Invalid input!")
        time.sleep(2)

    return filtered_articles

# Helper Functions
def _get_visible_articles(articles, start_idx, max_lines):
    """Get the range of visible articles."""
    return [(idx, line_number) for idx, line_number in 
            enumerate(range(1, max_lines), start=start_idx)
            if idx < len(articles)]

def _format_article_title(title, max_width):
    """Format article title to fit window width."""
    return f"{title[:max_width-3]}..." if len(title) > max_width else title

def _parse_article_selection(choices, max_len):
    """Parse and validate article selection input."""
    selected_numbers = [num.strip() for num in choices.split(',')]
    selected_indices = []
    
    for num in selected_numbers:
        if not num.isdigit():
            _handle_invalid_selection()
            return None
            
        index = int(num) - 1
        if not (0 <= index < max_len):
            _handle_invalid_selection()
            return None
            
        selected_indices.append(index)
    
    return selected_indices

# Error Handling Functions
def _handle_no_articles():
    """Handle case when no articles are found."""
    message_win.error("No articles found!")

def _handle_feed_error(error):
    """Handle feed parsing errors."""
    message_win.error(f"Error fetching RSS feed: {error}.")
    time.sleep(2)

def _handle_invalid_selection():
    """Handle invalid article selection."""
    bottom_win.print("Invalid selection. Ensure you enter valid article numbers.")
    time.sleep(2)
