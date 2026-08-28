#!/usr/bin/env python3
"""把视频里烧进画面的字幕抠成可读的联系表。

    python3 tools/subs.py 视频.mp4 -o 输出目录          # 自动找字幕条
    python3 tools/subs.py 视频.mp4 --band 0.75:0.88     # 手动指定
    python3 tools/subs.py 视频.mp4 --probe              # 只导几张整帧，人工看位置

为什么需要它：教学视频的内容主要在口播里，但本环境没有 ffmpeg / whisper，
音轨转不了。好在这类视频几乎都带烧录字幕——把字幕条按时间抠出来去重，
就能拿到一份接近逐字稿的东西。

**这不是转录，是抄字幕。** 字幕本身通常是创作者用自动识别生成的，会有错
（实测某条视频把「脚点」识别成「眼点」）。引用时必须标明来源是字幕而非音轨，
并把发现的错误记在 sources/ 里。

字幕条的自动定位靠三个特征：亮（白字）、边缘密（笔画多）、横向居中。
逐行算这三项的乘积再沿时间取分位数，取最宽的连续高分区间。
判错了就用 --band 手动指定，别跟它较劲。
"""
from __future__ import annotations

import argparse
import pathlib

import cv2
import numpy as np


def read_frames(path, stride=1):
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    out, i = [], 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if i % stride == 0:
            out.append(f)
        i += 1
    cap.release()
    return out, fps


def find_band(frames, sample=60):
    """逐行打分找字幕条：亮 × 边缘密 × 横向居中。"""
    idx = np.linspace(0, len(frames) - 1, min(sample, len(frames))).astype(int)
    h, w = frames[0].shape[:2]
    lo, hi = int(w * 0.2), int(w * 0.8)          # 只看中间 60%，避开两侧 UI
    prof = []
    for i in idx:
        g = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY).astype(np.float32)
        gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
        # 笔画密度：黑底白字和白底黑字都算数，不看亮度只看梯度
        prof.append((cv2.magnitude(gx, gy)[:, lo:hi] > 120).mean(axis=1))
    p = np.percentile(np.array(prof), 75, axis=0)   # 沿时间取高分位：字幕不是每帧都有
    p = np.convolve(p, np.ones(9) / 9, mode="same")
    if p.max() <= 0:
        return 0.85, 1.0
    thr = p.max() * 0.45
    runs, s = [], None
    for y in range(h):
        if p[y] >= thr and s is None:
            s = y
        elif p[y] < thr and s is not None:
            runs.append((s, y))
            s = None
    if s is not None:
        runs.append((s, h))
    if not runs:
        return 0.85, 1.0
    a, b = max(runs, key=lambda r: r[1] - r[0])
    pad = int(h * 0.012)
    return max(0, a - pad) / h, min(h, b + pad) / h


def text_mask(crop):
    """提取笔画。背景在动而字没变时，原始像素差会很大，笔画图不会——
    去重必须比字，不能比画面。

    用**梯度**而不是亮度：白底黑字的字幕同样常见（实测某条视频就是），
    按「亮 = 字」去做，抓到的是那块白色底板而不是笔画，底板形状相近的
    两句话会被误判成同一句，然后整段字幕安静地消失。梯度对黑底白字和
    白底黑字都成立。

    横向只取中间 60%：字幕居中，两侧是会动的画面。
    """
    g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY).astype(np.float32)
    w = g.shape[1]
    g = g[:, int(w * 0.2):int(w * 0.8)]
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    m = (cv2.magnitude(gx, gy) > 120).astype(np.float32)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.float32))
    return cv2.resize(m, (200, 32))


def extract(frames, fps, y0f, y1f, step=0.25, thr=0.04):
    """按时间抽样，相邻字模近似重复的丢掉。"""
    h = frames[0].shape[0]
    y0, y1 = int(y0f * h), int(y1f * h)
    keep, prev = [], None
    for i in range(0, len(frames), max(1, int(step * fps))):
        crop = frames[i][y0:y1]
        if crop.size == 0:
            continue
        m = text_mask(crop)
        if prev is None or np.abs(m - prev).mean() > thr:
            keep.append((i / fps, crop))
            prev = m
    return keep


def sheets(keep, outdir, tag, per=14):
    outdir.mkdir(parents=True, exist_ok=True)
    n = 0
    for s in range(0, len(keep), per):
        grp = keep[s:s + per]
        w = max(c.shape[1] for _, c in grp)
        rows = []
        for t, c in grp:
            pad = np.full((c.shape[0], w, 3), 20, np.uint8)
            pad[:, :c.shape[1]] = c
            cv2.putText(pad, f"{t:.0f}s", (6, 26), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 255, 255), 2)
            rows.append(pad)
            rows.append(np.full((3, w, 3), 90, np.uint8))
        cv2.imwrite(str(outdir / f"{tag}_{n:02d}.png"), np.vstack(rows))
        n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description="抠出烧录字幕，生成可读联系表")
    ap.add_argument("video")
    ap.add_argument("-o", "--out", default="subs_out")
    ap.add_argument("--band", help="手动指定字幕条，形如 0.75:0.88（画面高度的比例）")
    ap.add_argument("--probe", action="store_true", help="只导 4 张整帧供人工看位置")
    ap.add_argument("--step", type=float, default=0.25, help="抽样间隔（秒）")
    ap.add_argument("--thr", type=float, default=0.04,
                    help="去重阈值（字模差异比例），越大留得越少")
    ap.add_argument("--per", type=int, default=14, help="每张联系表放几条")
    a = ap.parse_args()

    path = pathlib.Path(a.video)
    frames, fps = read_frames(path)
    outdir = pathlib.Path(a.out)
    tag = path.stem[:8]
    print(f"{path.name}  {len(frames)} 帧  {fps:.1f}fps  {len(frames)/fps:.0f}s "
          f" {frames[0].shape[1]}x{frames[0].shape[0]}")

    if a.probe:
        outdir.mkdir(parents=True, exist_ok=True)
        for k, p in enumerate((0.1, 0.35, 0.6, 0.85)):
            cv2.imwrite(str(outdir / f"{tag}_probe{k}.png"),
                        frames[int(p * (len(frames) - 1))])
        print(f"  已导 4 张整帧到 {outdir}")
        return

    if a.band:
        y0f, y1f = (float(x) for x in a.band.split(":"))
        how = "手动"
    else:
        y0f, y1f = find_band(frames)
        how = "自动"
    print(f"  字幕条（{how}）：画面高度的 {y0f:.3f}–{y1f:.3f}")

    keep = extract(frames, fps, y0f, y1f, a.step, a.thr)
    n = sheets(keep, outdir, tag, a.per)
    print(f"  去重后 {len(keep)} 条 -> {n} 张联系表，在 {outdir}")
    print("  注意：这是抄字幕不是转录音轨，字幕本身可能有识别错误")


if __name__ == "__main__":
    main()
