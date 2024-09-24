import base64
import asyncio
import aiohttp
from aiohttp import web
import websockets
from websockets.exceptions import ConnectionClosedOK
from flask import Flask, render_template

image_path = '/Users/peku/Desktop/KMS3716_mask.png'
# Read the image file as binary data
with open(image_path, 'rb') as file:
    image_data = file.read()

# Encode the image data as base64
black_image_data = base64.b64encode(image_data).decode('utf-8')

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

async def websocket_handler(websocket, path):
    url = 'http://0.0.0.0:7861/sdapi/v1/progress'


    async with aiohttp.ClientSession() as session:
        while True:
            try:
            # Send the black image data to the client
                await websocket.send(black_image_data)

            # try:
            #     async with session.get(url) as response:
            #         data = await response.json()
            #         current_image = data.get('current_image')
            #         if current_image:
            #             await websocket.send(current_image)
            except ConnectionClosedOK:
                break

            await asyncio.sleep(1)

def main():
    loop = asyncio.get_event_loop()

    start_server = websockets.serve(websocket_handler, '0.0.0.0', 4500)

    loop.run_until_complete(start_server)
    loop.run_forever()

if __name__ == '__main__':
    main()
