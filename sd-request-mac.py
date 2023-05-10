# loading API request stuff
import json
import base64
import requests

# loading zeromq stuff
# import time
# import zmq

import os

output_folder = "/Users/peku/Development/output"

import random

import datetime

# Get the current timestamp
now = datetime.datetime.now()

# Format the timestamp as a string, e.g., "2023-05-01_12-30-15"
timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")


# loading inky stuff
# from inky.auto import auto
# from PIL import Image, ImageFont, ImageDraw
# from font_source_serif_pro import SourceSerifProSemibold
# from font_source_sans_pro import SourceSansProSemibold

# keyboard input
# 'keyboard' doesn't work on macOS :(
# import keyboard
from pynput import keyboard

# setup inky
# inky_display = auto(ask_user=True, verbose=True)
# inky_display.set_border(inky_display.WHITE)

# font = ImageFont.truetype(SourceSerifProSemibold, 24)

# creating zeromq context and starting up the server
# context = zmq.Context()
# socket = context.socket(zmq.REP)
# socket = context.socket(zmq.PULL)
# print('Binding to port 5555')
# socket.bind("tcp://*:5555")

# poller = zmq.Poller()
# poller.register(socket, zmq.POLLIN)

# functions for API requests

def submit_post(url: str, data: dict):
    # Submit a POST request to the given URL with the given data.
    return requests.post(url, data=json.dumps(data))

def save_encoded_image(b64_image: str, output_path: str):
    # Save the given image to the given output path
    with open(output_path, "wb") as image_file:
        image_file.write(base64.b64decode(b64_image))

# def inky_refresh(text: str):
#     img = Image.new("P", (inky_display.width, inky_display.height))
#     draw = ImageDraw.Draw(img)
#     message = text
#     w, h = font.getsize(message)
#     x = (inky_display.width / 2) - (w / 2)
#     y = (inky_display.height / 2) - (h / 2)
#     draw.text((x, y), message, inky_display.BLACK, font)
#     inky_display.set_image(img)
#     inky_display.show()

# here comes the labels
labels1 = ["frightening", "scary", "uninterested", "dog", "curious", "excited", "cat", "flowerpot", "banana", "ghost", "alien", "chicken", "posh lonely"]
labels2 = ["joyful", "sombre", "romantic", "dreamy", "serene", "mysterious", "contemplative", "nostalgic", "intense", "whimsical", "golden hour", "dramatic", "natural", "neon"]
labels3 = ["boy", "dog", "cat", "girl", "pope", "business man", "tree", "forest", "wolf", "fields", "foxes", "family", "chair", "desk", "building"]

def on_press(key):
    pass

def on_release(key):
    try:
        # Check if the released key is 'g'
        if key.char == 'g':
            print("let's send a request now!")
            # prompt_msg = labels2[int(analog_values[2])] + " portrait of a " + labels1[int(analog_values[1])] + " " + labels3[int(analog_values[3])]
            prompt_msg = labels2[random.randint(0,12)] + " portrait of a " + labels1[random.randint(0,12)] + " " + labels3[0]
            print(prompt_msg)
            # inky_refresh(prompt_msg)
            txt2img_url = 'http://0.0.0.0:7861/sdapi/v1/txt2img'
            data = {'prompt': prompt_msg, 'steps': '25'}
            response = submit_post(txt2img_url, data)
            filename = timestamp + "_" + prompt_msg.replace(" ", "_") + '.png'
            output_path = os.path.join(output_folder, filename)
            # save_encoded_image(response.json()['images'][0], prompt_msg.replace(" ", "_") + "_" + timestamp + '.png')
            save_encoded_image(response.json()['images'][0], output_path)

            #img1 = Image.open('portrait.png')
            #img1.show()
    except AttributeError:
        pass

    if key == keyboard.Key.esc:
        # Stop the listener when the 'esc' key is pressed
        return False

# Start the keyboard listener
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()

# while True:
#     socks = dict(poller.poll())
#     if socket in socks:
#         message = socket.recv_multipart()
#         # parsing the received message into something usable.
#         # there must be a better way of doing this
#         analog_raw_values = message[1].decode().lstrip('[ ').rstrip('] ').replace(' ', '').split(',')
#         analog_values = [x for x in analog_raw_values]
#         print(analog_values)
#         # print(analog_values[1].lstrip(' '))
#         # if int(analog_values[2]) == 1:
#         if keyboard.is_pressed('g'):
#             print("let's send a request now!")
#             # prompt_msg = labels2[int(analog_values[2])] + " portrait of a " + labels1[int(analog_values[1])] + " " + labels3[int(analog_values[3])]
#             prompt_msg = labels2[random.randint(0,12)] + " portrait of a " + labels1[random.randint(0,12)] + " " + labels3[0]
#             print(prompt_msg)
#             # inky_refresh(prompt_msg)
#             txt2img_url = 'http://0.0.0.0:7861/sdapi/v1/txt2img'
#             data = {'prompt': prompt_msg, 'steps': '25'}
#             response = submit_post(txt2img_url, data)
#             save_encoded_image(response.json()['images'][0], + prompt_msg.replace(" ", "_") + "_" + timestamp + '.png')
#             #img1 = Image.open('portrait.png')
#             #img1.show()


#         # print(type(analog_raw_values))
#         # print(type(message[1].decode()))
#         # print(message[1].decode())