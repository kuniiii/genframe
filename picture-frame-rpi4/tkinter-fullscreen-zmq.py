import argparse
import tkinter as tk
from PIL import Image, ImageTk, ImageFilter
import io
import zmq
import base64
from queue import Queue
from threading import Thread, Lock
import signal
import sys

def is_base64(sb):
    try:
        if isinstance(sb, str):
            # If there's any unicode here, an exception will be thrown and the function will return false
            sb_bytes = bytes(sb, 'ascii')
        elif isinstance(sb, bytes):
            sb_bytes = sb
        else:
            raise ValueError("Argument must be string or bytes")
        return base64.b64encode(base64.b64decode(sb_bytes)) == sb_bytes
    except Exception:
        return False

class Application(tk.Frame):
    def __init__(self, master=None, fullscreen=False):
        super().__init__(master, bg='black')
        self.master = master
        self.pack(fill=tk.BOTH, expand=True)

        self.fullscreen = fullscreen
        self.label = tk.Label(self, width=1080, height=1920, bg='black', relief='flat', bd=0)
        self.label.pack(expand=True)

        self.imgtk = None  # Store the current PhotoImage
        self.prev_img = None  # Store the previous image
        self.window_destroyed = False  # Flag to check if window is destroyed
        self.window_destroyed_lock = Lock()  # Lock for the window_destroyed flag

        if self.fullscreen:
            self.master.attributes("-fullscreen", True)
            self.master.configure(background='black')
            self.master.bind("<Escape>", self.exit_fullscreen)

        self.image_queue = Queue()
        self.thread = Thread(target=self.receive_images)
        self.thread.start()

        self.process_images()

    # def blend_images(self, img1, img2, steps=10):
    #     for step in range(steps + 1):
    #         alpha = step / steps
    #         blended_image = Image.blend(img1, img2, alpha)
    #         blurred_image = blended_image.filter(ImageFilter.GaussianBlur(15))
    #         self.image_queue.put(blurred_image)

    def blend_images(self, img1, img2, steps=10):
        for step in range(steps + 1):
            alpha = step / steps
            blended_image = Image.blend(img1, img2, alpha)
            self.image_queue.put(blended_image)
        self.prev_img = img2

    def receive_images(self):
        print("Entering receive_images function...")
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:5556")  # Connect to the new port

        socket.setsockopt(zmq.SUBSCRIBE, b"client1")

        while True:
            with self.window_destroyed_lock:
                if self.window_destroyed:
                    break

            image_data = socket.recv_multipart()

            # Extract the image data from the message
            image_base64 = image_data[1]
            messages_type = image_data[2].decode('utf-8')
            print(f"Message received: {messages_type}")

            # Decode the base64 image string to bytes
            if is_base64(image_base64):
                image_bytes = base64.b64decode(image_base64)
            else:
                print("Received string is not a valid base64 string: ", image_base64)
                continue  # Skip to the next loop iteration
            # image_bytes = base64.b64decode(image_base64)

            try:
                # Create a PIL Image from the bytes
                image = Image.open(io.BytesIO(image_bytes))

                # Resize the image to fill the window
                window_width = self.master.winfo_screenwidth() * 0.75  # Get 90% of the screen width
                window_height = self.master.winfo_screenheight() * 0.75  # Get 90% of the screen height
                print("the image size width x height", image.width, image.height)
                image_ratio = image.width / image.height
                window_ratio = window_width / window_height

                if window_ratio >= image_ratio:
                    # If the window is wider than the image, scale to match height
                    height = window_height
                    width = window_height * image_ratio
                else:
                    # If the window is narrower than the image, scale to match width
                    width = window_width
                    height = window_width / image_ratio

                image = image.resize((int(width), int(height)), Image.ANTIALIAS)

                # If a previous image exists, blend the current and previous image
                if self.prev_img and messages_type == 'progress':
                    self.blend_images(self.prev_img, image)
                    # image = image.filter(ImageFilter.GaussianBlur(15))

                self.prev_img = image  # Store the current image for the next iteration

                self.image_queue.put(image)
            except Exception as e:
                print(f"Error occured while processing image")
                continue


    def process_images(self):
        with self.window_destroyed_lock:
            if not self.window_destroyed:
                try:
                    image = self.image_queue.get_nowait()
                except:
                    image = None
                if image is not None:
                     # Mark the previous PhotoImage object for garbage collection
                    self.imgtk = None

                    # Create a Tkinter-compatible image
                    self.imgtk = ImageTk.PhotoImage(image=image)

                    self.label.config(image=self.imgtk)

                    # Update the Tkinter window
                    self.master.update()

                self.after(100, self.process_images)

    def exit_fullscreen(self, event=None):
        with self.window_destroyed_lock:
            self.window_destroyed = True
        self.master.destroy()

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    cleanup()
    sys.exit(0)

def cleanup():
    try:
        root.destroy()
    except:
        pass

    try:
        app.destroy()
    except:
        pass

    try:
        context.destroy()
    except:
        pass

    print("Cleaned up, exiting")

    # with app.window_destroyed_lock:
        # app.window_destroyed = True
    # logging.info("Signal received: %s", sig)
    # socket.close()
    # context.term()
    # sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Runs the Application in fullscreen if --fullscreen argument is passed.')
    parser.add_argument('--fullscreen', action='store_true', help='Runs the application in fullscreen.')

    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    root = tk.Tk()
    app = Application(master=root, fullscreen=args.fullscreen)

    try:
        # Start the Tkinter event loop
        app.mainloop()

    except KeyboardInterrupt:
        print("Keyboard interrupt")
        cleanup()

    except Exception as e:
        print("An error occured: %s", e)

    finally:
        # Wait for the image receiving thread to finish
        app.thread.join()

