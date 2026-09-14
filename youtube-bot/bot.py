"""YouTube Live Chat → Game Controller bot.

Uses the official YouTube Data API v3 to read live chat messages
and translate commands into keyboard/mouse input.

Usage:
    python bot.py VIDEO_ID
    python bot.py https://www.youtube.com/watch?v=VIDEO_ID

Requires YOUTUBE_API_KEY environment variable or C:\youtube_api_key.txt
"""
import sys
import re
import json
import time
import urllib.request
import urllib.error
import urllib.parse
from collections import defaultdict
from commands import parse_and_execute
import tts

GLOBAL_COOLDOWN = 1.5
PER_USER_COOLDOWN = 2.0

last_global = 0.0
user_cooldowns: dict[str, float] = defaultdict(float)

API_BASE = 'https://www.googleapis.com/youtube/v3'


def get_api_key() -> str:
    """Read YouTube API key from env var or file."""
    import os
    key = os.environ.get('YOUTUBE_API_KEY', '').strip()
    if key:
        return key
    for path in [r'C:\youtube_api_key.txt', r'C:\credentials\youtube_api_key.txt']:
        try:
            with open(path, 'r') as f:
                key = f.read().strip()
                if key:
                    return key
        except FileNotFoundError:
            pass
    print('ERROR: No YouTube API key found.')
    print('Set YOUTUBE_API_KEY env var or put it in C:\\youtube_api_key.txt')
    sys.exit(1)


def api_get(endpoint: str, params: dict, api_key: str) -> dict:
    """Make a GET request to the YouTube Data API."""
    params['key'] = api_key
    url = f'{API_BASE}/{endpoint}?{urllib.parse.urlencode(params)}'
    req = urllib.request.Request(url, headers={
        'Accept': 'application/json',
    })
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        print(f'API error {e.code}: {body[:500]}')
        raise


def extract_video_id(url: str) -> str:
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:/live/)([a-zA-Z0-9_-]{11})',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    return url


def get_live_chat_id(video_id: str, api_key: str) -> str:
    """Get the liveChatId for a video."""
    data = api_get('videos', {
        'part': 'liveStreamingDetails',
        'id': video_id,
    }, api_key)

    items = data.get('items', [])
    if not items:
        print(f'ERROR: Video {video_id} not found.')
        sys.exit(1)

    details = items[0].get('liveStreamingDetails', {})
    chat_id = details.get('activeLiveChatId')
    if not chat_id:
        print('ERROR: No active live chat found.')
        print('Make sure the stream is LIVE and chat is enabled.')
        sys.exit(1)

    return chat_id


def process_message(author: str, text: str) -> None:
    global last_global
    text = text.strip()
    if not text:
        return

    now = time.time()
    if now - last_global < GLOBAL_COOLDOWN:
        return
    if now - user_cooldowns[author] < PER_USER_COOLDOWN:
        return

    result = parse_and_execute(text)
    if result:
        last_global = now
        user_cooldowns[author] = now
        print(f'[{author}] {text}  =>  {result}')
        tts.speak(f'{author}, {result}')


def poll_chat(chat_id: str, api_key: str) -> None:
    """Poll YouTube live chat using the official API."""
    page_token = None
    poll_interval = 2.0

    while True:
        params = {
            'part': 'snippet,authorDetails',
            'liveChatId': chat_id,
            'maxResults': 200,
        }
        if page_token:
            params['pageToken'] = page_token

        try:
            data = api_get('liveChat/messages', params, api_key)
        except Exception as e:
            print(f'[Poll error: {e}]')
            time.sleep(5)
            continue

        # Use YouTube's recommended polling interval
        poll_interval = data.get('pollingIntervalMillis', 2000) / 1000.0
        page_token = data.get('nextPageToken')

        for item in data.get('items', []):
            snippet = item.get('snippet', {})
            author_details = item.get('authorDetails', {})

            if snippet.get('type') != 'textMessageEvent':
                continue

            author = author_details.get('displayName', 'unknown')
            text = snippet.get('textMessageDetails', {}).get('messageText', '')
            process_message(author, text)

        time.sleep(poll_interval)


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python bot.py <youtube-url-or-video-id>')
        sys.exit(1)

    video_id = extract_video_id(sys.argv[1])
    api_key = get_api_key()

    print(f'Video ID: {video_id}')
    print(f'Global cooldown: {GLOBAL_COOLDOWN}s | Per-user: {PER_USER_COOLDOWN}s')
    print()
    print('Commands:')
    print('  press:w          - press W key')
    print('  press:ctrl+s     - key combo')
    print('  hold:w:2         - hold W for 2 sec')
    print('  mouse:up         - move mouse up 50px')
    print('  mouse:left:200   - move mouse left 200px')
    print('  click:left       - left click')
    print('  click:right      - right click')
    print('  type:hello       - type text')
    print()
    tts.start()

    print('Fetching live chat ID...')
    chat_id = get_live_chat_id(video_id, api_key)
    print(f'Live chat connected!')
    print('Listening for commands...')
    print('=' * 50)

    try:
        poll_chat(chat_id, api_key)
    except KeyboardInterrupt:
        print('\nStopped.')
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
