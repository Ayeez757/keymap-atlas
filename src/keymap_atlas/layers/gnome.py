"""6 · GNOME 键位层：gsettings 里的 wm keybindings。

GNOME 的值形如 `['<Super>t', '<Primary><Alt>t']`，用 ast.literal_eval 就够，
不必调 gsettings 的描述接口。
"""

from __future__ import annotations

import ast
import shutil
import subprocess

from ..config import Config, gnome_available
from ..keycaps import gnome_accel_to_caps
from .base import INACTIVE, Collector, LayerResult, Row

PREFIX = "6 · GNOME 键位层"

GNOME_SCHEMAS = [
    "org.gnome.desktop.wm.keybindings",
    "org.gnome.shell.keybindings",
    "org.gnome.mutter.keybindings",
]

GNOME_ZH = {
    "switch-applications": "切换应用（同一应用多窗口）",
    "switch-applications-backward": "反向切换应用",
    "switch-windows": "切换窗口",
    "switch-windows-backward": "反向切换窗口",
    "switch-group": "切换同应用窗口分组",
    "switch-to-workspace-left": "切到左边工作区",
    "switch-to-workspace-right": "切到右边工作区",
    "switch-to-workspace-up": "切到上边工作区",
    "switch-to-workspace-down": "切到下边工作区",
    "move-to-workspace-left": "把窗口移到左边工作区",
    "move-to-workspace-right": "把窗口移到右边工作区",
    "close": "关闭窗口",
    "minimize": "最小化窗口",
    "maximize": "最大化窗口",
    "unmaximize": "取消最大化",
    "begin-move": "开始移动窗口",
    "begin-resize": "开始调整窗口大小",
    "toggle-fullscreen": "切换全屏",
    "toggle-tiled-left": "把窗口贴到左半边",
    "toggle-tiled-right": "把窗口贴到右半边",
    "activate-window-menu": "打开窗口菜单",
    "show-desktop": "显示桌面",
    "panel-run-dialog": "打开运行命令对话框",
    "toggle-overview": "切换总览",
    "toggle-application-view": "切换应用列表",
    "toggle-message-tray": "切换通知托盘",
    "screenshot": "截图",
    "screenshot-window": "截取窗口",
    "show-screenshot-ui": "打开截图界面",
    "switch-monitor": "切换显示器",
    "rotate-monitor": "旋转显示器",
    "logout": "注销",
    "screensaver": "屏保 / 锁屏",
    "switch-input-source": "切换输入源（键盘布局）",
    "switch-input-source-backward": "反向切换键盘布局",
    "toggle-touchpad": "开关触摸板",
}


def _read_schema(schema: str) -> dict[str, str]:
    """读一个 schema 的所有键值，返回 {键名: 原始值}。"""
    if not shutil.which("gsettings"):
        return {}
    try:
        r = subprocess.run(["gsettings", "list-recursively", schema],
                           capture_output=True, text=True, timeout=6)
    except (OSError, subprocess.SubprocessError):
        return {}
    if r.returncode != 0:
        return {}
    out: dict[str, str] = {}
    for line in r.stdout.splitlines():
        parts = line.split(" ", 2)
        if len(parts) == 3:
            out[parts[1]] = parts[2]
    return out


def parse_accel_list(raw: str) -> list[str]:
    """`['<Super>t', '<Primary><Alt>t']` → ['<Super>t', '<Primary><Alt>t']。"""
    try:
        val = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return []
    if isinstance(val, str):
        return [val] if val else []
    if isinstance(val, (list, tuple)):
        return [str(x) for x in val if x]
    return []


class GnomeLayer(Collector):
    name = PREFIX

    def __init__(self, cfg: Config):
        self.cfg = cfg

    def available(self) -> bool:
        return gnome_available(self.cfg)

    def collect(self) -> LayerResult:
        if not self.available():
            return LayerResult(self.name, skipped="没有 gsettings 命令")

        rows: list[Row] = []
        for schema in GNOME_SCHEMAS:
            sub = schema.split(".")[-1]
            for key, raw in sorted(_read_schema(schema).items()):
                accels = parse_accel_list(raw)
                if not accels:
                    continue
                action = GNOME_ZH.get(key, key.replace("-", " "))
                for accel in accels:
                    if accel.startswith("disabled"):
                        continue
                    rows.append(Row(
                        layer=f"{PREFIX} › {sub}",
                        keys=gnome_accel_to_caps(accel),
                        action=action,
                        note="当前会话不是 GNOME，这些键位不生效",
                        status=INACTIVE,
                        source=f"gsettings {schema} {key}",
                    ))

        if not rows:
            return LayerResult(self.name, skipped="gsettings 里没有可用的快捷键值")
        return LayerResult(self.name, rows)
