import keyring
import json
import os
import bottom_win
import sys
import message_win
from time import sleep
from jsonschema import validate, ValidationError
from keyring.backends.Windows import WinVaultKeyring

CONFIG_FILE = 'rss_feeds.json'
SERVICE_ID = "ednasg"
KEY_ID = "api_key"
USERNAME_ID = "oxylabs_username"
PASSWORD_ID = "oxylabs_password"

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
    
    config_path = _get_config_path()
    try:
        if not os.path.exists(config_path): # Check if config file exists
            _handle_no_config()
        with open(config_path, 'r') as f: # Open config file
            feeds = json.load(f) # Load config
            validate(instance=feeds, schema=FEED_SCHEMA) # Validate config
            return feeds
    except (json.JSONDecodeError, ValidationError) as e: # Handle JSON errors
        _handle_json_error(e)
        _handle_exit()
    except Exception as e:
        _handle_error(e)
        _handle_exit()


def update_config(url, nickname):
    """Add a new feed to the configuration."""
    feeds = load_config() # Load config, no need to catch errors, will exit if error
    try:
        # Check for duplicate URLs
        if any(feed['url'] == url for feed in feeds.values()):
            bottom_win.print("URL already exists in the configuration.")
            return feeds
            
        # Add new feed
        new_key = str(len(feeds) + 1)
        feeds[new_key] = {"url": url, "nickname": nickname}
        validate(instance=feeds, schema=FEED_SCHEMA) # Validate config
        
        # Save updated config
        with open(_get_config_path(), 'w') as f:
            json.dump(feeds, f, indent=4)
            
        return feeds
        
    except ValidationError as e:
        _handle_json_error(e)
        return load_config()  # Return current config if update failed
    except Exception as e:
        _handle_error(e) 
        return load_config()  # Return current config if update failed
    

def reset_credentials():
    """Reset credentials."""
    def draw_callback():
        message_win.erase()
        message_win.print("Resetting credentials...")
        
    api_key = bottom_win.getstr("Enter your API key: ", callback=draw_callback)
    if not _set_api_key(api_key):
        return _handle_reset_credentials_error()
    username = bottom_win.getstr("Enter your Oxylabs username: ", callback=draw_callback)
    password = bottom_win.getstr("Enter your Oxylabs password: ", callback=draw_callback)   
    if not _set_oxylabs_credentials(username, password):
        return _handle_reset_credentials_error()
    bottom_win.print("Credentials reset.")
    sleep(2)
    return None

def _handle_reset_credentials_error():
    """Handle reset credentials error."""
    message_win.print("Unable to reset credentials.")
    sleep(2)
    return None

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

def get_oxylabs_credentials():
    """Fetch or prompt for Oxylabs credentials."""
    if os.name == 'nt':
        keyring.set_keyring(WinVaultKeyring())
    
    username = keyring.get_password(SERVICE_ID, USERNAME_ID)
    password = keyring.get_password(SERVICE_ID, PASSWORD_ID)
    
    if not username or not password:
        username = bottom_win.getstr("Enter Oxylabs Username [leave blank to skip]: ")
        if username:
            password = bottom_win.getstr("Enter Oxylabs Password [leave blank to skip]: ")
            if password:
                _set_oxylabs_credentials(username, password)

    return username, password

# Helpers

def _get_config_path():
    # determine if application is a script file or frozen exe
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)

    return os.path.join(application_path, CONFIG_FILE)

def _set_oxylabs_credentials(username, password):
    try:
        if not username or not password:
            bottom_win.print("Error: Username and password cannot be empty")
            return False
            
        keyring.set_password(SERVICE_ID, USERNAME_ID, username)
        keyring.set_password(SERVICE_ID, PASSWORD_ID, password)
        bottom_win.print("Oxylabs credentials set.")
        return True
        
    except keyring.errors.PasswordSetError as e:
        bottom_win.print(f"Error setting credentials: {str(e)}")
        return False
    except Exception as e:
        bottom_win.print(f"Unexpected error: {str(e)}")
        return False

def _set_api_key(api_key):
    try:
        if not api_key:
            bottom_win.print("Error: API key cannot be empty")
            return False
            
        keyring.set_password(SERVICE_ID, KEY_ID, api_key)
        bottom_win.print("OpenAI API key set.")
        return True
        
    except keyring.errors.PasswordSetError as e:
        bottom_win.print(f"Error setting API key: {str(e)}")
        return False
    except Exception as e:
        bottom_win.print(f"Unexpected error: {str(e)}")
        return False

def _handle_no_config():
    """Handle no configuration found."""
    bottom_win.print("No valid configuration found. Creating new config...")
    with open(_get_config_path(), 'w') as f:
        json.dump({}, f, indent=4)

def _handle_json_error(e):
    """Handle JSON error."""
    bottom_win.print(f"JSON error: {e}. Press any key to continue...")
    bottom_win.getch()
    return {}

def _handle_error(e):
    """Handle unexpected error."""
    bottom_win.print(f"Unexpected error: {e}. Press any key to continue...")
    bottom_win.getch()
    return {}

def _handle_exit():
    """Handle exit."""
    bottom_win.print("Exiting due to fatal error...")
    sys.exit()