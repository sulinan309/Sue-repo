#!/usr/bin/env python3
"""静态对比卡片：锚在「踩实高脚」这个事件上，看之后 0.8 秒腿做了什么。

    python3 card.py 成功目录 失败目录 \
        --ok-video B.mp4 --fail-video A.mp4 -o card.png

和 compare.py（动态并排）的分工：
  compare.py 回答「两次差在哪个量上」——整段分布，适合边看边讲。
  card.py    回答「踩上去之后发生了什么」——事件前后的定格，适合截图转发。

三条和动态版不同的设计决定：

1. **锚在事件上，不锚在时间段上。** T0 ＝ 高脚建立持续接触的时刻
   （取最长的一段连续 contact 的起点；单次状态跳变太抖，不能用）。
   两侧取**同样的**偏移量 +0.4s / +0.8s——如果一边取 0.7s、另一边取 0.3s，
   比的就不是同一个阶段了。

2. **一切以承重踝为参考点。** 承重脚踩在固定的岩点上，用它作原点，
   镜头平移被精确抵消（本片镜头漂移达 183px），再除以躯干长，
   数字就能跨素材、跨机位、跨人比较。绝不输出像素值——
   机位近 20%，同一个动作的像素数就差 20%。

3. **定格必须自证有代表性。** 四张精选静帧没有任何机制排除「刚好挑到
   支持结论的那几帧」——这正是动态版踩过的坑。所以底部画完整轨迹，
   把取样点标在上面：读者能看见这三帧落在曲线的什么位置。
"""
from __future__ import annotations

import argparse
import json
import pathlib

import cv2
import numpy as np

from climbanno.viz import (
    SURFACE, CARD, FAIL, OK, INK1, INK2, INKM, GRID, AXIS, CASE,
    T, wrap, wash, cased)

L_SHO, R_SHO, L_HIP, R_HIP, L_KNE, R_KNE, L_ANK, R_ANK = 11, 12, 23, 24, 25, 26, 27, 28
GHOST = (150, 150, 150)       # 踩实瞬间的重心位置——中性灰，不占序列色
SAMPLES = (0.0, 0.4, 0.8)     # 两侧取同样的时刻
TRACK_S = 1.2                 # 轨迹图画到 T0 之后多久


def medf(a, w=7):
    """中位滤波：去掉关键点抖动，保留镜头跟随这种慢变化。"""
    out = a.copy()
    for i in range(len(a)):
        s = a[max(0, i - w // 2):i + w // 2 + 1]
        s = s[np.isfinite(s)]
        if len(s):
            out[i] = np.median(s)
    return out


def load(outdir, video, foot=R_ANK, limb="RF"):
    d = np.load(pathlib.Path(outdir) / "keypoints.npz")
    xy, com = d["xy"], d["com"]
    fps = float(d["fps"]) if "fps" in d else 30.0
    ev = [json.loads(x) for x in
          (pathlib.Path(outdir) / "evidence.jsonl").open(encoding="utf-8")]
    st = [{c["limb"]: c["state"] for c in e["contacts"]} for e in ev]

    ax, ay = medf(xy[:, foot, 0]), medf(xy[:, foot, 1])
    torso = medf(np.linalg.norm((xy[:, L_SHO] + xy[:, R_SHO]) / 2 -
                                (xy[:, L_HIP] + xy[:, R_HIP]) / 2, axis=1))
    cap = cv2.VideoCapture(video)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()

    # T0：最长的一段连续接触的起点。单次 contact 跳变每秒好几回，不能当事件用
    best, i = (0, 0), 0
    while i < len(st):
        if st[i].get(limb) == "contact":
            j = i
            while j < len(st) and st[j].get(limb) == "contact":
                j += 1
            if j - i > best[1] - best[0]:
                best = (i, j)
            i = j
        else:
            i += 1
    t0, t_end = best
    return {"xy": xy, "com": com, "frames": frames, "fps": fps, "torso": torso,
            "ax": ax, "ay": ay, "t0": t0, "t_end": t_end,
            "dx": (com[:, 0] - ax) / torso,      # 水平：力的方向对不对
            "dy": (ay - com[:, 1]) / torso}      # 垂直：腿站起来了多少


def idx(s, dt):
    return min(s["t0"] + int(round(dt * s["fps"])), len(s["xy"]) - 1,
               len(s["frames"]) - 1)


def ghost_xy(s, i):
    """踩实瞬间的重心，换算到第 i 帧的画面坐标——这样镜头漂移被抵消。"""
    t0 = s["t0"]
    return (s["ax"][i] + s["dx"][t0] * s["torso"][i],
            s["ay"][i] - s["dy"][t0] * s["torso"][i])


def common_boxes(srcs, aspect):
    """两行取同一个框尺寸：比例尺不同的话，两行之间就没法直接比大小。"""
    raw = [crop_box(s, aspect) for s in srcs]
    bw = max(b[2] - b[0] for b in raw)
    out = []
    for s, b in zip(srcs, raw):
        h, w = s["frames"][0].shape[:2]
        bh = bw / aspect
        if bw > w or bh > h:                 # 放不下就整体退回该段自己的框
            out.append(b)
            continue
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        cx = min(max(cx, bw / 2), w - bw / 2)
        cy = min(max(cy, bh / 2), h - bh / 2)
        out.append((int(cx - bw / 2), int(cy - bh / 2),
                    int(cx + bw / 2), int(cy + bh / 2)))
    return out


def crop_box(s, aspect):
    """框住这几帧里所有要画的东西：躯干、腿、重心、残影。"""
    pts = []
    for dt in SAMPLES:
        i = idx(s, dt)
        for k in (L_SHO, R_SHO, L_HIP, R_HIP, L_KNE, R_KNE, L_ANK, R_ANK):
            if np.isfinite(s["xy"][i, k]).all():
                pts.append(s["xy"][i, k])
        if np.isfinite(s["com"][i]).all():
            pts.append(s["com"][i])
        pts.append(np.array(ghost_xy(s, i)))
    p = np.array(pts)
    h, w = s["frames"][0].shape[:2]
    x0, x1, y0, y1 = p[:, 0].min(), p[:, 0].max(), p[:, 1].min(), p[:, 1].max()
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    bh = (y1 - y0) * 1.18
    bw = max(bh * aspect, (x1 - x0) * 1.45)
    bh = bw / aspect
    if bw > w:
        bw, bh = w, w / aspect
    if bh > h:
        bh, bw = h, h * aspect
    cx = min(max(cx, bw / 2), w - bw / 2)
    cy = min(max(cy, bh / 2), h - bh / 2)
    return (int(cx - bw / 2), int(cy - bh / 2),
            int(cx + bw / 2), int(cy + bh / 2))


def cell(s, dt, col, box, w_out, h_out):
    """一格定格：铅垂线 + 踩实瞬间的重心残影 + 当前重心 + 两者之间的位移。"""
    i = idx(s, dt)
    img = s["frames"][i].copy()
    a = (int(s["ax"][i]), int(s["ay"][i]))
    c = s["com"][i]

    if np.isfinite(c).all():
        c = (int(c[0]), int(c[1]))
        g = ghost_xy(s, i)
        g = (int(g[0]), int(g[1]))
        # 承重脚的铅垂参考线：水平偏移就是重心到它的距离
        cased(lambda k, t: cv2.line(img, (a[0], min(c[1], g[1]) - 70), a, k, t,
                                    cv2.LINE_AA), col, 7, 3)
        cased(lambda k, t: cv2.circle(img, a, 13, k, t, cv2.LINE_AA), col, 8, 4)
        # 水平偏移，画在重心那一行
        cased(lambda k, t: cv2.arrowedLine(img, c, (a[0], c[1]), k, t,
                                           cv2.LINE_AA, tipLength=0.2), col, 9, 5)
        if dt > 0:
            # 残影 + 位移：虚线圆是踩实瞬间重心所在，箭头是这段时间走了多远
            for k in range(0, 360, 30):
                cv2.ellipse(img, g, (13, 13), 0, k, k + 16, CASE, 6, cv2.LINE_AA)
                cv2.ellipse(img, g, (13, 13), 0, k, k + 16, GHOST, 3, cv2.LINE_AA)
            if abs(c[1] - g[1]) > 12:
                cased(lambda k, t: cv2.arrowedLine(img, (g[0], g[1]), (g[0], c[1]),
                                                   k, t, cv2.LINE_AA, tipLength=0.18),
                      col, 11, 6)
        cv2.circle(img, c, 12, CASE, -1, cv2.LINE_AA)
        cv2.circle(img, c, 9, (255, 255, 255), -1, cv2.LINE_AA)

    x0, y0, x1, y1 = box
    return cv2.resize(img[y0:y1, x0:x1], (w_out, h_out))


def track(canvas, lab, txt, x, y, w, h, rows, x0b, x1b):
    """轨迹图：证明那三帧不是挑出来的——它们落在完整曲线上。"""
    cv2.rectangle(canvas, (x, y), (x + w - 1, y + h - 1), CARD, -1)
    lab.append((x + 22, y + 16, "重心相对承重脚的高度变化", 23, INK1))
    tw = txt.w("重心相对承重脚的高度变化", 23)
    lab.append((x + 30 + tw, y + 21, "躯干长的倍数 · 从踩实瞬间起算",
                17, INKM, False))

    lo, hi = -0.6, 0.8
    ytop, ybot = y + 56, y + h - 62

    def py(v):
        return ybot - (v - lo) / (hi - lo) * (ybot - ytop)

    def px(t):
        return x0b + (x1b - x0b) * t / TRACK_S

    for v in (-0.5, -0.25, 0.0, 0.25, 0.5, 0.75):
        gy = int(py(v))
        cv2.line(canvas, (x0b, gy), (x1b, gy),
                 AXIS if v == 0 else GRID, 1, cv2.LINE_AA)
        s = f"{v:+.2f}" if v else " 0.00"
        lab.append((x0b - 12 - txt.w(s, 16, False), txt.vc(s, gy, 16, False),
                    s, 16, INKM, False))
    for t in (0.0, 0.4, 0.8, 1.2):
        s = f"{t:.1f}s"
        lab.append((px(t) - txt.w(s, 16, False) / 2, ybot + 10, s, 16, INKM, False))

    for name, col, ts, vs in rows:
        pts = [(int(px(t)), int(py(v))) for t, v in zip(ts, vs)
               if np.isfinite(v) and t <= TRACK_S]
        for k in range(len(pts) - 1):
            cv2.line(canvas, pts[k], pts[k + 1], col, 2, cv2.LINE_AA)
        for dt in SAMPLES:                       # 取样点标出来
            j = int(round(dt * (len(ts) - 1) / ts[-1])) if ts[-1] else 0
            if j < len(vs) and np.isfinite(vs[j]):
                p = (int(px(ts[j])), int(py(vs[j])))
                cv2.circle(canvas, p, 8, CARD, -1, cv2.LINE_AA)
                cv2.circle(canvas, p, 5, col, -1, cv2.LINE_AA)
        if pts:                                  # 线尾直接标名，不靠图例配色
            lab.append((pts[-1][0] + 14, txt.vc(name, pts[-1][1], 20), name, 20, INK1))

    lab.append((x + 22, y + h - 22,
                "实线＝完整轨迹　●＝上面三张定格的取样时刻", 16, INKM, False))


def main():
    ap = argparse.ArgumentParser(description="踩实高脚之后的定格对比卡片")
    ap.add_argument("ok_dir")
    ap.add_argument("fail_dir")
    ap.add_argument("--ok-video", required=True)
    ap.add_argument("--fail-video", required=True)
    ap.add_argument("-o", "--out", default="card.png")
    a = ap.parse_args()

    O = load(a.ok_dir, a.ok_video)
    F = load(a.fail_dir, a.fail_video)
    txt = T()

    PAD, GAP, ASPECT = 24, 14, 0.60
    GUT = 172                                  # 左侧行名栏
    W = 1240
    CW = (W - PAD * 2 - GUT - GAP * 2) // 3
    CH = int(round(CW / ASPECT))
    HEAD, COLH, TRK = 128, 44, 264

    body = ("腿蹬出的力顺着腿的方向。重心在脚的侧后方时，这股力主要把人推离墙面；"
            "移到脚的正上方，同样的力才真正用在往上。")
    cue = "脚已经在上面了，现在把髋送到那只脚的正上方。"   # 取自 FAULT-ROCKOVER-STALL-010.hints
    note = ("所有量以承重踝为参考点、再除以躯干长，因此不受镜头移动和拍摄距离影响；"
            "两侧取同样的时刻。重心为单目视频估计的二维代理，未测量真实受力。")

    fw = W - PAD * 2
    foot, fy = [], 6
    for blk, sz, col, bold, gap in ((body, 20, INK2, False, 12),
                                    ("下次的口令：" + cue, 21, INK1, True, 12),
                                    (note, 16, INKM, False, 0)):
        for ln in wrap(txt, blk, sz, bold, fw):
            foot.append((fy, ln, sz, col, bold))
            fy += sz + 9
        fy += gap
    FOOT = fy + 4

    H = HEAD + COLH + CH * 2 + GAP + 18 + TRK + 16 + FOOT
    canvas = np.full((H, W, 3), SURFACE, np.uint8)
    lab = []

    rows = [("站起来了", OK, O, "重心升上去了"),
            ("没站起来", FAIL, F, "重心反而沉下去")]
    boxes = common_boxes([r[2] for r in rows], ASPECT)
    y = HEAD + COLH
    for r, (name, col, s, verdict) in enumerate(rows):
        box = boxes[r]
        ry = y + r * (CH + GAP)
        cv2.rectangle(canvas, (PAD, ry), (PAD + 5, ry + CH), col, -1)
        lab.append((PAD + 18, ry + 6, name, 27, INK1))
        lab.append((PAD + 18, ry + 44, verdict, 17, INK2, False))
        d8 = s["dy"][idx(s, 0.8)] - s["dy"][s["t0"]]
        lab.append((PAD + 18, ry + 84, f"{d8:+.2f}", 40, INK1))
        lab.append((PAD + 18, ry + 134, "0.8 秒内的高度变化", 15, INKM, False))
        lab.append((PAD + 18, ry + 170,
                    f"踩实时横向偏 {abs(s['dx'][s['t0']]):.2f}", 16, INK2, False))
        for c, dt in enumerate(SAMPLES):
            cx = PAD + GUT + c * (CW + GAP)
            canvas[ry:ry + CH, cx:cx + CW] = cell(s, dt, col, box, CW, CH)
        if r == 0:                              # 列头只写一次
            for c, dt in enumerate(SAMPLES):
                cx = PAD + GUT + c * (CW + GAP)
                t = "踩实瞬间" if dt == 0 else f"+{dt:.1f} 秒"
                lab.append((cx + CW / 2 - txt.w(t, 21) / 2, ry - 34, t, 21, INK1))

    lab += [(PAD, 22, "踩上高脚之后，腿做了什么？", 40, INK1),
            (PAD, 74, f"两次都把右脚踩实了。踩实时重心横向偏出 "
                      f"{abs(O['dx'][O['t0']]):.2f} 对 {abs(F['dx'][F['t0']]):.2f}；"
                      f"接下来 0.8 秒，一个升 "
                      f"{O['dy'][idx(O, 0.8)] - O['dy'][O['t0']]:+.2f}，一个沉 "
                      f"{F['dy'][idx(F, 0.8)] - F['dy'][F['t0']]:+.2f}。",
             21, INK2, False)]
    lx, ly = W - PAD, 88                      # 图例：画真的标记，不用文字里的 ○●
    for text, kind in (("承重脚铅垂线", "line"), ("当前重心", "dot"),
                       ("踩实瞬间的重心", "ghost")):
        lx = int(lx - txt.w(text, 17, False))
        lab.append((lx, txt.vc(text, ly, 17, False), text, 17, INKM, False))
        lx -= 26
        if kind == "dot":
            cv2.circle(canvas, (lx + 5, ly), 8, CASE, -1, cv2.LINE_AA)
            cv2.circle(canvas, (lx + 5, ly), 6, (255, 255, 255), -1, cv2.LINE_AA)
        elif kind == "ghost":
            for k in range(0, 360, 40):
                cv2.ellipse(canvas, (lx + 5, ly), (7, 7), 0, k, k + 22,
                            GHOST, 2, cv2.LINE_AA)
        else:
            cv2.line(canvas, (lx + 5, ly - 9), (lx + 5, ly + 9), INK2, 3, cv2.LINE_AA)
        lx -= 22

    ty = y + CH * 2 + GAP + 18
    trows = []
    for name, col, s, _ in rows:
        n = min(int(TRACK_S * s["fps"]) + 1, s["t_end"] - s["t0"])
        ts = [k / s["fps"] for k in range(n)]
        vs = [s["dy"][s["t0"] + k] - s["dy"][s["t0"]] for k in range(n)]
        trows.append((name, col, ts, vs))
    track(canvas, lab, txt, PAD, ty, W - PAD * 2, TRK, trows,
          PAD + 92, W - PAD - 132)

    fyy = ty + TRK + 16
    lab += [(PAD, fyy + dy, ln, sz, col, bold) for dy, ln, sz, col, bold in foot]
    cv2.imwrite(a.out, txt.draw(canvas, lab))

    print(f"已写出 {a.out}  {W}x{H}")
    for name, _, s, _ in rows:
        print(f"  {name}  T0={s['t0'] / s['fps']:.2f}s  "
              f"横向偏 {abs(s['dx'][s['t0']]):.2f}  "
              + "  ".join(f"+{dt:.1f}s {s['dy'][idx(s, dt)] - s['dy'][s['t0']]:+.2f}"
                          for dt in SAMPLES))


if __name__ == "__main__":
    main()
