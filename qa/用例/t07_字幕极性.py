#!/usr/bin/env python3
"""T07 · 字幕抽取的极性：白底黑字和黑底白字都要出笔画。

annotator/README 的第五条教训：

    「字幕抽取丢了 48–64 秒 —— 按亮度取字模，白底黑字的片子抓到的是底板。」

机制是这样的：`subs.extract()` 靠**相邻字模的差异**去重，差异小于 `thr`
就丢掉。按亮度取模时，白底黑字的两句不同的话都会得到一整块白底板，
两块底板长得几乎一样 → 判成重复 → 整段字幕安静地消失。程序不报错。

`subs.text_mask()` 改用梯度（Sobel 幅值），对两种极性都成立。
本用例用合成图把这件事钉死，不需要真视频：

  1. 两种极性都必须出笔画（覆盖率显著高于空白底板）
  2. 同一句话在两种极性下的字模必须几乎相同（梯度与极性无关）
  3. 白底上两句**不同**的话，字模差异必须大于去重阈值——否则就会被丢掉
  4. 对照：把 text_mask 换成「亮＝字」的朴素实现，第 3 条立刻不成立
     （这就是当年丢掉 48–64 秒的那条路径）
  5. find_band 在两种极性下都要定位到字幕条
"""
from __future__ import annotations

import sys

import cv2
import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import qalib as Q                                            # noqa: E402

W, H = 720, 72
THR = 0.04              # subs.extract 的默认去重阈值
S1 = "PUT THE HIP OVER THE FOOT"
S2 = "DO NOT PULL WITH ARMS FIRST"


def plate(text, fg, bg, w=W, h=H):
    """一条字幕：纯色底板 + 居中一行字。文字落在中间 60%，与 text_mask 的裁切一致。"""
    img = np.full((h, w, 3), bg, np.uint8)
    if text:
        scale, th = 0.9, 2
        (tw, tht), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, th)
        cv2.putText(img, text, ((w - tw) // 2, (h + tht) // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, scale, fg, th, cv2.LINE_AA)
    return img


def naive_bright_mask(crop):
    """当年那条错的路径：按亮度取字模（亮＝字）。留作对照，不是被测代码。"""
    g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY).astype(np.float32)
    w = g.shape[1]
    g = g[:, int(w * 0.2):int(w * 0.8)]
    return cv2.resize((g > 200).astype(np.float32), (200, 32))


def diff(a, b):
    return float(np.abs(a - b).mean())


def run():
    sys.path.insert(0, str(Q.KB))
    from tools import subs

    r = Q.Runner("T07 字幕极性")

    dark = plate(S1, fg=(255, 255, 255), bg=(18, 18, 18))     # 黑底白字
    light = plate(S1, fg=(20, 20, 20), bg=(240, 240, 240))    # 白底黑字
    dark2 = plate(S2, fg=(255, 255, 255), bg=(18, 18, 18))
    light2 = plate(S2, fg=(20, 20, 20), bg=(240, 240, 240))
    blank_d = plate("", fg=(255, 255, 255), bg=(18, 18, 18))
    blank_l = plate("", fg=(20, 20, 20), bg=(240, 240, 240))

    m_d, m_l = subs.text_mask(dark), subs.text_mask(light)
    m_d2, m_l2 = subs.text_mask(dark2), subs.text_mask(light2)
    m_bd, m_bl = subs.text_mask(blank_d), subs.text_mask(blank_l)

    c = r.case("两种极性都出笔画")
    r.check(m_d.mean() > 0.02, f"黑底白字覆盖率 {m_d.mean():.3f}",
            round(float(m_d.mean()), 3), "> 0.02")
    r.check(m_l.mean() > 0.02, f"白底黑字覆盖率 {m_l.mean():.3f}",
            round(float(m_l.mean()), 3), "> 0.02")
    r.check(m_bd.mean() < 0.005, f"空白黑底板覆盖率 {m_bd.mean():.3f}",
            round(float(m_bd.mean()), 3), "< 0.005")
    r.check(m_bl.mean() < 0.005, f"空白白底板覆盖率 {m_bl.mean():.3f}",
            round(float(m_bl.mean()), 3), "< 0.005")
    r.check(m_l.mean() > 8 * max(m_bl.mean(), 1e-6),
            "白底黑字的笔画量远高于空白底板（不是抓到了底板）",
            (round(float(m_l.mean()), 4), round(float(m_bl.mean()), 4)),
            "前者 >> 后者")

    c = r.case("同一句话，两种极性给出几乎相同的字模")
    r.check(diff(m_d, m_l) < THR,
            f"黑底白字 vs 白底黑字 字模差 {diff(m_d, m_l):.4f}",
            round(diff(m_d, m_l), 4), f"< {THR}")

    c = r.case("不同的两句话必须区分得开（否则会被 extract 当重复丢掉）")
    for name, a, b in (("白底黑字", m_l, m_l2), ("黑底白字", m_d, m_d2)):
        d = diff(a, b)
        r.check(d > THR, f"{name}：两句不同的话字模差 {d:.4f}",
                round(d, 4), f"> {THR}（去重阈值）")
    r.check(diff(m_l, subs.text_mask(plate(S1, (20, 20, 20), (240, 240, 240))))
            <= THR, "同一句话重复出现时仍判为重复（去重没被破坏）",
            round(diff(m_l, subs.text_mask(light)), 4), f"<= {THR}")

    c = r.case("对照 · 朴素「亮＝字」实现在白底上量的是底板不是笔画")
    n_l, n_d = naive_bright_mask(light), naive_bright_mask(dark)
    r.check(abs(m_l.mean() - m_d.mean()) < 0.005,
            f"梯度字模与极性无关：黑底 {m_d.mean():.4f} vs 白底 {m_l.mean():.4f}",
            (round(float(m_d.mean()), 4), round(float(m_l.mean()), 4)),
            "两者几乎相等")
    r.check(n_l.mean() > 5 * n_d.mean(),
            f"朴素字模严重依赖极性：黑底 {n_d.mean():.4f} vs 白底 {n_l.mean():.4f}",
            (round(float(n_d.mean()), 4), round(float(n_l.mean()), 4)),
            "白底覆盖率高出 5 倍以上")
    r.check(n_l.mean() > 0.8,
            f"白底上朴素字模覆盖率 {n_l.mean():.3f}——抓到的是整块底板",
            round(float(n_l.mean()), 3), "> 0.8")

    c = r.case("对照 · 低对比度白底：朴素实现直接塌成常量，梯度仍分得开")
    # 笔画和底板都在亮度阈值同一侧（205 与 250 都 > 200），
    # 朴素字模变成全 1，任何两句话都完全相同 → extract 会把它们全当重复丢掉。
    lc1 = plate(S1, fg=(205, 205, 205), bg=(250, 250, 250))
    lc2 = plate(S2, fg=(205, 205, 205), bg=(250, 250, 250))
    nb1, nb2 = naive_bright_mask(lc1), naive_bright_mask(lc2)
    g1, g2 = subs.text_mask(lc1), subs.text_mask(lc2)
    r.eq(float(nb1.mean()), 1.0, "朴素字模全为 1（整块底板）")
    r.eq(diff(nb1, nb2), 0.0, "朴素字模下两句不同的话完全相同 → 必被丢掉")
    r.check(g1.mean() > 0.02, f"梯度字模仍有笔画（覆盖率 {g1.mean():.4f}）",
            round(float(g1.mean()), 4), "> 0.02")
    r.check(diff(g1, g2) > THR,
            f"梯度字模下两句的差 {diff(g1, g2):.4f} 仍大于去重阈值",
            round(diff(g1, g2), 4), f"> {THR}")

    c = r.case("端到端 · extract 在白底片子上不丢句子")
    # 造一段每秒换一句的视频：360 高的画面，底部 56px 是字幕条。
    fps = 30.0
    texts = [S1, S2, "KEEP THE HEEL DOWN", "TRUST THE FOOT"]
    FH, Y0, Y1 = 360, 300, 356

    def clip(fg, bg):
        out = []
        for k, t in enumerate(texts):
            band = plate(t, fg=fg, bg=bg, h=Y1 - Y0)
            for j in range(int(fps)):
                f = np.full((FH, W, 3), (40 + k * 7, 60, 80), np.uint8)
                f[Y0:Y1] = band
                out.append(f)
        return out

    for name, fg, bg in (("白底黑字", (20, 20, 20), (240, 240, 240)),
                         ("黑底白字", (255, 255, 255), (18, 18, 18)),
                         ("低对比度白底", (205, 205, 205), (250, 250, 250))):
        frames = clip(fg, bg)
        keep = subs.extract(frames, fps, Y0 / FH, Y1 / FH, step=0.25, thr=THR)
        r.eq(len(keep), len(texts), f"{name}：{len(texts)} 句抽出 {len(texts)} 条")

    frames = clip((205, 205, 205), (250, 250, 250))
    real = subs.text_mask
    try:
        subs.text_mask = naive_bright_mask
        keep_bad = subs.extract(frames, fps, Y0 / FH, Y1 / FH, step=0.25, thr=THR)
    finally:
        subs.text_mask = real
    r.eq(len(keep_bad), 1,
         "对照：换成朴素字模，同一段素材 4 句塌成 1 条"
         "（这就是「丢了 48–64 秒」的形状）")

    c = r.case("find_band 在两种极性下定位到同一条字幕条")
    got = {}
    for name, fg, bg in (("黑底白字", (255, 255, 255), (18, 18, 18)),
                         ("白底黑字", (20, 20, 20), (240, 240, 240))):
        FH2 = 400
        frames = []
        for k in range(30):
            f = np.full((FH2, W, 3), (60 + k, 70, 90), np.uint8)
            f[320:376] = plate(S1 if k % 2 else S2, fg, bg, h=56)
            frames.append(f)
        y0, y1 = subs.find_band(frames)
        got[name] = (round(y0, 3), round(y1, 3))
        lo, hi = 320 / FH2, 376 / FH2
        # find_band 找的是**笔画行**，不是整块底板，所以只要求落在底板范围内。
        r.check(lo - 0.02 <= y0 < y1 <= hi + 0.02,
                f"{name}：字幕条 {y0:.3f}–{y1:.3f} 落在底板 {lo:.3f}–{hi:.3f} 内",
                (round(y0, 3), round(y1, 3)), f"⊆ {lo:.3f}–{hi:.3f}")
        r.check(y1 - y0 > 0.02, f"{name}：字幕条非退化（高度 {y1 - y0:.3f}）",
                round(y1 - y0, 3), "> 0.02")
    r.eq(got["黑底白字"], got["白底黑字"],
         "两种极性给出同一条字幕条（极性不影响定位）")
    return r.report()


if __name__ == "__main__":
    Q.main_guard(run)
