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
import cv2
import numpy as np

from climbanno.viz import (
    SURFACE, CARD, FAIL, OK, INK1, INK2, INKM, GRID, AXIS, CASE,
    T, wrap, wash, cased)

from climbanno.anchor import (
    load, idx, rise, ghost_xy, common_boxes, draw_marks, crop_to, GHOST)

SAMPLES = (0.0, 0.4, 0.8)     # 两侧取同样的时刻
TRACK_S = 1.2                 # 轨迹图画到 T0 之后多久


def cell(s, dt, col, box, w_out, h_out):
    """一格定格。标记的画法在 anchor.draw_marks，与动态版共用。"""
    i = idx(s, dt)
    return crop_to(draw_marks(s, i, col, ghost=dt > 0), box, w_out, h_out)


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
    boxes = common_boxes([r[2] for r in rows], ASPECT, SAMPLES)
    y = HEAD + COLH
    for r, (name, col, s, verdict) in enumerate(rows):
        box = boxes[r]
        ry = y + r * (CH + GAP)
        cv2.rectangle(canvas, (PAD, ry), (PAD + 5, ry + CH), col, -1)
        lab.append((PAD + 18, ry + 6, name, 27, INK1))
        lab.append((PAD + 18, ry + 44, verdict, 17, INK2, False))
        d8 = rise(s, idx(s, 0.8))
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
                      f"接下来 0.8 秒，一个升 {rise(O, idx(O, 0.8)):+.2f}，"
                      f"一个沉 {rise(F, idx(F, 0.8)):+.2f}。",
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
        vs = [rise(s, s["t0"] + k) for k in range(n)]
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
              + "  ".join(f"+{dt:.1f}s {rise(s, idx(s, dt)):+.2f}" for dt in SAMPLES))


if __name__ == "__main__":
    main()
