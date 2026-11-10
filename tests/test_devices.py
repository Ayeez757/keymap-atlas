"""设备矩阵解析与指纹。

用真实 `/proc/bus/input/devices` 的脱敏快照做固定输入，避免测试依赖跑测机器。
"""

from __future__ import annotations

import unittest
from pathlib import Path

from keymap_atlas import devices as dev

FIXTURES = Path(__file__).parent / "fixtures"


class TestDecodeBitmap(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(dev.decode_bitmap(""), set())

    def test_bits(self):
        # 0x8000 = 第 15 位（高位在前，按 8 位一组解析）
        self.assertIn(15, dev.decode_bitmap("8000"))
        self.assertIn(0, dev.decode_bitmap("1"))


class TestDeviceBlocks(unittest.TestCase):
    def setUp(self):
        self.text = (FIXTURES / "proc_input_devices.txt").read_text()
        self.blocks = dev.device_blocks(self.text)

    def test_parses_blocks(self):
        self.assertGreater(len(self.blocks), 10)

    def test_lid_switch_has_no_key(self):
        lid = [b for b in self.blocks if b.name == "Lid Switch"]
        self.assertTrue(lid)
        self.assertEqual(lid[0].key, set())

    def test_at_keyboard_is_matrix(self):
        kb = [b for b in self.blocks if b.name == "AT Translated Set 2 keyboard"]
        self.assertTrue(kb)
        self.assertTrue(dev.is_keyboard_matrix(kb[0]))

    def test_lid_is_not_matrix(self):
        lid = [b for b in self.blocks if b.name == "Lid Switch"][0]
        self.assertFalse(dev.is_keyboard_matrix(lid))

    def test_mouse_is_not_matrix(self):
        for b in self.blocks:
            if "mouse" in b.handlers:
                self.assertFalse(dev.is_keyboard_matrix(b), b.name)


class TestReadDevices(unittest.TestCase):
    def setUp(self):
        self.text = (FIXTURES / "proc_input_devices.txt").read_text()
        self.report = dev.read_devices(text=self.text)

    def test_unions_multiple_keyboards(self):
        self.assertGreaterEqual(len(self.report.names), 2)

    def test_union_superset_of_each(self):
        for b in dev.device_blocks(self.text):
            if dev.is_keyboard_matrix(b):
                self.assertTrue(b.key <= self.report.union, b.name)

    def test_providers_point_back(self):
        for code, names in self.report.providers.items():
            self.assertTrue(names)
            self.assertIn(code, self.report.union)

    def test_mouse_wheel_detected(self):
        self.assertIsInstance(self.report.mouse_wheel, bool)

    def test_name_text_falls_back(self):
        empty = dev.read_devices(text="")
        self.assertEqual(empty.name_text(), "未检测到")
        self.assertEqual(empty.union, set())

    def test_fingerprint_stable_and_16_chars(self):
        a = dev.device_fingerprint(self.text)
        b = dev.device_fingerprint(self.text)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 16)
        int(a, 16)   # 必须是十六进制

    def test_fingerprint_changes_with_devices(self):
        text2 = self.text.replace('N: Name="AT Translated Set 2 keyboard"',
                                  'N: Name="Other Keyboard"')
        self.assertNotEqual(dev.device_fingerprint(self.text),
                            dev.device_fingerprint(text2))


if __name__ == "__main__":
    unittest.main()
