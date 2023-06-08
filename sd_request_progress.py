import zmq
import aiohttp
import asyncio
import base64

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
                output_socket.send_multipart([b"client1", response_img_to_send])
                print(f"Progress image {step_counter} sent")
                step_counter += 1

            await asyncio.sleep(1)  # Avoid overloading the server, adjust sleep time as needed

        # Send the final image through ZeroMQ
        final_response = await txt2img_task
        if 'images' in final_response and final_response['images']:
            response_img_base64_encoded = final_response['images'][0]
            response_img_to_send = response_img_base64_encoded.encode()
            output_socket.send_multipart([b"client1", response_img_to_send])
            print("Final image sent")

def run_process_txt2img(txt2img_url: str, data: dict, progressapi_url: str, output_socket: zmq.Socket):
    asyncio.run(process_txt2img(txt2img_url, data, progressapi_url, output_socket))