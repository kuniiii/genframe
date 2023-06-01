import os
import sys
from pathlib import Path
from tkinter import Tk, Label
import tkinter.font as tkFont
from PIL import Image, ImageTk
from PIL import UnidentifiedImageError
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

import time

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
    print(f"New image detected: {event.dest_path}")
    if event.dest_path.lower().endswith(".png"):
        # Wait until the file size is non-zero
        while os.path.getsize(event.dest_path) == 0:
            time.sleep(1)  # wait for 0.1 seconds

        # Verify the image
        with open(event.dest_path, 'rb') as f:
            img = Image.open(f)
            try:
                img.verify()
            except (IOError, SyntaxError) as e:
                print(f'Bad file, skipping: {event.dest_path}, error: {e}')
                return

        # Open the image
        new_image = Image.open(event.dest_path)
        # new_image.thumbnail((root.winfo_screenwidth(), root.winfo_screenheight()))
        new_image.thumbnail((root.winfo_screenwidth(), root.winfo_screenheight() * 0.9))  # Adjust for 90% of screen height

        # Morphing effect
        num_steps = 10
        for i in range(1, num_steps + 1):
            alpha = i / num_steps
            morphed_image = Image.blend(current_image, new_image, alpha)
            show_image(morphed_image, event.dest_path)
            root.update()

        current_image = new_image

class PNGPatternMatchingEventHandler(PatternMatchingEventHandler):
    patterns = ["*.png"]

    def on_moved(self, event):
        print(f"File moved: {event.src_path} -> {event.dest_path}")
        if event.dest_path.lower().endswith(".png"):
            on_new_image(event)
            
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <folder_path>")
        sys.exit(1)

    folder_path = Path(sys.argv[1])

    if not folder_path.is_dir():
        print(f"Folder not found: {folder_path}")
        sys.exit(1)

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
    event_handler = PNGPatternMatchingEventHandler()
    observer.schedule(event_handler, str(folder_path), recursive=False)
    observer.start()

    root.mainloop()

    observer.stop()
    observer.join()