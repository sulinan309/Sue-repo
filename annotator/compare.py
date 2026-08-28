#!/usr/bin/env python3
"""并排对比两次尝试：从「踩实高脚」那一刻起，看腿把人送高了多少。

    python3 compare.py 成功目录 失败目录 \
        --ok-video B.mp4 --fail-video A.mp4 -o compare.mp4

和 card.py（静态卡片）的分工：卡片是几张定格，截图就能转发；
这里是完整过程，两条轨迹当场分开——这是静态做不到的那部分。

## 三条设计决定

**锚在事件上，两段按真实速度播。** T0 ＝ 高脚建立持续接触的时刻（见
anchor.py）。上一版按「动作进度」把两段拉伸对齐，因为两段总时长不同；
锚定事件之后这个变形就不需要了——两段都从各自的 T0 起、按原速播 2 秒，
屏上一个共用的计时器。没有时间轴变形，就少一处要向读者解释的东西。

**实时数字这次可以上屏了。** 上一版把逐帧瞬时值放大当标题，结果某些帧上
失败的数字反而更小，对比自己塌掉。现在屏上的是**从 T0 起算的累计位移**，
不是瞬时采样：实测两条曲线在 0–2.0s 内从不交叉，最小间距 0.26 倍躯干长。
先验证不交叉，再决定敢不敢显示——顺序不能反。

**完整轨迹先画成暗线，再由亮线追上去。** 读者一开始就看得见整条路径，
所以不存在「挑了哪几帧」的问题；亮线推进的是时间，不是结论。

## 口径

一切以承重踝为参考点、再除以躯干长（见 anchor.py）。绝不输出像素值。
"""
from __future__ import annotations

import argparse

import cv2
import numpy as np

from climbanno.anchor import (
    load, idx, rise, common_boxes, draw_marks, crop_to, GHOST)
from climbanno.viz import (
    SURFACE, CARD, FAIL, OK, INK1, INK2, INKM, GRID, AXIS,
    T, wrap, rrect, paste_rounded)

PLAY_S = 2.0                  # 从 T0 起播多久
HOLD_IN, HOLD_OUT = 0.5, 1.6  # 首尾定格，给读者时间看清起点和终局
Y_LO, Y_HI = -0.6, 1.1        # 轨迹图纵轴；实测 -0.43 ~ +0.97
RAD = 16                      # 卡片圆角


def chart(canvas, lab, txt, x, y, w, h, rows, t_now, txt_only=False):
    """轨迹图：暗线是完整路径，亮线追到当前时刻。"""
    rrect(canvas, x, y, x + w - 1, y + h - 1, CARD, RAD)
    lab.append((x + 24, y + 18, "重心相对承重脚的高度", 23, INK1))
    tw = txt.w("重心相对承重脚的高度", 23)
    lab.append((x + 32 + tw, y + 23, "躯干长的倍数 · 从踩实瞬间起算",
                17, INKM, False))

    x0b, x1b = x + 96, x + w - 132
    ytop, ybot = y + 62, y + h - 58

    def py(v):
        return int(ybot - (v - Y_LO) / (Y_HI - Y_LO) * (ybot - ytop))

    def px(t):
        return int(x0b + (x1b - x0b) * t / PLAY_S)

    for v in (-0.5, 0.0, 0.5, 1.0):
        gy = py(v)
        cv2.line(canvas, (x0b, gy), (x1b, gy),
                 AXIS if v == 0 else GRID, 1, cv2.LINE_AA)
        s = f"{v:+.1f}" if v else " 0.0"
        lab.append((x0b - 14 - txt.w(s, 16, False), txt.vc(s, gy, 16, False),
                    s, 16, INKM, False))
    for t in (0.0, 0.5, 1.0, 1.5, 2.0):
        s = f"{t:.1f}s"
        lab.append((px(t) - txt.w(s, 16, False) / 2, ybot + 12, s, 16, INKM, False))

    for name, col, vs in rows:
        pts = [(px(k / len(vs) * PLAY_S), py(v)) for k, v in enumerate(vs)]
        dim = tuple(int(c * 0.34 + s * 0.66) for c, s in zip(col, CARD))
        for k in range(len(pts) - 1):            # 完整路径，压暗
            cv2.line(canvas, pts[k], pts[k + 1], dim, 2, cv2.LINE_AA)
        j = min(int(t_now / PLAY_S * (len(pts) - 1)), len(pts) - 1)
        for k in range(j):                       # 已走过的部分，点亮
            cv2.line(canvas, pts[k], pts[k + 1], col, 3, cv2.LINE_AA)
        cv2.circle(canvas, pts[j], 9, CARD, -1, cv2.LINE_AA)
        cv2.circle(canvas, pts[j], 6, col, -1, cv2.LINE_AA)
        lab.append((pts[-1][0] + 18, txt.vc(name, pts[-1][1], 19), name, 19, INK2))

    lab.append((x + 24, y + h - 26,
                "暗线＝完整轨迹　亮线＝已播放到这里", 16, INKM, False))


def main():
    ap = argparse.ArgumentParser(description="踩实高脚之后的并排对比")
    ap.add_argument("ok_dir")
    ap.add_argument("fail_dir")
    ap.add_argument("--ok-video", required=True)
    ap.add_argument("--fail-video", required=True)
    ap.add_argument("-o", "--out", default="compare.mp4")
    a = ap.parse_args()

    O = load(a.ok_dir, a.ok_video)
    F = load(a.fail_dir, a.fail_video)
    fps = O["fps"]
    npl = int(PLAY_S * fps)
    for nm, s in (("站起来了", O), ("没站起来", F)):
        avail = min(s["t_end"], s["n"]) - s["t0"]
        if avail < npl:
            raise SystemExit(f"{nm} 从 T0 起只有 {avail / fps:.1f}s，不足 {PLAY_S}s")

    series = {nm: [rise(s, s["t0"] + k) for k in range(npl)]
              for nm, s in (("站起来了", O), ("没站起来", F))}
    cross = [k for k in range(npl)
             if series["站起来了"][k] <= series["没站起来"][k] and k > 2]
    if cross:
        raise SystemExit(f"两条轨迹在 +{cross[0] / fps:.2f}s 交叉——"
                         "交叉时不能在屏上显示实时数字，先改口径")

    PAD, GAP, ASPECT = 24, 16, 0.60
    W = 968
    PW = (W - PAD * 2 - GAP) // 2
    PVH = int(round(PW / ASPECT))
    HEAD, PHH, CH = 136, 82, 296

    body = ("腿蹬出的力顺着腿的方向。重心在脚的侧后方时，这股力主要把人推离墙面；"
            "移到脚的正上方，同样的力才真正用在往上。")
    cue = "脚已经在上面了，现在把髋送到那只脚的正上方。"  # FAULT-ROCKOVER-STALL-010.hints
    note = ("以承重踝为参考点、除以躯干长，因此不受镜头移动和拍摄距离影响；"
            "两段均从各自的踩实瞬间起、按原速播放。重心为单目视频估计的二维代理。")

    txt = T()
    fw = W - PAD * 2
    foot, fy = [], 4
    for blk, sz, col, bold, gap in ((body, 20, INK2, False, 12),
                                    ("下次的口令：" + cue, 21, INK1, True, 12),
                                    (note, 16, INKM, False, 0)):
        for ln in wrap(txt, blk, sz, bold, fw):
            foot.append((fy, ln, sz, col, bold))
            fy += sz + 9
        fy += gap
    FOOT = fy + 4

    y_pan = HEAD
    y_ch = y_pan + PHH + PVH + 18
    y_ft = y_ch + CH + 18
    H = y_ft + FOOT + 20

    rows = [("站起来了", OK, O, "腿把人送上去了", PAD),
            ("没站起来", FAIL, F, "腿没接住，人沉回去", PAD + PW + GAP)]
    boxes = common_boxes([r[2] for r in rows], ASPECT,
                         (0.0, PLAY_S / 2, PLAY_S))

    n_in, n_out = int(HOLD_IN * fps), int(HOLD_OUT * fps)
    total = n_in + npl + n_out
    vw = cv2.VideoWriter(a.out, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))

    for f in range(total):
        k = min(max(f - n_in, 0), npl - 1)        # 首尾定格
        t = k / fps
        canvas = np.full((H, W, 3), SURFACE, np.uint8)
        lab = []

        for r, (name, col, s, verdict, px0) in enumerate(rows):
            i = s["t0"] + k
            rrect(canvas, px0, y_pan, px0 + PW - 1, y_pan + PHH + PVH - 1,
                  CARD, RAD)
            img = draw_marks(s, i, col, ghost=k > 0)
            paste_rounded(canvas, crop_to(img, boxes[r], PW, PVH),
                          px0, y_pan + PHH, RAD, top=False)
            cv2.rectangle(canvas, (px0 + 22, y_pan + 26),
                          (px0 + 35, y_pan + 39), col, -1)     # 色标
            lab.append((px0 + 46, y_pan + 16, name, 25, INK1))
            lab.append((px0 + 46, y_pan + 50, verdict, 17, INK2, False))
            v = f"{rise(s, i):+.2f}"
            lab.append((px0 + PW - 22 - txt.w(v, 34), y_pan + 24, v, 34, INK1))

        cv2.rectangle(canvas, (0, 0), (W, 4), GRID, -1)         # 播放进度
        cv2.rectangle(canvas, (0, 0), (int(W * (f + 1) / total), 4), INK2, -1)

        lab += [(PAD, 26, "踩实高脚之后，腿做了什么？", 36, INK1),
                (PAD, 76, "两段都从各自的踩实瞬间起算，按原速播放", 20, INK2, False)]
        badge = ("踩实瞬间" if f < n_in else
                 f"{PLAY_S:.1f} 秒后" if f >= n_in + npl else "进行中")
        tm = f"+{t:.2f}s"
        lab.append((W - PAD - txt.w(tm, 54), 22, tm, 54, INK1))
        lab.append((W - PAD - txt.w(badge, 17, False), 88, badge, 17, INKM, False))

        chart(canvas, lab, txt, PAD, y_ch, W - PAD * 2, CH,
              [(nm, OK if nm == "站起来了" else FAIL, series[nm])
               for nm in ("站起来了", "没站起来")], t)
        lab += [(PAD, y_ft + dy, ln, sz, c, b) for dy, ln, sz, c, b in foot]
        vw.write(txt.draw(canvas, lab))
    vw.release()

    print(f"已写出 {a.out}  {W}x{H}  {total} 帧 "
          f"（定格 {HOLD_IN}s + 播放 {PLAY_S}s + 定格 {HOLD_OUT}s）")
    for nm, s in (("站起来了", O), ("没站起来", F)):
        print(f"  {nm}  T0={s['t0'] / fps:.2f}s  踩实时横向偏 "
              f"{abs(s['dx'][s['t0']]):.2f}  " +
              "  ".join(f"+{d:.1f}s {rise(s, idx(s, d)):+.2f}"
                        for d in (0.5, 1.0, 1.5, 2.0)))
    print(f"  两条轨迹最小间距 "
          f"{min(series['站起来了'][k] - series['没站起来'][k] for k in range(3, npl)):.2f}"
          " 倍躯干长（不交叉，故实时数字可上屏）")


if __name__ == "__main__":
    main()
