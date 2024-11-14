# ednasg

A Python application that fetches articles from RSS feeds and generates a news anchor script using OpenAI's ChatGPT. The program provides a user-friendly interface for selecting feeds and articles, customizing prompts, and displaying the generated script.

## Features

- Fetch articles from multiple RSS feeds.
- Select articles for script generation.
- Customize the ChatGPT prompt for personalized scripts.
- Display the generated script in a scrollable interface.
- Save the script to a file.

## Requirements

- Python 3.12 or later
- An OpenAI API key (for ChatGPT usage)
- Git optionally for auto-updating and ease of install
- Several Python libraries, that should be auto installed with the install script, or bundled in the binary.
    - jsonschema
    - requests
    - openai
    - windows_curses (if using on Windows)
    - keyring
    - packaging

## Installation

### Binary
If you would prefer to skip these steps you can download the binary releases on the release page. Simply download, click and run, otherwise continue reading.

### 1. Clone the Repository and enter directory

```bash
git clone https://github.com/steelproxy/ednasg.git
cd ednasg
```

### 2. Run the Install Script

- MacOS:
```bash
chmod +x install-macos.sh
./install-macos.sh
```

- Windows:
```
.\install-windows.bat
```

- Linux:
    - If you are using Linux, you should be able to figure this out yourself. Just create the virtual environment and install the requirements, every other part of this program is OS agnostic, however it does depend on a keyring service being installed.
    - If using KDE install ```dbus-python``` as a system package, the pip package has some issues.


## Usage

### 1. Activate the virtual environment
You must be in the ednasg folder to run these commands.
- Windows 
```
.\.venv\Scripts\activate
```

- MacOS/Linux
```bash
./.venv/bin/activate
```

### 2. Run the program
After you have activated the virutal environment, run ednasg with this command.
```
python ./ednasg.py
```

### 3. Follow the on-screen prompts to:

1. Enter your OpenAI API key.
2. Select an RSS feed or add new feeds.
    - You can add multiple feeds at once by formatting them as comma seperated values ex. 
    ```
    https://feed1.com/index.xml,https://feed2.com/index.html,...
    ```
3. Choose articles from the fetched feed.
    - You may search for articles by pressing '/', it will bring up a search bar and return your results after you press enter. To return to the whole list simply open search again and hit enter without any other input.
4. Customize the script prompt if desired.
    - After entering your prompt you may press CTRL+D to begin generating the script.
5. After generating the script, you can scroll through it with up/down arrows and save it to a file by entering the desired filename when prompted.
   
### 4. Deactive the virtual environment when done
To deactivate the virtual environment, run:
```bash
deactivate
```
You can also simply exit the terminal.

## Contributing
Contributions are welcome! If you have suggestions or improvements, feel free to submit a pull request or open an issue.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

### Acknowledgments
- OpenAI for the ChatGPT API.
- feedparser for parsing RSS feeds.
- curses for terminal user interface.
- requests for downloading binary updates.
- jsonschema for validating configuration.
- packaging for handling version strings.

