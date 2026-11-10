"""查表：从索引里按中文 / 拼音首字母 / 英文 / 键位找快捷键。

三个入口共用一份逻辑：
  · `keymap-atlas lookup 音量`       终端直出
  · `keymap-atlas lookup --fuzzel`   fuzzel 弹窗（Super+Alt+/ 绑的就是它）
  · `keys-lookup.sh`                 旧脚本（内部调本模块）
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .i18n import aliases_for, matches

TSV_NAME = "shortcuts-index.tsv"


def load_index(path: Path) -> list[dict[str, str]]:
    """读 TSV 索引。列固定为 keys/action/note/layer/status/aliases。"""
    rows: list[dict[str, str]] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        parts += [""] * (6 - len(parts))
        rows.append({
            "keys": parts[0], "action": parts[1], "note": parts[2],
            "layer": parts[3], "status": parts[4], "aliases": parts[5],
        })
    return rows


def search(rows: list[dict[str, str]], query: str,
           include_inactive: bool = False) -> list[dict[str, str]]:
    out = []
    for r in rows:
        if not include_inactive and r.get("status") != "生效":
            continue
        if matches(r.get("action", ""), r.get("aliases", ""), r.get("keys", ""), query):
            out.append(r)
    return out


def format_row(r: dict[str, str], width: int = 30) -> str:
    keys = (r.get("keys") or "")[:width].ljust(width)
    note = ("  ⚠ " + r["note"]) if r.get("note") else ""
    return f"{keys} │ {r.get('action', '')}  [{r.get('layer', '')}]{note}"


def build_fuzzel_lines(rows: list[dict[str, str]]) -> list[str]:
    return [format_row(r) for r in rows]


def fuzzel_pick(lines: list[str], prompt: str = "快捷键 › ") -> str | None:
    """弹 fuzzel 选一条，返回选中行（取消则 None）。"""
    bin_path = shutil.which("fuzzel")
    if not bin_path:
        return None
    lines = lines[:14]
    cmd = [
        bin_path, "--dmenu", "--prompt", prompt, "--lines", str(max(3, len(lines))),
        "--width", "68", "--match-mode", "fzf", "--auto-select", "--no-icons",
        "--font", "Noto Sans CJK SC:size=11",
    ]
    try:
        r = subprocess.run(cmd, input="\n".join(lines), capture_output=True,
                           text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return r.stdout.strip() or None


def copy_to_clipboard(text: str) -> bool:
    for tool in ("wl-copy", "xclip"):
        if not shutil.which(tool):
            continue
        try:
            if tool == "wl-copy":
                subprocess.run([tool], input=text, text=True, timeout=5, check=False)
            else:
                subprocess.run([tool, "-selection", "clipboard"], input=text,
                               text=True, timeout=5, check=False)
            return True
        except (OSError, subprocess.SubprocessError):
            continue
    return False


def notify(text: str, app: str = "快捷键") -> None:
    if not shutil.which("notify-send"):
        return
    try:
        subprocess.run(["notify-send", "-a", app, "-r", "20241108", text],
                       timeout=5, check=False)
    except (OSError, subprocess.SubprocessError):
        pass


def aliases_column(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """给缺 aliases 列的旧索引补齐（老格式 5 列）。"""
    for r in rows:
        if not r.get("aliases"):
            r["aliases"] = aliases_for(r.get("action", ""), r.get("keys", ""))
    return rows
