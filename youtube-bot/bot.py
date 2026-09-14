"""YouTube Live Chat → Game Controller bot.

Reads chat from a YouTube live stream and translates commands into
keyboard/mouse input on this machine.

Usage:
    python bot.py https://www.youtube.com/watch?v=VIDEO_ID
    python bot.py VIDEO_ID
"""
import sys
import re
import json
import time
import subprocess
import threading
from collections import defaultdict
from commands import parse_and_execute
import tts

GLOBAL_COOLDOWN = 1.5
PER_USER_COOLDOWN = 2.0

last_global = 0.0
user_cooldowns: dict[str, float] = defaultdict(float)


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
        print(f"[{author}] {text}  =>  {result}")
        tts.speak(f"{author}, {result}")


def read_chat_ytdlp(video_url: str) -> None:
    """Use yt-dlp to read live chat in real time."""
    proc = subprocess.Popen(
        [
            'yt-dlp', '--skip-download',
            '--sub-lang', 'live_chat',
            '--write-sub', '--sub-format', 'json',
            '-o', '-',
            '--no-warnings',
            '--quiet',
            video_url,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # yt-dlp writes live_chat.json with one JSON object per line
    # Wait for the .json file to appear
    import glob
    import os

    # yt-dlp will create a file like VIDEO_ID.live_chat.json
    time.sleep(5)
    json_files = glob.glob('*.live_chat.json')
    if json_files:
        follow_json_file(json_files[0])
    else:
        proc.wait()
        raise RuntimeError("yt-dlp didn't produce a live_chat file")


def follow_json_file(path: str) -> None:
    """Tail a live_chat.json file as yt-dlp writes to it."""
    import os
    with open(path, 'r', encoding='utf-8') as f:
        while True:
            line = f.readline()
            if line:
                try:
                    obj = json.loads(line)
                    actions = obj.get('replayChatItemAction', {}).get('actions', [])
                    for action in actions:
                        item = action.get('addChatItemAction', {}).get('item', {})
                        renderer = item.get('liveChatTextMessageRenderer', {})
                        if renderer:
                            author = renderer.get('authorName', {}).get('simpleText', 'unknown')
                            runs = renderer.get('message', {}).get('runs', [])
                            text = ''.join(r.get('text', '') for r in runs)
                            process_message(author, text)
                except (json.JSONDecodeError, KeyError):
                    pass
            else:
                time.sleep(0.3)


def read_chat_polling(video_id: str) -> None:
    """Fallback: poll YouTube's live chat using raw HTTP."""
    import urllib.request
    import urllib.error

    url = f'https://www.youtube.com/watch?v={video_id}'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    # Fetch the page to get initial chat continuation token
    req = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(req)
    page = resp.read().decode('utf-8', errors='replace')

    # Extract API key
    api_key_match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', page)
    if not api_key_match:
        raise RuntimeError('Could not find YouTube API key on page')
    api_key = api_key_match.group(1)

    # Extract continuation token
    cont_match = re.search(r'"continuation":"([^"]+)"', page)
    if not cont_match:
        raise RuntimeError('Could not find chat continuation token — is this a live stream with chat enabled?')
    continuation = cont_match.group(1)

    # Extract client version
    ver_match = re.search(r'"clientVersion":"([^"]+)"', page)
    client_version = ver_match.group(1) if ver_match else '2.20260914.00.00'

    live_chat_url = f'https://www.youtube.com/youtubei/v1/live_chat/get_live_chat?key={api_key}'

    seen = set()

    while True:
        body = json.dumps({
            'context': {
                'client': {
                    'clientName': 'WEB',
                    'clientVersion': client_version,
                }
            },
            'continuation': continuation,
        }).encode('utf-8')

        req = urllib.request.Request(
            live_chat_url,
            data=body,
            headers={**headers, 'Content-Type': 'application/json'},
        )

        try:
            resp = urllib.request.urlopen(req)
            data = json.loads(resp.read())
        except Exception as e:
            print(f"[Chat poll error: {e}]")
            time.sleep(5)
            continue

        # Update continuation
        for cont in data.get('continuationContents', {}).get('liveChatContinuation', {}).get('continuations', []):
            if 'invalidationContinuationData' in cont:
                continuation = cont['invalidationContinuationData']['continuation']
            elif 'timedContinuationData' in cont:
                continuation = cont['timedContinuationData']['continuation']

        # Process messages
        actions = data.get('continuationContents', {}).get('liveChatContinuation', {}).get('actions', [])
        for action in actions:
            item = action.get('addChatItemAction', {}).get('item', {})
            renderer = item.get('liveChatTextMessageRenderer', {})
            if not renderer:
                continue

            msg_id = renderer.get('id', '')
            if msg_id in seen:
                continue
            seen.add(msg_id)
            if len(seen) > 5000:
                seen = set(list(seen)[-2000:])

            author = renderer.get('authorName', {}).get('simpleText', 'unknown')
            runs = renderer.get('message', {}).get('runs', [])
            text = ''.join(r.get('text', '') for r in runs)
            process_message(author, text)

        time.sleep(2)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python bot.py <youtube-url-or-video-id>")
        sys.exit(1)

    raw = sys.argv[1]
    video_id = extract_video_id(raw)
    video_url = f'https://www.youtube.com/watch?v={video_id}'

    print(f"Connecting to live chat: {video_url}")
    print(f"Global cooldown: {GLOBAL_COOLDOWN}s | Per-user: {PER_USER_COOLDOWN}s")
    print("")
    print("Commands:")
    print("  press:w          - press W key")
    print("  press:ctrl+s     - key combo")
    print("  hold:w:2         - hold W for 2 sec")
    print("  mouse:up         - move mouse up 50px")
    print("  mouse:left:200   - move mouse left 200px")
    print("  click:left       - left click")
    print("  click:right      - right click")
    print("  type:hello       - type text")
    print("")
    tts.start()
    print("Listening for commands...")
    print("=" * 50)

    try:
        read_chat_polling(video_id)
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as e:
        print(f"Polling method failed: {e}")
        print("Bot stopped.")
        sys.exit(1)


if __name__ == "__main__":
    main()
