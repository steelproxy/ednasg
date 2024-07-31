import keyring
import json
import os
import bottom_win

CONFIG_FILE = 'rss_feeds.json'

def update_config(url, nickname):
    """Update the configuration file with a new URL and nickname."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                try:
                    feeds = json.load(f)
                    # Ensure feeds is a dictionary
                    if not isinstance(feeds, dict):
                        raise ValueError("Configuration file is not in expected format")
                except (json.JSONDecodeError, ValueError) as e:
                    # Handle empty or invalid JSON file
                    feeds = {}
        else:
            feeds = {}

        # Avoid duplicate URLs
        if not any(feed['url'] == url for feed in feeds.values()):
            new_key = str(len(feeds) + 1)
            feeds[new_key] = {"url": url, "nickname": nickname}
            with open(CONFIG_FILE, 'w') as f:
                json.dump(feeds, f, indent=4)
    except Exception as e:
        # Handle any exceptions that occur during file operations
        raise ValueError(f"Error updating configuration: {e}")
    return feeds

def get_api_key():
    """Fetch the OpenAI API key from the system keyring or prompt the user to enter it."""
    # keyring request
    service_id = "ednasg"
    key_id = "api_key"
    api_key = keyring.get_password(service_id, key_id)
    
    if api_key is None:
        while not api_key:
            bottom_win.print("Enter OpenAI API Key: ")
            api_key = bottom_win.getstr()
    
    # get key if nonexistent
    while not api_key:
        return None

    keyring.set_password(service_id, key_id, api_key)
    return api_key

def load_or_create_config():
    """Load configuration from file or create a new one if not found or invalid."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                feeds = json.load(f)
                # Check if loaded data is a dictionary
                if not isinstance(feeds, dict):
                    raise ValueError("Configuration file is not in expected format")
        except (json.JSONDecodeError, ValueError) as e:
            # Handle empty or invalid JSON file
            bottom_win.print(f"Error reading configuration file: {e}. Press any key to create a new one...")
            bottom_win.getch()
            feeds = {}
        except Exception as e:
            # Handle other potential file errors
            bottom_win.print(f"Unexpected error: {e}. Press any key to create a new one...")
            bottom_win.getch()
            feeds = {}
    else:
        # Prompt the user to create a config file
        bottom_win.print("No configuration file found. Press any key to create one...")
        bottom_win.getch()
        open(CONFIG_FILE, 'w').close()  # Create an empty file
        feeds = {}

    return feeds