#!/usr/bin/env python3
"""T08 · 知识库口径：同一句话、同一条 observable，在几个地方必须是同一份。

annotator/README 的分工声明：

    「下次这样试」的每一句都从知识库的 `hints` 字段取，不在代码里写。

这句话只有被机器核过才算数。管线的教练卡片、案例单元的 `hints_given`、
知识单元的 `hints`——三处任何一处被人手改一句，产品说的话就和知识库脱钩了，
而且不会有任何报错。

同理 `kb_link.EMITTED` 里那 8 条 observable 声称「经过校验确认在知识库中逐字存在」，
以及编译产物 `dist/kb.json`（管线真正读的是它，不是 kb/*.md）会不会过期。
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

import yaml

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import qalib as Q                                            # noqa: E402

KB_DIR = Q.KB / "kb"

# 单元总数**不设固定值**。知识库归研究专家写，单元数会合法地增长——
# 2026-08-28 本轮工作期间就从 66 涨到了 70。把它钉成常数只会制造假警报。
# 真正的门禁是：validate 退出码为 0（没有错误），警告只有已知那一条，
# 以及本用例独立数出的单元数与 validate 报的一致。
EXPECT_WARN = 1
KNOWN_WARN = "[警告] 首期状态:"        # 等待岩馆视频接入，预期长期存在


def units():
    out = {}
    for p in sorted(KB_DIR.rglob("*.md")):
        m = re.match(r"^---\n(.*?)\n---\n", p.read_text(encoding="utf-8"), re.S)
        if not m:
            continue
        fm = yaml.safe_load(m.group(1))
        if isinstance(fm, dict) and fm.get("id"):
            out[fm["id"]] = fm
    return out


def run():
    sys.path.insert(0, str(Q.ANNOTATOR))
    from climbanno import kb_link

    r = Q.Runner("T08 知识库口径")
    U = units()

    c = r.case("validate.py 的已知良好状态")
    cp = subprocess.run([sys.executable, "tools/validate.py"],
                        cwd=str(Q.KB), capture_output=True, text=True)
    r.eq(cp.returncode, 0, "validate.py 退出码为 0（没有错误）")
    r.eq([ln for ln in cp.stdout.splitlines() if ln.startswith("[错误]")], [],
         "输出里没有任何 [错误] 行")
    m = re.search(r"校验通过：(\d+) 个单元，(\d+) 个警告", cp.stdout)
    r.check(m is not None, "输出里有「校验通过」那一行",
            cp.stdout.strip().splitlines()[-1:], "含校验通过")
    warns = [ln for ln in cp.stdout.splitlines() if ln.startswith("[警告]")]
    r.eq(len(warns), EXPECT_WARN, f"警告数（已知只有「首期状态」一条）")
    for w in warns:
        r.check(w.startswith(KNOWN_WARN), f"警告是已知那一条：{w}", w,
                f"以 {KNOWN_WARN} 开头")
    if m:
        r.eq(len(U), int(m.group(1)),
             f"本用例独立数出的单元数与 validate 报的一致"
             f"（当前 {len(U)} 个，不设固定值）")

    c = r.case("产品说的每一句话都能在知识库里找到出处")
    kb_hints = set()
    for uid, fm in U.items():
        for h in fm.get("hints") or []:
            kb_hints.add(str(h).strip())
    r.check(len(kb_hints) > 0, f"知识库共 {len(kb_hints)} 条 hints",
            len(kb_hints), "> 0")

    said = []          # (来源, 句子)
    for d in ("out5", "out7"):
        s = json.loads((Q.FIXTURES / d / "summary.json").read_text(encoding="utf-8"))
        for card in s.get("coach_cards") or []:
            for h in card.get("下次这样试") or []:
                said.append((f"{d}/summary.json 教练卡片", str(h).strip()))
    for cid, fm in U.items():
        if fm.get("type") != "case":
            continue
        for h in fm.get("hints_given") or []:
            said.append((f"{cid}.hints_given", str(h).strip()))
    r.check(len(said) > 0, f"共收集到 {len(said)} 条对用户说的话",
            len(said), "> 0")
    for src, h in said:
        r.check(h in kb_hints, f"{src}：「{h}」在知识库 hints 里逐字存在",
                h, "知识库某单元的 hints 之一")

    c = r.case("卡片引用的知识单元 ID 都存在")
    for d in ("out5", "out7"):
        s = json.loads((Q.FIXTURES / d / "summary.json").read_text(encoding="utf-8"))
        for card in s.get("coach_cards") or []:
            for uid in card.get("依据") or []:
                r.check(uid in U, f"{d}: 教练卡片依据 {uid} 存在", uid, "存在于 kb/")
    for cid, fm in U.items():
        if fm.get("type") != "case":
            continue
        for uid in fm.get("knowledge") or []:
            r.check(uid in U, f"{cid}: knowledge 引用 {uid} 存在", uid, "存在于 kb/")

    c = r.case("kb_link.EMITTED 的 8 条 observable 逐字存在")
    r.eq(len(kb_link.EMITTED), 8, "EMITTED 条数")
    for uid, obs in kb_link.EMITTED:
        ok = uid in U and obs in (U[uid].get("observables") or [])
        r.check(ok, f"{uid} 的 observables 里逐字含「{obs}」", ok, True)

    c = r.case("summary.json 里的能力对照与当前 kb_link 一致")
    for d in ("out5", "out7"):
        s = json.loads((Q.FIXTURES / d / "summary.json").read_text(encoding="utf-8"))
        rep = s.get("knowledge_base") or {}
        got = [(x["unit"], x["observable"])
               for x in rep.get("emitted_observables") or []]
        r.eq(got, [list(x) and tuple(x) for x in kb_link.EMITTED],
             f"{d}: emitted_observables 与 kb_link.EMITTED 相同")
        r.eq((rep.get("kb") or {}).get("broken_references"), "无",
             f"{d}: 无断裂引用")
        r.eq(rep.get("not_measured"), kb_link.NOT_MEASURED,
             f"{d}: 未测量清单与 kb_link 一致")

    c = r.case("「知识库有多少条 observables」这个数有几个版本（缺陷 D-008）")
    dist_now = json.loads((Q.KB / "dist" / "kb.json").read_text(encoding="utf-8"))
    now_units = len(dist_now["units"])
    now_obs = sum(len(u.get("observables") or []) for u in dist_now["units"].values())
    readme = (Q.ANNOTATOR / "README.md").read_text(encoding="utf-8")
    m2 = re.search(r"对照 `climbing-kb` 的 (\d+) 条 observables", readme)
    r.check(m2 is not None, "annotator/README 里写了 observables 总数",
            m2.group(0) if m2 else None, "找得到那句话")
    snap_obs = {d: (json.loads((Q.FIXTURES / d / "summary.json")
                               .read_text(encoding="utf-8"))
                    ["knowledge_base"]["kb"]) for d in ("out5", "out7")}
    r.eq(snap_obs["out5"]["observables_total"],
         snap_obs["out7"]["observables_total"],
         "两份产物记录的 observables 总数彼此一致")
    if m2:
        r.known_defect(
            int(m2.group(1)) == now_obs, "D-008",
            f"同一个量三个数：annotator/README {m2.group(1)} 条 / "
            f"产物 summary.json {snap_obs['out5']['observables_total']} 条 / "
            f"当前 dist/kb.json {now_obs} 条"
            f"（单元数同理：产物 {snap_obs['out5']['units']} vs 当前 {now_units}）")
        r.known_defect(
            snap_obs["out5"]["units"] == now_units, "D-008",
            "产物没有记录知识库版本号，只记了当时的计数，"
            "事后无法判断这份产物是对着哪一版知识库跑的")

    c = r.case("dist/kb.json 是管线真正读的那份，不能过期")
    dist = Q.KB / "dist" / "kb.json"
    r.check(dist.exists(), "dist/kb.json 存在", dist.exists(), True)
    if dist.exists():
        kb = json.loads(dist.read_text(encoding="utf-8"))
        r.eq(sorted(kb["units"]), sorted(U), "dist 与 kb/ 的单元集合相同")
        drift = []
        for uid in sorted(set(kb["units"]) & set(U)):
            for field in ("hints", "observables"):
                a = kb["units"][uid].get(field) or []
                b = U[uid].get(field) or []
                if a != b:
                    drift.append(f"{uid}.{field}")
        r.eq(drift, [], "dist 与 kb/ 的 hints / observables 逐字相同")
    return r.report()


if __name__ == "__main__":
    Q.main_guard(run)
