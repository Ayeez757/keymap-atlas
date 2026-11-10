"""真实按键探针（GTK4）。

为什么需要它：`/proc/bus/input/devices` 的能力位图会把 HID 的「通用数组」
（`Usage Minimum 0x00, Usage Maximum 0xff`）整段标成「有这个键」，于是报告
会列出从来按不出的音量键。唯一可信的证据是**你真的按了一次**。

两条安全红线：
1. 探测期间必须抑制 niri 快捷键，否则 Print / F1 会在到达窗口之前被 niri 截走；
2. niri 的抑制动作是 **toggle（无状态翻转）**，翻错一次整个桌面快捷键就失灵。
   所以这里自己记账，只在状态不同时翻转，并在所有退出路径恢复。
"""

from __future__ import annotations

import atexit
import signal
import subprocess
import sys

from . import evidence as ev
from . import kdl
from .config import Config

# 修饰键不记录：按住它们只是为了组成组合键
IGNORE_KEYSYMS = {
    "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
    "Super_L", "Super_R", "Meta_L", "Meta_R", "Hyper_L", "Hyper_R",
    "Caps_Lock", "Num_Lock", "ISO_Level3_Shift", "ISO_Level5_Shift",
}

# Shift 变体的 keysym 名 → 不带 Shift 时的配置写法
SHIFTED = {
    "exclam": "1", "at": "2", "numbersign": "3", "dollar": "4",
    "percent": "5", "asciicircum": "6", "ampersand": "7", "asterisk": "8",
    "parenleft": "9", "parenright": "0", "underscore": "Minus",
    "plus": "Equal", "colon": "semicolon", "question": "Slash",
    "bar": "Backslash", "asciitilde": "grave", "braceleft": "BracketLeft",
    "braceright": "BracketRight", "quotedbl": "apostrophe",
    "less": "Comma", "greater": "Period",
}

_CANON: dict[str, str] | None = None


def canon_map() -> dict[str, str]:
    """`{'s': 'S', 'slash': 'Slash'}`：GTK 名小写 → 配置写法。"""
    global _CANON
    if _CANON is None:
        _CANON = {k.lower(): k for k in kdl.KEYMAP}
    return _CANON


def normalize(name: str) -> str:
    """把 GTK 报的 keysym 名归一成 niri 配置里的写法。"""
    if not name:
        return name
    cm = canon_map()
    low = name.lower()
    if low in cm:
        return cm[low]
    if low in SHIFTED:
        v = SHIFTED[low]
        return cm.get(v.lower(), v)
    return name


def wanted_keysyms(cfg: Config) -> list[str]:
    """配置里真正被用到的 keysym —— 只需要验证这些。"""
    if not cfg.niri_config.is_file():
        return []
    out: list[str] = []
    for b in kdl.parse_file(cfg.niri_config):
        main = b.main
        if main in kdl.KEYMAP and main not in out:
            out.append(main)
    return out


_INHIBIT = {"on": False}


def niri_inhibit(on: bool) -> bool:
    """切换 niri 的快捷键抑制状态，带记账防翻错。"""
    if on == _INHIBIT["on"]:
        return True
    try:
        subprocess.run(["niri", "msg", "action", "toggle-keyboard-shortcuts-inhibit"],
                       capture_output=True, text=True, timeout=3, check=False)
    except (OSError, subprocess.SubprocessError):
        return False
    _INHIBIT["on"] = on
    return True


def release_inhibit() -> None:
    """无论如何都恢复到「不抑制」。"""
    if _INHIBIT["on"]:
        niri_inhibit(False)


def force_release() -> None:
    """强制复位：toggle 连翻两次必然回到「不抑制」，不管之前是什么状态。"""
    for _ in range(2):
        try:
            subprocess.run(["niri", "msg", "action",
                            "toggle-keyboard-shortcuts-inhibit"],
                           capture_output=True, timeout=3, check=False)
        except (OSError, subprocess.SubprocessError):
            return
    _INHIBIT["on"] = False


def run_gui(cfg: Config, save_cb) -> int:
    try:
        import gi
        gi.require_version("Gtk", "4.0")
        from gi.repository import Gdk, GLib, Gtk
    except (ImportError, ValueError) as exc:
        print(f"[错误] 起不了 GTK4 窗口：{exc}", file=sys.stderr)
        print("       装 PyGObject（Debian/Ubuntu: python3-gi gir1.2-gtk-4.0，"
              "Fedora: python3-gobject gtk4）后重试。", file=sys.stderr)
        return 2

    atexit.register(release_inhibit)
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        try:
            signal.signal(sig, lambda *_: (release_inhibit(), sys.exit(0)))
        except (OSError, ValueError):
            pass

    want = wanted_keysyms(cfg)
    data = ev.load(cfg)
    observed = set(data.observed)
    absent = set(data.absent)
    pressed: list[str] = []

    app = Gtk.Application(application_id="dev.keymapatlas.keyprobe")

    def on_activate(a):
        win = Gtk.ApplicationWindow(application=a, title="按键探针 · keymap-atlas")
        win.set_default_size(720, 620)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        for m in ("top", "bottom", "start", "end"):
            getattr(box, f"set_margin_{m}")(22)

        title = Gtk.Label()
        title.set_markup("<span size='x-large' weight='bold'>按键探针</span>")
        title.set_xalign(0)
        box.append(title)

        sub = Gtk.Label()
        sub.set_markup(
            "<span size='small'>探测期间 niri 快捷键已被<b>临时抑制</b>，"
            "你按下的键会直接进入本窗口。把想验证的键都按一遍；"
            "<b>Esc</b> 结束，<b>F9</b> 结束并保存。</span>")
        sub.set_xalign(0)
        sub.set_wrap(True)
        box.append(sub)

        status = Gtk.Label()
        status.set_xalign(0)
        status.set_wrap(True)
        box.append(status)

        big = Gtk.Label()
        big.set_xalign(0)
        big.set_wrap(True)
        big.set_selectable(True)
        sw1 = Gtk.ScrolledWindow()
        sw1.set_child(big)
        sw1.set_vexpand(True)
        fr1 = Gtk.Frame(label="已实测按出")
        fr1.set_child(sw1)
        box.append(fr1)

        rest = Gtk.Label()
        rest.set_xalign(0)
        rest.set_wrap(True)
        sw2 = Gtk.ScrolledWindow()
        sw2.set_child(rest)
        sw2.set_size_request(-1, 170)
        fr2 = Gtk.Frame(label="还没按到的键（按到就会移到上面）")
        fr2.set_child(sw2)
        box.append(fr2)

        def refresh():
            got = [k for k in want if k in observed]
            miss = [k for k in want if k not in observed]
            if pressed:
                big.set_markup(" ".join(
                    f"<span background='#2e7d32' foreground='white' size='large'> {k} </span>"
                    for k in got))
            else:
                big.set_markup("<span foreground='#888'>（还没有按任何键）</span>")
            rest.set_text("  ".join(miss) if miss else "（全部按到了）")
            status.set_markup(
                f"待测 {len(want)} 个 · 本次新按到 <b>{len(pressed)}</b> 个 · "
                f"累计已实测 {len(observed)} 个 · 已标「没有」{len(absent)} 个")
            win.set_title(f"按键探针 — {len(pressed)}/{len(want)}")

        done = {"flag": False}

        def finish(save=True):
            if done["flag"]:
                return
            done["flag"] = True
            if save:
                p = save_cb(set(observed))
                print(f"[已保存] {p}")
                print(f"  本次按到: {' '.join(pressed) or '(无)'}")
            else:
                print("[未保存] 按 F9 才会写入")
            release_inhibit()
            win.destroy()
            app.quit()

        def on_key(_ctrl, keyval, _keycode, _state):
            name = Gdk.keyval_name(keyval)
            if not name:
                return False
            if name == "Escape":
                finish()
                return True
            if name == "F9":
                finish(save=True)
                return True
            if name in IGNORE_KEYSYMS:
                return True
            canon = normalize(name)
            if canon not in observed:
                pressed.append(canon)
            observed.add(canon)
            refresh()
            return True

        ctrl = Gtk.EventControllerKey()
        ctrl.connect("key-pressed", on_key)
        win.add_controller(ctrl)
        win.connect("close-request", lambda w: (finish(save=False), False)[1])
        win.set_child(box)
        refresh()
        win.present()

        def after_present():
            if not niri_inhibit(True):
                status.set_text("⚠ 无法抑制 niri 快捷键，部分按键可能被 niri 截走")
            return False

        GLib.timeout_add(350, after_present)

    app.connect("activate", on_activate)
    app.run(None)
    return 0
