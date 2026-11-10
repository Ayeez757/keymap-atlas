"""KDL 绑定解析与中文翻译。

最需要守住的不变量：include 的层级覆盖语义。niri 按出现顺序解析，后面的
include 覆盖前面的同名键位；测试里用两个文件构造冲突来钉住这一点。
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from keymap_atlas import kdl


class TestStripComment(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(kdl.strip_comment("a b // c").strip(), "a b")

    def test_keeps_slashes_inside_quotes(self):
        s = 'spawn "sh" "-c" "echo http://x"  // 真注释'
        out = kdl.strip_comment(s)
        self.assertIn("http://x", out)
        self.assertNotIn("真注释", out)

    def test_hash_comment(self):
        self.assertNotIn("注释", kdl.strip_comment("a // 注释 # 还是注释"))


class TestIsCombo(unittest.TestCase):
    def test_modifiers_and_keys(self):
        for tok in ["Super+Q", "Mod+Alt+Equal", "Print", "XF86AudioMute", "F1"]:
            self.assertTrue(kdl.is_combo(tok), tok)

    def test_non_combos(self):
        for tok in ["include", "//", "binds", "{", "output"]:
            self.assertFalse(kdl.is_combo(tok), tok)


class TestParseFile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name: str, text: str) -> Path:
        p = self.dir / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_simple_binds(self):
        p = self.write("a.kdl", """
binds {
    Super+Q { close-window; }
    Print { screenshot; }
}
""")
        binds = kdl.parse_file(p)
        combos = [b.combo for b in binds]
        self.assertIn("Super+Q", combos)
        self.assertIn("Print", combos)

    def test_multiline_body_collected(self):
        p = self.write("a.kdl", """
binds {
    Super+T {
        spawn "foot";
        allow-when-locked=true;
    }
}
""")
        b = [x for x in kdl.parse_file(p) if x.combo == "Super+T"][0]
        self.assertIn("spawn", b.text)
        self.assertIn("allow-when-locked", b.text)

    def test_include_is_recursive_and_relative(self):
        self.write("b.kdl", "binds {\n Super+1 { focus-workspace 1; }\n}\n")
        a = self.write("a.kdl", 'include optional=true "b.kdl"\n')
        combos = [b.combo for b in kdl.parse_file(a)]
        self.assertIn("Super+1", combos)

    def test_include_cycle_terminates(self):
        self.write("b.kdl", 'include "a.kdl"\n')
        a = self.write("a.kdl", 'include "b.kdl"\n')
        self.assertEqual(kdl.parse_file(a), [])

    def test_include_after_bind_overrides_in_merge(self):
        """后 include 的文件覆盖先定义的同名键位——niri 的实际语义。"""
        self.write("later.kdl", "binds {\n Super+Q { screenshot; }\n}\n")
        a = self.write("a.kdl", """
binds {
    Super+Q { close-window; }
}
include "later.kdl"
""")
        merged = kdl.merge(kdl.parse_file(a))
        self.assertIn("screenshot", merged["Super+Q"].text)
        self.assertIsNotNone(merged["Super+Q"].overrides)

    def test_missing_file_returns_empty(self):
        self.assertEqual(kdl.parse_file(self.dir / "nope.kdl"), [])


class TestBindProperties(unittest.TestCase):
    def test_main_and_mods(self):
        b = kdl.Bind(combo="Super+Alt+Equal", props="", body=[], line=1, source="x")
        self.assertEqual(b.main, "Equal")
        self.assertEqual(b.mods, ["Super", "Alt"])

    def test_main_without_mods(self):
        b = kdl.Bind(combo="Print", props="", body=[], line=1, source="x")
        self.assertNotIn("Print", b.mods)


class TestTranslate(unittest.TestCase):
    def test_spawn_terminal(self):
        self.assertIn("终端", kdl.translate_spawn(["foot"]))

    def test_dms_screenshot(self):
        out = kdl.translate_spawn(["dms", "screenshot", "region"])
        self.assertTrue(out)

    def test_unknown_program_falls_back_to_name(self):
        out = kdl.translate_spawn(["my-script.sh"])
        self.assertIn("my-script.sh", out)

    def test_translate_body_picks_first_recognised_statement(self):
        out = kdl.translate(["Super+T {", "  spawn \"foot\";", "}"])
        self.assertEqual(out, "打开终端")

    def test_translate_body_without_braces_is_unrecognised(self):
        # Bind.body 一定含花括号；裸语句属异常输入，返回占位而不是崩
        self.assertEqual(kdl.translate(["spawn \"foot\""]), "（未识别）")


class TestGroupOf(unittest.TestCase):
    def test_known_groups_are_stable(self):
        self.assertIn(kdl.group_of("Super+Q", "关闭窗口"), kdl.GROUP_ORDER)

    def test_every_group_in_order(self):
        for g in kdl.GROUP_ORDER:
            self.assertIsInstance(g, str)


if __name__ == "__main__":
    unittest.main()
