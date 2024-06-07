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

# Function to create and return a Tkinter window and label for image display
def create_image_window():
    window = tk.Tk()
    window.title("GenFrame Portraits")
    # Check if the script was started with --fullscreen argument
    if '--fullscreen' in sys.argv:
        window.attributes('-fullscreen', True)  # Set the window to fullscreen
        window.configure(background='black')  # Set background to black
    else:
        window.configure(background='black')  # Set background to black even if not fullscreen

    # Initial dummy image to initialize the label
    img = PhotoImage(width=1, height=1)
    label = Label(window, image=img, bg='black')  # Ensure label background is also black
    label.image = img  # Keep a reference so it's not garbage collected
    label.pack(expand=True)  # Center the content in the window
    return window, label

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def blend_images(image1, image2, window, label, steps=10, duration=0.0001):
    # Create a smooth transition between two images.
    # :param image1: The first PIL Image object.
    # :param image2: The second PIL Image object.
    # :param window: The Tkinter window object.
    # :param label: The Tkinter label used for displaying the image.
    # :param steps: Number of steps in the transition.
    # :param duration: Total duration of the transition in seconds.
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
    target_width, target_height = 1392, 768 #TODO REVISE
    previous_image = None

    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            print(message)
                # Check if execution is complete
            if message['type'] == 'executing' and message['data'].get('node') is None:
                    execution_complete = True # Set flag to true when execution is complete
                    break # Exit the loop since execution is done
            else:
                try:
                    # Process the image data
                    current_image = Image.open(io.BytesIO(out[8:])) # Load image data from bytes
                    # Resize the image to fit the window, maintaining the aspect ratio
                    current_image = current_image.resize((target_width, target_height), Image.LANCZOS)

                    if previous_image is not None:
                        # Perform the crossfade transition between the previous and current images
                        blend_images(previous_image, current_image, window, label, steps=10, duration=0.00001)
                        # continue
                    else:
                        # Directly show the current image if there is no previous image
                        photo = ImageTk.PhotoImage(current_image)
                        label.config(image=photo)
                        label.image = photo  # Keep a reference so it's not garbage collected
                        window.update()

                    previous_image = current_image  # Update the previous image
                except Exception as e:
                    print(f"Error processing image: {e}")

workflow_path = os.path.join(os.path.dirname(__file__), 'workflow_api-sdxl-solarpunk.json')
# workflow_path = os.path.join(os.path.dirname(__file__), 'workflow_api_ws_solarpunk_sdxlturbo.json')
with open(workflow_path, 'r') as file:
    prompt_text = file.read()

prompt = json.loads(prompt_text)

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
    print("constructed prompt:", prompt_msg)
    print("seed:", seed)
    
    if analog_values[4] == '0':
        seed = str(random.randint(10**11, 10**12-1))
        print("Seed updated: ", seed)
    elif analog_values[4] == '1':
        print("Seed kept the same: ", seed)
    
    cfg_msg = labels3[int(analog_values[3])]
    print("cfg_msg:", cfg_msg)
    
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
                prompt["6"]["inputs"]["text"] = labels1
                # Run the first function and get the final image
                # Example: get_images(ws, "sample prompt", window, label)

        except zmq.ZMQError as e:
            print(f"ZMQError: An error occurred while receiving a message from the socket: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while polling or receiving a message from the socket: {e}")

def main():
    # Setup logging (uncomment if logging is desired)
    # setup_logging()

    labels1 = ["futuristic digital concept art", "vibrant pop art", "abstract expressionist", "dreamlike surrealist", "geometric cubist", "light-filled impressionist", "everyday realist", "romanticist", "antique neoclassical", "playful ornate rococo", "dramatic baroque", "renaissance"]
    labels2 = ["ecstatic", "joyful", "happy", "optimistic", "contented", "calm", "indifferent", "bored", "anxious", "frustrated", "angry", "sad", "depressed"]
    labels3 = ["1", "3", "5", "6", "7", "8", "9", "11", "15", "20", "25", "30"]
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
