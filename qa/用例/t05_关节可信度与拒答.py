#!/usr/bin/env python3
"""T05 · 关节可信度，以及「看不准就不给结论」。

annotator/README 的两条教训：

  「姿态检出率 100%，可信率 85%」——噪声上算的结论和信号上算的长得一模一样。
  「拿伪影下结论，比不下结论更糟。」

所以这里测三件事：

  1. **可信率本身能复现**。`pose.reliability()` / `reliable_windows()` 从
     fixtures 重算，必须与 summary.json 里的 `pose_reliable_rate` /
     `analyzable_windows` 逐位相同——同一个量不能有两个来源。
  2. **可信度判据真的会判不可信**。合成一段肢体朝向镜头的姿态，
     `joint_reliability()` 和 `drive._unreliable()` 必须标出来。
     全 True 的可信度函数和没有可信度函数是一回事。
  3. **不可信时下游确实闭嘴**。`detect_stalls` / `detect_rises` / `detect`
     在可信帧不足时不能给结论。**能正确拒答和能正确回答同样重要。**

口径提醒：管线跑这三个检测器时传了逐帧单应 `wall_H`（墙面坐标），
而 `wall_H` 没有被写进任何产物文件，只存在于内存。所以本用例只能在
**图像坐标**下跑它们，数值与 summary.json 不同——差多少见用例「墙面坐标是承重的」。
这条缺口记在 D-006。
"""
from __future__ import annotations

import json
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import qalib as Q                                            # noqa: E402

BLESS = "--bless" in sys.argv
JOINTS = ("L_ELBOW", "R_ELBOW", "L_KNEE", "R_KNEE")


def synth(n=40, over=None):
    """造一具正面站立的合成骨架：左右对称、四肢长度正常。

    坐标随手编，只要满足 joint_reliability 的两条约束即可：
    同名肢段左右投影等长；远端段/近端段比例接近 1。
    """
    xy = np.zeros((n, 33, 2))
    base = {
        11: (-40, 0), 12: (40, 0),          # 肩
        13: (-60, 60), 14: (60, 60),        # 肘
        15: (-70, 120), 16: (70, 120),      # 腕
        23: (-30, 140), 24: (30, 140),      # 髋
        25: (-32, 220), 26: (32, 220),      # 膝
        27: (-34, 300), 28: (34, 300),      # 踝
        0: (0, -40), 31: (-36, 320), 32: (36, 320),
    }
    base.update(over or {})
    for k, (x, y) in base.items():
        xy[:, k] = (x + 360, y + 300)
    return xy


def frames_of(xy, vis_val=0.9, fps=30.0):
    from climbanno import pose
    return [pose.Frame(i, i / fps, True, xy[i], np.full(33, vis_val))
            for i in range(len(xy))]


def run():
    from climbanno import drive, pose

    r = Q.Runner("T05 关节可信度与拒答")
    snap = {}

    # --- 1. 可信率与可分析区间必须与 summary 同源 --------------------------
    c = r.case("pose.reliability / reliable_windows 从 fixtures 重算 == summary")
    for d in ("out5", "out7"):
        fr, fps = Q.frames_from_npz(Q.FIXTURES / d)
        s = json.loads((Q.FIXTURES / d / "summary.json").read_text(encoding="utf-8"))
        rel = pose.reliability(fr)
        wins = [[round(a, 2), round(b, 2)]
                for a, b in pose.reliable_windows(rel, fps)]
        r.eq(round(float(np.mean([f.ok for f in fr])), 3), s["pose_rate"],
             f"{d}: 姿态检出率")
        r.eq(round(float(rel.mean()), 3), s["pose_reliable_rate"],
             f"{d}: 姿态可信率")
        r.eq(wins, s["analyzable_windows"], f"{d}: 可分析区间")
        r.check(s["pose_rate"] > s["pose_reliable_rate"],
                f"{d}: 检出率严格高于可信率——两者不是一回事",
                (s["pose_rate"], s["pose_reliable_rate"]), "检出率更高")

    # --- 2. 关节级可信度：fixtures 快照 ------------------------------------
    c = r.case("joint_reliability 逐关节可信率快照")
    for d in ("out5", "out7"):
        fr, _ = Q.frames_from_npz(Q.FIXTURES / d)
        snap[d] = {j: Q.r2(float(pose.joint_reliability(fr, j).mean()), 3)
                   for j in JOINTS}
        xy = np.load(Q.FIXTURES / d / "keypoints.npz")["xy"]
        snap[d].update({f"_unreliable_{s}": Q.r2(
            float(drive._unreliable(xy, s).mean()), 3) for s in ("L", "R")})
    base = Q.read_baseline("reliability_golden.json")
    if base is None or BLESS:
        Q.write_baseline("reliability_golden.json", snap)
        r.skip("基线首次生成（或 --bless 重建），本轮不比对")
    else:
        for d in snap:
            for k in snap[d]:
                r.eq(snap[d][k], base.get(d, {}).get(k), f"{d}.{k}")

    c = r.case("关节可信度确实有区分度（不是常量 1）")
    for d in ("out5", "out7"):
        vals = [snap[d][j] for j in JOINTS]
        r.check(min(vals) < 0.9, f"{d}: 至少一个关节可信率 < 0.9", vals, "有低值")
        r.check(max(vals) > min(vals) + 0.2,
                f"{d}: 关节之间的可信率差 > 0.2", vals, "存在分化")

    # --- 3. 合成用例：会不会判不可信 ---------------------------------------
    c = r.case("合成 · 正常对称姿态：四个关节都可信")
    fr = frames_of(synth())
    for j in JOINTS:
        r.eq(float(pose.joint_reliability(fr, j).mean()), 1.0,
             f"正常姿态 {j} 全帧可信")

    c = r.case("合成 · 左前臂朝向镜头（投影压缩）：只该左肘不可信")
    # 左前臂 13->15 投影缩到 12px，右侧仍是 ~62px：对称比 0.19 < SYM_MIN，
    # 且远/近端比 0.19 < PROP_MIN，两条约束都该命中。
    fr = frames_of(synth(over={15: (-64, 72)}))
    r.eq(float(pose.joint_reliability(fr, "L_ELBOW").mean()), 0.0,
         "左肘全帧不可信")
    r.eq(float(pose.joint_reliability(fr, "R_ELBOW").mean()), 1.0,
         "右肘不受牵连（只归咎更短的一侧）")
    r.eq(float(pose.joint_reliability(fr, "L_KNEE").mean()), 1.0, "左膝不受牵连")

    c = r.case("合成 · 右腿正对镜头：右膝不可信，左膝不受牵连")
    # 整条右腿沿纵向压缩（大腿 80→20px，小腿 80→40px），模拟腿指向镜头。
    # 只压膝盖不压脚踝是不对的——那样小腿反而变长，会把左膝也判成"短的一侧"。
    SQUASH = {26: (32, 160), 28: (32, 200)}
    fr = frames_of(synth(over=SQUASH))
    r.eq(float(pose.joint_reliability(fr, "R_KNEE").mean()), 0.0, "右膝全帧不可信")
    r.eq(float(pose.joint_reliability(fr, "L_KNEE").mean()), 1.0, "左膝仍可信")
    r.eq(float(pose.joint_reliability(fr, "L_ELBOW").mean()), 1.0, "左肘不受牵连")

    c = r.case("合成 · drive._unreliable 对同一段压缩也要报")
    xy = synth(over=SQUASH)
    xy[:20, 26] = (32 + 360, 220 + 300)          # 前 20 帧正常，后 20 帧压缩
    xy[:20, 28] = (34 + 360, 300 + 300)
    bad_r = drive._unreliable(xy, "R")
    r.eq(bool(bad_r[:20].any()), False, "正常帧不被标记")
    r.eq(bool(bad_r[20:].all()), True, "压缩帧全部被标记")
    r.eq(float(drive._unreliable(xy, "L").mean()), 0.0, "左腿不受牵连")

    # --- 4. 拒答：不可信时不给结论 -----------------------------------------
    c = r.case("拒答 · 全帧不可信时 detect_stalls / detect_rises / detect 不出结论")
    fr, fps = Q.frames_from_npz(Q.FIXTURES / "out5")
    z = np.load(Q.FIXTURES / "out5" / "keypoints.npz")
    ct = Q.contacts_from_evidence(Q.FIXTURES / "out5")
    n = len(z["xy"])
    rel_all = np.ones(n, bool)
    rel_none = np.zeros(n, bool)
    st_all = drive.detect_stalls(z["xy"], z["com"], ct, fps, reliable=rel_all)
    st_none = drive.detect_stalls(z["xy"], z["com"], ct, fps, reliable=rel_none)
    rs_all = drive.detect_rises(z["xy"], z["com"], ct, fps, reliable=rel_all)
    rs_none = drive.detect_rises(z["xy"], z["com"], ct, fps, reliable=rel_none)
    dv_all = drive.detect(z["xy"], z["com"], ct, fps, reliable=rel_all)
    dv_none = drive.detect(z["xy"], z["com"], ct, fps, reliable=rel_none)
    r.check(len(st_all) > 0, "可信时 detect_stalls 给出结论", len(st_all), "> 0")
    r.eq(len(st_none), 0, "不可信时 detect_stalls 一条不给")
    r.check(len(rs_all) > 0, "可信时 detect_rises 给出结论", len(rs_all), "> 0")
    r.eq(len(rs_none), 0, "不可信时 detect_rises 一条不给")
    r.eq(len(dv_none), 0, "不可信时 detect 一条不给")

    c = r.case("拒答 · 局部可信率低于 40% 的停滞段要被丢掉")
    # detect_stalls 里 `if rel < 0.4: continue`。把第一段停滞所在的帧
    # 打成不可信，那一段就该消失，而第二段照常给出。
    t0, t1 = st_all[0].t0, st_all[0].t1
    mask = rel_all.copy()
    mask[int(t0 * fps):int(t1 * fps)] = False
    st_part = drive.detect_stalls(z["xy"], z["com"], ct, fps, reliable=mask)
    r.eq(len(st_all) - len(st_part), 1, "恰好少了一段")
    r.check(all(abs(s.t0 - t0) > 1e-6 for s in st_part),
            f"消失的正是 {t0}–{t1}s 那段",
            [Q.r2(s.t0) for s in st_part], f"不含 {t0}")

    c = r.case("拒答 · 可信度会改变结论，不是装饰")
    r.check([Q.r2(s.t0) for s in st_all] != [Q.r2(s.t0) for s in st_part],
            "同一输入、不同可信掩膜 → 不同结论",
            ([Q.r2(s.t0) for s in st_all], [Q.r2(s.t0) for s in st_part]),
            "两者不同")

    # --- 5. 已知缺陷 D-005：Drive.knee_reliable 恒为 True -------------------
    c = r.case("Drive.knee_reliable 是否可能为 False（缺陷 D-005）")
    seen = []
    for d in ("out5", "out7"):
        zz = np.load(Q.FIXTURES / d / "keypoints.npz")
        cc = Q.contacts_from_evidence(Q.FIXTURES / d)
        ff, ffps = Q.frames_from_npz(Q.FIXTURES / d)
        for mask in (None, np.ones(len(zz["xy"]), bool), pose.reliability(ff)):
            seen += [dv.knee_reliable
                     for dv in drive.detect(zz["xy"], zz["com"], cc, ffps,
                                            reliable=mask)]
    r.check(len(seen) > 0, "至少检出了一些发力事件用于取样", len(seen), "> 0")
    r.known_defect(
        any(v is False for v in seen), "D-005",
        f"{len(seen)} 个发力事件全部 knee_reliable=True："
        f"detect() 在膝角不可信时 continue 掉了事件，"
        f"注释写的「不丢弃事件，只标记」与代码不符，"
        f"coach.py 的「该机位膝角不可测」分支不可达")

    # --- 6. 墙面坐标是承重的（D-006 的量化） -------------------------------
    c = r.case("墙面坐标不是可选项：去掉 wall_H 净上升就换一个数（缺陷 D-006）")
    s5 = json.loads((Q.FIXTURES / "out5" / "summary.json").read_text(encoding="utf-8"))
    pipe = {(x["t0"], x["t1"]): x["net_rise"] for x in s5["stalls"]}
    img = {(Q.r2(x.t0), Q.r2(x.t1)): Q.r2(x.net_rise)
           for x in drive.detect_stalls(z["xy"], z["com"], ct, fps,
                                        reliable=pose.reliability(fr))}
    r.eq(sorted(img), sorted(pipe), "两种坐标下停滞段的起止相同")
    diffs = {k: (pipe[k], img[k]) for k in pipe if k in img}
    detail = "；".join(f"{k}: 墙面 {a:+.2f} / 图像 {b:+.2f}（差 {abs(a - b):.2f}）"
                      for k, (a, b) in diffs.items())
    worst = max(abs(a - b) for a, b in diffs.values())
    r.check(worst > 0.15,
            f"至少一段的净上升因坐标系不同而显著改变 —— {detail}",
            Q.r2(worst), "> 0.15")
    # CASE-2608-001 的头条数字就是这一段：墙面坐标 -0.03，图像坐标 -0.24。
    r.close(pipe[(2.2, 6.07)], -0.03, 0.005, "管线（墙面坐标）2.2–6.07s 净上升")
    r.close(img[(2.2, 6.07)], -0.24, 0.005, "图像坐标下同一段净上升")
    r.known_defect(False, "D-006",
                   "wall_H 只存在于内存，未写进任何产物；"
                   "drive.* 三个检测器的管线口径无法脱离原视频复现")
    return r.report()


if __name__ == "__main__":
    Q.main_guard(run)
