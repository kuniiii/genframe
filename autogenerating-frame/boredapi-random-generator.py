import requests
import time
import json
import base64
import io
from PIL import Image, PngImagePlugin

import os

output_folder = "/Users/peku/Development/output-boredapi"

import datetime

# Get the current timestamp
now = datetime.datetime.now()

# Format the timestamp as a string, e.g., "2023-05-01_12-30-15"
timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

image_path = "/Users/peku/Development/artnet/picture-frame-rpi4/face_portrait_openpose.png"

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

def get_random_activity():
    url = "https://www.boredapi.com/api/activity"
    response = requests.get(url)

    if response.status_code == 200:
        json_data = response.json()
        activity = json_data["activity"]
        return activity
    else:
        print(f"Error: Unable to fetch data from the Bored API. Status code: {response.status_code}")
        return None

# def get_random_wikipedia_page_title():
#     url = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=random&rnnamespace=0&rnlimit=1"
#     response = requests.get(url)

#     if response.status_code == 200:
#         json_data = response.json()
#         random_page_title = json_data["query"]["random"][0]["title"]
#         return random_page_title
#     else:
#         print(f"Error: Unable to fetch data from the Wikipedia API. Status code: {response.status_code}")
#         return None

base64_controlnet_input_image = get_image_as_base64_string(image_path)

while True:
    # random_page_title = get_random_wikipedia_page_title()
    # if random_page_title is not None:
    random_activity = get_random_activity()
    if random_activity is not None:
        print(f"Random activity: {random_activity}")


        txt2img_url = 'http://10.28.44.87:7860/sdapi/v1/txt2img'
        data = {
            'prompt': "A friendly Viktor Orban " + random_activity + " by Edward Hopper",
            'steps': '40',
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
        filename = timestamp + "_" + random_activity.replace(" ", "_") + '.png'
        output_path = os.path.join(output_folder, filename)
        # save_encoded_image(response.json()['images'][0], prompt_msg.replace(" ", "_") + "_" + timestamp + '.png')
        # save_encoded_image(response.json()['images'][0], output_path)

        # Submit the extra-single-image request
        extra_single_image_url = 'http://10.28.44.87:7860/sdapi/v1/extra-single-image'
        image_data = response.json()['images'][0]
        extra_single_image_response = submit_extra_single_image_request(extra_single_image_url, image_data)
        # print(extra_single_image_response.json())
        save_encoded_image(extra_single_image_response.json()['image'], output_path)

        # Handle the response from the extra-single-image request as needed
        # For example, you could save the returned image or print additional information

        # r = response.json()['images'][0]
        # for i in r['images']:
        #     print ("Let's go further")
        #     image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))
        #     png_payload = {
        #         "image": "data:image/png;base64," + i
        #     }
        #     print ("Prepped payload")
        #     response2 = requests.post(url = 'http://0.0.0.0:7861/sdapi/v1/extra-single-image', json=png_payload)
        #     print ("Sent payload")
        #     save_encoded_image(response2.json()['images'][0], output_path)


        # upscaler_url = 'http://0.0.0.0:7861/sdapi/v1/extra-single-image'
        # data = {response.json()['images'][0]}


    time.sleep(10)  # Pause for 60 seconds before making the next request