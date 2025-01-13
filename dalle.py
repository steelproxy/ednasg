import openai
import bottom_win
import requests
from message_win import clear_buffer
from message_win import print_msg
import utils

CHATGPT_ROLE = """You are a helpful assistant that analyzes a generated 99 second social media news script to write multiple image descriptions for the DALLE-3 API. 
You ensure each description adheres to DALL-E 3's safety standards and does not include any prohibited content. 
You are given a script and you will need to write a given number of image descriptions for scenes relevant to the script.
You will provide a list of descriptions, one per line, with no extra newlines between descriptions, and nothing else.
"""

def generate_photos(client, script, num_images=3):
    clear_buffer()
    print_msg("DALLE-3 photo generation activated...")
    print_msg("Analyzing script for keywords to feed to DALLE...")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=_create_gpt_message(script, num_images),
            temperature=0.7
        )
    except openai.error.OpenAIError as e:
        print_msg(f"Error during GPT API call: {e}")
        utils.pause()
        return
    except Exception as e:
        print_msg(f"Unknown error during GPT API call: {e}")
        utils.pause()
        return

    if not hasattr(response, 'choices') or not response.choices:
        raise ValueError("API response does not contain 'choices'")

    if not hasattr(response.choices[0], 'message') or not hasattr(response.choices[0].message, 'content'):
        raise ValueError("API response does not contain expected content")

    dalle_descriptions = response.choices[0].message.content.strip().split('\n')
    if len(dalle_descriptions) < num_images:
        print_msg("Not enough descriptions generated for the requested number of images.")
        utils.pause()
        return

    for i, dalle_description in enumerate(dalle_descriptions[:num_images]):
        print_msg(f"Description {i+1}: {dalle_description}")

        print_msg(f"Generating 1 photo of 1024x1024 resolution for description {i+1}.")

        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=dalle_description,
                size="1024x1024",
                quality="standard",
                n=1,
            )
        except openai.error.OpenAIError as e:
            print_msg(f"Error during DALL·E API call for description {i+1}: {e}")
            utils.pause()
            return
        except Exception as e:
            print_msg(f"Unknown error during DALL·E API call for description {i+1}: {e}")
            utils.pause()
            return

        print_msg(f"Response for description {i+1}: {response}")

        image_url = response.data[0].url
        print_msg(f"Image URL for description {i+1}: {image_url}")
        image_data = requests.get(image_url).content
        with open(f"generated_image_{i+1}.png", "wb") as file:
            file.write(image_data)
        print_msg(f"Image for description {i+1} saved as 'generated_image_{i+1}.png'")

def _create_gpt_message(script, num_images):
    """Create the message structure for the GPT API request."""
    return [
        {"role": "system", "content": CHATGPT_ROLE},
        {"role": "user", "content": f"script: {script}\n"}
    ]
