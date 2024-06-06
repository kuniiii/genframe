import sys # loading the /modules path
sys.path.insert(1, '/home/peterkun/Desktop/Development/modules/')

import base64
import zmq
import io
import random
import datetime
from PIL import Image
import artnet_inky_seedcfg
import sd_request_progress_new

output_folder = "/home/peterkun/Desktop/output/"

# Get the current timestamp
now = datetime.datetime.now()

# Format the timestamp as a string, e.g., "2023-05-01_12-30-15"
timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

# controlnet init image
image_path = "face_portrait_openpose.png"

# here comes the labels
labels1 = ["futuristic digital concept art", "vibrant pop art", "abstract expressionist", "dreamlike surrealist", "geometric cubist", "light-filled impressionist", "everyday realist", "romanticist", "antique neoclassical", "playful ornate rococo", "dramatic baroque", "renaissance"]
labels2 = ["ecstatic", "joyful", "happy", "optimistic", "contented", "calm", "indifferent", "bored", "anxious", "frustrated", "angry", "sad", "depressed"]
labels3 = ["1", "3", "5", "6", "7", "8", "9", "11", "15", "20", "25", "30"]

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
    # parsing the received message into something usable.
    # there must be a better way of doing this
    analog_raw_values = message[1].decode().lstrip('[ ').rstrip('] ').replace(' ', '').split(',')
    analog_values = [x for x in analog_raw_values] # converting to integer
    print(analog_values)
    print("let's send a request now!")
    prompt_msg = construct_prompt(labels1, labels2, analog_values)
    print(prompt_msg)
    print(seed)
    
    # switch's random state: '0', keep state: '1'
    if analog_values[4] == '0':
        seed = str(random.randint(10**11, 10**12-1))
        print("Seed updated: ", seed)
    elif analog_values[4] == '1':
        print("Seed kept the same: ", seed)
    
    cfg_msg = labels3[int(analog_values[3])]
    print(cfg_msg)
    artnet_inky_seedcfg.inky_refresh(prompt_msg, 30, seed, cfg_msg)
    
    data = construct_data(prompt_msg, cfg_msg, base64_controlnet_input_image, seed)
    return data, seed

def main():
    context, input_socket, output_socket, poller = setup_zmq_context_and_sockets()
    seed = str(random.randint(10**11, 10**12-1))
    base64_controlnet_input_image = get_image_as_base64_string(image_path)
    progressapi_url = 'http://res52.itu.dk:8022/sdapi/v1/progress'
    txt2img_url = 'http://res52.itu.dk:8022/sdapi/v1/txt2img'

    while True:
        try:
            events = dict(poller.poll())
            if input_socket in events:
                message = input_socket.recv_multipart()
                data, seed = process_message(message, labels1, labels2, labels3, base64_controlnet_input_image, seed) 
                
                # Run the first function and get the final image
                final_image, progress = sd_request_progress_new.run_process_txt2img(txt2img_url, data, progressapi_url, output_socket)
                
                print("Progress in main:", progress)
                image_data = final_image
        except zmq.ZMQError as e:
            print(f"ZMQError: An error occurred while receiving a message from the socket: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while polling or receiving a message from the socket: {e}")

if __name__ == "__main__":
    main()