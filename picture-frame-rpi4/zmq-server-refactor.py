# loading modules
import sys
# caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(1, '/home/peterkun/Desktop/Development/modules/')

import sd_request_progress

# loading API request stuff
import json
import base64
import requests

# loading zeromq stuff
import time
import zmq

import io
import os

output_folder = "/home/peterkun/Desktop/output/"

import datetime

# Get the current timestamp
now = datetime.datetime.now()

# Format the timestamp as a string, e.g., "2023-05-01_12-30-15"
timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

# controlnet init image
image_path = "face_portrait_openpose.png"

from PIL import Image, PngImagePlugin

import artnet_inky

# creating zeromq context and starting up the server
context = zmq.Context()
input_socket = context.socket(zmq.SUB)
print('Binding to port 5555')
input_socket.bind("tcp://*:5555")
input_socket.setsockopt(zmq.SUBSCRIBE, b"client1")

output_socket = context.socket(zmq.PUB)
output_socket.bind("tcp://*:5556")  # Bind to a different port

poller = zmq.Poller()
poller.register(input_socket, zmq.POLLIN)

# functions for API requests

def submit_post(url: str, data: dict):
    # Submit a POST request to the given URL with the given data.
    return requests.post(url, data=json.dumps(data))

def save_encoded_image(b64_image: str, output_path: str):
    # Save the given image to the given output path
    with open(output_path, "wb") as image_file:
        image_file.write(base64.b64decode(b64_image))

def submit_extra_single_image_request(api_url, image_data, upscaling_resize=2):
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
# labels1 = ["frightening", "scary", "uninterested", "dog", "curious", "excited", "cat", "flowerpot", "banana", "ghost", "alien", "chicken", "posh lonely"]
# labels2 = ["joyful", "sombre", "romantic", "dreamy", "serene", "mysterious", "contemplative", "nostalgic", "intense", "whimsical", "golden hour", "dramatic", "natural", "neon"]
# labels3 = ["boy", "dog", "cat", "girl", "pope", "business man", "tree", "forest", "wolf", "fields", "foxes", "family", "chair", "desk", "building"]
labels1 = ["vivid", "dramatic", "ethereal", "surreal", "cinematic", "minimalistic", "monochromatic", "abstract", "nostalgic", "majestic", "intimate", "inspiring", "radiant"]
labels2 = ["ecstatic", "joyful", "optimistic", "contented", "calm", "indifferent", "bored", "anxious", "frustrated", "angry", "sad", "depressed", "despairing"]
labels3 = ["woman", "girl", "witch", "queen", "maiden", "matron", "dancer", "bride", "mother", "warrior", "goddess", "widow", "seductress"]

base64_controlnet_input_image = get_image_as_base64_string(image_path)

while True:
    events = dict(poller.poll())
    if input_socket in events: # and events[input_socket == zmq.POLLIN:
        message = input_socket.recv_multipart()
        # parsing the received message into something usable.
        # there must be a better way of doing this
        analog_raw_values = message[1].decode().lstrip('[ ').rstrip('] ').replace(' ', '').split(',')
        analog_values = [x for x in analog_raw_values]
        print(analog_values)
        print("let's send a request now!")
        prompt_msg = labels1[int(analog_values[1])] + " portrait of a " + labels2[int(analog_values[2])] + " " + labels3[int(analog_values[3])]
        print(prompt_msg)

        artnet_inky.inky_refresh(prompt_msg, 30)
        progressapi_url = 'http://0.0.0.0:7861/sdapi/v1/progress'
        txt2img_url = 'http://0.0.0.0:7861/sdapi/v1/txt2img'
        extra_single_image_url = 'http://0.0.0.0:7861/sdapi/v1/extra-single-image'
        data = {
        'prompt': prompt_msg,
        'negative_prompt': 'deformed, ugly, tiling, poorly drawn hands, poorly drawn feet, poorly drawn face, out of frame, extra limbs',
        'steps': '10',
        #'width': '384',
        #'height': '512',
        'enable_hr': 'true',
        'denoising_strength': '0.7',
        'firstphase_width': '384',
        'firstphase_height': '512',
        'hr_scale': '2',
        'hr_upscaler': 'ESRGAN_4x',
        'hr_resize_x': '768',
        'hr_resize_y': '1024',
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
        # Run the first function and get the final image
        final_image = sd_request_progress.run_process_txt2img(txt2img_url, data, progressapi_url, output_socket)
        # sd_request_progress.run_process_txt2img(txt2img_url, data, progressapi_url, output_socket)

        # Submit the extra-single-image reques
        extra_single_image_url = 'http://0.0.0.0:7861/sdapi/v1/extra-single-image'
        # image_data = response.json()['images'][0]
        image_data = final_image
        # extra_single_image_response = submit_extra_single_image_request(extra_single_image_url, image_data).json()
        # print(extra_single_image_response.keys())
        # extra_single_image_to_send = extra_single_image_response['image'].encode()
        # print(extra_single_image_to_send)
        # output_socket.send_multipart([b"client1", extra_single_image_to_send, b"upscaled"])
        # print(extra_single_image_response.json())
        # save_encoded_image(extra_single_image_response.json()['image'], output_path)


        # Submit the extra-single-image reques
        # extra_single_image_url = 'http://0.0.0.0:7861/sdapi/v1/extra-single-image'
        # extra_single_image_response = sd_request_progress.submit_extra_single_image_request(extra_single_image_url, final_image, 2, output_socket)
        # print("we did it!")

        # save_encoded_image(extra_single_image_response.json()['image'], output_path)

        # response = submit_post(txt2img_url, data)
        # response_img_base64_encoded = response.json()['images'][0]
        # response_img_to_send = response_img_base64_encoded.encode()
        # save_encoded_image(response.json()['images'][0], prompt_msg + '.png')
        # print(response.json()['images'][0])
        # output_socket.send_multipart([b"client1", response_img_to_send])
        # filename = timestamp + "_" + prompt_msg.replace(" ", "_") + '.png'
        # output_path = os.path.join(output_folder, filename)