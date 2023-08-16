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

import random

import datetime

# Get the current timestamp
now = datetime.datetime.now()

# Format the timestamp as a string, e.g., "2023-05-01_12-30-15"
timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

# controlnet init image
image_path = "face_portrait_openpose.png"

from PIL import Image, PngImagePlugin

import artnet_inky_seedcfg

def setup_zmq_context_and_sockets():
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
    return context, input_socket, output_socket, poller

# functions for API requests

def submit_post(url: str, data: dict, retries = 3):
    for i in range(retries):
        try:
            # Submit a POST request to the given URL with the given data.
            return requests.post(url, data=json.dumps(data))
        except requests.exceptions.RequestException as e:
            print(f"RequestException: An error occurred while trying to send a POST request to {url}: {e}")
            if i < retries -1: # i is zero indexed
                time.sleep(1) # wait for a second before retry
            else:
                print(f"Failed to send POST request after {retries} attempts.")
        except Exception as e:
            print(f"An unexpected error occurred while trying to send a POST request: {e}")

def save_encoded_image(b64_image: str, output_path: str):
    try:
        # Save the given image to the given output path
        with open(output_path, "wb") as image_file:
            image_file.write(base64.b64decode(b64_image))
    except FileNotFoundError:
        print(f"FileNotFoundError: The output path {output_path} was not found.")
    except PermissionError:
        print(f"PermissionError: Permission denied when trying to write to the output file {output_path}.")
    except Exception as e:
        print(f"An unexpected error occurred while saving the encoded image: {e}")

def submit_extra_single_image_request(api_url, image_data, upscaling_resize=2, retries=3):
    for i in range(retries):
        try:
            payload = {
                "image": image_data,
                "upscaling_resize": upscaling_resize,
                "upscaler_1" : "ESRGAN_4x"
            }
            response = requests.post(api_url, json=payload)
            return response
        except requests.exceptions.RequestException as e:
            print(f"RequestException: An error occurred while trying to send a POST request to {api_url}: {e}")
            if i < retries - 1:  # i is zero indexed
                time.sleep(1)  # wait for a second before trying again
            else:
                print(f"Failed to send POST request after {retries} attempts.")
        except Exception as e:
            print(f"An unexpected error occurred while trying to send a POST request: {e}")

# Open an image and return it in a base64 string
def get_image_as_base64_string(image_path):
    try:
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
    except FileNotFoundError:
        print(f"FileNotFoundError: The image file {image_path} was not found.")
    except PermissionError:
        print(f"PermissionError: Permission denied when trying to open the image file {image_path}.")
    except Exception as e:
        print(f"An unexpected error occurred while getting the image as a base64 string: {e}")


# here comes the labels
# labels1 = ["frightening", "scary", "uninterested", "dog", "curious", "excited", "cat", "flowerpot", "banana", "ghost", "alien", "chicken", "posh lonely"]
# labels2 = ["joyful", "sombre", "romantic", "dreamy", "serene", "mysterious", "contemplative", "nostalgic", "intense", "whimsical", "golden hour", "dramatic", "natural", "neon"]
# labels3 = ["boy", "dog", "cat", "girl", "pope", "business man", "tree", "forest", "wolf", "fields", "foxes", "family", "chair", "desk", "building"]
# labels1 = ["vivid", "dramatic", "ethereal", "surreal", "cinematic", "minimalistic", "monochromatic", "abstract", "nostalgic", "majestic", "intimate", "inspiring", "radiant"]
labels1 = ["futuristic digital concept art", "vibrant pop art", "abstract expressionist", "dreamlike surrealist", "geometric cubist", "light-filled impressionist", "everyday realist", "romanticist", "antique neoclassical", "playful ornate rococo", "dramatic baroque", "renaissance"]
labels2 = ["ecstatic", "joyful", "happy", "optimistic", "contented", "calm", "indifferent", "bored", "anxious", "frustrated", "angry", "sad", "depressed"]
labels3 = ["1", "3", "5", "6", "7", "8", "9", "11", "15", "20", "25", "30"]
# labels3 = ["woman", "girl", "witch", "queen", "maiden", "matron", "dancer", "bride", "mother", "warrior", "goddess", "widow", "seductress"]

base64_controlnet_input_image = get_image_as_base64_string(image_path)

def main():
    context, input_socket, output_socket, poller = setup_zmq_context_and_sockets()
    seed = str(random.randint(10**11, 10**12-1))

    while True:
        try:
            events = dict(poller.poll())
            if input_socket in events: # and events[input_socket == zmq.POLLIN:
                message = input_socket.recv_multipart()
                # parsing the received message into something usable.
                # there must be a better way of doing this
                analog_raw_values = message[1].decode().lstrip('[ ').rstrip('] ').replace(' ', '').split(',')
                analog_values = [x for x in analog_raw_values] # converting to integer
                print(analog_values)
                print("let's send a request now!")
                # prompt_msg = labels1[int(analog_values[1])] + " portrait of a " + labels2[int(analog_values[2])] + " girl"
                prompt_msg = labels1[int(analog_values[1])] + " portrait of " + ("an " if labels2[int(analog_values[2])][0] in 'aeiou' else "a ") + labels2[int(analog_values[2])] + " girl"

                print(prompt_msg)
                print(seed)
                # artnet_inky.inky_refresh(prompt_msg, 30, seed, cfg_msg)
                progressapi_url = 'http://0.0.0.0:7860/sdapi/v1/progress'
                txt2img_url = 'http://0.0.0.0:7860/sdapi/v1/txt2img'
                extra_single_image_url = 'http://0.0.0.0:7860/sdapi/v1/extra-single-image'

                # switch's random state: '0', keep state: '1'
                if analog_values[4] == '0':
                    seed = str(random.randint(10**11, 10**12-1))
                    print("Seed updated: ", seed)
                elif analog_values[4] == '1':
                    print("Seed kept the same: ", seed)
                    # seed = seed
                cfg_msg = labels3[int(analog_values[3])]
                print(cfg_msg)
                artnet_inky_seedcfg.inky_refresh(prompt_msg, 30, seed, cfg_msg)
                data = {
                'prompt': prompt_msg,
                'negative_prompt': 'deformed, ugly, tiling, poorly drawn hands, poorly drawn feet, poorly drawn face, out of frame, extra limbs',
                'steps': '10',
                'cfg_scale': cfg_msg,
                'width': '384',
                'height': '512',
                'enable_hr': 'true',
                'denoising_strength': '0.7',
#                 'firstphase_width': '288',
#                 'firstphase_height': '512',
                'hr_scale': '2',
                'hr_upscaler': 'ESRGAN_4x',
                'hr_resize_x': '768',
                'hr_resize_y': '1024',
                'sampler_name': 'Euler',
                'save_images': 'true',
                'seed': seed,
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
                extra_single_image_url = 'http://0.0.0.0:7860/sdapi/v1/extra-single-image'

                image_data = final_image
        except zmq.ZMQError as e:
            print(f"ZMQError: An error occurred while receiving a message from the socket: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while polling or receiving a message from the socket: {e}")

if __name__ == "__main__":
    main()