#!/usr/bin/env python3
"""T09 · 评测集验收：在标注案例上跑，分类报通过率。

`.claude/agents/qa.md` 的要求：
「成功案例判对多少、失败案例判对多少、**易误判案例判对多少**。
第三类是重点，前两类容易刷分。」**易误判单独报，混在总通过率里等于没报。**

评测集是研究专家写的 `climbing-kb/kb/cases/*.md`：
`eval_class`（成功 / 失败 / 易误判）+ `eval_expect`（这一段系统该说什么、不该说什么）。
本用例把每条 `eval_expect` 翻译成可执行断言，跑在 `qa/fixtures/` 上。

**边界要说清楚**：`eval_expect` 是自然语言，这里的断言是它的**一种翻译**。
翻译对不对由研究专家复核——本文件把翻译逐条写在断言描述里，就是为了让人能核。
另外三条案例全部来自**同一个人、同一面墙**，通过率不能外推。

## 只跑得动不依赖视频的那部分

`detect_bent_adjust` / `stalls` / `rises` / 教练卡片 / 岩点关联，都能从
`keypoints.npz` + `evidence.jsonl` 复现（前三者的**图像坐标**版本，
带 `wall_H` 的管线口径见 D-006）。`stalls` / `rises` / 教练卡片
本轮取自 `summary.json`，即**管线当时的真实输出**，不是重算值。
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import numpy as np
import yaml

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import qalib as Q                                            # noqa: E402

CASE_DIR = Q.KB / "kb" / "cases"
SRC = {"CASE-2608-001": "out5", "CASE-2608-002": "out7",
       "CASE-2608-003": "out7"}
# 「腿力不够」这一类归因是 eval_expect 明确禁止的（右膝屈到 40°，蓄力是到位的）
FORCE_WORDS = ("力量", "力气", "太弱", "不够有力", "腿力")


def front(path):
    m = re.match(r"^---\n(.*?)\n---\n", pathlib.Path(path).read_text(encoding="utf-8"),
                 re.S)
    return yaml.safe_load(m.group(1)) if m else {}


def bent_adjust(outdir):
    """用**正常阈值**跑屈臂检测。CASE-2608-003 的 measured 是研究专家把
    RISING / HAND_HIGH 放开为「全部报告」跑的，那是取材，不是产品行为。
    验收要看的是产品行为。"""
    from climbanno import pose, posture
    fr, fps = Q.frames_from_npz(outdir)
    ct = Q.contacts_from_evidence(outdir)
    rel = pose.reliability(fr)
    eok = {s: pose.joint_reliability(fr, s + "_ELBOW") for s in ("L", "R")}
    com = np.load(pathlib.Path(outdir) / "keypoints.npz")["com"]
    return posture.detect_bent_adjust(fr, ct, fps, reliable=rel,
                                      elbow_ok=eok, com=com)


def hold_link(outdir, limb):
    ev = [json.loads(x) for x in
          (pathlib.Path(outdir) / "evidence.jsonl").open(encoding="utf-8")]
    tot = hit = 0
    for e in ev:
        for c in e["contacts"]:
            if c["limb"] == limb and c["state"] == "contact":
                tot += 1
                hit += c.get("hold") is not None
    return hit, tot


def run():
    r = Q.Runner("T09 评测集验收")
    result = {}          # eval_class -> [(case_id, 通过?)]

    def record(cid, klass, case):
        result.setdefault(klass, []).append((cid, not case.fails))

    # --- 失败类 · CASE-2608-001（out5）---------------------------------
    cid, fx = "CASE-2608-001", Q.FIXTURES / "out5"
    fm = front(CASE_DIR / f"{cid}.md")
    c = r.case(f"{cid}【{fm.get('eval_class')}】"
               f"应报「踩上去了但没站起来」并指向重心偏移，不指向腿力")
    r.eq(fm.get("eval_class"), "失败", f"{cid}: eval_class")
    s = json.loads((fx / "summary.json").read_text(encoding="utf-8"))
    cards = s.get("coach_cards") or []
    stall_cards = [x for x in cards if "没站起来" in (x.get("标题") or "")]
    r.check(len(stall_cards) >= 1,
            "报出了「踩上去了但没站起来」的卡片",
            [x.get("标题") for x in cards], "至少 1 张")
    for card in stall_cards:
        why = card.get("为什么") or []
        r.check(any("重心" in w and ("正上方" in w or "上方" in w) for w in why),
                f"{card['时间']}: 归因指向重心没送到脚的正上方", why, "含重心/正上方")
        bad = [w for w in why if any(k in w for k in FORCE_WORDS)]
        r.eq(bad, [], f"{card['时间']}: 不把原因归给腿部力量")
        r.check("FAULT-ROCKOVER-STALL-010" in (card.get("依据") or []),
                f"{card['时间']}: 依据含 FAULT-ROCKOVER-STALL-010",
                card.get("依据"), "含该单元")
    r.check(len(s.get("stalls") or []) >= 1, "管线确实检出了停滞段",
            len(s.get("stalls") or []), ">= 1")
    r.eq(len(bent_adjust(fx)), 0, "不在这一段附带报屈臂（正常阈值）")
    record(cid, "失败", c)

    # --- 成功类 · CASE-2608-002（out7）---------------------------------
    cid, fx = "CASE-2608-002", Q.FIXTURES / "out7"
    fm = front(CASE_DIR / f"{cid}.md")
    c = r.case(f"{cid}【{fm.get('eval_class')}】不该报任何停滞或屈臂，"
               f"可以报动作链完整")
    r.eq(fm.get("eval_class"), "成功", f"{cid}: eval_class")
    s = json.loads((fx / "summary.json").read_text(encoding="utf-8"))
    r.eq(s.get("stalls"), [], "不报停滞")
    r.eq(len(bent_adjust(fx)), 0, "不报屈臂（正常阈值）")
    cards = s.get("coach_cards") or []
    r.eq([x.get("标题") for x in cards if "没站起来" in (x.get("标题") or "")],
         [], "没有「没站起来」类卡片")
    r.check(any("做对了" in (x.get("标题") or "") for x in cards),
            "报出了「这次发力做对了」", [x.get("标题") for x in cards], "含做对了")
    rises = s.get("rises") or []
    r.check(len(rises) >= 1, "检出了重心上升段", len(rises), ">= 1")
    r.close(rises[0].get("lead_s"), 0.13, 0.005,
            "出手比重心起升晚 +0.13s（eval_expect 点名的量）")
    record(cid, "成功", c)

    # --- 易误判类 · CASE-2608-003（out7）-------------------------------
    # 这一类是重点。它记录的正是「管线曾把进展报成问题」的那两段。
    cid, fx = "CASE-2608-003", Q.FIXTURES / "out7"
    p3 = CASE_DIR / f"{cid}.md"
    c = r.case(f"{cid}【易误判】不该报屈臂、不该声称看见同点换脚")
    if not p3.exists():
        r.skip(f"{cid} 不存在")
    else:
        fm = front(p3)
        r.eq(fm.get("eval_class"), "易误判", f"{cid}: eval_class")
        m3 = fm.get("measured") or {}

        # ① 不应报「换脚时挂在手上／屈臂」——两段重心都在升
        ba = bent_adjust(fx)
        r.eq([(round(x.t0, 2), round(x.t1, 2), x.foot) for x in ba], [],
             "正常阈值下不报任何屈臂时段（这正是被推翻过的那条结论）")
        for seg in m3.get("脚离点段") or []:
            r.check(seg["重心上升"] > 0,
                    f"取材记录：{seg['起止']} 这一段重心在上升（+{seg['重心上升']}）",
                    seg["重心上升"], "> 0")

        # ② 不应声称看见同点换脚——脚与岩点关联率是 0，它分不出来
        s = json.loads((fx / "summary.json").read_text(encoding="utf-8"))
        spoken = json.dumps(s.get("coach_cards") or [], ensure_ascii=False)
        for kw in ("换脚", "同点", "同一个岩点"):
            r.eq(spoken.count(kw), 0, f"对用户说的话里没有「{kw}」")
        for cn, limb in (("左脚", "LF"), ("右脚", "RF")):
            hit, tot = hold_link(fx, limb)
            r.eq([hit, tot], (m3.get("岩点关联") or {}).get(cn),
                 f"{cn}与岩点的关联 [满足数, 总数]")
            r.eq(hit, 0, f"{cn}接触帧一次都没关联上岩点——它确实分不出是哪个点")

        # ③ 可以报的：某只脚离开 0.43 秒、期间另一只脚始终在点上
        ct = Q.contacts_from_evidence(fx)
        for seg in m3.get("脚离点段") or []:
            a, b = seg["帧区间"]
            other = "RF" if seg["脚"] == "左" else "LF"
            rate = float(np.mean([ct[other][i] == "contact" for i in range(a, b)]))
            r.close(rate, 1.0, 1e-9,
                    f"{seg['起止']}：另一只脚全程在点上（可以报的那一条）")
        record(cid, "易误判", c)

    n_f = r.report()

    # --- 分类通过率：易误判单独报 ---------------------------------------
    print("\n评测集分类通过率（易误判单独报，不并入总数）")
    print("─" * 62)
    for klass in ("成功", "失败", "易误判"):
        rows = result.get(klass, [])
        if not rows:
            print(f"  {klass:4s}  0/0   —— 评测集里还没有这一类")
            continue
        ok = sum(1 for _, v in rows if v)
        print(f"  {klass:4s}  {ok}/{len(rows)}   " +
              "  ".join(f"{cid}{'✓' if v else '✗'}" for cid, v in rows))
    print("─" * 62)
    print("  样本量说明：3 条案例全部来自同一个人、同一面墙、两段素材。")
    print("  通过率**不能外推**到别的攀岩者、机位或岩馆。")
    print("  需要研究专家补：不同人 / 不同机位 / 不同墙，三类各若干条。")
    return n_f


if __name__ == "__main__":
    Q.main_guard(run)
