from openai import OpenAI

def get_script(client, articles, custom_prompt):
    """Generate a news anchor script using ChatGPT based on the provided articles."""
    
    # Error checking for 'articles'
    if not isinstance(articles, list):
        raise ValueError("Expected 'articles' to be a list")
    
    for article in articles:
        if not isinstance(article, dict) or 'title' not in article or 'summary' not in article:
            raise ValueError("Each article should be a dictionary with 'title' and 'summary' keys")

    # Default prompt if not provided
    if not custom_prompt:
        custom_prompt = "Create a 99-second news anchor script for the following articles:"

    # Construct messages for the API call
    messages = [
        {"role": "system", "content": "You are a helpful assistant that writes news anchor scripts."},
        {"role": "user", "content": f"{custom_prompt}\n\n" +
         "\n".join(f"- {article['title']}: {article['summary']}" for article in articles)}
    ]
    
    # Get response from OpenAI API
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7
    )

    # Error checking for 'response'
    if not hasattr(response, 'choices') or not response.choices:
        raise ValueError("API response does not contain 'choices'")
    
    if not hasattr(response.choices[0], 'message') or not hasattr(response.choices[0].message, 'content'):
        raise ValueError("API response does not contain expected content")

    return response.choices[0].message.content.strip()
