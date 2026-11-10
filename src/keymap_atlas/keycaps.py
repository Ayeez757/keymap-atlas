"""把各种应用风格的键名（ghostty / KDE / GNOME / fcitx）归一成显示用的键帽。"""

from __future__ import annotations

KEYNORM = {
    "plus": "=", "minus": "-", "zero": "0", "enter": "Enter", "tab": "Tab",
    "backspace": "Backspace", "escape": "Esc", "space": "Space",
    "page_up": "PgUp", "page_down": "PgDn", "home": "Home", "end": "End",
    "up": "↑", "down": "↓", "left": "←", "right": "→",
    "delete": "Del", "insert": "Ins", "return": "Enter", "comma": ",",
    "period": ".", "slash": "/", "semicolon": ";", "apostrophe": "'",
    "grave": "`", "bracketleft": "[", "bracketright": "]",
    "backslash": "\\", "equal": "=", "print": "PrtSc",
}

MODNORM = {
    "ctrl": "Ctrl", "control": "Ctrl", "shift": "Shift", "alt": "Alt",
    "super": "Super", "meta": "Super", "mod4": "Super", "mod1": "Alt",
}

GS_CAP = {
    "<Primary>": "Ctrl", "<Control>": "Ctrl", "<Shift>": "Shift",
    "<Alt>": "Alt", "<Super>": "Super", "<Mod4>": "Super", "<Meta>": "Super",
}


def norm_caps(key_spec: str, sep: str = "+") -> list[str]:
    """`ctrl+shift+t` / `Meta+T` / `Ctrl_Tab` → ['Ctrl','Shift','T']。"""
    out: list[str] = []
    for raw in key_spec.split(sep):
        p = raw.strip()
        low = p.lower()
        if low in MODNORM:
            out.append(MODNORM[low])
        elif low in KEYNORM:
            out.append(KEYNORM[low])
        elif len(p) == 1 and p.isalpha():
            out.append(p.upper())
        elif p.startswith("F") and p[1:].isdigit():
            out.append(p)
        else:
            out.append(p.replace("_", " ").strip() or p)
    return out


def gnome_accel_to_caps(accel: str) -> list[str]:
    """`<Primary><Alt>t` → ['Ctrl','Alt','T']。"""
    import re
    mods = re.findall(r"<[^>]+>", accel)
    rest = re.sub(r"<[^>]+>", "", accel).strip()
    caps = [GS_CAP.get(m, m.strip("<>")) for m in mods]
    if rest:
        low = rest.lower()
        if low in KEYNORM:
            caps.append(KEYNORM[low])
        elif len(rest) == 1 and rest.isalpha():
            caps.append(rest.upper())
        elif rest.startswith("F") and rest[1:].isdigit():
            caps.append(rest)
        else:
            caps.append(rest.capitalize() if rest.islower() else rest)
    return caps
