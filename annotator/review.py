#!/usr/bin/env python3
"""从证据记录里找候选发现。

    python3 review.py out2/evidence.jsonl

这是「证据 → 候选发现」的接缝，不是「候选发现 → 教学建议」。
后者归知识库和攀岩专家模型——本文件不产出任何建议。

**每条候选发现都必须过基线对比。**
这是本文件存在的主要理由：攀岩视频里很多量天然高频
（髋部 30% 的帧在动、手部 78% 的帧附近有移动），
不跟随机基线比，很容易把「本来就常见」当成「这个人的问题」。
一条没过基线的观察，不是弱发现，是**不是发现**。
"""
from __future__ import annotations

import json
import sys
from math import erf, sqrt

import numpy as np

HIP_MOVE = 0.35          # 髋部移动阈值，与 contact.py 的 STILL_HIP 对齐
FPS = 30.0
LIMBS = ["LH", "RH", "LF", "RF"]
CN = {"LH": "左手", "RH": "右手", "LF": "左脚", "RF": "右脚"}


def z_test(k: int, n: int, p0: float) -> tuple[float, float]:
    """单尾二项检验的正态近似。"""
    if n == 0:
        return 0.0, 1.0
    sd = sqrt(n * p0 * (1 - p0))
    if sd == 0:
        return 0.0, 1.0
    z = (k - n * p0) / sd
    return z, 1 - 0.5 * (1 + erf(z / sqrt(2)))


def load(path):
    ev = [json.loads(l) for l in open(path, encoding="utf-8")]
    n = len(ev)
    hip = np.array([e["hip_speed"] for e in ev])
    st = {L: [] for L in LIMBS}
    for e in ev:
        m = {c["limb"]: c["state"] for c in e["contacts"]}
        for L in LIMBS:
            st[L].append(m.get(L, "uncertain"))
    return ev, n, hip, st


def move_events(seq, n, minlen=3):
    """contact → 非 contact → contact 的移动事件，返回起始帧。"""
    out, i = [], 0
    while i < n:
        if seq[i] == "contact":
            j = i
            while j < n and seq[j] == "contact":
                j += 1
            k = j
            while k < n and seq[k] != "contact":
                k += 1
            if j < n and k < n and (k - j) >= minlen:
                out.append((j, k))
            i = k if k > i else i + 1
        else:
            i += 1
    return out


def finding(name, unit, k, n_, base, note=""):
    z, p = z_test(k, n_, base)
    sig = p < 0.05
    return {
        "name": name, "kb_unit": unit,
        "observed": f"{k}/{n_} ({k/n_*100:.0f}%)" if n_ else "n/a",
        "baseline": f"{base*100:.0f}%",
        "z": round(z, 2), "p": round(p, 3),
        "verdict": "高于基线" if sig else ("样本不足，仅为倾向" if p < 0.2 else "与基线无实质差异，不构成发现"),
        "evidence_level": "可确认事实" if sig else "证据不足",
        "note": note,
    }


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "out/evidence.jsonl"
    ev, n, hip, st = load(path)
    ok = sum(e["ok"] for e in ev)
    print(f"\n素材：{n} 帧 / {n/FPS:.1f}s    姿态检出 {ok}/{n} ({ok/n*100:.0f}%)\n")

    out = []

    # --- 伸手前髋是否先动（FAULT-REACH-FIRST-005 / TEC-POS-COM-001）---
    W = 9                                   # 0.3s
    base = float(np.mean([np.any(hip[max(0, i - W):i] > HIP_MOVE) for i in range(W, n)]))
    hits = tot = 0
    for L in ("LH", "RH"):
        for s, _ in move_events(st[L], n):
            tot += 1
            if np.any(hip[max(0, s - W):s] > HIP_MOVE):
                hits += 1
    out.append(finding("伸手前髋部已先移动", "FAULT-REACH-FIRST-005", hits, tot, base,
                       "知识库里教学杠杆最高的一条：先移重心再伸手"))

    # --- 脚脱落与伸手是否同步（FAULT-FOOT-CUT-003）---
    W2 = 15                                 # 0.5s
    hand_near = float(np.mean([
        any(st[H][k] != "contact" for H in ("LH", "RH")
            for k in range(max(0, i - W2), min(n, i + W2))) for i in range(n)]))
    hits = tot = 0
    for L in ("LF", "RF"):
        for s, _ in move_events(st[L], n, minlen=2):
            tot += 1
            if any(st[H][k] != "contact" for H in ("LH", "RH")
                   for k in range(max(0, s - W2), min(n, s + W2))):
                hits += 1
    out.append(finding("脚脱落与伸手同步发生", "FAULT-FOOT-CUT-003", hits, tot, hand_near,
                       "同步发生指向张力传递断裂；但手部移动本身高频，基线很高"))

    # --- 犹豫（FAULT-HESITATE-013）---
    stall = np.array([e["n_contact"] >= 3 and e["hip_stable"] for e in ev])
    runs, cur = [], 0
    for v in stall:
        if v:
            cur += 1
        elif cur:
            runs.append(cur); cur = 0
    if cur:
        runs.append(cur)
    runs = np.array(runs) / FPS if runs else np.array([0.0])
    long_ = int(np.sum(runs > 2.0))
    print("候选发现（每条都过基线对比）\n" + "─" * 66)
    for f in out:
        print(f"  {f['name']}")
        print(f"    知识单元 {f['kb_unit']}")
        print(f"    观察 {f['observed']}   基线 {f['baseline']}   z={f['z']}  p={f['p']}")
        print(f"    判定：{f['verdict']}    证据等级：{f['evidence_level']}")
        if f["note"]:
            print(f"    {f['note']}")
        print()

    print(f"  停顿（FAULT-HESITATE-013）")
    print(f"    总停顿 {runs.sum():.1f}s / {n/FPS:.1f}s ({runs.sum()/(n/FPS)*100:.0f}%)"
          f"   中位 {np.median(runs):.1f}s   超过 2s 的 {long_} 次")
    print(f"    判定：{'存在长停顿，值得看' if long_ >= 3 else '多为动作间短暂稳定，不构成犹豫'}\n")

    print("各肢体移动次数")
    for L in LIMBS:
        print(f"    {CN[L]} {len(move_events(st[L], n))} 次")

    print("\n本层无法回答的问题（需要更高能力档位）")
    for q, tier in [
        ("髋部离墙多远、有没有贴墙", "P4 墙体坐标系"),
        ("重心有没有移到承重脚的正上方", "P4 墙体坐标系"),
        ("脚踩在岩点有效受力面还是边缘", "P3 接触区精细视觉"),
        ("爬的是哪条线、有没有抓线外的点", "线路底库，视频给不出"),
    ]:
        print(f"    {q:28s} ← {tier}")
    print()


if __name__ == "__main__":
    main()
