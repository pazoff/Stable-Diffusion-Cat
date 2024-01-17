import requests
import json
from PIL import Image
from io import BytesIO
import base64
from datetime import datetime
import os
from cat.mad_hatter.decorators import tool, hook, plugin
from pydantic import BaseModel


# Settings

class StableDiffusionCatCatSettings(BaseModel):
    # API key
    required_Wizmodel_api_key: str
    required_Steps_for_image_generation: int = 50


# Give your settings schema to the Cat.
@plugin
def settings_schema():
    return StableDiffusionCatCatSettings.schema()


def generate_image(prompt, cat, steps):

    # Load the settings
    settings = cat.mad_hatter.get_plugin().load_settings()
    wizmodel_api_key = settings.get("required_Wizmodel_api_key")
    steps_for_image_generation = settings.get("required_Steps_for_image_generation")

    if (steps_for_image_generation == None) or (steps_for_image_generation < 1):
        steps_for_image_generation = steps

    if (wizmodel_api_key == None) or (wizmodel_api_key == ""):
        cat.send_ws_message('Missing API key. Please enter your Wizmodel API key in the Stable Diffusion Cat plugin settings! You can get your free API key from this website: https://www.wizmodel.com/models/keyPanel', msg_type='chat')
        return False


    # Wizmodel.com API endpoint URL
    url = "https://api.wizmodel.com/sdapi/v1/txt2img"

    # Request payload
    payload = json.dumps({
        "prompt": prompt,
        "steps": steps_for_image_generation
    })

    # Request headers
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {wizmodel_api_key}'
    }

    try:
        # Make a POST request
        response = requests.post(url, headers=headers, data=payload)

        # Check for successful response
        response.raise_for_status()

        
        base64_string = response.json()['images'][0]

        # Decode the base64 string into bytes
        image_data = base64.b64decode(base64_string)
        image_bytes = BytesIO(image_data)

        # Generate a unique filename based on the current timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"output_image_{timestamp}.jpg"

        # Specify the folder path
        folder_path = "/admin/assets/stable-diffusion-cat"

        # Check if the folder exists, create it if not
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Construct the output file name with the formatted date and time
        output_filename = os.path.join(folder_path, filename)

        # Open the image using Pillow
        image = Image.open(image_bytes)
        #image.show()

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
        #cat.send_ws_message(f"Request error: {e}", msg_type='chat')

    except Exception as e:
        # Handle other unexpected errors
        print(f"An unexpected error occurred: {e}")
        #cat.send_ws_message(f"An unexpected error occurred: {e}", msg_type='chat')

    # Return False if image generation fails
    return False

@hook
def before_cat_reads_message(user_message_json: dict, cat):
    
    message = user_message_json["text"]
    
    if message.endswith('*'):
        message = message[:-1]
        print("Generating image based on the prompt " + message)
        cat.send_ws_message(content='Generating image based on the prompt <b>' + message + '</b> ...', msg_type='chat')
        generated_image_path = generate_image(message, cat, 50)
        if generated_image_path:
            print(f"Image successfully generated and saved as: {generated_image_path}")
            cat.send_ws_message(content='<img src="' + generated_image_path + '">', msg_type='chat')
        else:
            print("Image generation failed.")
            cat.send_ws_message('No image was generated!', msg_type='chat')

    user_message_json["text"] = "Tell me more about " + message
    return user_message_json
