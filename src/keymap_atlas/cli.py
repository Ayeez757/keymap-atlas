"""命令行入口：`keymap-atlas <子命令>`。

子命令刻意做成「一条命令一个任务」，因为绝大部分用户只会跑前两个：

  report  生成全层级报告（md/html/tsv/json）
  probe   真实按键探针（GTK4）
  hid     只读 HID 描述符，回答「不按键能判断吗」
  lookup 按中文/拼音/键位查表
  layers  列出本机能解析到哪些层、各多少条
  doctor  自检：这台机器上哪些证据源可用
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__, evidence as ev, hid as hidmod
from .config import Config, lid_present, session_desktop
from .layers import all_layers
from .layers.niri import keyboard_summary
from . import devices as devmod
from . import lookup as lk
from . import render


def _cfg(args) -> Config:
    cfg = Config()
    if getattr(args, "outdir", None):
        cfg.out_dir = Path(args.outdir).expanduser().resolve()
    if getattr(args, "config", None):
        cfg.niri_config = Path(args.config).expanduser()
    if getattr(args, "state_dir", None):
        cfg.state_dir = Path(args.state_dir).expanduser()
    return cfg


# ------------------------------------------------------------------- report
def cmd_report(args) -> int:
    cfg = _cfg(args)
    results = all_layers(cfg)
    if args.skip_inactive:
        # 只要当前会话真能按出来的：把整层都是「未生效」的层直接扔掉
        results = [r for r in results if not r.all_inactive]
    keyboard, fingerprint = keyboard_summary(cfg)

    written = render.write_all(results, cfg.out_dir, keyboard, fingerprint,
                               state_dir=cfg.state_dir)
    total = sum(r.count for r in results)
    used = sum(1 for r in results if r.rows)

    print(f"[键盘] {keyboard or '未检测到'}  指纹 {fingerprint}")
    print(f"[统计] {used} 个可解析层，共 {total} 条快捷键")
    for res in results:
        if res.skipped and not res.rows:
            print(f"  - {res.name}: 跳过（{res.skipped}）")
        else:
            print(f"  - {res.name}: {res.count} 条")
    for name, path in written.items():
        print(f"[已写入] {path}")
    return 0


# --------------------------------------------------------------------- hid
def cmd_hid(args) -> int:
    devs = hidmod.analyse()
    if not args.all:
        # 过滤掉纯触摸板/鼠标，但**不要**把「描述符里没有键盘页」的设备一起丢掉：
        # 笔记本内置键盘正是这种情况（键表交给 ACPI），丢掉就只剩一句「读不到」。
        keyboard_like = [d for d in devs if hidmod.is_keyboard_like(d)]
        devs = keyboard_like or devs

    if args.json:
        print(json.dumps([{
            "hidraw": d.hidraw, "name": d.name, "desc_len": d.desc_len,
            "kbd_explicit": d.kbd_explicit, "kbd_ranges": d.kbd_ranges,
            "consumer_explicit": d.consumer_explicit,
            "consumer_ranges": d.consumer_ranges,
            "generic_keyboard": d.generic_keyboard,
            "generic_consumer": d.generic_consumer,
        } for d in devs], ensure_ascii=False, indent=1))
        return 0

    for d in devs:
        print(f"\n=== {d.hidraw}  {d.name}  ({d.desc_len} 字节描述符) ===")
        print(f"  键盘页显式列举: {len(d.kbd_explicit)} 个"
              + (f" → {', '.join(f'0x{u:02x}' for u in d.kbd_explicit[:12])}"
                 if d.kbd_explicit else ""))
        print(f"  键盘页范围声明: {len(d.kbd_ranges)} 段"
              + ("" if not d.kbd_ranges else
                 " → " + ", ".join(f"0x{a:02x}-0x{b:02x}" for a, b in d.kbd_ranges)))
        print(f"  Consumer 页显式列举: {len(d.consumer_explicit)} 个")
        print(f"  Consumer 页范围声明: {len(d.consumer_ranges)} 段"
              + ("" if not d.consumer_ranges else
                 " → " + ", ".join(f"0x{a:02x}-0x{b:02x}" for a, b in d.consumer_ranges)))
        if d.generic_keyboard:
            print("  ⚠ 键盘页有「泛型全范围」数组 → 位图会谎报有这个键，必须实测")
        if d.generic_consumer:
            print("  ⚠ Consumer 页有「泛型全范围」数组 → 媒体键同样不可信")

    if args.keys or args.detail:
        cfg = _cfg(args)
        keys = []
        if cfg.niri_config.is_file():
            from . import kdl
            for b in kdl.parse_file(cfg.niri_config):
                if b.main not in keys and (b.main in kdl.KEYMAP or b.main in kdl.MOUSE_KEYS):
                    keys.append(b.main)
        print(f"\n=== 配置里用到的 {len(keys)} 个键，描述符层面能不能判定 ===")
        tally = {"yes": 0, "maybe": 0, "unk": 0, "no": 0}
        for k in keys:
            v, why = hidmod.verdict(k, devs)
            tally[v] = tally.get(v, 0) + 1
            mark = {"yes": "✅ 有", "maybe": "❓ 可能", "unk": "❓ 无法判定",
                    "no": "⛔ 没有"}[v]
            print(f"  {k:26s} {mark}   {why}")
        print(f"\n汇总：显式声明 {tally['yes']} · 窄范围 {tally['maybe']} · "
              f"必须实测 {tally['unk']} · 一定没有 {tally['no']}")
    return 0


# ------------------------------------------------------------------- probe
def cmd_probe(args) -> int:
    from . import probe as pb
    cfg = _cfg(args)

    if args.release:
        pb.force_release()
        print("已强制复位 niri 快捷键抑制（toggle 连翻两次 = 回到不抑制）")
        return 0

    if args.reset:
        cfg.probe_path.unlink(missing_ok=True)
        print(f"[已清空] {cfg.probe_path}")
        return 0

    if args.clear_absent:
        cfg.notes_path.unlink(missing_ok=True)
        print(f"[已清空] {cfg.notes_path}")
        return 0

    if args.absent is not None:
        data = ev.load(cfg)
        absent = set(data.absent)
        for k in args.absent:
            c = pb.normalize(k)
            absent.add(c)
            extra = f"（由 {k} 归一化）" if c != k else ""
            print(f"  标记为「没有」: {c}{extra}")
        p = ev.save_notes(cfg, absent)
        print(f"[已保存] {p} → 共 {len(absent)} 个")
        return 0

    if args.list:
        want = pb.wanted_keysyms(cfg)
        data = ev.load(cfg)
        print(f"配置里用到的 keysym：{len(want)} 个\n")
        for k in want:
            if k in data.observed:
                mark = "✅ 实测按出"
            elif k in data.absent:
                mark = "⛔ 标记为没有"
            elif k in data.observed_stale:
                mark = "❓ 实测记录来自旧键盘"
            else:
                mark = "❓ 未验证"
            print(f"  {k:26s} {mark}")
        return 0

    fp = devmod.device_fingerprint()

    def save(observed: set[str]) -> Path:
        return ev.save_probe(cfg, observed, fp)

    return pb.run_gui(cfg, save)


# ------------------------------------------------------------------ lookup
def cmd_lookup(args) -> int:
    cfg = _cfg(args)
    index = cfg.out_dir / lk.TSV_NAME
    if not index.is_file():
        index = cfg.state_dir / lk.TSV_NAME
    rows = lk.aliases_column(lk.load_index(index))
    if not rows:
        print(f"[错误] 没找到索引 {index}，先跑 `keymap-atlas report`", file=sys.stderr)
        return 1

    query = " ".join(args.query).strip()
    hits = lk.search(rows, query, include_inactive=args.all)
    if not hits:
        print(f"没有匹配「{query}」的快捷键（共 {len(rows)} 条）")
        return 1

    if args.fuzzel:
        picked = lk.fuzzel_pick(lk.build_fuzzel_lines(hits))
        if not picked:
            return 0
        lk.copy_to_clipboard(picked)
        lk.notify(picked)
        print(picked)
        return 0

    for r in hits:
        print(lk.format_row(r))
    print(f"\n共 {len(hits)} 条" + ("" if args.all else "（只含当前生效的层；加 --all 看全部）"))
    return 0


# ------------------------------------------------------------------ layers
def cmd_layers(args) -> int:
    cfg = _cfg(args)
    print(f"会话：{session_desktop()}   笔记本：{'是' if lid_present() else '否'}")
    print(f"状态目录：{cfg.state_dir}")
    for res in all_layers(cfg):
        if res.skipped and not res.rows:
            print(f"  {res.name:32s} —    跳过：{res.skipped}")
        else:
            tag = "（未生效）" if res.all_inactive else ""
            print(f"  {res.name:32s} {res.count:4d} 条{tag}")
    return 0


# ------------------------------------------------------------------ doctor
def cmd_doctor(args) -> int:
    cfg = _cfg(args)
    checks = [
        ("niri 配置", cfg.niri_config.is_file(), str(cfg.niri_config)),
        ("Ghostty 配置", cfg.ghostty_config.is_file(), str(cfg.ghostty_config)),
        ("fcitx5 配置", cfg.fcitx_config.is_file(), str(cfg.fcitx_config)),
        ("KDE 快捷键文件", cfg.kde_config.is_file(), str(cfg.kde_config)),
        ("/proc/bus/input/devices", Path("/proc/bus/input/devices").is_file(),
         "/proc/bus/input/devices"),
        ("HID 描述符可读", bool(hidmod.analyse()), "/sys/class/hidraw/*/device/report_descriptor"),
        ("busctl", bool(__import__("shutil").which("busctl")), "logind 属性"),
        ("gsettings", bool(__import__("shutil").which("gsettings")), "GNOME 键位"),
        ("fuzzel", bool(__import__("shutil").which("fuzzel")), "弹窗查表"),
        ("wl-copy", bool(__import__("shutil").which("wl-copy")), "复制到剪贴板"),
        ("notify-send", bool(__import__("shutil").which("notify-send")), "桌面通知"),
    ]
    for name, ok, detail in checks:
        print(f"  {'✅' if ok else '⛔'} {name:24s} {detail}")

    data = ev.load(cfg, devmod.device_fingerprint())
    print(f"\n证据：实测 {len(data.observed)} 个 · 标记没有 {len(data.absent)} 个"
          + (" · 实测记录来自旧键盘（需重跑 probe）" if data.is_stale() else ""))
    print(f"版本：keymap-atlas {__version__}")
    return 0


# -------------------------------------------------------------------- main
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="keymap-atlas",
        description="把一台 Linux 机器上各层快捷键收集成中文速查表，并用实测/HID 证据判断键位真假。",
    )
    p.add_argument("--version", action="version", version=f"keymap-atlas {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--outdir", default=None, help="产物目录（默认当前目录）")
        sp.add_argument("--config", default=None, help="niri config.kdl 路径")
        sp.add_argument("--state-dir", default=None, help="证据/状态目录")

    r = sub.add_parser("report", help="生成全层级报告")
    common(r)
    r.add_argument("--skip-inactive", action="store_true",
                   help="只输出当前会话生效的层")
    r.set_defaults(func=cmd_report)

    h = sub.add_parser("hid", help="只读 HID 描述符分析")
    common(h)
    h.add_argument("--json", action="store_true")
    h.add_argument("--keys", action="store_true", help="对照配置里用到的键给结论")
    h.add_argument("--detail", action="store_true", help="同 --keys")
    h.add_argument("--all", action="store_true", help="含非键盘类 HID 设备")
    h.set_defaults(func=cmd_hid)

    pr = sub.add_parser("probe", help="真实按键探针（GTK4 窗口）")
    common(pr)
    pr.add_argument("--list", action="store_true", help="只打印清单，不开窗")
    pr.add_argument("--reset", action="store_true", help="清空实测记录")
    pr.add_argument("--absent", nargs="*", metavar="KEYSYM",
                    help="标记键盘上确实没有的键")
    pr.add_argument("--clear-absent", action="store_true", help="清空「没有这个键」记录")
    pr.add_argument("--release", action="store_true", help="强制解除 niri 快捷键抑制")
    pr.set_defaults(func=cmd_probe)

    l = sub.add_parser("lookup", help="按中文/拼音/键位查表")
    common(l)
    l.add_argument("query", nargs="*", help="查询词：音量 / jt / Ctrl+C")
    l.add_argument("--all", action="store_true", help="含未生效的层")
    l.add_argument("--fuzzel", action="store_true", help="用 fuzzel 弹窗选")
    l.set_defaults(func=cmd_lookup)

    la = sub.add_parser("layers", help="列出本机能解析到的层")
    common(la)
    la.set_defaults(func=cmd_layers)

    d = sub.add_parser("doctor", help="自检证据源是否可用")
    common(d)
    d.set_defaults(func=cmd_doctor)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args) or 0)
    except KeyboardInterrupt:
        print("\n[中断]", file=sys.stderr)
        return 130
    except BrokenPipeError:
        os._exit(0)


if __name__ == "__main__":          # python -m keymap_atlas.cli
    raise SystemExit(main())
