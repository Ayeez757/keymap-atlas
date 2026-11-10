"""渲染层：Markdown / HTML / TSV / JSON。

HTML 是最容易出事的地方（单引号截断属性、`<` 未转义、空分组没隐藏），
所以用标准库 html.parser 真的把产物解析一遍，而不是只做字符串计数。
"""

from __future__ import annotations

import json
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

from keymap_atlas import render
from keymap_atlas.layers.base import ACTIVE, INACTIVE, LayerResult, Row


def make_row(**kw) -> Row:
    base = dict(layer="1 · niri 合成器层 › 窗口 / 列管理",
                keys=["Super", "Q"], action="关闭窗口",
                note="", status=ACTIVE, state="ok", source="~/.config/niri/config.kdl")
    base.update(kw)
    return Row(**base)


class RowTableParser(HTMLParser):
    """收集 <tr data-b=...> 的属性，用来验证属性没被截断。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blobs: list[str] = []
        self.ids: list[str] = []
        self.scripts = 0
        self.tags: list[str] = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        d = dict(attrs)
        if tag == "tr" and "data-b" in d:
            self.blobs.append(d["data-b"])
        if tag == "script":
            self.scripts += 1
        if "id" in d:
            self.ids.append(d["id"])


class TestRenderTSV(unittest.TestCase):
    def setUp(self):
        self.res = [LayerResult("1 · niri 合成器层", [make_row()])]

    def test_six_columns(self):
        for line in render.render_tsv(self.res).splitlines():
            self.assertEqual(len(line.split("\t")), 6)

    def test_tabs_and_newlines_are_sanitised(self):
        r = make_row(action="含\t制表符\n和换行")
        out = render.render_tsv([LayerResult("层", [r])])
        self.assertEqual(len(out.rstrip("\n").split("\t")), 6)
        self.assertEqual(len(out.rstrip("\n").splitlines()), 1)

    def test_empty(self):
        self.assertEqual(render.render_tsv([]), "")


class TestRenderJSON(unittest.TestCase):
    def test_roundtrip(self):
        res = [LayerResult("1 · niri 合成器层", [make_row()])]
        doc = json.loads(render.render_json(res, "键盘A", "abc123"))
        self.assertEqual(doc["count"], 1)
        self.assertEqual(doc["keyboard"], "键盘A")
        self.assertEqual(doc["fingerprint"], "abc123")
        self.assertEqual(doc["rows"][0]["keys"], "Super + Q")
        self.assertEqual(doc["layers"][0]["name"], "1 · niri 合成器层")

    def test_skipped_layer_recorded(self):
        res = [LayerResult("4 · 内核", [], skipped="缺 busctl")]
        doc = json.loads(render.render_json(res, "", ""))
        self.assertEqual(doc["layers"][0]["skipped"], "缺 busctl")


class TestRenderMarkdown(unittest.TestCase):
    def test_contains_headers_and_row(self):
        md = render.render_markdown([LayerResult("1 · niri 合成器层", [make_row()])],
                                    "键盘A", "abc123")
        self.assertIn("键盘A", md)
        self.assertIn("abc123", md)
        self.assertIn("关闭窗口", md)
        self.assertIn("Super", md)

    def test_state_icons(self):
        rows = [make_row(state="ok"), make_row(state="bad"), make_row(state="unknown")]
        md = render.render_markdown([LayerResult("层", rows)], "", "")
        for icon in ("✅", "⛔", "❓"):
            self.assertIn(icon, md)

    def test_inactive_layer_marked(self):
        md = render.render_markdown(
            [LayerResult("5 · KDE", [make_row(status=INACTIVE)])], "", "")
        self.assertIn(INACTIVE, md)


class TestRenderHTML(unittest.TestCase):
    def setUp(self):
        self.res = [
            LayerResult("1 · niri 合成器层", [
                make_row(),
                make_row(keys=["Super", "Alt", "Equal"], action="系统音量 +3%",
                         note="锁屏时也生效", state="unknown"),
                make_row(keys=["Print"], action="全屏截图", state="bad"),
            ]),
            LayerResult("2 · fcitx5", [make_row(layer="2 · fcitx5", keys=["Ctrl", "Space"],
                                               action="切换输入法")]),
        ]
        self.html = render.render_html(self.res, "键盘A", "abc123")

    def test_parses_cleanly(self):
        p = RowTableParser()
        p.feed(self.html)
        self.assertEqual(len(p.blobs), 4)

    def test_has_search_box(self):
        p = RowTableParser()
        p.feed(self.html)
        self.assertIn("q", p.ids)

    def test_inline_script_present(self):
        p = RowTableParser()
        p.feed(self.html)
        self.assertGreaterEqual(p.scripts, 1)

    def test_no_raw_quote_breakage(self):
        """data-b 里若出现未转义的引号，属性会被截断。"""
        p = RowTableParser()
        p.feed(self.html)
        for b in p.blobs:
            self.assertNotIn('"', b)
            self.assertNotIn("<", b)

    def test_escapes_html_in_user_supplied_text(self):
        res = [LayerResult("层", [make_row(action="<script>alert(1)</script>")])]
        html = render.render_html(res, "", "")
        # 正文里必须被转义；只允许页尾自己那一个真 <script>
        self.assertNotIn("<script>alert(1)</script>", html)

    def test_contains_keyboard_and_fingerprint(self):
        self.assertIn("键盘A", self.html)
        self.assertIn("abc123", self.html)

    def test_search_blob_lowercase(self):
        p = RowTableParser()
        p.feed(self.html)
        for b in p.blobs:
            self.assertEqual(b, b.lower())


class TestWriteAll(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.res = [LayerResult("1 · niri 合成器层", [make_row()])]

    def tearDown(self):
        self.tmp.cleanup()

    def test_writes_four_files_and_fingerprint(self):
        out = self.root / "out"
        state = self.root / "state"
        written = render.write_all(self.res, out, "键盘A", "abc123", state_dir=state)
        for name in ("all-shortcuts-zh.md", "all-shortcuts-zh.html",
                     "shortcuts-index.tsv", "shortcuts-index.json"):
            self.assertTrue((out / name).is_file(), name)
            self.assertIn(name, written)
        self.assertEqual((state / "fingerprint.txt").read_text().strip(), "abc123")

    def test_creates_missing_dirs(self):
        out = self.root / "deep" / "nested"
        render.write_all(self.res, out, "", "")
        self.assertTrue((out / "shortcuts-index.tsv").is_file())

    def test_without_state_dir_skips_fingerprint(self):
        out = self.root / "out2"
        written = render.write_all(self.res, out, "", "")
        self.assertNotIn("fingerprint", written)


class TestTimestamp(unittest.TestCase):
    def test_format(self):
        ts = render.timestamp()
        self.assertRegex(ts, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}")


if __name__ == "__main__":
    unittest.main()
