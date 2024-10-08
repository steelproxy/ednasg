import keyring
import json
import os
import bottom_win
from jsonschema import validate, ValidationError

CONFIG_FILE = 'rss_feeds.json'

# Define a schema for the RSS feed configuration
feed_schema = {
    "type": "object",
    "patternProperties": {
        "^[0-9]+$": {  # The keys are numbers as strings
            "type": "object",
            "properties": {
                "url": {"type": "string", "format": "uri"},
                "nickname": {"type": "string"}
            },
            "required": ["url", "nickname"]
        }
    },
    "additionalProperties": False
}

def load_config():
    """Load and validate the configuration file, or return an empty dictionary."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                feeds = json.load(f)
                validate(instance=feeds, schema=feed_schema)  # Validate the JSON against the schema
                return feeds
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            bottom_win.print(f"Configuration error: {e}. Press any key to reset...")
            bottom_win.getch()
            return {}
        except Exception as e:
            bottom_win.print(f"Unexpected error: {e}. Press any key to continue...")
            bottom_win.getch()
            return {}
    return {}

def update_config(url, nickname):
    """Update the configuration file with a new URL and nickname."""
    try:
        feeds = load_config()  # Load and validate existing config
        if not any(feed['url'] == url for feed in feeds.values()):
            new_key = str(len(feeds) + 1)
            feeds[new_key] = {"url": url, "nickname": nickname}
            validate(instance=feeds, schema=feed_schema)  # Validate the updated data
            with open(CONFIG_FILE, 'w') as f:
                json.dump(feeds, f, indent=4)
        else:
            bottom_win.print("URL already exists in the configuration.")
    except ValidationError as e:
        bottom_win.print(f"Invalid data format: {e}")
    except Exception as e:
        bottom_win.print(f"Error updating configuration: {e}")
    
    return feeds

def get_api_key():
    """Fetch the OpenAI API key from the system keyring or prompt the user to enter it."""
    if os.name == 'nt':
        keyring.set_keyring(keyring.backends.Windows.WinVaultKeyring())
    
    service_id = "ednasg"
    key_id = "api_key"
    api_key = keyring.get_password(service_id, key_id)
    
    if api_key is None:
        while not api_key:
            bottom_win.print("Enter OpenAI API Key: ")
            api_key = bottom_win.getstr()
    
    # Store the key if it was newly entered
    if api_key:
        keyring.set_password(service_id, key_id, api_key)
    
    return api_key

def load_or_create_config():
    """Load or create a configuration file if it doesn't exist."""
    feeds = load_config()
    
    if not feeds:
        bottom_win.print("No valid configuration found. Press any key to create a new one...")
        bottom_win.getch()
        with open(CONFIG_FILE, 'w') as f:
            json.dump({}, f, indent=4)
    
    return feeds
