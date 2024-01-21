# Import necessary libraries and modules
import requests
import json
from PIL import Image
from io import BytesIO
import base64
from datetime import datetime
import os
from cat.mad_hatter.decorators import tool, hook, plugin
from pydantic import BaseModel
from typing import Dict

# Define settings schema using Pydantic for the Cat plugin
class StableDiffusionCatCatSettings(BaseModel):
    # API key
    required_Wizmodel_api_key: str
    # Number of steps for image generation (with a default value of 50)
    required_Steps_for_image_generation: int = 50

# Plugin function to provide the Cat with the settings schema
@plugin
def settings_schema():
    return StableDiffusionCatCatSettings.schema()

# Function to generate an image based on a prompt
def generate_image(prompt, cat, steps):
    # Load the plugin settings
    settings = cat.mad_hatter.get_plugin().load_settings()
    wizmodel_api_key = settings.get("required_Wizmodel_api_key")
    steps_for_image_generation = settings.get("required_Steps_for_image_generation")

    # Set default steps if not provided or less than 1
    if (steps_for_image_generation is None) or (steps_for_image_generation < 1):
        steps_for_image_generation = steps

    # Check for a valid Wizmodel API key
    if (wizmodel_api_key is None) or (wizmodel_api_key == ""):
        cat.send_ws_message('Missing API key. Please enter your Wizmodel API key in the Stable Diffusion Cat plugin settings! You can get your free API key from this website: https://www.wizmodel.com/models/keyPanel', msg_type='chat')
        return False

    # Define Wizmodel.com API endpoint URL
    url = "https://api.wizmodel.com/sdapi/v1/txt2img"

    # Prepare request payload
    payload = json.dumps({
        "prompt": prompt,
        "steps": steps_for_image_generation
    })

    # Define request headers
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {wizmodel_api_key}'
    }

    try:
        # Make a POST request to Wizmodel API
        response = requests.post(url, headers=headers, data=payload)

        # Check for successful response
        response.raise_for_status()

        # Extract base64-encoded image string from the response
        base64_string = response.json()['images'][0]

        # Decode the base64 string into bytes
        image_data = base64.b64decode(base64_string)
        image_bytes = BytesIO(image_data)

        # Generate a unique filename based on the current timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"output_image_{timestamp}.jpg"

        # Specify the folder path for saving the image
        folder_path = "/admin/assets/stable-diffusion-cat"

        # Check if the folder exists, create it if not
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Construct the output file name with the formatted date and time
        output_filename = os.path.join(folder_path, filename)

        # Open the image using Pillow
        image = Image.open(image_bytes)

        # Save the image to a local file with a unique name
        image.save(output_filename)

        # Close the image to release resources
        image.close()

        print(f"Image generation successful. Image saved as: {output_filename}")

        # Return the output filename
        return output_filename

    except requests.exceptions.RequestException as e:
        # Handle request-related errors
        print(f"Request error: {e}")
        # cat.send_ws_message(f"Request error: {e}", msg_type='chat')

    except Exception as e:
        # Handle other unexpected errors
        print(f"An unexpected error occurred: {e}")
        # cat.send_ws_message(f"An unexpected error occurred: {e}", msg_type='chat')

    # Return False if image generation fails
    return False

# Hook function for fast reply generation
@hook(priority=9)
def agent_fast_reply(fast_reply, cat) -> Dict:
    return_direct = False

    # Get user message from the working memory
    message = cat.working_memory["user_message_json"]["text"]

    # Check if the message ends with an asterisk
    if message.endswith('*'):
        # Remove the asterisk
        message = message[:-1]

        print("Generating image based on the prompt " + message)
        cat.send_ws_message(content='Generating image based on the prompt ' + message + ' ...', msg_type='chat_token')

        # Generate image with the provided prompt and 50 steps
        generated_image_path = generate_image(message, cat, 50)

        if generated_image_path:
            print(f"Image successfully generated and saved as: {generated_image_path}")
            return {"output": f"<p><b>{message}</b></p><img src=\"{generated_image_path}\">"}
        else:
            print("Image generation failed.")
            return {"output": "No image was generated!"}

    # Return fast reply if no image generation is requested
    return fast_reply
