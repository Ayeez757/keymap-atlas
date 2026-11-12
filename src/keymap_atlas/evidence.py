"""证据层：把「这个键到底能不能按出来」的判定依据排成一条优先级链。

优先级（高 → 低）：
  1. observed  用探针**实测按出**过的 keysym        → ✅ 可按
  2. hid       HID 描述符显式声明（且不是泛型全范围）→ ✅ 可按
  3. absent    用户明确标记「我这键盘没有这个键」    → ⛔ 按不出
  4. hid       HID 描述符**有这一页**却没覆盖        → ⛔ 按不出
  5. acpi      固件/ACPI 按键接口上报它               → ✅ 可按（未实测）
  6. hid       只被泛型全范围覆盖 / 窄范围覆盖        → ❓ 存疑
  7. bitmap    /proc KEY 位图声称有（最弱证据）       → ✅ 但标注「未实测」

这样修掉了三个真实误判：
  · Consumer Control 的通用数组让 /proc 声称「有音量键」，实机按不出；
  · PrintScreen 在 evdev 是 KEY_SYSRQ(99) 而非 210，位图里 210 是 Consumer
    接口声明的假象；
  · 笔记本的亮度/音量键根本不经过键盘 HID 描述符，而是 ACPI 单独上报，
    拿「描述符里没写」去断言「键不存在」是错的（见第 4 步与 acpi 证据）。

证据文件带键盘指纹：换键盘后旧记录**不删除**，只降级为「旧键盘记录」，
避免用户在键盘之间来回换时反复丢掉实测结果（见 PRD：键盘会换）。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from . import hid as hidmod
from .config import Config
from .devices import KeyboardReport

OK, BAD, UNKNOWN = "ok", "bad", "unknown"

STATE_LABEL = {OK: "✅ 可按", BAD: "⛔ 按不出", UNKNOWN: "❓ 存疑"}


@dataclass
class Verdict:
    state: str
    reason: str
    source: str            # observed / hid / absent / bitmap / none

    @property
    def icon(self) -> str:
        return {"ok": "✅", "bad": "⛔", "unknown": "❓"}[self.state]


def _read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return {}


def _write_json(p: Path, obj: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1))


@dataclass
class Evidence:
    """一处证据 = 一组 keysym + 它们属于哪把键盘。"""

    observed: set[str] = field(default_factory=set)
    absent: set[str] = field(default_factory=set)
    observed_stale: set[str] = field(default_factory=set)   # 属于旧键盘的实测
    fingerprint: str = ""

    def is_stale(self, keysym: str) -> bool:
        return keysym in self.observed_stale


def load(cfg: Config, fingerprint: str = "") -> Evidence:
    """读取实测与人工标记，并按键盘指纹区分「当前键盘」与「旧键盘」。

    兼容旧路径 ~/.config/shortcut-keyboard-{notes,probe}.json。
    """
    ev = Evidence(fingerprint=fingerprint)

    notes = _read_json(cfg.notes_path) if cfg.notes_path.exists() else {}
    if not notes and cfg.legacy_notes().exists():
        notes = _read_json(cfg.legacy_notes())

    probe = _read_json(cfg.probe_path) if cfg.probe_path.exists() else {}
    if not probe and cfg.legacy_probe().exists():
        probe = _read_json(cfg.legacy_probe())

    ev.absent = set(notes.get("absent", []))

    observed = set(probe.get("observed", []))
    probe_fp = probe.get("fingerprint", "")
    # 没有指纹（旧格式）视为当前键盘，宁可多信一点也不丢用户数据；
    # 有指纹且与当前不符 → 记为 stale，降级展示而不是删除。
    if probe_fp and fingerprint and probe_fp != fingerprint:
        ev.observed_stale = observed
    else:
        ev.observed = observed
    return ev


def save_probe(cfg: Config, observed: set[str], fingerprint: str) -> Path:
    cfg.ensure_state_dir()
    _write_json(cfg.probe_path, {
        "observed": sorted(observed),
        "fingerprint": fingerprint,
        "updated": datetime.now().isoformat(timespec="seconds"),
    })
    return cfg.probe_path


def save_notes(cfg: Config, absent: set[str]) -> Path:
    cfg.ensure_state_dir()
    _write_json(cfg.notes_path, {
        "absent": sorted(absent),
        "updated": datetime.now().isoformat(timespec="seconds"),
    })
    return cfg.notes_path


def clear_stale(cfg: Config, fingerprint: str) -> int:
    """丢弃属于旧键盘的实测记录，返回丢弃条数。"""
    probe = _read_json(cfg.probe_path)
    probe_fp = probe.get("fingerprint", "")
    if probe_fp and fingerprint and probe_fp != fingerprint:
        n = len(probe.get("observed", []))
        cfg.probe_path.unlink(missing_ok=True)
        return n
    return 0


def judge(keysym: str,
          *,
          evidence: Evidence,
          hid_devices: list[hidmod.HidDevice] | None,
          keyboard: KeyboardReport | None,
          keycode: int | None,
          is_mouse: bool = False) -> Verdict:
    """按优先级链给单个 keysym 下结论。

    hid_devices / keyboard 传 None 表示「这台机器读不到」，对应证据跳过，
    而不是当成「没有」。
    """
    if is_mouse:
        if keyboard is None:
            return Verdict(UNKNOWN, "读不到 input 设备", "none")
        if keyboard.mouse_wheel:
            return Verdict(OK, "检测到滚轮", "bitmap")
        return Verdict(BAD, "未检测到鼠标滚轮", "bitmap")

    # 1. 实测按出（当前键盘）
    if keysym in evidence.observed:
        return Verdict(OK, "已实测按出", "observed")

    # 2. HID 描述符显式声明
    hv = hidmod.VERDICT_UNKNOWN
    hv_reason = ""
    if hid_devices is not None and keysym in hidmod.KEYSYM_USAGE:
        hv, hv_reason = hidmod.verdict(keysym, hid_devices)
        if hv == hidmod.VERDICT_YES:
            return Verdict(OK, hv_reason, "hid")

    # 3. 用户标记「没有」
    if keysym in evidence.absent:
        return Verdict(BAD, "你标记为「本机键盘没有这个键」", "absent")

    # 4. HID 描述符里有这一页、但确实没覆盖
    if hv == hidmod.VERDICT_NO:
        return Verdict(BAD, hv_reason, "hid")

    # 5. 固件 / ACPI 按键接口上报它
    #    笔记本的亮度、音量、触摸板键常常不经过键盘的 HID 描述符，而是由
    #    Intel HID events / Ideapad extra buttons / Video Bus 这类接口单独上报。
    #    这些接口的键位写死在 ACPI 表里，不是 HID 通用数组，位图可信。
    if keycode is not None and keyboard is not None:
        owners = keyboard.acpi.get(keycode)
        if owners:
            src = "、".join(sorted(set(owners)))
            return Verdict(OK, f"由固件接口上报（{src}），未实测", "acpi")

    # 6. 旧键盘的实测记录：不是否定，只是提示存疑
    if keysym in evidence.observed_stale:
        return Verdict(UNKNOWN, "实测记录来自换键盘之前的旧键盘，请重跑 probe", "observed")

    # 7. HID 存疑 / 窄范围
    #    普通按键（字母、数字、F 键、方向键、修饰键）只被通用数组覆盖是**正常的**——
    #    几乎所有 USB 键盘都这么写描述符。这种键继续走 /proc 位图（位图对它们可信，
    #    因为矩阵里必然包含）；只有 XF86 媒体键/亮度键才真正无法从文件判定。
    if hv == hidmod.VERDICT_UNKNOWN:
        if keysym.startswith("XF86") or keycode is None:
            return Verdict(UNKNOWN, hv_reason or "文件层面无法判定，需实测", "hid")
        # 落到第 8 步用位图判定，但备注里保留「描述符未点名」这一事实
        hv = hidmod.VERDICT_UNKNOWN
    elif hv == hidmod.VERDICT_MAYBE:
        return Verdict(OK, hv_reason + "（未实测）", "hid")

    # 8. 最弱证据：/proc KEY 位图
    if keycode is not None and keyboard is not None:
        if keycode in keyboard.union:
            if keysym.startswith("XF86"):
                return Verdict(UNKNOWN,
                               "媒体键；能力位图来自通用数组不可信，未实测", "bitmap")
            return Verdict(OK, "按键矩阵里有（未实测）", "bitmap")
        return Verdict(BAD, "键盘按键矩阵里没有这个键", "bitmap")

    return Verdict(UNKNOWN, "缺少判定依据", "none")


def summarize(verdicts: list[Verdict]) -> dict[str, int]:
    out = {OK: 0, BAD: 0, UNKNOWN: 0}
    for v in verdicts:
        out[v.state] = out.get(v.state, 0) + 1
    return out
