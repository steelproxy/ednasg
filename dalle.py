import openai
import bottom_win
from message_win import clear_buffer
from message_win import print_msg, print_buffer
import utils
import aiohttp
import asyncio
import utils
import curses
from screen_manager import handle_resize
from openai import AsyncOpenAI

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
            # Create an async client from the existing client's API key
            async_client = AsyncOpenAI(api_key=client.api_key)
            
            response = await async_client.images.generate(
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

    bottom_win.print("DALLE-3 Generating Images... (Press 'q' to cancel)")
    
    # Create the event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Create tasks for each image generation
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
    
    # Create a future that will be done when all tasks are complete
    all_tasks = asyncio.gather(*tasks)
    
    # Make getch non-blocking
    bottom_win.win.nodelay(True)
    
    # Run the event loop in a non-blocking way
    while not all_tasks.done():
        # Do other work here while waiting for tasks to complete
        # For example, you could update a progress bar, check for user input, etc.
        # Run the event loop for a short time to allow tasks to progress
        loop.run_until_complete(asyncio.sleep(0.1))
        
        # Check for user input to cancel (non-blocking)
        try:
            ch = bottom_win.win.getch()
            if ch == ord('q'):
                print_msg("Cancelling image generation...")
                all_tasks.cancel()
                break
            elif ch == curses.KEY_RESIZE:
                handle_resize()
                print_buffer()
                bottom_win.print("DALLE-3 Generating Images... (Press 'q' to cancel)")
        except curses.error:
            pass  # No input available
    
    # Restore normal getch behavior
    bottom_win.win.nodelay(False)
    
    # Clean up
    loop.close()
    
    if not all_tasks.cancelled():
        bottom_win.handle_input("DALLE-3 photo generation finished. Press enter to exit...", print_buffer, None, {10: (None, "break")}, True)

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
