import feedparser
from openai import OpenAI
import curses
import keyring
import json
import os

CONFIG_FILE = 'rss_feeds.json'

# Function to display a status bar and input prompt in the same window
def print_bottom_bar(win, message):
    height, width = win.getmaxyx()
    win.bkgd(' ', curses.color_pair(1))
    
    win.clear()
    
    # Display status message
    win.addstr(0, 0, message, curses.color_pair(1))
    
    win.refresh()

def fetch_rss_feed(url):
    return feedparser.parse(url)

def get_chatgpt_script(client, api_key, articles):
    messages = [
        {"role": "system", "content": "You are a helpful assistant that writes news anchor scripts."}
    ]

    prompt = "Create a 99-second news anchor script for the following articles:\n\n"
    for article in articles:
        prompt += f"- {article['title']}: {article['summary']}\n"

    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7
    )

    return response.choices[0].message.content.strip()

def get_api_key(win):
    service_id = "ednasg"
    key_id = "api_key"
    
    api_key = keyring.get_password(service_id, key_id)
    if not api_key:
        print_bottom_bar(win, "Enter OpenAI API Key: ")
        api_key = win.getstr().decode('utf-8')
        keyring.set_password(service_id, key_id, api_key)
    
    return api_key

def display_articles(win, articles):
    win.clear()
    height, width = win.getmaxyx()
    max_lines = height - 2  # Reserve space for status bar and input prompt
    max_width = width - 2

    win.addstr(0, 0, "Available Articles:")
    line_number = 1
    for idx, article in enumerate(articles):
        if line_number >= max_lines:
            break

        title = article['title']

        if len(title) > max_width:
            title = title[:max_width - 3] + "..."

        try:
            win.addstr(line_number, 0, f"{idx + 1}. {title[:max_width]}")
            line_number += 1
        except curses.error:
            pass

    win.refresh()

def load_or_create_config(win):
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        # Prompt the user to create a config file
        print_bottom_bar(win, "No configuration file found. Enter an RSS feed URL to create one: ")
        new_feed_url = win.getstr().decode('utf-8').strip()

        if new_feed_url:
            feeds = { "1": new_feed_url }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(feeds, f)
            return feeds
        else:
            return {}

def main(stdscr):
    curses.curs_set(1)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.echo()
    
    height, width = stdscr.getmaxyx()
    message_area_win = curses.newwin(height - 1, width, 0, 0)
    bottom_bar_win = curses.newwin(1, width, height - 1, 0)

    stdscr.clear()
    
    message_area_win.addstr(0, 0, f"Loading rss config...\n")
    
    # Load or create the configuration file
    feeds = load_or_create_config(bottom_bar_win)
    
    if not feeds:
        message_area_win.addstr(f"No RSS feed URL provided. Exiting.\n")
        message_area_win.refresh()
        print_bottom_bar(bottom_bar_win, "Press any button to exit...\n")
        bottom_bar_win.getch()
        return

    # Allow user to select from available feeds
    message_area_win.addstr(f"Available RSS feeds: \n")
    for key, url in feeds.items():
        message_area_win.addstr(f"    {key}: {url}\n")
        message_area_win.refresh()
    print_bottom_bar(bottom_bar_win, "Select a feed number or enter a new URL: ")
    
    selected_option = bottom_bar_win.getstr().decode('utf-8').strip()
    
    rss_url = feeds.get(selected_option) if selected_option in feeds else selected_option

    if not rss_url:
        message_area_win.addstr(f"Invalid feed selection. Exiting.")
        message_area_win.refresh()
        print_bottom_bar(bottom_bar_win, "Press any key to exit...")
        bottom_bar_win.getch()
        return

    api_key = get_api_key(bottom_bar_win)
    client = OpenAI(api_key=api_key)

    print_bottom_bar(bottom_bar_win, "Fetching RSS feed...")
    feed = fetch_rss_feed(rss_url)
    articles = [{'title': entry.title, 'summary': entry.summary} for entry in feed.entries]

    display_articles(message_area_win, articles)

    # Display the prompt in the same location as the status bar
    print_bottom_bar(bottom_bar_win, "Enter the numbers of articles to include (comma-separated): ")

    # Get user's input for article selection
    choices = bottom_bar_win.getstr().decode('utf-8')
    selected_indices = [int(num.strip()) - 1 for num in choices.split(',') if num.strip().isdigit()]
    selected_articles = [articles[i] for i in selected_indices]

    print_bottom_bar(bottom_bar_win, "Generating news anchor script...")

    script = get_chatgpt_script(client, api_key, selected_articles)

    message_area_win.clear()
    message_area_win.addstr(0, 0, f"News script successfully generated!")
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
