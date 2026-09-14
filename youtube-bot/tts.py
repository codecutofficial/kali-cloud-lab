"""Lightweight streaming TTS using Microsoft Edge neural voices.

Queues speech in a background thread so commands aren't blocked.
Uses edge-tts (free, no API key) + pygame for audio playback.
"""
import asyncio
import os
import queue
import tempfile
import threading

try:
    import edge_tts
    import pygame
    pygame.mixer.init()
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

VOICE = "en-US-ChristopherNeural"
RATE = "+15%"

_q: queue.Queue[str | None] = queue.Queue()
_started = False


def _worker() -> None:
    """Background loop: pull text from queue, synthesize, play."""
    while True:
        text = _q.get()
        if text is None:
            break
        try:
            tmp = asyncio.run(_synthesize(text))
            pygame.mixer.music.load(tmp)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(50)
            pygame.mixer.music.unload()
            os.unlink(tmp)
        except Exception as e:
            print(f"[TTS error] {e}")
        _q.task_done()


async def _synthesize(text: str) -> str:
    """Generate speech to a temp mp3 file."""
    comm = edge_tts.Communicate(text, VOICE, rate=RATE)
    fd, tmp = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    await comm.save(tmp)
    return tmp


def start() -> None:
    """Start the background TTS worker thread."""
    global _started
    if not TTS_AVAILABLE or _started:
        return
    _started = True
    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    print("[TTS] Edge neural voice ready")


def speak(text: str) -> None:
    """Queue text to be spoken. Non-blocking."""
    if not TTS_AVAILABLE:
        return
    if _q.qsize() > 5:
        return
    _q.put(text)


def stop() -> None:
    """Signal the worker to exit."""
    _q.put(None)
