#!/usr/bin/env python3
"""校验攀岩知识库的结构完整性。

检查的是结构，不是文风：
  - YAML front matter 能否解析
  - 必填字段是否齐全
  - ID 是否唯一、是否与文件名一致
  - 引用的 ID 是否真实存在（引用不能断裂）
  - 卡点是否至少给了两个候选解释
  - 标 `研究证据` 的单元是否给了可访问来源
  - 证据等级和审核状态取值是否合法

用法：python3 tools/validate.py [--quiet]
退出码：0 全部通过；1 存在错误
"""
import sys
import pathlib
import re

try:
    import yaml
except ImportError:
    sys.exit("需要 PyYAML：pip install pyyaml")

KB = pathlib.Path(__file__).resolve().parent.parent / "kb"

EVIDENCE_LEVELS = {"可确认事实", "研究证据", "专家共识", "专家假设", "证据不足"}
REVIEW_STATUSES = {"pending", "fact_checked", "climb_reviewed", "approved"}
UNIT_STATUSES = {"active", "draft", "deprecated"}

# type -> (目录, 必填字段)
REQUIRED = {
    "principle": ("principles", [
        "id", "type", "name", "one_liner", "meaning", "physics",
        "observables", "techniques", "sources", "evidence_level", "review"]),
    "physics": ("physics", [
        "id", "type", "name", "aliases", "one_liner", "strict_definition",
        "plain_explanation", "model_assumptions", "key_variables",
        "climbing_manifestation", "techniques", "misconceptions",
        "sources", "evidence_level", "review"]),
    "technique": ("techniques", [
        "id", "type", "name", "aliases", "layer", "one_liner", "solves",
        "applies_to", "not_applicable", "principles", "physics", "phases",
        "observables", "hints", "safety", "sources", "evidence_level", "review"]),
    "fault": ("faults", [
        "id", "type", "name", "aliases", "user_language", "observables",
        "candidate_explanations", "techniques", "hints", "tasks",
        "safety", "evidence_level", "review"]),
    "task": ("tasks", [
        "id", "type", "name", "goal", "technique_refs", "steps",
        "evidence", "fallback", "safety", "grade_range", "review"]),
}

# 哪些字段承载 ID 引用
REF_FIELDS = ["physics", "principles", "techniques", "tasks", "faults",
              "prerequisites", "technique_refs", "beta_refs", "cases"]

ID_PREFIX = {"PRIN": "principle", "PHY": "physics", "TEC": "technique",
             "FAULT": "fault", "TASK": "task"}

errors, warnings = [], []


def err(unit, msg):
    errors.append(f"[错误] {unit}: {msg}")


def warn(unit, msg):
    warnings.append(f"[警告] {unit}: {msg}")


def load_units():
    """读取所有单元，返回 {id: (front_matter, path)}。"""
    units = {}
    for path in sorted(KB.rglob("*.md")):
        raw = path.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n", raw, re.S)
        if not m:
            err(path.name, "缺少 YAML front matter")
            continue
        try:
            fm = yaml.safe_load(m.group(1))
        except yaml.YAMLError as e:
            err(path.name, f"YAML 解析失败：{e}")
            continue
        if not isinstance(fm, dict):
            err(path.name, "front matter 不是键值结构")
            continue
        uid = fm.get("id")
        if not uid:
            err(path.name, "缺少 id")
            continue
        if uid in units:
            err(path.name, f"id 重复：{uid} 已在 {units[uid][1].name} 中使用")
            continue
        if path.stem != uid:
            err(path.name, f"文件名与 id 不一致（id={uid}）")
        units[uid] = (fm, path)
    return units


def check_unit(uid, fm, path, units):
    utype = fm.get("type")
    if utype not in REQUIRED:
        err(uid, f"未知 type：{utype!r}")
        return
    expected_dir, required = REQUIRED[utype]
    if path.parent.name != expected_dir:
        err(uid, f"type={utype} 应当放在 kb/{expected_dir}/，实际在 kb/{path.parent.name}/")

    prefix = uid.split("-")[0]
    if ID_PREFIX.get(prefix) != utype:
        err(uid, f"id 前缀 {prefix} 与 type={utype} 不匹配")

    for field in required:
        if field not in fm:
            err(uid, f"缺少必填字段：{field}")
        elif fm[field] is None or (isinstance(fm[field], (list, str)) and len(fm[field]) == 0):
            # aliases、not_applicable 允许为空数组
            if field not in ("aliases",):
                err(uid, f"必填字段为空：{field}")

    # 证据等级
    lvl = fm.get("evidence_level")
    if utype != "task":
        if lvl not in EVIDENCE_LEVELS:
            err(uid, f"证据等级取值非法：{lvl!r}")
        elif lvl == "研究证据":
            srcs = fm.get("sources") or []
            if not any(s.get("url") for s in srcs if isinstance(s, dict)):
                err(uid, "标为『研究证据』但 sources 中没有任何可访问 url")

    # 单元状态
    st = fm.get("status")
    if st is not None and st not in UNIT_STATUSES:
        err(uid, f"status 取值非法：{st!r}")

    # 审核块
    review = fm.get("review")
    if isinstance(review, dict):
        if review.get("status") not in REVIEW_STATUSES:
            err(uid, f"review.status 取值非法：{review.get('status')!r}")
        if not re.match(r"^\d+\.\d+\.\d+$", str(review.get("version", ""))):
            err(uid, f"review.version 不是语义化版本：{review.get('version')!r}")
    elif "review" in fm:
        err(uid, "review 不是键值结构")

    # 卡点必须给多个候选解释
    if utype == "fault":
        cands = fm.get("candidate_explanations") or []
        if len(cands) < 2:
            err(uid, f"卡点必须至少给 2 个候选解释，当前 {len(cands)} 个")
        for i, c in enumerate(cands):
            if not isinstance(c, dict):
                err(uid, f"candidate_explanations[{i}] 不是键值结构")
                continue
            for k in ("explanation", "evidence_required"):
                if not c.get(k):
                    err(uid, f"candidate_explanations[{i}] 缺少 {k}")
            tref = c.get("technique")
            if tref and tref not in units:
                err(uid, f"candidate_explanations[{i}].technique 引用了不存在的 {tref}")

    # 技巧的三阶段
    if utype == "technique":
        phases = fm.get("phases")
        if isinstance(phases, dict):
            for p in ("prepare", "execute", "stabilize"):
                if not phases.get(p):
                    err(uid, f"phases 缺少 {p}")
        elif "phases" in fm:
            err(uid, "phases 不是键值结构")

    # 引用完整性
    for field in REF_FIELDS:
        for ref in fm.get(field) or []:
            if isinstance(ref, str) and ref not in units:
                err(uid, f"{field} 引用了不存在的 {ref}")


def check_crossrefs(units):
    """技巧↔物理、技巧↔卡点应当双向可达；单向的给警告不给错误。"""
    for uid, (fm, _) in units.items():
        if fm.get("type") != "technique":
            continue
        for phy in fm.get("physics") or []:
            back = units.get(phy, ({}, None))[0].get("techniques") or []
            if uid not in back:
                warn(phy, f"技巧 {uid} 引用了它，但它的 techniques 里没有回指")

    # 每个技巧至少要有一项现实任务，否则知识落不回岩馆
    for uid, (fm, _) in units.items():
        if fm.get("type") == "technique" and not (fm.get("tasks") or []):
            warn(uid, "没有关联任何现实任务，知识无法落回岩馆")

    # 首期 Beta 与案例为空是预期状态，统一提示一次
    empty_beta = [u for u, (fm, _) in units.items()
                  if fm.get("type") == "technique" and not (fm.get("beta_refs") or [])]
    if empty_beta:
        warn("首期状态", f"{len(empty_beta)} 个技巧尚未关联标准 Beta 片段（等待岩馆视频接入）")


def main():
    quiet = "--quiet" in sys.argv
    units = load_units()
    for uid, (fm, path) in units.items():
        check_unit(uid, fm, path, units)
    check_crossrefs(units)

    counts = {}
    for fm, _ in units.values():
        counts[fm.get("type")] = counts.get(fm.get("type"), 0) + 1

    if not quiet:
        print("知识库单元统计：")
        for t, (d, _) in REQUIRED.items():
            print(f"  {t:10s} {counts.get(t, 0):3d}")
        print(f"  {'合计':10s} {len(units):3d}\n")

    for w in warnings:
        print(w)
    if warnings and not quiet:
        print()
    for e in errors:
        print(e)

    if errors:
        print(f"\n校验失败：{len(errors)} 个错误，{len(warnings)} 个警告")
        return 1
    print(f"校验通过：{len(units)} 个单元，{len(warnings)} 个警告")
    return 0


if __name__ == "__main__":
    sys.exit(main())
