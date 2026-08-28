"""姿态流：ROI 追踪的 2D 关键点提取。

对应 docs/03-感知层架构.md 的 P0/P1 档。

攀岩视频里人常常只占画面很小一块，整帧送检的检出率会很低。
这里用「上一帧的人体框 → 外扩 → 上采样 → 检测」的 ROI 追踪，
在测试素材上把检出率从 46.7% 提到 92.9%。
"""
from __future__ import annotations

import dataclasses
import numpy as np

# MediaPipe Pose 的 33 点索引
NOSE = 0
L_SHO, R_SHO = 11, 12
L_ELB, R_ELB = 13, 14
L_WRI, R_WRI = 15, 16
L_HIP, R_HIP = 23, 24
L_KNE, R_KNE = 25, 26
L_ANK, R_ANK = 27, 28
L_FOOT, R_FOOT = 31, 32

# 画骨架用的连接
SKELETON = [
    (L_SHO, R_SHO), (L_SHO, L_ELB), (L_ELB, L_WRI), (R_SHO, R_ELB), (R_ELB, R_WRI),
    (L_SHO, L_HIP), (R_SHO, R_HIP), (L_HIP, R_HIP),
    (L_HIP, L_KNE), (L_KNE, L_ANK), (L_ANK, L_FOOT),
    (R_HIP, R_KNE), (R_KNE, R_ANK), (R_ANK, R_FOOT),
]

# 四个肢端——接触判定用这四个点
LIMB_POINTS = {"LH": L_WRI, "RH": R_WRI, "LF": L_FOOT, "RF": R_FOOT}

# 环节质量占比与质心位置（Winter / de Leva 人体测量数据）
# (近端点, 远端点, 质量占比, 质心距近端的比例)
SEGMENTS = [
    (L_SHO, R_SHO, 0.081, 0.50),   # 头颈，用肩中点近似承载
    (L_SHO, L_HIP, 0.2485, 0.50),  # 躯干左半
    (R_SHO, R_HIP, 0.2485, 0.50),  # 躯干右半
    (L_SHO, L_ELB, 0.028, 0.436), (R_SHO, R_ELB, 0.028, 0.436),
    (L_ELB, L_WRI, 0.016, 0.430), (R_ELB, R_WRI, 0.016, 0.430),
    (L_WRI, L_WRI, 0.006, 0.0),   (R_WRI, R_WRI, 0.006, 0.0),
    (L_HIP, L_KNE, 0.100, 0.433), (R_HIP, R_KNE, 0.100, 0.433),
    (L_KNE, L_ANK, 0.0465, 0.433), (R_KNE, R_ANK, 0.0465, 0.433),
    (L_ANK, L_FOOT, 0.0145, 0.50), (R_ANK, R_FOOT, 0.0145, 0.50),
]


@dataclasses.dataclass
class Frame:
    """一帧的姿态结果。坐标是原图像素坐标。"""
    idx: int
    t: float
    ok: bool
    xy: np.ndarray | None = None          # (33, 2)
    vis: np.ndarray | None = None         # (33,)
    com: tuple[float, float] | None = None  # 2D 质心代理
    hip: tuple[float, float] | None = None  # 髋中点——知识库指定的重心视觉代理

    def pt(self, i: int) -> tuple[float, float] | None:
        if not self.ok or self.vis[i] < 0.3:
            return None
        return float(self.xy[i][0]), float(self.xy[i][1])


def _com_2d(xy: np.ndarray, vis: np.ndarray) -> tuple[float, float] | None:
    """环节质量加权的 2D 质心代理。

    注意这是**投影到图像平面的 2D 代理**，不是真实三维重心。
    知识库 PHY-GRAVITY-COM-001 规定不得输出重心的精确数值，
    渲染层据此只画位置不给坐标。
    """
    tot, acc = 0.0, np.zeros(2)
    for a, b, m, r in SEGMENTS:
        if vis[a] < 0.3 or vis[b] < 0.3:
            continue
        p = xy[a] + (xy[b] - xy[a]) * r
        acc += p * m
        tot += m
    if tot < 0.5:      # 一半以上的质量都没看到，不给结果
        return None
    return tuple(acc / tot)


class PoseTracker:
    """ROI 追踪的姿态提取。

    重捕获策略很关键。第一版在检测失败时把 ROI 直接置空、下一帧回退到
    全图原分辨率检测——人只占画幅 1/5 时，缩到模型输入尺寸就太小了，
    于是「一次丢失 → 全图检测失败 → 继续丢失」形成连锁。
    实测这让开头 20% 的检出率只有 43.7%，而锁定之后的后 60% 是 100%。

    现在改成：丢失后保留最后已知位置，按 1.6x → 2.6x → 全图 逐级扩大搜索，
    每一级都上采样到目标分辨率再送检。
    """

    def __init__(self, model_path: str, pad: float = 0.6, min_roi: int = 320,
                 target: int = 640, conf: float = 0.25):
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python import vision
        from mediapipe.tasks.python.vision import RunningMode

        self._mp = __import__("mediapipe")
        self._lm = vision.PoseLandmarker.create_from_options(
            vision.PoseLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=model_path),
                running_mode=RunningMode.VIDEO, num_poses=1,
                min_pose_detection_confidence=conf,
                min_pose_presence_confidence=conf,
                min_tracking_confidence=conf))
        self.pad, self.min_roi, self.target = pad, min_roi, target
        self._roi: tuple[int, int, int, int] | None = None
        self._last: tuple[int, int, int, int] | None = None   # 丢失后仍保留
        self._miss = 0

    def _boxes(self, w: int, h: int) -> list[tuple[int, int, int, int]]:
        """按优先级给出候选搜索框：跟踪框 → 逐级扩大 → 全图。"""
        base = self._roi or self._last
        if base is None:
            return [(0, 0, w, h)]
        x0, y0, x1, y1 = base
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        side = max(x1 - x0, y1 - y0, self.min_roi)
        out = []
        for grow in ((1 + self.pad,) if self._roi else (1.6, 2.6)):
            half = side * grow / 2
            out.append((max(0, int(cx - half)), max(0, int(cy - half)),
                        min(w, int(cx + half)), min(h, int(cy + half))))
        out.append((0, 0, w, h))
        return out

    def _detect_in(self, bgr, box, t_ms):
        """在给定框内检测。返回原图坐标的关键点，或 None。"""
        import cv2
        rx0, ry0, rx1, ry1 = box
        sub = bgr[ry0:ry1, rx0:rx1]
        if sub.size == 0:
            return None
        scale = min(4.0, max(1.0, self.target / max(sub.shape[0], sub.shape[1])))
        if scale > 1.01:
            sub = cv2.resize(sub, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        img = self._mp.Image(image_format=self._mp.ImageFormat.SRGB,
                             data=cv2.cvtColor(sub, cv2.COLOR_BGR2RGB))
        res = self._lm.detect_for_video(img, t_ms)
        if not res.pose_landmarks:
            return None
        L = res.pose_landmarks[0]
        sh, sw = sub.shape[:2]
        xy = np.array([[l.x * sw / scale + rx0, l.y * sh / scale + ry0] for l in L])
        vis = np.array([l.visibility for l in L])
        return xy, vis

    def __call__(self, bgr: np.ndarray, idx: int, t: float,
                 hint: tuple[int, int, int, int] | None = None) -> Frame:
        h, w = bgr.shape[:2]
        boxes = [hint] if hint else self._boxes(w, h)
        t_ms = int(t * 1000)
        got = None
        for k, box in enumerate(boxes):
            got = self._detect_in(bgr, box, t_ms + k)   # 时间戳须单调递增
            if got is not None:
                break

        if got is None:
            self._roi = None
            self._miss += 1
            if self._miss > 45:          # 长时间找不到才丢弃最后位置
                self._last = None
            return Frame(idx, t, False)

        xy, vis = got
        self._miss = 0
        good = vis > 0.3
        if good.sum() >= 6:
            g = xy[good]
            self._roi = (int(g[:, 0].min()), int(g[:, 1].min()),
                         int(g[:, 0].max()), int(g[:, 1].max()))
            self._last = self._roi
        else:
            self._roi = None

        hip = None
        if vis[L_HIP] > 0.3 and vis[R_HIP] > 0.3:
            hip = tuple((xy[L_HIP] + xy[R_HIP]) / 2)
        return Frame(idx, t, True, xy, vis, _com_2d(xy, vis), hip)

    def close(self):
        try:
            self._lm.close()
        except Exception:
            pass


def smooth(frames: list[Frame], win: int = 5) -> list[Frame]:
    """对关键点做中值平滑，抑制抖动。丢帧不插值——看不见就是看不见。"""
    idx = [i for i, f in enumerate(frames) if f.ok]
    if not idx:
        return frames
    half = win // 2
    stack = {i: frames[i].xy.copy() for i in idx}
    for pos, i in enumerate(idx):
        lo, hi = max(0, pos - half), min(len(idx), pos + half + 1)
        neigh = np.stack([stack[idx[k]] for k in range(lo, hi)])
        frames[i].xy = np.median(neigh, axis=0)
        frames[i].com = _com_2d(frames[i].xy, frames[i].vis)
        if frames[i].vis[L_HIP] > 0.3 and frames[i].vis[R_HIP] > 0.3:
            frames[i].hip = tuple((frames[i].xy[L_HIP] + frames[i].xy[R_HIP]) / 2)
    return frames


def backfill(tracker: "PoseTracker", frames_bgr, pf: list[Frame], fps: float,
             pad: float = 1.0) -> list[Frame]:
    """第二趟：对丢失帧用前后成功帧插值出的 ROI 重试。

    人是连续运动的，夹在两个成功帧之间的失败帧，位置其实被约束得很好。
    第一趟按时间顺序推进时用不上「未来」的信息，第二趟可以。
    """
    n = len(pf)
    oks = [i for i, f in enumerate(pf) if f.ok]
    if len(oks) < 2:
        return pf

    def box_of(i):
        g = pf[i].xy[pf[i].vis > 0.3]
        return (g[:, 0].min(), g[:, 1].min(), g[:, 0].max(), g[:, 1].max())

    import bisect
    t_ms = int(pf[-1].t * 1000) + 1000      # 从更大的时间戳继续，保持单调
    fixed = 0
    for i in range(n):
        if pf[i].ok:
            continue
        j = bisect.bisect_left(oks, i)
        prev = oks[j - 1] if j > 0 else None
        nxt = oks[j] if j < len(oks) else None
        if prev is None and nxt is None:
            continue
        if prev is None:
            bx = box_of(nxt)
        elif nxt is None:
            bx = box_of(prev)
        else:                                # 线性插值
            a, b = box_of(prev), box_of(nxt)
            w_ = (i - prev) / (nxt - prev)
            bx = tuple(a[k] + (b[k] - a[k]) * w_ for k in range(4))
        cx, cy = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
        half = max(bx[2] - bx[0], bx[3] - bx[1], 200) * (1 + pad) / 2
        H, W = frames_bgr[i].shape[:2]
        box = (max(0, int(cx - half)), max(0, int(cy - half)),
               min(W, int(cx + half)), min(H, int(cy + half)))
        got = tracker._detect_in(frames_bgr[i], box, t_ms)
        t_ms += 1
        if got is None:
            continue
        xy, vis = got
        hip = None
        if vis[L_HIP] > 0.3 and vis[R_HIP] > 0.3:
            hip = tuple((xy[L_HIP] + xy[R_HIP]) / 2)
        pf[i] = Frame(i, pf[i].t, True, xy, vis, _com_2d(xy, vis), hip)
        fixed += 1
    return pf, fixed


# --- 姿态可靠性 -----------------------------------------------------------
# 姿态检出率 100% 不等于姿态可信。攀岩里有两类常见的「检出了但不可信」：
#
#   1. 肢段朝向镜头 —— 大腿正对相机时投影被压缩，该关节的角度失去意义
#   2. 姿态跳变     —— 深蹲、遮挡、运动模糊时关键点会在帧间大幅跳跃
#
# 实测一段 3.2 秒的素材：检出率 100%，但前 1 秒有 14/30 帧的关键点
# 跳变超过 0.35 倍躯干长（最大一帧 2.12），而 1 秒之后只有 2/65。
# 在那段数据上算出来的膝角会从 124° 跳到 50° 再跳回 117°，全是伪影。
#
# 不标出可靠区间，下游会在噪声上给出言之凿凿的错误结论。

KEY_LM = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
JUMP_MAX = 0.35          # 关键点帧间跳变上限（躯干长倍数）
VIS_MIN = 0.50           # 关键点平均可见度下限


def reliability(frames: list[Frame], win: int = 5) -> np.ndarray:
    """逐帧姿态可靠性（True=可信）。检出与可信是两件事。"""
    n = len(frames)
    ok = np.array([f.ok for f in frames])
    xy = np.stack([f.xy if f.ok else np.full((33, 2), np.nan) for f in frames])
    vis = np.stack([f.vis if f.ok else np.zeros(33) for f in frames])

    torso = np.linalg.norm((xy[:, L_SHO] + xy[:, R_SHO]) / 2 -
                           (xy[:, L_HIP] + xy[:, R_HIP]) / 2, axis=1)
    jump = np.zeros(n)
    if n > 1:
        jump[1:] = np.nanmax(np.linalg.norm(xy[1:, KEY_LM] - xy[:-1, KEY_LM],
                                            axis=2), axis=1) / np.maximum(torso[1:], 1e-6)
    good = ok & (np.nanmean(vis[:, KEY_LM], axis=1) >= VIS_MIN) & \
        (np.nan_to_num(jump, nan=9.9) <= JUMP_MAX)

    # 单帧抖动不该毁掉整段：用滑动多数票
    out = good.copy()
    h = win // 2
    for i in range(n):
        seg = good[max(0, i - h):i + h + 1]
        out[i] = seg.mean() >= 0.5
    return out


def reliable_windows(rel: np.ndarray, fps: float, min_s: float = 0.4):
    """把可靠帧合并成区间，返回 [(起秒, 止秒), ...]。"""
    out, i, n = [], 0, len(rel)
    while i < n:
        if not rel[i]:
            i += 1
            continue
        j = i
        while j < n and rel[j]:
            j += 1
        if (j - i) / fps >= min_s:
            out.append((i / fps, j / fps))
        i = j
    return out


# --- 关节角度可信度 -------------------------------------------------------
# reliability() 判的是「整体姿态是否可信」，但还有一层更细的问题：
# **某个具体关节的角度是否可信**。
#
# 二维投影下，一段肢体指向镜头时会被压缩，该关节的角度随之失去意义。
# 只用「投影长度低于自身中位」来判会漏——如果这段肢体在整段视频里
# 大部分时间都朝向镜头，它自身的中位数本来就是压缩值。
# 实测左前臂投影中位 0.16、右前臂 0.31，自身中位法只标出 9% 的帧，
# 而实际上左肘角度全程不可用（中位报 37°，是伪影）。
#
# 所以用两条互补的约束：
#   1. **左右对称**：同名肢段的真实三维长度相等，投影长度比偏离 1 太多，
#      短的那侧就是被压缩了
#   2. **近远端比例**：前臂与上臂、小腿与大腿的真实长度接近，比例过小同样说明压缩

JOINT_SEG = {          # 关节 -> (近端段, 远端段, 对侧关节)
    "L_ELBOW": ((11, 13), (13, 15), "R_ELBOW"),
    "R_ELBOW": ((12, 14), (14, 16), "L_ELBOW"),
    "L_KNEE": ((23, 25), (25, 27), "R_KNEE"),
    "R_KNEE": ((24, 26), (26, 28), "L_KNEE"),
}
SYM_MIN = 0.65         # 左右投影长度比下限
PROP_MIN = 0.55        # 远端段/近端段 投影比下限


def joint_reliability(frames: list[Frame], joint: str) -> np.ndarray:
    """某个关节的角度是否可信（True=可信）。"""
    n = len(frames)
    xy = np.stack([f.xy if f.ok else np.full((33, 2), np.nan) for f in frames])
    ok = np.array([f.ok for f in frames])
    prox, dist, mirror = JOINT_SEG[joint]

    def L(seg):
        return np.linalg.norm(xy[:, seg[0]] - xy[:, seg[1]], axis=1)

    p, d = L(prox), L(dist)
    mp, md = JOINT_SEG[mirror][0], JOINT_SEG[mirror][1]
    p2, d2 = L(mp), L(md)

    with np.errstate(invalid="ignore", divide="ignore"):
        sym_p = np.minimum(p, p2) / np.maximum(p, p2)
        sym_d = np.minimum(d, d2) / np.maximum(d, d2)
        prop = d / np.maximum(p, 1e-6)
        # 只在本侧更短时才归咎于本侧
        mine_short_p = p <= p2
        mine_short_d = d <= d2

    bad = (~ok)
    bad |= (sym_p < SYM_MIN) & mine_short_p
    bad |= (sym_d < SYM_MIN) & mine_short_d
    bad |= prop < PROP_MIN
    return ~np.nan_to_num(bad, nan=True).astype(bool)
