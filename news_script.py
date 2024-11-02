import curses
import message_win
import bottom_win
import screen_manager
from openai import OpenAI
import time

DEFAULT_GPT_PROMPT = "Create a 99-second news anchor script for the following articles:"

def _display_script(script, start_idx=0):
    """Display the script in a scrollable manner with wrapped lines."""
    height, width = message_win.win.getmaxyx()
    max_lines = height - 1  # Reserve space for status bar
    max_width = width - 1  # Adjust for potential side margin
    lines = script.split('\n')

    # Use _wrap_text to wrap lines
    wrapped_lines = _wrap_text(script, max_width)

    # Calculate the range of lines to display
    end_idx = min(start_idx + max_lines, len(wrapped_lines))

    # Clear the window and display the lines
    message_win.win.clear()
    for i in range(start_idx, end_idx):
        message_win.win.addstr(i - start_idx, 0, wrapped_lines[i])

    message_win.win.refresh()

def _wrap_text(text, max_width):
    """Wrap text to fit within specified width."""
    lines = text.split('\n')
    wrapped_lines = []
    for line in lines:
        while len(line) > max_width:
            wrapped_lines.append(line[:max_width])
            line = line[max_width:]
        wrapped_lines.append(line)
    return wrapped_lines

def get_script(client, articles, custom_prompt):
    """Generate a news anchor script using ChatGPT based on the provided articles."""
    
    # Error checking for 'articles'
    if not isinstance(articles, list):
        raise ValueError("Expected 'articles' to be a list")
    
    for article in articles:
        if not isinstance(article, dict) or 'title' not in article or 'summary' not in article:
            raise ValueError("Each article should be a dictionary with 'title' and 'summary' keys")

    # Default prompt if not provided
    if not custom_prompt:
        custom_prompt = DEFAULT_GPT_PROMPT

    # Construct messages for the API call
    messages = [
        {"role": "system", "content": "You are a helpful assistant that writes news anchor scripts."},
        {"role": "user", "content": f"{custom_prompt}\n\n" +
         "\n".join(f"- {article['title']}: {article['summary']}" for article in articles)}
    ]
    
    # Get response from OpenAI API
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7
    )

    # Error checking for 'response'
    if not hasattr(response, 'choices') or not response.choices:
        raise ValueError("API response does not contain 'choices'")
    
    if not hasattr(response.choices[0], 'message') or not hasattr(response.choices[0].message, 'content'):
        raise ValueError("API response does not contain expected content")

    return response.choices[0].message.content.strip()

def display_scrollable_script(script):
    """Display the script in a scrollable manner."""
    script_scroll_idx = 0
    max_y, max_x = message_win.win.getmaxyx()
    wrapped_lines = _wrap_text(script, max_x)
    
    while True:
        bottom_win.print("Use UP/DOWN keys to scroll, 'q' to quit.")
        _display_script(script, script_scroll_idx)
        
        ch = bottom_win.getch()
        if ch == curses.KEY_DOWN:
            if script_scroll_idx < len(wrapped_lines) - (max_y - 1):
                script_scroll_idx += 1
        elif ch == curses.KEY_UP:
            if script_scroll_idx > 0:
                script_scroll_idx -= 1
        elif ch == ord('q'):
            break
        elif ch == curses.KEY_RESIZE:
            max_y, max_x = screen_manager.handle_resize()
            wrapped_lines = _wrap_text(script, max_x)
            script_scroll_idx = 0
def save_script_to_file(script):
    """Save the script to a file."""
    if not script:
        bottom_win.print("Error: No script content to save")
        return False

    default_filename = "news_script.txt"
    filename = bottom_win.getstr(f"Filename to save to (default: {default_filename}): ").strip()
    if not filename:
        filename = default_filename

    try:
        with open(filename, 'w') as f:
            f.write(script)
    except IOError as e:
        bottom_win.print(f"Error saving file: {str(e)}")
        return False
    except Exception as e:
        bottom_win.print(f"Unexpected error saving file: {str(e)}")
        return False
    bottom_win.print(f"Script written to file: {filename}")
    time.sleep(2)
    return True