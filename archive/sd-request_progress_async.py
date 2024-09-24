import json
import base64
import asyncio
from aiohttp import ClientSession
from PIL import Image
import io
import os

def save_encoded_image(b64_image: str, output_path: str):
    """
    Save the given image to the given output path.
    """

    # Decode the base64 image
    image_data = base64.b64decode(b64_image)
    image = Image.open(io.BytesIO(image_data))

    # Resize the image
    resized_image = image.resize((512, 512))

    # Save the image as a .tmp file first
    temp_path = output_path + ".temp"
    resized_image.save(temp_path, format='PNG')

    # Rename the .tmp file to the desired output path
    os.rename(temp_path, output_path)

async def submit_post(session: ClientSession, url: str, data: dict):
    """
    Submit a POST request to the given URL with the given data.
    """
    async with session.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'}) as response:
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
        'prompt': 'portrait of a cat with a hat, masterful oilpainting on canvas',
        'negative_prompt': 'deformed, ugly, tiling, poorly drawn hands, poorly drawn feet, poorly drawn face, out of frame, extra limbs',
        'steps': '10',
        #'width': '384',
        #'height': '512',
        'enable_hr': 'true',
        'denoising_strength': '0.7',
        'firstphase_width': '384',
        'firstphase_height': '512',
        'hr_scale': '2',
        'hr_upscaler': 'ESRGAN_4x',
        'hr_resize_x': '768',
        'hr_resize_y': '1024',
        'sampler_name': 'Euler',
        'save_images': 'true'
        # 'alwayson_scripts': {
        #     'controlnet': {
        #         'args': [
        #             {
        #                 'input_image': base64_controlnet_input_image,
        #                 'model': 'control_v11p_sd15_openpose [cab727d4]'
        #             }
        #         ]
        #     }
        # }
        }
    async with ClientSession() as session:
        # Submit txt2img post request
        txt2img_task = asyncio.create_task(submit_post(session, txt2img_url, data))
        print("txt2img going on")

        progressapi_url = 'http://0.0.0.0:7861/sdapi/v1/progress'

        # Initialize the counter for the image steps
        step_counter = 1

        # Check progress while waiting for txt2img response
        while not txt2img_task.done():
            print("progress going on")
            progress_response = await submit_get(session, progressapi_url)

            progress_response_copy = dict(progress_response)
            if 'current_image' in progress_response_copy:
                del progress_response_copy['current_image']
            print(progress_response_copy)

            if 'current_image' in progress_response and progress_response['current_image']:
                save_encoded_image(progress_response['current_image'], f'dog_progress_{step_counter}.png')
                step_counter += 1

            await asyncio.sleep(1)  # Avoid overloading the server, adjust sleep time as needed

        # Wait for a little more to make sure no more progress images are coming
        await asyncio.sleep(5)

        # Save the final image once txt2img process is done and no more progress images are coming
        response = await txt2img_task

        if 'images' in response and response['images']:
            save_encoded_image(response['images'][0], 'dog.png')

if __name__ == '__main__':
    asyncio.run(main())