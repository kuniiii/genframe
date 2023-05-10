import sys
from pathlib import Path
from flask import Flask, send_file, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Latest PNG Viewer</title>
    <style>
        .image-container {
            width: 100%;
            text-align: center;
        }
        img {
            max-width: 100%;
        }
    </style>
</head>
<body>
    <div class="image-container">
        <img id="latest-png" src="{{ url_for('serve_latest_png') }}" alt="Latest PNG">
    </div>

    <script>
        function refreshImage() {
            var latestPng = document.getElementById('latest-png');
            latestPng.src = latestPng.src.split('?')[0] + '?' + new Date().getTime();
        }

        setInterval(refreshImage, 5000);  // Refresh the image every 5 seconds
    </script>
</body>
</html>
"""

folder_path = None

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/latest.png")
def serve_latest_png():
    png_files = list(folder_path.glob("*.png"))
    latest_png = max(png_files, key=lambda p: p.stat().st_mtime)
    return send_file(str(latest_png), mimetype="image/png")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <folder_path>")
        sys.exit(1)

    folder_path = Path(sys.argv[1])

    if not folder_path.is_dir():
        print(f"Folder not found: {folder_path}")
        sys.exit(1)

    app.run(host="0.0.0.0", port=4000)
