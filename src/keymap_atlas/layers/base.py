"""所有层级共用的数据结构。

一个 Row = 一条快捷键。layer 用「N · 名称 › 子组」的形式，顶层名用 ` › `
切分，这样渲染时可以按层分组、按子组排序。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..i18n import aliases_for

ACTIVE = "生效"
INACTIVE = "未生效"


@dataclass
class Row:
    layer: str
    keys: list[str]
    action: str
    note: str = ""
    status: str = ACTIVE
    state: str | None = None       # ok / bad / unknown，None 表示不适用
    source: str = ""               # 这条来自哪个配置文件 / 接口

    @property
    def layer_top(self) -> str:
        return self.layer.split(" › ")[0]

    @property
    def keys_text(self) -> str:
        return " + ".join(self.keys)

    @property
    def keys_plain(self) -> str:
        return " ".join(self.keys)

    @property
    def aliases(self) -> str:
        return aliases_for(self.action, self.keys)

    @property
    def search_blob(self) -> str:
        # 层名也进检索串：HTML 页内搜「Fn」要能高亮到固件功能键那一组。
        return (self.action + " " + self.keys_plain + " " + self.note
                + " " + self.layer + " " + self.aliases).lower()

    @property
    def note_with_state(self) -> str:
        icon = {"ok": "✅ ", "bad": "⛔ ", "unknown": "❓ "}.get(self.state or "", "")
        return icon + self.note


class Collector:
    """每层一个 Collector 子类，实现 available() 与 collect()。"""

    name = "基类"

    def available(self) -> bool:
        return True

    def collect(self) -> list[Row]:
        raise NotImplementedError

    # 小工具：按层前缀添加
    def _rows(self) -> list[Row]:
        return []


@dataclass
class LayerResult:
    name: str
    rows: list[Row] = field(default_factory=list)
    skipped: str = ""       # 非空 = 这一层被跳过，原因是这个

    @property
    def count(self) -> int:
        return len(self.rows)

    @property
    def all_inactive(self) -> bool:
        return bool(self.rows) and all(r.status == INACTIVE for r in self.rows)
