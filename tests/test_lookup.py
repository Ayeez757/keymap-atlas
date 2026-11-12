"""检索：中文子串 + 拼音首字母前缀。

这是用户实际用得最多的一条路径，断言要贴着真实查询写：
「音量」「yl」「jt」都要命中，而「jt」不能命中「剪贴板」。
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from keymap_atlas import i18n, lookup
from keymap_atlas.layers.base import ACTIVE, INACTIVE, Row


def make_row(**kw) -> Row:
    base = dict(layer="1 · niri 合成器层 › 其它", keys=["Super", "Q"],
                action="关闭窗口", status=ACTIVE)
    base.update(kw)
    return Row(**base)


class TestAliasesFor(unittest.TestCase):
    def test_chinese_adds_pinyin(self):
        a = i18n.aliases_for("系统音量 +3%", ["Super", "Alt", "="])
        self.assertIn("yinliang", a)
        self.assertIn("yl", a)

    def test_keys_added_as_tokens(self):
        # 单字母键不进别名表（会让任何以该字母开头的查询都命中），
        # 但键位串本身仍可整串匹配，见 test_key_string_match
        a = i18n.aliases_for("关闭窗口", ["Super", "Q"])
        self.assertIn("super", a)

    def test_initials_require_exact_token(self):
        a = "jietu jt screenshot"
        self.assertTrue(i18n.matches("区域截图", a, "", "jt"))
        self.assertFalse(i18n.matches("剪贴板", "jiantieban jtb clipboard", "", "jt"))

    def test_long_query_uses_prefix(self):
        a = "yinliang yl volume"
        self.assertTrue(i18n.matches("系统音量", a, "", "yinlia"))
        self.assertTrue(i18n.matches("系统音量", a, "", "vol"))

    def test_deduplicated(self):
        a = i18n.aliases_for("音量 音量", ["音量"])
        toks = a.split()
        self.assertEqual(len(toks), len(set(toks)))

    def test_no_alias_for_unknown_action(self):
        a = i18n.aliases_for("某个不认识的动词", [])
        self.assertNotIn("yinliang", a)


class TestMatches(unittest.TestCase):
    def test_chinese_substring(self):
        self.assertTrue(i18n.matches("关闭窗口", "", "Super + Q", "关闭"))

    def test_pinyin_prefix(self):
        a = i18n.aliases_for("切换到下一个工作区", ["Super", "PgDn"])
        self.assertTrue(i18n.matches("切换到下一个工作区", a, "Super + PgDn", "gzq"))

    def test_no_false_positive_for_jt(self):
        """jt 必须能命中「截图」，但没有理由命中「剪贴板」。"""
        jt = i18n.aliases_for("区域截图", ["Super", "Alt", "S"])
        self.assertTrue(i18n.matches("区域截图", jt, "Super + Alt + S", "jt"))
        jtb = i18n.aliases_for("剪贴板历史", ["Super", "V"])
        self.assertFalse(i18n.matches("剪贴板历史", jtb, "Super + V", "jt"))

    def test_empty_query_matches_all(self):
        self.assertTrue(i18n.matches("任何", "", "", ""))

    def test_key_string_match(self):
        self.assertTrue(i18n.matches("关闭", "", "Super + Q", "Super + Q"))


class TestLookupSearch(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"keys": "Super + Alt + =", "action": "系统音量 +3%", "note": "",
             "layer": "1 · niri", "status": ACTIVE,
             "aliases": i18n.aliases_for("系统音量 +3%", ["Super", "Alt", "="])},
            {"keys": "Super + V", "action": "剪贴板历史", "note": "",
             "layer": "1 · niri", "status": ACTIVE,
             "aliases": i18n.aliases_for("剪贴板历史", ["Super", "V"])},
            {"keys": "Ctrl + F9", "action": "KDE 显示所有窗口", "note": "",
             "layer": "5 · KDE", "status": INACTIVE,
             "aliases": i18n.aliases_for("KDE 显示所有窗口", ["Ctrl", "F9"])},
        ]

    def test_chinese(self):
        hits = lookup.search(self.rows, "音量")
        self.assertEqual([h["keys"] for h in hits], ["Super + Alt + ="])

    def test_pinyin(self):
        hits = lookup.search(self.rows, "yl")
        self.assertEqual(len(hits), 1)

    def test_inactive_excluded_by_default(self):
        self.assertEqual(lookup.search(self.rows, "KDE"), [])

    def test_inactive_included_with_flag(self):
        hits = lookup.search(self.rows, "KDE", include_inactive=True)
        self.assertEqual(len(hits), 1)

    def test_no_match(self):
        self.assertEqual(lookup.search(self.rows, "zzzz"), [])

    def test_layer_name_matches(self):
        """层名参与检索：搜「Fn」要能命中固件功能键那一组。"""
        rows = [{"keys": "亮度+", "action": "提高屏幕亮度", "note": "固件上报键码 225",
                 "layer": "4 · 内核 / 硬件层 › 固件功能键（Fn 行）",
                 "status": ACTIVE, "aliases": ""}]
        self.assertEqual(len(lookup.search(rows, "Fn")), 1)
        self.assertEqual(len(lookup.search(rows, "固件")), 1)
        self.assertEqual(len(lookup.search(rows, "内核")), 1)


class TestLoadIndex(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.tsv"
            p.write_text("Super + Q\t关闭窗口\t\t1 · niri\t生效\tgb ck q\n")
            rows = lookup.load_index(p)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["action"], "关闭窗口")

    def test_missing_file(self):
        self.assertEqual(lookup.load_index(Path("/nonexistent/x.tsv")), [])

    def test_short_lines_padded(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.tsv"
            p.write_text("a\tb\n")
            r = lookup.load_index(p)[0]
            self.assertEqual(r["status"], "")
            self.assertEqual(r["aliases"], "")


class TestAliasesColumn(unittest.TestCase):
    def test_fills_missing_aliases(self):
        rows = [{"keys": "Super + Q", "action": "关闭窗口", "aliases": ""}]
        out = lookup.aliases_column(rows)
        self.assertTrue(out[0]["aliases"])

    def test_keeps_existing(self):
        rows = [{"keys": "Super + Q", "action": "关闭窗口", "aliases": "already"}]
        self.assertEqual(lookup.aliases_column(rows)[0]["aliases"], "already")


class TestFormatRow(unittest.TestCase):
    def test_contains_action_and_layer(self):
        r = {"keys": "Super + Q", "action": "关闭窗口", "note": "仅当…",
             "layer": "1 · niri"}
        s = lookup.format_row(r)
        self.assertIn("关闭窗口", s)
        self.assertIn("1 · niri", s)
        self.assertIn("仅当", s)


if __name__ == "__main__":
    unittest.main()
