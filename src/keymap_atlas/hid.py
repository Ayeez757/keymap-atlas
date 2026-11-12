"""只读解析 HID 报告描述符：不解开键盘就能算出「哪些键真的存在」。

原理：一个键能不能按出来，取决于 HID 报告描述符里是否真的声明了那个
Usage。`/proc/bus/input/devices` 的 KEY 位图是内核把描述符「宽化」后的结果：
遇到 `Usage Minimum=0x00, Usage Maximum=0x3C` 这种通用全范围数组，内核会把
**整个区间**都标成「有这个键」。这就是「明明没有音量键，报告却列出来」的根因。

直接读 /sys/class/hidraw/hidraw*/device/report_descriptor 只读、无需 root、
无需按键，解析出每个 Input 报告的 Usage 范围，就能得到准确得多的答案。

HID item 编码（踩过坑，写清楚）：b0 位 0-1 = 数据长度(0/1/2/4)，
位 2-3 = 类型（0=Main, 1=Global, 2=Local），位 4-7 = tag。
早期版本把类型搞反写成 1=Input，导致解析结果全空。
"""

from __future__ import annotations

import glob
import os
from dataclasses import dataclass, field
from pathlib import Path

HIDRAW_GLOB = "/sys/class/hidraw/hidraw*"

HID_MAIN, HID_GLOBAL, HID_LOCAL = 0, 1, 2

USAGE_PAGE = {
    0x01: "Generic Desktop", 0x07: "Keyboard/Keypad", 0x08: "LED",
    0x09: "Button", 0x0B: "Telephony", 0x0C: "Consumer", 0x0D: "Digitizer",
    0xFF00: "Vendor",
}


def page_name(p: int | None) -> str:
    if p is None:
        return "?"
    return USAGE_PAGE.get(p) or USAGE_PAGE.get(p & 0xFF00) or f"0x{p:04x}"


@dataclass
class Field:
    page: int | None
    usages: set[int]
    umin: int | None
    umax: int | None
    count: int | None
    size: int | None
    report_id: int | None
    flags: int

    @property
    def is_generic_range(self) -> bool:
        """从 0x00 起步、跨度很大的范围数组 —— 内核会据此谎报所有键。"""
        return (self.umin == 0 and self.umax is not None and self.umax > 0x80)


class HIDParse:
    """迷你 HID 描述符解析器，只提取「每个 Input 项声明了哪些 usage」。"""

    def __init__(self, data: bytes):
        self.d = data
        self.fields: list[Field] = []
        self.parse()

    def parse(self) -> None:
        d, i = self.d, 0
        g = {"page": None, "usize": None, "ucount": None, "report_id": None}
        loc = self._reset_local()

        while i < len(d):
            b = d[i]
            i += 1
            if b == 0xFE:                     # long item
                sz = d[i] if i < len(d) else 0
                i += 2 + sz
                continue
            n = b & 0x03
            n = 4 if n == 3 else n
            typ = (b >> 2) & 0x03
            tag = (b >> 4) & 0x0F
            raw = d[i:i + n]
            i += n
            val = int.from_bytes(raw, "little") if raw else 0

            if typ == HID_MAIN:
                if tag == 0x08:               # Input
                    self._add_input(g, loc, val)
                    loc = self._reset_local()
                elif tag in (0x09, 0x0B):     # Output / Feature
                    loc = self._reset_local()
                elif tag == 0x0A:             # Collection
                    # Collection 之前的 Usage 是「集合名」，不是字段。
                    # 例：05 0c 09 01 a1 01 里的 0x01 是 Consumer Control 集合名。
                    loc = self._reset_local()
                elif tag == 0x0C:             # End Collection
                    pass
            elif typ == HID_GLOBAL:
                if tag == 0x00:
                    g["page"] = val
                elif tag == 0x07:
                    g["usize"] = val
                elif tag == 0x08:
                    g["report_id"] = val
                elif tag == 0x09:
                    g["ucount"] = val
            elif typ == HID_LOCAL:
                if tag == 0x00:               # Usage
                    loc["usage"] = val
                    loc["usage_page"] = g["page"]   # usage 归属「声明时」的页
                elif tag == 0x01:
                    loc["umin"] = val
                elif tag == 0x02:
                    loc["umax"] = val

    @staticmethod
    def _reset_local() -> dict:
        return {"usage": None, "usage_page": None, "umin": None, "umax": None,
                "usages": []}

    def _add_input(self, g: dict, loc: dict, flags: int) -> None:
        usages: set[int] = set()
        # 只有「声明时的页」与当前 Input 的页一致，才算显式列举。
        # 例：05 01 09 06 里的 0x06 属于 Generic Desktop，不是键盘页的 C。
        if loc["usage"] is not None and loc.get("usage_page") == g["page"]:
            usages.add(loc["usage"])
        for u in loc["usages"]:
            usages.add(u)
        self.fields.append(Field(page=g["page"], usages=usages,
                                 umin=loc["umin"], umax=loc["umax"],
                                 count=g["ucount"], size=g["usize"],
                                 report_id=g["report_id"], flags=flags))

    def usages(self, page: int) -> set[int]:
        out: set[int] = set()
        for f in self.fields:
            if f.page == page:
                out |= f.usages
        return out

    def ranges(self, page: int) -> list[tuple[int, int]]:
        return [(f.umin, f.umax) for f in self.fields
                if f.page == page and f.umin is not None and f.umax is not None]

    def keyboard_usages(self) -> set[int]:
        return {u for u in self.usages(0x07) if u <= 0xFF}

    def keyboard_ranges(self) -> list[tuple[int, int]]:
        return self.ranges(0x07)

    def consumer_usages(self) -> set[int]:
        return self.usages(0x0C)

    def consumer_ranges(self) -> list[tuple[int, int]]:
        return self.ranges(0x0C)


# ------------------------------------------------------------- 设备关联
@dataclass
class HidDevice:
    hidraw: str
    name: str
    phys: str
    desc_len: int
    kbd_explicit: list[int] = field(default_factory=list)
    kbd_ranges: list[tuple[int, int]] = field(default_factory=list)
    consumer_explicit: list[int] = field(default_factory=list)
    consumer_ranges: list[tuple[int, int]] = field(default_factory=list)
    generic_keyboard: bool = False
    generic_consumer: bool = False
    fields: list[Field] = field(default_factory=list)


def hidraw_info(path: str | Path) -> tuple[str, str]:
    """hidraw 节点 → (设备名, 物理路径)。

    注意 uevent 在 <hidraw>/device/uevent，不是 <hidraw>/uevent。
    """
    base = Path(path)
    name, devpath = "", ""
    for cand in (base / "device" / "uevent", base / "uevent"):
        try:
            for line in cand.read_text().splitlines():
                if line.startswith("HID_NAME="):
                    name = line.split("=", 1)[1].strip()
                elif line.startswith("HID_PHYS="):
                    devpath = line.split("=", 1)[1].strip()
        except OSError:
            continue
        if name:
            break
    return name, devpath


def read_descriptor(hidraw: str) -> bytes | None:
    p = f"/sys/class/hidraw/{hidraw}/device/report_descriptor"
    try:
        return Path(p).read_bytes()
    except OSError:
        return None


def device_from_parse(p: HIDParse, hidraw: str = "test",
                      name: str = "", phys: str = "",
                      desc_len: int = 0) -> HidDevice:
    """HIDParse → HidDevice。analyse() 与测试共用，避免两处各拼一遍字段。"""
    return HidDevice(
        hidraw=hidraw, name=name, phys=phys, desc_len=desc_len,
        kbd_explicit=sorted(p.keyboard_usages()),
        kbd_ranges=p.keyboard_ranges(),
        consumer_explicit=sorted(p.consumer_usages()),
        consumer_ranges=p.consumer_ranges(),
        generic_keyboard=any(u0 == 0 and (u1 - u0) > 0x80 for u0, u1 in p.keyboard_ranges()),
        generic_consumer=any(u0 == 0 and (u1 - u0) > 0x80 for u0, u1 in p.consumer_ranges()),
        fields=p.fields,
    )


def analyse(hidraws: list[str] | None = None) -> list[HidDevice]:
    if hidraws is None:
        hidraws = sorted(glob.glob(HIDRAW_GLOB))
    results: list[HidDevice] = []
    for hw in hidraws:
        hid = os.path.basename(hw)
        data = read_descriptor(hid)
        if not data:
            continue
        name, phys = hidraw_info(hw)
        results.append(device_from_parse(HIDParse(data), hidraw=hid, name=name,
                                         phys=phys, desc_len=len(data)))
    return results


def is_keyboard_like(d: HidDevice) -> bool:
    """描述符里有没有「键盘类」的按键声明。

    厂商页（0xff00/0xffxx）的设备不算——笔记本内置键盘常把整张键表交给
    ACPI，描述符里只剩下厂商页和触摸板页，这种情况必须由别的证据判定。
    """
    return bool(d.kbd_explicit or d.kbd_ranges or d.consumer_ranges)


# --------------------------- keysym → (usage page, usage id) 对照
# 只列「快捷键配置里可能出现」的键，用于 verdict()。
KEYSYM_USAGE: dict[str, tuple[int, int]] = {
    # 字母
    **{c: (0x07, 0x04 + i) for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")},
    # 数字：1=0x1e … 9=0x26，0=0x27（0x1d 是保留位，不能用 0x1E+i）
    **{str(i): (0x07, 0x1D + i) for i in range(1, 10)},
    "0": (0x07, 0x27),
    "Enter": (0x07, 0x28), "Return": (0x07, 0x28),
    "Esc": (0x07, 0x29), "Escape": (0x07, 0x29),
    "Backspace": (0x07, 0x2A), "BackSpace": (0x07, 0x2A),
    "Tab": (0x07, 0x2B), "Space": (0x07, 0x2C),
    "Minus": (0x07, 0x2D), "Equal": (0x07, 0x2E),
    "BracketLeft": (0x07, 0x2F), "BracketRight": (0x07, 0x30),
    "Backslash": (0x07, 0x31), "semicolon": (0x07, 0x33),
    "apostrophe": (0x07, 0x34), "grave": (0x07, 0x35),
    "Comma": (0x07, 0x36), "Period": (0x07, 0x37), "Slash": (0x07, 0x38),
    "Insert": (0x07, 0x49), "Home": (0x07, 0x4A),
    "Page_Up": (0x07, 0x4B), "Delete": (0x07, 0x4C),
    "End": (0x07, 0x4D), "Page_Down": (0x07, 0x4E),
    "Print": (0x07, 0x46),
    **{f"F{i}": (0x07, 0x39 + i) for i in range(1, 13)},   # F1=0x3a … F12=0x45
    # 媒体 / 专用键：实际多走 Consumer 页
    "XF86AudioRaiseVolume": (0x0C, 0xE9),
    "XF86AudioLowerVolume": (0x0C, 0xEA),
    "XF86AudioMute": (0x0C, 0xE2),
    "XF86AudioPlay": (0x0C, 0xB0),
    "XF86AudioPause": (0x0C, 0xB1),
    "XF86AudioStop": (0x0C, 0xB7),
    "XF86AudioNext": (0x0C, 0xB5),
    "XF86AudioPrev": (0x0C, 0xB6),
    "XF86AudioMicMute": (0x0C, 0x80),
    "XF86MonBrightnessUp": (0x0C, 0x6F),
    "XF86MonBrightnessDown": (0x0C, 0x70),
    "XF86Launch1": (0x0C, 0x183),          # 常见映射，可能不适用
    "XF86TouchpadToggle": (0x0C, 0x256),
}

VERDICT_YES, VERDICT_MAYBE, VERDICT_UNKNOWN, VERDICT_NO = "yes", "maybe", "unk", "no"


def verdict(keysym: str, devices: list[HidDevice]) -> tuple[str, str]:
    """返回 (结论, 说明)。

    yes   有接口显式声明了它（基本确定能按出）
    maybe 只落在「窄范围」里（可能能按出，建议实测）
    unk   文件层面无法判定：只被泛型全范围覆盖，或描述符里根本没有这一页
    no    描述符里**有这一页**、但确实没覆盖它（才能断言按不出）

    「没有这一页」和「有这一页但没这个键」是两件事，必须分开：
    不少笔记本的 Fn 行、亮度、音量键根本不经过键盘的 HID 描述符，
    而是由 ACPI（Intel HID events、Ideapad extra buttons、Video Bus）
    单独上报 KEY_BRIGHTNESS*/KEY_VOLUME*。这类设备的描述符里只有厂商页，
    拿「描述符没写」去断言「键不存在」就是误判。
    """
    if not devices:
        # 没有设备 ≠ 所有描述符都没覆盖。读不到就说不确定，别断言「没有」。
        return VERDICT_UNKNOWN, "没有可读的 HID 描述符"
    if keysym not in KEYSYM_USAGE:
        return VERDICT_UNKNOWN, "不在 usage 对照表里"
    page, usage = KEYSYM_USAGE[keysym]
    saw_range = saw_generic = False
    page_owners: list[str] = []
    keyboard_owners: list[str] = []
    for d in devices:
        # 「这一段声明能不能替键盘背书」：只有真的带键盘页 0x07 的描述符才算。
        # 触摸板也声明 Consumer 页（用来上报「手指按下」），它没覆盖某个 usage
        # 不能说键盘上没有这个键。
        kbd_like = any(f.page == 0x07 for f in d.fields)
        for f in d.fields:
            if f.page != page:
                continue
            page_owners.append(getattr(d, "name", "") or getattr(d, "hidraw", "?"))
            if kbd_like:
                keyboard_owners.append(getattr(d, "name", "") or getattr(d, "hidraw", "?"))
            if usage in f.usages:
                return VERDICT_YES, f"{d.hidraw} 显式列举了 usage 0x{usage:02x}"
            if f.umin is not None and f.umax is not None and f.umin <= usage <= f.umax:
                if f.is_generic_range:
                    saw_generic = True
                else:
                    saw_range = True
    if saw_generic:
        return VERDICT_UNKNOWN, "只被泛型全范围覆盖 → 描述符无法判定，需实测"
    if saw_range:
        return VERDICT_MAYBE, "落在窄范围声明内 → 可能能按出，建议实测"
    if not page_owners:
        # 所有描述符都没有这一页。这不能证明键不存在：笔记本的亮度、音量、
        # 触摸板键常常由 ACPI 接口（Intel HID events、Ideapad extra buttons、
        # Video Bus）单独上报，键盘的 HID 描述符里只有厂商页。
        return VERDICT_UNKNOWN, (f"描述符里没有 {page_name(page)} 页"
                                 f"（0x{page:02x}）→ 文件层面无法判定，需实测")
    if keyboard_owners:
        # 这一页确实由键盘类接口声明，而它没覆盖这个 usage → 可以断言按不出。
        return VERDICT_NO, (f"{page_name(page)} 页由 {keyboard_owners[0]} 声明，"
                            f"但没覆盖 usage 0x{usage:02x}")
    # 只有触摸板 / 鼠标这类设备声明了该页。它们各自的使用范围很窄，
    # 不能据此推断键盘上没有这个键。
    return VERDICT_UNKNOWN, (f"{page_name(page)} 页只由 {page_owners[0]} 声明"
                             f"（非键盘设备）→ 需实测")
