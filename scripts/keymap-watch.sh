#!/usr/bin/env bash
# keymap-watch.sh —— 键盘热插拔监视：换键盘就自动重算清单
#
# 为什么需要：设备名、按键矩阵、能力位图都随插拔变化，「这个键有没有」的
# 结论必须跟着重算。udevadm monitor 不需要 root。
#
# 用法:
#   ./keymap-watch.sh            # 前台监视（Ctrl+C 结束）
#   ./keymap-watch.sh --once     # 只检查一次，变了就重建
#   ./keymap-watch.sh --quiet    # 后台常驻（systemd 用户服务用这个）
#
# v0.1.0 修掉的两个坑（旧脚本曾因此一分钟弹 30 条通知）：
#   1. 生成命令必须显式传 --outdir/--state-dir。旧脚本靠 cwd，而 systemd
#      服务的 cwd 是 $HOME，产物写到了别处，这里读永远「不相同」→ 无限重建。
#   2. 重建后必须断言「落盘指纹 == 当前指纹」。不相等就只提醒一次，不再循环。
set -uo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 允许用环境变量覆盖（测试与非常规安装都用得上）
WORKDIR="${KEYMAP_ATLAS_DIR:-$(cd "$SELF_DIR/.." && pwd)}"
OUTDIR="${KEYMAP_ATLAS_OUT:-$WORKDIR/examples}"
STATE_DIR="${KEYMAP_ATLAS_STATE:-${XDG_CONFIG_HOME:-$HOME/.config}/keymap-atlas}"
FP_FILE="$STATE_DIR/fingerprint.txt"
LOG="${KEYMAP_ATLAS_LOG:-$WORKDIR/keyboard-watch.log}"
COOLDOWN="${KEYMAP_ATLAS_COOLDOWN:-5}"      # 秒，两次重建之间的最小间隔

ONCE=0
QUIET=0
for a in "$@"; do
    case "$a" in
        --once)  ONCE=1 ;;
        --quiet) QUIET=1 ;;
        -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    esac
done

say() {
    [[ $QUIET -eq 1 ]] || printf '%s\n' "$*"
    printf '%s %s\n' "$(date '+%F %T')" "$*" >>"$LOG" 2>/dev/null || true
}

# 统一入口：优先用装好的命令，其次用仓库里的源码（免安装也能跑）
kma() {
    if command -v keymap-atlas >/dev/null 2>&1; then
        keymap-atlas "$@"
    else
        PYTHONPATH="$WORKDIR/src" python3 -m keymap_atlas "$@"
    fi
}

# 指纹直接读 /proc，避免重建产物就为了拿一个哈希
probe_fp() {
    PYTHONPATH="$WORKDIR/src" python3 - <<'PY' 2>/dev/null
from keymap_atlas.devices import device_fingerprint
print(device_fingerprint())
PY
}

stored_fp() {
    [[ -f "$FP_FILE" ]] && tr -d '\n' <"$FP_FILE" || printf ''
}

kb_names() {
    PYTHONPATH="$WORKDIR/src" python3 - <<'PY' 2>/dev/null || printf '未知'
from keymap_atlas.devices import read_devices
print(read_devices().name_text())
PY
}

notify() {
    local title="$1" body="$2"
    command -v notify-send >/dev/null 2>&1 || return 0
    # -r 固定 ID：同一条通知原地替换，不会在通知中心堆一列
    notify-send -a "键位图鉴" -r 20241108 -i input-keyboard "$title" "$body" 2>/dev/null || true
}

_last_rebuild=0

rebuild() {
    local now cur
    now=$(date +%s)
    if (( now - _last_rebuild < COOLDOWN )); then
        say "冷却中（${COOLDOWN}s），跳过这次重建"
        return 0
    fi
    _last_rebuild=$now

    say "键盘指纹变化 → 重建索引与报告"
    if ! kma report --outdir "$OUTDIR" --state-dir "$STATE_DIR" >/dev/null 2>&1; then
        say "重建失败。手动跑一次看报错：PYTHONPATH=$WORKDIR/src python3 -m keymap_atlas report"
        notify "键位图鉴：重建失败" "手动运行 keymap-atlas report 查看报错"
        return 1
    fi

    cur=$(probe_fp)
    local stored
    stored=$(stored_fp)
    if [[ -n "$cur" && "$cur" != "$stored" ]]; then
        # 写盘了但落盘值和当前值不一致：说明读到了不稳定的中间态（插拔过程中）
        say "警告：落盘指纹($stored) 与当前指纹($cur) 不一致，等下一次事件再试"
        notify "键位图鉴：键盘状态不稳定" "等插拔完成后会自动重试一次"
        return 1
    fi

    say "重建完成，当前指纹 ${stored:-未知}"
    notify "键盘已变更" "快捷键清单已按新键盘重新生成（$(kb_names)）"
    return 0
}

if [[ $ONCE -eq 1 ]]; then
    cur=$(probe_fp)
    [[ -n "$cur" ]] || { say "读取键盘失败"; exit 1; }
    if [[ "$cur" != "$(stored_fp)" ]]; then
        rebuild
    else
        say "键盘未变化（指纹 $cur）"
    fi
    exit 0
fi

say "开始监视键盘插拔（当前指纹 $(stored_fp)）…… Ctrl+C 结束"
# 一次插拔会连发多条事件（一个 Dongle 有 7 个 input 节点），必须去抖
udevadm monitor --subsystem-match=input --property 2>/dev/null | while read -r line; do
    case "$line" in
        ACTION=add|ACTION=remove|ACTION=change)
            sleep 1.2
            cur=$(probe_fp)
            if [[ -n "$cur" && "$cur" != "$(stored_fp)" ]]; then
                rebuild
            fi
            ;;
    esac
done
