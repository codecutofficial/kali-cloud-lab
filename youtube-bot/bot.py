"""YouTube Live Chat → Game Controller bot.

Reads chat from a YouTube live stream and translates commands into
keyboard/mouse input on this machine.

Usage:
    python bot.py https://www.youtube.com/watch?v=VIDEO_ID
    python bot.py VIDEO_ID
"""
import sys
import time
from collections import defaultdict
from chat_downloader import ChatDownloader
from commands import parse_and_execute
import tts

GLOBAL_COOLDOWN = 1.5
PER_USER_COOLDOWN = 2.0

last_global = 0.0
user_cooldowns: dict[str, float] = defaultdict(float)


def on_chat_message(msg: dict) -> None:
    global last_global

    text = msg.get("message", "").strip()
    author = msg.get("author", {}).get("name", "unknown")
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


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python bot.py <youtube-url-or-video-id>")
        sys.exit(1)

    url = sys.argv[1]
    if not url.startswith("http"):
        url = f"https://www.youtube.com/watch?v={url}"

    print(f"Connecting to live chat: {url}")
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
        chat = ChatDownloader().get_chat(url)
        for msg in chat:
            on_chat_message(msg)
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
