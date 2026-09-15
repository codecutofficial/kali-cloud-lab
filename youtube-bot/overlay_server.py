"""Local server for OBS overlay — injects API key and video ID automatically.

Reads YOUTUBE_API_KEY from env var or C:\youtube_api_key.txt.
Serves the overlay HTML on http://localhost:4455/overlay

Usage:
    python overlay_server.py VIDEO_ID
    python overlay_server.py VIDEO_ID --port 4455

Then add a Browser Source in OBS pointing to:
    http://localhost:4455/overlay
"""
import sys
import os
import re
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

HOST = '127.0.0.1'
DEFAULT_PORT = 4455


def get_api_key():
    key = os.environ.get('YOUTUBE_API_KEY', '').strip()
    if key:
        return key
    for path in [r'C:\youtube_api_key.txt', 'youtube_api_key.txt']:
        try:
            with open(path) as f:
                k = f.read().strip()
                if k:
                    return k
        except FileNotFoundError:
            pass
    return ''


def extract_video_id(url):
    for p in [r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})', r'(?:/live/)([a-zA-Z0-9_-]{11})']:
        m = re.search(p, url)
        if m:
            return m.group(1)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    return url


class OverlayHandler(SimpleHTTPRequestHandler):
    api_key = ''
    video_id = ''
    overlay_html = ''

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path in ('/', '/overlay', '/overlay.html'):
            html = self.overlay_html
            # Inject API key and video ID into the HTML
            html = html.replace(
                "const API_KEY = params.get('key') || '';",
                f"const API_KEY = params.get('key') || '{self.api_key}';"
            )
            html = html.replace(
                "const VIDEO_ID = params.get('video') || '';",
                f"const VIDEO_ID = params.get('video') || '{self.video_id}';"
            )
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            return

        if parsed.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'ok')
            return

        self.send_error(404)

    def log_message(self, format, *args):
        pass  # Silence request logs


def main():
    if len(sys.argv) < 2:
        print('Usage: python overlay_server.py <video-id-or-url> [--port PORT]')
        sys.exit(1)

    video_id = extract_video_id(sys.argv[1])
    api_key = get_api_key()

    port = DEFAULT_PORT
    if '--port' in sys.argv:
        idx = sys.argv.index('--port')
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])

    if not api_key:
        print('WARNING: No YouTube API key found.')
        print('Set YOUTUBE_API_KEY env var or put it in C:\\youtube_api_key.txt')

    # Load overlay HTML
    overlay_path = None
    for p in [
        os.path.join(os.path.dirname(__file__), '..', 'obs-overlay', 'overlay.html'),
        os.path.join(os.path.dirname(__file__), 'overlay.html'),
        r'C:\obs-overlay\overlay.html',
        os.path.join(os.environ.get('USERPROFILE', ''), 'youtube-bot', 'overlay.html'),
    ]:
        if os.path.exists(p):
            overlay_path = p
            break

    if not overlay_path:
        # Download from GitHub
        print('Overlay HTML not found locally, downloading...')
        import urllib.request
        url = 'https://raw.githubusercontent.com/codecutofficial/kali-cloud-lab/main/obs-overlay/overlay.html'
        try:
            resp = urllib.request.urlopen(url)
            html = resp.read().decode('utf-8')
        except Exception as e:
            print(f'Failed to download overlay: {e}')
            sys.exit(1)
    else:
        with open(overlay_path, 'r', encoding='utf-8') as f:
            html = f.read()

    OverlayHandler.api_key = api_key
    OverlayHandler.video_id = video_id
    OverlayHandler.overlay_html = html

    server = HTTPServer((HOST, port), OverlayHandler)
    print(f'Overlay server running at http://{HOST}:{port}/overlay')
    print(f'Video ID: {video_id}')
    print(f'API key: {"set" if api_key else "NOT SET"}')
    print()
    print('Add this as a Browser Source in OBS:')
    print(f'  URL: http://localhost:{port}/overlay')
    print(f'  Width: 1920  Height: 1080')
    print()
    print('Press Ctrl+C to stop.')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')
        server.server_close()


if __name__ == '__main__':
    main()
