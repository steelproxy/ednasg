import openai
import bottom_win
import requests
from message_win import clear_buffer
from message_win import print_msg
import utils
import aiohttp
import asyncio
import utils

CHATGPT_ROLE = """You are a helpful assistant that analyzes a generated 99-second social media news script to write multiple safe, vivid image descriptions for the DALL·E 3 API.

Your goal is to create descriptions that follow OpenAI's content and safety policies. Avoid any mention of:
- Real people (living or deceased)
- Politicians, celebrities, or historical figures
- Company names, logos, or brands
- Sensitive topics (violence, sex, drugs, war, politics, religion, medical conditions)
- Anything controversial or graphic

If the content provided contains mentions of politicians, celebrities, or historical figures, please describe their likelyhood instead of their actual names.
Descriptions must be under 200 characters clear, descriptive, and family-friendly, focusing on visual detail, colors, and composition. Never mention camera types, prompt instructions, or art styles. 
I NEED to test how the tool works with extremely simple prompts. DO NOT add any detail or revise my prompt, just simply use the prompt AS-IS.
"""

CHATGPT_SECONDARY_ROLE = """You will receive a script and a number of images. Return a numbered list of short image descriptions, one per line, with no extra commentary or formatting."""
MAX_RETRY = 3

async def _generate_single_image(client, description, identifier, resolution, image_quality):
    retry_count = 0
    while True:
        print_msg(f"photo {identifier}: retry count: {retry_count} description: {description}")
        if(retry_count >= MAX_RETRY):
            print_msg(f"photo {identifier}: unable to generate photo! max retry count reached.")
            break

        print_msg(f"photo {identifier}: Generating photo at {resolution} resolution")
        try:
            response = client.images.generate(
                model="dall-e-3",
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
            break

        except Exception as e:
            utils.handle_openai_error(e, f"photo {identifier} thread")
            if isinstance(e, openai.BadRequestError):
                print_msg(f"photo {identifier} generation failed, potentially bad prompt. regenerating description...")
                description = _description_regenerate(description)
                retry_count += 1
                continue
            else:
                break    

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

    bottom_win.bgetstr("DALLE-3 photo generation finished. Press enter to exit...")

def _description_regenerate(client, description):
    print_msg(f"recreating bad description: \"{description}\".")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=_recreate_description(description),
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
    
    new_description = response.choices[0].message.content.strip()
    if not new_description:
        print_msg("error regenerating description: \"{description}\"")
        return None
    print_msg(f"recreated description: \"{new_description}\"")
    return new_description
    

def _recreate_description(description):
    """Create the message structure for the GPT API request."""
    return [
        {"role": "system", "content": CHATGPT_ROLE},
        {"role": "user", "content": f"DALL-E-3 has flagged this description, please regenerate it to successfully pass the content filters: {description}"}
    ]


def _create_gpt_message(script, num_images):
    """Create the message structure for the GPT API request."""
    return [
        {"role": "system", "content": CHATGPT_ROLE + CHATGPT_SECONDARY_ROLE},
        {"role": "user", "content": f"number of images: {num_images}\nscript: {script}\n"}
    ]
