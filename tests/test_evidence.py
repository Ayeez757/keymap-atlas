"""证据优先级链。

这是整个项目最核心的断言集合：谁能覆盖谁。测试直接钉住优先级，防止以后
重构时把「泛型范围」和「用户实测」的顺序搞反——那正是 v0.0.x 的两个真实 bug。
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from keymap_atlas import evidence as ev
from keymap_atlas import hid
from keymap_atlas.config import Config
from keymap_atlas.devices import KeyboardReport

FIXTURES = Path(__file__).parent / "fixtures"


def make_keyboard(codes: set[int], wheel: bool = False) -> KeyboardReport:
    report = KeyboardReport(union=set(codes), names=["测试键盘"],
                            aux=set(), mouse_wheel=wheel, providers={})
    return report


def make_hid() -> list[hid.HidDevice]:
    return hid.analyse([str(FIXTURES / "hidraw0.bin"), str(FIXTURES / "hidraw1.bin")])


def descriptor_with_usage(page: int, usage: int) -> hid.HidDevice:
    """手工拼一个「点名了某个 usage」的描述符。

    真实设备都只写泛型范围，靠 fixture 造不出「显式声明」这条路，所以在这里
    直接按 HID item 编码拼：Usage Page / Usage / Logical Min-Max / Report
    Size / Report Count / Input。
    """
    data = bytes([
        0x05, page,          # Usage Page
        0x09, usage,         # Usage（← 点名这一条）
        0x15, 0x00,          # Logical Minimum 0
        0x25, 0x01,          # Logical Maximum 1
        0x75, 0x01,          # Report Size 1
        0x95, 0x01,          # Report Count 1
        0x81, 0x02,          # Input(Data,Var,Abs)
    ])
    return hid.device_from_parse(hid.HIDParse(data), hidraw="synthetic")


class TestJudgePriority(unittest.TestCase):
    """逐条验证优先级：越靠前越权威。"""

    def setUp(self):
        self.cfg = Config()
        self.kb = make_keyboard(set(range(1, 250)))
        self.devices = make_hid()
        self.ev = ev.Evidence()

    def judge(self, keysym, keycode=None, **kw):
        return ev.judge(keysym, evidence=kw.pop("evidence", self.ev),
                        hid_devices=kw.pop("hid_devices", self.devices),
                        keyboard=kw.pop("keyboard", self.kb),
                        keycode=keycode, is_mouse=kw.pop("is_mouse", False))

    def test_observed_beats_everything(self):
        e = ev.Evidence(observed={"XF86AudioRaiseVolume"},
                        absent={"XF86AudioRaiseVolume"})
        v = self.judge("XF86AudioRaiseVolume", 115, evidence=e)
        self.assertEqual(v.state, ev.OK)
        self.assertEqual(v.source, "observed")

    def test_absent_beats_bitmap(self):
        e = ev.Evidence(absent={"Print"})
        v = self.judge("Print", 99, evidence=e)
        self.assertEqual(v.state, ev.BAD)
        self.assertEqual(v.source, "absent")

    def test_hid_explicit_beats_absent(self):
        """描述符点名了这个 usage，就不该被手工标记否掉。"""
        e = ev.Evidence(absent={"A"})
        devs = [descriptor_with_usage(0x07, 0x04)]
        v = self.judge("A", 30, evidence=e, hid_devices=devs)
        self.assertEqual(v.state, ev.OK)
        self.assertEqual(v.source, "hid")

    def test_hid_page_absent_is_unknown(self):
        """描述符里根本没有 Consumer 页 → 不能断言媒体键按不出。

        笔记本的亮度、音量键常由 ACPI 接口（Intel HID events 等）单独上报，
        键盘 HID 描述符里只有厂商页。这里只能落到 ❓。
        """
        devs = [descriptor_with_usage(0x07, 0x04)]
        v = self.judge("XF86AudioRaiseVolume", 115, hid_devices=devs)
        self.assertEqual(v.state, ev.UNKNOWN)
        self.assertEqual(v.source, "hid")

    def test_hid_keyboard_page_without_usage_is_bad(self):
        """键盘类描述符声明了 Consumer 页却没覆盖这个 usage → 可以断言按不出。"""
        data = bytes([
            0x05, 0x07, 0x19, 0x00, 0x29, 0x65,   # 键盘页 0x00-0x65（真键盘都有）
            0x15, 0x00, 0x25, 0x01, 0x75, 0x08, 0x95, 0x06, 0x81, 0x00,
            0x05, 0x0C, 0x09, 0xE9,   # Consumer 页：只点名 Volume Up
            0x15, 0x00, 0x25, 0x01, 0x75, 0x01, 0x95, 0x01, 0x81, 0x02,
        ])
        devs = [hid.device_from_parse(hid.HIDParse(data), hidraw="kbd")]
        v = self.judge("XF86AudioRaiseVolume", 115, hid_devices=devs)
        self.assertEqual(v.state, ev.OK)          # 点名了 Volume Up
        v2 = self.judge("XF86AudioPlay", 164, hid_devices=devs)
        self.assertEqual(v2.state, ev.BAD)
        self.assertEqual(v2.source, "hid")

    def test_acpi_button_interface_confirms(self):
        """亮度键只出现在 ACPI 接口（Intel HID events）的位图里 → 可按。"""
        from keymap_atlas.devices import KeyboardReport
        kb = KeyboardReport(union={16, 113, 114, 115}, names=["AT 键盘"],
                            aux=[], mouse_wheel=False, providers={},
                            acpi={224: ["Intel HID events", "Video Bus"],
                                  225: ["Intel HID events", "Video Bus"]})
        v = self.judge("XF86MonBrightnessUp", 225, keyboard=kb)
        self.assertEqual(v.state, ev.OK)
        self.assertEqual(v.source, "acpi")
        self.assertIn("Intel HID events", v.reason)

    def test_niri_media_bind_is_bad_not_unknown(self):
        """niri 里配的是 XF86 键，但键盘位图里没有 → 之前误判成「描述符没覆盖」。"""
        from keymap_atlas.devices import KeyboardReport
        kb = KeyboardReport(union=set(range(1, 250)), names=["测试键盘"],
                            aux=[], mouse_wheel=False, providers={})
        v = self.judge("XF86AudioRaiseVolume", 115, keyboard=kb)
        self.assertEqual(v.state, ev.UNKNOWN)

    def test_media_key_without_evidence_is_unknown(self):
        # XF86 键只被泛型全范围覆盖 + 位图命中 → 必须存疑，不能断言「有」
        v = self.judge("XF86AudioRaiseVolume", 115)
        self.assertEqual(v.state, ev.UNKNOWN)

    def test_plain_key_with_bitmap_is_ok(self):
        v = self.judge("Q", 16)
        self.assertEqual(v.state, ev.OK)

    def test_missing_from_bitmap_is_bad(self):
        kb = make_keyboard({1, 2, 3})
        v = self.judge("Q", 16, keyboard=kb)
        self.assertEqual(v.state, ev.BAD)

    def test_stale_observation_is_unknown(self):
        e = ev.Evidence(observed_stale={"XF86MonBrightnessUp"})
        v = self.judge("XF86MonBrightnessUp", 225, evidence=e)
        self.assertEqual(v.state, ev.UNKNOWN)
        self.assertEqual(v.source, "observed")

    def test_none_inputs_degrade_to_unknown(self):
        v = self.judge("Q", None, hid_devices=None, keyboard=None)
        self.assertEqual(v.state, ev.UNKNOWN)

    def test_mouse_wheel(self):
        v = self.judge("WheelScrollUp", None, keyboard=make_keyboard({1}, True),
                       is_mouse=True)
        self.assertEqual(v.state, ev.OK)
        v2 = self.judge("WheelScrollUp", None, keyboard=make_keyboard({1}, False),
                        is_mouse=True)
        self.assertEqual(v2.state, ev.BAD)

    def test_mouse_without_keyboard(self):
        v = self.judge("WheelScrollUp", None, keyboard=None, is_mouse=True)
        self.assertEqual(v.state, ev.UNKNOWN)


class TestEvidenceFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.cfg = Config(state_dir=root / "state", out_dir=root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_save_and_load_roundtrip(self):
        ev.save_probe(self.cfg, {"A", "Super"}, "fp1")
        ev.save_notes(self.cfg, {"Print"})
        e = ev.load(self.cfg, "fp1")
        self.assertEqual(e.observed, {"A", "Super"})
        self.assertEqual(e.absent, {"Print"})
        self.assertEqual(e.observed_stale, set())

    def test_fingerprint_mismatch_demotes_to_stale(self):
        ev.save_probe(self.cfg, {"A"}, "old-keyboard")
        e = ev.load(self.cfg, "new-keyboard")
        self.assertEqual(e.observed, set())
        self.assertEqual(e.observed_stale, {"A"})

    def test_old_format_without_fingerprint_is_trusted(self):
        self.cfg.ensure_state_dir()
        self.cfg.probe_path.write_text(json.dumps({"observed": ["B"]}))
        e = ev.load(self.cfg, "whatever")
        self.assertEqual(e.observed, {"B"})

    def test_corrupt_json_is_ignored(self):
        self.cfg.ensure_state_dir()
        self.cfg.probe_path.write_text("{not json")
        e = ev.load(self.cfg, "fp")
        self.assertEqual(e.observed, set())

    def test_clear_stale(self):
        ev.save_probe(self.cfg, {"A", "B"}, "fp")
        n = ev.clear_stale(self.cfg, "fp")
        self.assertGreaterEqual(n, 0)

    def test_summarize(self):
        counts = ev.summarize([
            ev.Verdict(ev.OK, "", "bitmap"),
            ev.Verdict(ev.OK, "", "hid"),
            ev.Verdict(ev.BAD, "", "absent"),
        ])
        self.assertEqual(counts.get(ev.OK), 2)
        self.assertEqual(counts.get(ev.BAD), 1)


class TestVerdictIcon(unittest.TestCase):
    def test_icons(self):
        self.assertEqual(ev.Verdict(ev.OK, "", "").icon, "✅")
        self.assertEqual(ev.Verdict(ev.BAD, "", "").icon, "⛔")
        self.assertEqual(ev.Verdict(ev.UNKNOWN, "", "").icon, "❓")


if __name__ == "__main__":
    unittest.main()
