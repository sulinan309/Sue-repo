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
MIN_RISE = 0.18       # 重心上升达到这个幅度（躯干长倍数）算发力**成功**
                      # 判的是**稳定后的净上升**，不是峰值上升。
                      # 用峰值会把「升上去又掉回来」判成成功——实测有一次
                      # 峰值升 0.84 倍躯干长、随后回落 0.61，净收益接近零。
MIN_ATTEMPT = 0.04    # 低于这个幅度连「尝试」都算不上（下攀、原地调整）
                      #
                      # 把「尝试」和「成功」分成两道门是必要的：
                      # 只用一道 MIN_RISE，失败的发力会被直接滤掉——
                      # 而失败的发力恰恰是最该分析的。
COM_OVER_FOOT = 0.45  # 重心与承重脚的水平偏移超过这个值（躯干长倍数），
                      # 视为「重心没在脚的上方」。图像平面代理，见下方说明。


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
    success: bool             # 稳定后是否真的还在高处
    rise_ratio: float         # 峰值上升 / 躯干长
    net_ratio: float          # 稳定后的净上升 / 躯干长（判定成功用这个）
    knee_held: float          # 稳定后的膝角——蹬伸有没有被保持住
    com_over_foot: float | None   # 蹬起时重心与承重脚的水平偏移（躯干长倍数）
    foot_slip: bool           # 蹬伸过程中承重脚是否脱离接触
    fallback: float           # 蹬伸后重心回落量（躯干长倍数），正=掉回去了

    def candidates(self) -> list[tuple[str, str, str]]:
        """失败时给出候选解释，按证据强度排序。

        **不给唯一原因**——这是知识库对卡点单元的硬性要求。
        每条都附上支撑它的可观察量，以及对应的知识单元。
        """
        if self.success:
            return []
        out = []
        if self.com_over_foot is not None and self.com_over_foot > COM_OVER_FOOT:
            out.append((
                f"重心没有移到{SIDE_CN[self.leg]}脚的上方"
                f"（蹬起时水平偏移 {self.com_over_foot:.2f} 倍躯干长）",
                "蹬伸方向主要把身体推离墙面，只有很小的分量向上",
                "FAULT-ROCKOVER-STALL-010"))
        if self.chain == "hand_first":
            out.append((
                f"手先动、身体被手拉（出手比起升早 {abs(self.lead):.2f}s）",
                "身体被拉向手，重心偏离承重脚，腿失去有效发力角度",
                "FAULT-PULL-FIRST-011"))
        if self.foot_slip:
            out.append((
                "蹬伸过程中承重脚脱离接触",
                "支撑点消失，蹬伸无处着力",
                "FAULT-FOOT-SLIP-001"))
        if (self.knee_to - self.knee_from) < 30:
            out.append((
                f"蹬伸幅度有限（膝 {self.knee_from:.0f}°→{self.knee_to:.0f}°）",
                "深度屈膝时伸膝肌群力臂最短，起始阶段本就最费力",
                "TEC-MOV-ROCKOVER-002"))
        elif self.knee_held < self.knee_to - 25:
            out.append((
                f"蹬伸没有保持住（峰值 {self.knee_to:.0f}°，稳定后回到 {self.knee_held:.0f}°）",
                "腿伸了一下又收回去，重心没有被送到脚的上方",
                "TEC-MOV-ROCKOVER-002"))
        if self.fallback > 0.05:
            out.append((
                f"蹬起后重心回落 {self.fallback:.2f} 倍躯干长",
                "上升没有被新的接触点接住",
                "PRIN-STABLE-002"))
        if not out:
            out.append(("可观察量未指向明确原因", "需要侧后方视角或人工确认", None))
        return out

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


def detect(xy, com, contacts, fps: float, wall_H=None) -> list[Drive]:
    """contacts: {limb: [state per frame]}，来自 contact.analyse 的结果。

    wall_H 给了就把重心和踝点映射到墙面坐标再算位移。

    **这一步是必须的，不是优化。** 手持镜头的漂移会直接混进「重心上升」里：
    实测有一段视频相机漂移 183 像素，而检测器报的「重心上升 164 像素」
    几乎全是相机在动，人根本没上去。用图像坐标算发力位移会得出相反的结论。
    """
    import cv2
    n = len(xy)

    if wall_H is not None:
        def _w(pts):
            out_ = np.full_like(pts, np.nan, dtype=float)
            for m in range(len(pts)):
                if wall_H[m] is None or not np.isfinite(pts[m]).all():
                    continue
                q = np.array(pts[m], np.float32).reshape(1, 1, 2)
                out_[m] = cv2.perspectiveTransform(
                    q, np.linalg.inv(wall_H[m])).reshape(2)
            return out_
        com = _w(com)
        xy = xy.copy()
        for kp in (L_ANK, R_ANK, L_HIP, R_HIP, L_KNE, R_KNE, L_WRI, R_WRI, 11, 12):
            xy[:, kp] = _w(xy[:, kp])
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
            if not np.isfinite(scale) or dy < MIN_ATTEMPT * scale:
                i += 1               # 连尝试都算不上：下攀或原地调整
                continue

            rise_ratio = dy / scale

            # 重心是否在承重脚上方（图像平面代理）。
            # 严格判断需要墙面法向和重力方向，那是 P4；
            # 但在正面视角下，水平偏移量本身就是可观察事实。
            ank = R_ANK if side == "R" else L_ANK
            cof = None
            if np.isfinite(xy[i, ank, 0]) and np.isfinite(com[i, 0]):
                cof = abs(float(com[i, 0] - xy[i, ank, 0])) / scale

            foot_key = "RF" if side == "R" else "LF"
            slip = any(contacts[foot_key][m] != "contact"
                       for m in range(i, min(n, j + 1)))

            tail = min(n, j + int(0.7 * fps))
            fb = 0.0
            net = rise_ratio
            knee_held = float(k[j])
            if tail > j:
                low = float(np.nanmax(com[j:tail, 1]))     # y 越大越低
                fb = max(0.0, (low - com[j, 1]) / scale)
                # 稳定后的净上升：取 settle 窗口末段的中位高度
                end_y = float(np.nanmedian(com[max(j, tail - 5):tail, 1]))
                net = float(-(end_y - com[i, 1])) / scale
                kk = k[max(j, tail - 5):tail]
                kk = kk[np.isfinite(kk)]
                if len(kk):
                    knee_held = float(np.median(kk))
            success = net >= MIN_RISE

            last_t = i / fps
            out.append(Drive(
                side, s / fps, i / fps, j / fps, t_rise, t_hand, which,
                float(k[i]), float(k[j]),
                float(com[j, 0] - com[i, 0]), dy, lead, chain,
                success, rise_ratio, net, knee_held, cof, slip, fb))
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
    tail = ("接点稳定" if d.success else "未完成")
    note = d.chain_cn + ("" if d.success
                         else f"；峰值升 {d.rise_ratio:.2f} 倍躯干长，"
                              f"稳定后净升 {d.net_ratio:+.2f}"
                              + (f"（回落 {d.fallback:.2f}）" if d.fallback > 0.05 else ""))
    rows.append((tail, f"{d.t_ext_end:.1f}s 之后", note))
    return rows


PHASE_CN = {"load": "蓄力", "drive": "蹬起", "reach": "出手", "settle": "收尾"}


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
                "knee": (d.knee_from, d.knee_to), "rise": d.com_dy,
                "success": d.success, "rise_ratio": d.rise_ratio,
                "com_over_foot": d.com_over_foot,
                "candidates": d.candidates()}
    return None


# --- 停滞的高脚 -----------------------------------------------------------
# drive.detect() 靠「膝角屈到最深 → 快速伸展」来定位发力事件。
# 这意味着一个盲区：**失败得最彻底的那种发力，它反而看不见**——
# 高脚踩上去了、腿一直屈着、始终没能站起来，全程没有可检出的伸展峰。
#
# 这正是 FAULT-ROCKOVER-STALL-010「高脚站不起来」的典型形态，
# 所以它需要一个独立的检测器：不找伸展，找**长时间的屈膝 + 没有净上升**。

STALL_KNEE = 75.0        # 膝角低于此值算深屈
STALL_MIN_S = 1.2        # 至少持续多久才算停滞
STALL_NET = 0.15         # 窗口内净上升低于此值（躯干长倍数）算没站起来


@dataclasses.dataclass
class Stall:
    leg: str
    t0: float
    t1: float
    knee_med: float
    knee_max: float
    net_rise: float          # 躯干长倍数，正=上升
    offset_med: float        # 重心相对承重踝的水平偏移，躯干长倍数
    other_knee_med: float    # 另一条腿的膝角中位——判断有没有参与
    foot_contact_rate: float

    def candidates(self) -> list[tuple[str, str, str]]:
        out = []
        if abs(self.offset_med) > 0.30:
            out.append((
                f"重心始终没有移到{SIDE_CN[self.leg]}脚的上方"
                f"（水平偏移中位 {abs(self.offset_med):.2f} 倍躯干长）",
                "腿蹬出去的力主要把身体推离墙面，只有很小的分量向上；"
                "这一步不是力气问题，是力的方向不对",
                "FAULT-ROCKOVER-STALL-010"))
        if self.knee_max < 100:
            out.append((
                f"{SIDE_CN[self.leg]}膝全程未打开（中位 {self.knee_med:.0f}°，"
                f"峰值仅 {self.knee_max:.0f}°）",
                "深度屈膝时伸膝肌群力臂最短，起始阶段本就最费力；"
                "重心不先送过去，这个角度几乎推不动",
                "TEC-MOV-ROCKOVER-002"))
        if self.other_knee_med > 160:
            other = "L" if self.leg == "R" else "R"
            out.append((
                f"{SIDE_CN[other]}腿全程接近伸直（膝中位 {self.other_knee_med:.0f}°），未参与",
                "另一条腿既没有蹬墙配平，也没有提供第二个发力点",
                "TEC-MOV-FLAG-001"))
        if self.foot_contact_rate < 0.8:
            out.append((
                f"承重脚接触不稳（仅 {self.foot_contact_rate*100:.0f}% 的帧判为接触）",
                "支撑点本身不牢，蹬伸无处着力",
                "FAULT-FOOT-SLIP-001"))
        return out


def detect_stalls(xy, com, contacts, fps: float, wall_H=None) -> list[Stall]:
    import cv2
    n = len(xy)
    if wall_H is not None:
        def _w(pts):
            o = np.full_like(pts, np.nan, dtype=float)
            for m in range(len(pts)):
                if wall_H[m] is None or not np.isfinite(pts[m]).all():
                    continue
                q = np.array(pts[m], np.float32).reshape(1, 1, 2)
                o[m] = cv2.perspectiveTransform(q, np.linalg.inv(wall_H[m])).reshape(2)
            return o
        com = _w(com)
        xy = xy.copy()
        for kp in (L_ANK, R_ANK, L_HIP, R_HIP, L_KNE, R_KNE, 11, 12):
            xy[:, kp] = _w(xy[:, kp])

    knee = {"L": _smooth(_angle(xy[:, L_HIP], xy[:, L_KNE], xy[:, L_ANK])),
            "R": _smooth(_angle(xy[:, R_HIP], xy[:, R_KNE], xy[:, R_ANK]))}
    torso = _smooth(np.linalg.norm(
        (xy[:, 11] + xy[:, 12]) / 2 - (xy[:, L_HIP] + xy[:, R_HIP]) / 2, axis=1))
    need = int(STALL_MIN_S * fps)
    out: list[Stall] = []

    for side in ("L", "R"):
        deep = knee[side] < STALL_KNEE
        i = 0
        while i < n:
            if not deep[i]:
                i += 1
                continue
            j = i
            while j < n and deep[j]:
                j += 1
            if (j - i) >= need:
                sc = float(np.nanmedian(torso[i:j]))
                net = float(-(com[j - 1, 1] - com[i, 1])) / sc if np.isfinite(sc) else 0.0
                if net < STALL_NET:
                    ank = R_ANK if side == "R" else L_ANK
                    off = (com[i:j, 0] - xy[i:j, ank, 0]) / sc
                    fk = "RF" if side == "R" else "LF"
                    rate = float(np.mean([contacts[fk][m] == "contact"
                                          for m in range(i, j)]))
                    other = "L" if side == "R" else "R"
                    out.append(Stall(
                        side, i / fps, j / fps,
                        float(np.nanmedian(knee[side][i:j])),
                        float(np.nanmax(knee[side][i:j])),
                        net, float(np.nanmedian(off)),
                        float(np.nanmedian(knee[other][i:j])), rate))
            i = j
    out.sort(key=lambda s: s.t0)
    return out
