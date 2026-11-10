"""各层解析器：fcitx5 / Ghostty / KDE / GNOME / 内核。

都用「把文本喂进去」的方式测，能跑在装了别的东西的机器上。KDE 那条最关键：
`kglobalshortcutsrc` 里存的是字面量 `\\t`，不是真 TAB。
"""

from __future__ import annotations

import unittest

from keymap_atlas.layers import fcitx, ghostty, gnome, kde


class TestFcitx(unittest.TestCase):
    def test_parse_ini(self):
        text = """
[Hotkey/TriggerKeys]
0=Control+space
1=Shift_L

[Hotkey/PrevPage]
0=Up
"""
        got = fcitx.parse_config_text(text) if hasattr(fcitx, "parse_config_text") else None
        self.assertTrue(got is not None, "应提供纯文本入口 parse_config_text")

    def test_caps_mapping(self):
        self.assertEqual(fcitx.FCITX_CAP["Control"], "Ctrl")
        self.assertEqual(fcitx.FCITX_CAP["Shift_L"], "左Shift")
        self.assertEqual(fcitx.FCITX_CAP["space"], "Space")

    def test_builtin_defaults_exist(self):
        self.assertIn("TriggerKeys", fcitx.FCITX_BUILTIN)
        self.assertIn("Ctrl+Space", fcitx.FCITX_BUILTIN["TriggerKeys"])

    def test_prefix_numbered(self):
        self.assertTrue(fcitx.PREFIX.startswith("2 · "))


class TestGhostty(unittest.TestCase):
    def test_parse_keybinds(self):
        text = """
# 注释
keybind = ctrl+shift+t=new_tab
keybind = ctrl+shift+w=close_surface
keybind = super+enter=new_split:down
"""
        got = ghostty.parse_keybinds(text)
        self.assertEqual(len(got), 3)
        self.assertEqual(got[0][0], "ctrl+shift+t")

    def test_ignores_non_keybind_lines(self):
        self.assertEqual(ghostty.parse_keybinds("font-size = 12\nwindow-height = 30"), [])

    def test_translate_known(self):
        self.assertEqual(ghostty.translate_action("new_tab"), ghostty.GHOSTTY_ZH["new_tab"])

    def test_translate_text_action(self):
        out = ghostty.translate_action("text:\\n")
        self.assertIn("换行", out)

    def test_translate_unknown_kept(self):
        self.assertEqual(ghostty.translate_action("some_future_action"),
                         "some_future_action")

    def test_prefix_numbered(self):
        self.assertTrue(ghostty.PREFIX.startswith("3 · "))


class TestKde(unittest.TestCase):
    def test_literal_backslash_t_is_split(self):
        """真实文件的写法：动作里两套键用字面量 \\t 分隔，后面才是默认值与友好名。"""
        text = (
            "[kwin]\n"
            "Expose=Ctrl+F9\\tMeta+F9,Ctrl+F9\\tMeta+F9,显示所有窗口\n"
        )
        got = kde.parse_kglobalshortcuts(text)
        self.assertEqual(len(got), 1)
        _, action, combos, _ = got[0]
        self.assertEqual(combos, ["Ctrl+F9", "Meta+F9"])
        self.assertEqual(action, "显示所有窗口")

    def test_real_tab_also_works(self):
        text = "[kwin]\nExpose=Ctrl+F9\tMeta+F9,Ctrl+F9\tMeta+F9,显示所有窗口\n"
        combos = [c for _, _, cs, _ in kde.parse_kglobalshortcuts(text) for c in cs]
        self.assertEqual(combos, ["Ctrl+F9", "Meta+F9"])

    def test_unbound_entries_skipped(self):
        text = "[kwin]\nfoo=none,none,不绑定\nbar=unbound,unbound,x\n"
        self.assertEqual(kde.parse_kglobalshortcuts(text), [])

    def test_inverse_action_group_skipped(self):
        """$InverseAction 是反向动作元数据，不是快捷键，必须整段丢弃。"""
        text = (
            "[kwin]\nWalk Through Windows=Alt+Tab,Alt+Tab,切换窗口\n"
            "[kwin][$InverseAction]\n"
            "Walk Through Windows=Walk Through Windows (Reverse)\n"
        )
        got = kde.parse_kglobalshortcuts(text)
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0][2], ["Alt+Tab"])

    def test_friendly_name_preferred(self):
        text = "[kwin]\ncloseWindow=Alt+F4,Alt+F4,关闭窗口\n"
        got = kde.parse_kglobalshortcuts(text)
        self.assertEqual(got[0][1], "关闭窗口")

    def test_group_comment_ignored(self):
        text = "# 注释\n;也是注释\n[kwin]\nx=Alt+F4,Alt+F4,关窗\n"
        self.assertEqual(len(kde.parse_kglobalshortcuts(text)), 1)

    def test_prefix_numbered(self):
        self.assertTrue(kde.PREFIX.startswith("5 · "))


class TestGnome(unittest.TestCase):
    def test_parse_accel_list(self):
        self.assertEqual(gnome.parse_accel_list("['<Super>t', '<Primary><Alt>t']"),
                         ["<Super>t", "<Primary><Alt>t"])

    def test_parse_single_string(self):
        self.assertEqual(gnome.parse_accel_list("'<Super>q'"), ["<Super>q"])

    def test_parse_empty(self):
        self.assertEqual(gnome.parse_accel_list("[]"), [])

    def test_parse_garbage(self):
        self.assertEqual(gnome.parse_accel_list("not a python literal"), [])

    def test_schemas_are_gnome(self):
        for s in gnome.GNOME_SCHEMAS:
            self.assertTrue(s.startswith("org.gnome."), s)

    def test_prefix_numbered(self):
        self.assertTrue(gnome.PREFIX.startswith("6 · "))


class TestKernelLayerInternals(unittest.TestCase):
    def test_default_logind_covers_common_handles(self):
        from keymap_atlas.layers import kernel
        # 长按类属性 systemd 默认值不一定存在，只要求常规电源/盖子都在
        for prop in ("HandlePowerKey", "HandleSuspendKey", "HandleHibernateKey",
                     "HandleRebootKey", "HandleLidSwitch", "HandlePowerKeyLongPress"):
            self.assertIn(prop, kernel.DEFAULT_LOGIND, prop)

    def test_sysrq_mask_parses(self):
        from keymap_atlas.layers import kernel
        m = kernel.sysrq_mask()
        self.assertTrue(m is None or isinstance(m, int))

    def test_prefix_numbered(self):
        from keymap_atlas.layers import kernel
        self.assertTrue(kernel.PREFIX.startswith("4 · "))


class TestLayerOrder(unittest.TestCase):
    def test_six_layers_fixed_order(self):
        from keymap_atlas.layers import LAYER_CLASSES
        self.assertEqual(len(LAYER_CLASSES), 6)
        prefixes = [c.name for c in LAYER_CLASSES]
        for i, p in enumerate(prefixes, 1):
            self.assertTrue(p.startswith(f"{i} · "), p)

    def test_unlistable_documented(self):
        from keymap_atlas.layers import UNLISTABLE
        self.assertGreaterEqual(len(UNLISTABLE), 5)
        blob = " ".join(" ".join(item) for item in UNLISTABLE)
        self.assertIn("portal", blob.lower())


if __name__ == "__main__":
    unittest.main()
