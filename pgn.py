from pygooglenews import GoogleNews
import bottom_win
import message_win
from time import sleep
from time import strptime
import pickle
import re
from bottom_win import bgetstr

gn = GoogleNews()

def search_querytime():
    message_win.clear_buffer()
    message_win.print_msg("Searching by query/time...")
    message_win.print_msg("Hint: You can search for any keyword, within any specified time range. ex: \"news\",\"6mo\" or leave blank for any.")
    message_win.print_msg("Hint: If you want to search for news within a certain radius of an area use as such: \"within 10 miles of Kent, OH\".")
    query = bgetstr("Please enter your query: ")
    message_win.print_msg(f"Query: {query}")
    timespan = bgetstr("Time before: ")
    message_win.print_msg(f"Time: {timespan or "any"}")
    return _format_entires_to_articles(gn.search(query, when=timespan))

def search_geolocation():
    message_win.clear_buffer()
    message_win.print_msg("Searching by geolocation...")
    message_win.print_msg("Hint: geolocation can be formatted in several ways.")
    message_win.print_msg(" eg. \"geo_location\": \"California,United States\"")
    message_win.print_msg(" eg. \"geo_location\": \"United Kingdom\"")
    message_win.print_msg(" eg. \"geo_location\": \"lat: 47.6205, lng: -122.3493, rad: 25000\"")
    message_win.print_msg("They can also be formatted as their respective Google Canonical Location Name or Criteria ID")
    message_win.print_msg(" eg. \"geo_location\": \"1023191\"")
    message_win.print_msg("A list of these values is available at: https://developers.google.com/adwords/api/docs/appendix/geotargeting")
    geolocation = bgetstr("Please enter the geolocation: ")
    return _format_entires_to_articles(gn.geo_headlines(geolocation))

def search_topic():
    message_win.clear_buffer()
    message_win.print_msg("Searching by topic...")
    message_win.print_msg("Available Topics: ")
    topics = [
        "World",
        "Nation",
        "Business",
        "Technology",
        "Entertainment",
        "Science",
        "Sports",
        "Health"
    ]
    # Print each topic with its corresponding number
    for i, topic in enumerate(topics, start=1):
        message_win.print_msg(f"{i}. {topic}")
    while True:
        selected_topic = bgetstr("Please enter the name of the topic youd like to search for: ")
        if selected_topic not in topics:
            bottom_win.print("Invalid topic selection! Please try again...")
            sleep(2)
        else:
            break
    return _format_entires_to_articles(gn.topic_headlines(selected_topic))

def pgn_search():
    """Search for articles using pygooglenews."""
    message_win.clear_buffer()
    message_win.print_msg("Google News SERP Scraping mode activated.")
    message_win.print_msg("You can search in a few different ways:")
    message_win.print_msg("1: Top Stories")
    message_win.print_msg("2: Topic")
    message_win.print_msg("3: Geolocation")
    message_win.print_msg("4: Query/Time (eg. 'london' '6mo')")

    while True:
        selection = bgetstr("Enter search method [q to return to main menu]: ")
        if selection not in ["1", "2", "3", "4", "q"]:
            bottom_win.print("Invalid selection! Please try again...")
            sleep(2)
        else:
            break

    match selection:
        case "1":
            return _format_entires_to_articles(gn.top_news())
        
        case "2":
            return search_topic()
        
        case "3":
            return search_geolocation()
        
        case "4":
            return search_querytime()
        case "q":
            return False

#def link(uri, label=None):
#    if label is None: 
#        label = uri
#    parameters = ''
#
#    # OSC 8 ; params ; URI ST <name> OSC 8 ;; ST 
#    escape_mask = '\033]8;{};{}\033\\{}\033]8;;\033\\'
#
#    return escape_mask.format(parameters, uri, label)

def _format_entires_to_articles(results):
    """Format the pygooglenews response to a list of articles."""       
    # Transform each article to match expected format (title, summary, date)
    entries = results['entries']
    formatted_articles = []
    for article in entries:
        formatted_articles.append({
            'title': article['title'],
            'summary': re.sub('<[^<]+?>', '', article['summary']),
            'date': strptime(article['published'], "%a, %d %b %Y %H:%M:%S %Z"),
            'url': article['link']
        })
        
    return formatted_articles

