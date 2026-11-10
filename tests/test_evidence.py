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

    def test_hid_no_coverage_is_bad(self):
        """描述符完全没有 Consumer 页 → 媒体键一定按不出。"""
        devs = [descriptor_with_usage(0x07, 0x04)]
        v = self.judge("XF86AudioRaiseVolume", 115, hid_devices=devs)
        self.assertEqual(v.state, ev.BAD)
        self.assertEqual(v.source, "hid")

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
