"""1 · niri 合成器层：从 `binds {}` 解析，并用证据链逐条判定能否按出。"""

from __future__ import annotations

from .. import devices as devmod
from .. import evidence as evmod
from .. import hid as hidmod
from .. import kdl
from ..config import Config, niri_available
from .base import ACTIVE, Collector, LayerResult, Row

PREFIX = "1 · niri 合成器层"


class NiriLayer(Collector):
    name = PREFIX

    def __init__(self, cfg: Config):
        self.cfg = cfg

    def available(self) -> bool:
        return niri_available(self.cfg)

    def collect(self) -> LayerResult:
        if not self.available():
            return LayerResult(self.name, skipped=f"没找到 {self.cfg.niri_config}")

        binds = kdl.parse_file(self.cfg.niri_config)
        merged = kdl.merge(binds)

        report = devmod.read_devices()
        fingerprint = devmod.device_fingerprint()
        evidence = evmod.load(self.cfg, fingerprint)
        hid_devs = hidmod.analyse()

        rows: list[Row] = []
        for combo, b in merged.items():
            main = b.main
            keycaps = [kdl.KEYMAP[m][2] for m in b.mods]

            if main in kdl.KEYMAP:
                keycaps.append(kdl.KEYMAP[main][2])
                code = kdl.KEYMAP[main][0]
                main_zh = kdl.KEYMAP[main][1]
                v = evmod.judge(main, evidence=evidence, hid_devices=hid_devs,
                                keyboard=report, keycode=code)
            elif main in kdl.MOUSE_KEYS:
                keycaps.append(kdl.MOUSE_CAP[main])
                main_zh = kdl.MOUSE_ZH[main]
                v = evmod.judge(main, evidence=evidence, hid_devices=hid_devs,
                                keyboard=report, keycode=None, is_mouse=True)
            else:
                main_zh = main
                v = evmod.Verdict(evmod.BAD, "未知键名", "none")

            action = kdl.translate(b.body)
            notes: list[str] = []
            if v.state != evmod.OK:
                notes.append(v.reason)
            for flag in _flags(b):
                notes.append(flag)

            rows.append(Row(
                layer=f"{PREFIX} › {kdl.group_of(combo, action)}",
                keys=keycaps,
                action=action,
                note="；".join(notes),
                status=ACTIVE,
                state=v.state,
                source=b.source,
            ))

        # 按分组顺序排，组内保持配置出现顺序
        order = {g: i for i, g in enumerate(kdl.GROUP_ORDER)}
        rows.sort(key=lambda r: order.get(r.layer.split(" › ")[-1], 99))
        return LayerResult(self.name, rows)


def _flags(b: kdl.Bind) -> list[str]:
    """把 niri 的绑定属性翻成中文备注。"""
    out: list[str] = []
    props = b.text
    import re
    if "allow-when-locked=true" in props:
        out.append("锁屏时也生效")
    if "repeat=false" in props:
        out.append("按住不重复")
    cd = re.search(r"cooldown-ms=(\d+)", props)
    if cd:
        out.append(f"连发限速 {cd.group(1)}ms")
    if "allow-inhibiting=false" in props:
        out.append("应用接管按键时仍生效")
    if b.overrides:
        import os
        out.append(f"覆盖了 {os.path.basename(b.overrides)} 中的同名绑定")
    return out


def keyboard_summary(cfg: Config) -> tuple[str, str]:
    """(键盘名, 指纹)，给报告头部用。"""
    report = devmod.read_devices()
    return report.name_text(), devmod.device_fingerprint()
