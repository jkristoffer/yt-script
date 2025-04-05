import os
import yt_dlp
import tempfile
import json
import os

SECRET_TOKEN = os.environ.get("API_SECRET")
def get_transcript(video_url):
    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'outtmpl': os.path.join(tmpdir, '%(id)s.%(ext)s')
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            ydl.download([video_url])
            video_id = info['id']
            vtt_path = os.path.join(tmpdir, f'{video_id}.en.vtt')

            if not os.path.exists(vtt_path):
                return None

            with open(vtt_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            text_lines = [
                line.strip() for line in lines
                if line.strip() and not line.strip().isdigit() and '-->' not in line
            ]
            return '\n'.join(text_lines)

# Vercel handler
def handler(request, response):
    try:
        if request.method != "POST":
            response.status_code = 405
            response.headers["Content-Type"] = "application/json"
            response.body = json.dumps({"error": "Only POST method is allowed"})
            return response
        
        # 🔒 Auth check
        auth_header = request.headers.get("authorization")
        if not auth_header or auth_header != f"Bearer {SECRET_TOKEN}":
            response.status_code = 401
            response.body = '{"error": "Unauthorized"}'
            return response

        # ✅ Proceed as normal...
        body = json.loads(request.body)
        video_url = body.get("url")

        if not video_url:
            response.status_code = 400
            response.headers["Content-Type"] = "application/json"
            response.body = json.dumps({"error": "Missing 'url' in request body"})
            return response

        transcript = get_transcript(video_url)
        if not transcript:
            response.status_code = 404
            response.headers["Content-Type"] = "application/json"
            response.body = json.dumps({"error": "Transcript not found"})
            return response

        response.status_code = 200
        response.headers["Content-Type"] = "application/json"
        response.body = json.dumps({"transcript": transcript})
        return response

    except Exception as e:
        response.status_code = 500
        response.headers["Content-Type"] = "application/json"
        response.body = json.dumps({"error": str(e)})
        return response