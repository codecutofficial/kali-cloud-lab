"""Command parser and executor for YouTube chat controls."""
import time
import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

BLOCKED_KEYS = frozenset([
    "alt+f4", "ctrl+alt+delete", "ctrl+alt+del",
    "win", "winleft", "winright", "super",
    "alt+tab", "ctrl+shift+escape",
])

ALLOWED_KEYS = frozenset([
    "a","b","c","d","e","f","g","h","i","j","k","l","m",
    "n","o","p","q","r","s","t","u","v","w","x","y","z",
    "0","1","2","3","4","5","6","7","8","9",
    "up","down","left","right",
    "space","enter","tab","escape","esc",
    "backspace","delete","del",
    "shift","ctrl","alt",
    "f1","f2","f3","f4","f5","f6","f7","f8","f9","f10","f11","f12",
    "home","end","pageup","pagedown",
    "insert","capslock","numlock",
    "+","-","=","[","]",";","'",",",".","/","`","\\",
])

MAX_MOUSE_MOVE = 500
MAX_HOLD_SECS = 3.0
MAX_TYPE_LEN = 20
DEFAULT_MOUSE_PX = 50

MOUSE_DIRS = {
    "up":    (0, -1),
    "down":  (0,  1),
    "left":  (-1, 0),
    "right": (1,  0),
}


def _is_combo_blocked(combo: str) -> bool:
    return combo.lower().replace(" ", "") in {
        k.replace(" ", "") for k in BLOCKED_KEYS
    }


def _keys_valid(keys: list[str]) -> bool:
    for k in keys:
        if k.lower() not in ALLOWED_KEYS:
            return False
    return True


def parse_and_execute(message: str) -> str | None:
    """Parse a chat message and execute if it's a valid command.
    Returns a description string on success, None if not a command."""
    msg = message.strip().lower()
    if ":" not in msg:
        return None

    parts = msg.split(":", maxsplit=2)
    action = parts[0].strip()

    if action == "press" and len(parts) >= 2:
        combo = parts[1].strip()
        if _is_combo_blocked(combo):
            return f"BLOCKED: {combo}"
        keys = [k.strip() for k in combo.split("+")]
        if not _keys_valid(keys):
            return f"UNKNOWN KEY: {combo}"
        if len(keys) == 1:
            pyautogui.press(keys[0])
        else:
            pyautogui.hotkey(*keys)
        return f"press {combo}"

    elif action == "hold" and len(parts) >= 2:
        key = parts[1].strip()
        duration = 1.0
        if len(parts) == 3:
            try:
                duration = min(float(parts[2].strip()), MAX_HOLD_SECS)
            except ValueError:
                duration = 1.0
        if _is_combo_blocked(key) or key not in ALLOWED_KEYS:
            return f"BLOCKED: {key}"
        pyautogui.keyDown(key)
        time.sleep(max(0.1, duration))
        pyautogui.keyUp(key)
        return f"hold {key} {duration:.1f}s"

    elif action == "mouse" and len(parts) >= 2:
        direction = parts[1].strip()
        if direction not in MOUSE_DIRS:
            return None
        px = DEFAULT_MOUSE_PX
        if len(parts) == 3:
            try:
                px = min(int(parts[2].strip()), MAX_MOUSE_MOVE)
            except ValueError:
                px = DEFAULT_MOUSE_PX
        dx, dy = MOUSE_DIRS[direction]
        pyautogui.moveRel(dx * px, dy * px, duration=0.1)
        return f"mouse {direction} {px}px"

    elif action == "click" and len(parts) >= 2:
        button = parts[1].strip()
        if button in ("left", "right", "middle"):
            pyautogui.click(button=button)
            return f"click {button}"

    elif action == "type" and len(parts) >= 2:
        text = parts[1].strip()[:MAX_TYPE_LEN]
        if text:
            pyautogui.typewrite(text, interval=0.03)
            return f"type '{text}'"

    return None
