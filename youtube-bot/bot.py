"""YouTube Live Chat → Game Controller bot.

Reads chat from a YouTube live stream and translates commands into
keyboard/mouse input on this machine.

Usage:
    python bot.py https://www.youtube.com/watch?v=VIDEO_ID
    python bot.py VIDEO_ID
"""
import sys
import re
import time
from collections import defaultdict

try:
    import pytchat
except ImportError:
    print("pytchat not installed. Run: pip install pytchat")
    sys.exit(1)

from commands import parse_and_execute
import tts

GLOBAL_COOLDOWN = 1.5
PER_USER_COOLDOWN = 2.0

last_global = 0.0
user_cooldowns: dict[str, float] = defaultdict(float)


def extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:/live/)([a-zA-Z0-9_-]{11})',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    # Assume it's already a video ID
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    return url


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python bot.py <youtube-url-or-video-id>")
        sys.exit(1)

    video_id = extract_video_id(sys.argv[1])

    print(f"Connecting to live chat for video: {video_id}")
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
        chat = pytchat.create(video_id=video_id)
        while chat.is_alive():
            for msg in chat.get().sync_items():
                text = msg.message.strip()
                author = msg.author.name
                if not text:
                    continue

                now = time.time()
                if now - last_global < GLOBAL_COOLDOWN:
                    continue
                if now - user_cooldowns[author] < PER_USER_COOLDOWN:
                    continue

                result = parse_and_execute(text)
                if result:
                    globals()['last_global'] = now
                    user_cooldowns[author] = now
                    print(f"[{author}] {text}  =>  {result}")
                    tts.speak(f"{author}, {result}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
