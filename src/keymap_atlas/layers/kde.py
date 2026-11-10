"""5 · KDE 全局快捷键层：读 ~/.config/kglobalshortcutsrc。

文件格式（kglobalshortcutsrc v1）：

    [kmix]
    decrease_volume=Volume Down,Volume Down,降低音量

值是 `当前绑定,默认绑定,友好名` 三段逗号分隔；同一个动作的**多套**快捷键用
真实 TAB 分隔成多组（`A,B,名前<TAB>C,D,名后`）。所以要先按 TAB 切组，再按逗号切三段。

这份文件在非 KDE 会话里也在（KDE 装过就会留），但绑定不生效——所以整层标「未生效」。
"""

from __future__ import annotations

from pathlib import Path

from ..config import Config, kde_available
from ..keycaps import norm_caps
from .base import INACTIVE, Collector, LayerResult, Row

PREFIX = "5 · KDE 全局快捷键层"

# KDE 的组名 / 快捷键名 → 中文。未收录的保留原文（友好名多半自带中文）。
KDE_ZH = {
    "kwin": "窗口管理器", "KWin": "窗口管理器",
    "KDE Keyboard Layout Switcher": "键盘布局切换",
    "kmix": "音量", "KDE Daemon": "KDE 守护进程",
    "khotkeys": "自定义动作", "plasmashell": "Plasma 桌面",
    "ActivityManager": "活动（虚拟桌面）", "ksmserver": "会话管理",
    "KRunner": "KRunner 启动器", "org.kde.konsole": "Konsole 终端",
    "org.kde.dolphin": "Dolphin 文件管理器", "spectacle": "Spectacle 截图",
    "org_kde_powerdevil": "电源管理", "kaccess": "辅助功能",
    "kmag": "放大镜", "kmousetool": "鼠标辅助",
}

# 「没绑定」的当前值写法
NO_BIND = {"none", "", "default(", "launch(", "unbound"}


def _has_cjk(s: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in s)


def _pick_action(key: str, friendly: str) -> str:
    """优先用文件里的友好名（KDE 存的是本地化文案），其次内置表。"""
    if friendly and _has_cjk(friendly):
        return friendly
    if friendly and friendly not in ("none",):
        return friendly
    if key in KDE_ZH:
        return KDE_ZH[key]
    return key.replace("_", " ").replace("-", " ")


def parse_kglobalshortcuts(text: str) -> list[tuple[str, str, list[str], str]]:
    """返回 [(组名, 动作名, [组合键…], 友好名)]。

    KDE 的存法：一行的值是若干「快捷键组」用逗号分隔，每组内多个键用制表符
    分隔，第三段起是本地化友好名。制表符在文件里是**字面量 \\t（两个字符）**，
    实测本机 16 行如此；真 TAB 也一并兼容。只取第一组（KDE 当前生效的那组）。
    """
    out: list[tuple[str, str, list[str], str]] = []
    group = ""
    skip_group = False

    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(";"):
            continue
        if s.startswith("[") and s.endswith("]"):
            # KDE 用 [kwin][$InverseAction] 这种双段写法。
            # $InverseAction 段不是快捷键，是「反向动作」的元数据（如
            # Walk Through Windows → (Reverse)），必须整段丢弃。
            group = s[1:-1].replace("][", " › ")
            skip_group = "$InverseAction" in group
            continue
        if "=" not in s or skip_group:
            continue
        key, val = s.split("=", 1)
        key = key.strip()
        if key.startswith("_k_"):
            continue

        parts = val.split(",")
        if len(parts) < 3:
            # 没有友好名段：整段当快捷键，友好名留空
            active, friendly = parts[0], ""
        else:
            active, friendly = parts[0], ",".join(parts[2:]).strip()

        combos = [c.strip() for c in active.replace("\\t", "\t").split("\t")]
        combos = [c for c in combos if c and c.lower() not in NO_BIND]
        if not combos:
            continue
        out.append((group, _pick_action(key, friendly), combos, friendly))
    return out


class KdeLayer(Collector):
    name = PREFIX

    def __init__(self, cfg: Config):
        self.cfg = cfg

    def available(self) -> bool:
        return kde_available(self.cfg)

    def collect(self) -> LayerResult:
        p: Path = self.cfg.kde_config
        if not p.is_file():
            return LayerResult(self.name, skipped=f"没找到 {p}")

        rows: list[Row] = []
        for group, action, combos, _friendly in parse_kglobalshortcuts(
                p.read_text(errors="replace")):
            group_zh = KDE_ZH.get(group, group)
            for combo in combos:
                rows.append(Row(
                    layer=f"{PREFIX} › {group_zh}",
                    keys=norm_caps(combo),
                    action=action,
                    note="当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用",
                    status=INACTIVE,
                    source=str(p),
                ))
        return LayerResult(self.name, rows)
