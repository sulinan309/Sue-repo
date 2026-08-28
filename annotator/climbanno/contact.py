"""接触代理与动作阶段判定。

对应 docs/03-感知层架构.md 的 P3 档（双流融合）。

**边界声明**（贯穿全模块）：
所有接触状态都是**视觉运动学代理**，不是力学接触。
我们无法从单目视频测量握力、蹬力或各接触点的负荷分配。
「接触」只表示「该肢端在墙面坐标里静止了足够久」，
不表示「这只手在承重」。渲染层必须把这条边界一起显示出来。

两点设计取舍：

1. **速度在墙面坐标里算，不在图像坐标里算。**
   手持镜头会让静止的肢体在图像上也有速度。用单应把肢端映射回
   参考帧坐标之后，相机运动被消掉，静止判定才可靠。

2. **接触主要由「墙面坐标里的静止」判定，岩点关联是附加信息。**
   岩点检测会漏（白色岩点、与墙同色的岩点），如果把「找得到岩点」
   当成接触的必要条件，漏检就会变成漏判接触。
   反过来，肢端在墙面上静止不动，本身就是接触的证据——
   哪怕我们没认出它踩的是哪个点。
"""
from __future__ import annotations

import dataclasses
import numpy as np

from .pose import Frame, LIMB_POINTS, L_SHO, R_SHO, L_HIP, R_HIP

LIMBS = ["LH", "RH", "LF", "RF"]
LIMB_CN = {"LH": "左手", "RH": "右手", "LF": "左脚", "RF": "右脚"}

# 阈值以「躯干长度」为单位，避免因人远近而失效
STILL_LIMB = 0.55       # 平滑后的肢端速度（躯干长/秒）低于此值 → 进入接触
MOVING_LIMB = 1.10      # 高于此值 → 退出接触（迟滞，防止阈值附近闪烁）
STILL_HIP = 0.35        # 髋部速度低于此值算轨迹稳定
HOLD_NEAR = 0.30        # 肢端到岩点边缘 < 此值则关联该岩点
SPEED_WIN = 5           # 速度滑动中值窗口

# 为什么要平滑：单帧速度受关键点抖动影响很大，尤其人在画面里较小时。
# 第一版直接用单帧速度并要求「连续 N 帧低于阈值」，结果速度在阈值附近
# 反复穿越，连续计数不断被打断——61% 的帧速度达标，判出的接触却只有 1.04/4。
# 改成先做滑动中值再判定，并用进入/退出两个阈值做迟滞。


@dataclasses.dataclass
class Contact:
    limb: str
    state: str            # contact | moving | uncertain
    hold: str | None      # 关联到的岩点，可能为 None（岩点没检出也不影响接触判定）
    speed: float          # 墙面坐标下的归一化速度
    dist: float | None    # 到岩点边缘的归一化距离


@dataclasses.dataclass
class Evidence:
    idx: int
    t: float
    ok: bool
    contacts: list[Contact]
    n_contact: int
    stage: str
    headline: str
    hip_stable: bool
    hip_speed: float
    moving_limbs: list[str]
    support: list[tuple[float, float]]     # 支撑面顶点（图像坐标）
    com_in_support: bool | None            # 二维投影代理，不是力学判断

    def as_dict(self):
        d = dataclasses.asdict(self)
        d["evidence_level"] = "可确认事实" if self.ok else "证据不足"
        d["proxy_note"] = ("接触与重心来自单目视频视觉推断；"
                           "com_in_support 是二维投影代理，不构成力学稳定性判断")
        d["not_measured"] = ["接触力", "负荷分配", "摩擦系数",
                             "重心的三维位置", "髋部到墙面的度量距离"]
        return d


def _torso(f: Frame) -> float | None:
    if not f.ok:
        return None
    if min(f.vis[L_SHO], f.vis[R_SHO], f.vis[L_HIP], f.vis[R_HIP]) < 0.3:
        return None
    d = float(np.linalg.norm((f.xy[L_SHO] + f.xy[R_SHO]) / 2 -
                             (f.xy[L_HIP] + f.xy[R_HIP]) / 2))
    return d if d > 8 else None


def _in_poly(pt, poly) -> bool:
    if len(poly) < 3:
        return False
    import cv2
    return cv2.pointPolygonTest(np.array(poly, np.float32), tuple(map(float, pt)), False) >= 0


def _headline(stage: str, n: int, moving: list[str]) -> str:
    if stage == "contact_stabilization":
        return ("四点稳定丨准备下一步" if n >= 4 else
                "三点支撑丨姿态稳定" if n == 3 else "接触稳定")
    if stage == "limb_transport":
        who = LIMB_CN.get(moving[0], "") if moving else ""
        return f"单肢转移丨{who}移动中"
    if stage == "multi_limb_transition":
        return "多点过渡丨动态调整"
    if stage == "low_contact_count":
        return "接触点不足丨可能腾空或遮挡"
    if stage == "no_pose":
        return "未检出姿态"
    return "过渡中"


def analyse(frames: list[Frame], holds_per_frame, fps: float,
            hold_r=None, wall_H=None) -> list[Evidence]:
    """逐帧判定接触与阶段。

    holds_per_frame[i]  该帧各岩点的图像坐标
    hold_r              各岩点半径，用于把距离从「到质心」换算成「到边缘」
    wall_H              各帧相对参考帧的单应；给了就在墙面坐标里算速度

    分两趟：先把所有速度算出来做平滑，再分类。
    """
    import cv2
    hold_r = hold_r or {}
    n = len(frames)

    def to_wall(p, i):
        if wall_H is None or wall_H[i] is None:
            return np.asarray(p, float)
        q = np.array(p, np.float32).reshape(1, 1, 2)
        return cv2.perspectiveTransform(q, np.linalg.inv(wall_H[i])).reshape(2)

    # ---- 第一趟：墙面坐标与原始速度 ----
    scales = [_torso(f) for f in frames]
    raw = {k: np.full(n, np.nan) for k in LIMBS}
    hip_raw = np.full(n, np.nan)
    prev_w: dict[str, np.ndarray] = {}
    prev_hip = None

    for i, f in enumerate(frames):
        s = scales[i]
        if not f.ok or s is None:
            prev_w, prev_hip = {}, None
            continue
        cur = {}
        for limb in LIMBS:
            p = f.pt(LIMB_POINTS[limb])
            if p is None:
                continue
            wp = to_wall(p, i)
            cur[limb] = wp
            if limb in prev_w:
                raw[limb][i] = float(np.linalg.norm(wp - prev_w[limb])) / s * fps
        prev_w = cur
        if f.hip is not None:
            hw = to_wall(f.hip, i)
            if prev_hip is not None:
                hip_raw[i] = float(np.linalg.norm(hw - prev_hip)) / s * fps
            prev_hip = hw

    def med_smooth(a):
        out_ = a.copy()
        h = SPEED_WIN // 2
        for i in range(n):
            seg = a[max(0, i - h):i + h + 1]
            seg = seg[~np.isnan(seg)]
            out_[i] = np.median(seg) if len(seg) else np.nan
        return out_

    sp = {k: med_smooth(v) for k, v in raw.items()}
    hip_sp = med_smooth(hip_raw)

    # ---- 第二趟：迟滞分类 ----
    out: list[Evidence] = []
    in_contact = {k: False for k in LIMBS}

    for i, f in enumerate(frames):
        if not f.ok or scales[i] is None:
            out.append(Evidence(i, f.t, False, [], 0, "no_pose",
                                _headline("no_pose", 0, []), False, 0.0, [], [], None))
            in_contact = {k: False for k in LIMBS}
            continue

        s = scales[i]
        holds = holds_per_frame[i]
        contacts, moving, support = [], [], []

        for limb in LIMBS:
            p = f.pt(LIMB_POINTS[limb])
            if p is None:
                contacts.append(Contact(limb, "uncertain", None, 0.0, None))
                in_contact[limb] = False
                continue

            v = sp[limb][i]
            v = 0.0 if np.isnan(v) else float(v)

            # 迟滞：低于进入阈值就接触，高于退出阈值才松开
            if in_contact[limb]:
                if v > MOVING_LIMB:
                    in_contact[limb] = False
            else:
                if v <= STILL_LIMB:
                    in_contact[limb] = True

            hid, hd = None, None
            for k, hp in holds.items():
                rawd = float(np.linalg.norm(np.array(p) - np.array(hp)))
                edge = max(0.0, rawd - hold_r.get(k, 0.0)) / s
                if hd is None or edge < hd:
                    hid, hd = k, edge
            if hd is not None and hd > HOLD_NEAR:
                hid = None

            if in_contact[limb]:
                contacts.append(Contact(limb, "contact", hid, v, hd))
                support.append(p)
            elif v > MOVING_LIMB:
                contacts.append(Contact(limb, "moving", hid, v, hd))
                moving.append(limb)
            else:
                contacts.append(Contact(limb, "uncertain", hid, v, hd))

        hv = hip_sp[i]
        hv = 0.0 if np.isnan(hv) else float(hv)
        hip_stable = hv <= STILL_HIP

        nc = sum(c.state == "contact" for c in contacts)
        if nc < 2:
            stage = "low_contact_count"
        elif hip_stable and nc >= 3 and not moving:
            stage = "contact_stabilization"
        elif len(moving) == 1:
            stage = "limb_transport"
        elif len(moving) >= 2:
            stage = "multi_limb_transition"
        else:
            stage = "contact_stabilization" if nc >= 3 else "transition"

        poly = _hull(support)
        cis = _in_poly(f.com, poly) if (f.com is not None and len(poly) >= 3) else None
        out.append(Evidence(i, f.t, True, contacts, nc, stage,
                            _headline(stage, nc, moving), hip_stable, hv,
                            moving, poly, cis))
    return out


def _hull(pts):
    if len(pts) < 3:
        return [tuple(map(float, p)) for p in pts]
    import cv2
    h = cv2.convexHull(np.array(pts, np.float32))
    return [tuple(map(float, p[0])) for p in h]


def stabilise(ev: list[Evidence], win: int = 7) -> list[Evidence]:
    """阶段标签众数平滑，避免逐帧跳变造成闪烁。"""
    stages = [e.stage for e in ev]
    half = win // 2
    for i, e in enumerate(ev):
        if not e.ok:
            continue
        seg = [s for s in stages[max(0, i - half):i + half + 1] if s != "no_pose"]
        if seg:
            m = max(set(seg), key=seg.count)
            if m != e.stage:
                e.stage = m
                e.headline = _headline(m, e.n_contact, e.moving_limbs)
    return ev


def summarise(ev: list[Evidence]) -> dict:
    ok = [e for e in ev if e.ok]
    if not ok:
        return {"frames": len(ev), "pose_rate": 0.0}
    from collections import Counter
    return {
        "frames": len(ev),
        "pose_rate": round(len(ok) / len(ev), 3),
        "mean_contacts": round(float(np.mean([e.n_contact for e in ok])), 2),
        "stage_frames": dict(Counter(e.stage for e in ok)),
        "hip_stable_rate": round(sum(e.hip_stable for e in ok) / len(ok), 3),
        "hold_linked_rate": round(
            float(np.mean([sum(c.hold is not None for c in e.contacts) / 4 for e in ok])), 3),
    }
