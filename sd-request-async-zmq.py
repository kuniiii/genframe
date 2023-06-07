import tkinter as tk
from PIL import Image, ImageTk
import io
import zmq
import asyncio
import numpy as np

def nparray_to_photoimage(arr):
    img = Image.fromarray(arr)
    imgtk = ImageTk.PhotoImage(image=img)
    return imgtk

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()

        self.label = tk.Label(self, text="Waiting for images...", width=512, height=512)
        self.label.pack()

        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.receive_images())

    async def receive_images(self):
        print("Entering receive_images function...")
        context = zmq.asyncio.Context()
        pull = context.socket(zmq.PUSH)
        pull.connect("tcp://localhost:5554")

        while True:
            image_data = await pull.recv()
            print(f"Image received")

            arr = np.frombuffer(image_data, dtype=np.uint8).reshape(512, 512, 4)
            imgtk = nparray_to_photoimage(arr)

            self.label.config(image=imgtk)
            self.label.image = imgtk

            await asyncio.sleep(1)

root = tk.Tk()
app = Application(master=root)
app.mainloop()