import websocket
import uuid
import json
import urllib.request
import urllib.parse
import base64
import os
import logging
import random
import tkinter as tk
from tkinter import PhotoImage, Label
from PIL import Image, ImageTk
import io
import time
import threading
import sys
import zmq

def setup_logging():
    logger = logging.getLogger('websocket')
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler('websocket_trace_again.log')
    fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.propagate = False
    websocket.enableTrace(True, handler=fh)

server_address = "artnet.itu.dk:8100"
client_id = str(uuid.uuid4())

# controlnet init image
image_path = "face_portrait_openpose.png"

def create_image_window():
    window = tk.Tk()
    window.title("Received Image")
    if '--fullscreen' in sys.argv:
        window.attributes('-fullscreen', True)
        window.configure(background='black')
    else:
        window.configure(background='black')

    img = PhotoImage(width=1, height=1)
    label = Label(window, image=img, bg='black')
    label.image = img
    label.pack(expand=True)
    return window, label

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def blend_images(image1, image2, window, label, steps=10, duration=0.0001):
    for step in range(steps + 1):
        alpha = step / steps
        blended_image = Image.blend(image1, image2, alpha)
        photo = ImageTk.PhotoImage(blended_image)
        label.config(image=photo)
        label.image = photo
        window.update()

execution_complete = True

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


def get_images(ws, prompt, window, label):
    global execution_complete
    if not execution_complete:
        print("Execution haven't finished. Ignoring key press.")
        return
    execution_complete = False
    prompt_id = queue_prompt(prompt)['prompt_id']
    target_width, target_height = 1392, 768
    previous_image = None

    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            print(message)
            if message['type'] == 'executing' and message['data'].get('node') is None:
                execution_complete = True
                break
        else:
            try:
                current_image = Image.open(io.BytesIO(out[8:]))
                if previous_image is None:
                    previous_image = current_image
                else:
                    blend_images(previous_image, current_image, window, label)
                    previous_image = current_image
            except Exception as e:
                print(f"Error processing image: {e}")

def setup_zmq_context_and_sockets():
    context = zmq.Context()
    input_socket = context.socket(zmq.SUB)
    print('Binding to port 55555')
    input_socket.bind("tcp://*:55555")
    input_socket.setsockopt(zmq.SUBSCRIBE, b"client1")

    output_socket = context.socket(zmq.PUB)
    output_socket.bind("tcp://*:55556")

    poller = zmq.Poller()
    poller.register(input_socket, zmq.POLLIN)
    return context, input_socket, output_socket, poller

def construct_prompt(labels1, labels2, analog_values):
    return labels1[int(analog_values[1])] + " portrait of " + ("an " if labels2[int(analog_values[2])][0] in 'aeiou' else "a ") + labels2[int(analog_values[2])] + " girl"

def construct_data(prompt_msg, cfg_msg, base64_controlnet_input_image, seed):
    return {
        'prompt': prompt_msg,
        'negative_prompt': 'deformed, ugly, tiling, poorly drawn hands, poorly drawn feet, poorly drawn face, out of frame, extra limbs',
        'steps': '5',
        'cfg_scale': cfg_msg,
        'width': '384',
        'height': '512',
        'enable_hr': 'true',
        'denoising_strength': '0.7',
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


def process_message(message, labels1, labels2, labels3, base64_controlnet_input_image, seed):
    analog_raw_values = message[1].decode().lstrip('[ ').rstrip('] ').replace(' ', '').split(',')
    analog_values = [x for x in analog_raw_values]
    print(analog_values)
    print("let's send a request now!")
    prompt_msg = construct_prompt(labels1, labels2, analog_values)
    print(prompt_msg)
    print(seed)
    
    if analog_values[4] == '0':
        seed = str(random.randint(10**11, 10**12-1))
        print("Seed updated: ", seed)
    elif analog_values[4] == '1':
        print("Seed kept the same: ", seed)
    
    cfg_msg = labels3[int(analog_values[3])]
    print(cfg_msg)
    
    data = construct_data(prompt_msg, cfg_msg, base64_controlnet_input_image, seed)
    return data, seed

def zmq_thread(labels1, labels2, labels3, image_path):
    context, input_socket, output_socket, poller = setup_zmq_context_and_sockets()
    seed = str(random.randint(10**11, 10**12-1))
    base64_controlnet_input_image = get_image_as_base64_string(image_path)

    while True:
        try:
            events = dict(poller.poll())
            if input_socket in events:
                message = input_socket.recv_multipart()
                data, seed = process_message(message, labels1, labels2, labels3, base64_controlnet_input_image, seed) 
                
                # Run the first function and get the final image
                # HERE COMES A FUNCTION THAT MAKES A CALL

        except zmq.ZMQError as e:
            print(f"ZMQError: An error occurred while receiving a message from the socket: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while polling or receiving a message from the socket: {e}")

def main():
    labels1 = ['asd', 'basd']  # Replace with actual labels
    labels2 = ['asd', 'basd']  # Replace with actual labels
    labels3 = ['asd', 'basd']  # Replace with actual labels
    # image_path = 'path_to_image'  # Replace with the actual image path

    # Start the ZeroMQ thread
    zmq_thread_instance = threading.Thread(target=zmq_thread, args=(labels1, labels2, labels3, image_path))
    zmq_thread_instance.start()

    # Tkinter GUI setup
    window, label = create_image_window()
    
    # WebSocket setup and interaction (add your WebSocket logic here)
    
    # Start the Tkinter main loop
    window.mainloop()

if __name__ == "__main__":
    main()
