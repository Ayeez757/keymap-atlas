# 六层从哪来

每层都回答三个问题：文件在哪、怎么解析、什么时候不生效。

## 1 · niri 合成器层

**文件**：`~/.config/niri/config.kdl`（默认值），递归跟随 `include optional=true "..."`。

**解析**：`binds { ... }` 里一个 `键位 { 动作 }` 是一条。`include` 是相对当前文件
所在目录解析的，同一文件只解析一次（防循环）。**同名键位后者覆盖前者**——
这是 niri 的真实语义，报告里会用备注标出「被某文件覆盖」。

**动作翻中文**：`spawn "dms" "screenshot" "region"` → 「截图：区域截图」，
`niri msg action close-window` → 「关闭窗口」。未收录的保留原文。

**键名**：`Mod` 是 niri 的修饰键别名（默认 Super），报告统一显示为 `Super`。

## 2 · 输入法层（fcitx5）

**文件**：`~/.config/fcitx5/config`。

**注意**：这个文件经常**整篇都是注释**（本机就是）。此时用 fcitx5 的内置默认值
`Ctrl+Space` 切换、左 Shift 临时中英切换、`Ctrl+Alt+P` 标点、`Tab/Shift+Tab`
翻页，并在备注里写明「配置里全是注释 → 用的是内置默认值」，不要假装是你配的。

## 3 · 终端应用层（Ghostty）

**文件**：`~/.config/ghostty/config`，每行 `keybind = 组合键=动作`。

**关键区别**：这些键**只有 Ghostty 窗口有焦点时才有效**，属于应用层，不是全局。
备注里一律带这句，否则用户会以为在任何地方按都行。

## 4 · 内核 / 硬件层

三个来源：

- **logind 电源键语义**：`busctl get-property org.freedesktop.login1 ... HandlePowerKey`
  等 11 个属性（电源键、睡眠键、休眠键、重启键、合盖、以及各自的长按版本）。
  读不到就用 systemd 出厂默认值并在备注注明。
- **SysRq**：`/proc/sys/kernel/sysrq` 的位掩码。**只有 mask & 1 时**才列
  `b/o/e/i/k/r` 这类「立刻生效」的组合；否则只列 `s`（同步）、`u`（重挂只读），
  因为其余组合在没有 1 位时不生效。
- **虚拟终端**：`Ctrl+Alt+F1…F12`。

## 5 · KDE 全局快捷键层（未生效）

**文件**：`~/.config/kglobalshortcutsrc`。

**最容易踩的坑**：值里多个键用**制表符**分隔，而文件里存的是**字面量 `\t`
（反斜杠 + t 两个字符）**，不是真 TAB。本机 16 行如此。必须
`val.replace("\\t", "\t")` 先还原，否则那一整行会被当成一条垃圾数据丢掉。

另一个坑：`[kwin][$InverseAction]` 段不是快捷键，是「反向动作」的元数据
（`Walk Through Windows` → `Walk Through Windows (Reverse)`），必须整段丢弃。

因为当前会话不是 KDE，整层标「未生效」——列出来是为了以后迁移时参考。

## 6 · GNOME 键位层（未生效）

**来源**：`gsettings list-recursively` 读三个 schema
（`wm.keybindings`、`shell.keybindings`、`mutter.keybindings`）。

值形如 `['<Super>t', '<Primary><Alt>t']`，用 `ast.literal_eval` 解析（不用
`gsettings describe`，那个输出是给人看的、不可解析）。`<Primary>` 归一成 `Ctrl`。

## 故意不列的层

| 层 | 为什么列不出来 | 自己怎么看 |
|---|---|---|
| Firefox / Chromium / Electron 应用内快捷键 | 编译进程序，或存在 profile 的加密库里 | 应用自己的「键盘快捷键」页 |
| GTK / Qt 的 `.ui` accel | 散布在源码与资源包，运行期才注册 | 无统一接口，只能看应用文档 |
| 键盘固件的 Fn 组合 | 键盘控制器自己处理，**操作系统完全看不到** | 按一下看有没有反应 |
| 浏览器扩展快捷键 | 存在各扩展自己的存储里 | `chrome://extensions/shortcuts` |
| portal `GlobalShortcuts` | 按会话/应用隔离，读别人会话会被 `Access denied` | 只能由应用自己上报 |
| Flatpak / Snap 自定义键 | 沙箱有自己的配置目录 | 进沙箱内看 |

最后一条的实测证据：对 Chromium 的会话
`/org/freedesktop/portal/desktop/session/1_440/chromium_global_shortcuts`
调用 `ListShortcuts` 返回 `Call failed: Access denied`；`CreateSession` 返回
`Call failed: An app id is required`。也就是说 portal 这条路**技术上存在但用不了**。
