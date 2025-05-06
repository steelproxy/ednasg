import message_win
import bottom_win
import json
import utils

def gpt_scoring(client, script):
    prompt = f"""
        Evaluate the following 99-second video script for engagement potential.
        Your output should be in json with the parameters
        "date",
        "hook_strength",
        "sentiment",
        "clarity",
        "tone_consistency",
        "tone",
        "emotional_trigger"

        Give the following scores:

        - Hook Strength (1-5)
        - Overall Sentiment (Positive/Neutral/Negative)
        - Clarity (1-5)
        - Tone Consistency (1-5)
        - Tone (Casual/Formal/Serious/etc.)
        - Emotional Trigger (if any)

        Script:
        {script}
        """
    
    saved_buffer = message_win.message_buffer
    message_win.clear_buffer()
    message_win.print_msg("Scoring news script...")

    try:
        response = client.chat.completions.create(        # Get response from OpenAI API
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert content evaluator for 99 second news video scripts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
    except Exception as e:
        utils.handle_openai_error(e, "GPT API call")
        raise

    if not hasattr(response, 'choices') or not response.choices:          # Check response format
        raise ValueError("API response does not contain 'choices'")
    
    if not hasattr(response.choices[0], 'message') or not hasattr(response.choices[0].message, 'content'):
        raise ValueError("API response does not contain expected content")


    message_win.print_msg("Parsing JSON results...")
    try:
        # Clean up the response by removing markdown code block markers
        response_text = response.choices[0].message.content.strip()
        # Remove ```json and ``` markers if present
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        return json.loads(response_text)
    except Exception as e:
        message_win.print_msg("Error parsing response:", e)
        message_win.print_msg("Raw response:\n", response.choices[0].message.content.strip())
        return None