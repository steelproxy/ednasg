import keyring
import json
import os
import bottom_win
from jsonschema import validate, ValidationError
from keyring.backends.Windows import WinVaultKeyring

CONFIG_FILE = 'rss_feeds.json'
SERVICE_ID = "ednasg"
KEY_ID = "api_key"

# Define schema for RSS feed configuration
FEED_SCHEMA = {
    "type": "object",
    "patternProperties": {
        "^[0-9]+$": {
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
    """Load and validate the configuration file."""
    if not os.path.exists(CONFIG_FILE):
        return {}
        
    try:
        with open(CONFIG_FILE, 'r') as f:
            feeds = json.load(f)
            validate(instance=feeds, schema=FEED_SCHEMA)
            return feeds
    except (json.JSONDecodeError, ValidationError) as e:
        bottom_win.print(f"Configuration error: {e}. Press any key to reset...")
        bottom_win.getch()
        return {}
    except Exception as e:
        bottom_win.print(f"Unexpected error: {e}. Press any key to continue...")
        bottom_win.getch()
        return {}

def update_config(url, nickname):
    """Add a new feed to the configuration."""
    try:
        feeds = load_config()
        
        # Check for duplicate URLs
        if any(feed['url'] == url for feed in feeds.values()):
            bottom_win.print("URL already exists in the configuration.")
            return feeds
            
        # Add new feed
        new_key = str(len(feeds) + 1)
        feeds[new_key] = {"url": url, "nickname": nickname}
        validate(instance=feeds, schema=FEED_SCHEMA)
        
        # Save updated config
        with open(CONFIG_FILE, 'w') as f:
            json.dump(feeds, f, indent=4)
            
        return feeds
        
    except ValidationError as e:
        bottom_win.print(f"Invalid data format: {e}")
    except Exception as e:
        bottom_win.print(f"Error updating configuration: {e}")
    
    return load_config()  # Return current config if update failed

def get_api_key():
    """Fetch or prompt for OpenAI API key."""
    if os.name == 'nt':
        keyring.set_keyring(WinVaultKeyring())
    
    api_key = keyring.get_password(SERVICE_ID, KEY_ID)
    
    # Prompt for key if not found
    if not api_key:
        api_key = bottom_win.getstr("Enter OpenAI API Key: ")
        if api_key:
            keyring.set_password(SERVICE_ID, KEY_ID, api_key)
    
    return api_key

def load_or_create_config():
    """Initialize configuration file if needed."""
    feeds = load_config()
    
    if not feeds:
        bottom_win.print("No valid configuration found. Creating new config...")
        with open(CONFIG_FILE, 'w') as f:
            json.dump({}, f, indent=4)
    
    return feeds
