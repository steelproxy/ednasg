import feedparser
from openai import OpenAI
import curses
import keyring

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

def main(stdscr):
    curses.curs_set(1)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.echo()
    
    # Create a window for status and input prompt
    height, width = stdscr.getmaxyx()
    
    message_area_win = curses.newwin(height - 1, width, 0, 0)
    bottom_bar_win = curses.newwin(1, width, height - 1, 0)
    
    stdscr.clear()
    
    print_bottom_bar(bottom_bar_win, "Enter RSS feed URL: ")
    rss_url = bottom_bar_win.getstr().decode('utf-8')

    api_key = get_api_key(bottom_bar_win)
    client = OpenAI(api_key=api_key)

    print_bottom_bar(bottom_bar_win, "Fetching rss feed...")
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
    filename = bottom_bar_win.getstr().decode('utf-8')
    
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
