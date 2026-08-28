"""覆盖渲染。

信息设计的一条原则：**每个视觉元素都要能说清自己是观察还是推断。**

  橙圈 = 检测到的岩点（视觉流观察）
  绿圈 = 接触代理已确认（双流融合推断，不是力学接触）
  黄圈 = 可能接触（证据较弱）
  青点 = 姿态关键点（姿态流观察）
  品红 = 2D 质心代理（由关键点推算，不是三维重心）

底部面板固定保留一行「未测量」声明。这不是免责声明，是产品纪律：
知识库规范 05 节要求表达强度随证据等级变化，看不准就说看不准。
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
C_HOLD = (60, 170, 255)      # 橙 —— 岩点
C_CONF = (90, 230, 90)       # 绿 —— 已确认接触
C_POSS = (60, 220, 240)      # 黄 —— 可能接触
C_BONE = (200, 220, 80)      # 青黄 —— 骨架
C_KP = (240, 220, 120)       # 青 —— 关键点
C_COM = (220, 60, 220)       # 品红 —— 质心代理
C_PANEL = (22, 20, 18)

STAGE_CN = {
    "contact_stabilization": "接触稳定",
    "limb_transport": "单肢转移",
    "multi_limb_transition": "多肢过渡",
    "low_contact_count": "接触点不足",
    "transition": "过渡",
    "no_pose": "未检出姿态",
}
LAYOUT_CN = {"toward_left": "偏左", "toward_right": "偏右",
             "centered": "居中", "unknown": "不确定"}


class Text:
    """PIL 文字渲染，缓存字体。"""

    def __init__(self):
        self._c = {}

    def font(self, size, bold=True):
        k = (size, bold)
        if k not in self._c:
            self._c[k] = ImageFont.truetype(FONT if bold else FONT_R, size)
        return self._c[k]

    def draw(self, bgr, items):
        """items: [(x, y, text, size, (b,g,r), bold)]"""
        img = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(img)
        for x, y, t, s, c, *rest in items:
            bold = rest[0] if rest else True
            d.text((x, y), t, font=self.font(s, bold), fill=(c[2], c[1], c[0]))
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def draw_frame(bgr, frame, ev, holds_xy, txt: Text, *, meta: dict) -> np.ndarray:
    h, w = bgr.shape[:2]
    out = bgr.copy()
    labels = []

    contacted = {c.hold: c for c in ev.contacts if c.hold and c.state != "none"}
    legend_box = (w - 160, 8, w, 8 + 24 * 4 + 14)     # 图例占位，标签避开

    def chip(x, y, tw, th, alpha=0.55):
        """给文字垫一层半透明底，避免落在花墙上看不清。"""
        x0, y0 = max(0, x - 3), max(0, y - 2)
        x1, y1 = min(w, x + tw + 3), min(h, y + th + 2)
        if x1 <= x0 or y1 <= y0:
            return
        roi = out[y0:y1, x0:x1]
        out[y0:y1, x0:x1] = cv2.addWeighted(
            roi, 1 - alpha, np.full_like(roi, (18, 16, 14), np.uint8), alpha, 0)

    def clear_of_legend(x, y, tw, th):
        lx0, ly0, lx1, ly1 = legend_box
        return not (x < lx1 and x + tw > lx0 and y < ly1 and y + th > ly0)

    # ---- 岩点 ----
    for hid, (x, y) in holds_xy.items():
        x, y = int(x), int(y)
        r = int(meta["hold_r"].get(hid, 22))
        c = contacted.get(hid)
        if c is None:
            cv2.circle(out, (x, y), r, C_HOLD, 2, cv2.LINE_AA)
            lx, ly, tw, th = x + r + 3, y - 9, 34, 18
            if clear_of_legend(lx, ly, tw, th):
                chip(lx, ly, tw, th, 0.45)
                labels.append((lx, ly, hid, 15, C_HOLD, False))
        else:
            col = C_CONF if c.state == "confirmed" else C_POSS
            cv2.circle(out, (x, y), r + 4, col, 3, cv2.LINE_AA)
            s = f"{hid}·{LIMB_CN[c.limb]}"
            lx, ly = x + r + 6, y - 22
            if lx + 90 > w:                      # 右侧放不下就翻到左边
                lx = max(2, x - r - 96)
            chip(lx, ly, 88, 22)
            labels.append((lx, ly, s, 17, col))

    # ---- 骨架 ----
    if frame.ok:
        for a, b in SKELETON:
            pa, pb = frame.pt(a), frame.pt(b)
            if pa and pb:
                cv2.line(out, tuple(map(int, pa)), tuple(map(int, pb)),
                         C_BONE, 2, cv2.LINE_AA)
        for i in range(33):
            p = frame.pt(i)
            if p:
                cv2.circle(out, tuple(map(int, p)), 3, C_KP, -1, cv2.LINE_AA)

        # 肢端加粗，并标出运动中的肢体
        for limb, li in LIMB_POINTS.items():
            p = frame.pt(li)
            if not p:
                continue
            p = tuple(map(int, p))
            st = next((c.state for c in ev.contacts if c.limb == limb), "none")
            col = C_CONF if st == "confirmed" else C_POSS if st == "possible" else (150, 150, 150)
            cv2.circle(out, p, 8, col, 2, cv2.LINE_AA)
            if limb in ev.moving_limbs:
                cv2.circle(out, p, 15, (80, 120, 255), 2, cv2.LINE_AA)

        # 2D 质心代理 + 髋部（知识库指定的重心视觉代理）
        if frame.hip:
            hp = tuple(map(int, frame.hip))
            cv2.drawMarker(out, hp, (255, 200, 80), cv2.MARKER_CROSS, 16, 2, cv2.LINE_AA)
        if frame.com:
            cp = tuple(map(int, frame.com))
            cv2.circle(out, cp, 11, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(out, cp, 8, C_COM, -1, cv2.LINE_AA)

    # ---- 底部证据面板 ----
    ph = 132
    panel = out[h - ph:, :].copy()
    out[h - ph:, :] = cv2.addWeighted(panel, 0.25,
                                      np.full_like(panel, C_PANEL, np.uint8), 0.75, 0)
    cv2.line(out, (0, h - ph), (w, h - ph), (70, 200, 255), 2)

    stage = STAGE_CN.get(ev.stage, ev.stage)
    tone = C_CONF if ev.ok else (120, 120, 120)
    y0 = h - ph + 8
    labels += [
        (14, y0, f"攀爬证据  t={ev.t:5.2f}s  帧{ev.idx:03d}", 19, (240, 240, 240)),
        (14, y0 + 28, f"阶段 {stage}", 21, tone),
        (150, y0 + 30, f"已确认接触 {ev.confirmed}/4    可能接触 {ev.possible}/4"
                       f"    {'整体静止' if ev.kinematic_still else '运动中'}", 17, (225, 225, 225)),
        (14, y0 + 60, f"视觉布局 质心{LAYOUT_CN.get(ev.layout, ev.layout)}"
                      f"    质心速度 {ev.com_speed:.2f} 躯干长/秒"
                      + (f"    运动肢体 {'、'.join(LIMB_CN[m] for m in ev.moving_limbs)}"
                         if ev.moving_limbs else ""), 16, (200, 200, 200), False),
        (14, y0 + 86, "2D 接触代理｜未测量接触力、负荷分配与髋墙度量距离",
         16, (120, 190, 250), False),
    ]

    # ---- 右上角图例 ----
    lg = [("岩点", C_HOLD), ("已确认接触", C_CONF), ("可能接触", C_POSS),
          ("2D 质心代理", C_COM)]
    lx0, ly0, lx1, ly1 = legend_box
    cv2.rectangle(out, (lx0, ly0), (lx1 - 4, ly1), C_PANEL, -1)
    cv2.rectangle(out, (lx0, ly0), (lx1 - 4, ly1), (60, 60, 60), 1)
    for i, (name, col) in enumerate(lg):
        yy = ly0 + 18 + i * 24
        cv2.circle(out, (lx0 + 14, yy), 7, col, 2, cv2.LINE_AA)
        labels.append((lx0 + 28, yy - 10, name, 15, col, False))

    return txt.draw(out, labels)
