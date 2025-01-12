import openai
import bottom_win
import requests
from message_win import clear_buffer
from message_win import print_msg

KEYWORD_PROMPT = "Please analyze my 99 second social media news script and generate one image description that i can feed to DALLE-3 to generate an image for my video. Please make sure it does not contain text that is not allowed by DALLE-3's safety system: "

def generate_photos(client, script):
    clear_buffer()
    print_msg("DALLE-3 photo generation activated...")
    print_msg("Analyzing script for a keyword to feed to DALLE...")

    try:
        response = client.chat.completions.create(  # Get response from OpenAI API
            model="gpt-4o",
            messages=_create_gpt_message(script),
            temperature=0.7
        )
    except openai.error.OpenAIError as e:
        print_msg(f"Error during GPT API call: {e}")
        return

    if not hasattr(response, 'choices') or not response.choices:          # Check response format
        raise ValueError("API response does not contain 'choices'")
    
    if not hasattr(response.choices[0], 'message') or not hasattr(response.choices[0].message, 'content'):
        raise ValueError("API response does not contain expected content")

    keyword = response.choices[0].message.content.strip()
    print_msg(f"Keyword: {keyword}")

    print_msg("Generating 1 photo(s) of 1024x1024 resolution.")
    
    try:
        # Call the DALL·E API to generate an image
        response = client.images.generate(
            model="dall-e-3",
            prompt=keyword,
            size="1024x1024",
            quality="standard",
            n=1,
        )
    except openai.error.OpenAIError as e:
        print_msg(f"Error during DALL·E API call: {e}")
        return

    print_msg(f"Response: {response}")

    # Loop through the generated image URLs
    image_url = response.data[0].url
    print_msg(f"Image URL: {image_url}")
    image_data = requests.get(image_url).content
    with open(f"generated_image.png", "wb") as file:
        file.write(image_data)
    print_msg(f"Image saved as 'generated_image.png'")

def _create_gpt_message(script):     # Prepare GPT API messages
    """Create the message structure for the GPT API request."""
    return [
        {"role": "system", "content": "You are a helpful assistant that analyzes a generated 99 second social media news script to write an image description for the DALLE-3 API. Ensure the description adheres to DALL-E 3's safety standards and does not include any prohibited content."},
        {"role": "user", "content": f"{KEYWORD_PROMPT}\n\n" +
         "\n".join(f"{script}")}
    ]
