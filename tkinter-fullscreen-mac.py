import os
import sys
from pathlib import Path
from tkinter import Tk, Label
import tkinter.font as tkFont
from PIL import Image, ImageTk, ImageFilter
from PIL import UnidentifiedImageError
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler, FileSystemEventHandler

import time
import platform

def get_latest_png(folder_path):
    png_files = list(folder_path.glob("*.png"))
    if png_files:
        latest_png = max(png_files, key=lambda p: p.stat().st_mtime)
        return latest_png
    else:  #No png files found
        return None

def show_image(image, filename):
    global photo
    photo = ImageTk.PhotoImage(image)
    label.config(image=photo)
    label.image = photo

    # Display filename underneath the image
    filename_label.config(text=filename)

def on_new_image(event):
    global current_image
    print(f"New image detected: {event.src_path if is_linux else event.dest_path}")
    if (event.src_path if is_linux else event.dest_path).lower().endswith(".png"):
        image_path = event.src_path if is_linux else event.dest_path
        # Wait until the file size is non-zero
        while os.path.getsize(image_path) == 0:
            time.sleep(1)  # wait for 0.1 seconds

        # Verify the image
        with open(image_path, 'rb') as f:
            img = Image.open(f)
            try:
                img.verify()
            except (IOError, SyntaxError) as e:
                print(f'Bad file, skipping: {image_path}, error: {e}')
                return

        # Open the image
        new_image = Image.open(image_path)
        new_image.thumbnail((root.winfo_screenwidth(), root.winfo_screenheight() * 0.9))  # Adjust for 90% of screen height

        # Morphing effect
        num_steps = 10
        max_radius = 25  # Maximum blur radius
        min_radius = 0  # Minimum blur radius
        for i in range(1, num_steps + 1):
            alpha = i / num_steps
            morphed_image = Image.blend(current_image, new_image, alpha)

            # Calculate blur radius for this step
            radius = max_radius - ((max_radius - min_radius) * (i / num_steps))
            morphed_image = morphed_image.filter(ImageFilter.GaussianBlur(radius=radius))

            show_image(morphed_image, image_path)
            root.update()

        # Display the original, unblurred image
        show_image(new_image, image_path)
        current_image = new_image

class PNGPatternMatchingEventHandler(PatternMatchingEventHandler):
    patterns = ["*.png"]

    def on_moved(self, event):
        print(f"File moved: {event.src_path} -> {event.dest_path}")
        if event.dest_path.lower().endswith(".png"):
            on_new_image(event)

class LinuxFileSystemEventHandler(FileSystemEventHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_event_time = None

    def should_handle(self, event):
        now = time.time()
        if self.last_event_time is not None and now - self.last_event_time < 1:  # If less than 1 second has passed
            return False  # Ignore this event

        self.last_event_time = now
        return True

    def on_modified(self, event):
        if not self.should_handle(event):
            return

        print(f"File modified: {event.src_path}")
        if event.src_path.lower().endswith(".png"):
            on_new_image(event)
        elif event.src_path.lower().endswith(".temp"):
            png_file = event.src_path.rsplit('.', 1)[0] + '.png'
            if os.path.exists(png_file):
                new_event = type('new_event', (object,), {'src_path': png_file})
                on_new_image(new_event)

    def on_deleted(self, event):
        if not self.should_handle(event):
            return

        print(f"File deleted: {event.src_path}")
        if event.src_path.lower().endswith(".temp"):
            png_file = event.src_path.rsplit('.', 1)[0] + '.png'
            if os.path.exists(png_file):
                new_event = type('new_event', (object,), {'src_path': png_file})
                on_new_image(new_event)

    def on_created(self, event):
        if not self.should_handle(event):
            return

        print(f"File created: {event.src_path}")
        if event.src_path.lower().endswith(".png"):
            time.sleep(0.5)  # wait for the write operation to finish
            on_new_image(event)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <folder_path>")
        sys.exit(1)

    folder_path = Path(sys.argv[1])

    if not folder_path.is_dir():
        print(f"Folder not found: {folder_path}")
        sys.exit(1)

    is_linux = platform.system() == 'Linux'

    root = Tk()
    root.attributes("-fullscreen", True)
    root.bind("<Escape>", lambda event: root.destroy())
    root.configure(bg="black")

    roboto_font = tkFont.Font(family="Roboto", size=14)  # Use Roboto font size 8
    label = Label(root, bg="black")
    label.pack(expand=True, anchor="center")
    filename_label = Label(root, bg="black", fg="white", font=roboto_font)  # Label for displaying filename
    filename_label.pack(expand=True, anchor="center")

    latest_png = get_latest_png(folder_path)
    if latest_png: # If a png file was found
        current_image = Image.open(latest_png)
        current_image.thumbnail((root.winfo_screenwidth(), root.winfo_screenheight() * 0.9))  # Adjust for 90% of screen height
        show_image(current_image, str(latest_png))
    else: # No png file was found, so create an empty image
        width, height = root.winfo_screenwidth(), int(root.winfo_screenheight() * 0.9)
        current_image = Image.new('RGBA', (width, height), 'black')  # Create a new black image
        show_image(current_image, "No images found")

    observer = Observer()
    event_handler = LinuxFileSystemEventHandler() if is_linux else PNGPatternMatchingEventHandler()
    observer.schedule(event_handler, str(folder_path), recursive=False)
    observer.start()

    root.mainloop()

    observer.stop()
    observer.join()