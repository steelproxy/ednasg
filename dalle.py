import openai
import bottom_win
import requests
from message_win import clear_buffer
from message_win import print_msg
import utils
import aiohttp
import asyncio
import utils

CHATGPT_ROLE = """You are a helpful assistant that analyzes a generated 99 second social media news script to write multiple image descriptions for the DALLE-3 API. 
You ensure each description adheres to DALL-E 3's safety standards and does not include any prohibited content. 
You are given a script and you will need to write a given number of image descriptions for scenes relevant to the script.
You will provide a list of descriptions, one per line, with no extra newlines between descriptions, and nothing else.
"""

async def _generate_single_image(client, description, identifier, resolution, image_quality):
    print_msg(f"photo {identifier}: description: {description}")
    print_msg(f"photo {identifier}: Generating photo at {resolution} resolution")
    try:
        response = client.images.generate(
            prompt=description,
            size=resolution,
            quality=image_quality,
            n=1,
        )
        print_msg(f"Response for photo {identifier}: {response}")

        image_url = response.data[0].url
        print_msg(f"Image URL for photo {identifier}: {image_url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as img_response:
                image_data = await img_response.read()

        with open(f"generated_image_{identifier}.png", "wb") as file:
            file.write(image_data)
        print_msg(f"Image {identifier} saved as 'generated_image_{identifier}.png'")

    except Exception as e:
        utils.handle_openai_error(e, f"photo {identifier} thread")

def generate_photos(client, script, num_images=3, image_quality="standard", resolution="1024x1024"):
    clear_buffer()
    bottom_win.print("ChatGPT Generating Descriptions...")
    print_msg("DALLE-3 photo generation activated...")
    print_msg(f"Generating {num_images} images...")
    print_msg(f"Image quality: {image_quality}")
    print_msg(f"Image resolution: {resolution}")
    print_msg("Analyzing script to generate descriptions for DALLE-3...")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=_create_gpt_message(script, num_images),
            temperature=0.7
        )
    except Exception as e:
        utils.handle_openai_error(e, "GPT API call")
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

    bottom_win.print("DALLE-3 Generating Images...")
    
    # Create and run async tasks
    async def run_tasks():
        tasks = [
            _generate_single_image(
                client, 
                description, 
                i, 
                resolution, 
                image_quality
            )
            for i, description in enumerate(dalle_descriptions[:num_images])
        ]
        await asyncio.gather(*tasks)

    # Run the async tasks properly
    asyncio.run(run_tasks())

    bottom_win.bgetstr("DALLE-3 photo generation complete. Press enter to exit...")

def _create_gpt_message(script, num_images):
    """Create the message structure for the GPT API request."""
    return [
        {"role": "system", "content": CHATGPT_ROLE},
        {"role": "user", "content": f"number of images: {num_images}\nscript: {script}\n"}
    ]
