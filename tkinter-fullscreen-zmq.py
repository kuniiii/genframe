import tkinter as tk
from PIL import Image, ImageTk
import io
import zmq
import base64

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()

        self.label = tk.Label(self, width=1024, height=1024)
        self.label.pack()

        self.imgtk = None  # Store the current PhotoImage

        self.receive_images()

    def receive_images(self):
        print("Entering receive_images function...")
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:5556")  # Connect to the new port

        socket.setsockopt(zmq.SUBSCRIBE, b"client1")

        while True:
            image_data = socket.recv_multipart()
            print("Message received")

            # Extract the image data from the message
            image_base64 = image_data[1]

            # Decode the base64 image string to bytes
            image_bytes = base64.b64decode(image_base64)

            # Create a PIL Image from the bytes
            image = Image.open(io.BytesIO(image_bytes))

            # Resize the image to fit the window
            resized_image = image.resize((1024, 1024))

            # Create a Tkinter-compatible image
            self.imgtk = ImageTk.PhotoImage(image=resized_image)

            self.label.config(image=self.imgtk)

            # Update the Tkinter window
            self.master.update()

root = tk.Tk()
app = Application(master=root)

# Start the Tkinter event loop
app.mainloop()