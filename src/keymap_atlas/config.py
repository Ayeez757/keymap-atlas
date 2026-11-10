"""路径解析与「这一层在这台机器上存在吗」的探测。

设计目标：换一台机器（GNOME / KDE / Sway / 纯 tty）也能跑，缺的层整层跳过，
而不是崩在 FileNotFoundError 上。所有路径都能用环境变量覆盖，方便测试。

优先级（高 → 低）：
  1. 命令行参数（--config-dir 等，由 CLI 传进 Config）
  2. 环境变量 KEYMAP_ATLAS_CONFIG_DIR
  3. $XDG_CONFIG_HOME
  4. ~/.config
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

# 旧版本（v0.0.x 脚本时代）把证据文件直接放在 ~/.config 根下。为了不丢用户
# 已有的实测记录，读取时兼容旧路径，写入时用新目录，并只提示一次迁移。
LEGACY_NOTES = ".config/shortcut-keyboard-notes.json"
LEGACY_PROBE = ".config/shortcut-keyboard-probe.json"


def _xdg_config_home() -> Path:
    env = os.environ.get("KEYMAP_ATLAS_CONFIG_DIR")
    if env:
        return Path(env).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg).expanduser() / "keymap-atlas"
    return Path.home() / ".config" / "keymap-atlas"


@dataclass
class Config:
    """一次运行要用到的全部路径与开关。"""

    # niri 合成器层
    niri_config: Path = field(default_factory=lambda: Path.home() / ".config/niri/config.kdl")
    # 应用层
    fcitx_config: Path = field(default_factory=lambda: Path.home() / ".config/fcitx5/config")
    ghostty_config: Path = field(default_factory=lambda: Path.home() / ".config/ghostty/config")
    kde_config: Path = field(default_factory=lambda: Path.home() / ".config/kglobalshortcutsrc")
    # 证据 / 状态
    state_dir: Path = field(default_factory=_xdg_config_home)
    out_dir: Path = field(default_factory=Path.cwd)

    @property
    def notes_path(self) -> Path:
        return self.state_dir / "notes.json"

    @property
    def probe_path(self) -> Path:
        return self.state_dir / "probe.json"

    @property
    def fingerprint_path(self) -> Path:
        return self.state_dir / "fingerprint.txt"

    def legacy_notes(self) -> Path:
        return Path.home() / LEGACY_NOTES

    def legacy_probe(self) -> Path:
        return Path.home() / LEGACY_PROBE

    def ensure_state_dir(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------ 层探测
def has_layers_file(p: Path) -> bool:
    return p.is_file()


def has_program(name: str) -> bool:
    return shutil.which(name) is not None


def niri_available(cfg: Config) -> bool:
    """niri 层：既要有配置文件，也要有 niri 在跑（否则绑定的键没有意义）。"""
    return cfg.niri_config.is_file()


def fcitx_available(cfg: Config) -> bool:
    return cfg.fcitx_config.is_file() or has_program("fcitx5")


def ghostty_available(cfg: Config) -> bool:
    return cfg.ghostty_config.is_file()


def kernel_available(cfg: Config | None = None) -> bool:
    """内核/硬件层：logind 的 D-Bus 属性 + /proc/sys/kernel/sysrq。"""
    return has_program("busctl") and Path("/proc/sys/kernel/sysrq").is_file()


def kde_available(cfg: Config) -> bool:
    return cfg.kde_config.is_file()


def gnome_available(cfg: Config | None = None) -> bool:
    return has_program("gsettings")


def lid_present() -> bool:
    """笔记本才有合盖事件；台式机跳过 HandleLidSwitch。"""
    return Path("/proc/acpi/button/lid").is_dir()


def session_desktop() -> str:
    return os.environ.get("XDG_CURRENT_DESKTOP", "") or os.environ.get("DESKTOP_SESSION", "") or "未知"
