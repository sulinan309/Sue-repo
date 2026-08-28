"""姿态状态识别：身体朝向 × 手臂状态。

对应知识单元 TEC-POS-ORIENT-002（正身与侧身）、FAULT-SQUARE-REACH-008（正身硬够）、
FAULT-PULL-FIRST-011（用手拉代替用腿蹬）。

**边界声明**：本模块识别的是**姿态组合**，不是发力。
单目视频测不到握力、蹬力和肌肉激活，所以状态名描述的是「身体处于什么位置」，
不是「用了多少力」。「侧身未省力」的意思是「已经侧身但两臂仍屈着」，
是一个可观察的姿态事实，不是对发力效率的测量。

朝向怎么测：相机在攀爬者身后时，正对墙面（正身）的肩线与相机视轴垂直，
在图像上投影最宽；转髋侧身时肩线转向视轴方向，投影缩短。
所以 肩宽/躯干长 相对该段视频的高分位值，就是一个朝向代理。
"""
from __future__ import annotations

import dataclasses
import numpy as np

L_SHO, R_SHO, L_ELB, R_ELB, L_WRI, R_WRI = 11, 12, 13, 14, 15, 16
L_HIP, R_HIP = 23, 24

ELBOW_BENT = 160.0        # 肘角小于此值算明显弯曲
FRONTAL = 0.82            # 朝向比 ≥ 此值算正身
SIDE = 0.62               # 朝向比 ≤ 此值算侧身，之间算过渡

STATE_CN = {
    "frontal_straight": "正身支撑",
    "frontal_bent": "正身拉臂",
    "side_straight": "侧身省力",
    "side_bent": "侧身未省力",
    "transition": "转体过渡",
    "unknown": "看不准",
}
# 每个状态关联的知识单元，供反馈层检索
STATE_KB = {
    "frontal_bent": ["FAULT-SQUARE-REACH-008", "FAULT-PULL-FIRST-011"],
    "side_bent": ["TEC-POS-ORIENT-002"],
    "side_straight": ["TEC-POS-ORIENT-002", "PHY-TORQUE-003"],
    "frontal_straight": ["PRIN-LEGS-004"],
}


@dataclasses.dataclass
class Posture:
    idx: int
    ok: bool
    orient: float | None      # 朝向比：1≈正身，越小越侧
    facing: str               # frontal | side | transition | unknown
    both_bent: bool
    elbow_l: float | None
    elbow_r: float | None
    state: str
    state_cn: str


def _angle(a, b, c):
    v1, v2 = a - b, c - b
    cos = np.sum(v1 * v2, axis=-1) / (
        np.linalg.norm(v1, axis=-1) * np.linalg.norm(v2, axis=-1) + 1e-9)
    return np.degrees(np.arccos(np.clip(cos, -1, 1)))


def analyse(frames) -> list[Posture]:
    n = len(frames)
    xy = np.stack([f.xy if f.ok else np.full((33, 2), np.nan) for f in frames])
    vis = np.stack([f.vis if f.ok else np.zeros(33) for f in frames])

    torso = np.linalg.norm((xy[:, L_SHO] + xy[:, R_SHO]) / 2 -
                           (xy[:, L_HIP] + xy[:, R_HIP]) / 2, axis=1)
    sw = np.linalg.norm(xy[:, L_SHO] - xy[:, R_SHO], axis=1)
    ratio = sw / np.maximum(torso, 1e-6)

    # 用该段视频自身的高分位做归一：那是她正对墙面时的肩线投影宽度。
    # 不用固定常数，因为不同人的肩宽/躯干比本来就不同。
    ref = np.nanpercentile(ratio, 90)
    orient = ratio / max(ref, 1e-6)
    orient = np.clip(orient, 0, 1.4)
    orient = _median_smooth(orient, 9)

    eL = _angle(xy[:, L_SHO], xy[:, L_ELB], xy[:, L_WRI])
    eR = _angle(xy[:, R_SHO], xy[:, R_ELB], xy[:, R_WRI])

    out = []
    for i, f in enumerate(frames):
        if not f.ok or np.isnan(orient[i]):
            out.append(Posture(i, False, None, "unknown", False, None, None,
                               "unknown", STATE_CN["unknown"]))
            continue
        o = float(orient[i])
        facing = "frontal" if o >= FRONTAL else ("side" if o <= SIDE else "transition")
        seen = min(vis[i, L_ELB], vis[i, R_ELB], vis[i, L_WRI], vis[i, R_WRI]) > 0.3
        bent = bool(seen and eL[i] < ELBOW_BENT and eR[i] < ELBOW_BENT)

        if facing == "transition":
            st = "transition"
        else:
            st = f"{facing}_{'bent' if bent else 'straight'}"
        out.append(Posture(i, True, o, facing, bent,
                           float(eL[i]) if seen else None,
                           float(eR[i]) if seen else None,
                           st, STATE_CN[st]))
    return _hold_state(out, 7)


def _median_smooth(a, win):
    out = a.copy()
    h = win // 2
    for i in range(len(a)):
        seg = a[max(0, i - h):i + h + 1]
        seg = seg[~np.isnan(seg)]
        out[i] = np.median(seg) if len(seg) else np.nan
    return out


def _hold_state(ps: list[Posture], win: int) -> list[Posture]:
    """状态众数平滑，避免逐帧跳变。"""
    raw = [p.state for p in ps]
    h = win // 2
    for i, p in enumerate(ps):
        if not p.ok:
            continue
        seg = [s for s in raw[max(0, i - h):i + h + 1] if s != "unknown"]
        if seg:
            m = max(set(seg), key=seg.count)
            p.state, p.state_cn = m, STATE_CN[m]
    return ps


def summarise(ps: list[Posture]) -> dict:
    from collections import Counter
    ok = [p for p in ps if p.ok]
    if not ok:
        return {}
    c = Counter(p.state for p in ok)
    return {"状态占比": {STATE_CN[k]: f"{v/len(ok)*100:.0f}%"
                        for k, v in c.most_common()},
            "朝向比中位": round(float(np.median([p.orient for p in ok])), 2)}
