"""中文 / 拼音 / 英文检索别名。

为什么不用「按描述模糊匹配」：中文没有空格，`index()` 子串匹配会把
「jt」误命中「剪贴板」（拼音首字母里没有 j、t 相邻…实际上会）。做法是
把每条记录展开成一串别名 token：

  · 中文词 → 全拼 + 首字母 + 英文
  · 键位 → 去掉修饰词后的原样小写 token
  · 检索时 ASCII 按**词首前缀**匹配（`jt` 能中「截图 jietu」，不会中「剪贴板」）
"""

from __future__ import annotations

import re

ALIAS: dict[str, str] = {
    "音量": "yinliang yl volume", "亮度": "liangdu ld brightness",
    "静音": "jingyin jy mute", "麦克风": "maikefeng mkf mic",
    "播放": "bofang bf play", "暂停": "zanting zt pause",
    "上一曲": "shangyiqu syq prev", "下一曲": "xiayiqu xyq next",
    "截图": "jietu jt screenshot", "全屏": "quanping qp fullscreen",
    "窗口": "chuangkou ck window", "列": "lie column", "居中": "juzhong jz center",
    "浮动": "fudong fd floating", "标签页": "biaoqianye bqy tab",
    "工作区": "gongzuoqu gzq workspace", "总览": "zonglan zl overview",
    "终端": "zhongduan zd terminal", "启动器": "qidongqi qdq launcher",
    "剪贴板": "jiantieban jtb clipboard", "通知": "tongzhi tz notification",
    "设置": "shezhi sz settings", "电源": "dianyuan dy power", "锁屏": "suoping sp lock",
    "便签": "bianqian bq notepad", "取色": "quse qs color", "壁纸": "bizhi bz wallpaper",
    "夜间": "yejian yj night", "休眠": "xiumian xm inhibit", "进程": "jincheng jc process",
    "显示器": "xianshiqi xsq monitor", "聚焦": "jujiao jj focus",
    "切换": "qiehuan qh switch", "移动": "yidong yd move", "关闭": "guanbi gb close",
    "最大化": "zuidahua zdh maximize", "退出": "tuichu tc quit",
    "重命名": "zhongmingming zmm rename",
    "快捷键": "kuaijiejian kjj shortcut", "输入法": "shurufa srf ime",
    "中英文": "zhongyingwen zyw", "候选": "houhuan hx candidate", "翻页": "fanye fy page",
    "放大": "fangda fd zoom", "缩小": "suoxiao sx", "字体": "ziti zt font",
    "新建": "xinjian xj new", "复制": "fuzhi fz copy", "粘贴": "zhantie zt paste",
    "电源键": "dianyuanjian dyj", "睡眠": "shuimian sm suspend", "重启": "chongqi cq reboot",
    "虚拟终端": "xunizhongduan xnzd tty", "触摸板": "chumoban cmb touchpad",
    "超时": "chaoshi cs timeout",
}

_TOKEN_SPLIT = re.compile(r"[\s+│]+")


def aliases_for(action: str, keys) -> str:
    """为一条快捷键生成检索别名串（空格分隔，去重保序）。"""
    if isinstance(keys, (list, tuple)):
        keypart = " ".join(keys)
    else:
        keypart = str(keys)

    out: list[str] = []
    for zh, py in ALIAS.items():
        if zh in action:
            out.extend(py.split())

    for tok in _TOKEN_SPLIT.split(keypart):
        tok = tok.strip().lower()
        if len(tok) > 1 or (tok and not tok.isalpha()):
            out.append(tok)

    return " ".join(dict.fromkeys(x for x in out if x))


# 2-3 个字母的查询几乎都是「拼音首字母」用法。这时必须**整词相等**，
# 否则 `jt`（截图）会前缀命中 `jtb`（剪贴板）——实测旧版本就是这个 bug。
_INITIALS_RE = re.compile(r"^[a-z]{2,3}$")


def matches(haystack_action: str, aliases: str, keys: str, query: str) -> bool:
    """一条记录是否命中查询。

    中文走子串；ASCII 走 token 匹配：2-3 个字母按首字母整词相等，
    更长的按词首前缀（`yinliang` 能中 `yinliang`，`vol` 能中 `volume`）。
    """
    q = query.strip()
    if not q:
        return True
    ql = q.lower()
    if q in haystack_action or q in keys:
        return True

    short = bool(_INITIALS_RE.match(ql))
    for tok in aliases.split():
        if tok == ql:
            return True
        # 短查询：只允许和「完整英文单词」做前缀匹配（vol → volume），
        # 不允许命中别的首字母缩写（jt 不能命中 jtb）。
        if tok.startswith(ql) and (not short or len(tok) >= 4):
            return True
    return False
