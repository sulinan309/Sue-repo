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
from climbanno import coach as CO
from climbanno import render as RD
from climbanno.kb_link import capability_report


def main():
    ap = argparse.ArgumentParser(description="攀岩视频动作标注")
    ap.add_argument("video")
    ap.add_argument("-o", "--out", default="out")
    ap.add_argument("--model", default="pose_landmarker_full.task")
    ap.add_argument("--ref-frame", type=int, default=0, help="用哪一帧检测岩点")
    ap.add_argument("--no-video", action="store_true", help="只跑分析不出视频")
    ap.add_argument("--debug", action="store_true",
                    help="显示工程遥测面板（默认是面向用户的教练卡片）")
    ap.add_argument("--range", default=None, metavar="起:止",
                    help="只分析这一段（秒），例如 0:8.6")
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
    if args.range:
        a, b = (float(x) if x else None for x in args.range.split(":"))
        lo = int((a or 0) * fps)
        hi = int(b * fps) if b else len(frames_bgr)
        frames_bgr = frames_bgr[lo:hi]
        print(f"      只分析 {lo/fps:.2f}–{hi/fps:.2f}s")
    n = len(frames_bgr)
    h, w = frames_bgr[0].shape[:2]
    print(f"[1/5] 读入 {n} 帧  {w}x{h}  {fps:.1f}fps")

    # 场景突变检测：视频里混入非攀爬内容（录屏界面、剪辑切换）时，
    # 姿态和几何全部失效，但管线不会报错，只会安静地输出错误分析。
    # 这里只做告警，不自动裁剪——裁哪一段应当由人决定。
    gray0 = [float(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).mean()) for f in frames_bgr]
    jumps = [i for i in range(1, n) if abs(gray0[i] - gray0[i - 1]) > 12]
    if jumps:
        print(f"      ⚠ 检测到 {len(jumps)} 处画面突变，最早在 {jumps[0]/fps:.2f}s"
              f"（整体亮度跳变 >12）。若那里不是攀爬内容，用 --range 排除后重跑。")

    # ---- 姿态流 ----
    tracker = P.PoseTracker(args.model)
    pframes = [tracker(f, i, i / fps) for i, f in enumerate(frames_bgr)]
    hit1 = sum(f.ok for f in pframes)
    pframes, fixed = P.backfill(tracker, frames_bgr, pframes, fps)
    tracker.close()
    pframes = P.smooth(pframes)
    rel = P.reliability(pframes)
    wins = P.reliable_windows(rel, fps)
    hit = sum(f.ok for f in pframes)
    print(f"[2/5] 姿态  检出 {hit}/{n} ({hit/n*100:.1f}%)"
          f"    首趟 {hit1} + 补检 {fixed}")
    print(f"      可信 {int(rel.sum())}/{n} ({rel.mean()*100:.0f}%)"
          f"    可分析区间 " + ("、".join(f"{a:.1f}–{b:.1f}s" for a, b in wins)
                              if wins else "无"))
    if rel.mean() < 0.95:
        print("      （检出≠可信：肢段朝向镜头或关键点跳变时，角度类结论不成立）")

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
    kp_xy_img = kp_xy.copy()          # 渲染要用图像坐标，别被墙面变换覆盖
    kp_com = np.array([f.com if f.com else (np.nan, np.nan) for f in pframes])
    ct_seq = {L: [next((c.state for c in e.contacts if c.limb == L), "uncertain")
                  for e in ev] for L in CT.LIMBS}
    drives = DV.detect(kp_xy, kp_com, ct_seq, fps, wall_H=Hs, reliable=rel)
    stalls = DV.detect_stalls(kp_xy, kp_com, ct_seq, fps, wall_H=Hs, reliable=rel)
    rises = DV.detect_rises(kp_xy, kp_com, ct_seq, fps, wall_H=Hs, reliable=rel)
    cards = [c for c in CO.build(stalls, drives, rises)
             if float(rel[int(c.t0 * fps):max(int(c.t1 * fps), int(c.t0 * fps) + 1)]
                      .mean()) >= 0.6]      # 卡片不落在不可信区间上
    print(f"[5/6] 姿态状态  " + "  ".join(
        f"{k}{v}" for k, v in PT.summarise(post).get("状态占比", {}).items())
        + f"    落点计划 {len(plan)} 个    发力事件 {len(drives)} 次"
        + (f"    高脚停滞 {len(stalls)} 段" if stalls else "")
        + (f"    重心上升 {len(rises)} 次" if rises else ""))
    for k, r in enumerate(rises, 1):
        print(f"      上升{k} {r.t0:.2f}–{r.t1:.2f}s  净升 {r.net:+.2f} 倍躯干长"
              + (f"  {CT.LIMB_CN.get(r.hand, r.hand)}出手比起升晚 {r.lead:+.2f}s"
                 if r.lead is not None else "  出手未检出")
              + (f"  重心相对承重踝 {r.off_start:+.2f}→{r.off_end:+.2f}"
                 if r.off_start is not None else ""))
    for k, s in enumerate(stalls, 1):
        print(f"      停滞{k} {DV.SIDE_CN[s.leg]}腿 {s.t0:.1f}–{s.t1:.1f}s  "
              f"膝中位 {s.knee_med:.0f}°  净升 {s.net_rise:+.2f}  "
              f"重心偏移 {s.offset_med:+.2f}")
        for _what, _why, _unit in s.candidates():
            print(f"         · {_what}  [{_unit}]")
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
    summ["pose_reliable_rate"] = round(float(rel.mean()), 3)
    summ["analyzable_windows"] = [[round(a, 2), round(b, 2)] for a, b in wins]
    summ["rises"] = [{"t0": round(r.t0, 2), "t1": round(r.t1, 2),
                      "net": round(r.net, 2), "hand": r.hand,
                      "lead_s": None if r.lead is None else round(r.lead, 2),
                      "off_start": None if r.off_start is None else round(r.off_start, 2),
                      "off_end": None if r.off_end is None else round(r.off_end, 2),
                      "foot": r.foot} for r in rises]
    summ["coach_cards"] = CO.summary(cards)
    summ["stalls"] = [{
        "leg": DV.SIDE_CN[s.leg], "t0": round(s.t0, 2), "t1": round(s.t1, 2),
        "knee_med": round(s.knee_med), "knee_max": round(s.knee_max),
        "net_rise": round(s.net_rise, 2), "offset_med": round(s.offset_med, 2),
        "other_knee_med": round(s.other_knee_med),
        "foot_contact_rate": round(s.foot_contact_rate, 2),
        "candidates": [{"发现": a, "机制": b, "知识单元": c}
                       for a, b, c in s.candidates()],
    } for s in stalls]
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
                             cv2.VideoWriter_fourcc(*"mp4v"), float(fps),
                             (int(w), int(h)))
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
                    "debug": args.debug,
                    "card": CO.card_at(cards, i / fps),
                    "stall": next((s for s in stalls
                                   if s.t0 <= i / fps <= s.t1), None),
                    "ankle": (lambda a: (float(a[0]), float(a[1]))
                              if np.isfinite(a).all() else None)(
                        kp_xy_img[i, 28 if (next((s for s in stalls
                                                  if s.t0 <= i / fps <= s.t1), None)
                                            or type("x", (), {"leg": "R"})).leg == "R"
                                  else 27]),
                    "posture_cn": p_.state_cn, "orient": p_.orient,
                    "eL": p_.elbow_l, "eR": p_.elbow_r,
                    "posture_col": POST_COL.get(p_.state, (235, 235, 235))}
            vw.write(RD.draw_frame(frames_bgr[i], pframes[i], ev[i],
                                   per_frame[i], txt, meta=meta))
        vw.release()
        print(f"[6/6] 已写出 {out/'annotated.mp4'}")
    else:
        print("[6/6] 跳过视频渲染")

    if cards:
        print("\n教练卡片：")
        for c in cards:
            print(f"  [{c.t0:.1f}–{c.t1:.1f}s] {c.title}   {c.sub}")
            for x in c.todo:
                print(f"      → {x}")
    print(f"\n耗时 {time.time()-t0:.1f}s   "
          f"姿态检出率 {summ['pose_rate']*100:.1f}%   "
          f"平均接触点 {summ.get('mean_contacts', 0)}/4")
    print("阶段分布：", summ.get("stage_frames"))


if __name__ == "__main__":
    main()
