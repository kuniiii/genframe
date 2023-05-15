import sys
import time
from pathlib import Path
from PIL import Image, ImageTk
from tkinter import Tk, Canvas
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FullScreenApp:
    def __init__(self, image, master=None):
        self.master = master
        self.master.attributes("-fullscreen", True)
        self.master.bind("<Escape>", self.close)

        self.canvas = Canvas(self.master, width=self.master.winfo_screenwidth(), height=self.master.winfo_screenheight(), bg="black")
        self.canvas.pack(fill="both", expand=True)

        self.update_image(image)

    def update_image(self, image):
        self.image = ImageTk.PhotoImage(image)
        self.image_label = self.canvas.create_image(self.master.winfo_screenwidth() // 2, self.master.winfo_screenheight() // 2, image=self.image)

    def morph_images(self, old_image, new_image, steps=20, delay=25):
        for step in range(1, steps + 1):
            alpha = step / steps
            blended_image = Image.blend(old_image, new_image, alpha)
            self.update_image(blended_image)
            self.master.update()
            time.sleep(delay / 1000)

    def close(self, event):
        self.master.destroy()

class FolderMonitor(FileSystemEventHandler):
    def __init__(self, app, folder_path):
        self.app = app
        self.folder_path = folder_path

    def on_created(self, event):
        if event.src_path.lower().endswith('.png'):
            image_path = Path(event.src_path)
            if image_path.is_file():
                new_image = Image.open(image_path)
                old_image = self.app.image._PhotoImage__photo.image
                self.app.morph_images(old_image, new_image)

def main(folder_path):
    last_updated_png = sorted(folder_path.glob('*.png'), key=lambda p: p.stat().st_mtime, reverse=True)[0]
    image = Image.open(last_updated_png)

    root = Tk()
    app = FullScreenApp(image, master=root)

    event_handler = FolderMonitor(app, folder_path)
    observer = Observer()
    observer.schedule(event_handler, str(folder_path), recursive=False)
    observer.start()

    try:
        root.mainloop()
    finally:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <folder_path>")
        sys.exit(1)

    folder_path = Path(sys.argv[1])

    if not folder_path.is_dir():
        print(f"Folder not found: {folder_path}")
        sys.exit(1)

    main(folder_path)