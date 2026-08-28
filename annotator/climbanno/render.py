"""覆盖渲染。

信息设计的一条原则：**画面上每一个元素都要挣得它占的位置。**

第一版把检测到的 27 个岩点全部圈出并编号，结果是画面被编号淹没，
真正重要的四个接触点反而看不出来。现在只画与判定直接相关的东西：

  绿色粗骨架   姿态流观察
  绿环 + 标签  该肢端判定为接触（视觉运动学代理，不是力学承重）
  橙圈         该接触点关联到的岩点（关联不上就不画，不影响接触判定）
  半透明绿面   支撑面 —— 接触点围出的范围（PHY-EQUILIBRIUM-002）
  品红点       2D 质心代理

其余检测到的岩点保留在 holds.json 里，不画。
"""
from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .pose import SKELETON, LIMB_POINTS
from .contact import LIMB_CN

FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

# BGR
C_OK = (90, 235, 105)        # 绿 —— 接触 / 骨架
C_HOLD = (60, 170, 255)      # 橙 —— 关联岩点
C_MOVE = (80, 150, 255)      # 橙红 —— 移动中的肢体
C_COM = (225, 70, 225)       # 品红 —— 质心代理
C_DIM = (150, 150, 150)
C_PANEL = (20, 18, 16)

STAGE_TONE = {
    "contact_stabilization": C_OK,
    "limb_transport": (110, 200, 255),
    "multi_limb_transition": (110, 200, 255),
    "low_contact_count": (110, 190, 250),
    "transition": (200, 200, 200),
    "no_pose": C_DIM,
}
ACTION_CN = {
    "contact_stabilization": "身体稳定",
    "limb_transport": "换手换脚",
    "multi_limb_transition": "动态调整",
    "low_contact_count": "接触不足",
    "transition": "过渡",
    "no_pose": "未检出",
}


class Text:
    def __init__(self):
        self._c = {}

    def font(self, size, bold=True):
        k = (size, bold)
        if k not in self._c:
            self._c[k] = ImageFont.truetype(FONT if bold else FONT_R, size)
        return self._c[k]

    def size(self, t, s, bold=True):
        b = self.font(s, bold).getbbox(t)
        return b[2] - b[0], b[3] - b[1]

    def draw(self, bgr, items):
        img = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(img)
        for x, y, t, s, c, *rest in items:
            bold = rest[0] if rest else True
            d.text((x, y), t, font=self.font(s, bold), fill=(c[2], c[1], c[0]))
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def _scale_of(frame) -> float:
    """用躯干长度决定线宽和标记大小——人在画面里小的时候，
    固定线宽会把人整个盖住。"""
    from .pose import L_SHO, R_SHO, L_HIP, R_HIP
    if not frame.ok:
        return 1.0
    try:
        d = float(np.linalg.norm((frame.xy[L_SHO] + frame.xy[R_SHO]) / 2 -
                                 (frame.xy[L_HIP] + frame.xy[R_HIP]) / 2))
    except Exception:
        return 1.0
    return float(np.clip(d / 140.0, 0.45, 1.6))     # 140px 是标定基准


def draw_frame(bgr, frame, ev, holds_xy, txt: Text, *, meta: dict) -> np.ndarray:
    h, w = bgr.shape[:2]
    out = bgr.copy()
    labels = []
    k = _scale_of(frame)
    W = lambda base, lo=1: max(lo, int(round(base * k)))     # 线宽
    R = lambda base: max(3, int(round(base * k)))            # 半径
    F = lambda base: max(13, int(round(base * (0.6 + 0.4 * k))))  # 字号

    placed: list[tuple[int, int, int, int]] = []

    def _hit(r):
        for q in placed:
            if not (r[2] < q[0] or r[0] > q[2] or r[3] < q[1] or r[1] > q[3]):
                return True
        return False

    def place(ax, ay, tw, th, rad, prefer_right=True):
        """在锚点周围找一个不与已放标签重叠的位置。"""
        d = rad + R(12)
        cands = []
        for side in ((1, -1) if prefer_right else (-1, 1)):
            for dy in (0, -1, 1, -2, 2):
                x = ax + d if side > 0 else ax - d - tw
                cands.append((x, ay - th // 2 + dy * (th + 6)))
        for dy in (-1, 1):                      # 兜底：正上/正下
            cands.append((ax - tw // 2, ay + dy * (rad + th + 10)))
        for x, y in cands:
            x = max(6, min(w - tw - 8, int(x)))
            y = max(6, min(h - th - 8, int(y)))
            r = (x - 7, y - 4, x + tw + 7, y + th + 6)
            if not _hit(r):
                placed.append(r)
                return x, y
        x = max(6, min(w - tw - 8, int(ax + d)))
        y = max(6, min(h - th - 8, int(ay - th // 2)))
        placed.append((x - 7, y - 4, x + tw + 7, y + th + 6))
        return x, y

    def chip(x, y, tw, th, alpha=0.62):
        x0, y0 = max(0, x - 7), max(0, y - 4)
        x1, y1 = min(w, x + tw + 7), min(h, y + th + 6)
        if x1 <= x0 or y1 <= y0:
            return
        roi = out[y0:y1, x0:x1]
        out[y0:y1, x0:x1] = cv2.addWeighted(
            roi, 1 - alpha, np.full_like(roi, (24, 22, 20), np.uint8), alpha, 0)

    # ---- 支撑面：接触点围出的范围 ----
    if len(ev.support) >= 3:
        poly = np.array(ev.support, np.int32)
        ov = out.copy()
        cv2.fillPoly(ov, [poly], (120, 230, 140))
        out = cv2.addWeighted(ov, 0.18, out, 0.82, 0)
        cv2.polylines(out, [poly], True, (120, 230, 140), 1, cv2.LINE_AA)

    # ---- 骨架 ----
    if frame.ok:
        for a, b in SKELETON:
            pa, pb = frame.pt(a), frame.pt(b)
            if pa and pb:
                cv2.line(out, tuple(map(int, pa)), tuple(map(int, pb)),
                         (30, 90, 40), W(9, 3), cv2.LINE_AA)  # 深色描边，花墙上也看得清
                cv2.line(out, tuple(map(int, pa)), tuple(map(int, pb)),
                         C_OK, W(5, 2), cv2.LINE_AA)
        for i in (0, 11, 12, 13, 14, 23, 24, 25, 26):       # 只画主要关节
            p = frame.pt(i)
            if p:
                cv2.circle(out, tuple(map(int, p)), R(5), (70, 190, 240), -1, cv2.LINE_AA)

    # ---- 四个肢端 ----
    for c in ev.contacts:
        p = frame.pt(LIMB_POINTS[c.limb]) if frame.ok else None
        if p is None:
            continue
        pi = tuple(map(int, p))

        fs = F(22)
        if c.state == "contact":
            cv2.circle(out, pi, R(20), (25, 80, 35), W(7, 3), cv2.LINE_AA)
            cv2.circle(out, pi, R(20), C_OK, W(4, 2), cv2.LINE_AA)
            s = f"{LIMB_CN[c.limb]}·接触"
            col = C_OK
        elif c.state == "moving":
            cv2.circle(out, pi, R(18), C_MOVE, W(3, 2), cv2.LINE_AA)
            s = f"{LIMB_CN[c.limb]}·移动"
            col = C_MOVE
        else:
            cv2.circle(out, pi, R(14), C_DIM, W(2, 1), cv2.LINE_AA)
            s = None
            col = C_DIM

        if s:
            tw, th = txt.size(s, fs)
            lx, ly = place(pi[0], pi[1], tw, th, R(20), pi[0] < w * 0.62)
            chip(lx, ly, tw, th)
            labels.append((lx, ly, s, fs, col))

    # ---- 接下来的两个落点（回放视角，不是预测）----
    nx = meta.get("next_landings") or []
    limb_now = {c.limb: frame.pt(LIMB_POINTS[c.limb]) for c in ev.contacts} if frame.ok else {}
    for rank, (lm, pos, dt) in enumerate(nx[:2]):
        px, py = int(pos[0]), int(pos[1])
        cur0 = limb_now.get(lm)
        if cur0 and np.linalg.norm(np.array(cur0) - np.array([px, py])) < R(26):
            continue                            # 落点已到，不必再提示
        first = rank == 0
        col = (70, 210, 255) if first else (120, 170, 190)
        rad = R(26 if first else 19)
        # 目标环 + 十字准星
        cv2.circle(out, (px, py), rad, (20, 40, 60), W(7, 3), cv2.LINE_AA)
        cv2.circle(out, (px, py), rad, col, W(4, 2), cv2.LINE_AA)
        cv2.line(out, (px - rad - R(8), py), (px - rad + R(3), py), col, W(3, 2), cv2.LINE_AA)
        cv2.line(out, (px + rad - R(3), py), (px + rad + R(8), py), col, W(3, 2), cv2.LINE_AA)
        cv2.line(out, (px, py - rad - R(8)), (px, py - rad + R(3)), col, W(3, 2), cv2.LINE_AA)
        cv2.line(out, (px, py + rad - R(3)), (px, py + rad + R(8)), col, W(3, 2), cv2.LINE_AA)
        # 第一个落点画一条虚线，从当前肢端指过去
        cur = limb_now.get(lm)
        if first and cur:
            a = np.array(cur, float); b = np.array([px, py], float)
            L_ = np.linalg.norm(b - a)
            if L_ > 12:
                d = (b - a) / L_
                for s0 in range(int(rad + 6), int(L_ - rad), 22):
                    p1 = b - d * s0
                    p2 = b - d * min(s0 + 11, L_ - rad)
                    cv2.line(out, tuple(p1.astype(int)), tuple(p2.astype(int)),
                             col, W(2, 1), cv2.LINE_AA)
        s = f"{'①' if first else '②'} {LIMB_CN[lm]}落点 {dt:.1f}s"
        fsz = F(21 if first else 18)
        tw, th = txt.size(s, fsz)
        lx, ly = place(px, py, tw, th, rad, px < w * 0.6)
        chip(lx, ly, tw, th, 0.7)
        labels.append((lx, ly, s, fsz, col))

    # ---- 质心代理 ----
    if frame.ok and frame.com:
        cp = tuple(map(int, frame.com))
        cv2.circle(out, cp, R(17), (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(out, cp, R(13), C_COM, -1, cv2.LINE_AA)
        cv2.circle(out, cp, R(6), (255, 255, 255), -1, cv2.LINE_AA)
        s = "重心代理"
        fs = F(21)
        tw, th = txt.size(s, fs)
        lx, ly = cp[0] + R(26), cp[1] - th // 2
        lx = max(6, min(w - tw - 8, lx))
        chip(lx, ly, tw, th)
        labels.append((lx, ly, s, fs, C_COM))

    # ---- 底部证据面板 ----
    # 按实际行高从下往上排，避免不同字号下互相压行
    rows = [
        (f"攀岩动作证据    t={ev.t:05.2f}s    帧 {ev.idx}", 20, (185, 185, 185), False, 10),
        (ev.headline, 38, STAGE_TONE.get(ev.stage, C_OK) if ev.ok else C_DIM, True, 16),
        (f"可见接触 {ev.n_contact}/4    |    当前动作：{ACTION_CN.get(ev.stage, '—')}",
         23, (235, 235, 235), False, 10),
        ("稳定性代理：" + ("髋部轨迹稳定" if ev.hip_stable else "髋部移动中")
         + (f"    支撑面 {len(ev.support)} 点" if len(ev.support) >= 3 else ""),
         23, (235, 235, 235), False, 10),
        ("姿态：" + meta.get("posture_cn", "—")
         + (f"    朝向比 {meta['orient']:.2f}" if meta.get("orient") is not None else "")
         + (f"    肘 L{meta['eL']:.0f}° R{meta['eR']:.0f}°"
            if meta.get("eL") is not None else ""),
         23, meta.get("posture_col", (235, 235, 235)), False, 12),
        ("落点为回放已知的实际落点，非实时预测  |  姿态为位置观察，未测量发力",
         19, (135, 195, 250), False, 12),
    ]
    heights = [txt.size(s, sz, b)[1] + gap for s, sz, _, b, gap in rows]
    ph = sum(heights) + 18
    tone = STAGE_TONE.get(ev.stage, C_OK) if ev.ok else C_DIM
    out[h - ph:, :] = cv2.addWeighted(
        out[h - ph:, :], 0.12, np.full((ph, w, 3), C_PANEL, np.uint8), 0.88, 0)
    cv2.line(out, (0, h - ph), (w, h - ph), tone, 3)

    yy = h - ph + 12
    for (s, sz, col, bold, gap), hh in zip(rows, heights):
        labels.append((22, yy, s, sz, col, bold))
        yy += hh
    return txt.draw(out, labels)
