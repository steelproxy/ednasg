import keyring
from keyring.backends.Windows import WinVaultKeyring
import message_win
import bottom_win
import os
from time import sleep

# Application Constants
SERVICE_ID = "ednasg"
OPENAI_KEY_ID = "openai_api_key"

def get_openai_api_key():
    """Fetch or prompt for OpenAI API key.
    
    Returns:
        str: OpenAI API key
    """
    if os.name == 'nt':
        keyring.set_keyring(WinVaultKeyring())
    
    api_key = keyring.get_password(SERVICE_ID, OPENAI_KEY_ID)
    
    # Prompt for key if not found
    if not api_key:
        api_key = bottom_win.getstr("Enter OpenAI API Key: ", callback=message_win.print_buffer)
        if api_key:
            keyring.set_password(SERVICE_ID, OPENAI_KEY_ID, api_key)
    
    return api_key

def reset_credentials(callback=None):
    """Reset API and Oxylabs credentials.
    
    Prompts user to enter new OpenAI API key and Oxylabs credentials.
    Sets the new credentials in the system keyring if provided.
    
    Returns:
        None
        
    Side Effects:
        - Updates keyring with new credentials if provided
        - Prints status messages to bottom window
        - Sleeps for 2 seconds after completion
    """
    message_win.baprint("Resetting credentials...")
        
    api_key = bottom_win.getstr("Enter your OpenAI API key: ", callback=message_win.print_buffer)
    if not _set_openai_api_key(api_key):
        return _handle_reset_credentials_error()
    bottom_win.print("Credentials reset.")
    sleep(2)
    return 

def _set_openai_api_key(api_key):
    """Set OpenAI API key in keyring.
    
    Args:
        api_key: OpenAI API key
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        keyring.set_password(SERVICE_ID, OPENAI_KEY_ID, api_key)
        bottom_win.print("OpenAI API key set.")
        sleep(2)
        return True
        
    except keyring.errors.PasswordSetError as e:
        return _handle_set_credentials_error(str(e))
    except Exception as e:
        return _handle_set_credentials_error(str(e))
    
def _handle_set_credentials_error(message="Unknown error"):
    """Handle set credentials error.
    
    Args:
        message: Error message to display
        
    Returns:
        bool: False to indicate failure
    """
    message_win.error(f"Unable to set credentials. [{message}]")
    return False

def _handle_reset_credentials_error():
    """Handle reset credentials error."""
    message_win.error("Unable to reset credentials.")
    return None