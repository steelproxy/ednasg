import requests
import config
import bottom_win
import message_win
from news_script import display_scrollable_script
import time
import json

def oxylabs_search():
    """Search for articles using Oxylabs."""
    message_win.clear()
    message_win.print("Google News SERP Scraping mode activated.")
    message_win.print("Hint: geolocation can be formatted in several ways.")
    message_win.print(" eg. \"geo_location\": \"California,United States\"")
    message_win.print(" eg. \"geo_location\": \"United Kingdom\"")
    message_win.print(" eg. \"geo_location\": \"lat: 47.6205, lng: -122.3493, rad: 25000\"")
    message_win.print("They can also be formatted as their respective Google Canonical Location Name or Criteria ID")
    message_win.print(" eg. \"geo_location\": \"1023191\"")
    message_win.print("A list of these values is available at: https://developers.google.com/adwords/api/docs/appendix/geotargeting")
    
    username, password = config.get_oxylabs_credentials()
    if not username or not password:
        bottom_win.print("No Oxylabs credentials found. Skipping search...")
        return None
    
    query = bottom_win.getstr("Enter search query: ")
    message_win.print(f"Query: {query}")
    
    location = bottom_win.getstr("Enter location: ")
    message_win.print(f"Location: {location}")
    
    bottom_win.print("Making request...")
    response = _make_oxylabs_request(query, location, username, password)
    articles = _format_response_to_articles(response)
    
    return articles
    
def _format_response_to_articles(response):
    """Format the Oxylabs response to a list of articles."""
    if not response or 'results' not in response:
        return []
    
    try:
        # Navigate to the main results array
        articles = response['results'][0]['content']['results']['main']
        
        # Transform each article to match expected format (title, summary, date)
        formatted_articles = []
        for article in articles:
            formatted_articles.append({
                'title': article['title'],
                'summary': article['desc'],
                'date': time.localtime()  # Current time since Oxylabs only provides relative dates
            })
        
        return formatted_articles
    except (KeyError, IndexError):
        return []
    
def _make_oxylabs_request(query, location, username, password):
    """Make a request to Oxylabs."""
    # Structure payload.
    payload = {
        'source': 'google_search',
        'query': query,
        'parse': True,
        'geo_location': location,  # Location targeting
        'context': [
            {'key': 'udm', 'value': 12},
            {'key': 'tbm', 'value': 'nws'},  # Ensures Google News results
            {'key': 'limit', 'value': 100}
        ],
        'render': 'html',  # Enable JavaScript rendering (optional)
    }
    
    # Get response.
    try:
        response = requests.post(
            'https://realtime.oxylabs.io/v1/queries',
            auth=(username, password),
            json=payload,
            timeout=30
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        bottom_win.print(f"Error making Oxylabs request: {str(e)}")
        return None
    
    return response.json()