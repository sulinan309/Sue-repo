#!/usr/bin/env python3
"""并排对比两次尝试，把决定成败的那个量画出来。

    python3 compare.py 失败目录 成功目录 \
        --fail-video A.mp4 --ok-video B.mp4 -o compare.mp4

只画一个量——重心与承重脚的水平距离（除以躯干长）。其余全部去掉。
对比的说服力来自「只有一个变量不同」，多画一样东西就削弱一分。

排版的三条硬规则（吃过亏才写下来的）：

1. 论据必须是**整段的统计量**，不能是逐帧实时值。
   逐帧值会波动：失败那一次有 3% 的帧比成功的中位数还低。
   如果把实时数字放大当标题，总有几帧会自己打自己的脸。
   所以标题位是中位数，实时值只以一个小圆点出现在分布里——
   读者看到的是「它偶尔到过那儿，但它不住在那儿」。

2. 统计量在渲染前一次算完。
   之前是边写帧边往列表里 append 再取中位数，
   于是第 5 帧显示的是前 5 帧的中位数，数字一路漂移。

3. 文字不穿数据色。颜色只上到色块、条、箭头；
   标题和数值一律用墨色，靠旁边的色标认身份。

配色不是挑出来的，是验出来的（dataviz 规范的六项检查，深色底 #101112）：
    绿/橙、红/绿这类「成功=绿 失败=红」的直觉配色，
    在红绿色盲下 ΔE 只有 4.1——**两块颜色根本分不开**，低于 6–8 的下限带，
    再加辅助编码也救不回来。改用分类槽位 1/2（蓝 #3987e5、橙 #d95926）：
    CVD ΔE 26.8，常视 ΔE 31.8，对比度均过 3:1，六项全过。
    身份另有直接标签兜底，任何一处都不靠颜色单独承担。
"""
from __future__ import annotations

import argparse
import json
import pathlib

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

L_SHO, R_SHO, L_HIP, R_HIP, L_ANK, R_ANK = 11, 12, 23, 24, 27, 28
SKEL = [(11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (11, 23), (12, 24),
        (23, 24), (23, 25), (25, 27), (24, 26), (26, 28), (27, 31), (28, 32)]

# —— 调色板（BGR）。深色底 #101112，全部经 validate_palette.js 验过 ——
SURFACE = (18, 17, 16)        # #101112  页面底
CARD = (25, 26, 26)           # #1a1a19  卡片面
FAIL = (38, 89, 217)          # #d95926  分类槽位 2 橙 —— 没站起来
OK = (229, 135, 57)           # #3987e5  分类槽位 1 蓝 —— 站起来了
INK1 = (255, 255, 255)        # #ffffff  主墨
INK2 = (183, 194, 195)        # #c3c2b7  次墨
INKM = (129, 135, 137)        # #898781  弱墨（轴、注解）
GRID = (42, 44, 44)           # #2c2c2a  网格发丝线
AXIS = (53, 56, 56)           # #383835  基线
CASE = (12, 12, 12)           # 视频上覆盖层的包边色（画面即"底"，靠包边脱开）

NO_START = "。，、；：？！）】》」』·…%"   # 避头尾：这些字符不另起一行

BAR_H = 22                    # 条 ≤24px，留白比填满好看
CAP_R = 4                     # 数据端 4px 圆角，基线端方角
X_MAX = 0.6                   # 轴上限；实测最大 0.54


class T:
    """文字层：整帧只做一次 BGR→PIL→BGR，标签先攒后画。"""

    def __init__(self):
        self._c = {}

    def f(self, s, bold=True):
        k = (s, bold)
        if k not in self._c:
            self._c[k] = ImageFont.truetype(FONT_B if bold else FONT_R, s)
        return self._c[k]

    def w(self, t, s, bold=True):
        return self.f(s, bold).getlength(t)

    def vc(self, t, cy, s, bold=True):
        """返回让文字在 cy 处垂直居中的绘制 y。"""
        b = self.f(s, bold).getbbox(t)
        return cy - (b[1] + b[3]) / 2

    def draw(self, bgr, items):
        im = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(im)
        for x, y, s, sz, c, *r in items:
            d.text((x, y), s, font=self.f(sz, r[0] if r else True),
                   fill=(c[2], c[1], c[0]))
        return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


# ——————————————————————————— 绘图基元 ———————————————————————————

def wrap(txt, s, size, bold, width):
    """按实测宽度断行。文字宁可多占一行，也不能被画布切掉。"""
    lines, cur = [], ""
    for ch in s:
        if not cur or txt.w(cur + ch, size, bold) <= width:
            cur += ch
        elif ch in NO_START:
            lines.append(cur + ch)
            cur = ""
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def rbar(img, x0, y0, x1, y1, col, r=CAP_R):
    """从基线长出的横条：基线端方角，数据端 r 圆角。"""
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    if x1 - x0 <= r:
        cv2.rectangle(img, (x0, y0), (max(x1, x0 + 1), y1), col, -1)
        return
    cv2.rectangle(img, (x0, y0), (x1 - r, y1), col, -1, cv2.LINE_AA)
    cv2.rectangle(img, (x1 - r, y0 + r), (x1, y1 - r), col, -1, cv2.LINE_AA)
    cv2.ellipse(img, (x1 - r, y0 + r), (r, r), 0, -90, 0, col, -1, cv2.LINE_AA)
    cv2.ellipse(img, (x1 - r, y1 - r), (r, r), 0, 0, 90, col, -1, cv2.LINE_AA)


def wash(img, x0, y0, x1, y1, col, a):
    """色相淡洗，不用饱和色块。"""
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    sub = img[y0:y1, x0:x1]
    if sub.size:
        sub[:] = (sub * (1 - a) + np.array(col, float) * a).astype(np.uint8)


def cased(fn, col, wide, thin):
    """先画暗包边再画本体——覆盖在视频上的标记靠这个脱开背景。"""
    fn(CASE, wide)
    fn(col, thin)


# ——————————————————————————— 数据 ———————————————————————————

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
            "ev": ev[a:b], "fps": fps, "dur": (b - a) / fps}


def bearing_foot(src, i):
    """承重脚：接触中且位置更高的那只。"""
    xy, ev = src["xy"], src["ev"]
    st = {c["limb"]: c["state"] for c in ev[i]["contacts"]}
    c = [k for f, k in (("RF", R_ANK), ("LF", L_ANK))
         if st.get(f) == "contact" and np.isfinite(xy[i, k]).all()]
    if not c:
        c = [k for f, k in (("RF", R_ANK), ("LF", L_ANK))
             if np.isfinite(xy[i, k]).all()]
    return min(c, key=lambda k: xy[i, k, 1]) if c else None


def offsets(src):
    """整段的逐帧偏移量，渲染前一次算完——不能边画边攒。"""
    xy, com = src["xy"], src["com"]
    out = np.full(len(xy), np.nan)
    for i in range(len(xy)):
        ank = bearing_foot(src, i)
        if ank is None or not np.isfinite(com[i]).all():
            continue
        torso = np.linalg.norm((xy[i, L_SHO] + xy[i, R_SHO]) / 2 -
                               (xy[i, L_HIP] + xy[i, R_HIP]) / 2)
        if torso > 8:
            out[i] = abs(float(com[i, 0] - xy[i, ank, 0])) / torso
    return out


def crop_box(src, aspect):
    """整段固定一个裁切框：人只占画面约 1/4，不裁就是在并排展示两面墙。

    用整段的关键点包围盒定框，所以镜头漂移时人也不会跑出框。
    """
    h, w = src["frames"][0].shape[:2]
    p = src["xy"][np.isfinite(src["xy"]).all(-1)]
    if not len(p):
        return 0, 0, w, h
    x0, x1 = p[:, 0].min(), p[:, 0].max()
    y0, y1 = p[:, 1].min(), p[:, 1].max()
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    bh = (y1 - y0) * 1.12
    bw = max(bh * aspect, (x1 - x0) * 1.30)
    bh = bw / aspect
    if bw > w:                       # 放不下就以画幅宽为准
        bw, bh = w, w / aspect
    if bh > h:
        bh, bw = h, h * aspect
    cx = min(max(cx, bw / 2), w - bw / 2)
    cy = min(max(cy, bh / 2), h - bh / 2)
    return (int(cx - bw / 2), int(cy - bh / 2),
            int(cx + bw / 2), int(cy + bh / 2))


# ——————————————————————————— 视频面板 ———————————————————————————

def video_panel(src, i, col, box, w_out, h_out):
    img = src["frames"][i].copy()
    xy, com = src["xy"], src["com"]

    # 骨架只是背景：压暗包边 + 细亮线，别跟数据标记抢
    for a, b in SKEL:
        if np.isfinite(xy[i, a]).all() and np.isfinite(xy[i, b]).all():
            pa = tuple(xy[i, a].astype(int))
            pb = tuple(xy[i, b].astype(int))
            cased(lambda c, t: cv2.line(img, pa, pb, c, t, cv2.LINE_AA),
                  (205, 205, 205), 6, 2)

    ank = bearing_foot(src, i)
    if ank is not None and np.isfinite(com[i]).all():
        ax, ay = xy[i, ank].astype(int)
        cx, cy = com[i].astype(int)
        # 承重脚的铅垂参考线（实线、细，不跟骨架混）
        top = min(cy, ay) - 70
        cased(lambda c, t: cv2.line(img, (ax, top), (ax, ay), c, t,
                                         cv2.LINE_AA), col, 6, 2)
        cased(lambda c, t: cv2.circle(img, (ax, ay), 12, c, t,
                                           cv2.LINE_AA), col, 7, 3)
        # 被测量的那一段：重心 → 铅垂线的水平距离
        cased(lambda c, t: cv2.arrowedLine(img, (cx, cy), (ax, cy), c, t,
                                                cv2.LINE_AA, tipLength=0.18),
              col, 9, 5)
        # 重心是地标不是序列，用中性白 + 暗环，少占一个色相
        cv2.circle(img, (cx, cy), 10, CASE, -1, cv2.LINE_AA)
        cv2.circle(img, (cx, cy), 8, (255, 255, 255), -1, cv2.LINE_AA)

    x0, y0, x1, y1 = box
    return cv2.resize(img[y0:y1, x0:x1], (w_out, h_out))


# ——————————————————————————— 图表 ———————————————————————————

def chart(canvas, lab, txt, x, y, w, h, rows, x0b, x1b):
    """两行横条：条＝整段中位数（论据），淡带＝80% 分位区间，点＝当前帧。

    读者因此看到的是一个分布，不是一个会跳的数字。
    """
    cv2.rectangle(canvas, (x, y), (x + w - 1, y + h - 1), CARD, -1)

    lab.append((x + 20, y + 15, "重心偏离承重脚", 23, INK1))
    tw = txt.w("重心偏离承重脚", 23)
    lab.append((x + 28 + tw, y + 20, "躯干长的倍数 · 越小越省力", 17, INKM, False))

    y_ax = y + h - 56
    span = x1b - x0b

    def px(v):
        return x0b + span * min(v, X_MAX) / X_MAX

    for t in (0.0, 0.2, 0.4, 0.6):                     # 发丝网格，实线，退后
        gx = int(px(t))
        cv2.line(canvas, (gx, y + 46), (gx, y_ax), GRID, 1, cv2.LINE_AA)
        s = f"{t:.1f}"
        lab.append((gx - txt.w(s, 17, False) / 2, y_ax + 10, s, 17, INKM, False))
    cv2.line(canvas, (x0b, y_ax), (x1b, y_ax), AXIS, 1, cv2.LINE_AA)

    for r, (name, col, med, lo, hi, mn, mx, cur) in enumerate(rows):
        ry = y + 54 + r * 62
        cy = ry + BAR_H // 2
        # 色标：与视频面板左侧色条同宽同色，身份由它承担，文字不穿色
        cv2.rectangle(canvas, (x + 20, ry - 1), (x + 25, ry + BAR_H + 1), col, -1)
        lab.append((x + 38, txt.vc(name, cy, 21), name, 21, INK1))

        bx = px(med)
        rbar(canvas, x0b, ry, bx, ry + BAR_H, col)
        v = f"{med:.2f}"
        vw = txt.w(v, 30)
        vx = bx + 12 if bx + 12 + vw < x1b + 62 else bx - vw - 12
        lab.append((vx, txt.vc(v, cy, 30), v, 30, INK1))

        # 分布带：80% 分位淡洗 + 全距发丝线 + 当前帧的点
        sy = ry + BAR_H + 9
        cv2.line(canvas, (int(px(mn)), sy + 5), (int(px(mx)), sy + 5),
                 AXIS, 1, cv2.LINE_AA)
        wash(canvas, px(lo), sy, px(hi), sy + 10, col, 0.22)
        if np.isfinite(cur):
            pxc = int(px(cur))
            cv2.circle(canvas, (pxc, sy + 5), 7, CARD, -1, cv2.LINE_AA)
            cv2.circle(canvas, (pxc, sy + 5), 5, col, -1, cv2.LINE_AA)

    lab.append((x + 20, y + h - 26,
                "条＝整段中位数　淡带＝80% 的时间落在这里　细线＝全距　●＝当前帧",
                16, INKM, False))


# ——————————————————————————— 主流程 ———————————————————————————

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

    # 统计量在渲染前一次算完
    sf, so = offsets(F), offsets(O)
    gf, go = sf[np.isfinite(sf)], so[np.isfinite(so)]
    if not len(gf) or not len(go):
        raise SystemExit("两段里至少有一段没有可用帧")
    mf, mo = float(np.median(gf)), float(np.median(go))
    below = int((gf < mo).sum())
    above = int((go > mf).sum())

    txt = T()
    body = ("腿蹬出的力顺着腿的方向。重心在脚的侧后方时，这股力主要把人推离墙面；"
            "移到脚的正上方，同样的力才真正用在往上。")
    hit = (f"没站起来的 {len(gf)} 帧里，仅 {below} 帧低于站起来了的中位数；"
           + ("反过来，一帧也没有。" if not above else f"反过来有 {above} 帧。"))
    src_note = "重心为单目视频估计的二维代理，未测量真实受力"

    PAD, GAP, ASPECT = 20, 16, 0.46
    PW = 432
    PVH = int(round(PW / ASPECT))
    PHH = 84
    HEAD, CH = 100, 224
    W = PAD * 2 + PW * 2 + GAP

    # 页脚按实际行数排，改文案不会再切字
    fw = W - PAD * 2
    foot, fy = [], 4
    for block, sz, col, bold, gap in ((body, 20, INK2, False, 14),
                                      (hit, 20, INK1, True, 12),
                                      (src_note, 16, INKM, False, 0)):
        for ln in wrap(txt, block, sz, bold, fw):
            foot.append((fy, ln, sz, col, bold))
            fy += sz + 9
        fy += gap
    FOOT = fy + 6
    H = HEAD + PHH + PVH + 16 + CH + 14 + FOOT
    y_pan, y_ch, y_ft = HEAD, HEAD + PHH + PVH + 16, HEAD + PHH + PVH + 16 + CH + 14
    x0b, x1b = PAD + 152, W - PAD - 92        # 条的起止（右侧给数值留位）

    bf, bo = crop_box(F, ASPECT), crop_box(O, ASPECT)
    n = max(len(F["frames"]), len(O["frames"]))
    vw = cv2.VideoWriter(a.out, cv2.VideoWriter_fourcc(*"mp4v"), F["fps"], (W, H))

    panels = [("没站起来", FAIL, "高脚踩住了，但身体上不去", F, sf, bf, PAD,
               f"{F['dur']:.1f}s", f"原片 {f0}–{f1}s"),
              ("站起来了", OK, "腿先蹬，身体先升，手后出", O, so, bo,
               PAD + PW + GAP, f"{O['dur']:.1f}s", f"原片 {o0}–{o1}s")]

    for i in range(n):
        p = i / max(n - 1, 1)                 # 按动作进度对齐，不按秒对齐
        canvas = np.full((H, W, 3), SURFACE, np.uint8)
        lab = []
        cur = {}

        for name, col, sub, src, ser, box, px0, dur, rng in panels:
            j = int(round(p * (len(src["frames"]) - 1)))
            cur[name] = ser[j]
            cv2.rectangle(canvas, (px0, y_pan), (px0 + PW, y_pan + PHH), CARD, -1)
            cv2.rectangle(canvas, (px0, y_pan), (px0 + 5, y_pan + PHH), col, -1)
            lab.append((px0 + 20, y_pan + 12, name, 27, INK1))
            lab.append((px0 + 20, y_pan + 50, sub, 18, INK2, False))
            lab.append((px0 + PW - 20 - txt.w(dur, 18, False), y_pan + 16,
                        dur, 18, INK2, False))
            lab.append((px0 + PW - 20 - txt.w(rng, 15, False), y_pan + 53,
                        rng, 15, INKM, False))
            canvas[y_pan + PHH:y_pan + PHH + PVH, px0:px0 + PW] = \
                video_panel(src, j, col, box, PW, PVH)

        lab += [(PAD, 20, "同一个人 · 同一面墙 · 同一个动作", 34, INK1),
                (PAD, 64, "两次尝试之间，只有一个量不同：重心离承重脚有多远",
                 21, INK2, False)]
        meta = "两段按动作进度对齐播放"
        lab.append((W - PAD - txt.w(meta, 17, False), 68, meta, 17, INKM, False))

        chart(canvas, lab, txt, PAD, y_ch, W - PAD * 2, CH, [
            ("没站起来", FAIL, mf, np.percentile(gf, 10), np.percentile(gf, 90),
             gf.min(), gf.max(), cur["没站起来"]),
            ("站起来了", OK, mo, np.percentile(go, 10), np.percentile(go, 90),
             go.min(), go.max(), cur["站起来了"]),
        ], x0b, x1b)

        lab += [(PAD, y_ft + dy, ln, sz, col, bold)
                for dy, ln, sz, col, bold in foot]
        vw.write(txt.draw(canvas, lab))
    vw.release()

    print(f"已写出 {a.out}  {W}x{H}  {n} 帧")
    print(f"  重心偏离承重脚 中位   没站起来 {mf:.2f}   站起来了 {mo:.2f}")
    print(f"  分布 p10–p90        没站起来 {np.percentile(gf,10):.2f}–"
          f"{np.percentile(gf,90):.2f}   站起来了 {np.percentile(go,10):.2f}–"
          f"{np.percentile(go,90):.2f}")
    print(f"  重叠                失败低于成功中位 {below}/{len(gf)}   "
          f"成功高于失败中位 {above}/{len(go)}")


if __name__ == "__main__":
    main()
