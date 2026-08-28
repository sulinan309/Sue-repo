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
    """ROI 追踪的姿态提取。"""

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

    def _roi_for(self, w: int, h: int) -> tuple[int, int, int, int]:
        if self._roi is None:
            return 0, 0, w, h
        x0, y0, x1, y1 = self._roi
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        half = max(x1 - x0, y1 - y0, self.min_roi) * (1 + self.pad) / 2
        return (max(0, int(cx - half)), max(0, int(cy - half)),
                min(w, int(cx + half)), min(h, int(cy + half)))

    def __call__(self, bgr: np.ndarray, idx: int, t: float) -> Frame:
        import cv2
        h, w = bgr.shape[:2]
        rx0, ry0, rx1, ry1 = self._roi_for(w, h)
        sub = bgr[ry0:ry1, rx0:rx1]
        if sub.size == 0:
            self._roi = None
            return Frame(idx, t, False)

        scale = min(3.0, max(1.0, self.target / max(sub.shape[0], sub.shape[1])))
        if scale > 1.01:
            sub = cv2.resize(sub, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        img = self._mp.Image(image_format=self._mp.ImageFormat.SRGB,
                             data=cv2.cvtColor(sub, cv2.COLOR_BGR2RGB))
        res = self._lm.detect_for_video(img, int(t * 1000))
        if not res.pose_landmarks:
            self._roi = None            # 丢失后下一帧回到全图
            return Frame(idx, t, False)

        L = res.pose_landmarks[0]
        sh, sw = sub.shape[:2]
        xy = np.array([[l.x * sw / scale + rx0, l.y * sh / scale + ry0] for l in L])
        vis = np.array([l.visibility for l in L])

        good = vis > 0.3
        if good.sum() >= 6:
            g = xy[good]
            self._roi = (int(g[:, 0].min()), int(g[:, 1].min()),
                         int(g[:, 0].max()), int(g[:, 1].max()))
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
