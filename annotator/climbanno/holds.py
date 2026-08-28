"""视觉流：岩点检测与墙面锁定。

对应 docs/03-感知层架构.md 的 P2/P3 档。

两件事：
  1. 从画面里找出岩点（颜色分割 + 形状过滤 + 人体排除）
  2. 用墙面特征估每帧单应，把岩点位置锁在墙上——手持镜头漂移时仍然对齐

第 2 点是 P4「墙体坐标系」的一个极简版本：它只做二维图像对齐，
不给出度量尺度，也不知道墙面法向。用它可以稳定岩点位置，
但不能回答「髋部离墙多远」——那需要真正的墙面几何。
"""
from __future__ import annotations

import dataclasses
import cv2
import numpy as np


@dataclasses.dataclass
class Hold:
    id: str
    x: float          # 参考帧坐标
    y: float
    r: float
    area: int
    kind: str         # dark | color


# 躯干核心点：头、肩、肘、髋、膝。
# **刻意不包含腕和踝**——接触中的岩点必然紧贴肢端，
# 把肢端一起挖掉会正好丢失我们最需要的那些岩点。
# 头部则相反：它永远不是接触点，而深色头发很容易被当成岩点，所以要遮。
HEAD = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
CORE = HEAD + [11, 12, 13, 14, 23, 24, 25, 26]


def person_mask(shape, frames, dilate: int = 25, core_only: bool = True) -> np.ndarray:
    """用姿态关键点凸包生成人体掩膜。

    core_only=True 时只遮躯干核心，保留手脚附近的区域，
    代价是鞋子和深色衣物可能被当成岩点候选——这一部分交给
    detect_stable() 的时间一致性过滤来剔除。
    """
    m = np.zeros(shape[:2], np.uint8)
    for f in frames:
        if not f.ok:
            continue
        idx = [i for i in (CORE if core_only else range(33)) if f.vis[i] > 0.3]
        if len(idx) < 3:
            continue
        cv2.fillConvexPoly(m, cv2.convexHull(f.xy[idx].astype(np.int32)), 1)
    if dilate:
        m = cv2.dilate(m, np.ones((dilate, dilate), np.uint8))
    return m


def detect(frame: np.ndarray, exclude: np.ndarray | None = None, *,
           v_dark: int = 90, s_color: int = 110, hue: tuple[int, int] = (60, 132),
           area: tuple[int, int] = (250, 12000), max_r: int = 70,
           bottom_cut: float = 0.72) -> list[Hold]:
    """在一帧上检测岩点。

    这套阈值是针对「浅色墙 + 深色/饱和色岩点」调的，换岩馆需要重标。
    真实产品应当用岩馆标准 Beta 建线路底库，而不是靠颜色现场猜——
    这里是 demo，用颜色够了。
    """
    h, w = frame.shape[:2]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]

    dark = (V < v_dark)
    color = (H >= hue[0]) & (H <= hue[1]) & (S > s_color) & (V > 60)
    m = (dark | color).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))

    m[int(h * bottom_cut):, :] = 0          # 垫子区域
    if exclude is not None:
        m[exclude > 0] = 0

    n, lab, stats, cent = cv2.connectedComponentsWithStats(m, 8)
    out = []
    for i in range(1, n):
        x, y, ww, hh, a = stats[i]
        if not (area[0] <= a <= area[1]):
            continue
        ar = ww / max(hh, 1)
        if ar > 5 or ar < 0.2:
            continue
        if a / (ww * hh) < 0.38:            # 太空心的多半不是岩点
            continue
        cx, cy = float(cent[i][0]), float(cent[i][1])
        kind = "dark" if dark[int(cy), int(cx)] else "color"
        out.append(Hold("", cx, cy, min(max_r, max(ww, hh) * 0.6), int(a), kind))

    out.sort(key=lambda k: (k.y, k.x))      # 自上而下编号，和岩馆习惯一致
    for j, hold in enumerate(out):
        hold.id = f"H{j + 1:02d}"
    return out


class WallTracker:
    """逐帧估计相对参考帧的单应，把参考帧坐标映射到当前帧。"""

    def __init__(self, ref_gray: np.ndarray, max_corners: int = 600):
        self.prev = ref_gray
        self.p = cv2.goodFeaturesToTrack(ref_gray, maxCorners=max_corners,
                                         qualityLevel=0.006, minDistance=7)
        self.H = np.eye(3)
        self.ok = True

    def update(self, gray: np.ndarray) -> np.ndarray:
        if self.p is None or len(self.p) < 12:
            self.ok = False
            return self.H
        p1, st, _ = cv2.calcOpticalFlowPyrLK(self.prev, gray, self.p, None,
                                             winSize=(21, 21), maxLevel=3)
        good = st.ravel() == 1
        if good.sum() >= 12:
            Hd, _ = cv2.findHomography(self.p[good], p1[good], cv2.RANSAC, 3.0)
            if Hd is not None:
                self.H = Hd @ self.H
                self.ok = True
            else:
                self.ok = False
        else:
            self.ok = False
        self.prev = gray
        self.p = cv2.goodFeaturesToTrack(gray, maxCorners=600,
                                         qualityLevel=0.006, minDistance=7)
        return self.H

    def project(self, pts: np.ndarray) -> np.ndarray:
        """参考帧坐标 → 当前帧坐标。"""
        p = np.asarray(pts, np.float32).reshape(-1, 1, 2)
        return cv2.perspectiveTransform(p, self.H).reshape(-1, 2)


def detect_stable(frames_bgr, grays, pose_frames, ref_i: int, *,
                  samples: int = 12, persist: float = 0.45,
                  merge_px: float = 26.0, **kw) -> tuple[list[Hold], list[np.ndarray]]:
    """多帧检测 + 墙面坐标聚类，只保留位置稳定的岩点。

    原理很简单：**岩点不动，鞋子和衣服会动。**
    把每个采样帧的候选点用单应映射回参考帧坐标，同一个岩点会落在一起；
    人身上的假阳性因为人在移动，映射回去是散的，聚不成簇。

    返回 (岩点列表, 每帧的单应矩阵)。
    """
    n = len(frames_bgr)
    # 先算出每帧相对参考帧的单应
    Hs: list[np.ndarray] = [None] * n
    Hs[ref_i] = np.eye(3)
    wt = WallTracker(grays[ref_i])
    for i in range(ref_i + 1, n):
        Hs[i] = wt.update(grays[i]).copy()
    if ref_i > 0:
        wb = WallTracker(grays[ref_i])
        for i in range(ref_i - 1, -1, -1):
            Hs[i] = wb.update(grays[i]).copy()

    idxs = np.unique(np.linspace(0, n - 1, samples).astype(int))
    votes: list[list] = []
    for i in idxs:
        mask = person_mask(frames_bgr[i].shape, [pose_frames[i]], core_only=True)
        cands = detect(frames_bgr[i], exclude=mask, **kw)
        if not cands:
            continue
        pts = np.array([[c.x, c.y] for c in cands], np.float32).reshape(-1, 1, 2)
        back = cv2.perspectiveTransform(pts, np.linalg.inv(Hs[i])).reshape(-1, 2)
        for c, b in zip(cands, back):
            votes.append([float(b[0]), float(b[1]), c.r, c.area, c.kind])

    # 在参考帧坐标里做贪心聚类
    clusters: list[dict] = []
    for x, y, r, a, kind in votes:
        for cl in clusters:
            if (x - cl["x"]) ** 2 + (y - cl["y"]) ** 2 < merge_px ** 2:
                k = cl["n"]
                cl["x"] = (cl["x"] * k + x) / (k + 1)
                cl["y"] = (cl["y"] * k + y) / (k + 1)
                cl["r"] = (cl["r"] * k + r) / (k + 1)
                cl["a"] = (cl["a"] * k + a) / (k + 1)
                cl["n"] = k + 1
                break
        else:
            clusters.append({"x": x, "y": y, "r": r, "a": a, "n": 1, "kind": kind})

    need = max(2, int(len(idxs) * persist))
    keep = [c for c in clusters if c["n"] >= need]
    keep.sort(key=lambda c: (c["y"], c["x"]))
    out = [Hold(f"H{j+1:02d}", c["x"], c["y"], c["r"], int(c["a"]), c["kind"])
           for j, c in enumerate(keep)]
    return out, Hs
