"""Desktop Chat Overlay — always-on-top live YouTube chat display.

Shows user avatars, names, and messages in a translucent overlay window
that stays on top of all other windows. Uses YouTube Data API v3.

Usage:
    python chat_overlay.py VIDEO_ID
    python chat_overlay.py VIDEO_ID --key YOUR_API_KEY
"""
import sys
import os
import re
import json
import threading
import time
import io
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError

try:
    import tkinter as tk
    from tkinter import font as tkfont
except ImportError:
    print("tkinter not available")
    sys.exit(1)

try:
    from PIL import Image, ImageTk, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

API_BASE = 'https://www.googleapis.com/youtube/v3'
MAX_MESSAGES = 25
OVERLAY_WIDTH = 380
OVERLAY_HEIGHT = 700
BG_COLOR = '#0d0d0d'
ACCENT = '#00f0ff'
TEXT_COLOR = '#eeeeee'
AUTHOR_COLOR = '#00f0ff'


def get_api_key():
    for path in [r'C:\youtube_api_key.txt', 'youtube_api_key.txt']:
        try:
            with open(path) as f:
                k = f.read().strip()
                if k:
                    return k
        except FileNotFoundError:
            pass
    return os.environ.get('YOUTUBE_API_KEY', '')


def api_get(endpoint, params, api_key):
    params['key'] = api_key
    url = f'{API_BASE}/{endpoint}?{urlencode(params)}'
    req = Request(url, headers={'Accept': 'application/json'})
    resp = urlopen(req, timeout=10)
    return json.loads(resp.read())


def extract_video_id(url):
    for p in [r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})', r'(?:/live/)([a-zA-Z0-9_-]{11})']:
        m = re.search(p, url)
        if m:
            return m.group(1)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    return url


def load_avatar(url, size=32):
    if not HAS_PIL or not url:
        return None
    try:
        data = urlopen(url, timeout=5).read()
        img = Image.open(io.BytesIO(data)).resize((size, size), Image.LANCZOS)
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        img.putalpha(mask)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


class ChatOverlay:
    def __init__(self, video_id, api_key):
        self.video_id = video_id
        self.api_key = api_key
        self.chat_id = None
        self.page_token = None
        self.seen = set()
        self.avatar_cache = {}
        self.messages = []
        self.running = True

        self.root = tk.Tk()
        self.root.title('Live Chat')
        self.root.geometry(f'{OVERLAY_WIDTH}x{OVERLAY_HEIGHT}+20+100')
        self.root.configure(bg=BG_COLOR)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.92)
        self.root.resizable(True, True)
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

        # Try to remove title bar on Windows
        try:
            self.root.overrideredirect(False)
        except Exception:
            pass

        # Header
        header = tk.Frame(self.root, bg='#111118', height=40)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(header, text='LIVE CHAT', font=('Segoe UI', 12, 'bold'),
                 fg=ACCENT, bg='#111118').pack(side='left', padx=12, pady=8)
        self.status_label = tk.Label(header, text='Connecting...',
                                     font=('Segoe UI', 9), fg='#666', bg='#111118')
        self.status_label.pack(side='right', padx=12)

        # Separator
        tk.Frame(self.root, bg=ACCENT, height=2).pack(fill='x')

        # Chat area
        self.chat_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.chat_frame.pack(fill='both', expand=True, padx=6, pady=6)

        self.canvas = tk.Canvas(self.chat_frame, bg=BG_COLOR, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.chat_frame, orient='vertical', command=self.canvas.yview)
        self.msg_frame = tk.Frame(self.canvas, bg=BG_COLOR)

        self.msg_frame.bind('<Configure>',
                           lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.create_window((0, 0), window=self.msg_frame, anchor='nw',
                                  width=OVERLAY_WIDTH - 30)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')

        # Start chat polling in background
        self.poll_thread = threading.Thread(target=self.poll_loop, daemon=True)
        self.poll_thread.start()

        self.root.mainloop()

    def on_close(self):
        self.running = False
        self.root.destroy()

    def poll_loop(self):
        # Get live chat ID
        try:
            data = api_get('videos', {'part': 'liveStreamingDetails', 'id': self.video_id}, self.api_key)
            items = data.get('items', [])
            if items:
                self.chat_id = items[0].get('liveStreamingDetails', {}).get('activeLiveChatId')
            if not self.chat_id:
                self.root.after(0, lambda: self.status_label.config(text='No live chat found', fg='#ff3e3e'))
                return
            self.root.after(0, lambda: self.status_label.config(text='Connected', fg='#4ade80'))
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f'Error: {e}', fg='#ff3e3e'))
            return

        # Poll loop
        while self.running:
            try:
                params = {'part': 'snippet,authorDetails', 'liveChatId': self.chat_id, 'maxResults': 50}
                if self.page_token:
                    params['pageToken'] = self.page_token
                data = api_get('liveChat/messages', params, self.api_key)
                self.page_token = data.get('nextPageToken')
                interval = data.get('pollingIntervalMillis', 3000) / 1000.0

                for item in data.get('items', []):
                    msg_id = item.get('id', '')
                    if msg_id in self.seen:
                        continue
                    self.seen.add(msg_id)
                    if len(self.seen) > 3000:
                        self.seen = set(list(self.seen)[-1500:])

                    snippet = item.get('snippet', {})
                    author_details = item.get('authorDetails', {})
                    if snippet.get('type') != 'textMessageEvent':
                        continue

                    author = author_details.get('displayName', 'Viewer')
                    avatar_url = author_details.get('profileImageUrl', '')
                    text = snippet.get('textMessageDetails', {}).get('messageText', '')
                    if text:
                        self.root.after(0, lambda a=author, av=avatar_url, t=text: self.add_message(a, av, t))

                time.sleep(interval)
            except Exception:
                time.sleep(5)

    def add_message(self, author, avatar_url, text):
        row = tk.Frame(self.msg_frame, bg='#161622', bd=0, highlightthickness=1,
                       highlightbackground='#1a1a30')
        row.pack(fill='x', pady=3, padx=2)

        # Avatar
        left = tk.Frame(row, bg='#161622', width=40)
        left.pack(side='left', padx=(6, 4), pady=6)
        left.pack_propagate(False)

        if avatar_url and avatar_url not in self.avatar_cache:
            def load_av(url=avatar_url, frame=left):
                img = load_avatar(url, 32)
                if img:
                    self.avatar_cache[url] = img
                    self.root.after(0, lambda: self._set_avatar(frame, img))
            threading.Thread(target=load_av, daemon=True).start()
        elif avatar_url in self.avatar_cache:
            self._set_avatar(left, self.avatar_cache[avatar_url])

        # Text
        right = tk.Frame(row, bg='#161622')
        right.pack(side='left', fill='x', expand=True, padx=(0, 8), pady=6)

        tk.Label(right, text=author, font=('Segoe UI', 10, 'bold'),
                 fg=AUTHOR_COLOR, bg='#161622', anchor='w').pack(fill='x')
        tk.Label(right, text=text, font=('Segoe UI', 10),
                 fg=TEXT_COLOR, bg='#161622', anchor='w', wraplength=280,
                 justify='left').pack(fill='x')

        # Remove old messages
        children = self.msg_frame.winfo_children()
        while len(children) > MAX_MESSAGES:
            children[0].destroy()
            children = self.msg_frame.winfo_children()

        # Auto-scroll to bottom
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def _set_avatar(self, frame, img):
        lbl = tk.Label(frame, image=img, bg='#161622', bd=0)
        lbl.image = img
        lbl.pack()


def main():
    if len(sys.argv) < 2:
        print('Usage: python chat_overlay.py <video-id-or-url> [--key API_KEY]')
        sys.exit(1)

    video_id = extract_video_id(sys.argv[1])

    api_key = ''
    if '--key' in sys.argv:
        idx = sys.argv.index('--key')
        if idx + 1 < len(sys.argv):
            api_key = sys.argv[idx + 1]

    if not api_key:
        api_key = get_api_key()

    if not api_key:
        print('No API key found. Use --key or set YOUTUBE_API_KEY env var')
        sys.exit(1)

    print(f'Starting chat overlay for video: {video_id}')
    ChatOverlay(video_id, api_key)


if __name__ == '__main__':
    main()
