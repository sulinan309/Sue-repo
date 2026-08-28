"""对比图的公共绘图层：调色板、文字排版、基本图元。

compare.py（动态）和 card.py（静态）共用这一份。分成两份写过一次，
结果调色板改了一边没改另一边——两个产物的同一个量用了不同的颜色。

配色不是挑出来的，是验出来的（dataviz 六项检查，深色底 #101112）：
「成功＝绿、失败＝红」最顺手，但红绿在红绿色盲下 ΔE 只有 4.1，两块颜色
根本分不开，低于 6–8 的下限带，加辅助编码也救不回。改用分类槽位 1/2
（蓝 #3987e5、橙 #d95926）：CVD ΔE 26.8、常视 31.8、对比度均过 3:1。
身份另有直接标签兜底，任何一处都不靠颜色单独承担。
"""
from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

# —— 调色板（BGR）——
SURFACE = (18, 17, 16)        # #101112  页面底
CARD = (25, 26, 26)           # #1a1a19  卡片面
FAIL = (38, 89, 217)          # #d95926  分类槽位 2 橙 —— 没站起来
OK = (229, 135, 57)           # #3987e5  分类槽位 1 蓝 —— 站起来了
INK1 = (255, 255, 255)        # #ffffff  主墨
INK2 = (183, 194, 195)        # #c3c2b7  次墨
INKM = (129, 135, 137)        # #898781  弱墨（轴、注解）
GRID = (42, 44, 44)           # #2c2c2a  网格发丝线
AXIS = (53, 56, 56)           # #383835  基线
CASE = (12, 12, 12)           # 覆盖在视频上的标记包边色

BAR_H = 22                    # 条 ≤24px，留白比填满好看
CAP_R = 4                     # 数据端 4px 圆角，基线端方角

NO_START = "。，、；：？！）】》」』·…%"   # 避头尾：这些字符不另起一行


class T:
    """文字层：整帧只做一次 BGR→PIL→BGR，标签先攒后画。"""

    def __init__(self):
        self._c = {}

    def f(self, s, bold=True):
        k = (s, bold)
        if k not in self._c:
            self._c[k] = ImageFont.truetype(FONT_B if bold else FONT_R, s)
        return self._c[k]

    def w(self, t, s, bold=True):
        return self.f(s, bold).getlength(t)

    def vc(self, t, cy, s, bold=True):
        """返回让文字在 cy 处垂直居中的绘制 y。"""
        b = self.f(s, bold).getbbox(t)
        return cy - (b[1] + b[3]) / 2

    def draw(self, bgr, items):
        im = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(im)
        for x, y, s, sz, c, *r in items:
            d.text((x, y), s, font=self.f(sz, r[0] if r else True),
                   fill=(c[2], c[1], c[0]))
        return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def wrap(txt, s, size, bold, width):
    """按实测宽度断行。文字宁可多占一行，也不能被画布切掉。"""
    lines, cur = [], ""
    for ch in s:
        if not cur or txt.w(cur + ch, size, bold) <= width:
            cur += ch
        elif ch in NO_START:
            lines.append(cur + ch)
            cur = ""
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def rbar(img, x0, y0, x1, y1, col, r=CAP_R):
    """从基线长出的横条：基线端方角，数据端 r 圆角。"""
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    if x1 - x0 <= r:
        cv2.rectangle(img, (x0, y0), (max(x1, x0 + 1), y1), col, -1)
        return
    cv2.rectangle(img, (x0, y0), (x1 - r, y1), col, -1, cv2.LINE_AA)
    cv2.rectangle(img, (x1 - r, y0 + r), (x1, y1 - r), col, -1, cv2.LINE_AA)
    cv2.ellipse(img, (x1 - r, y0 + r), (r, r), 0, -90, 0, col, -1, cv2.LINE_AA)
    cv2.ellipse(img, (x1 - r, y1 - r), (r, r), 0, 0, 90, col, -1, cv2.LINE_AA)


def wash(img, x0, y0, x1, y1, col, a):
    """色相淡洗，不用饱和色块。"""
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    sub = img[y0:y1, x0:x1]
    if sub.size:
        sub[:] = (sub * (1 - a) + np.array(col, float) * a).astype(np.uint8)


def cased(fn, col, wide, thin):
    """先画暗包边再画本体——覆盖在视频上的标记靠这个脱开背景。"""
    fn(CASE, wide)
    fn(col, thin)
