import zmq
import base64
import asyncio
from aiohttp import ClientSession

async def submit_post(session: ClientSession, url: str, data: dict):
    """
    Submit a POST request to the given URL with the given data.
    """
    async with session.post(url, json=data) as response:
        return await response.json()

async def submit_get(session: ClientSession, url: str):
    """
    Submit a GET request to the given URL.
    """
    async with session.get(url) as response:
        return await response.json()

async def process_txt2img(txt2img_url: str, data: dict, progressapi_url: str, output_socket: zmq.Socket):
    async with ClientSession() as session:
        # Submit txt2img post request
        txt2img_task = asyncio.create_task(submit_post(session, txt2img_url, data))
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

async def main():
    txt2img_url = 'http://0.0.0.0:7861/sdapi/v1/txt2img'
    data = {
        'prompt': 'a cat wearing a hat, oil on canvas',
        'steps': 150
    }

    progressapi_url = 'http://0.0.0.0:7861/sdapi/v1/progress'

    context = zmq.Context()
    output_socket = context.socket(zmq.PUB)
    output_socket.bind("tcp://*:5556")  # Bind to a different port

    await process_txt2img(txt2img_url, data, progressapi_url, output_socket)

    # Clean up ZeroMQ resources
    output_socket.close()
    context.term()

if __name__ == '__main__':
    asyncio.run(main())