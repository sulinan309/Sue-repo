#!/usr/bin/env python3
"""T02 · 锚点口径的黄金快照（最高优先级）。

这是整套测试的地基：**同样的输入必须产出同样的数字**。
测的是 `climbanno/anchor.py` 的算法本体（medf / t0 定位 / dx / dy / rise），
输入只有 `qa/fixtures/`，**不读任何视频**——原始视频是容器级的，会消失。

快照分两层：

1. **逐帧序列的 SHA-256**。dx / dy / torso / ax / ay 四条序列四舍五入到
   小数点后 6 位再取哈希。「重构不改行为」这句话必须由这个哈希来说，
   不能由人来说。采样点对得上而中间某几帧变了，抽样是抓不到的。
2. **上屏数字**。compare.py 和 card.py 会把这些数印在成品上：
   T0、踩实时横向偏、+0.4/0.5/0.8/1.0/1.5/2.0s 的高度变化、两条轨迹最小间距。

已知正确值（工程师报告 + 本轮用真视频复跑核对过，见测试报告）：

    compare  站起来了 T0=0.97s 横向偏 0.25  +2.0s +0.99
             没站起来 T0=2.10s 横向偏 0.40  +2.0s -0.50   最小间距 0.37
    card     +0.8s  +0.36 / -0.53

这些值直接写进本文件的 EXPECT，与自动生成的基线互为独立来源：
基线文件被误 --bless 覆盖时，EXPECT 仍然会响。
"""
from __future__ import annotations

import hashlib
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import qalib as Q                                            # noqa: E402

BLESS = "--bless" in sys.argv
TIMES = (0.0, 0.4, 0.5, 0.8, 1.0, 1.5, 2.0)
PLAY_S = 2.0

# out7 = 站起来了（成功），out5 = 没站起来（失败）。
ROLE = {"out7": "站起来了", "out5": "没站起来"}

# 独立于基线文件的第二来源。容差 0.005 = 上屏保留两位小数时的半个最小刻度。
EXPECT = {
    "out7": {"t0_s": 0.97, "横向偏": 0.25,
             "rise": {0.4: 0.24, 0.8: 0.36, 2.0: 0.99}},
    "out5": {"t0_s": 2.10, "横向偏": 0.40,
             "rise": {0.4: -0.50, 0.8: -0.53, 2.0: -0.50}},
}
EXPECT_MIN_GAP = 0.37
TOL = 0.005


def seq_sha(a):
    return hashlib.sha256(np.round(np.asarray(a, float), 6).tobytes()).hexdigest()


def run():
    from climbanno import anchor

    r = Q.Runner("T02 锚点数值基线（黄金快照）")
    snap = {}

    S = {}
    c = r.case("无视频加载器可用，且 n 口径成立")
    for d in ("out7", "out5"):
        S[d] = Q.load_nv(Q.FIXTURES / d)
        r.check(S[d]["frames"] is None, f"{d}: 没有读入任何视频帧",
                S[d]["frames"], None)
        r.eq(S[d]["n"], len(S[d]["xy"]), f"{d}: n == keypoints 行数")

    c = r.case("逐帧序列哈希")
    for d in ("out7", "out5"):
        s = S[d]
        snap[d] = {
            "fps": float(s["fps"]), "n": int(s["n"]),
            "t0": int(s["t0"]), "t_end": int(s["t_end"]),
            "t0_s": Q.r2(s["t0"] / s["fps"]),
            "持续接触秒": Q.r2((s["t_end"] - s["t0"]) / s["fps"]),
            "踩实时横向偏": Q.r2(abs(s["dx"][s["t0"]])),
            "sha": {k: seq_sha(s[k]) for k in ("dx", "dy", "torso", "ax", "ay")},
            "rise": {f"+{t:.1f}s": Q.r2(anchor.rise(s, anchor.idx(s, t)))
                     for t in TIMES},
        }

    npl = int(PLAY_S * S["out7"]["fps"])
    series = {d: [anchor.rise(S[d], S[d]["t0"] + k) for k in range(npl)]
              for d in ("out7", "out5")}
    cross = [k for k in range(npl)
             if series["out7"][k] <= series["out5"][k] and k > 2]
    gap = min(series["out7"][k] - series["out5"][k] for k in range(3, npl))
    snap["pair"] = {"npl": npl, "交叉帧": cross,
                    "最小间距": Q.r2(gap),
                    "成功侧全正帧数": int(sum(1 for v in series["out7"][3:] if v > 0)),
                    "失败侧全负帧数": int(sum(1 for v in series["out5"][3:] if v < 0)),
                    "窗口帧数": npl - 3}

    base = Q.read_baseline("anchor_golden.json")
    if base is None or BLESS:
        Q.write_baseline("anchor_golden.json", snap)
        r.skip("基线首次生成（或 --bless 重建），本轮不比对哈希")
    else:
        for d in ("out7", "out5"):
            for k in ("dx", "dy", "torso", "ax", "ay"):
                r.eq(snap[d]["sha"][k], base[d]["sha"][k],
                     f"{d}.{k} 逐帧序列 SHA-256")

    c = r.case("上屏数字与基线一致")
    if base is not None and not BLESS:
        for d in ("out7", "out5"):
            for k in ("fps", "n", "t0", "t_end", "t0_s", "持续接触秒",
                      "踩实时横向偏"):
                r.eq(snap[d][k], base[d][k], f"{d}.{k}")
            for k in snap[d]["rise"]:
                r.eq(snap[d]["rise"][k], base[d]["rise"][k], f"{d}.rise{k}")
        for k in snap["pair"]:
            r.eq(snap["pair"][k], base["pair"][k], f"pair.{k}")
    else:
        r.skip("基线首次生成，本轮不比对")

    c = r.case("与工程师报告的已知正确值对照（独立于基线文件）")
    for d, exp in EXPECT.items():
        r.close(snap[d]["t0_s"], exp["t0_s"], TOL, f"{ROLE[d]} T0（秒）")
        r.close(snap[d]["踩实时横向偏"], exp["横向偏"], TOL,
                f"{ROLE[d]} 踩实时横向偏")
        for t, v in exp["rise"].items():
            r.close(snap[d]["rise"][f"+{t:.1f}s"], v, TOL,
                    f"{ROLE[d]} +{t:.1f}s 高度变化")
    r.close(snap["pair"]["最小间距"], EXPECT_MIN_GAP, TOL, "两条轨迹最小间距")

    c = r.case("compare.py 上屏前提：0–2.0s 内两条轨迹不交叉")
    # compare.py main() 里有同样的断言，交叉就报错退出。这里在没有视频的
    # 情况下把那条断言单独测掉——它是「实时数字敢不敢上屏」的唯一依据。
    r.eq(snap["pair"]["交叉帧"], [], "去掉前 3 帧后无交叉帧")
    r.check(snap["pair"]["最小间距"] > 0, "最小间距为正",
            snap["pair"]["最小间距"], "> 0")
    r.eq(snap["pair"]["成功侧全正帧数"], snap["pair"]["窗口帧数"],
         "成功侧该窗口全部为正")
    r.eq(snap["pair"]["失败侧全负帧数"], snap["pair"]["窗口帧数"],
         "失败侧该窗口全部为负")

    c = r.case("符号相反，不是程度差别（案例单元的核心论断）")
    r.check(snap["out7"]["rise"]["+2.0s"] > 0 > snap["out5"]["rise"]["+2.0s"],
            "+2.0s 高度变化符号相反",
            (snap["out7"]["rise"]["+2.0s"], snap["out5"]["rise"]["+2.0s"]),
            "一正一负")

    # --- 基线自身的灵敏度 -------------------------------------------------
    # 一条永远通过的基线和没有基线是一回事。这里主动把输入改坏，
    # 确认哈希和上屏数字都会跟着变——否则上面那些 OK 不能说明任何事。
    #
    # 扰动量选 3 像素（躯干长 186px 的 1.6%）：out5 与 out6（旧版管线）的
    # 关键点最大差 98px、COM 最大差 15px，落到结论上是 -0.50 → -0.38。
    # 3px 远小于那次事故，基线连它都抓得住，才谈得上抓得住真正的静默变化。
    #
    # 注意扰动必须加在 T0 之后：rise() 是相对 T0 的差值，整段平移会被差值
    # 抵消掉——这本身是个正确的性质（镜头整体平移不该改变结论），
    # 顺手在下面断言掉，免得哪天有人把它改成绝对量。
    c = r.case("基线灵敏度自检：输入改坏时基线必须变")
    import pathlib
    import shutil
    import tempfile
    t0 = snap["out5"]["t0"]
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td) / "out5_mut"
        shutil.copytree(Q.FIXTURES / "out5", tmp)
        z = dict(np.load(tmp / "keypoints.npz"))
        z["com"] = z["com"].copy()
        z["com"][t0 + 1:, 1] -= 3.0               # T0 之后重心上移 3 像素
        np.savez(tmp / "keypoints.npz", **z)
        m = Q.load_nv(tmp)
        r.check(seq_sha(m["dy"]) != snap["out5"]["sha"]["dy"],
                "T0 后上移 3px：dy 哈希发生变化",
                seq_sha(m["dy"])[:16], "≠ " + snap["out5"]["sha"]["dy"][:16])
        got = Q.r2(anchor.rise(m, anchor.idx(m, 2.0)))
        r.check(got != snap["out5"]["rise"]["+2.0s"],
                "T0 后上移 3px：+2.0s 上屏数字发生变化",
                got, "≠ " + str(snap["out5"]["rise"]["+2.0s"]))

    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td) / "out5_shift"
        shutil.copytree(Q.FIXTURES / "out5", tmp)
        z = dict(np.load(tmp / "keypoints.npz"))
        z["com"] = z["com"].copy() - 7.0
        z["xy"] = z["xy"].copy() - 7.0            # 整幅画面平移，模拟镜头位移
        np.savez(tmp / "keypoints.npz", **z)
        m = Q.load_nv(tmp)
        got = Q.r2(anchor.rise(m, anchor.idx(m, 2.0)))
        r.eq(got, snap["out5"]["rise"]["+2.0s"],
             "整幅平移 7px：+2.0s 数字不变（承重踝参考点该抵消镜头平移）")
    return r.report()


if __name__ == "__main__":
    Q.main_guard(run)
