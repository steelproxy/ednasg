import curses
import time

global win

def display_articles(articles, start_idx):
    """Display a paginated list of articles in the window."""
    height, width = win.getmaxyx()
    max_lines = height - 1  # Reserve space for status bar and input prompt
    max_width = width - 2

    win.clear()
    win.addstr(0, 0, "Available Articles:")
    line_number = 1
    for idx in range(start_idx, min(start_idx + max_lines - 1, len(articles))):
        # Get article info
        article = articles[idx]
        title = article['title']
        date = article['date']
        date_str = time.strftime("%m,%d,%y", date)

        # Truncate title if needed
        if len(title) > max_width:
            title = title[:max_width - 3] + "..."

        try:
            win.addstr(line_number, 0, f"({date_str}) {idx + 1}. {title[:max_width]}")
            line_number += 1
        except curses.error:
            pass

    win.refresh()

def display_feeds(feeds, start_idx):
    """Display a paginated list of RSS feeds in the window."""
    height, width = win.getmaxyx()
    max_lines = height - 1  # Reserve space for status bar and input prompt
    max_width = width - 2  # Side margins

    win.clear()
    win.addstr(0, 0, "Available RSS Feeds:")
    line_number = 1
    for idx in range(start_idx, min(start_idx + max_lines - 1, len(feeds.items()))):
        # Get feed info
        key, details = list(feeds.items())[idx]
        nickname = details['nickname']
        url = details['url']
        
        # Truncate feed nickname if needed
        if len(nickname) > max_width:
            nickname = nickname[:max_width - 3] + "..."

        try:
            win.addstr(line_number, 0, f"{key}: {nickname} ({url})")
            line_number += 1
        except curses.error:
            pass

    win.refresh()

def display_script(script, start_idx=0):
    """Display the script in a scrollable manner with wrapped lines."""
    height, width = win.getmaxyx()
    max_lines = height - 1  # Reserve space for status bar
    max_width = width - 1  # Adjust for potential side margin
    lines = script.split('\n')

    # Wrap lines to fit within the window width
    wrapped_lines = []
    for line in lines:
        while len(line) > max_width:
            wrapped_lines.append(line[:max_width])
            line = line[max_width:]
        wrapped_lines.append(line)

    # Calculate the range of lines to display
    end_idx = min(start_idx + max_lines, len(wrapped_lines))

    # Clear the window and display the lines
    win.clear()
    for i in range(start_idx, end_idx):
        win.addstr(i - start_idx, 0, wrapped_lines[i])

    win.refresh()

def print(message):
    """Display a message in the window."""
    win.addstr(message + '\n')
    win.refresh()

def clear():
    """Clear the window."""
    win.clear()
    win.refresh()

def getch():
    """Get a character from the window."""
    return win.getch()
