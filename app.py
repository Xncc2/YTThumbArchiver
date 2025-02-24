from flask import Flask, render_template_string, request, redirect, url_for
import concurrent.futures
import yt_dlp

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Thumbnails for {{ channel_id }}</title>
    <style>
        .thumbnail-container {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .thumbnail-box {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: center;
        }
        img {
            max-width: 320px;
            height: auto;
            display: block;
        }
    </style>
</head>
<body>
    <h1>Thumbnails for channel: {{ channel_id }}</h1>
    <iframe src="https://www.youtube.com/channel/{{ channel_id }}" width="100%" height="500"></iframe>
    <div class="thumbnail-container">
        {% for video in thumbnails %}
            <div class="thumbnail-box">
                <h3>Video ID: {{ video.video_id }}</h3>
                <strong>Main Thumbnails:</strong><br>
                {% for thumb in video.main %}
                    <img src="{{ thumb }}" onerror="this.style.display='none';" alt="Main Thumbnail">
                {% endfor %}
                <br>
                <strong>Auto Thumbnails:</strong><br>
                {% for thumb in video.auto %}
                    <img src="{{ thumb }}" onerror="this.style.display='none';" alt="Auto Thumbnail">
                {% endfor %}
            </div>
        {% endfor %}
    </div>
</body>
</html>
"""

FORM_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube Thumbnail Fetcher</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
        }
        input[type="text"] {
            padding: 10px;
            width: 300px;
            font-size: 16px;
        }
        input[type="submit"] {
            padding: 10px 20px;
            font-size: 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <h1>YouTube Thumbnail Fetcher</h1>
    <form method="POST" action="/">
        <label for="channel_id">Enter YouTube Channel ID:</label><br><br>
        <input type="text" id="channel_id" name="channel_id" placeholder="e.g., UC_x5XG1OV2P6uZZ5FSM9Ttw" required><br><br>
        <input type="submit" value="Get Thumbnails">
    </form>
</body>
</html>
"""

def get_video_thumbnails(channel_id):
    def extract_video_ids(url):
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=False)
            if 'entries' in result:
                return [video['id'] for video in result['entries']]
            return []

    urls = [
        f'https://www.youtube.com/channel/{channel_id}/videos',
        f'https://www.youtube.com/channel/{channel_id}/shorts'
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_to_url = {executor.submit(extract_video_ids, url): url for url in urls}
        video_ids = []
        for future in concurrent.futures.as_completed(future_to_url):
            video_ids.extend(future.result())

    thumbnails = []
    for video_id in video_ids:
        thumbnails.append({
            "video_id": video_id,
            "main": [
                f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
                f'https://img.youtube.com/vi/{video_id}/hq720.jpg',
                f'https://img.youtube.com/vi/{video_id}/sddefault.jpg'
            ],
            "auto": [
                f'https://img.youtube.com/vi/{video_id}/hq1.jpg',
                f'https://img.youtube.com/vi/{video_id}/hq2.jpg',
                f'https://img.youtube.com/vi/{video_id}/hq3.jpg',
                f'https://img.youtube.com/vi/{video_id}/sd1.jpg',
                f'https://img.youtube.com/vi/{video_id}/sd2.jpg',
                f'https://img.youtube.com/vi/{video_id}/sd3.jpg',
                f'https://img.youtube.com/vi/{video_id}/mq1.jpg',
                f'https://img.youtube.com/vi/{video_id}/mq2.jpg',
                f'https://img.youtube.com/vi/{video_id}/mq3.jpg'
            ]
        })

    return thumbnails

@app.route("/thumbnails/<channel_id>")
def thumbnails(channel_id):
    thumbnails = get_video_thumbnails(channel_id)
    return render_template_string(HTML_TEMPLATE, channel_id=channel_id, thumbnails=thumbnails)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        channel_id = request.form.get("channel_id")
        if channel_id:
            return redirect(url_for("thumbnails", channel_id=channel_id))
    return render_template_string(FORM_TEMPLATE)

if __name__ == "__main__":
    app.run(debug=True)
