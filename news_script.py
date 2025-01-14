import curses
import message_win
import bottom_win
import screen_manager
import utils
from openai import OpenAI
import time

DEFAULT_GPT_PROMPT = "Create a 99-second news anchor script for the following articles:"

def get_script(client, articles, custom_prompt):      # Generate news script using ChatGPT
    """Generate a news anchor script using ChatGPT based on the provided articles."""
    _validate_articles(articles)
    messages = _create_gpt_messages(articles, custom_prompt)
    
    try:
        response = client.chat.completions.create(        # Get response from OpenAI API
            model="gpt-4o",
            messages=messages,
            temperature=0.7
        )
    except Exception as e:
        utils.handle_openai_error(e, "GPT API call")
        utils.pause()
        return

    if not hasattr(response, 'choices') or not response.choices:          # Check response format
        raise ValueError("API response does not contain 'choices'")
    
    if not hasattr(response.choices[0], 'message') or not hasattr(response.choices[0].message, 'content'):
        raise ValueError("API response does not contain expected content")

    return response.choices[0].message.content.strip()

def display_scrollable_script(script):
    """Display the script in a scrollable window with user controls."""
    script_scroll_idx = 0
    max_y, max_x = message_win.win.getmaxyx()
    wrapped_lines = _wrap_text(script, max_x)
    
    while True:
        bottom_win.print("Use UP/DOWN keys or mouse wheel to scroll, 'q' to quit.")
        _display_script(script, script_scroll_idx)
        
        ch = bottom_win.getch()
        if hasattr(utils, "MOUSE_UP") and ch == curses.KEY_MOUSE:
            try:
                mouse_event = curses.getmouse()
                if mouse_event[4] & utils.MOUSE_UP:
                    ch = curses.KEY_UP
                elif mouse_event[4] & utils.MOUSE_DOWN:
                    ch = curses.KEY_DOWN
            except curses.error:
                continue
                
        if ch == ord('q'):
            break
            
        script_scroll_idx = _handle_scroll_input(ch, script_scroll_idx, wrapped_lines)

def get_save_filename():                              # Prompt for save location
    """Get the filename from user input with default option."""
    default_filename = "news_script.txt"
    while True:
        choice = bottom_win.getstr("Would you like to save this script? (y/n) [n]: ")
        if choice not in ["y", "n", ""]:
            bottom_win.print("Invalid selection!")
            time.sleep(2)
            continue
        elif choice == "y":
            filename = bottom_win.getstr(f"Filename to save to (default: {default_filename}): ").strip()
            return filename or default_filename
        else:
            break
    return ""
    

def write_script_to_file(filename, script):           # Handle file writing
    """Write the script content to the specified file."""
    try:
        with open(filename, 'w') as f:
            f.write(script)
        return True
    except IOError as e:
        message_win.error(f"Error saving file: {str(e)}")
    except Exception as e:
        message_win.error(f"Unexpected error saving file: {str(e)}")
    return False

def save_script_to_file(script):                      # Main save function
    """Save the script to a file with user-specified filename."""
    if not script:
        message_win.error("Error: No script content to save")
        return False

    filename = get_save_filename()
    if filename != "":
        if write_script_to_file(filename, script):        # Attempt to save
            bottom_win.print(f"Script written to file: {filename}")
            time.sleep(2)
            return True
        return False
    return True

def _display_script(script, start_idx=0):             # Show current script view
    """Display the current portion of the script in the window."""
    height, width = message_win.win.getmaxyx()
    max_lines = height - 1                            # Reserve bottom line
    max_width = width - 1                             # Account for borders
    wrapped_lines = _wrap_text(script, max_width)

    end_idx = min(start_idx + max_lines, len(wrapped_lines))
    
    message_win.win.erase()
    for i in range(start_idx, end_idx):               # Display visible lines
        message_win.win.addstr(i - start_idx, 0, wrapped_lines[i])
    message_win.win.refresh()

def _wrap_text(text, max_width):                      # Handle text wrapping
    """Wrap text to fit within the specified width."""
    lines = text.split('\n')
    wrapped_lines = []
    for line in lines:
        while len(line) > max_width:                  # Split long lines
            wrapped_lines.append(line[:max_width])
            line = line[max_width:]
        wrapped_lines.append(line)
    return wrapped_lines

def _validate_articles(articles):                      # Verify article format
    """Validate the structure of the articles list."""
    if not isinstance(articles, list):
        raise ValueError("Expected 'articles' to be a list")
    
    for article in articles:                           # Check each article
        if not isinstance(article, dict) or 'title' not in article or 'summary' not in article:
            raise ValueError("Each article should be a dictionary with 'title' and 'summary' keys")

def _create_gpt_messages(articles, custom_prompt):     # Prepare GPT API messages
    """Create the message structure for the GPT API request."""
    prompt = custom_prompt or DEFAULT_GPT_PROMPT
    return [
        {"role": "system", "content": "You are a helpful assistant that writes news anchor scripts."},
        {"role": "user", "content": f"{prompt}\n\n" +
         "\n".join(f"- {article['title']}: {article['summary']}" for article in articles)}
    ]
    
def _handle_scroll_input(ch, script_scroll_idx, wrapped_lines):    # Process scroll commands
    """Handle user input for scrolling through the script."""   
    max_y, max_x = message_win.win.getmaxyx()
    
    if ch == curses.KEY_DOWN:     # Handle scroll down
        if script_scroll_idx < len(wrapped_lines) - (max_y - 1):
            return script_scroll_idx + 1
    elif ch == curses.KEY_UP:     # Handle scroll up
        if script_scroll_idx > 0:
            return script_scroll_idx - 1
    elif ch == curses.KEY_RESIZE:                      # Handle window resize
        max_y, max_x = screen_manager.handle_resize()
        return 0
        
    return script_scroll_idx
