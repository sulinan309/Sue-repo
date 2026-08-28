"""接触代理与动作阶段判定。

对应 docs/03-感知层架构.md 的 P3 档（双流融合）。

这一层是姿态流与视觉流交汇的地方：姿态给出四个肢端在哪里，
视觉给出岩点在哪里，两者结合才能回答「手到底在哪个岩点上」。

**边界声明**（贯穿全模块）：
所有接触状态都是**二维视觉邻近代理**，不是力学接触。
我们无法从单目视频测量握力、蹬力或各接触点的负荷分配。
「confirmed」只表示「肢端与岩点在图像上足够近且足够稳」，
不表示「这只手在承重」。渲染层必须把这条边界一起显示出来。
"""
from __future__ import annotations

import dataclasses
import numpy as np

from .pose import Frame, LIMB_POINTS, L_SHO, R_SHO, L_HIP, R_HIP

LIMBS = ["LH", "RH", "LF", "RF"]
LIMB_CN = {"LH": "左手", "RH": "右手", "LF": "左脚", "RF": "右脚"}

# 阈值以「躯干长度」为单位，避免因人远近而失效。
# 距离量的是**肢端到岩点边缘**而不是到质心——大体积块的质心可能离
# 实际接触位置很远，用质心距离会把真实接触判成未接触。
NEAR_CONFIRM = 0.16      # 肢端到岩点边缘 < 此值 → 可能确认
NEAR_POSSIBLE = 0.34     # < 此值 → 可能接触
STILL_LIMB = 0.55        # 肢端速度（躯干长/秒）低于此值算静止
STILL_COM = 0.35         # 质心速度低于此值算整体静止


@dataclasses.dataclass
class Contact:
    limb: str
    hold: str | None
    state: str            # confirmed | possible | none
    dist: float | None    # 归一化距离
    speed: float          # 归一化速度


@dataclasses.dataclass
class Evidence:
    """一帧的判定结果。字段命名刻意区分『观察』与『代理』。"""
    idx: int
    t: float
    ok: bool
    contacts: list[Contact]
    confirmed: int
    possible: int
    stage: str
    kinematic_still: bool
    layout: str           # toward_left | toward_right | centered
    com_speed: float
    moving_limbs: list[str]
    note: str = "2D 接触代理｜未测量力与负荷分配"

    def as_dict(self):
        d = dataclasses.asdict(self)
        d["evidence_level"] = "可确认事实" if self.ok else "证据不足"
        d["not_measured"] = ["接触力", "负荷分配", "摩擦系数",
                             "重心的三维位置", "髋部到墙面的度量距离"]
        return d


def _torso(f: Frame) -> float | None:
    if not f.ok:
        return None
    if min(f.vis[L_SHO], f.vis[R_SHO], f.vis[L_HIP], f.vis[R_HIP]) < 0.3:
        return None
    sho = (f.xy[L_SHO] + f.xy[R_SHO]) / 2
    hip = (f.xy[L_HIP] + f.xy[R_HIP]) / 2
    d = float(np.linalg.norm(sho - hip))
    return d if d > 8 else None


def analyse(frames: list[Frame], hold_xy_per_frame: list[dict[str, tuple[float, float]]],
            fps: float, hold_r: dict[str, float] | None = None) -> list[Evidence]:
    """逐帧判定接触与阶段。

    hold_xy_per_frame[i] 是该帧各岩点的图像坐标；
    hold_r 是各岩点半径，用于把距离从「到质心」换算成「到边缘」。
    """
    hold_r = hold_r or {}
    out: list[Evidence] = []
    prev_pts: dict[str, np.ndarray] = {}
    prev_com: np.ndarray | None = None

    for i, f in enumerate(frames):
        scale = _torso(f)
        if not f.ok or scale is None:
            out.append(Evidence(i, f.t, False, [], 0, 0, "no_pose", False,
                                "unknown", 0.0, []))
            prev_pts, prev_com = {}, None
            continue

        holds = hold_xy_per_frame[i]
        contacts, moving = [], []
        cur_pts = {}

        for limb in LIMBS:
            p = f.pt(LIMB_POINTS[limb])
            if p is None:
                contacts.append(Contact(limb, None, "none", None, 0.0))
                continue
            pa = np.array(p)
            cur_pts[limb] = pa
            speed = 0.0
            if limb in prev_pts:
                speed = float(np.linalg.norm(pa - prev_pts[limb])) / scale * fps
            if speed > STILL_LIMB:
                moving.append(limb)

            best, bd = None, 1e9
            for hid, hp in holds.items():
                raw = float(np.linalg.norm(pa - np.array(hp)))
                edge = max(0.0, raw - hold_r.get(hid, 0.0)) / scale
                if edge < bd:
                    best, bd = hid, edge

            if best is None:
                contacts.append(Contact(limb, None, "none", None, speed))
            elif bd < NEAR_CONFIRM and speed <= STILL_LIMB:
                contacts.append(Contact(limb, best, "confirmed", bd, speed))
            elif bd < NEAR_POSSIBLE:
                contacts.append(Contact(limb, best, "possible", bd, speed))
            else:
                contacts.append(Contact(limb, None, "none", bd, speed))

        com_speed = 0.0
        if f.com is not None:
            ca = np.array(f.com)
            if prev_com is not None:
                com_speed = float(np.linalg.norm(ca - prev_com)) / scale * fps
            prev_com = ca

        n_conf = sum(c.state == "confirmed" for c in contacts)
        n_poss = sum(c.state in ("confirmed", "possible") for c in contacts)
        still = com_speed <= STILL_COM and not moving

        if n_poss < 2:
            stage = "low_contact_count"
        elif still and n_conf >= 3:
            stage = "contact_stabilization"
        elif len(moving) == 1:
            stage = "limb_transport"
        elif len(moving) >= 2:
            stage = "multi_limb_transition"
        else:
            stage = "contact_stabilization" if n_conf >= 3 else "transition"

        # 「视觉布局」而不是「平衡」——它只描述图像上质心相对接触点的偏向，
        # 不构成对稳定性的力学判断
        layout = "unknown"
        anchors = [np.array(holds[c.hold]) for c in contacts
                   if c.hold and c.state in ("confirmed", "possible")]
        if anchors and f.com is not None:
            cx = float(np.mean([a[0] for a in anchors]))
            off = (f.com[0] - cx) / scale
            layout = ("toward_right" if off > 0.25 else
                      "toward_left" if off < -0.25 else "centered")

        out.append(Evidence(i, f.t, True, contacts, n_conf, n_poss, stage,
                            still, layout, com_speed, moving))
        prev_pts = cur_pts
    return out


def stabilise(ev: list[Evidence], win: int = 5) -> list[Evidence]:
    """对阶段标签做众数平滑，避免逐帧跳变造成的闪烁。"""
    stages = [e.stage for e in ev]
    half = win // 2
    for i, e in enumerate(ev):
        if not e.ok:
            continue
        seg = [s for s in stages[max(0, i - half):i + half + 1] if s != "no_pose"]
        if seg:
            e.stage = max(set(seg), key=seg.count)
    return ev


def summarise(ev: list[Evidence]) -> dict:
    ok = [e for e in ev if e.ok]
    if not ok:
        return {"frames": len(ev), "pose_rate": 0.0}
    from collections import Counter
    st = Counter(e.stage for e in ok)
    return {
        "frames": len(ev),
        "pose_rate": round(len(ok) / len(ev), 3),
        "mean_confirmed": round(float(np.mean([e.confirmed for e in ok])), 2),
        "stage_frames": dict(st),
        "still_rate": round(sum(e.kinematic_still for e in ok) / len(ok), 3),
    }
