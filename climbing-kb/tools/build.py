#!/usr/bin/env python3
"""把知识库编译成检索用的 JSON。

产出两份：
  dist/kb.json           全量，供内容生产、专家审核和轻验证使用
  dist/kb.approved.json  仅 review.status == approved 的单元，供产品自动输出使用

分成两份是《知识库规范》06 节的要求：只有走完三类审核的单元
才能进入产品的自动反馈；未审核的内容可以用于内容生产和人工流程。

编译时补全反向索引：
  - 物理原理 → 引用它的技巧
  - 技巧 → 指向它的卡点
  - 用户语言 → 卡点（产品用自然语言定位问题的入口）

用法：python3 tools/build.py
"""
import json
import pathlib
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("需要 PyYAML：pip install pyyaml")

ROOT = pathlib.Path(__file__).resolve().parent.parent
KB, DIST = ROOT / "kb", ROOT / "dist"


def load():
    units = {}
    for path in sorted(KB.rglob("*.md")):
        raw = path.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
        if not m:
            continue
        fm = yaml.safe_load(m.group(1))
        fm["_body"] = m.group(2).strip()
        fm["_path"] = str(path.relative_to(ROOT))
        # 把文件体按二级标题切开，供下游分别取用
        sections = {}
        for sm in re.finditer(r"^## (.+?)\n(.*?)(?=^## |\Z)", m.group(2), re.S | re.M):
            sections[sm.group(1).strip()] = sm.group(2).strip()
        fm["_sections"] = sections
        units[fm["id"]] = fm
    return units


def build_indexes(units):
    """补全反向索引和自然语言入口。"""
    referenced_by = {uid: [] for uid in units}
    for uid, fm in units.items():
        for field in ("physics", "principles", "techniques", "tasks",
                      "faults", "prerequisites", "technique_refs"):
            for ref in fm.get(field) or []:
                if isinstance(ref, str) and ref in referenced_by:
                    referenced_by[ref].append({"id": uid, "via": field})
    for uid, fm in units.items():
        fm["_referenced_by"] = referenced_by[uid]

    # 用户语言 → 卡点：产品拿到一句用户抱怨时的第一跳
    phrase_index = {}
    for uid, fm in units.items():
        if fm.get("type") != "fault":
            continue
        for phrase in (fm.get("user_language") or []) + (fm.get("aliases") or []):
            phrase_index.setdefault(phrase, []).append(uid)

    # 术语 → 单元：别名归一
    alias_index = {}
    for uid, fm in units.items():
        for name in [fm.get("name")] + (fm.get("aliases") or []):
            if name:
                alias_index.setdefault(name, []).append(uid)

    return {"user_phrase_to_fault": phrase_index, "alias_to_unit": alias_index}


def summarize(units):
    by_type, by_evidence, by_review = {}, {}, {}
    for fm in units.values():
        by_type[fm.get("type")] = by_type.get(fm.get("type"), 0) + 1
        if fm.get("evidence_level"):
            lvl = fm["evidence_level"]
            by_evidence[lvl] = by_evidence.get(lvl, 0) + 1
        st = (fm.get("review") or {}).get("status")
        by_review[st] = by_review.get(st, 0) + 1
    return {"by_type": by_type, "by_evidence_level": by_evidence,
            "by_review_status": by_review, "total": len(units)}


def main():
    units = load()
    indexes = build_indexes(units)
    DIST.mkdir(exist_ok=True)

    full = {"version": "0.1.0", "summary": summarize(units),
            "indexes": indexes, "units": units}
    (DIST / "kb.json").write_text(
        json.dumps(full, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    approved = {uid: fm for uid, fm in units.items()
                if (fm.get("review") or {}).get("status") == "approved"}
    prod = {"version": "0.1.0", "summary": summarize(approved),
            "indexes": build_indexes(approved), "units": approved}
    (DIST / "kb.approved.json").write_text(
        json.dumps(prod, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print(f"dist/kb.json           {len(units):3d} 个单元（全量）")
    print(f"dist/kb.approved.json  {len(approved):3d} 个单元（已审核，可进入产品自动输出）")
    if not approved:
        print("\n注意：目前没有任何单元通过三类审核，产品自动输出为空。")
        print("这是首期的预期状态——内容已就绪，等待攀岩专家审核签署。")
    s = summarize(units)
    print("\n证据等级分布：")
    for lvl, n in sorted(s["by_evidence_level"].items(), key=lambda x: -x[1]):
        print(f"  {lvl:8s} {n:3d}")


if __name__ == "__main__":
    main()
