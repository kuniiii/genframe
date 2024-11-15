import zmq
import aiohttp
import asyncio
import base64
# import requests
# import json
import artnet_inky_seedcfg
import time
from secrets import USERNAME, PASSWORD

async def submit_post(session: aiohttp.ClientSession, url: str, data: dict):
    # Encode credentials
    credentials = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
    headers = {"Authorization": f"Basic {credentials}"}
    try:
        async with session.post(url, json=data, headers=headers) as response:
            return await response.json()
    except aiohttp.ClientError as e:
        print(f"ClientError: An error occurred while trying to send a POST request to {url}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while trying to send a POST request: {e}")

async def submit_get(session: aiohttp.ClientSession, url: str):
    # Submit a GET request to the given URL.
    # Encode credentials
    credentials = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
    headers = {"Authorization": f"Basic {credentials}"}
    async with session.get(url, headers=headers) as response:
        return await response.json()

async def process_txt2img(txt2img_url: str, data: dict, progressapi_url: str, output_socket: zmq.Socket):
    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        # Submit txt2img post request
        txt2img_task = asyncio.create_task(submit_post(session, txt2img_url, data))  # Await the task
        print("txt2img going on")
        artnet_inky_seedcfg.inky_painting("painting...", 30)
        # Initialize the counter for the image steps
        step_counter = 1

        # Check progress while waiting for txt2img response
        while not txt2img_task.done():
            response = await submit_get(session, progressapi_url)
            print(f"Progress iteration: {step_counter}")
            print(response['progress'])

            if 'current_image' in response and response['current_image']:
                response_img_base64_encoded = response['current_image']
                response_img_to_send = response_img_base64_encoded.encode()
                output_socket.send_multipart([b"client1", response_img_to_send, b"progress"])
                print(f"Progress image {step_counter} sent")
                step_counter += 1

            await asyncio.sleep(0.1)  # Avoid overloading the server, adjust sleep time as needed

        # Send the final image through ZeroMQ
        final_response = await txt2img_task
        if 'images' in final_response and final_response['images']:
            artnet_inky_seedcfg.inky_refresh(data['prompt'], 30, data['seed'], data['cfg_scale'])
            response_img_base64_encoded = final_response['images'][0]
            response_img_to_send = response_img_base64_encoded.encode()
            output_socket.send_multipart([b"client1", response_img_to_send, b"final"])
            print("Final image sent")
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"Time taken by process_txt2img: {elapsed_time} seconds")  # Print the elapsed time
        return response_img_base64_encoded if 'images' in final_response else None

def run_process_txt2img(txt2img_url: str, data: dict, progressapi_url: str, output_socket: zmq.Socket):
    final_image = asyncio.run(process_txt2img(txt2img_url, data, progressapi_url, output_socket))
    return final_image  # Return the final image as base64 encoded