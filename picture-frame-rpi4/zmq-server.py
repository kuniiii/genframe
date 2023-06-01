# loading API request stuff
import json
import base64
import requests

# loading zeromq stuff
import time
import zmq

import io
import os

output_folder = "/home/peterkun/Desktop/Development/output-10may/"

import datetime

# Get the current timestamp
now = datetime.datetime.now()

# Format the timestamp as a string, e.g., "2023-05-01_12-30-15"
timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

# controlnet init image
image_path = "/home/peterkun/Desktop/Development/face_portrait_openpose.png"

from PIL import Image, PngImagePlugin

# loading inky stuff
from inky.auto import auto
from PIL import Image, ImageFont, ImageDraw
import textwrap
from font_source_serif_pro import SourceSerifProSemibold
# from font_source_sans_pro import SourceSansProSemibold

# keyboard input
import keyboard

# setup inky
inky_display = auto(ask_user=True, verbose=True)
inky_display.set_border(inky_display.WHITE)

font = ImageFont.truetype(SourceSerifProSemibold, 24)

# creating zeromq context and starting up the server
context = zmq.Context()
# socket = context.socket(zmq.REP)
socket = context.socket(zmq.PULL)
print('Binding to port 5555')
socket.bind("tcp://*:5555")

poller = zmq.Poller()
poller.register(socket, zmq.POLLIN)

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

def inky_refresh(text: str, max_width: int, font: ImageFont):
    img = Image.new("P", (inky_display.width, inky_display.height))
    draw = ImageDraw.Draw(img)

    #wrap text
    lines = textwrap.wrap(text, width=max_width)
    message = '\n'.join(lines)

    w, h = draw.textsize(message, font)
    x = (inky_display.width / 2) - (w / 2)
    y = (inky_display.height / 2) - (h / 2)
    #draw.text((x, y), message, inky_display.BLACK, font)
    draw.multiline_text((x, y), message, inky_display.BLACK, font)

    inky_display.set_image(img)
    inky_display.show()

# here comes the labels
# labels1 = ["frightening", "scary", "uninterested", "dog", "curious", "excited", "cat", "flowerpot", "banana", "ghost", "alien", "chicken", "posh lonely"]
# labels2 = ["joyful", "sombre", "romantic", "dreamy", "serene", "mysterious", "contemplative", "nostalgic", "intense", "whimsical", "golden hour", "dramatic", "natural", "neon"]
# labels3 = ["boy", "dog", "cat", "girl", "pope", "business man", "tree", "forest", "wolf", "fields", "foxes", "family", "chair", "desk", "building"]
labels1 = ["vivid", "dramatic", "ethereal", "surreal", "cinematic", "minimalistic", "monochromatic", "abstract", "nostalgic", "majestic", "intimate", "inspiring", "radiant"]
labels2 = ["ecstatic", "joyful", "optimistic", "contented", "calm", "indifferent", "bored", "anxious", "frustrated", "angry", "sad", "depressed", "despairing"]
labels3 = ["woman", "girl", "witch", "queen", "maiden", "matron", "dancer", "bride", "mother", "warrior", "goddess", "widow", "seductress"]

base64_controlnet_input_image = get_image_as_base64_string(image_path)

while True:
    socks = dict(poller.poll())
    if socket in socks:
        message = socket.recv_multipart()
        # parsing the received message into something usable.
        # there must be a better way of doing this
        analog_raw_values = message[1].decode().lstrip('[ ').rstrip('] ').replace(' ', '').split(',')
        analog_values = [x for x in analog_raw_values]
        print(analog_values)

        # current_values = analog_values[1:4]


        # print(analog_values[1].lstrip(' '))
        # if int(analog_values[2]) == 1:
        # if keyboard.is_pressed('g'):
        print("let's send a request now!")
        prompt_msg = labels1[int(analog_values[1])] + " portrait of a " + labels2[int(analog_values[2])] + " " + labels3[int(analog_values[3])]
        print(prompt_msg)

        inky_refresh(prompt_msg, 30, font)
        txt2img_url = 'http://0.0.0.0:7861/sdapi/v1/txt2img'
        data = {
        'prompt': prompt_msg,
        'steps': '25',
        'sampler_name': 'Euler',
        'alwayson_scripts': {
            'controlnet': {
                'args': [
                    {
                        'input_image': base64_controlnet_input_image,
                        'model': 'control_v11p_sd15_openpose [cab727d4]'
                    }
                ]
            }
        }
        }
        response = submit_post(txt2img_url, data)
        save_encoded_image(response.json()['images'][0], prompt_msg + '.png')
        filename = timestamp + "_" + prompt_msg.replace(" ", "_") + '.png'
        output_path = os.path.join(output_folder, filename)

        # Submit the extra-single-image reques
        extra_single_image_url = 'http://0.0.0.0:7861/sdapi/v1/extra-single-image'
        image_data = response.json()['images'][0]
        extra_single_image_response = submit_extra_single_image_request(extra_single_image_url, image_data)
        # print(extra_single_image_response.json())
        save_encoded_image(extra_single_image_response.json()['image'], output_path)