"""层级注册表。

层号是**固定**的，不随本机是否装了某个桌面而变——这样同一份报告在不同机器
上对比时层号含义一致（未安装的层标「跳过」，而不是让后面的层号往前挤）。
"""

from __future__ import annotations

from ..config import Config
from .base import ACTIVE, INACTIVE, Collector, LayerResult, Row
from .fcitx import FcitxLayer
from .ghostty import GhosttyLayer
from .gnome import GnomeLayer
from .kde import KdeLayer
from .kernel import KernelLayer
from .niri import NiriLayer

LAYER_CLASSES: tuple[type[Collector], ...] = (
    NiriLayer,
    FcitxLayer,
    GhosttyLayer,
    KernelLayer,
    KdeLayer,
    GnomeLayer,
)

# 7 · 无法静态枚举的层：写清楚「为什么做不到」，避免用户以为漏了
UNLISTABLE = [
    ("Firefox / Chromium / Electron 应用内快捷键",
     "编译进程序或存在 profile 的加密库里，没有统一的导出接口"),
    ("GTK / Qt 的 .ui 文件与代码里的 accel",
     "散布在源码与资源包里，运行期才注册，没有枚举 API"),
    ("键盘固件里的 Fn 组合本身（Fn 是不是硬件层、能不能改）",
     "Fn 由键盘控制器自己处理，操作系统看不到按下 Fn 这个动作；"
     "它发出的功能键码已在内核层的「固件功能键（Fn 行）」里列出"),
    ("浏览器扩展的快捷键",
     "存在各扩展自己的存储里，需要逐个读取扩展数据目录"),
    ("Wayland 的 xdg-desktop-portal GlobalShortcuts",
     "按会话／应用隔离：对其他应用的会话调用 ListShortcuts 会被 Access denied"),
    ("Flatpak / Snap 应用的自定义键",
     "沙箱有自己的配置目录，路径与宿主不同"),
]


def all_layers(cfg: Config) -> list[LayerResult]:
    out: list[LayerResult] = []
    for cls in LAYER_CLASSES:
        layer = cls(cfg)
        try:
            res = layer.collect()
        except Exception as exc:                      # 单层失败不该毁掉整份报告
            res = LayerResult(cls.name, skipped=f"读取失败：{exc}")
        if not res.rows and not res.skipped:
            res.skipped = "没有解析到任何快捷键"
        out.append(res)
    return out


def all_rows(results: list[LayerResult], skip_inactive: bool = False) -> list[Row]:
    rows: list[Row] = []
    for res in results:
        for r in res.rows:
            if skip_inactive and r.status != ACTIVE:
                continue
            rows.append(r)
    return rows


__all__ = [
    "ACTIVE", "INACTIVE", "Collector", "LayerResult", "Row",
    "LAYER_CLASSES", "UNLISTABLE", "all_layers", "all_rows",
]
