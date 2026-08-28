#!/usr/bin/env python3
"""对攀岩视频做动作标注。

    python3 annotate.py 输入.mp4 -o 输出目录 [--model pose_landmarker_full.task]

产出：
    annotated.mp4   带覆盖层的视频
    evidence.jsonl  逐帧证据记录（每行一帧）
    summary.json    汇总 + 本次能/不能支撑的知识库 observables
    holds.json      检测到的岩点（参考帧坐标）

设计边界见 climbanno/contact.py 的模块说明：
所有接触状态都是二维视觉邻近代理，不是力学接触。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

import cv2
import numpy as np

from climbanno import pose as P
from climbanno import holds as HD
from climbanno import contact as CT
from climbanno import posture as PT
from climbanno import drive as DV
from climbanno import render as RD
from climbanno.kb_link import capability_report


def main():
    ap = argparse.ArgumentParser(description="攀岩视频动作标注")
    ap.add_argument("video")
    ap.add_argument("-o", "--out", default="out")
    ap.add_argument("--model", default="pose_landmarker_full.task")
    ap.add_argument("--ref-frame", type=int, default=0, help="用哪一帧检测岩点")
    ap.add_argument("--no-video", action="store_true", help="只跑分析不出视频")
    ap.add_argument("--samples", type=int, default=14, help="岩点检测采样帧数")
    ap.add_argument("--persist", type=float, default=0.4,
                    help="岩点位置一致性阈值：出现在多少比例的采样帧里才算数")
    args = ap.parse_args()

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        sys.exit(f"打不开视频：{args.video}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frames_bgr = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames_bgr.append(f)
    cap.release()
    n = len(frames_bgr)
    h, w = frames_bgr[0].shape[:2]
    print(f"[1/5] 读入 {n} 帧  {w}x{h}  {fps:.1f}fps")

    # ---- 姿态流 ----
    tracker = P.PoseTracker(args.model)
    pframes = [tracker(f, i, i / fps) for i, f in enumerate(frames_bgr)]
    hit1 = sum(f.ok for f in pframes)
    pframes, fixed = P.backfill(tracker, frames_bgr, pframes, fps)
    tracker.close()
    pframes = P.smooth(pframes)
    hit = sum(f.ok for f in pframes)
    print(f"[2/5] 姿态  检出 {hit}/{n} ({hit/n*100:.1f}%)"
          f"    首趟 {hit1} + 补检 {fixed}")

    # ---- 视觉流：岩点 ----
    ref_i = min(args.ref_frame, n - 1)
    grays = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames_bgr]
    hold_list, Hs = HD.detect_stable(frames_bgr, grays, pframes, ref_i,
                                     samples=args.samples, persist=args.persist)
    print(f"[3/5] 岩点  {len(hold_list)} 个稳定岩点"
          f"（{args.samples} 帧采样，位置一致性 ≥{args.persist:.0%}）")

    # ---- 墙面锁定：把参考帧岩点映射到每一帧 ----
    ref_pts = np.array([[hd.x, hd.y] for hd in hold_list], np.float32).reshape(-1, 1, 2)
    per_frame = []
    for i in range(n):
        pr = (cv2.perspectiveTransform(ref_pts, Hs[i]).reshape(-1, 2)
              if len(hold_list) else np.zeros((0, 2)))
        per_frame.append({hd.id: (float(pr[k][0]), float(pr[k][1]))
                          for k, hd in enumerate(hold_list)})
    drift = (float(np.mean(np.linalg.norm(
        np.array(list(per_frame[-1].values())) -
        np.array(list(per_frame[ref_i].values())), axis=1))) if hold_list else 0.0)
    print(f"[4/5] 墙面锁定  末帧岩点相对参考帧位移 {drift:.1f}px（相机漂移已补偿）")

    # ---- 接触代理与阶段 ----
    hr = {hd.id: hd.r for hd in hold_list}
    ev = CT.stabilise(CT.analyse(pframes, per_frame, fps, hold_r=hr, wall_H=Hs))
    post = PT.analyse(pframes)
    plan = CT.landing_plan(pframes, ev, wall_H=Hs)
    kp_xy = np.stack([f.xy if f.ok else np.full((33, 2), np.nan) for f in pframes])
    kp_com = np.array([f.com if f.com else (np.nan, np.nan) for f in pframes])
    ct_seq = {L: [next((c.state for c in e.contacts if c.limb == L), "uncertain")
                  for e in ev] for L in CT.LIMBS}
    drives = DV.detect(kp_xy, kp_com, ct_seq, fps)
    print(f"[5/6] 姿态状态  " + "  ".join(
        f"{k}{v}" for k, v in PT.summarise(post).get("状态占比", {}).items())
        + f"    落点计划 {len(plan)} 个    发力事件 {len(drives)} 次")
    for k, dv in enumerate(drives, 1):
        print(f"      第{k}次 {DV.SIDE_CN[dv.leg]}腿 {dv.t_drive:5.1f}s  "
              f"膝 {dv.knee_from:.0f}°→{dv.knee_to:.0f}°  "
              f"重心升 {dv.com_dy:.0f}px  {dv.chain_cn}")
    summ = CT.summarise(ev)

    # ---- 输出 ----
    with (out / "evidence.jsonl").open("w", encoding="utf-8") as fh:
        for e in ev:
            fh.write(json.dumps(e.as_dict(), ensure_ascii=False) + "\n")
    np.savez_compressed(out / "keypoints.npz",
        xy=np.stack([f.xy if f.ok else np.full((33, 2), np.nan) for f in pframes]),
        vis=np.stack([f.vis if f.ok else np.zeros(33) for f in pframes]),
        com=np.array([f.com if f.com else (np.nan, np.nan) for f in pframes]),
        hip=np.array([f.hip if f.hip else (np.nan, np.nan) for f in pframes]),
        fps=fps)
    (out / "holds.json").write_text(json.dumps(
        [{"id": hd.id, "x": hd.x, "y": hd.y, "r": hd.r, "area": hd.area,
          "kind": hd.kind} for hd in hold_list],
        ensure_ascii=False, indent=2), encoding="utf-8")

    report = capability_report(summ, len(hold_list))
    summ["source"] = {"video": args.video, "frames": n, "fps": fps,
                      "size": [w, h], "ref_frame": ref_i,
                      "holds_detected": len(hold_list)}
    summ["knowledge_base"] = report
    summ["posture"] = PT.summarise(post)
    summ["landings"] = len(plan)
    summ["drives"] = [{
        "leg": DV.SIDE_CN[x.leg], "t": round(x.t_drive, 2),
        "knee": [round(x.knee_from), round(x.knee_to)],
        "com_rise_px": round(x.com_dy), "com_dx_px": round(x.com_dx),
        "hand": x.hand, "t_hand": None if x.t_hand is None else round(x.t_hand, 2),
        "lead_s": None if x.lead is None else round(x.lead, 2),
        "chain": x.chain, "chain_cn": x.chain_cn,
        "phases": [{"阶段": a, "时间": b, "证据": c} for a, b, c in DV.describe(x)],
    } for x in drives]
    (out / "summary.json").write_text(
        json.dumps(summ, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.no_video:
        txt = RD.Text()
        POST_COL = {"frontal_straight": (120, 230, 140), "frontal_bent": (110, 190, 250),
                    "side_straight": (120, 230, 140), "side_bent": (110, 190, 250),
                    "transition": (200, 200, 200), "unknown": (150, 150, 150)}
        vw = cv2.VideoWriter(str(out / "annotated.mp4"),
                             cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
        for i in range(n):
            nxt = []
            for lg in CT.next_landings(plan, i, 2):
                pt = cv2.perspectiveTransform(
                    np.array(lg.wall_xy, np.float32).reshape(1, 1, 2), Hs[i]
                ).reshape(2) if Hs[i] is not None else np.array(lg.wall_xy)
                nxt.append((lg.limb, (float(pt[0]), float(pt[1])),
                            (lg.land - i) / fps))
            p_ = post[i]
            meta = {"hold_r": hr, "next_landings": nxt,
                    "drive": DV.phase_at(drives, i / fps),
                    "posture_cn": p_.state_cn, "orient": p_.orient,
                    "eL": p_.elbow_l, "eR": p_.elbow_r,
                    "posture_col": POST_COL.get(p_.state, (235, 235, 235))}
            vw.write(RD.draw_frame(frames_bgr[i], pframes[i], ev[i],
                                   per_frame[i], txt, meta=meta))
        vw.release()
        print(f"[6/6] 已写出 {out/'annotated.mp4'}")
    else:
        print("[6/6] 跳过视频渲染")

    print(f"\n耗时 {time.time()-t0:.1f}s   "
          f"姿态检出率 {summ['pose_rate']*100:.1f}%   "
          f"平均接触点 {summ.get('mean_contacts', 0)}/4")
    print("阶段分布：", summ.get("stage_frames"))


if __name__ == "__main__":
    main()
