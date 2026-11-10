"""niri 配置（KDL）解析与动作中文化。

niri 的配置是 KDL：`binds { Mod+Alt+Equal { spawn "dms" "ipc" "call" "audio" "increment" "3"; } }`，
并且支持 `include optional=true "dms/*.kdl"`。后者很关键：覆盖顺序就是生效顺序，
同名键位**后出现的赢**。所以这里递归解析 include，并按出现顺序保留全部绑定，
由上层决定「谁覆盖了谁」。
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------- 键名映射
# keysym -> (Linux evdev 键码, 中文说明, 键帽显示)
# 注意 "Print" 的 evdev 码是 99 (KEY_SYSRQ)，不是 210 —— 210 是 KEY_PRINT，
# 出现在 Consumer Control 接口里，普通键盘矩阵不会有。
KEYMAP: dict[str, tuple[int, str, str]] = {
    "Ctrl": (29, "左 Ctrl", "Ctrl"),
    "Control": (29, "左 Ctrl", "Ctrl"),
    "Alt": (56, "左 Alt", "Alt"),
    "Shift": (42, "左 Shift", "Shift"),
    "Mod": (125, "Super 键（Windows 徽标键）", "Super"),
    "Super": (125, "Super 键（Windows 徽标键）", "Super"),
}
KEYMAP.update({c: (code, "", c) for c, code in {
    "Q": 16, "W": 17, "E": 18, "R": 19, "T": 20, "Y": 21, "U": 22, "I": 23,
    "O": 24, "P": 25, "A": 30, "S": 31, "D": 32, "F": 33, "G": 34, "H": 35,
    "J": 36, "K": 37, "L": 38, "Z": 44, "X": 45, "C": 46, "V": 47, "B": 48,
    "N": 49, "M": 50,
}.items()})
KEYMAP.update({c: (code, "", c) for c, code in {
    "1": 2, "2": 3, "3": 4, "4": 5, "5": 6, "6": 7, "7": 8, "8": 9,
    "9": 10, "0": 11,
}.items()})
KEYMAP.update({
    "Minus": (12, "减号 - 键", "-"),
    "Equal": (13, "等号 = 键（就是 + 那个键，不用按 Shift）", "="),
    "BackSpace": (14, "退格键", "Backspace"),
    "Tab": (15, "Tab 键", "Tab"),
    "BracketLeft": (26, "左方括号 [", "["),
    "BracketRight": (27, "右方括号 ]", "]"),
    "Return": (28, "回车键", "Enter"),
    "semicolon": (39, "分号 ;", ";"),
    "apostrophe": (40, "单引号 '", "'"),
    "grave": (41, "反引号 `", "`"),
    "Backslash": (43, "反斜杠 \\", "\\"),
    "Comma": (51, "逗号 ,", ","),
    "Period": (52, "句点 .", "."),
    "Slash": (53, "斜杠 /", "/"),
    "Space": (57, "空格键", "Space"),
    "Escape": (1, "Esc 键", "Esc"),
    "Home": (102, "Home 键", "Home"),
    "Page_Up": (104, "PageUp 键", "PgUp"),
    "Page_Down": (109, "PageDown 键", "PgDn"),
    "End": (107, "End 键", "End"),
    "Delete": (111, "Delete 键", "Del"),
    "Insert": (110, "Insert 键", "Ins"),
    "Print": (99, "PrintScreen 键（evdev 码 99 / KEY_SYSRQ）", "PrtSc"),
    "F1": (59, "F1", "F1"), "F2": (60, "F2", "F2"), "F3": (61, "F3", "F3"),
    "F4": (62, "F4", "F4"), "F5": (63, "F5", "F5"), "F6": (64, "F6", "F6"),
    "F7": (65, "F7", "F7"), "F8": (66, "F8", "F8"), "F9": (67, "F9", "F9"),
    "F10": (68, "F10", "F10"), "F11": (87, "F11", "F11"), "F12": (88, "F12", "F12"),
    # 媒体 / 专用键（XF86 组）
    "XF86AudioRaiseVolume": (115, "音量加 媒体键", "音量+"),
    "XF86AudioLowerVolume": (114, "音量减 媒体键", "音量-"),
    "XF86AudioMute": (113, "静音 媒体键", "静音"),
    "XF86AudioMicMute": (248, "麦克风静音键", "麦静音"),
    "XF86AudioPlay": (164, "播放/暂停 媒体键", "播放"),
    "XF86AudioPause": (164, "播放/暂停 媒体键", "播放"),
    "XF86AudioPrev": (165, "上一曲 媒体键", "上一曲"),
    "XF86AudioNext": (163, "下一曲 媒体键", "下一曲"),
    "XF86MonBrightnessUp": (225, "亮度加 媒体键", "亮度+"),
    "XF86MonBrightnessDown": (224, "亮度减 媒体键", "亮度-"),
    "XF86Launch1": (148, "自定义启动键（常印 My Computer / 拍照图标）", "Launch1"),
    "XF86TouchpadToggle": (530, "触摸板开关键", "触控板"),
    "XF86TouchpadOn": (532, "触摸板开键", "触控板开"),
    "XF86TouchpadOff": (533, "触摸板关键", "触控板关"),
})

MOUSE_KEYS = {"WheelScrollUp", "WheelScrollDown", "WheelScrollLeft", "WheelScrollRight"}
MOUSE_ZH = {"WheelScrollUp": "鼠标滚轮向上", "WheelScrollDown": "鼠标滚轮向下",
            "WheelScrollLeft": "鼠标滚轮向左", "WheelScrollRight": "鼠标滚轮向右"}
MOUSE_CAP = {"WheelScrollUp": "滚轮↑", "WheelScrollDown": "滚轮↓",
             "WheelScrollLeft": "滚轮←", "WheelScrollRight": "滚轮→"}

# ---------------------------------------------------------- niri 动作中文名
ACTION_ZH = {
    "toggle-overview": "切换工作区总览（Overview）",
    "quit": "退出 niri（关闭整个会话）",
    "close-window": "关闭当前窗口",
    "maximize-column": "最大化当前列",
    "fullscreen-window": "全屏切换",
    "toggle-window-floating": "浮动窗口 / 平铺 切换",
    "switch-focus-between-floating-and-tiling": "在浮动窗口与平铺窗口间切换焦点",
    "toggle-column-tabbed-display": "列内标签页显示 切换",
    "focus-column-left": "聚焦左边一列",
    "focus-column-right": "聚焦右边一列",
    "focus-column-first": "聚焦最左一列",
    "focus-column-last": "聚焦最右一列",
    "focus-window-up": "聚焦上方窗口",
    "focus-window-down": "聚焦下方窗口",
    "move-column-left": "把当前列左移",
    "move-column-right": "把当前列右移",
    "move-column-to-first": "把当前列移到最前",
    "move-column-to-last": "把当前列移到最后",
    "move-window-up": "把当前窗口上移",
    "move-window-down": "把当前窗口下移",
    "focus-monitor-left": "聚焦左侧显示器",
    "focus-monitor-right": "聚焦右侧显示器",
    "focus-monitor-up": "聚焦上方显示器",
    "focus-monitor-down": "聚焦下方显示器",
    "move-column-to-monitor-left": "把当前列移到左侧显示器",
    "move-column-to-monitor-right": "把当前列移到右侧显示器",
    "move-column-to-monitor-up": "把当前列移到上方显示器",
    "move-column-to-monitor-down": "把当前列移到下方显示器",
    "focus-workspace-down": "切到下一个工作区",
    "focus-workspace-up": "切到上一个工作区",
    "move-column-to-workspace-down": "把当前列移到下一个工作区",
    "move-column-to-workspace-up": "把当前列移到上一个工作区",
    "move-workspace-down": "把本工作区顺序下移",
    "move-workspace-up": "把本工作区顺序上移",
    "consume-or-expel-window-left": "窗口并入 / 推出到左列",
    "consume-or-expel-window-right": "窗口并入 / 推出到右列",
    "expel-window-from-column": "把窗口从列中拆出来",
    "switch-preset-column-width": "循环切换预设列宽",
    "switch-preset-window-height": "循环切换预设窗口高度",
    "reset-window-height": "重置窗口高度",
    "expand-column-to-available-width": "当前列扩展到可用宽度",
    "center-column": "当前列居中",
    "center-visible-columns": "可见列整体居中",
    "set-column-width": "设置列宽",
    "set-window-height": "设置窗口高度",
    "next-window": "在最近使用窗口间切换（下一个）",
    "previous-window": "在最近使用窗口间切换（上一个）",
    "toggle-keyboard-shortcuts-inhibit": "切换「快捷键抑制」（把按键交还应用）",
    "power-off-monitors": "关闭显示器（省电）",
    "toggle-touchpad": "触摸板开关",
}

# --------------------------------------------------------- DMS IPC 中文名
DMS_ZH = {
    ("audio", "increment"): "系统音量 +{0}%",
    ("audio", "decrement"): "系统音量 -{0}%",
    ("audio", "mute"): "系统静音 切换",
    ("audio", "micmute"): "麦克风静音 切换",
    ("mpris", "playPause"): "播放 / 暂停（当前播放器）",
    ("mpris", "previous"): "上一曲",
    ("mpris", "next"): "下一曲",
    ("mpris", "increment"): "播放器音量 +{0}%",
    ("mpris", "decrement"): "播放器音量 -{0}%",
    ("brightness", "increment"): "屏幕亮度 +{0}%",
    ("brightness", "decrement"): "屏幕亮度 -{0}%",
    ("spotlight", "toggle"): "打开 / 关闭 启动器 Spotlight",
    ("spotlight-bar", "toggle"): "打开 / 关闭 顶部 Spotlight 输入条",
    ("clipboard", "toggle"): "剪贴板历史",
    ("dash", "toggle"): "打开 Dash 面板{0}",
    ("powermenu", "toggle"): "电源菜单（关机 / 重启 / 注销）",
    ("control-center", "toggle"): "控制中心（音量、亮度、网络等）",
    ("color-picker", "toggle"): "屏幕取色器",
    ("night", "toggle"): "夜间模式（护眼色温）",
    ("inhibit", "toggle"): "阻止休眠 / 息屏 切换",
    ("settings", "focusOrToggle"): "DMS 设置面板",
    ("notifications", "toggle"): "通知中心",
    ("notepad", "toggle"): "便签",
    ("notepad", "toggleExpand"): "便签（展开）",
    ("lock", "lock"): "锁屏",
    ("processlist", "focusOrToggle"): "进程管理器",
    ("keybinds", "toggle"): "快捷键面板",
    ("workspace-rename", "open"): "重命名当前工作区",
    ("window-rules", "toggle"): "窗口规则编辑器",
    ("outputs", "cycleProfile"): "循环切换显示器配置方案",
    ("niri", "showTouchpadOsd"): "显示触摸板状态提示",
}
DASH_TAB_ZH = {"media": "（媒体页）", "wallpaper": "（壁纸页）", "": ""}
SCREENSHOT_ZH = {"": "区域截图", "full": "全屏截图", "window": "窗口截图"}

TERMINALS = ("ghostty", "alacritty", "foot", "kitty", "wezterm", "konsole", "gnome-terminal")


@dataclass
class Bind:
    combo: str
    props: str
    body: list[str]
    line: int
    source: str
    overrides: str | None = None

    @property
    def text(self) -> str:
        return self.props + " " + " ".join(self.body)

    @property
    def main(self) -> str:
        return self.combo.split("+")[-1]

    @property
    def mods(self) -> list[str]:
        return self.combo.split("+")[:-1]


# ------------------------------------------------------------- KDL 解析
def strip_comment(line: str) -> str:
    """去掉行尾 `//` 注释，但引号内的 `//`（比如 URL）不能切。"""
    out: list[str] = []
    in_str = False
    for ch in line:
        if ch == '"':
            in_str = not in_str
        if ch == "/" and not in_str:
            break
        out.append(ch)
    return "".join(out).rstrip()


def is_combo(tok: str) -> bool:
    parts = tok.split("+")
    if len(parts) == 1:
        return tok in KEYMAP or tok in MOUSE_KEYS
    return all(p in KEYMAP for p in parts)


INCLUDE_RE = re.compile(r'^include\s+(?:optional=true\s+)?"(.+?)"$')


def parse_file(path: str | Path, acc: list[Bind] | None = None,
               seen: set[Path] | None = None) -> list[Bind]:
    """递归解析 niri 配置，把 binds 收集进 acc（保持出现顺序）。

    include 是相对当前文件所在目录解析的；同一文件只解析一次（防循环）。
    """
    acc = [] if acc is None else acc
    seen = set() if seen is None else seen

    p = Path(path).expanduser()
    try:
        p = p.resolve()
    except OSError:
        return acc
    if p in seen or not p.is_file():
        return acc
    seen.add(p)

    pending: tuple[str, str, list[str], int, str, int] | None = None
    lineno = 0

    for raw in p.read_text(errors="replace").splitlines():
        lineno += 1
        line = strip_comment(raw).strip()
        if not line:
            continue

        inc = INCLUDE_RE.match(line)
        if inc:
            parse_file(p.parent / inc.group(1), acc, seen)
            continue

        if pending:
            combo, props, body, start, src, depth = pending
            body.append(line)
            depth += line.count("{") - line.count("}")
            if depth <= 0:
                acc.append(Bind(combo=combo, props=props, body=body, line=start, source=src))
                pending = None
            else:
                pending = (combo, props, body, start, src, depth)
            continue

        tok = line.split()[0]
        if not is_combo(tok):
            continue
        props = line[len(tok):]
        depth = line.count("{") - line.count("}")
        body = [line]
        if depth <= 0:
            acc.append(Bind(combo=tok, props=props, body=body, line=lineno, source=str(p)))
        else:
            pending = (tok, props, body, lineno, str(p), depth)

    if pending:
        acc.append(Bind(combo=pending[0], props=pending[1], body=pending[2],
                        line=pending[3], source=pending[4]))
    return acc


def merge(binds: list[Bind]) -> dict[str, Bind]:
    """同名键位后者覆盖前者（niri 的 include 顺序语义），并记下被覆盖者。"""
    merged: dict[str, Bind] = {}
    for b in binds:
        if b.combo in merged:
            b.overrides = merged[b.combo].source
        merged[b.combo] = b
    return merged


# --------------------------------------------------------- 动作 -> 中文
def translate_spawn(args: list[str]) -> str:
    prog, rest = args[0], args[1:]
    if any(s in prog for s in TERMINALS):
        return "打开终端"
    if prog == "dms":
        if rest and rest[0] == "screenshot":
            which = rest[1] if len(rest) > 1 else ""
            return "截图：" + SCREENSHOT_ZH.get(which, "截图")
        if rest and rest[0] == "ipc":
            toks = [t for t in rest[1:] if t != "call"]
            target = toks[0] if toks else ""
            func = toks[1] if len(toks) > 1 else ""
            extra = toks[2:]
            tpl = DMS_ZH.get((target, func))
            if tpl:
                if target == "dash":
                    tab = extra[0] if extra else ""
                    return tpl.format(DASH_TAB_ZH.get(tab, f"（{tab}）" if tab else ""))
                return tpl.format(extra[0] if extra else "")
            return f"DMS {target} {func} {' '.join(extra)}".strip()
        return "DMS：" + " ".join(rest)
    if prog == "niri" and len(rest) >= 3 and rest[0] == "msg" and rest[1] == "action":
        return ACTION_ZH.get(rest[2], rest[2])
    return "运行 " + os.path.basename(prog)


def translate(body: list[str]) -> str:
    text = " ".join(body)
    inner = text[text.find("{") + 1: text.rfind("}")] \
        if "{" in text and "}" in text else ""
    stmts = [s.strip() for s in re.split(r";", inner) if s.strip()]
    for st in stmts:
        sp = re.match(r'^spawn\s+(.*)$', st)
        if sp:
            args = re.findall(r'"(.*?)"', sp.group(1))
            if args:
                return translate_spawn(args)
        parts = st.split()
        if not parts:
            continue
        act, extra = parts[0], parts[1:]
        if act in ACTION_ZH:
            zh = ACTION_ZH[act]
            if not extra:
                return zh
            if act in ("next-window", "previous-window"):
                tail = " ".join(extra)
                if 'scope="output"' in tail:
                    zh += "（限定当前显示器）"
                if 'filter="app-id"' in tail:
                    zh += "（按应用分组）"
                return zh
            if act in ("set-column-width", "set-window-height"):
                v = extra[0].strip('"')
                what = "列宽" if act == "set-column-width" else "窗口高度"
                return f"{what} {v}（{'放大' if v.startswith('+') else '缩小'}）"
            return zh + " " + " ".join(extra)
        if act in ("focus-workspace", "move-column-to-workspace"):
            base = "切换到工作区" if act == "focus-workspace" else "把当前列移到工作区"
            return base + " " + " ".join(t.strip('"') for t in extra)
        return act
    return "（未识别）"


# ------------------------------------------------------------ 分组归类
GROUP_ORDER = ["窗口 / 列管理", "焦点 / 窗口切换", "工作区", "显示器 / 输出",
               "声音 / 亮度 / 媒体", "截图", "应用 / 系统面板",
               "多媒体 / 专用键", "鼠标滚轮", "其它"]

APPLY_WORDS = ("终端", "启动器", "Spotlight", "面板", "中心", "菜单", "剪贴板",
               "便签", "设置", "取色", "通知", "壁纸", "进程", "电源", "锁屏",
               "夜间", "休眠", "快捷键", "规则", "配置", "重命名", "退出 niri",
               "触摸板")


def group_of(combo: str, action: str) -> str:
    if combo.split("+")[-1] in MOUSE_KEYS:
        return "鼠标滚轮"
    if "XF86" in combo:
        return "多媒体 / 专用键"
    if "截图" in action:
        return "截图"
    if any(w in action for w in ("音量", "亮度", "静音", "播放", "曲")):
        return "声音 / 亮度 / 媒体"
    if "工作区" in action:
        return "工作区"
    if any(w in action for w in ("聚焦", "最近使用窗口")):
        return "焦点 / 窗口切换"
    if any(w in action for w in ("显示器", "输出")):
        return "显示器 / 输出"
    if any(w in action for w in ("列", "窗口", "全屏", "浮动", "标签页", "居中")):
        return "窗口 / 列管理"
    if any(w in action for w in APPLY_WORDS):
        return "应用 / 系统面板"
    return "其它"
