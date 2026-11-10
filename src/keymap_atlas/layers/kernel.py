"""4 · 内核 / 硬件层：logind 的电源键策略、SysRq、VT 切换。

这些不是「某个人设的快捷键」，而是内核和 logind 在更底层决定的行为：
按电源键时内核先产生 KEY_POWER，logind 依据 `HandlePowerKey=` 决定做什么。
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..config import Config, kernel_available
from .base import Collector, LayerResult, Row

PREFIX = "4 · 内核 / 硬件层"

# logind 属性 → 中文；值是动作名 → 中文
HANDLE_ZH = {
    "HandlePowerKey": "按下电源键",
    "HandlePowerKeyLongPress": "长按电源键",
    "HandleSuspendKey": "按下睡眠键",
    "HandleSuspendKeyLongPress": "长按睡眠键",
    "HandleHibernateKey": "按下休眠键",
    "HandleHibernateKeyLongPress": "长按休眠键",
    "HandleRebootKey": "按下重启键",
    "HandleRebootKeyLongPress": "长按重启键",
    "HandleLidSwitch": "合上笔记本盖子",
    "HandleLidSwitchExternalPower": "合盖（接电源时）",
    "HandleLidSwitchDocked": "合盖（已接扩展坞时）",
}

ACTION_ZH = {
    "poweroff": "关机", "suspend": "睡眠",
    "hibernate": "休眠", "hybrid-sleep": "混合睡眠",
    "suspend-then-hibernate": "先睡眠后休眠",
    "reboot": "重启", "ignore": "不做任何事",
    "lock": "锁屏", "kexec": "kexec 重启", "halt": "停机关电源",
    "soft": "软休眠", "factory-reset": "恢复出厂",
}

SYS_RQ_ZH = {
    "b": "立即重启（不卸载、不同步）", "c": "触发内核崩溃转储",
    "e": "向所有进程发 SIGTERM", "f": "调用 OOM killer",
    "i": "向所有进程发 SIGKILL", "k": "安全访问键（SAK）",
    "l": "显示所有 CPU 栈回溯", "m": "导出内存信息到控制台",
    "o": "关机（不卸载、不同步）", "p": "导出寄存器与标志",
    "q": "显示所有定时器", "r": "从键盘模式切回 XLATE",
    "s": "同步所有已挂载文件系统", "t": "显示所有任务",
    "u": "重新挂载为只读", "w": "显示阻塞态任务",
    "h": "显示帮助", "n": "设置实时优先级（nice）",
    "j": "解冻文件系统", "d": "显示已持有的锁",
    "x": "在 xmonad 中使用（架构相关）",
    "z": "导出 ftrace 缓冲",
}

DEFAULT_LOGIND = {
    "HandlePowerKey": "poweroff",
    "HandleSuspendKey": "suspend",
    "HandleHibernateKey": "hibernate",
    "HandleRebootKey": "reboot",
    "HandleLidSwitch": "suspend",
    "HandlePowerKeyLongPress": "ignore",
}


def _busctl_props() -> dict[str, str]:
    """读 logind 的 Handle* 属性。失败就用 systemd 出厂默认。"""
    if not shutil.which("busctl"):
        return dict(DEFAULT_LOGIND)
    got: dict[str, str] = {}
    for prop in HANDLE_ZH:
        try:
            r = subprocess.run(
                ["busctl", "get-property", "org.freedesktop.login1",
                 "/org/freedesktop/login1", "org.freedesktop.login1.Manager", prop],
                capture_output=True, text=True, timeout=4,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if r.returncode == 0 and r.stdout.strip():
            val = r.stdout.strip().strip('"')
            if val:
                got[prop] = val
    return got or dict(DEFAULT_LOGIND)


def sysrq_mask() -> int | None:
    p = Path("/proc/sys/kernel/sysrq")
    try:
        return int(p.read_text().strip())
    except (OSError, ValueError):
        return None


class KernelLayer(Collector):
    name = PREFIX

    def __init__(self, cfg: Config):
        self.cfg = cfg

    def available(self) -> bool:
        return kernel_available(self.cfg)

    def collect(self) -> LayerResult:
        if not self.available():
            return LayerResult(self.name, skipped="没有 /proc/sys/kernel/sysrq 或 busctl")

        rows: list[Row] = []

        for prop, action in sorted(_busctl_props().items()):
            zh = HANDLE_ZH.get(prop)
            if not zh:
                continue
            act_zh = ACTION_ZH.get(action, action)
            note = f"logind 的 {prop}={action}"
            if action == "ignore":
                note += "（用户自定义时常见：不响应）"
            rows.append(Row(
                layer=f"{PREFIX} › 电源与盖子",
                keys=["电源键"] if "Power" in prop else ["合盖"],
                action=f"{zh} → {act_zh}",
                note=note,
                source="busctl org.freedesktop.login1.Manager",
            ))

        mask = sysrq_mask()
        if mask is not None:
            rows.append(Row(
                layer=f"{PREFIX} › 紧急救援（SysRq）",
                keys=["Alt", "SysRq", "?"],
                action="直接触发内核级操作",
                note=(f"当前 /proc/sys/kernel/sysrq={mask}："
                      + ("全部 SysRq 功能已启用" if mask & 1 else
                         "只允许同步等少数功能（写不了文件系统）")),
                source="/proc/sys/kernel/sysrq",
            ))
            for key in ("b", "o", "s", "u", "e", "i", "k", "r"):
                if not (mask & 1) and key not in ("s", "u"):
                    continue
                rows.append(Row(
                    layer=f"{PREFIX} › 紧急救援（SysRq）",
                    keys=["Alt", "SysRq", key.upper()],
                    action=SYS_RQ_ZH.get(key, key),
                    note="SysRq 组合：内核直接处理，绕过所有用户态程序",
                    source="/proc/sys/kernel/sysrq",
                ))

        rows.append(Row(
            layer=f"{PREFIX} › 虚拟终端（VT）",
            keys=["Ctrl", "Alt", "F1 … F12"],
            action="切换到内核虚拟终端 tty1–tty12",
            note="内核 vt 子系统处理；tty1 通常是没有图形界面时的登录终端",
            source="drivers/tty/vt",
        ))
        rows.append(Row(
            layer=f"{PREFIX} › 虚拟终端（VT）",
            keys=["Ctrl", "Alt", "F7"],
            action="切回图形界面所在的 VT",
            note="多数发行版图形会话在 tty2 或 tty1，不确定时按 Ctrl+Alt+F1/F2 试",
            source="drivers/tty/vt",
        ))
        return LayerResult(self.name, rows)
