"""发力事件检测：把「正身发力」从静态姿态还原成有时序的动作。

这个模块修正了一个概念错误。

posture.py 做的是**逐帧姿态分类**（此刻是正身还是侧身、直臂还是屈臂）。
但攀岩里说的「正身发力」不是一个姿态，是一个**有先后顺序的事件**：

    蓄力 → 蹬起 → 出手 → 接点稳定

而且它的质量几乎完全由**顺序**决定，不由姿态决定。
知识库 PHY-KCHAIN-006 写得很清楚：

    正确顺序：重心先移到高脚正上方 → 腿蹬伸 → 手在末端维持平衡
    常见错误：先用手往上拉 → 身体被拉向手 → 重心偏离高脚
    两种顺序用的肌肉一样多，结果完全不同。

所以这里测的核心量只有一个：

    **手离开原岩点的时刻，减去身体开始上升的时刻。**

    为正 → 腿先蹬、身体先升、手借着上升的窗口出手（动作链完整）
    为负 → 手先动、身体被手拉上去（动作链断裂，见 FAULT-PULL-FIRST-011）

同样是「重心上升 50 像素」，这个差值决定了它是腿做的功还是手做的功。
这一点从单目视频完全可测，不需要墙体坐标系。
"""
from __future__ import annotations

import dataclasses
import numpy as np

L_HIP, R_HIP, L_KNE, R_KNE, L_ANK, R_ANK = 23, 24, 25, 26, 27, 28
L_WRI, R_WRI = 15, 16
SIDE_CN = {"L": "左", "R": "右"}

EXT_MIN = 22.0        # 一次蹬伸至少要伸展多少度才算发力事件
EXT_WIN = 0.90        # 蹬伸必须在多少秒内完成
RISE_V = 12.0         # 重心上升速度阈值（像素/秒，按躯干长归一后再判）
MIN_GAP = 0.8         # 同一条腿的两次发力至少间隔多少秒
MIN_RISE = 0.18       # 重心至少要上升多少（躯干长的倍数）才算一次发力
                      # 没有这一条，下攀和原地调整时的膝伸展也会被当成发力


@dataclasses.dataclass
class Drive:
    leg: str                  # L | R
    t_load: float             # 蓄力开始
    t_drive: float            # 蹬起开始（膝角最小点）
    t_ext_end: float          # 蹬伸结束
    t_rise: float | None      # 重心开始上升
    t_hand: float | None      # 手离开原岩点
    hand: str | None          # LH | RH
    knee_from: float
    knee_to: float
    com_dx: float
    com_dy: float             # 正值 = 上升
    lead: float | None        # t_hand - t_rise，正=腿先蹬手后出
    chain: str                # leg_first | hand_first | unclear

    @property
    def chain_cn(self):
        return {"leg_first": "腿先蹬·动作链完整",
                "hand_first": "手先出·动作链断裂",
                "unclear": "时序看不准"}[self.chain]


def _angle(a, b, c):
    v1, v2 = a - b, c - b
    cos = np.sum(v1 * v2, axis=-1) / (
        np.linalg.norm(v1, axis=-1) * np.linalg.norm(v2, axis=-1) + 1e-9)
    return np.degrees(np.arccos(np.clip(cos, -1, 1)))


def _smooth(a, win=7):
    out = a.copy()
    h = win // 2
    for i in range(len(a)):
        seg = a[max(0, i - h):i + h + 1]
        seg = seg[~np.isnan(seg)]
        out[i] = np.median(seg) if len(seg) else np.nan
    return out


def detect(xy, com, contacts, fps: float) -> list[Drive]:
    """contacts: {limb: [state per frame]}，来自 contact.analyse 的结果。"""
    n = len(xy)
    knee = {"L": _smooth(_angle(xy[:, L_HIP], xy[:, L_KNE], xy[:, L_ANK])),
            "R": _smooth(_angle(xy[:, R_HIP], xy[:, R_KNE], xy[:, R_ANK]))}
    torso = _smooth(np.linalg.norm(
        (xy[:, 11] + xy[:, 12]) / 2 - (xy[:, L_HIP] + xy[:, R_HIP]) / 2, axis=1))
    comy = _smooth(com[:, 1])
    # 归一化的重心上升速度（躯干长/秒，向上为正）
    vy = np.full(n, np.nan)
    vy[1:] = -(comy[1:] - comy[:-1]) / np.maximum(torso[1:], 1e-6) * fps
    vy = _smooth(vy, 9)

    W = int(EXT_WIN * fps)
    out: list[Drive] = []

    for side in ("L", "R"):
        k = knee[side]
        last_t = -1e9            # 每条腿单独去重，不跨腿比较
        i = 1
        while i < n - W:
            # 找局部极小（屈到最深）
            if not (np.isfinite(k[i]) and k[i] <= k[i - 1] and k[i] <= k[i + 1]):
                i += 1
                continue
            seg = k[i:i + W]
            if not np.any(np.isfinite(seg)):
                i += 1
                continue
            j = i + int(np.nanargmax(seg))
            if not np.isfinite(k[j]) or (k[j] - k[i]) < EXT_MIN:
                i += 1
                continue
            if (i / fps - last_t) < MIN_GAP:
                i += 1
                continue

            # 蓄力起点：从极小点往回找膝角开始下降的位置
            s = i
            while s > 0 and np.isfinite(k[s - 1]) and k[s - 1] >= k[s]:
                s -= 1
                if (i - s) / fps > 1.5:
                    break

            # 重心开始上升的时刻
            t_rise = None
            for m in range(i, min(n, j + 3)):
                if np.isfinite(vy[m]) and vy[m] > RISE_V / 100:
                    t_rise = m / fps
                    break

            # 哪只手在出手：按**实际位移**判，不看接触状态。
            # 接触状态会因为关键点抖动出现假的 moving——实测中左手全程只动了
            # 4 像素却被标成 moving，而真正出手的右手移动了 157 像素。
            # 位移是更硬的证据。
            end = min(n, j + int(0.8 * fps))
            t_hand, which = None, None
            best = 0.0
            for H, wi in (("RH", R_WRI), ("LH", L_WRI)):
                seg = xy[i:end, wi]
                if not np.isfinite(seg).all():
                    continue
                disp = np.linalg.norm(seg - seg[0], axis=1)
                if disp.max() > best:
                    best, which = disp.max(), H
            scale_h = float(np.nanmedian(torso[i:end])) if end > i else np.nan
            if which and np.isfinite(scale_h) and best > 0.45 * scale_h:
                wi = R_WRI if which == "RH" else L_WRI
                seg = xy[i:end, wi]
                disp = np.linalg.norm(seg - seg[0], axis=1)
                cross = np.argmax(disp > 0.12 * scale_h)   # 位移开始超过阈值的帧
                t_hand = (i + int(cross)) / fps
            else:
                which = None

            lead = (t_hand - t_rise) if (t_hand is not None and t_rise is not None) else None
            chain = ("unclear" if lead is None else
                     "leg_first" if lead >= -0.03 else "hand_first")

            dy = float(-(com[j, 1] - com[i, 1]))
            scale = float(np.nanmedian(torso[i:j + 1])) if j > i else np.nan
            if not np.isfinite(scale) or dy < MIN_RISE * scale:
                i += 1               # 膝伸了但身体没上去，不是发力
                continue

            last_t = i / fps
            out.append(Drive(
                side, s / fps, i / fps, j / fps, t_rise, t_hand, which,
                float(k[i]), float(k[j]),
                float(com[j, 0] - com[i, 0]), dy, lead, chain))
            i = j + 1

    out.sort(key=lambda d: d.t_drive)
    # 合并两腿在同一时刻的重复检出，保留伸展更大的那条
    merged: list[Drive] = []
    for d in out:
        if merged and abs(d.t_drive - merged[-1].t_drive) < MIN_GAP:
            if (d.knee_to - d.knee_from) > (merged[-1].knee_to - merged[-1].knee_from):
                merged[-1] = d
        else:
            merged.append(d)
    return merged


def describe(d: Drive) -> list[tuple[str, str, str]]:
    """按知识库的三阶段模型给出可读的时序表。"""
    rows = [
        ("蓄力", f"{d.t_load:.1f}–{d.t_drive:.1f}s",
         f"{SIDE_CN[d.leg]}膝屈至 {d.knee_from:.0f}°，在{SIDE_CN[d.leg]}腿上建立发力空间"),
        ("蹬起", f"{d.t_drive:.1f}–{d.t_ext_end:.1f}s",
         f"{SIDE_CN[d.leg]}膝 {d.knee_from:.0f}°→{d.knee_to:.0f}°，"
         f"重心上升 {d.com_dy:.0f}px、横移 {d.com_dx:+.0f}px"),
    ]
    if d.t_hand is not None:
        rows.append(("出手", f"{d.t_hand:.1f}s",
                     f"{'右手' if d.hand=='RH' else '左手'}离开原岩点"
                     + (f"，比重心起升晚 {d.lead:+.2f}s" if d.lead is not None else "")))
    rows.append(("接点稳定", f"{d.t_ext_end:.1f}s 之后", d.chain_cn))
    return rows


PHASE_CN = {"load": "蓄力", "drive": "蹬起", "reach": "出手", "settle": "接点稳定"}


def phase_at(drives: list[Drive], t: float, tail: float = 0.8):
    """当前时刻处于哪次发力的哪个阶段。不在任何发力事件内则返回 None。"""
    for k, d in enumerate(drives, 1):
        if not (d.t_load - 0.05 <= t <= d.t_ext_end + tail):
            continue
        if t < d.t_drive:
            ph = "load"
        elif d.t_hand is not None and t >= d.t_hand:
            ph = "reach" if t <= d.t_ext_end else "settle"
        elif t <= d.t_ext_end:
            ph = "drive"
        else:
            ph = "settle"
        return {"n": k, "total": len(drives), "leg": SIDE_CN[d.leg],
                "phase": ph, "phase_cn": PHASE_CN[ph], "chain": d.chain,
                "chain_cn": d.chain_cn, "lead": d.lead,
                "knee": (d.knee_from, d.knee_to), "rise": d.com_dy}
    return None
