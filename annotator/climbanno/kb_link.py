"""把标注结果接回攀岩知识库。

这个 demo 和一个通用姿态叠加的区别，全在这个文件里：
它对照 climbing-kb 的 122 条 observables，回答一句话——

    **这段视频跑完，知识库里哪些「视频中能看见什么」是这条管线真的能给出的？**

没有这一层，标注只是好看的覆盖层；有了它，标注才是知识库的证据来源。
"""
from __future__ import annotations

import json
import pathlib

# 本管线实现到哪一档。P3 只做了「肢端—岩点邻近代理」，
# 没有做接触面精细判断（鞋踩在有效受力面还是边缘），所以标成 partial。
IMPLEMENTED = {"P0": "full", "P1": "partial", "P2": "none",
               "PX-AUDIO": "none", "P3": "partial", "P4": "none"}

# 本管线确实产出的 observable（按知识库原文匹配）
EMITTED = [
    ("PRIN-SPEED-005", "是否出现长时间停顿后才启动（犹豫）"),
    ("FAULT-HESITATE-013", "单次停顿的时长和全程停顿总时长"),
    ("FAULT-REACH-FIRST-005", "伸手动作与髋部移动的先后顺序"),
    ("TEC-POS-COM-001", "髋部在伸手之前有没有先移动"),
    ("PRIN-COM-003", "髋部的移动路径（髋部是重心最好的视觉代理）"),
    ("FAULT-WRONG-HAND-015", "是否出现同一个岩点上的换手动作"),
    ("TEC-POS-TENSION-003", "伸手的瞬间脚是否脱落"),
    ("FAULT-FOOT-CUT-003", "脚脱落与伸手动作之间的时间关系（是否同步发生）"),
]

NOT_MEASURED = [
    "接触力与各接触点的负荷分配",
    "摩擦系数与鞋底状态",
    "重心的三维位置（只给二维投影代理）",
    "髋部到墙面的度量距离（需要墙体坐标系，见 docs/03 的 P4）",
    "鞋踩在岩点有效受力面还是边缘（需要接触区精细视觉，P3 未完成部分）",
]


def _kb_root() -> pathlib.Path | None:
    here = pathlib.Path(__file__).resolve()
    for up in here.parents:
        cand = up / "climbing-kb"
        if (cand / "dist" / "kb.json").exists():
            return cand
    return None


def capability_report(summary: dict, n_holds: int) -> dict:
    """对照知识库给出能力覆盖报告。知识库不在时降级为静态声明。"""
    rep = {
        "implemented_tiers": IMPLEMENTED,
        "emitted_observables": [{"unit": u, "observable": o} for u, o in EMITTED],
        "not_measured": NOT_MEASURED,
        "evidence_discipline": (
            "所有接触状态为二维视觉邻近代理，不代表力学承重；"
            "阶段标签为运动学代理，不构成对稳定性的力学判断。"),
    }

    root = _kb_root()
    if root is None:
        rep["kb"] = "未找到 climbing-kb/dist/kb.json，跳过对照"
        return rep

    kb = json.loads((root / "dist" / "kb.json").read_text(encoding="utf-8"))
    total = sum(len(u.get("observables") or []) for u in kb["units"].values())

    # 校验 EMITTED 里引用的 observable 确实存在于知识库
    bad = []
    for uid, obs in EMITTED:
        u = kb["units"].get(uid)
        if not u or obs not in (u.get("observables") or []):
            bad.append(f"{uid} :: {obs}")

    cov = None
    mapfile = root / "perception" / "observable-capability-map.yaml"
    if mapfile.exists():
        try:
            import yaml
            cm = yaml.safe_load(mapfile.read_text(encoding="utf-8"))
            from collections import Counter
            c = Counter(t for tiers in cm["map"].values() for t in tiers)
            cov = {
                "本管线完整实现档位的条目数": c.get("P0", 0),
                "部分实现档位的条目数": c.get("P1", 0) + c.get("P3", 0),
                "未实现档位的条目数": (c.get("P2", 0) + c.get("P4", 0)
                                     + c.get("PX-AUDIO", 0)),
            }
        except Exception as e:                      # pragma: no cover
            cov = {"error": str(e)}

    rep["kb"] = {
        "path": str(root),
        "units": len(kb["units"]),
        "observables_total": total,
        "emitted_count": len(EMITTED),
        "tier_coverage": cov,
        "broken_references": bad or "无",
        "note": ("emitted_observables 是本次管线真的产出了证据的条目；"
                 "其余条目要么需要未实现的能力档位，要么需要跨视频对齐。"),
    }
    return rep
