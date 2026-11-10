#!/usr/bin/env bash
# keys-lookup.sh —— 弹出式中文快捷键速查（fuzzel）
#
# 用法:
#   keys-lookup.sh                 # 弹搜索窗（中文 / 拼音首字母 / 英文 / 键位都能查）
#   keys-lookup.sh 音量            # 带关键字预过滤
#   keys-lookup.sh yl              # 拼音首字母
#   keys-lookup.sh --all 音量      # 连当前不生效的层（KDE / GNOME）一起
#   keys-lookup.sh --cli 音量      # 不开弹窗，终端直出（SSH / 无图形时用）
#
# 选中后复制到剪贴板并弹一条通知。
# 索引过期（脚本更新、键盘变化）时先自动重建一次。
set -uo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKDIR="${KEYMAP_ATLAS_DIR:-$(cd "$SELF_DIR/.." && pwd)}"
OUTDIR="${KEYMAP_ATLAS_OUT:-$WORKDIR/examples}"
STATE_DIR="${KEYMAP_ATLAS_STATE:-${XDG_CONFIG_HOME:-$HOME/.config}/keymap-atlas}"
TSV="$OUTDIR/shortcuts-index.tsv"
FP_FILE="$STATE_DIR/fingerprint.txt"

kma() {
    if command -v keymap-atlas >/dev/null 2>&1; then
        keymap-atlas "$@"
    else
        PYTHONPATH="$WORKDIR/src" python3 -m keymap_atlas "$@"
    fi
}

probe_fp() {
    PYTHONPATH="$WORKDIR/src" python3 - <<'PY' 2>/dev/null
from keymap_atlas.devices import device_fingerprint
print(device_fingerprint())
PY
}

needs_rebuild() {
    [[ ! -f "$TSV" ]] && return 0
    # 源码比索引新（改了脚本没重建）
    local newest
    newest=$(find "$WORKDIR/src" -name '*.py' -newer "$TSV" -print -quit 2>/dev/null)
    [[ -n "$newest" ]] && return 0
    # 指纹变了 = 换键盘
    local cur
    cur=$(probe_fp)
    [[ -n "$cur" ]] || return 1          # 探测不到就别乱重建
    [[ ! -f "$FP_FILE" ]] && return 0
    [[ "$(tr -d '\n' <"$FP_FILE")" != "$cur" ]] && return 0
    return 1
}

if needs_rebuild; then
    kma report --outdir "$OUTDIR" --state-dir "$STATE_DIR" >/dev/null 2>&1
fi
[[ -f "$TSV" ]] || { echo "找不到索引：$TSV（先跑 keymap-atlas report）" >&2; exit 1; }

INITIAL=""
SHOW_ALL=0
CLI=0
for a in "$@"; do
    case "$a" in
        --all) SHOW_ALL=1 ;;
        --cli) CLI=1 ;;
        -h|--help) sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *)     INITIAL="$a" ;;
    esac
done

# ---- 组装候选：TSV 列 = keys / action / note / layer / status / aliases ----
build_list() {
    awk -F'\t' -v all="$SHOW_ALL" -v q="$INITIAL" '
        BEGIN { ql = tolower(q) }
        {
            if (all != 1 && $5 != "生效") next
            if (ql != "") {
                hit = 0
                if (index($2, q) > 0) hit = 1
                if (!hit) {
                    n = split(tolower($6), toks, " ")
                    for (i = 1; i <= n; i++) if (index(toks[i], ql) == 1) { hit = 1; break }
                }
                if (!hit && index(tolower($1), ql) > 0) hit = 1
                if (!hit) next
            }
            printf "%-30s \342\224\202 %s%s%s\n", $1, $2,
                   ($4 != "" ? "  [" $4 "]" : ""),
                   ($3 != "" ? "  \342\232\240 " $3 : "")
        }' "$TSV"
}

LIST=$(build_list)
if [[ $CLI -eq 1 ]]; then
    if [[ -z "$LIST" ]]; then echo "没有匹配「$INITIAL」的快捷键"; exit 0; fi
    printf '%s\n' "$LIST"
    exit 0
fi

if [[ -z "$LIST" ]]; then
    command -v notify-send >/dev/null 2>&1 && \
        notify-send -a "键位图鉴" "没有匹配「$INITIAL」" "试试：音量 / 亮度 / 截图 / 工作区 / 终端" 2>/dev/null
    exit 0
fi

LINES=$(printf '%s\n' "$LIST" | wc -l)
[[ $LINES -gt 14 ]] && LINES=14

SEARCH_ARG=()
# 纯中文交给 fuzzel 继续过滤；ASCII 已由别名列预筛过，不再塞进搜索框
if [[ -n "$INITIAL" && ! "$INITIAL" =~ ^[A-Za-z0-9[:space:]]+$ ]]; then
    SEARCH_ARG=(--search "$INITIAL")
fi

CHOICE=$(printf '%s\n' "$LIST" | fuzzel \
    --dmenu \
    --prompt "快捷键 › " \
    --placeholder "中文或拼音首字母：音量 yl / 截图 jt / 工作区 gzq" \
    "${SEARCH_ARG[@]}" \
    --lines "$LINES" \
    --width 68 \
    --match-mode fzf \
    --auto-select \
    --no-icons \
    --font "Noto Sans CJK SC:size=11" 2>/dev/null) || exit 0

[[ -z "${CHOICE:-}" ]] && exit 0

printf '%s' "$CHOICE" | wl-copy 2>/dev/null || true
command -v notify-send >/dev/null 2>&1 && \
    notify-send -a "键位图鉴" -r 20241108 "已复制到剪贴板" "$CHOICE" 2>/dev/null
printf '%s\n' "$CHOICE"
