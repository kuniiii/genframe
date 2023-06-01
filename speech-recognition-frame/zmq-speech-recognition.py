# loading API request stuff
import json
import base64
import requests

# loading zeromq stuff
import time
import zmq

import io
import os

output_folder = "/Users/peku/Development/output-speech-recognition/"

import datetime

# Get the current timestamp
now = datetime.datetime.now()

# Format the timestamp as a string, e.g., "2023-05-01_12-30-15"
timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

# controlnet init image
image_path = "/Users/peku/Development/artnet-picture-frame-v1/controlnet_solarpunk_city_scribble.png"

from PIL import Image, PngImagePlugin

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

# here comes the labels
labels1 = ["Budapest", "Copenhagen", "Oslo", "Helsinki"]

base64_controlnet_input_image = get_image_as_base64_string(image_path)

while True:
    socks = dict(poller.poll())
    if socket in socks:
        message = socket.recv_multipart()
        # parsing the received message into something usable.
        # there must be a better way of doing this
        print(message)
        # raw_values = message[0].decode().lstrip('[ ').rstrip('] ').replace(' ', '').split(',')
        # print(raw_values)
        # analog_values = [x for x in analog_raw_values]
        # print(analog_values)
        # print(raw_values[0])
        print("let's send a request now!")
        # prompt_msg = "A beautiful green lush solarpunk very highly detailed ((" + labels1[int(raw_values[0])] + "))  solarpunk city digital surrealism art by Greg Rutkowski and Josan Gonzalez, highly detailed, digital concept art, Volumetric natural light, sharp focus, Golden Ratio illustration"
        # print(prompt_msg)

        # txt2img_url = 'http://0.0.0.0:7861/sdapi/v1/txt2img'
        # data = {
        # 'prompt': prompt_msg,
        # 'steps': '50',
        # 'sampler_name': 'Euler',
        # 'alwayson_scripts': {
        #     'controlnet': {
        #         'args': [
        #             {
        #                 'input_image': base64_controlnet_input_image,
        #                 'model': 'control_v11p_sd15_scribble [d4ba51ff]'
        #             }
        #         ]
        #     }
        # }
        # }
        # response = submit_post(txt2img_url, data)
        # # save_encoded_image(response.json()['images'][0], prompt_msg + '.png')
        # filename = timestamp + "_" + labels1[int(raw_values[0])] + '.png'
        # output_path = os.path.join(output_folder, filename)

        # # Submit the extra-single-image reques
        # extra_single_image_url = 'http://0.0.0.0:7861/sdapi/v1/extra-single-image'
        # image_data = response.json()['images'][0]
        # extra_single_image_response = submit_extra_single_image_request(extra_single_image_url, image_data)
        # # print(extra_single_image_response.json())
        # save_encoded_image(extra_single_image_response.json()['image'], output_path)