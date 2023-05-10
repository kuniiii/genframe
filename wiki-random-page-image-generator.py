import requests
import time
import json
import base64

import os

output_folder = "/Users/peku/Development/output-wiki"

import datetime

# Get the current timestamp
now = datetime.datetime.now()

# Format the timestamp as a string, e.g., "2023-05-01_12-30-15"
timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

def submit_post(url: str, data: dict):
    # Submit a POST request to the given URL with the given data.
    return requests.post(url, data=json.dumps(data))

def save_encoded_image(b64_image: str, output_path: str):
    # Save the given image to the given output path
    with open(output_path, "wb") as image_file:
        image_file.write(base64.b64decode(b64_image))

def get_random_wikipedia_page_title():
    url = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=random&rnnamespace=0&rnlimit=1"
    response = requests.get(url)

    if response.status_code == 200:
        json_data = response.json()
        random_page_title = json_data["query"]["random"][0]["title"]
        return random_page_title
    else:
        print(f"Error: Unable to fetch data from the Wikipedia API. Status code: {response.status_code}")
        return None

while True:
    random_page_title = get_random_wikipedia_page_title()
    if random_page_title is not None:
        print(f"Random Wikipedia page title: {random_page_title}")
        txt2img_url = 'http://0.0.0.0:7861/sdapi/v1/txt2img'
        data = {'prompt': random_page_title + " by Carl Bloch", 'steps': '25'}
        response = submit_post(txt2img_url, data)
        filename = timestamp + "_" + random_page_title.replace(" ", "_") + '.png'
        output_path = os.path.join(output_folder, filename)
        # save_encoded_image(response.json()['images'][0], prompt_msg.replace(" ", "_") + "_" + timestamp + '.png')
        save_encoded_image(response.json()['images'][0], output_path)

    time.sleep(10)  # Pause for 60 seconds before making the next request
