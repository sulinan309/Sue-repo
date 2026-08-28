"""把证据翻译成用户看得懂的话。

**建议文案不在这里写，从知识库取。**

这是刻意的分工。管线负责「测到了什么」，知识库负责「该说什么」——
`hints` 字段本来就是按「最少剧透的一句话」写的，经过审核，
而且改文案不用改代码。这里只做三件事：

  1. 把测到的量翻译成她的体验（「高脚踩上去了，但没站起来」而不是
     「stall detected, knee median 39°」）
  2. 说清机制，一两句，不堆术语
  3. 从知识库拉出对应的提示和现实任务

数字尽量少露：0.43 倍躯干长对用户没有意义，画面里那条箭头才有意义。
"""
from __future__ import annotations

import dataclasses
import json
import pathlib


@dataclasses.dataclass
class Card:
    t0: float
    t1: float
    title: str            # 她的体验
    sub: str              # 一行上下文
    why: list[str]        # 为什么会这样，机制
    todo: list[str]       # 下次怎么做，来自知识库 hints
    task: str | None      # 一项现实任务
    units: list[str]      # 依据的知识单元，供追溯


def _kb():
    here = pathlib.Path(__file__).resolve()
    for up in here.parents:
        f = up / "climbing-kb" / "dist" / "kb.json"
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))["units"]
    return {}


def _hints(units, uid, n=1):
    u = units.get(uid) or {}
    return (u.get("hints") or [])[:n]


def _task(units, uid):
    u = units.get(uid) or {}
    for t in (u.get("tasks") or []):
        tu = units.get(t) or {}
        if tu.get("name"):
            return f"{tu['name']}（{t}）"
    return None


def from_stall(s, units) -> Card:
    """高脚停滞 → 用户卡片。"""
    side = "右" if s.leg == "R" else "左"
    other = "左" if s.leg == "R" else "右"
    why, todo, uids = [], [], []

    if abs(s.offset_med) > 0.30:
        why.append(f"你的重心一直在{side}脚的{'左' if s.offset_med < 0 else '右'}边，"
                   f"没有送到脚的正上方")
        why.append("腿蹬出去的力顺着腿的方向。重心在脚的侧后方时，"
                   "这股力主要是把你推离墙面，只有很小一部分往上")
        uids.append("FAULT-ROCKOVER-STALL-010")
        todo += _hints(units, "FAULT-ROCKOVER-STALL-010", 2)

    if s.knee_max < 100:
        why.append(f"{side}腿全程都是屈着的，一次都没真正打开")
        uids.append("TEC-MOV-ROCKOVER-002")
        if len(todo) < 3:
            todo += _hints(units, "TEC-MOV-ROCKOVER-002", 1)

    if s.other_knee_med > 160:
        why.append(f"{other}腿一直是直的，整段都没帮上忙")
        uids.append("TEC-MOV-FLAG-001")
        todo += _hints(units, "TEC-MOV-FLAG-001", 1)

    # 去重并保持顺序
    seen, todo2 = set(), []
    for x in todo:
        if x not in seen:
            seen.add(x)
            todo2.append(x)

    return Card(
        s.t0, s.t1,
        f"{side}脚踩上去了，但没站起来",
        f"{side}腿 · 在这个位置停了 {s.t1 - s.t0:.1f} 秒",
        why, todo2[:3],
        _task(units, uids[0]) if uids else None,
        uids)


def from_drive(d, units) -> Card | None:
    """发力事件 → 用户卡片。只在有话可说时返回。"""
    side = "右" if d.leg == "R" else "左"
    if d.chain == "hand_first":
        return Card(
            d.t_load, d.t_ext_end + 0.6,
            "手比腿先动了",
            f"{side}腿蹬起之前，手已经先离开了岩点",
            ["身体被手拉上去，重心会偏离承重脚，腿反而使不上力",
             "同样的高度，用手拉比用腿蹬费好几倍"],
            _hints(units, "FAULT-PULL-FIRST-011", 2),
            _task(units, "FAULT-PULL-FIRST-011"),
            ["FAULT-PULL-FIRST-011"])
    if d.success and d.lead is not None and d.lead > 0.05:
        return Card(
            d.t_load, d.t_ext_end + 0.6,
            "这次发力做对了",
            f"{side}腿先蹬、身体先升，手借着上升的窗口出手",
            [f"出手比身体起升晚 {d.lead:.2f} 秒，这个顺序让腿承担了主要的功"],
            [], None, ["PHY-KCHAIN-006"])
    return None


def build(stalls, drives) -> list[Card]:
    units = _kb()
    cards = [from_stall(s, units) for s in stalls]
    cards += [c for c in (from_drive(d, units) for d in drives) if c]
    cards.sort(key=lambda c: c.t0)
    return cards


def card_at(cards: list[Card], t: float) -> Card | None:
    for c in cards:
        if c.t0 <= t <= c.t1:
            return c
    return None


def summary(cards: list[Card]) -> list[dict]:
    return [{"时间": f"{c.t0:.1f}–{c.t1:.1f}s", "标题": c.title, "上下文": c.sub,
             "为什么": c.why, "下次这样试": c.todo, "练习任务": c.task,
             "依据": c.units} for c in cards]
