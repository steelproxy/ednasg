from pygooglenews import GoogleNews
import bottom_win
import message_win
from time import sleep
from datetime import datetime
import pickle
import re

gn = GoogleNews()

def search_querytime():
    message_win.clear_buffer()
    message_win.baprint("Searching by query/time...")
    message_win.baprint("Hint: You can search for any keyword, within any specified time range. ex: \"news\",\"6mo\" or leave blank for any.")
    query = bottom_win.getstr("Please enter your query: ", callback=message_win.print_buffer)
    message_win.baprint(f"Query: {query}")
    timespan = bottom_win.getstr("Time before: ", callback=message_win.print_buffer)
    message_win.baprint(f"Time: {timespan or "any"}")
    return _format_entires_to_articles(gn.search(query, when=timespan))

def search_geolocation():
    message_win.clear_buffer()
    message_win.baprint("Searching by geolocation...")
    message_win.baprint("Hint: geolocation can be formatted in several ways.")
    message_win.baprint(" eg. \"geo_location\": \"California,United States\"")
    message_win.baprint(" eg. \"geo_location\": \"United Kingdom\"")
    message_win.baprint(" eg. \"geo_location\": \"lat: 47.6205, lng: -122.3493, rad: 25000\"")
    message_win.baprint("They can also be formatted as their respective Google Canonical Location Name or Criteria ID")
    message_win.baprint(" eg. \"geo_location\": \"1023191\"")
    message_win.baprint("A list of these values is available at: https://developers.google.com/adwords/api/docs/appendix/geotargeting")
    geolocation = bottom_win.getstr("Please enter the geolocation: ", callback=message_win.print_buffer)
    return _format_entires_to_articles(gn.geo_headlines(geolocation))

def search_topic():
    message_win.clear_buffer()
    message_win.baprint("Searching by topic...")
    message_win.baprint("Available Topics: ")
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
        message_win.baprint(f"{i}. {topic}")
    while True:
        selected_topic = bottom_win.getstr("Please enter the name of the topic youd like to search for: ", callback=message_win.print_buffer)
        if selected_topic not in topics:
            bottom_win.print("Invalid topic selection! Please try again...")
            sleep(2)
        else:
            break
    return _format_entires_to_articles(gn.topic_headlines(selected_topic))

def pgn_search():
    """Search for articles using pygooglenews."""
    message_win.clear_buffer()
    message_win.baprint("Google News SERP Scraping mode activated.")
    message_win.baprint("You can search in a few different ways:")
    message_win.baprint("1: Top Stories")
    message_win.baprint("2: Topic")
    message_win.baprint("3: Geolocation")
    message_win.baprint("4: Query/Time (eg. 'london' '6mo')")

    while True:
        selection = bottom_win.getstr("Enter search method: ", callback=message_win.print_buffer)
        if selection not in ["1", "2", "3", "4"]:
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

def _format_entires_to_articles(results):
    """Format the pygooglenews response to a list of articles."""       
    # Transform each article to match expected format (title, summary, date)
    entries = results['entries']
    formatted_articles = []
    for article in entries:
        formatted_articles.append({
            'title': article['title'],
            'summary': re.sub('<[^<]+?>', '', article['summary']),
            'date': article['published']
        })
        
    return formatted_articles

