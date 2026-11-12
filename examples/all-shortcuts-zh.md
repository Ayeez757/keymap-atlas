# 全层级快捷键总表

> 当前检测到的键盘：**AT Translated Set 2 keyboard**  
> 键盘指纹：`265ce5c7254b088d`（换键盘后自动重算）  
> 生成时间：2026-11-13 01:02 CST

从 6 个可静态解析的层收集到 **350** 条快捷键。

| 层级 | 条数 | 状态 | 来源 |
|---|---|---|---|
| 1 · niri 合成器层 | 137 | 生效 | `/home/ayeez/.config/niri/dms/binds.kdl` |
| 2 · 输入法层（fcitx5） | 7 | 生效 | `/home/ayeez/.config/fcitx5/config` |
| 3 · 终端应用层（Ghostty） | 6 | 生效 | `/home/ayeez/.config/ghostty/config` |
| 4 · 内核 / 硬件层 | 28 | 生效 | `busctl org.freedesktop.login1.Manager` |
| 5 · KDE 全局快捷键层 | 114 | 未生效 | `/home/ayeez/.config/kglobalshortcutsrc` |
| 6 · GNOME 键位层 | 58 | 未生效 | `gsettings org.gnome.desktop.wm.keybindings activate-window-menu` |

**`Mod` = Super 键（Windows 徽标键）**。判定图标：✅ 实测按出 / ❓ 存疑 / ⛔ 硬件没有。

> **怎么让判定更准**：跑 `keymap-atlas probe` 把真实按键按一遍，结果写进状态目录；`keymap-atlas probe --absent Print` 可直接标注某个键你键盘上没有。实测优先于 `/proc/bus/input/devices` 的能力位图（位图会把通用 HID 数组误当成「有这个键」）。

## 1 · niri 合成器层 › 窗口 / 列管理（27 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Super + Q` | 关闭当前窗口 | ✅ 按住不重复 |
| `Alt + F4` | 关闭当前窗口 | ✅ 按住不重复 |
| `Super + F` | 最大化当前列 | ✅  |
| `Super + Shift + F` | 全屏切换 | ✅  |
| `Super + Shift + T` | 浮动窗口 / 平铺 切换 | ✅  |
| `Super + Shift + V` | 在浮动窗口与平铺窗口间切换焦点 | ✅  |
| `Super + W` | 列内标签页显示 切换 | ✅  |
| `Super + Shift + W` | 窗口规则编辑器 | ✅  |
| `Super + Shift + H` | 把当前列左移 | ✅  |
| `Super + Shift + J` | 把当前窗口下移 | ✅  |
| `Super + Shift + K` | 把当前窗口上移 | ✅  |
| `Super + Shift + L` | 把当前列右移 | ✅  |
| `Super + Ctrl + Home` | 把当前列移到最前 | ✅ 由固件接口上报（Intel HID events），未实测 |
| `Super + Ctrl + End` | 把当前列移到最后 | ✅ 由固件接口上报（Intel HID events），未实测 |
| `Super + [` | 窗口并入 / 推出到左列 | ✅  |
| `Super + ]` | 窗口并入 / 推出到右列 | ✅  |
| `Super + .` | 把窗口从列中拆出来 | ✅  |
| `Super + R` | 循环切换预设列宽 | ✅  |
| `Super + Shift + R` | 循环切换预设窗口高度 | ✅  |
| `Super + Ctrl + R` | 重置窗口高度 | ✅  |
| `Super + Ctrl + F` | 当前列扩展到可用宽度 | ✅  |
| `Super + C` | 当前列居中 | ✅  |
| `Super + Ctrl + C` | 可见列整体居中 | ✅  |
| `Super + -` | 列宽 -10%（缩小） | ✅  |
| `Super + =` | 列宽 +10%（放大） | ✅  |
| `Super + Shift + -` | 窗口高度 -10%（缩小） | ✅  |
| `Super + Shift + =` | 窗口高度 +10%（放大） | ✅  |

## 1 · niri 合成器层 › 焦点 / 窗口切换（14 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Alt + Tab` | 在最近使用窗口间切换（下一个）（限定当前显示器） | ✅  |
| `Alt + Shift + Tab` | 在最近使用窗口间切换（上一个）（限定当前显示器） | ✅  |
| `` Alt + ` `` | 在最近使用窗口间切换（下一个）（按应用分组） | ✅  |
| `` Alt + Shift + ` `` | 在最近使用窗口间切换（上一个）（按应用分组） | ✅  |
| `Super + H` | 聚焦左边一列 | ✅  |
| `Super + J` | 聚焦下方窗口 | ✅  |
| `Super + K` | 聚焦上方窗口 | ✅  |
| `Super + L` | 聚焦右边一列 | ✅  |
| `Super + Home` | 聚焦最左一列 | ✅ 由固件接口上报（Intel HID events），未实测 |
| `Super + End` | 聚焦最右一列 | ✅ 由固件接口上报（Intel HID events），未实测 |
| `Super + Ctrl + H` | 聚焦左侧显示器 | ✅  |
| `Super + Ctrl + J` | 聚焦下方显示器 | ✅  |
| `Super + Ctrl + K` | 聚焦上方显示器 | ✅  |
| `Super + Ctrl + L` | 聚焦右侧显示器 | ✅  |

## 1 · niri 合成器层 › 工作区（31 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Super + O` | 切换工作区总览（Overview） | ✅ 按住不重复 |
| `Super + Tab` | 切换工作区总览（Overview） | ✅ 按住不重复 |
| `Super + PgDn` | 切到下一个工作区 | ✅ 由固件接口上报（Intel HID events），未实测 |
| `Super + PgUp` | 切到上一个工作区 | ✅ 由固件接口上报（Intel HID events），未实测 |
| `Super + U` | 切到下一个工作区 | ✅  |
| `Super + I` | 切到上一个工作区 | ✅  |
| `Super + Ctrl + U` | 把当前列移到下一个工作区 | ✅  |
| `Super + Ctrl + I` | 把当前列移到上一个工作区 | ✅  |
| `Super + Alt + R` | 重命名当前工作区 | ✅  |
| `Super + Shift + PgDn` | 把本工作区顺序下移 | ✅ 由固件接口上报（Intel HID events），未实测 |
| `Super + Shift + PgUp` | 把本工作区顺序上移 | ✅ 由固件接口上报（Intel HID events），未实测 |
| `Super + Shift + U` | 把本工作区顺序下移 | ✅  |
| `Super + Shift + I` | 把本工作区顺序上移 | ✅  |
| `Super + 1` | 切换到工作区 1 | ✅  |
| `Super + 2` | 切换到工作区 2 | ✅  |
| `Super + 3` | 切换到工作区 3 | ✅  |
| `Super + 4` | 切换到工作区 4 | ✅  |
| `Super + 5` | 切换到工作区 5 | ✅  |
| `Super + 6` | 切换到工作区 6 | ✅  |
| `Super + 7` | 切换到工作区 7 | ✅  |
| `Super + 8` | 切换到工作区 8 | ✅  |
| `Super + 9` | 切换到工作区 9 | ✅  |
| `Super + Shift + 1` | 把当前列移到工作区 1 | ✅  |
| `Super + Shift + 2` | 把当前列移到工作区 2 | ✅  |
| `Super + Shift + 3` | 把当前列移到工作区 3 | ✅  |
| `Super + Shift + 4` | 把当前列移到工作区 4 | ✅  |
| `Super + Shift + 5` | 把当前列移到工作区 5 | ✅  |
| `Super + Shift + 6` | 把当前列移到工作区 6 | ✅  |
| `Super + Shift + 7` | 把当前列移到工作区 7 | ✅  |
| `Super + Shift + 8` | 把当前列移到工作区 8 | ✅  |
| `Super + Shift + 9` | 把当前列移到工作区 9 | ✅  |

## 1 · niri 合成器层 › 显示器 / 输出（6 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Super + Shift + Ctrl + H` | 把当前列移到左侧显示器 | ✅  |
| `Super + Shift + Ctrl + J` | 把当前列移到下方显示器 | ✅  |
| `Super + Shift + Ctrl + K` | 把当前列移到上方显示器 | ✅  |
| `Super + Shift + Ctrl + L` | 把当前列移到右侧显示器 | ✅  |
| `Super + P` | 循环切换显示器配置方案 | ✅  |
| `Super + Shift + P` | 关闭显示器（省电） | ✅  |

## 1 · niri 合成器层 › 声音 / 亮度 / 媒体（6 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Super + A` | 控制中心（音量、亮度、网络等） | ✅  |
| `Super + Alt + =` | 系统音量 +3% | ✅  |
| `Super + Alt + -` | 系统音量 -3% | ✅  |
| `Super + Alt + 0` | 系统静音 切换 | ✅  |
| `Super + Alt + Shift + =` | 屏幕亮度 +10% | ✅  |
| `Super + Alt + Shift + -` | 屏幕亮度 -10% | ✅  |

## 1 · niri 合成器层 › 截图（6 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `PrtSc` | 截图：区域截图 | ⛔ 你标记为「本机键盘没有这个键」 |
| `Ctrl + PrtSc` | 截图：全屏截图 | ⛔ 你标记为「本机键盘没有这个键」 |
| `Alt + PrtSc` | 截图：窗口截图 | ⛔ 你标记为「本机键盘没有这个键」 |
| `Super + Alt + S` | 截图：区域截图 | ✅  |
| `Super + Alt + Shift + F` | 截图：全屏截图 | ✅  |
| `Super + Alt + Ctrl + S` | 截图：窗口截图 | ✅  |

## 1 · niri 合成器层 › 应用 / 系统面板（22 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Super + Shift + /` | 快捷键面板 | ✅  |
| `Super + T` | 打开终端 | ✅  |
| `Super + Enter` | 打开终端 | ✅  |
| `Super + Space` | 打开 / 关闭 启动器 Spotlight | ✅  |
| `Alt + Space` | 打开 / 关闭 顶部 Spotlight 输入条 | ✅  |
| `Super + V` | 剪贴板历史 | ✅  |
| `Super + M` | 打开 Dash 面板（媒体页） | ✅  |
| `Super + X` | 电源菜单（关机 / 重启 / 注销） | ✅  |
| `Super + D` | 打开 Dash 面板 | ✅  |
| `Super + Shift + C` | 屏幕取色器 | ✅  |
| `Super + Alt + N` | 夜间模式（护眼色温） | ✅  |
| `Super + Alt + I` | 阻止休眠 / 息屏 切换 | ✅  |
| `Super + ,` | DMS 设置面板 | ✅  |
| `Super + Y` | 打开 Dash 面板（壁纸页） | ✅  |
| `Super + N` | 便签 | ✅  |
| `Super + Shift + N` | 便签（展开） | ✅  |
| `Super + Ctrl + N` | 通知中心 | ✅  |
| `Super + Alt + L` | 锁屏 | ✅  |
| `Super + Shift + E` | 退出 niri（关闭整个会话） | ✅  |
| `Ctrl + Alt + Del` | 进程管理器 | ✅  |
| `Ctrl + Alt + M` | 进程管理器 | ✅  |
| `Super + Esc` | 切换「快捷键抑制」（把按键交还应用） | ✅ 由固件接口上报（Ideapad extra buttons），未实测；应用接管按键时仍生效 |

## 1 · niri 合成器层 › 多媒体 / 专用键（18 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `音量+` | 系统音量 +3% | ✅ 由固件接口上报（Intel HID 5 button array、Intel HID events），未实测；锁屏时也生效 |
| `音量-` | 系统音量 -3% | ✅ 由固件接口上报（Intel HID 5 button array、Intel HID events），未实测；锁屏时也生效 |
| `静音` | 系统静音 切换 | ✅ 由固件接口上报（Intel HID events），未实测；锁屏时也生效 |
| `麦静音` | 麦克风静音 切换 | ✅ 由固件接口上报（Ideapad extra buttons），未实测；锁屏时也生效 |
| `播放` | 播放 / 暂停（当前播放器） | ✅ 由固件接口上报（Intel HID events），未实测；锁屏时也生效 |
| `播放` | 播放 / 暂停（当前播放器） | ✅ 由固件接口上报（Intel HID events），未实测；锁屏时也生效 |
| `上一曲` | 上一曲 | ❓ Consumer 页只由 GXTP5100:00 27C6:01E9 声明（非键盘设备）→ 需实测；锁屏时也生效 |
| `下一曲` | 下一曲 | ❓ Consumer 页只由 GXTP5100:00 27C6:01E9 声明（非键盘设备）→ 需实测；锁屏时也生效 |
| `Ctrl + 音量+` | 播放器音量 +3% | ✅ 由固件接口上报（Intel HID 5 button array、Intel HID events），未实测；锁屏时也生效 |
| `Ctrl + 音量-` | 播放器音量 -3% | ✅ 由固件接口上报（Intel HID 5 button array、Intel HID events），未实测；锁屏时也生效 |
| `亮度+` | 屏幕亮度 +5% | ✅ 由固件接口上报（Intel HID events、Video Bus），未实测；锁屏时也生效 |
| `亮度-` | 屏幕亮度 -5% | ✅ 由固件接口上报（Intel HID events、Video Bus），未实测；锁屏时也生效 |
| `触控板` | 触摸板开关 | ✅ 由固件接口上报（Ideapad extra buttons），未实测；锁屏时也生效；按住不重复 |
| `触控板开` | 显示触摸板状态提示 | ✅ 由固件接口上报（Ideapad extra buttons），未实测；锁屏时也生效；按住不重复 |
| `触控板关` | 显示触摸板状态提示 | ❓ 文件层面无法判定，需实测；锁屏时也生效；按住不重复 |
| `Launch1` | 截图：区域截图 | ✅ 由固件接口上报（Ideapad extra buttons），未实测 |
| `Ctrl + Launch1` | 截图：全屏截图 | ✅ 由固件接口上报（Ideapad extra buttons），未实测 |
| `Alt + Launch1` | 截图：窗口截图 | ✅ 由固件接口上报（Ideapad extra buttons），未实测 |

## 1 · niri 合成器层 › 其它（7 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Super + Alt + /` | 运行 bash | ✅  |
| `Super + Alt + Shift + /` | 运行 bash | ✅  |
| `Super + Alt + Shift + V` | 运行 screencast-menu | ✅  |
| `Super + Alt + Shift + R` | 运行 screencast | ✅  |
| `Super + Alt + Shift + S` | 运行 screencast | ✅  |
| `Super + Alt + Shift + M` | 运行 screencast | ✅  |
| `Super + Alt + Shift + N` | 运行 screencast | ✅  |

## 2 · 输入法层（fcitx5）（7 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Ctrl + Space` | 激活 / 关闭当前输入法 | 配置里全是注释 → fcitx5 内置默认值 |
| `左Shift` | 切换中英文（临时切换） | 配置里全是注释 → fcitx5 内置默认值 |
| `Ctrl + Alt + P` | 切换预编辑文本显示 | 配置里全是注释 → fcitx5 内置默认值 |
| `Tab` | 下一个候选词 | 配置里全是注释 → fcitx5 内置默认值 |
| `Shift + Tab` | 上一个候选词 | 配置里全是注释 → fcitx5 内置默认值 |
| `↓` | 候选词下一页 | 配置里全是注释 → fcitx5 内置默认值 |
| `↑` | 候选词上一页 | 配置里全是注释 → fcitx5 内置默认值 |

## 3 · 终端应用层（Ghostty）（6 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Ctrl + Shift + N` | 新建窗口 | 仅 Ghostty 窗口有焦点时生效 |
| `Ctrl + T` | 新建标签页 | 仅 Ghostty 窗口有焦点时生效 |
| `Ctrl + =` | 放大字体 | 仅 Ghostty 窗口有焦点时生效 |
| `Ctrl + -` | 缩小字体 | 仅 Ghostty 窗口有焦点时生效 |
| `Ctrl + 0` | 重置字体大小 | 仅 Ghostty 窗口有焦点时生效 |
| `Shift + Enter` | 直接输入 换行符 | 仅 Ghostty 窗口有焦点时生效 |

## 4 · 内核 / 硬件层 › 电源与盖子（11 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `合盖` | 按下休眠键 → s "hibernate | logind 的 HandleHibernateKey=s "hibernate |
| `合盖` | 长按休眠键 → s "ignore | logind 的 HandleHibernateKeyLongPress=s "ignore |
| `合盖` | 合上笔记本盖子 → s "suspend | logind 的 HandleLidSwitch=s "suspend |
| `合盖` | 合盖（已接扩展坞时） → s "ignore | logind 的 HandleLidSwitchDocked=s "ignore |
| `电源键` | 合盖（接电源时） → s  | logind 的 HandleLidSwitchExternalPower=s  |
| `电源键` | 按下电源键 → s "poweroff | logind 的 HandlePowerKey=s "poweroff |
| `电源键` | 长按电源键 → s "ignore | logind 的 HandlePowerKeyLongPress=s "ignore |
| `合盖` | 按下重启键 → s "reboot | logind 的 HandleRebootKey=s "reboot |
| `合盖` | 长按重启键 → s "poweroff | logind 的 HandleRebootKeyLongPress=s "poweroff |
| `合盖` | 按下睡眠键 → s "suspend | logind 的 HandleSuspendKey=s "suspend |
| `合盖` | 长按睡眠键 → s "hibernate | logind 的 HandleSuspendKeyLongPress=s "hibernate |

## 4 · 内核 / 硬件层 › 紧急救援（SysRq）（3 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Alt + SysRq + ?` | 直接触发内核级操作 | 当前 /proc/sys/kernel/sysrq=16：只允许同步等少数功能（写不了文件系统） |
| `Alt + SysRq + S` | 同步所有已挂载文件系统 | SysRq 组合：内核直接处理，绕过所有用户态程序 |
| `Alt + SysRq + U` | 重新挂载为只读 | SysRq 组合：内核直接处理，绕过所有用户态程序 |

## 4 · 内核 / 硬件层 › 虚拟终端（VT）（2 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Ctrl + Alt + F1 … F12` | 切换到内核虚拟终端 tty1–tty12 | 内核 vt 子系统处理；tty1 通常是没有图形界面时的登录终端 |
| `Ctrl + Alt + F7` | 切回图形界面所在的 VT | 多数发行版图形会话在 tty2 或 tty1，不确定时按 Ctrl+Alt+F1/F2 试 |

## 4 · 内核 / 硬件层 › 固件功能键（Fn 行）（12 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `静音` | 切换系统静音 | 固件上报键码 113（Intel HID events），配置里没有绑定；按 Fn 组合时系统看到的是这个键码，不是 F 键编号 |
| `音量-` | 降低系统音量（由桌面按固定步长处理） | 固件上报键码 114（Intel HID 5 button array），配置里没有绑定；按 Fn 组合时系统看到的是这个键码，不是 F 键编号 |
| `音量+` | 提高系统音量（由桌面按固定步长处理） | 固件上报键码 115（Intel HID 5 button array），配置里没有绑定；按 Fn 组合时系统看到的是这个键码，不是 F 键编号 |
| `自定义键` | 由厂商定义的附加键（常见为截图或性能模式） | 固件上报键码 148（Ideapad extra buttons），配置里没有绑定；按 Fn 组合时系统看到的是这个键码，不是 F 键编号 |
| `播放/暂停` | 播放或暂停当前媒体 | 固件上报键码 164（Intel HID events），配置里没有绑定；按 Fn 组合时系统看到的是这个键码，不是 F 键编号 |
| `摄像头` | 开 / 关摄像头 | 固件上报键码 212（Ideapad extra buttons），配置里没有绑定；按 Fn 组合时系统看到的是这个键码，不是 F 键编号 |
| `亮度-` | 降低屏幕亮度 | 固件上报键码 224（Intel HID events），配置里没有绑定；按 Fn 组合时系统看到的是这个键码，不是 F 键编号 |
| `亮度+` | 提高屏幕亮度 | 固件上报键码 225（Intel HID events），配置里没有绑定；按 Fn 组合时系统看到的是这个键码，不是 F 键编号 |
| `亮度循环` | 循环调节亮度 | 固件上报键码 243（Video Bus），配置里没有绑定；按 Fn 组合时系统看到的是这个键码，不是 F 键编号 |
| `麦克风静音` | 切换麦克风静音 | 固件上报键码 248（Ideapad extra buttons），配置里没有绑定；按 Fn 组合时系统看到的是这个键码，不是 F 键编号 |
| `触摸板开关` | 开 / 关触摸板 | 固件上报键码 530（Ideapad extra buttons），配置里没有绑定；按 Fn 组合时系统看到的是这个键码，不是 F 键编号 |
| `触摸板开` | 打开触摸板 | 固件上报键码 532（Ideapad extra buttons），配置里没有绑定；按 Fn 组合时系统看到的是这个键码，不是 F 键编号 |

## 5 · KDE 全局快捷键层 › 键盘布局切换（2 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Super + Alt + L` | 切换到上次使用过的键盘布局 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Alt + K` | 切换到下一个键盘布局 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |

## 5 · KDE 全局快捷键层 › 音量（9 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Microphone Volume Down` | 降低麦克风音量 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Volume Down` | 降低音量 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Shift + Volume Down` | 音量降低 1% | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Microphone Volume Up` | 提高麦克风音量 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Volume Up` | 提高音量 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Shift + Volume Up` | 音量提高 1% | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Microphone Mute` | 麦克风静音 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Volume Mute` | 麦克风静音 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Volume Mute` | 静音 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |

## 5 · KDE 全局快捷键层 › 会话管理（3 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Screensaver` | 锁定会话 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + L` | 锁定会话 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Ctrl + Alt + Del` | 显示注销屏幕 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |

## 5 · KDE 全局快捷键层 › 窗口管理器（59 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Super + Ctrl + A` | 激活请求注意的窗口 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + T` | 磁贴编辑器开关 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Ctrl + F9` | 显示/隐藏窗口平铺 (当前桌面) | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + F9` | 显示/隐藏窗口平铺 (当前桌面) | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Launch (C)` | 显示/隐藏窗口平铺 (全部桌面) | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Ctrl + F10` | 显示/隐藏窗口平铺 (全部桌面) | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + F10` | 显示/隐藏窗口平铺 (全部桌面) | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Ctrl + F7` | 显示/隐藏窗口平铺 (窗口类) | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + F7` | 显示/隐藏窗口平铺 (窗口类) | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + G` | 切换网格视图 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Ctrl + Esc` | 强制终止窗口 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + F6` | 指针移至屏幕中心 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + F5` | 指针移至焦点窗口中心 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + W` | 显示/隐藏桌面总览 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + D` | 暂时显示桌面 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Ctrl + ↓` | 切换到下方桌面 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Ctrl + ↑` | 切换到上方桌面 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Ctrl + ←` | 切换到左侧桌面 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Ctrl + →` | 切换到右侧桌面 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Alt + ↓` | 切换到下面的窗口 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Alt + ←` | 切换到左侧的窗口 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Alt + →` | 切换到右侧的窗口 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Alt + ↑` | 切换到上面的窗口 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Ctrl + F1` | 切换到桌面 1 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + F1` | 切换到桌面 1 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Ctrl + F2` | 切换到桌面 2 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + F2` | 切换到桌面 2 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Ctrl + F3` | 切换到桌面 3 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + F3` | 切换到桌面 3 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Ctrl + F4` | 切换到桌面 4 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + F4` | 切换到桌面 4 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Alt + Tab` | 遍历窗口 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Tab` | 遍历窗口 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Alt + Shift + Tab` | 遍历窗口 (反向) | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Shift + Tab` | 遍历窗口 (反向) | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `` Alt + ` `` | 遍历当前应用程序窗口 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `` Super + ` `` | 遍历当前应用程序窗口 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Alt + ~` | 遍历当前应用程序窗口 (反向) | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + ~` | 遍历当前应用程序窗口 (反向) | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Alt + F4` | 关闭窗口 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + PgUp` | 最大化窗口 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + PgDown` | 最小化窗口 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Ctrl + Shift + ↓` | 窗口下移一个桌面 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Ctrl + Shift + ↑` | 窗口上移一个桌面 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Ctrl + Shift + ←` | 窗口左移一个桌面 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Ctrl + Shift + →` | 窗口右移一个桌面 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Alt + F3` | 窗口菜单 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + ↓` | 快速铺放窗口到下方 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + ←` | 快速铺放窗口到左侧 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + →` | 快速铺放窗口到右侧 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + ↑` | 快速铺放窗口到上方 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Backspace` | 恢复窗口 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Shift + →` | 移动窗口到下一屏幕 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Shift + ←` | 移动窗口到上一屏幕 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Shift + Esc` | 禁用活动输入捕获 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + 0` | 缩放为实际大小(A) | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super +  + ` | 放大(I) | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + =` | 放大(I) | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + -` | 缩小(O) | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |

## 5 · KDE 全局快捷键层 › mediacontrol（7 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Media Next` | 播放下一首媒体 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Media Pause` | 暂停媒体播放 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Media Play` | 播放/暂停媒体播放 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Media Previous` | 播放上一首媒体 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Media Rewind` | 媒体播放向后时移 5 秒 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Media Fast Forward` | 媒体播放向前时移 5 秒 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Media Stop` | 停止媒体播放 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |

## 5 · KDE 全局快捷键层 › 电源管理（13 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Keyboard Brightness Down` | 降低键盘亮度 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Monitor Brightness Down` | 降低屏幕亮度 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Shift + Monitor Brightness Down` | 降低屏幕亮度 1% | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Hibernate` | 休眠 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Keyboard Brightness Up` | 提高键盘亮度 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Monitor Brightness Up` | 提高屏幕亮度 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Shift + Monitor Brightness Up` | 提高屏幕亮度 1% | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Power Down` | 断电 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Power Off` | 关机 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Sleep` | 挂起 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Keyboard Light On/Off` | 开关键盘背光 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Battery` | 切换电源管理方案 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + B` | 切换电源管理方案 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |

## 5 · KDE 全局快捷键层 › Plasma 桌面（21 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Super` | 激活应用程序启动器 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Alt + F1` | 激活应用程序启动器 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Ctrl + PgDown` | 激活下一个任务管理器条目 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Ctrl + PgUp` | 激活上一个任务管理器条目 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + 1` | 激活任务管理器条目 1 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + 2` | 激活任务管理器条目 2 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + 3` | 激活任务管理器条目 3 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + 4` | 激活任务管理器条目 4 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + 5` | 激活任务管理器条目 5 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + 6` | 激活任务管理器条目 6 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + 7` | 激活任务管理器条目 7 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + 8` | 激活任务管理器条目 8 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + 9` | 激活任务管理器条目 9 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Alt + P` | 在面板之间移动键盘焦点 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Q` | 显示活动切换器 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Ctrl + Shift + PgUp` | 向后移动活动任务管理器条目 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Ctrl + Shift + PgDown` | 向前移动活动任务管理器条目 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + A` | 遍历活动 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + Shift + A` | 遍历活动 (反向) | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Ctrl + F12` | 显示桌面 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |
| `Super + V` | 在鼠标位置显示剪贴板项目 | 当前会话不是 KDE，这些绑定不生效；进 KDE 会话才会用 |

## 6 · GNOME 键位层 › keybindings（58 条）

| 按键 | 功能 | 备注 |
|---|---|---|
| `Alt + Space` | 打开窗口菜单 | 当前会话不是 GNOME，这些键位不生效 |
| `Alt + F7` | 开始移动窗口 | 当前会话不是 GNOME，这些键位不生效 |
| `Alt + F8` | 开始调整窗口大小 | 当前会话不是 GNOME，这些键位不生效 |
| `Alt + F4` | 关闭窗口 | 当前会话不是 GNOME，这些键位不生效 |
| `Alt + F6` | cycle group | 当前会话不是 GNOME，这些键位不生效 |
| `Shift + Alt + F6` | cycle group backward | 当前会话不是 GNOME，这些键位不生效 |
| `Ctrl + Alt + Esc` | cycle panels | 当前会话不是 GNOME，这些键位不生效 |
| `Shift + Ctrl + Alt + Esc` | cycle panels backward | 当前会话不是 GNOME，这些键位不生效 |
| `Alt + Esc` | cycle windows | 当前会话不是 GNOME，这些键位不生效 |
| `Shift + Alt + Esc` | cycle windows backward | 当前会话不是 GNOME，这些键位不生效 |
| `Super + ↑` | 最大化窗口 | 当前会话不是 GNOME，这些键位不生效 |
| `Super + H` | 最小化窗口 | 当前会话不是 GNOME，这些键位不生效 |
| `Super + Shift + ↓` | move to monitor down | 当前会话不是 GNOME，这些键位不生效 |
| `Super + Shift + ←` | move to monitor left | 当前会话不是 GNOME，这些键位不生效 |
| `Super + Shift + →` | move to monitor right | 当前会话不是 GNOME，这些键位不生效 |
| `Super + Shift + ↑` | move to monitor up | 当前会话不是 GNOME，这些键位不生效 |
| `Super + Shift + Home` | move to workspace 1 | 当前会话不是 GNOME，这些键位不生效 |
| `Ctrl + Shift + Alt + ↓` | move to workspace down | 当前会话不是 GNOME，这些键位不生效 |
| `Super + Shift + End` | move to workspace last | 当前会话不是 GNOME，这些键位不生效 |
| `Super + Shift + PgUp` | 把窗口移到左边工作区 | 当前会话不是 GNOME，这些键位不生效 |
| `Super + Shift + KP_Prior` | 把窗口移到左边工作区 | 当前会话不是 GNOME，这些键位不生效 |
| `Super + Shift + Alt + ←` | 把窗口移到左边工作区 | 当前会话不是 GNOME，这些键位不生效 |
| `Ctrl + Shift + Alt + ←` | 把窗口移到左边工作区 | 当前会话不是 GNOME，这些键位不生效 |
| `Super + Shift + PgDn` | 把窗口移到右边工作区 | 当前会话不是 GNOME，这些键位不生效 |
| `Super + Shift + KP_Next` | 把窗口移到右边工作区 | 当前会话不是 GNOME，这些键位不生效 |
| `Super + Shift + Alt + →` | 把窗口移到右边工作区 | 当前会话不是 GNOME，这些键位不生效 |
| `Ctrl + Shift + Alt + →` | 把窗口移到右边工作区 | 当前会话不是 GNOME，这些键位不生效 |
| `Ctrl + Shift + Alt + ↑` | move to workspace up | 当前会话不是 GNOME，这些键位不生效 |
| `Alt + F2` | 打开运行命令对话框 | 当前会话不是 GNOME，这些键位不生效 |
| `Super + Tab` | 切换应用（同一应用多窗口） | 当前会话不是 GNOME，这些键位不生效 |
| `Alt + Tab` | 切换应用（同一应用多窗口） | 当前会话不是 GNOME，这些键位不生效 |
| `Shift + Super + Tab` | 反向切换应用 | 当前会话不是 GNOME，这些键位不生效 |
| `Shift + Alt + Tab` | 反向切换应用 | 当前会话不是 GNOME，这些键位不生效 |
| `Super + Above_Tab` | 切换同应用窗口分组 | 当前会话不是 GNOME，这些键位不生效 |
| `Alt + Above_Tab` | 切换同应用窗口分组 | 当前会话不是 GNOME，这些键位不生效 |
| `Shift + Super + Above_Tab` | switch group backward | 当前会话不是 GNOME，这些键位不生效 |
| `Shift + Alt + Above_Tab` | switch group backward | 当前会话不是 GNOME，这些键位不生效 |
| `Super + Space` | 切换输入源（键盘布局） | 当前会话不是 GNOME，这些键位不生效 |
| `XF86Keyboard` | 切换输入源（键盘布局） | 当前会话不是 GNOME，这些键位不生效 |
| `Shift + Super + Space` | 反向切换键盘布局 | 当前会话不是 GNOME，这些键位不生效 |
| `Shift + XF86Keyboard` | 反向切换键盘布局 | 当前会话不是 GNOME，这些键位不生效 |
| `Ctrl + Alt + Tab` | switch panels | 当前会话不是 GNOME，这些键位不生效 |
| `Shift + Ctrl + Alt + Tab` | switch panels backward | 当前会话不是 GNOME，这些键位不生效 |
| `Super + Home` | switch to workspace 1 | 当前会话不是 GNOME，这些键位不生效 |
| `Ctrl + Alt + ↓` | 切到下边工作区 | 当前会话不是 GNOME，这些键位不生效 |
| `Super + End` | switch to workspace last | 当前会话不是 GNOME，这些键位不生效 |
| `Super + PgUp` | 切到左边工作区 | 当前会话不是 GNOME，这些键位不生效 |
| `Super + KP_Prior` | 切到左边工作区 | 当前会话不是 GNOME，这些键位不生效 |
| `Super + Alt + ←` | 切到左边工作区 | 当前会话不是 GNOME，这些键位不生效 |
| `Ctrl + Alt + ←` | 切到左边工作区 | 当前会话不是 GNOME，这些键位不生效 |
| `Super + PgDn` | 切到右边工作区 | 当前会话不是 GNOME，这些键位不生效 |
| `Super + KP_Next` | 切到右边工作区 | 当前会话不是 GNOME，这些键位不生效 |
| `Super + Alt + →` | 切到右边工作区 | 当前会话不是 GNOME，这些键位不生效 |
| `Ctrl + Alt + →` | 切到右边工作区 | 当前会话不是 GNOME，这些键位不生效 |
| `Ctrl + Alt + ↑` | 切到上边工作区 | 当前会话不是 GNOME，这些键位不生效 |
| `Alt + F10` | toggle maximized | 当前会话不是 GNOME，这些键位不生效 |
| `Super + ↓` | 取消最大化 | 当前会话不是 GNOME，这些键位不生效 |
| `Alt + F5` | 取消最大化 | 当前会话不是 GNOME，这些键位不生效 |

## 7 · 无法静态枚举的层

下面这些**没有统一的枚举接口**，任何工具都读不出完整清单，只能进各自的地方看：

| 层 | 为什么读不出来 | 怎么查 |
|---|---|---|
| Firefox / Chromium / Electron 应用内快捷键 | 编译进程序或存在 profile 的加密库里，没有统一的导出接口 | 菜单 → 帮助 → 键盘快捷键；Firefox 也可在 about:config 搜 key_ 前缀 |
| GTK / Qt 的 .ui 文件与代码里的 accel | 散布在源码与资源包里，运行期才注册，没有枚举 API | 应用内「快捷键」设置页；或 grep accel 对应的 .ui 文件 |
| 键盘固件里的 Fn 组合本身（Fn 是不是硬件层、能不能改） | Fn 由键盘控制器自己处理，操作系统看不到按下 Fn 这个动作；它发出的功能键码已在内核层的「固件功能键（Fn 行）」里列出 | 查键盘说明书；或 sudo libinput debug-events --show-keycodes 实测 |
| 浏览器扩展的快捷键 | 存在各扩展自己的存储里，需要逐个读取扩展数据目录 | 扩展自己的快捷键设置页 |
| Wayland 的 xdg-desktop-portal GlobalShortcuts | 按会话／应用隔离：对其他应用的会话调用 ListShortcuts 会被 Access denied | busctl --user tree org.freedesktop.portal.Desktop 能看到会话属主，读不到内容 |
| Flatpak / Snap 应用的自定义键 | 沙箱有自己的配置目录，路径与宿主不同 | 进 flatpak run --command=sh 的应用沙箱里看 ~/.config |

**本机可直接看的入口**：niri + DMS 的快捷键面板（默认 `Mod+Shift+/`）、DMS 设置。
