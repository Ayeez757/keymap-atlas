"""2 · 输入法层（fcitx5）：读 ~/.config/fcitx5/config，全注释时用内置默认。"""

from __future__ import annotations

import re
from pathlib import Path

from ..config import Config, fcitx_available
from .base import Collector, LayerResult, Row

PREFIX = "2 · 输入法层（fcitx5）"

FCITX_ZH = {
    "TriggerKeys": "激活 / 关闭当前输入法",
    "EnumerateForwardKeys": "切换到下一个输入法",
    "EnumerateBackwardKeys": "切换到上一个输入法",
    "ActivateKeys": "临时启用输入法",
    "DeactivateKeys": "临时关闭输入法",
    "AltTriggerKeys": "切换中英文（临时切换）",
    "EnumerateGroupForwardKeys": "切换到下一个输入法组",
    "EnumerateGroupBackwardKeys": "切换到上一个输入法组",
    "TogglePreedit": "切换预编辑文本显示",
    "PrevPage": "候选词上一页",
    "NextPage": "候选词下一页",
    "PrevCandidate": "上一个候选词",
    "NextCandidate": "下一个候选词",
}

# fcitx5 出厂默认（配置文件里全是注释时生效）
FCITX_BUILTIN = {
    "TriggerKeys": ["Ctrl+Space"],
    "AltTriggerKeys": ["Shift_L"],
    "TogglePreedit": ["Ctrl+Alt+P"],
    "NextCandidate": ["Tab"],
    "PrevCandidate": ["Shift+Tab"],
    "NextPage": ["Down"],
    "PrevPage": ["Up"],
}

FCITX_CAP = {
    "Ctrl": "Ctrl", "Control": "Ctrl", "Shift": "Shift", "Alt": "Alt",
    "Super": "Super", "Meta": "Super", "space": "Space", "Tab": "Tab",
    "Up": "↑", "Down": "↓", "Shift_L": "左Shift", "Control_L": "左Ctrl",
    "Alt_L": "左Alt", "Super_L": "左Super",
}


def parse_config_text(text: str) -> dict[str, list[str]]:
    """ini 风格解析，只留 [section/key] 形式的键。纯文本入口便于测试。"""
    explicit: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^\[(.+)\]$", s)
        if m:
            current = m.group(1).split("/")[-1]
            continue
        if "=" in s and current:
            k, v = s.split("=", 1)
            explicit.setdefault(k.strip(), []).append(v.strip())
    return explicit


def parse_config(p: Path) -> dict[str, list[str]]:
    return parse_config_text(p.read_text(errors="replace"))


class FcitxLayer(Collector):
    name = PREFIX

    def __init__(self, cfg: Config):
        self.cfg = cfg

    def available(self) -> bool:
        return fcitx_available(self.cfg)

    def collect(self) -> LayerResult:
        if not self.available():
            return LayerResult(self.name, skipped="没装 fcitx5，也没找到配置文件")

        explicit: dict[str, list[str]] = {}
        if self.cfg.fcitx_config.is_file():
            explicit = parse_config(self.cfg.fcitx_config)

        src = explicit if explicit else FCITX_BUILTIN
        rows: list[Row] = []
        for key, vals in src.items():
            zh = FCITX_ZH.get(key)
            if not zh:
                continue
            for v in vals:
                caps = [FCITX_CAP.get(p.strip(), p.strip()) for p in v.split("+")]
                rows.append(Row(
                    layer=PREFIX,
                    keys=caps,
                    action=zh,
                    note="" if explicit else "配置里全是注释 → fcitx5 内置默认值",
                    source=str(self.cfg.fcitx_config),
                ))
        return LayerResult(self.name, rows)
