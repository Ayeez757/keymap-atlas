#!/usr/bin/env bash
# install-keymap-watch.sh —— 把键盘热插拔监视装成 systemd 用户服务
#
# 装完后：换/插键盘 → 自动重算清单与报告，不用手动跑脚本。
#
# 用法:
#   ./install-keymap-watch.sh              # 安装并立即启用
#   ./install-keymap-watch.sh --remove     # 卸载
#   ./install-keymap-watch.sh --status     # 看状态与最近日志
#
# 装的是什么：$HOME/.config/systemd/user/keymap-watch.service
# 依赖什么：udevadm（util-linux）、bash、python3；不需要 root。
set -uo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKDIR="${KEYMAP_ATLAS_DIR:-$(cd "$SELF_DIR/.." && pwd)}"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
UNIT="$UNIT_DIR/keymap-watch.service"
BINDIR="$WORKDIR/scripts"

# 优先用装好的命令路径；没装就把仓库自己的脚本路径写进服务
WATCH="$BINDIR/keymap-watch.sh"

case "${1:-}" in
    --remove)
        systemctl --user disable --now keymap-watch.service 2>/dev/null
        rm -f "$UNIT"
        systemctl --user daemon-reload
        echo "已卸载 keymap-watch.service"
        exit 0 ;;
    --status)
        systemctl --user status keymap-watch.service --no-pager 2>&1 | head -20
        echo "--- 最近日志 ---"
        journalctl --user -u keymap-watch.service -n 15 --no-pager 2>/dev/null | tail -15
        exit 0 ;;
    -h|--help)
        sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
        exit 0 ;;
esac

if [[ ! -x "$WATCH" ]]; then
    echo "❌ 找不到可执行的 $WATCH" >&2
    exit 1
fi
if ! command -v udevadm >/dev/null 2>&1; then
    echo "❌ 缺 udevadm（util-linux）。装完再试。" >&2
    exit 1
fi

mkdir -p "$UNIT_DIR"
sed "s|@BINDIR@|$BINDIR|g" "$BINDIR/systemd/keymap-watch.service.in" >"$UNIT"

systemctl --user daemon-reload
systemctl --user enable --now keymap-watch.service

sleep 1
if systemctl --user is-active --quiet keymap-watch.service; then
    echo "✅ 已安装并启动：keymap-watch.service"
    echo "   服务文件：$UNIT"
    echo "   现在换键盘会自动重建清单"
    echo "   跟随日志：journalctl --user -u keymap-watch -f"
    echo "   卸载：$0 --remove"
else
    echo "❌ 启动失败，看日志："
    journalctl --user -u keymap-watch.service -n 20 --no-pager
    exit 1
fi
