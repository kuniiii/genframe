import json
import asyncio
from aiohttp import ClientSession
import base64
from io import BytesIO
from PIL import Image, ImageTk
import tkinter as tk

class FullscreenApp:
    def __init__(self, master):
        self.master = master
        self.canvas = tk.Canvas(master, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)
        self.master.attributes('-fullscreen', True)
        self.master.bind("<Escape>", lambda e: (e.widget.withdraw(), e.widget.quit()))
        self.previous_image = None
        self.photo_image = None

        self.screen_width = self.master.winfo_screenwidth()
        self.screen_height = self.master.winfo_screenheight()

    def update_image(self, image_data):
        image = Image.open(BytesIO(base64.b64decode(image_data)))
        # Resize image to fit screen while maintaining aspect ratio
        image.thumbnail((self.screen_width, self.screen_height), Image.ANTIALIAS)
        if self.previous_image:
            image = Image.blend(self.previous_image, image, alpha=0.5)
        self.previous_image = image
        self.photo_image = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, image=self.photo_image, anchor='nw')

    def end_fullscreen(self, event=None):
        self.master.quit()

async def submit_post(session: ClientSession, url: str, data: dict):
    async with session.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'}) as response:
        return await response.json()

async def submit_get(session: ClientSession, url: str):
    async with session.get(url) as response:
        return await response.json()

async def main(app):
    txt2img_url = 'http://0.0.0.0:7861/sdapi/v1/txt2img'
    data = {'prompt': 'a dog wearing a hat'}

    async with ClientSession() as session:
        txt2img_task = asyncio.create_task(submit_post(session, txt2img_url, data))
        print("txt2img going on")

        progressapi_url = 'http://0.0.0.0:7861/sdapi/v1/progress'
        while not txt2img_task.done():
            print("progress going on")
            progress_response = await submit_get(session, progressapi_url)
            if 'current_image' in progress_response and progress_response['current_image']:
                app.update_image(progress_response['current_image'])
            await asyncio.sleep(1)

        await asyncio.sleep(5)

        response = await txt2img_task
        if 'images' in response and response['images']:
            app.update_image(response['images'][0])

if __name__ == '__main__':
    root = tk.Tk()
    app = FullscreenApp(root)
    asyncio.run(main(app))
    root.mainloop()
