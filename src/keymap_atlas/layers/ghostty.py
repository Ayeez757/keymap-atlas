"""3 · 终端应用层（Ghostty）：解析 `keybind = ...`，只在 Ghostty 有焦点时生效。"""

from __future__ import annotations

import re
from pathlib import Path

from ..config import Config, ghostty_available
from ..keycaps import norm_caps
from .base import Collector, LayerResult, Row

PREFIX = "3 · 终端应用层（Ghostty）"

GHOSTTY_ZH = {
    "new_window": "新建窗口", "new_tab": "新建标签页",
    "increase_font_size": "放大字体", "decrease_font_size": "缩小字体",
    "reset_font_size": "重置字体大小", "copy_to_clipboard": "复制",
    "paste_from_clipboard": "粘贴", "close_surface": "关闭当前标签页",
    "toggle_fullscreen": "全屏切换", "open_config": "打开配置文件",
    "new_split": "新建分屏", "close_tab": "关闭标签页",
    "previous_tab": "上一个标签页", "next_tab": "下一个标签页",
}

KEYBIND_RE = re.compile(r"^\s*keybind\s*=\s*(.+)$")


def parse_keybinds(text: str) -> list[tuple[str, str, str]]:
    """返回 [(原始组合键, 动作原文, 组合键)]。"""
    out: list[tuple[str, str, str]] = []
    for line in text.splitlines():
        m = KEYBIND_RE.match(line)
        if not m:
            continue
        spec = m.group(1).strip()
        if "=" not in spec:
            continue
        k, act = spec.split("=", 1)
        out.append((k.strip(), act.strip(), spec))
    return out


def translate_action(act: str) -> str:
    base = act.split(":")[0]
    if base == "text" and ":" in act:
        val = act.split(":", 1)[1]
        return "直接输入 " + ("换行符" if val in ("\\n", "\\\\n") else val)
    return GHOSTTY_ZH.get(base, act)


class GhosttyLayer(Collector):
    name = PREFIX

    def __init__(self, cfg: Config):
        self.cfg = cfg

    def available(self) -> bool:
        return ghostty_available(self.cfg)

    def collect(self) -> LayerResult:
        if not self.available():
            return LayerResult(self.name, skipped="没找到 Ghostty 配置文件")
        p: Path = self.cfg.ghostty_config
        rows: list[Row] = []
        for raw_keys, act, _spec in parse_keybinds(p.read_text(errors="replace")):
            rows.append(Row(
                layer=PREFIX,
                keys=norm_caps(raw_keys),
                action=translate_action(act),
                note="仅 Ghostty 窗口有焦点时生效",
                source=str(p),
            ))
        return LayerResult(self.name, rows)
