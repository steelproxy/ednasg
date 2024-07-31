# ednasg

A Python application that fetches articles from RSS feeds and generates a news anchor script using OpenAI's ChatGPT. The program provides a user-friendly interface for selecting feeds and articles, customizing prompts, and displaying the generated script.

## Features

- Fetch articles from multiple RSS feeds.
- Select articles for script generation.
- Customize the ChatGPT prompt for personalized scripts.
- Display the generated script in a scrollable interface.
- Save the script to a file.

## Requirements

- Python 3.6 or later
- An OpenAI API key (for ChatGPT usage)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/steelproxy/ednasg.git
cd ednasg
```

### 2. Run the Install Script

```bash
chmod +x install.sh
./install.sh
```

## Usage

### 1. Activate the virtual environment and run the program
```bash
source venv/bin/activate
python ./ednasg.py
```
### 3. Follow the on-screen prompts to:

1. Enter your OpenAI API key.
2. Select an RSS feed or add new feeds.
3. Choose articles from the fetched feed.
4. Customize the script prompt if desired.
5. After generating the script, you can scroll through it and save it to a file by entering the desired filename when prompted.
   
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

