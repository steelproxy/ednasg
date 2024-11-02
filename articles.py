import time
import curses
import feedparser
import bottom_win
import message_win

# Display Functions
def display_articles(articles, start_idx):
    """Display a paginated list of articles in the window."""
    height, width = message_win.win.getmaxyx()
    max_lines = height - 1
    max_width = width - 2

    message_win.win.clear()
    message_win.win.addstr(0, 0, "Available Articles:")
    
    for idx, line_number in _get_visible_articles(articles, start_idx, max_lines):
        article = articles[idx]
        title = _format_article_title(article['title'], max_width)
        date_str = time.strftime("%m,%d,%y", article['date'])
        
        try:
            message_win.win.addstr(line_number, 0, f"({date_str}) {idx + 1}. {title}")
        except curses.error:
            pass

    message_win.win.refresh()

# Article Input Functions
def get_manual_article():
    """Get manual article input from user."""
    title = _get_article_title()
    message_win.print(f"Title: {title}")
    summary = _get_article_summary()
    return [{'title': title, 'summary': summary, 'date': time.localtime()}]

def get_rss_articles(rss_url):
    """Fetch and parse articles from RSS feed."""
    bottom_win.print("Fetching RSS feed...")
    try:
        feed = feedparser.parse(rss_url)
        if _check_feed_errors(feed):
            return None
            
        articles = _extract_articles(feed)
        if not articles:
            _handle_no_articles()
            return None
            
        return _select_articles(articles)
        
    except Exception as e:
        _handle_feed_error(e)
        return None

# Article Selection Functions
def _select_articles(articles):
    """Let user select articles from the list."""
    article_scroll_idx = 0
    def scroll_down():
        nonlocal article_scroll_idx
        if article_scroll_idx < len(articles) - 1:
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
    
    choices = bottom_win.handle_input(
        "Enter the numbers of articles to include (comma-separated): ",
        lambda: display_articles(articles, article_scroll_idx),
        max_input_len=100,
        hotkeys={
            curses.KEY_DOWN: (scroll_down, "Scroll down"),
            curses.KEY_UP: (scroll_up, "Scroll up"),
            curses.KEY_RESIZE: (resize_callback, "Resize")
        }
    )
    
    selected_indices = _parse_article_selection(choices, len(articles))
    return [articles[i] for i in selected_indices] if selected_indices else None

# Helper Functions - Display
def _get_visible_articles(articles, start_idx, max_lines):
    """Get the range of visible articles."""
    return [(idx, line_number) for idx, line_number in 
            enumerate(range(1, max_lines), start=start_idx)
            if idx < len(articles)]

def _format_article_title(title, max_width):
    """Format article title to fit window width."""
    return f"{title[:max_width-3]}..." if len(title) > max_width else title

# Helper Functions - Input
def _get_article_title():
    """Get article title from user."""
    def resize_callback():
        message_win.clear()
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

# Helper Functions - RSS
def _check_feed_errors(feed):
    """Check for feed parsing errors."""
    if feed.bozo:
        message_win.print("Error parsing RSS feed. The feed may be invalid or improperly formatted.")
        time.sleep(2)
        return True
    return False

def _extract_articles(feed):
    """Extract article data from feed entries."""
    return [
        {'date': entry.updated_parsed, 'title': entry.title, 'summary': entry.summary}
        for entry in feed.entries
    ]

def _handle_no_articles():
    """Handle case when no articles are found."""
    message_win.print("No articles found in the RSS feed.")
    time.sleep(2)

def _handle_feed_error(error):
    """Handle feed parsing errors."""
    message_win.print(f"Error fetching RSS feed: {error}.")
    time.sleep(2)

# Helper Functions - Selection

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

def _handle_invalid_selection():
    """Handle invalid article selection."""
    bottom_win.print("Invalid selection. Ensure you enter valid article numbers.")
    time.sleep(2)
