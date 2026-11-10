"""渲染：Markdown / HTML / TSV / JSON 四种产物。

HTML 是自包含单文件（内联 CSS + JS），不用任何 CDN——这样下载到 U 盘、断网
也能开；下载页上那份示例就是它的输出。
"""

from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

from .layers import UNLISTABLE, LayerResult, Row
from .layers.base import ACTIVE, INACTIVE

STATE_ICON = {"ok": "✅", "bad": "⛔", "unknown": "❓"}

# 第 7 层的 Markdown 表：(层, 为什么读不出来, 怎么查)
UNLISTABLE_HOWTO = {
    UNLISTABLE[0][0]: "菜单 → 帮助 → 键盘快捷键；Firefox 也可在 about:config 搜 key_ 前缀",
    UNLISTABLE[1][0]: "应用内「快捷键」设置页；或 grep accel 对应的 .ui 文件",
    UNLISTABLE[2][0]: "查键盘说明书；或 sudo libinput debug-events --show-keycodes 实测",
    UNLISTABLE[3][0]: "扩展自己的快捷键设置页",
    UNLISTABLE[4][0]: "busctl --user tree org.freedesktop.portal.Desktop 能看到会话属主，读不到内容",
    UNLISTABLE[5][0]: "进 flatpak run --command=sh 的应用沙箱里看 ~/.config",
}


def _cell(text: str) -> str:
    """Markdown 表格单元格：竖线转义，反引号包住含特殊字符的键位。"""
    t = (text or "").replace("|", "\\|").replace("\n", " ")
    return t


def _md_keys(keys: list[str]) -> str:
    kk = " + ".join(keys)
    if "`" in kk:
        return f"`` {kk} ``"
    return f"`{kk}`"


def _tsv_safe(text: str) -> str:
    return (text or "").replace("\t", " ").replace("\r", " ").replace("\n", " ")


def timestamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")


# ------------------------------------------------------------------ Markdown
def render_markdown(results: list[LayerResult], keyboard: str, fingerprint: str) -> str:
    rows_total = sum(r.count for r in results)
    md: list[str] = [
        "# 全层级快捷键总表",
        "",
        f"> 当前检测到的键盘：**{keyboard or '未检测到'}**  ",
        f"> 键盘指纹：`{fingerprint}`（换键盘后自动重算）  ",
        f"> 生成时间：{timestamp()}",
        "",
        f"从 {sum(1 for r in results if r.rows)} 个可静态解析的层收集到 **{rows_total}** 条快捷键。",
        "",
        "| 层级 | 条数 | 状态 | 来源 |",
        "|---|---|---|---|",
    ]
    for res in results:
        if res.skipped and not res.rows:
            md.append(f"| {res.name} | — | 跳过：{_cell(res.skipped)} | |")
            continue
        status = INACTIVE if res.all_inactive else ACTIVE
        src = res.rows[0].source if res.rows else ""
        md.append(f"| {res.name} | {res.count} | {status} | `{_cell(src)}` |")
    md += [
        "",
        "**`Mod` = Super 键（Windows 徽标键）**。判定图标：✅ 实测按出 / ❓ 存疑 / ⛔ 硬件没有。",
        "",
        "> **怎么让判定更准**：跑 `keymap-atlas probe` 把真实按键按一遍，结果写进状态目录；"
        "`keymap-atlas probe --absent Print` 可直接标注某个键你键盘上没有。实测优先于 "
        "`/proc/bus/input/devices` 的能力位图（位图会把通用 HID 数组误当成「有这个键」）。",
        "",
    ]

    grouped: dict[str, list[Row]] = {}
    for res in results:
        for r in res.rows:
            grouped.setdefault(r.layer, []).append(r)

    for layer, rs in grouped.items():
        md.append(f"## {layer}（{len(rs)} 条）")
        md.append("")
        md.append("| 按键 | 功能 | 备注 |")
        md.append("|---|---|---|")
        for r in rs:
            md.append(f"| {_md_keys(r.keys)} | {_cell(r.action)} | "
                      f"{_cell(r.note_with_state)} |")
        md.append("")

    md.append("## 7 · 无法静态枚举的层")
    md.append("")
    md.append("下面这些**没有统一的枚举接口**，任何工具都读不出完整清单，只能进各自的地方看：")
    md.append("")
    md.append("| 层 | 为什么读不出来 | 怎么查 |")
    md.append("|---|---|---|")
    for layer, why in UNLISTABLE:
        md.append(f"| {layer} | {why} | {UNLISTABLE_HOWTO.get(layer, '')} |")
    md.append("")
    md.append("**本机可直接看的入口**：niri + DMS 的快捷键面板（默认 `Mod+Shift+/`）、DMS 设置。")
    md.append("")
    return "\n".join(md)


# ---------------------------------------------------------------------- HTML
CSS = """
:root{color-scheme:light dark}
*{box-sizing:border-box}
body{font-family:"Noto Sans CJK SC","Source Han Sans SC",system-ui,sans-serif;
 margin:0 auto;padding:34px 24px 64px;max-width:1120px;line-height:1.6;
 background:#fbfbfb;color:#1b1b1b}
h1{font-size:1.6rem;margin:0 0 6px}
h2{font-size:1.05rem;margin:38px 0 10px;padding-bottom:7px;border-bottom:2px solid #8884}
.sub{color:#777;font-size:.88rem}
table{width:100%;border-collapse:collapse;font-size:.9rem}
.card{background:#fff;border:1px solid #e5e5e5;border-radius:12px;overflow:hidden}
th{text-align:left;padding:8px 13px;background:#f4f4f4;font-size:.8rem;color:#666}
td{padding:8px 13px;border-top:1px solid #8882;vertical-align:middle}
tr:hover td{background:#f7f7f8}
kbd{display:inline-block;font-family:ui-monospace,monospace;font-size:.8rem;padding:2px 7px;
 border:1px solid #ccc;border-bottom-width:2px;border-radius:5px;background:#f6f6f6;
 white-space:nowrap}
.plus{color:#aaa;font-size:.72rem;margin:0 2px}
.tag{font-size:.72rem;padding:1px 8px;border-radius:999px;margin-left:8px;
 background:#8881;color:#666}
.tag.on{background:#2e7d3222;color:#2e7d32}
.tag.off{background:#b8860b22;color:#b8860b}
.off-row{opacity:.66}
.note{color:#888;font-size:.8rem}
#q{position:sticky;top:0;z-index:9;width:100%;font-size:1rem;padding:13px 16px;
 margin:16px 0 4px;border:1px solid #d8d8d8;border-radius:12px;background:#fff;
 color:inherit;font-family:inherit;box-shadow:0 2px 10px #0000000d}
#q:focus{outline:none;border-color:#7a7a7a;box-shadow:0 0 0 3px #8881}
#hint{font-size:.8rem;color:#999;margin:0 0 8px 4px;min-height:1.1em}
.hidden{display:none}
code{font-size:.85em;background:#8881;padding:1px 5px;border-radius:4px}
@media (prefers-color-scheme:dark){
 body{background:#131313;color:#e9e9e9}
 .card{background:#1c1c1c;border-color:#333}
 th{background:#242424;color:#999}
 kbd{background:#2b2b2b;border-color:#444;color:#eee}
 tr:hover td{background:#202020}}
"""

JS = """
(function(){
  var q=document.getElementById('q'),hint=document.getElementById('hint');
  var rows=[].slice.call(document.querySelectorAll('tr[data-b]'));
  var heads=[].slice.call(document.querySelectorAll('h2'));
  function run(){
    var v=q.value.trim().toLowerCase(),n=0;
    rows.forEach(function(tr){
      var ok=!v||tr.dataset.b.indexOf(v)>=0;
      tr.classList.toggle('hidden',!ok); if(ok)n++;
    });
    heads.forEach(function(h2){
      var card=h2.nextElementSibling,any=false;
      if(card&&card.querySelectorAll){
        any=[].slice.call(card.querySelectorAll('tr[data-b]'))
          .some(function(tr){return !tr.classList.contains('hidden');});
      }
      h2.classList.toggle('hidden',!any);
      if(card)card.classList.toggle('hidden',!any);
    });
    hint.textContent=v?('匹配 '+n+' 条（共 '+rows.length+' 条）'):'';
  }
  q.addEventListener('input',run);
  document.addEventListener('keydown',function(e){
    if(e.key==='/'&&document.activeElement!==q){e.preventDefault();q.focus();}
    if(e.key==='Escape'&&document.activeElement===q){q.value='';run();q.blur();}
  });
  if(location.hash.length>1){
    try{q.value=decodeURIComponent(location.hash.slice(1));}catch(e){}
    run();
  }
  q.focus();
})();
"""


def _esc(text: str) -> str:
    return html.escape(text or "", quote=True)


def _kbd(keys: list[str]) -> str:
    return '<span class="plus">+</span>'.join(
        f"<kbd>{_esc(c)}</kbd>" for c in keys)


def render_html(results: list[LayerResult], keyboard: str, fingerprint: str) -> str:
    total = sum(r.count for r in results)
    layers_used = sum(1 for r in results if r.rows)
    out: list[str] = [
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        "<title>全层级快捷键总表 · keymap-atlas</title>",
        f"<style>{CSS}</style></head><body>",
        "<h1>全层级快捷键总表</h1>",
        f'<p class="sub">共 {total} 条 · 覆盖 {layers_used} 个可静态解析的层 · '
        f"生成于 {_esc(timestamp())}</p>",
        f'<p class="sub"><b>当前键盘</b>：{_esc(keyboard) or "未检测到"} · '
        f"<b>指纹</b> <code>{_esc(fingerprint)}</code> —— 换/插键盘会自动重算并重建本页</p>",
        '<p class="sub">判定更准的办法：跑 <code>keymap-atlas probe</code> 把真实按键按一遍。'
        "实测结果优先于 <code>/proc</code> 能力位图。</p>",
        '<div class="card" style="margin:18px 0"><table><thead><tr><th>层级</th>'
        '<th style="width:90px">条数</th><th style="width:110px">状态</th>'
        "</tr></thead><tbody>",
    ]
    for res in results:
        if res.skipped and not res.rows:
            out.append(f'<tr><td>{_esc(res.name)}</td><td>—</td>'
                       f'<td><span class="tag">跳过</span></td></tr>')
            continue
        off = res.all_inactive
        out.append(f'<tr><td>{_esc(res.name)}</td><td>{res.count}</td><td>'
                   f'<span class="tag {"off" if off else "on"}">'
                   f'{INACTIVE if off else ACTIVE}</span></td></tr>')
    out.append("</tbody></table></div>")
    out.append("<p><kbd>Super</kbd> = Windows 徽标键（niri 的 <code>Mod</code>）。</p>")
    out.append('<input id="q" type="search" autocomplete="off" '
               'placeholder="🔍 输入中文即可查表：音量 / 亮度 / 截图 / 工作区 / 锁屏…'
               '（拼音 yl、jt、gzq 也可以）">')
    out.append('<div id="hint"></div>')

    grouped: dict[str, list[Row]] = {}
    for res in results:
        for r in res.rows:
            grouped.setdefault(r.layer, []).append(r)

    for layer, rs in grouped.items():
        off = all(r.status == INACTIVE for r in rs)
        tag_cls = "off" if off else "on"
        state_zh = INACTIVE if off else ACTIVE
        out.append(f"<h2>{_esc(layer)}<span class='tag {tag_cls}'>"
                   f"{len(rs)} 条 · {state_zh}</span></h2>")
        out.append('<div class="card"><table><thead><tr><th style="width:30%">按键</th>'
                   '<th style="width:45%">功能</th><th>备注</th></tr></thead><tbody>')
        for r in rs:
            cls = ' class="off-row"' if r.status == INACTIVE else ""
            blog = _esc(r.search_blob)
            out.append(f'<tr{cls} data-b="{blog}"><td>{_kbd(r.keys)}</td>'
                       f"<td>{_esc(r.action)}</td>"
                       f"<td class='note'>{_esc(r.note_with_state)}</td></tr>")
        out.append("</tbody></table></div>")

    out.append("<h2>7 · 无法静态枚举的层</h2>")
    out.append('<div class="card" style="padding:16px 18px"><table><thead><tr>'
               '<th>层</th><th>为什么读不出来</th><th>怎么查</th></tr></thead><tbody>')
    for layer, why in UNLISTABLE:
        out.append(f"<tr><td>{_esc(layer)}</td><td class='note'>{_esc(why)}</td>"
                   f"<td class='note'>{_esc(UNLISTABLE_HOWTO.get(layer, ''))}</td></tr>")
    out.append("</tbody></table></div>")
    out.append(f"<script>{JS}</script></body></html>")
    return "\n".join(out)


# ------------------------------------------------------------- TSV / JSON
INDEX_HEADER = ["keys", "action", "note", "layer_top", "status", "aliases"]


def render_tsv(results: list[LayerResult]) -> str:
    lines: list[str] = []
    for res in results:
        for r in res.rows:
            lines.append("\t".join([
                _tsv_safe(r.keys_text), _tsv_safe(r.action), _tsv_safe(r.note),
                _tsv_safe(r.layer_top), _tsv_safe(r.status), _tsv_safe(r.aliases),
            ]))
    return "\n".join(lines) + ("\n" if lines else "")


def render_json(results: list[LayerResult], keyboard: str, fingerprint: str) -> str:
    items = []
    for res in results:
        for r in res.rows:
            items.append({
                "keys": r.keys_text,
                "keys_plain": r.keys_plain,
                "action": r.action,
                "note": r.note,
                "state": r.state,
                "layer": r.layer,
                "layer_top": r.layer_top,
                "status": r.status,
                "source": r.source,
            })
    doc = {
        "generated": timestamp(),
        "keyboard": keyboard,
        "fingerprint": fingerprint,
        "count": len(items),
        "layers": [{"name": r.name, "count": r.count, "skipped": r.skipped}
                   for r in results],
        "rows": items,
    }
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


# ------------------------------------------------------------------- write
def write_all(results: list[LayerResult], out_dir: Path, keyboard: str,
              fingerprint: str, state_dir: Path | None = None) -> dict[str, Path]:
    out = out_dir
    out.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    files = {
        "markdown": ("all-shortcuts-zh.md", render_markdown(results, keyboard, fingerprint)),
        "html": ("all-shortcuts-zh.html", render_html(results, keyboard, fingerprint)),
        "tsv": ("shortcuts-index.tsv", render_tsv(results)),
        "json": ("shortcuts-index.json", render_json(results, keyboard, fingerprint)),
    }
    for _, (name, text) in files.items():
        p = out / name
        p.write_text(text, encoding="utf-8")
        written[name] = p

    if state_dir is not None:
        state_dir.mkdir(parents=True, exist_ok=True)
        fp_path = state_dir / "fingerprint.txt"
        fp_path.write_text(fingerprint + "\n", encoding="utf-8")
        written["fingerprint"] = fp_path

    return written
