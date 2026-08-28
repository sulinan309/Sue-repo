#!/usr/bin/env python3
"""取回「某只脚离开岩点」那些段的实测量，供换脚（A1）相关的案例单元使用。

    python3 climbing-kb/tools/swap_segments.py annotator/out7
    python3 climbing-kb/tools/swap_segments.py qa/fixtures/out7 qa/fixtures/out5

为什么需要这个脚本
------------------
管线里负责这件事的函数是 `climbanno.posture.detect_bent_adjust`，
但它的职责是**报警**：只有「手臂弯着 + 身体没在上升 + 手够高」三条同时成立
才会输出。案例单元需要的是**段本身的量**（多长、另一只脚在不在、重心升了多少），
不管它该不该报警。

所以这里只做一件事：把两个**报警阈值**放开为「全部报告」，
再调用管线原函数。段的划分、肘角、重心上升、手相对肩高度
**全部由管线自己计算，本文件没有任何替代实现**——
知识库里的数字必须和产物出自同一条代码路径，
否则同一个量会在 README、卡片和 KB 里慢慢变成三个数。

依赖 annotator/climbanno。管线改了这几个函数，这里算出来的数字就会变，
这是有意的：数字变了应当被看见，而不是被这份脚本掩盖。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "annotator"))

try:
    from climbanno import pose as P, posture as PT
except ImportError as e:      # pragma: no cover
    sys.exit(f"需要 annotator/climbanno（{e}）。先装 annotator/requirements.txt。")

L_SHO, R_SHO, L_HIP, R_HIP, L_ANK, R_ANK = 11, 12, 23, 24, 27, 28
LIMBS = ("LH", "RH", "LF", "RF")
CN = {"LH": "左手", "RH": "右手", "LF": "左脚", "RF": "右脚"}


def medf(a, w=7):
    """中位滤波，与 climbanno.anchor 同口径：去关键点抖动，保留慢变化。"""
    out = a.copy()
    for i in range(len(a)):
        s = a[max(0, i - w // 2):i + w // 2 + 1]
        s = s[np.isfinite(s)]
        if len(s):
            out[i] = np.median(s)
    return out


def load(outdir: pathlib.Path):
    d = np.load(outdir / "keypoints.npz")
    xy, vis, com = d["xy"], d["vis"], d["com"]
    fps = float(d["fps"]) if "fps" in d else 30.0
    ev = [json.loads(x) for x in (outdir / "evidence.jsonl").open(encoding="utf-8")]
    frames = [P.Frame(idx=i, t=i / fps, ok=bool(ev[i]["ok"]) if i < len(ev) else False,
                      xy=xy[i], vis=vis[i],
                      com=(tuple(com[i]) if np.isfinite(com[i]).all() else None))
              for i in range(len(xy))]
    ct = {L: [next((c["state"] for c in e["contacts"] if c["limb"] == L), "uncertain")
              for e in ev] for L in LIMBS}
    hold = {L: [next((c["hold"] for c in e["contacts"] if c["limb"] == L), None)
                for e in ev] for L in LIMBS}
    return frames, ct, hold, fps, xy


def report(outdir: str, windows=None):
    p = pathlib.Path(outdir)
    frames, ct, hold, fps, xy = load(p)
    rel = P.reliability(frames)
    eok = {s: P.joint_reliability(frames, f"{s}_ELBOW") for s in ("L", "R")}

    # 只放开报警阈值，段划分与各量的算法一律不动
    keep = (PT.RISING, PT.HAND_HIGH)
    PT.RISING, PT.HAND_HIGH = float("inf"), float("-inf")
    segs = PT.detect_bent_adjust(frames, ct, fps, reliable=rel, elbow_ok=eok)
    PT.RISING, PT.HAND_HIGH = keep
    alarms = PT.detect_bent_adjust(frames, ct, fps, reliable=rel, elbow_ok=eok)

    torso = medf(np.linalg.norm((xy[:, L_SHO] + xy[:, R_SHO]) / 2 -
                                (xy[:, L_HIP] + xy[:, R_HIP]) / 2, axis=1))
    ank = {"LF": (medf(xy[:, L_ANK, 0]), medf(xy[:, L_ANK, 1])),
           "RF": (medf(xy[:, R_ANK, 0]), medf(xy[:, R_ANK, 1]))}

    print(f"=== {outdir}   帧数 {len(frames)}   fps {fps:g}")
    print(f"    姿态可信率 {rel.mean():.3f}    "
          f"肘角可信率 左 {eok['L'].mean():.2f} / 右 {eok['R'].mean():.2f}")
    print(f"    当前阈值下会报警的段：{len(alarms)}    全部脚离点段：{len(segs)}")

    for b in segs:
        i, j = int(round(b.t0 * fps)), int(round(b.t1 * fps))
        other = "RF" if b.foot == "LF" else "LF"
        rate = sum(1 for k in range(i, j) if ct[other][k] == "contact") / max(j - i, 1)

        def rel_pos(k):
            k = min(max(k, 0), len(xy) - 1)
            (mx, my), (ox, oy) = ank[b.foot], ank[other]
            return np.array([mx[k] - ox[k], my[k] - oy[k]]) / torso[k]

        a0, a1 = rel_pos(i - 1), rel_pos(j)
        print(f"  {CN[b.foot]}离点 {b.t0:.2f}–{b.t1:.2f}s（{(j-i)/fps:.2f}s，帧 [{i},{j})）")
        print(f"      肘角中位 左={_r(b.elbow_med['L'])} 右={_r(b.elbow_med['R'])}"
              f"  可测手臂 {b.measurable}  有接近伸直的 {b.any_straight}")
        print(f"      重心上升 {b.com_rise:+.3f}   最高手相对肩 {b.hand_above:+.3f}"
              f"   {CN[other]}接触率 {rate:.2f}")
        print(f"      移动脚相对另一踝：段前 [{a0[0]:+.2f}, {a0[1]:+.2f}]"
              f"  段后 [{a1[0]:+.2f}, {a1[1]:+.2f}]"
              f"  净位移 {np.linalg.norm(a1 - a0):.2f}")

    print("    岩点关联（接触帧中关联到岩点的比例）：", end="")
    for L in LIMBS:
        c = sum(1 for s in ct[L] if s == "contact")
        ch = sum(1 for s, h in zip(ct[L], hold[L]) if s == "contact" and h)
        print(f" {CN[L]} {ch}/{c}", end="")
    print()

    if windows:
        idx = [i for i, f in enumerate(frames)
               if any(a <= f.t <= b for a, b in windows)]
        nf = sum(1 for i in idx
                 if ct["LF"][i] != "contact" and ct["RF"][i] != "contact")
        print(f"    指定区间内双脚同时非接触 {nf}/{len(idx)} 帧")
    print("    单位：长度为倍躯干长；图像坐标 x 向右为正、y 向下为正；角度为度。")


def _r(v):
    return "不可测" if v is None else f"{v:.1f}"


def main():
    ap = argparse.ArgumentParser(description="打印脚离点段的管线实测量")
    ap.add_argument("outdirs", nargs="+", help="annotator 输出目录，如 annotator/out7")
    ap.add_argument("--window", action="append", default=None,
                    metavar="起:止", help="额外统计的时间区间，可给多次")
    a = ap.parse_args()
    wins = [tuple(float(x) for x in w.split(":")) for w in (a.window or [])] or None
    for d in a.outdirs:
        report(d, wins)


if __name__ == "__main__":
    main()
