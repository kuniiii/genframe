import argparse
import cv2
from PIL import Image, ImageFilter
import io
import zmq
import base64
from queue import Queue
from threading import Thread

class Application:
    def __init__(self, fullscreen=False):
        self.fullscreen = fullscreen

        self.imgtk = None  # Store the current PhotoImage
        self.prev_img = None  # Store the previous image
        self.window_destroyed = False  # Flag to check if window is destroyed

        if self.fullscreen:
            cv2.namedWindow('Image', cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty('Image', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        self.image_queue = Queue()
        self.thread = Thread(target=self.receive_images)
        self.thread.start()

        self.process_images()

    def receive_images(self):
        print("Entering receive_images function...")
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:5556")  # Connect to the new port

        socket.setsockopt(zmq.SUBSCRIBE, b"client1")

        while not self.window_destroyed:
            image_data = socket.recv_multipart()

            # Extract the image data from the message
            image_base64 = image_data[1]
            messages_type = image_data[2].decode('utf-8')
            print(f"Message received: {messages_type}")

            # Decode the base64 image string to bytes
            image_bytes = base64.b64decode(image_base64)

            # Create a PIL Image from the bytes
            image = Image.open(io.BytesIO(image_bytes))

            # Resize the image to fill the window
            image = image.resize((1024, 1024), Image.ANTIALIAS)

            # If a previous image exists, blend the current and previous image
            if self.prev_img and messages_type == 'progress':
                image = Image.blend(self.prev_img, image, alpha=0.5)
                image = image.filter(ImageFilter.GaussianBlur(25))

            self.prev_img = image  # Store the current image for the next iteration

            self.image_queue.put(image)

    def process_images(self):
        while not self.window_destroyed:
            try:
                image = self.image_queue.get_nowait()
            except:
                image = None
            if image is not None:
                # Display the image with OpenCV
                cv2.imshow('Image', cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR))

            if cv2.waitKey(1) & 0xFF == 27:  # Escape key
                self.window_destroyed = True
                cv2.destroyAllWindows()
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Runs the Application in fullscreen if --fullscreen argument is passed.')
    parser.add_argument('--fullscreen', action='store_true', help='Runs the application in fullscreen.')

    args = parser.parse_args()

    app = Application(fullscreen=args.fullscreen)