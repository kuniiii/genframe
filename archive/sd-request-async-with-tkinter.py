import argparse
import json
import base64
import asyncio
from aiohttp import ClientSession
from PIL import Image, ImageTk, ImageFilter
import io
import os
import tkinter as tk
from typing import Optional
import logging
import threading

logging.basicConfig(level=logging.INFO)

def create_window() -> tk.Tk:
    window = tk.Tk()
    window.attributes('-fullscreen', True)
    window.bind('<Escape>', lambda e: window.quit())
    return window

def display_image(window: tk.Tk, label: tk.Label, image: Image.Image):
    tk_image = ImageTk.PhotoImage(image)
    label.config(image=tk_image)
    label.image = tk_image  # keep a reference to the image
    window.update()

def decode_image(b64_image: str) -> Image.Image:
    image_data = base64.b64decode(b64_image)
    image = Image.open(io.BytesIO(image_data))
    return image.resize((512, 512))

def blend_images(image1: Optional[Image.Image], image2: Image.Image) -> Image.Image:
    if image1 is None:
        return image2
    return Image.blend(image1, image2, alpha=0.5)

def run_gui(output_folder: str):
    window = create_window()
    label = tk.Label(window)
    label.pack()

    def update_gui():
        asyncio.run(main(output_folder, window, label))

    threading.Thread(target=update_gui).start()
    window.mainloop()

async def submit_post(session: ClientSession, url: str, data: dict):
    try:
        async with session.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'}) as response:
            return await response.json()
    except Exception as e:
        logging.error(f"Failed to submit POST request: {e}")
        return None

async def submit_get(session: ClientSession, url: str):
    try:
        async with session.get(url) as response:
            return await response.json()
    except Exception as e:
        logging.error(f"Failed to submit GET request: {e}")
        return None

async def main(output_folder: str, window: tk.Tk, label: tk.Label):
    txt2img_url = 'http://0.0.0.0:7861/sdapi/v1/txt2img'
    data = {
        'prompt': 'a dog wearing a hat',
        'steps': 50
        }

    window = create_window()
    label = tk.Label(window)
    label.pack()

    async with ClientSession() as session:
        txt2img_task = asyncio.create_task(submit_post(session, txt2img_url, data))
        logging.info("txt2img going on")

        progressapi_url = 'http://0.0.0.0:7861/sdapi/v1/progress'

        last_image = None

        while not txt2img_task.done():
            logging.info("progress going on")
            progress_response = await submit_get(session, progressapi_url)

            if progress_response is None:
                continue

            progress_response_copy = dict(progress_response)
            if 'current_image' in progress_response_copy:
                del progress_response_copy['current_image']
            logging.info(progress_response_copy)

            if 'current_image' in progress_response and progress_response['current_image']:
                image = decode_image(progress_response['current_image'])
                image = blend_images(last_image, image)
                image = image.filter(ImageFilter.BLUR)
                display_image(window, label, image)
                last_image = image

            await asyncio.sleep(1)

        await asyncio.sleep(5)

        response = await txt2img_task

        if response is None:
            logging.error("Failed to get final image")
            return

        if 'images' in response and response['images']:
            final_image = decode_image(response['images'][0])
            final_image.save(os.path.join(output_folder, 'dog.png'))
            display_image(window, label, final_image)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output_folder', help='The folder to save the final image')
    args = parser.parse_args()

    run_gui(args.output_folder)