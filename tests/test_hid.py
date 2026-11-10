"""HID 描述符解析。

核心断言是「能不能区分三种情况」：
  · 显式列举了 usage → 一定有
  · 只被泛型全范围（umin=0 且跨度大）覆盖 → 文件层面无法判定，必须实测
  · 完全没覆盖 → 一定没有
这个区分正是整个项目「不要相信 /proc 位图」的技术依据。
"""

from __future__ import annotations

import unittest
from pathlib import Path

from keymap_atlas import hid

FIXTURES = Path(__file__).parent / "fixtures"


class TestItemEncoding(unittest.TestCase):
    def test_type_bits(self):
        # HID item 首字节：位0-1 长度，位2-3 类型，位4-7 tag
        self.assertEqual(hid.HID_MAIN, 0)
        self.assertEqual(hid.HID_GLOBAL, 1)
        self.assertEqual(hid.HID_LOCAL, 2)

    def test_input_item_is_main(self):
        # 0x80 = 长度 0(位0-1=00) 类型 0(位2-3=00) tag 0x8 → Input
        b = 0x80
        self.assertEqual((b >> 2) & 0x3, hid.HID_MAIN)
        self.assertEqual(b >> 4, 0x8)


class TestKeyboardDescriptor(unittest.TestCase):
    """hidraw0：67 字节，键盘页声明 0xe0-0xe7 + 泛型 0x00-0xff。"""

    def setUp(self):
        data = (FIXTURES / "hidraw0.bin").read_bytes()
        self.fields = hid.HIDParse(data)

    def test_parses_fields(self):
        # 这把键盘只声明范围、不点名 usage，所以字段要落在 ranges 里而不是 usages 里
        self.assertTrue(self.fields.fields)
        self.assertTrue(self.fields.ranges(0x07))
        self.assertEqual(self.fields.usages(0x07), set())

    def test_generic_keyboard_range(self):
        ranges = self.fields.keyboard_ranges()
        self.assertTrue(any(a == 0 and b >= 0x80 for a, b in ranges),
                        f"应有一段泛型全范围，实际 {ranges}")

    def test_modifier_range(self):
        ranges = self.fields.keyboard_ranges()
        self.assertTrue(any(a == 0xE0 and b == 0xE7 for a, b in ranges),
                        f"应声明 0xe0-0xe7 修饰键，实际 {ranges}")

    def test_no_explicit_print(self):
        # 关键事实：这把键盘的描述符**没有**点名任何一个具体按键
        self.assertNotIn(0x46, self.fields.keyboard_usages())


class TestConsumerDescriptor(unittest.TestCase):
    """hidraw1：317 字节，Consumer 页泛型 0x0-0x2ff，键盘页窄范围 0x0-0x67。"""

    def setUp(self):
        data = (FIXTURES / "hidraw1.bin").read_bytes()
        self.fields = hid.HIDParse(data)

    def test_consumer_generic(self):
        ranges = self.fields.consumer_ranges()
        self.assertTrue(any(a == 0 and b >= 0x100 for a, b in ranges),
                        f"Consumer 应有泛型全范围，实际 {ranges}")

    def test_keyboard_range_is_not_generic(self):
        for a, b in self.fields.keyboard_ranges():
            if a == 0 and b >= 0x80:
                self.fail(f"键盘页不该出现泛型全范围：{a:#x}-{b:#x}")


class TestVerdict(unittest.TestCase):
    def setUp(self):
        self.devices = [
            hid.HIDParse((FIXTURES / "hidraw0.bin").read_bytes()),
            hid.HIDParse((FIXTURES / "hidraw1.bin").read_bytes()),
        ]

    def test_plain_letter_is_unknown_not_no(self):
        # A 在泛型全范围里 → unk（不能断言有，也不能断言没有）
        v, _ = hid.verdict("A", self.devices)
        self.assertEqual(v, hid.VERDICT_UNKNOWN)

    def test_print_plain(self):
        v, why = hid.verdict("Print", self.devices)
        self.assertIn(v, {hid.VERDICT_UNKNOWN, hid.VERDICT_YES, hid.VERDICT_NO})
        self.assertTrue(why)

    def test_unknown_keysym_is_unknown(self):
        v, why = hid.verdict("NotAKey", self.devices)
        self.assertEqual(v, hid.VERDICT_UNKNOWN)
        self.assertIn("对照表", why)

    def test_no_devices_means_unknown(self):
        v, _ = hid.verdict("XF86AudioRaiseVolume", [])
        self.assertEqual(v, hid.VERDICT_UNKNOWN)

    def test_generic_range_flag(self):
        f = hid.Field(page=0x0C, usages=set(), umin=0, umax=0x3FF,
                      count=1, size=16, report_id=0, flags=0)
        self.assertTrue(f.is_generic_range)
        f2 = hid.Field(page=0x0C, usages=set(), umin=0xE0, umax=0xE7,
                       count=1, size=1, report_id=0, flags=0)
        self.assertFalse(f2.is_generic_range)


class TestKeysymUsage(unittest.TestCase):
    def test_print_usage(self):
        self.assertEqual(hid.KEYSYM_USAGE["Print"], (0x07, 0x46))

    def test_volume_usage(self):
        self.assertEqual(hid.KEYSYM_USAGE["XF86AudioRaiseVolume"], (0x0C, 0xE9))
        self.assertEqual(hid.KEYSYM_USAGE["XF86AudioLowerVolume"], (0x0C, 0xEA))

    def test_letters_start_at_a(self):
        self.assertEqual(hid.KEYSYM_USAGE["A"], (0x07, 0x04))
        self.assertEqual(hid.KEYSYM_USAGE["Z"], (0x07, 0x1D))

    def test_digits(self):
        self.assertEqual(hid.KEYSYM_USAGE["1"], (0x07, 0x1E))
        self.assertEqual(hid.KEYSYM_USAGE["0"], (0x07, 0x27))

    def test_function_keys(self):
        self.assertEqual(hid.KEYSYM_USAGE["F1"], (0x07, 0x3A))
        self.assertEqual(hid.KEYSYM_USAGE["F12"], (0x07, 0x45))


if __name__ == "__main__":
    unittest.main()
