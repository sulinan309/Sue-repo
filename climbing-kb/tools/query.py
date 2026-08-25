#!/usr/bin/env python3
"""按用户语言、关键词或 ID 检索知识库。

这是攀岩专家模型的检索路径原型，也是项目三「MVP 核心环节轻验证」的调用入口。
它演示知识库要求的那条链路：

    用户的一句话 → 卡点 → 多个候选解释（各带证据要求）
                        → 局部提示 → 现实任务 → 物理原理

用法：
    python3 tools/query.py 脚滑              # 按用户语言或关键词
    python3 tools/query.py TEC-MOV-FLAG-001  # 按 ID
    python3 tools/query.py --list faults     # 列出某一类的全部单元
    python3 tools/query.py --chain FAULT-FOOT-SLIP-001   # 展开完整解题链
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
KBJSON = ROOT / "dist" / "kb.json"

C = {"h": "\033[1m", "d": "\033[2m", "y": "\033[33m", "c": "\033[36m", "0": "\033[0m"}
if not sys.stdout.isatty():
    C = {k: "" for k in C}


def load():
    if not KBJSON.exists():
        sys.exit("找不到 dist/kb.json，先运行：python3 tools/build.py")
    return json.loads(KBJSON.read_text(encoding="utf-8"))


def show_unit(kb, uid, indent=""):
    u = kb["units"].get(uid)
    if not u:
        print(f"{indent}{C['y']}[缺失]{C['0']} {uid}")
        return
    lvl = u.get("evidence_level", "")
    tag = f" {C['d']}[{lvl}]{C['0']}" if lvl else ""
    print(f"{indent}{C['h']}{uid}{C['0']}  {u.get('name','')}{tag}")
    if u.get("one_liner"):
        print(f"{indent}  {u['one_liner'].strip()}")


def show_chain(kb, uid):
    """展开一个卡点的完整解题链——这是产品给建议时走的路径。"""
    u = kb["units"].get(uid)
    if not u:
        sys.exit(f"找不到 {uid}")

    print(f"\n{C['h']}{u['name']}{C['0']}  {C['d']}{uid}{C['0']}\n")

    if u.get("user_language"):
        print(f"{C['c']}用户会怎么说{C['0']}")
        for p in u["user_language"]:
            print(f"  「{p}」")
        print()

    if u.get("observables"):
        print(f"{C['c']}视频里能看见什么{C['0']}  {C['d']}（这些是可确认事实）{C['0']}")
        for o in u["observables"]:
            print(f"  · {o}")
        print()

    cands = u.get("candidate_explanations") or []
    if cands:
        print(f"{C['c']}候选解释{C['0']}  {C['d']}（{len(cands)} 个，不强行给唯一原因）{C['0']}")
        for i, c in enumerate(cands, 1):
            print(f"  {i}. {c.get('explanation','')}")
            print(f"     {C['d']}需要的证据：{c.get('evidence_required','')}{C['0']}")
            if c.get("technique"):
                t = kb["units"].get(c["technique"], {})
                print(f"     {C['d']}对应技巧：{c['technique']} {t.get('name','')}{C['0']}")
        print()

    if u.get("hints"):
        print(f"{C['c']}局部提示{C['0']}  {C['d']}（最少剧透）{C['0']}")
        for h in u["hints"]:
            print(f"  → {h}")
        print()

    if u.get("tasks"):
        print(f"{C['c']}现实任务{C['0']}")
        for t in u["tasks"]:
            tu = kb["units"].get(t, {})
            print(f"  · {t}  {tu.get('name','')}")
            if tu.get("evidence"):
                print(f"    {C['d']}完成证据：{tu['evidence'].strip()}{C['0']}")
        print()

    if u.get("physics"):
        print(f"{C['c']}背后的物理{C['0']}")
        for p in u["physics"]:
            pu = kb["units"].get(p, {})
            print(f"  · {p}  {pu.get('name','')}")
            if pu.get("one_liner"):
                print(f"    {C['d']}{pu['one_liner'].strip()}{C['0']}")
        print()

    if u.get("safety"):
        print(f"{C['y']}安全边界{C['0']}  {C['d']}（产品输出建议时必须一并给出）{C['0']}")
        for s in u["safety"]:
            print(f"  ! {s}")
        print()

    rv = u.get("review") or {}
    if rv.get("status") != "approved":
        print(f"{C['y']}注意{C['0']}：该单元审核状态为 {rv.get('status')}，"
              f"尚未进入产品自动输出。\n")


def search(kb, term):
    hits = []
    # 精确匹配用户语言和别名
    for phrase, uids in kb["indexes"]["user_phrase_to_fault"].items():
        if term in phrase:
            hits += [(u, f"用户语言「{phrase}」") for u in uids]
    for alias, uids in kb["indexes"]["alias_to_unit"].items():
        if term in alias:
            hits += [(u, f"名称/别名「{alias}」") for u in uids]
    # 全文兜底
    if not hits:
        for uid, u in kb["units"].items():
            blob = json.dumps(u, ensure_ascii=False)
            if term in blob:
                hits.append((uid, "正文包含"))

    seen, uniq = set(), []
    for uid, why in hits:
        if uid not in seen:
            seen.add(uid)
            uniq.append((uid, why))
    return uniq


def main():
    kb = load()
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)

    if args[0] == "--list":
        want = args[1].rstrip("s") if len(args) > 1 else None
        for uid, u in sorted(kb["units"].items()):
            if want is None or u.get("type") == want:
                show_unit(kb, uid)
        return

    if args[0] == "--chain":
        show_chain(kb, args[1])
        return

    term = args[0]
    if term in kb["units"]:
        u = kb["units"][term]
        if u.get("type") == "fault":
            show_chain(kb, term)
        else:
            show_unit(kb, term)
            print()
            for field, label in [("physics", "物理原理"), ("principles", "动作原则"),
                                 ("techniques", "相关技巧"), ("tasks", "现实任务"),
                                 ("faults", "对应卡点")]:
                if u.get(field):
                    print(f"{C['c']}{label}{C['0']}")
                    for r in u[field]:
                        show_unit(kb, r, "  ")
                    print()
            if u.get("hints"):
                print(f"{C['c']}局部提示{C['0']}")
                for h in u["hints"]:
                    print(f"  → {h}")
                print()
            if u.get("_referenced_by"):
                print(f"{C['c']}被谁引用{C['0']}")
                for r in u["_referenced_by"]:
                    print(f"  {C['d']}{r['via']:14s}{C['0']} {r['id']}")
        return

    hits = search(kb, term)
    if not hits:
        print(f"没有找到与「{term}」相关的单元。")
        return
    print(f"\n「{term}」命中 {len(hits)} 个单元：\n")
    for uid, why in hits:
        show_unit(kb, uid)
        print(f"  {C['d']}匹配：{why}{C['0']}\n")
    faults = [u for u, _ in hits if kb["units"][u].get("type") == "fault"]
    if faults:
        print(f"{C['d']}展开解题链：python3 tools/query.py --chain {faults[0]}{C['0']}\n")


if __name__ == "__main__":
    main()
