import json
import asyncio
import gevent
from aiohttp import ClientSession
from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow cross-origin requests

# Asynchronous HTTP POST request
async def submit_post(session: ClientSession, url: str, data: dict):
    async with session.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'}) as response:
        return await response.json()

# Asynchronous HTTP GET request
async def submit_get(session: ClientSession, url: str):
    async with session.get(url) as response:
        return await response.json()

# Main function that runs the asyncio tasks
def main():
    while True:  # Infinite loop to send a new task every 20 seconds
        txt2img_url = 'http://0.0.0.0:7861/sdapi/v1/txt2img'
        data = {'prompt': 'a dog wearing a hat', 'steps': 120}

        with ClientSession() as session:
            txt2img_task = asyncio.create_task(submit_post(session, txt2img_url, data))
            print("txt2img going on")

            progressapi_url = 'http://0.0.0.0:7861/sdapi/v1/progress'

            while not txt2img_task.done():
                print("progress going on")
                progress_response = gevent.spawn(submit_get, progressapi_url).get()
                print("progress response:", progress_response)

                if 'current_image' in progress_response and progress_response['current_image']:
                    print('Emitting image')  # Log the emission event
                    # Emit a WebSocket event with the image data
                    socketio.emit('image_update', {'image_data': progress_response['current_image']})

                gevent.sleep(1)

            gevent.sleep(20)  # Wait 20 seconds before sending a new task

if __name__ == '__main__':
    # Create a gevent server
    http_server = socketio.server
    http_server.event.spawn(main)

    # Run the Flask app with the gevent server
    http_server.serve_forever()
