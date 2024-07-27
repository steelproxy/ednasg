import feedparser
from openai import OpenAI
import curses
import keyring

# Function to display a status bar
def display_status_bar(win, message):
    height, width = win.getmaxyx()
    status_bar = curses.newwin(1, width, height - 1, 0)
    status_bar.bkgd(' ', curses.color_pair(1))
    status_bar.addstr(0, 0, message, curses.color_pair(1))
    status_bar.refresh()

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

    # Use the optimized GPT-4 model (replace 'gpt-4o' with the exact model name if different)
    response = client.chat.completions.create(
        model="gpt-4o",  # Using GPT-4 with optimizations
        messages=messages,
        temperature=0.7
    )

    # Access the content of the response
    return response.choices[0].message.content.strip()

def get_api_key(stdscr):
    service_id = "ednasg"
    key_id = "api_key"
    
    api_key = keyring.get_password(service_id, key_id)
    if not api_key:
        stdscr.addstr(1, 0, "Enter OpenAI API key: ")
        stdscr.refresh()
        api_key = stdscr.getstr().decode('utf-8')
        keyring.set_password(service_id, key_id, api_key)
    
    return api_key

def main(stdscr):
    # Initialize curses
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.echo()

    # Get RSS feed URL from the user
    stdscr.clear()
    stdscr.addstr(0, 0, "Enter RSS feed URL: ")
    stdscr.refresh()
    rss_url = stdscr.getstr().decode('utf-8')

    # Get API key from keyring or prompt user
    api_key = get_api_key(stdscr)
    client = OpenAI(api_key=api_key)

    # Fetch and display RSS feed
    feed = fetch_rss_feed(rss_url)
    articles = [{'title': entry.title, 'summary': entry.summary} for entry in feed.entries]

    stdscr.clear()
    display_status_bar(stdscr, "Fetching RSS feed and preparing article list...")

    # Get terminal dimensions
    height, width = stdscr.getmaxyx()

    # Calculate maximum number of lines and width for articles
    max_lines = height - 3  # Leave space for status bar and margins
    max_width = width - 2   # Leave margins on the sides

    # Display articles
    stdscr.addstr(0, 0, "Available Articles:")
    line_number = 1
    for idx, article in enumerate(articles):
        if line_number >= max_lines:
            break

        title = article['title']

        # Truncate title to fit within the available width
        if len(title) > max_width:
            title = title[:max_width - 3] + "..."

        try:
            stdscr.addstr(line_number, 0, f"{idx + 1}. {title[:max_width]}")
            line_number += 1
        except curses.error:
            pass

    stdscr.addstr(line_number + 2, 0, "Enter the numbers of articles to include (comma-separated): ")
    stdscr.refresh()

    # Get user's choice
    choices = stdscr.getstr().decode('utf-8')
    selected_indices = [int(num.strip()) - 1 for num in choices.split(',') if num.strip().isdigit()]
    selected_articles = [articles[i] for i in selected_indices]

    # Generate script with ChatGPT
    display_status_bar(stdscr, "Generating news anchor script...")
    script = get_chatgpt_script(client, api_key, selected_articles)

    # Save script to files
    file_name = "news_script.txt"
    with open(file_name, 'w') as f:
        f.write(script)

    stdscr.clear()
    stdscr.addstr(0, 0, f"News script saved to {file_name}")
    stdscr.refresh()
    stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)
