#!/usr/bin/env python3
"""并排对比两次尝试，把决定成败的那个量画出来。

    python3 compare.py 失败目录 成功目录 -o 输出.mp4

为什么值得单独做一个对比视频：
单看一次尝试，「重心偏离承重脚 0.45 倍躯干长」只是一个数字，用户没有参照。
把同一个人、同一面墙的成功和失败并排放，这个数字才变成一条可以看见的分界线。

只画一个量——重心与承重脚的水平距离。其余全部去掉。
对比的说服力来自「只有一个变量不同」，多画一样东西就削弱一分。
"""
from __future__ import annotations

import argparse
import json
import pathlib

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
L_SHO, R_SHO, L_HIP, R_HIP, L_ANK, R_ANK = 11, 12, 23, 24, 27, 28
SKEL = [(11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (11, 23), (12, 24),
        (23, 24), (23, 25), (25, 27), (24, 26), (26, 28), (27, 31), (28, 32)]

BAD = (95, 170, 255)      # 橙 —— 失败
GOOD = (120, 230, 140)    # 绿 —— 成功
COM_C = (225, 70, 225)
INK = (18, 17, 16)


class T:
    def __init__(self):
        self._c = {}

    def f(self, s, bold=True):
        k = (s, bold)
        if k not in self._c:
            self._c[k] = ImageFont.truetype(FONT if bold else FONT_R, s)
        return self._c[k]

    def size(self, t, s, bold=True):
        b = self.f(s, bold).getbbox(t)
        return b[2] - b[0], b[3] - b[1]

    def draw(self, bgr, items):
        im = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(im)
        for x, y, s, sz, c, *r in items:
            d.text((x, y), s, font=self.f(sz, r[0] if r else True),
                   fill=(c[2], c[1], c[0]))
        return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def load(outdir, t0, t1, video):
    d = np.load(pathlib.Path(outdir) / "keypoints.npz")
    xy, com = d["xy"], d["com"]
    fps = float(d["fps"]) if "fps" in d else 30.0
    ev = [json.loads(x) for x in
          (pathlib.Path(outdir) / "evidence.jsonl").open(encoding="utf-8")]
    cap = cv2.VideoCapture(video)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    a, b = int(t0 * fps), min(int(t1 * fps), len(xy), len(frames))
    return {"xy": xy[a:b], "com": com[a:b], "frames": frames[a:b],
            "ev": ev[a:b], "fps": fps}


def bearing_foot(xy, com, ev, i):
    """承重脚：接触中且位置更高的那只。"""
    st = {c["limb"]: c["state"] for c in ev[i]["contacts"]}
    c = [(f, k) for f, k in (("RF", R_ANK), ("LF", L_ANK))
         if st.get(f) == "contact" and np.isfinite(xy[i, k]).all()]
    if not c:
        c = [(f, k) for f, k in (("RF", R_ANK), ("LF", L_ANK))
             if np.isfinite(xy[i, k]).all()]
    return min(c, key=lambda x: xy[i, x[1], 1])[1] if c else None


def panel(src, i, col, title, sub, txt: T, w_out, h_out):
    xy, com, ev = src["xy"], src["com"], src["ev"]
    i = min(i, len(xy) - 1)
    img = src["frames"][i].copy()
    h, w = img.shape[:2]
    lab = []

    torso = np.linalg.norm((xy[i, L_SHO] + xy[i, R_SHO]) / 2 -
                           (xy[i, L_HIP] + xy[i, R_HIP]) / 2)
    # 骨架：压暗，只作背景
    for a, b in SKEL:
        if np.isfinite(xy[i, a]).all() and np.isfinite(xy[i, b]).all():
            cv2.line(img, tuple(xy[i, a].astype(int)), tuple(xy[i, b].astype(int)),
                     (150, 150, 150), 3, cv2.LINE_AA)

    off = None
    ank = bearing_foot(xy, com, ev, i)
    if ank is not None and np.isfinite(com[i]).all() and torso > 8:
        ax, ay = xy[i, ank].astype(int)
        cx, cy = com[i].astype(int)
        off = abs(float(com[i, 0] - xy[i, ank, 0])) / torso
        # 承重脚的铅垂线
        for yy in range(min(cy, ay) - 60, ay, 18):
            cv2.line(img, (ax, yy), (ax, min(yy + 9, ay)), col, 3, cv2.LINE_AA)
        cv2.circle(img, (ax, ay), 13, col, 4, cv2.LINE_AA)
        # 重心到铅垂线的水平距离
        cv2.arrowedLine(img, (cx, cy), (ax, cy), col, 5, cv2.LINE_AA, tipLength=0.16)
        cv2.circle(img, (cx, cy), 16, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(img, (cx, cy), 12, COM_C, -1, cv2.LINE_AA)

    img = cv2.resize(img, (w_out, h_out - 150))
    pad = np.full((150, w_out, 3), INK, np.uint8)
    img = np.vstack([pad, img])
    cv2.rectangle(img, (0, 0), (w_out - 1, 149), col, 3)
    cv2.rectangle(img, (0, 0), (7, 149), col, -1)
    lab.append((26, 16, title, 40, col))
    lab.append((26, 70, sub, 22, (205, 205, 205), False))
    if off is not None:
        s = f"{off:.2f}"
        tw, _ = txt.size(s, 52)
        lab.append((w_out - tw - 30, 40, s, 52, col))
        s2 = "重心偏离承重脚"
        tw2, _ = txt.size(s2, 19, False)
        lab.append((w_out - tw2 - 30, 104, s2, 19, (185, 185, 185), False))
    return txt.draw(img, lab), off      # 标签必须在这里画，之前只算不画


def main():
    ap = argparse.ArgumentParser(description="并排对比两次尝试")
    ap.add_argument("fail_dir")
    ap.add_argument("ok_dir")
    ap.add_argument("--fail-video", required=True)
    ap.add_argument("--ok-video", required=True)
    ap.add_argument("--fail-range", default="2.2:6.1")
    ap.add_argument("--ok-range", default="0.9:2.6")
    ap.add_argument("-o", "--out", default="compare.mp4")
    a = ap.parse_args()

    f0, f1 = (float(x) for x in a.fail_range.split(":"))
    o0, o1 = (float(x) for x in a.ok_range.split(":"))
    F = load(a.fail_dir, f0, f1, a.fail_video)
    O = load(a.ok_dir, o0, o1, a.ok_video)
    fps = F["fps"]
    n = max(len(F["frames"]), len(O["frames"]))

    PW, PH = 640, 1060
    HEAD, FOOT = 118, 128
    W, H = PW * 2 + 24, HEAD + PH + FOOT
    txt = T()
    vw = cv2.VideoWriter(a.out, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))

    offs_f, offs_o = [], []
    for i in range(n):
        canvas = np.full((H, W, 3), INK, np.uint8)
        pf, of_ = panel(F, i, BAD, "没站起来", "高脚踩住了，但身体上不去", txt, PW, PH)
        po, oo = panel(O, i, GOOD, "站起来了", "腿先蹬，身体先升，手后出", txt, PW, PH)
        canvas[HEAD:HEAD + PH, 0:PW] = pf
        canvas[HEAD:HEAD + PH, PW + 24:] = po
        if of_ is not None:
            offs_f.append(of_)
        if oo is not None:
            offs_o.append(oo)

        lab = [(26, 22, "同一个人 · 同一面墙 · 同一个动作", 34, (245, 245, 245)),
               (26, 72, "两次尝试之间，只有一个量不同", 22, (170, 170, 170), False)]
        # 底部：把差别写死
        y = HEAD + PH + 16
        mf = np.median(offs_f) if offs_f else float("nan")
        mo = np.median(offs_o) if offs_o else float("nan")
        lab += [
            (26, y, f"重心偏离承重脚（中位）    没站起来 {mf:.2f}"
                    f"        站起来了 {mo:.2f}", 27, (245, 245, 245)),
            (26, y + 40,
             "腿蹬出去的力是顺着腿的方向的。重心在脚的侧后方时，这股力主要把人推离墙面；"
             "移到脚的上方，同样的力才真正用在往上。", 21, (215, 215, 215), False),
            (26, y + 76,
             "重心与承重脚的水平距离来自单目视频视觉推断，未测量真实受力",
             18, (135, 195, 250), False),
        ]
        vw.write(txt.draw(canvas, lab))
    vw.release()
    print(f"已写出 {a.out}")
    print(f"  重心偏离承重脚 中位：没站起来 {np.median(offs_f):.2f}   "
          f"站起来了 {np.median(offs_o):.2f}")


if __name__ == "__main__":
    main()
