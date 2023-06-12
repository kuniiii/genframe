import zmq
import aiohttp
import asyncio
import base64
# import requests
# import json

async def submit_post(session: aiohttp.ClientSession, url: str, data: dict):
    """
    Submit a POST request to the given URL with the given data.
    """
    async with session.post(url, json=data) as response:
        return await response.json()

async def submit_get(session: aiohttp.ClientSession, url: str):
    """
    Submit a GET request to the given URL.
    """
    async with session.get(url) as response:
        return await response.json()

async def process_txt2img(txt2img_url: str, data: dict, progressapi_url: str, output_socket: zmq.Socket):
    async with aiohttp.ClientSession() as session:
        # Submit txt2img post request
        txt2img_task = asyncio.create_task(submit_post(session, txt2img_url, data))  # Await the task
        print("txt2img going on")

        # Initialize the counter for the image steps
        step_counter = 1

        # Check progress while waiting for txt2img response
        while not txt2img_task.done():
            response = await submit_get(session, progressapi_url)
            print(f"Progress iteration: {step_counter}")

            if 'current_image' in response and response['current_image']:
                response_img_base64_encoded = response['current_image']
                response_img_to_send = response_img_base64_encoded.encode()
                output_socket.send_multipart([b"client1", response_img_to_send, b"progress"])
                print(f"Progress image {step_counter} sent")
                step_counter += 1

            await asyncio.sleep(1)  # Avoid overloading the server, adjust sleep time as needed

        # Send the final image through ZeroMQ
        final_response = await txt2img_task
        if 'images' in final_response and final_response['images']:
            response_img_base64_encoded = final_response['images'][0]
            response_img_to_send = response_img_base64_encoded.encode()
            output_socket.send_multipart([b"client1", response_img_to_send, b"final"])
            print("Final image sent")
        return response_img_base64_encoded if 'images' in final_response else None

def run_process_txt2img(txt2img_url: str, data: dict, progressapi_url: str, output_socket: zmq.Socket):
    final_image = asyncio.run(process_txt2img(txt2img_url, data, progressapi_url, output_socket))
    return final_image  # Return the final image as base64 encoded

# def submit_extra_single_image_request(single_img_extra_url: str, image_data, upscaling_resize: int, output_socket: zmq.Socket):
#     print("About to submit extra single image request")
#     payload = {
#         "image": image_data,
#         "upscaling_resize": upscaling_resize,
#         "upscaler_1" : "ESRGAN_4x"
#     }

#     response = requests.post(single_img_extra_url, json=payload)
#     response_data = response.json()
#     if 'image' in response.json() and response.json()['image']:
#         print("we have image in response!")
#         response_img_base64_encoded = response.json()['image'][0]
#         response_img_to_send = response_img_base64_encoded.encode('ascii')
#         output_socket.send_multipart([b"client1", response_img_to_send, b"final_single_img_extra"])
#         return response_img_to_send
#     else:
#         print("No image in response")
#         return None

# async def process_single_img_extra(single_img_extra_url: str, data: dict, progressapi_url: str, output_socket: zmq.Socket):
#     async with aiohttp.ClientSession() as session:
#         print("About to submit post")
#         single_img_extra_task = asyncio.create_task(submit_post(session, single_img_extra_url, data))
#         print("Post submitted")
#         step_counter = 1
#         while not single_img_extra_task.done():
#             response = await submit_get(session, progressapi_url)
#             print(f"Single img extra progress iteration: {step_counter}")
#             print(response)
#             if 'current_image' in response and response['current_image']:
#                 response_img_base64_encoded = response['current_image']
#                 response_img_to_send = response_img_base64_encoded.encode()
#                 output_socket.send_multipart([b"client1", response_img_to_send, b"process_single_img_extra"])
#                 print(f"Progress single extra image {step_counter} sent")
#                 step_counter += 1
#             await asyncio.sleep(1)
#         final_response = await single_img_extra_task
#         if 'images' in final_response and final_response['images']:
#             response_img_base64_encoded = final_response['images'][0]
#             response_img_to_send = response_img_base64_encoded.encode()
#             output_socket.send_multipart([b"client1", response_img_to_send, b"final_extra"])
#             print("Final single extra image sent")

# def run_process_single_img_extra(single_img_extra_url: str, data: dict, progressapi_url: str, output_socket: zmq.Socket):
#     asyncio.run(process_single_img_extra(single_img_extra_url, data, progressapi_url, output_socket))