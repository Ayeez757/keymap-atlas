"""从 /proc/bus/input/devices 读取键盘能力，并算出键盘指纹。

为什么需要这一层：一台机器上往往有好几个「键盘」接口
（内置 PS/2、外接 2.4G Dongle、Consumer Control、System Control、触摸板…），
早期版本「取第一个有 LED 且在 kbd handler 内的设备」会选错设备，
导致所有「这个键有没有」的判断都建立在别人身上。这里改成：

  · is_keyboard_matrix() 用多个必要条件一起筛，排除 Consumer/鼠标/电源键；
  · read_devices() 对**所有**键盘矩阵取并集，并记录每个键码来自哪把键盘；
  · device_fingerprint() 只依赖设备名/vid/pid/键数，稳定且能感知插拔。

注意：KEY 位图会把 HID「通用全范围数组」宽化成「这个键存在」，
所以这里只能作为**弱证据**；强证据见 evidence.py。
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

PROC_DEVICES = Path("/proc/bus/input/devices")

# 字母数字区键码（evdev），用来判断这块接口是不是真能打字
ALPHA_KEYS = list(range(2, 12)) + [
    16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
    30, 31, 32, 33, 34, 35, 36, 37, 38,
    44, 45, 46, 47, 48, 49, 50,
]

MOD_KEYS = {
    29: "左Ctrl", 42: "左Shift", 56: "左Alt", 125: "左Super",
    97: "右Ctrl", 54: "右Shift", 100: "右Alt", 126: "右Super",
}


@dataclass
class Device:
    name: str
    vendor: str = "0000"
    product: str = "0000"
    bus: str = "0000"
    phys: str = ""
    key: set[int] = field(default_factory=set)
    has_led: bool = False
    handlers: str = ""
    ev: int = 0
    rel: set[int] = field(default_factory=set)


def decode_bitmap(s: str) -> set[int]:
    """/proc 里 KEY= 位图是「64 位一组、高位在前」的十六进制串。

    例：`KEY=70000 0 0 ...` 这种写法也要能吃。
    """
    words = [int(x, 16) for x in s.split()]
    n = len(words)
    bits: set[int] = set()
    for i, w in enumerate(words):
        shift = (n - 1 - i) * 64
        for b in range(64):
            if (w >> b) & 1:
                bits.add(shift + b)
    return bits


def device_blocks(text: str | None = None) -> list[Device]:
    """把 /proc/bus/input/devices 解析成结构化块列表。

    text 参数只为测试注入用；默认读真实 /proc。
    """
    if text is None:
        try:
            text = PROC_DEVICES.read_text()
        except OSError:
            return []

    out: list[Device] = []
    for blk in text.strip().split("\n\n"):
        if not blk.strip():
            continue

        def g(pat: str, grp: int = 1) -> str | None:
            m = re.search(pat, blk, re.M)
            if not m:
                return None
            # 无捕获组的正则直接取 group(0)，避免 IndexError
            return m.group(grp) if m.groups() else m.group(0)

        name = g(r'^N: Name="(.*)"')
        if not name:
            continue
        key = g(r"^B: KEY=(.*)$")
        rel = g(r"^B: REL=(.*)$")
        ev = g(r"^B: EV=(.*)$")
        out.append(Device(
            name=name,
            vendor=g(r"Vendor=(\w+)") or "0000",
            product=g(r"Product=(\w+)") or "0000",
            bus=g(r"^I: Bus=(\w+)") or "0000",
            phys=g(r"^P: Phys=(.*)$") or "",
            key=decode_bitmap(key) if key else set(),
            has_led=bool(g(r"^B: LED=(.*)$")),
            handlers=g(r"^H: Handlers=(.*)$") or "",
            ev=int(ev, 16) if ev else 0,
            rel=decode_bitmap(rel) if rel else set(),
        ))
    return out


def is_keyboard_matrix(d: Device) -> bool:
    """判断某个 input 接口是不是「真正能打字的键盘矩阵」。

    条件：有 LED 能力（Caps/Num 灯）+ 不是按键式设备 + 字母区覆盖够多
    + 至少含 3 个修饰键。这能排除 Consumer Control / System Control /
    触摸板 / 鼠标 / 电源键这些同样带 KEY 位图的接口。
    """
    if not d.key or not d.has_led:
        return False
    if "button" in d.handlers:
        return False
    alpha = sum(1 for c in ALPHA_KEYS if c in d.key)
    mods = sum(1 for c in MOD_KEYS if c in d.key)
    return alpha >= 20 and mods >= 3


def is_acpi_button_device(d: Device) -> bool:
    """判断某个接口是不是「固件/ACPI 上报的功能键接口」。

    典型名字：Intel HID events、Intel HID 5 button array、Ideapad extra buttons、
    Video Bus、某机型自带的 HotKeys。特征：
      · 挂在 kbd handler 下（所以会向合成器发送按键事件）；
      · 不是真正的键盘矩阵（不能打字，没有 LED）；
      · 有自己的 KEY 位图。

    它们的键位是 ACPI 表里写死的，不是 HID 通用数组，所以位图**可信**——
    这和真正键盘矩阵的情况刚好相反。笔记本的亮度键常常只出现在这里，
    键盘的 HID 描述符里根本没有。
    """
    if not d.key or is_keyboard_matrix(d):
        return False
    return "kbd" in d.handlers


@dataclass
class KeyboardReport:
    union: set[int]
    names: list[str]
    aux: list[str]
    mouse_wheel: bool
    providers: dict[int, list[str]]
    # ACPI / 固件按键接口（Intel HID events、Ideapad extra buttons、Video Bus…）
    # 这些接口不上报打字键，只上报亮度、音量、触摸板这类功能键。
    # 键位由固件写死（不是 HID 通用数组），所以它们的能力位图是可信的。
    acpi: dict[int, list[str]] = field(default_factory=dict)

    def name_text(self) -> str:
        return "、".join(self.names) or "未检测到"

    def acpi_text(self) -> str:
        return "、".join(sorted({n for ns in self.acpi.values() for n in ns}))


def read_devices(verbose: bool = False, text: str | None = None) -> KeyboardReport:
    """每次调用都重新读 /proc，多把键盘取并集。

    返回值里的 providers 记录每个键码来自哪些键盘，方便在报告里说明
    「这个键来自外接键盘」之类的信息。
    """
    blocks = device_blocks(text)
    mats = [d for d in blocks if is_keyboard_matrix(d)]

    union: set[int] = set()
    providers: dict[int, list[str]] = {}
    for d in mats:
        union |= d.key
        for c in d.key:
            providers.setdefault(c, []).append(d.name.strip())

    aux = [d.name for d in blocks
           if "Consumer Control" in d.name or "System Control" in d.name]

    acpi: dict[int, list[str]] = {}
    for d in blocks:
        if not is_acpi_button_device(d):
            continue
        for c in d.key:
            acpi.setdefault(c, []).append(d.name.strip())

    mouse_wheel = any(
        (8 in d.rel and "mouse" in d.handlers) or (8 in d.rel and "kbd" not in d.handlers)
        for d in blocks
    )

    names = [d.name.strip() for d in mats]
    if verbose:
        print("检测到的键盘矩阵：")
        for d in mats:
            print(f"  - {d.name} (bus {d.bus} {d.vendor}:{d.product}, {len(d.key)} 键)")
        if acpi:
            print("检测到的固件/ACPI 按键接口：")
            for d in blocks:
                if is_acpi_button_device(d):
                    print(f"  - {d.name} ({len(d.key)} 键)")

    return KeyboardReport(union=union, names=names, aux=aux,
                          mouse_wheel=mouse_wheel, providers=providers,
                          acpi=acpi)


def fingerprint_of(devices: list[Device]) -> str:
    mats = sorted((d.name.strip(), d.vendor, d.product, len(d.key))
                  for d in devices if is_keyboard_matrix(d))
    return hashlib.sha1(repr(mats).encode()).hexdigest()[:16]


def device_fingerprint(text: str | None = None) -> str:
    """键盘指纹：设备名 + vid/pid + 键码数的哈希。

    用途：换键盘 / 插拔后判断是否需要重建索引；也用来判断旧实测记录
    是不是属于当前这把键盘（见 evidence.py）。
    """
    return fingerprint_of(device_blocks(text))
