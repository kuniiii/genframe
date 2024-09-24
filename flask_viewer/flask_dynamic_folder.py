import sys
from pathlib import Path
from flask import Flask, Response, send_file, render_template, abort
from flask_cors import CORS
from PIL import Image
import time
import os
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

app = Flask(__name__)
CORS(app)

folder_path = None
latest_png = None

def on_new_image(event):
    global latest_png
    print(f"New image detected: {event.dest_path}")
    if event.dest_path.lower().endswith(".png"):
        # Wait until the file size is non-zero
        while os.path.getsize(event.dest_path) == 0:
            time.sleep(2)  # wait for 1 seconds

        # Verify the image
        with open(event.dest_path, 'rb') as f:
            img = Image.open(f)
            try:
                img.verify()
                latest_png = Path(event.dest_path).name
                print(f"Latest image set to: {latest_png}")
            except (IOError, SyntaxError) as e:
                print(f'Bad file, skipping: {event.dest_path}, error: {e}')

class PNGPatternMatchingEventHandler(PatternMatchingEventHandler):
    patterns = ["*.png"]

    def on_moved(self, event):
        print(f"File moved: {event.src_path} -> {event.dest_path}")
        if event.dest_path.lower().endswith(".png"):
            on_new_image(event)

@app.route('/stream')
def stream():
    def event_stream():
        while True:
            print("in true")
            if latest_png:
                print("sending latest_png")
                yield f'data: {str(latest_png)}\n\n'  # Send the latest PNG path
            else:
                print("else no file")
                yield 'data: no file\n\n'
            time.sleep(1)  # Wait a second before sending the next event

    return Response(event_stream(), mimetype='text/event-stream')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/latest.png")
def serve_latest_png():
    if not latest_png:
        return abort(404)  # No PNG files found
    try:
        # Combine the folder path with the filename before serving
        img_path = str(folder_path / latest_png)
        print(f"Attempting to serve: {img_path}")
        return send_file(img_path, mimetype="image/png")
    except Exception as e:
        print(f"Error while serving image: {e}")
        return abort(500)  # Internal server error

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <folder_path>")
        sys.exit(1)

    folder_path = Path(sys.argv[1])

    if not folder_path.is_dir():
        print(f"Folder not found: {folder_path}")
        sys.exit(1)

    observer = Observer()
    event_handler = PNGPatternMatchingEventHandler()
    observer.schedule(event_handler, str(folder_path), recursive=False)
   
    observer.start()

    app.run(host="0.0.0.0", port=4000)
