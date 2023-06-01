import json
import base64
import io
import os
from PIL import Image, PngImagePlugin

import requests
import time
from datetime import datetime
from threading import Thread
from secrets import SLACK_BOT_TOKEN

output_folder = "/Users/peku/Development/output-slackbot/"

url = "https://slack.com/api/conversations.history"
channel_id = "C057W6XF01J"
headers = {"Authorization": "Bearer " + SLACK_BOT_TOKEN}

import datetime

# Get the current timestamp
now = datetime.datetime.now()

# Format the timestamp as a string, e.g., "2023-05-01_12-30-15"
timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

# controlnet init image
image_path = "/Users/peku/Development/artnet-picture-frame-v1/mountain_landscape_controlnet_lineart.png"


# functions for API requests

def submit_post(url: str, data: dict):
    # Submit a POST request to the given URL with the given data.
    return requests.post(url, data=json.dumps(data))

def save_encoded_image(b64_image: str, output_path: str):
    # Save the given image to the given output path
    with open(output_path, "wb") as image_file:
        image_file.write(base64.b64decode(b64_image))

def submit_extra_single_image_request(api_url, image_data, upscaling_resize=4):
    payload = {
        "image": image_data,
        "upscaling_resize": upscaling_resize,
        "upscaler_1" : "ESRGAN_4x"
    }
    response = requests.post(api_url, json=payload)
    return response

# Open an image and return it in a base64 string
def get_image_as_base64_string(image_path):
    # Open the image file
    with Image.open(image_path) as img:
        # Convert the image data to a byte stream
        byte_arr = io.BytesIO()
        img.save(byte_arr, format='PNG')
        byte_arr = byte_arr.getvalue()

        # Convert the byte stream to a base64 string
        base64_encoded_result_bytes = base64.b64encode(byte_arr)
        base64_encoded_result_str = base64_encoded_result_bytes.decode('ascii')

        return base64_encoded_result_str
    

response = requests.get(url, headers=headers, params={"channel": channel_id})
if response.json()['ok']:
    latest_read_ts = response.json()['messages'][0]['ts']
else:
    latest_read_ts = '0'
    
unread_count = 0
should_continue = True

base64_controlnet_input_image = get_image_as_base64_string(image_path)

# Define the state functions
def handle_one_unread():
    print("Handling one unread message...")
    print("let's send a request now!")
    prompt_msg = "landscape of a green field in front of mountains and clear sky"
    print(prompt_msg)

    txt2img_url = 'http://0.0.0.0:7861/sdapi/v1/txt2img'
    data = {
    'prompt': prompt_msg,
    'steps': '25',
    'sampler_name': 'Euler',
    'seed': '3116017065',
    'alwayson_scripts': {
        'controlnet': {
            'args': [
                {
                    'input_image': base64_controlnet_input_image,
                    'model': 'control_v11p_sd15_lineart [43d4be0d]'
                }
            ]
        }
    }
    }
    response = submit_post(txt2img_url, data)
    # save_encoded_image(response.json()['images'][0], prompt_msg + '.png')
    filename = timestamp + "_" + prompt_msg.replace(" ", "_") + '.png'
    output_path = os.path.join(output_folder, filename)

    # Submit the extra-single-image reques
    extra_single_image_url = 'http://0.0.0.0:7861/sdapi/v1/extra-single-image'
    image_data = response.json()['images'][0]
    extra_single_image_response = submit_extra_single_image_request(extra_single_image_url, image_data)
    # print(extra_single_image_response.json())
    save_encoded_image(extra_single_image_response.json()['image'], output_path)    

def handle_five_unread():
    print("Handling five unread messages...")
    print("let's send a request now!")
    prompt_msg = "landscape of a green field in front of mountains and cloudy sky"
    print(prompt_msg)

    txt2img_url = 'http://0.0.0.0:7861/sdapi/v1/txt2img'
    data = {
    'prompt': prompt_msg,
    'steps': '25',
    'sampler_name': 'Euler',
    'seed': '3116017065',
    'alwayson_scripts': {
        'controlnet': {
            'args': [
                {
                    'input_image': base64_controlnet_input_image,
                    'model': 'control_v11p_sd15_lineart [43d4be0d]'
                }
            ]
        }
    }
    }
    response = submit_post(txt2img_url, data)
    # save_encoded_image(response.json()['images'][0], prompt_msg + '.png')
    filename = timestamp + "_" + prompt_msg.replace(" ", "_") + '.png'
    output_path = os.path.join(output_folder, filename)

    # Submit the extra-single-image reques
    extra_single_image_url = 'http://0.0.0.0:7861/sdapi/v1/extra-single-image'
    image_data = response.json()['images'][0]
    extra_single_image_response = submit_extra_single_image_request(extra_single_image_url, image_data)
    # print(extra_single_image_response.json())
    save_encoded_image(extra_single_image_response.json()['image'], output_path)

def handle_many_unread():
    print("Handling more than ten unread messages...")
    print("let's send a request now!")
    prompt_msg = "landscape of a green field in front of mountains and stormy sky"
    print(prompt_msg)

    txt2img_url = 'http://0.0.0.0:7861/sdapi/v1/txt2img'
    data = {
    'prompt': prompt_msg,
    'steps': '25',
    'sampler_name': 'Euler',
    'seed': '3116017065',
    'alwayson_scripts': {
        'controlnet': {
            'args': [
                {
                    'input_image': base64_controlnet_input_image,
                    'model': 'control_v11p_sd15_lineart [43d4be0d]'
                }
            ]
        }
    }
    }
    response = submit_post(txt2img_url, data)
    # save_encoded_image(response.json()['images'][0], prompt_msg + '.png')
    filename = timestamp + "_" + prompt_msg.replace(" ", "_") + '.png'
    output_path = os.path.join(output_folder, filename)

    # Submit the extra-single-image reques
    extra_single_image_url = 'http://0.0.0.0:7861/sdapi/v1/extra-single-image'
    image_data = response.json()['images'][0]
    extra_single_image_response = submit_extra_single_image_request(extra_single_image_url, image_data)
    # print(extra_single_image_response.json())
    save_encoded_image(extra_single_image_response.json()['image'], output_path)

# Define the state machine
state_machine = {
    1: handle_one_unread,
    5: handle_five_unread,
    10: handle_many_unread
}

def update_unread_count():
    global latest_read_ts
    global unread_count
    global should_continue
    state_triggered = False  # Flag variable to track state triggering
    while should_continue:
        payload = {"channel": channel_id, "oldest": latest_read_ts}
        response = requests.get(url, headers=headers, params=payload)
        if response.json()['ok']:
            messages = response.json()['messages']
            new_unread_count = sum(1 for message in messages if float(message['ts']) > float(latest_read_ts))
            
            # Check if the unread count has changed
            if new_unread_count != unread_count:
                unread_count = new_unread_count
                
                # Reset the state_triggered flag when unread count changes
                state_triggered = False

            # Trigger the state functions if unread count matches the state
            if unread_count in state_machine and not state_triggered:
                state_machine[unread_count]()
                state_triggered = True

        time.sleep(5)

def handle_user_input():
    global latest_read_ts
    global should_continue
    while True:
        user_input = input("Enter 'g' to reset timestamp, 'u' to print unread count, or 'q' to quit: ")
        if user_input.lower() == 'g':
            response = requests.get(url, headers=headers, params={"channel": channel_id})
            if response.json()['ok']:
                last_message = response.json()['messages'][0]
                latest_read_ts = last_message['ts']
                last_message_time = datetime.datetime.fromtimestamp(float(last_message['ts']))
                last_message_text = last_message['text']
                print(f"Last message before reset was at {last_message_time} with content: {last_message_text}")
        elif user_input.lower() == 'u':
            print("Unread count: ", unread_count)
        elif user_input.lower() == 'q':
            should_continue = False
            break

update_thread = Thread(target=update_unread_count)
update_thread.start()

handle_user_input()

