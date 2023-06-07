import tkinter as tk
import zmq
from PIL import Image, ImageTk
import base64
import io

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

async def main():
    txt2img_url = 'http://0.0.0.0:7861/sdapi/v1/txt2img'
    data = {
        'prompt': 'a cat wearing a hat',
        'steps': 5
    }

    async with ClientSession() as session:
        # ZeroMQ setup
        context = zmq.Context()
        input_socket = context.socket(zmq.SUB)
        input_socket.connect("tcp://localhost:5556")
        input_socket.setsockopt_string(zmq.SUBSCRIBE, "client1")

        # Create a tkinter window
        window = tk.Tk()
        window.title("Progress Viewer")

        # Create a label for displaying images
        image_label = tk.Label(window)
        image_label.pack()

        # Submit txt2img post request
        response = await submit_post(session, txt2img_url, data)
        print("txt2img going on")

        progressapi_url = 'http://0.0.0.0:7861/sdapi/v1/progress'

        # Initialize the counter for the image steps
        step_counter = 1

        # Check progress while waiting for txt2img response
        iteration_count = 0
        max_iterations = 10  # Set a maximum number of iterations for testing purposes

        while 'current_image' not in response or not response['current_image']:
            print("progress going on")
            response = await submit_get(session, progressapi_url)
            print(f"Iteration: {iteration_count}")
            print(f"Response: {response}")
            print(f"Response keys: {response.keys()}")

            iteration_count += 1
            if iteration_count >= max_iterations:
                break

            await asyncio.sleep(1)  # Avoid overloading the server, adjust sleep time as needed

        # Check progress while waiting for txt2img response
#         while 'current_image' not in response or not response['current_image']:
#             print("progress going on")
#             response = await submit_get(session, progressapi_url)
#             await asyncio.sleep(1)  # Avoid overloading the server, adjust sleep time as needed

        # Send the progress images through ZeroMQ
        while 'current_image' in response and response['current_image']:
            print("we should send now")
            image_data = base64.b64decode(response['current_image'])
            image = Image.open(io.BytesIO(image_data))
            photo = ImageTk.PhotoImage(image)
            image_label.config(image=photo)
            image_label.image = photo

            print(f"Progress image {step_counter} sent")
            step_counter += 1

            print(f"Response: {response}")
            print(f"Current image: {response['current_image']}")

            response = await submit_get(session, progressapi_url)
            if 'current_image' in response and not response['current_image']:
                break  # No more progress images, exit the loop

            await asyncio.sleep(1)  # Avoid overloading the server, adjust sleep time as needed

        # Send the final image through ZeroMQ
        if 'images' in response and response['images']:
            image_data = base64.b64decode(response['images'][0])
            image = Image.open(io.BytesIO(image_data))
            photo = ImageTk.PhotoImage(image)
            image_label.config(image=photo)
            image_label.image = photo
            print("Final image sent")

    # Clean up ZeroMQ resources
    input_socket.close()
    context.term()

    # Start the tkinter event loop
    window.mainloop()

if __name__ == '__main__':
    asyncio.run(main())