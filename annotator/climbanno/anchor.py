"""事件锚定与归一化口径。compare.py（动态）和 card.py（静态）共用。

两条口径上的决定，写在这里而不是散在两个产物里：

**T0 ＝ 高脚建立「持续」接触的时刻。** 取最长一段连续 contact 的起点。
单次状态跳变不能用：out5 全片 8.6 秒里 RF 的接触状态变化 15 次，最抖的
1 秒内变了 8 次；6 段连续接触里有 4 段短于 0.25 秒，最长的一段 4.57 秒
才是真正踩实的那次。

**一切以承重踝为参考点，再除以躯干长。** 承重脚踩在固定岩点上，用它当原点，
镜头平移被精确抵消（本片镜头漂移达 183px），归一后数字能跨素材、跨机位、
跨人比较。绝不输出像素值：机位近 20%，同一个动作的像素数就差 20%，
那个数字换一段素材就作废。承重踝本身有 ±26px 抖动，先做中位滤波再用。
"""
from __future__ import annotations

import json
import pathlib
import sys

import cv2
import numpy as np

NOSE = 0
L_SHO, R_SHO, L_HIP, R_HIP, L_KNE, R_KNE, L_ANK, R_ANK = \
    11, 12, 23, 24, 25, 26, 27, 28


def medf(a, w=7):
    """中位滤波：去掉关键点抖动，保留镜头跟随这种慢变化。"""
    out = a.copy()
    for i in range(len(a)):
        s = a[max(0, i - w // 2):i + w // 2 + 1]
        s = s[np.isfinite(s)]
        if len(s):
            out[i] = np.median(s)
    return out


# 当前管线一定会写出的字段。缺了就说明这个目录是旧版本跑的。
FRESH_KEYS = ("pose_reliable_rate", "analyzable_windows")


def check_fresh(outdir):
    """旧目录会安静地给出不一样的数字——必须吵出来，而且要**能被程序读到**。

    out5 和 out6 是同一段视频的两次运行，关键点最大差 98px。用错了目录，
    +2.0s 的高度变化是 -0.50 还是 -0.38，全看你打了哪个数字，而且不报错。

    **返回缺失字段列表；空列表 = 这个目录是当前管线跑的。**
    在这之前它只 print 到 stderr、返回 None（qa/缺陷清单.md D-001）：
    调用方既不能 `if stale:` 也 catch 不到，`2>/dev/null` 或 notebook 里跑
    直接把这条防线整个吞掉。告警照旧发（有人在看终端时它仍然有用），
    但「要不要相信这个目录」现在是一个程序能判断的值。

    注意：`summary.json` 不存在时返回 `[]` 且一个字都不说——那是 D-002，
    本轮没动。**别把这个 `[]` 当成「目录新鲜」**：它只表示「没查到缺字段」。
    """
    p = pathlib.Path(outdir) / "summary.json"
    if not p.exists():
        return []
    s = json.loads(p.read_text(encoding="utf-8"))
    miss = [k for k in FRESH_KEYS if s.get(k) is None]
    if miss:
        print(f"[警告] {outdir}/summary.json 缺少 {'、'.join(miss)}——"
              f"这是旧版管线的输出，数字与当前管线不一致。请重跑 annotate.py。",
              file=sys.stderr)
    return miss


def require_fresh(outdir, why):
    """**会写进知识库的路径上用这个**：陈旧目录直接中断，不给「喊一声照常放行」。

    分界线（qa/缺陷清单.md D-001）：**会写进知识库的路径硬失败，只出图的路径告警。**
    渲染错一张卡片，重跑就是；写进 `kb/cases/*.md` 的数字会被后面所有分析引用，
    而且看不出它是哪一版跑的。所以 `compare.py` / `card.py` 仍然只走 check_fresh，
    `make_case.py` 走这里。

    `why` 说明「接下来要干什么」，直接进中止信息——中止信息要能一眼看出
    停下来的是哪一步。
    """
    miss = check_fresh(outdir)
    if miss:
        raise SystemExit(
            f"[中止] {outdir} 是旧版管线的输出（缺 {'、'.join(miss)}），"
            f"{why}会把旧版数字写进知识库，而且事后从版本里看不出来。\n"
            f"        请先重跑 annotate.py；确实要用旧目录就显式加 "
            f"--allow-stale（放行会写进案例的 versions 块）。")
    return miss


def load(outdir, video, foot=R_ANK, limb="RF"):
    # 探索性路径：只告警不中断（D-001 的分界线）。硬失败见 require_fresh()。
    check_fresh(outdir)
    d = np.load(pathlib.Path(outdir) / "keypoints.npz")
    xy, com = d["xy"], d["com"]
    fps = float(d["fps"]) if "fps" in d else 30.0
    ev = [json.loads(x) for x in
          (pathlib.Path(outdir) / "evidence.jsonl").open(encoding="utf-8")]
    st = [{c["limb"]: c["state"] for c in e["contacts"]} for e in ev]

    ax, ay = medf(xy[:, foot, 0]), medf(xy[:, foot, 1])
    torso = medf(np.linalg.norm((xy[:, L_SHO] + xy[:, R_SHO]) / 2 -
                                (xy[:, L_HIP] + xy[:, R_HIP]) / 2, axis=1))
    cap = cv2.VideoCapture(video)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()

    best, i = (0, 0), 0
    while i < len(st):
        if st[i].get(limb) == "contact":
            j = i
            while j < len(st) and st[j].get(limb) == "contact":
                j += 1
            if j - i > best[1] - best[0]:
                best = (i, j)
            i = j
        else:
            i += 1
    t0, t_end = best
    return {"xy": xy, "com": com, "frames": frames, "fps": fps, "torso": torso,
            "ax": ax, "ay": ay, "t0": t0, "t_end": t_end,
            "n": min(len(frames), len(xy)),
            "dx": (com[:, 0] - ax) / torso,      # 水平：力的方向对不对
            "dy": (ay - com[:, 1]) / torso}      # 垂直：腿站起来了多少


def idx(s, dt):
    """T0 之后 dt 秒对应的帧号。"""
    return min(s["t0"] + int(round(dt * s["fps"])), s["n"] - 1)


def rise(s, i):
    """第 i 帧相对 T0 的高度变化（倍躯干长）。"""
    return s["dy"][i] - s["dy"][s["t0"]]


def ghost_xy(s, i):
    """踩实瞬间的重心，换算到第 i 帧的画面坐标——这样镜头漂移被抵消。"""
    t0 = s["t0"]
    return (s["ax"][i] + s["dx"][t0] * s["torso"][i],
            s["ay"][i] - s["dy"][t0] * s["torso"][i])


def crop_box(s, aspect, times):
    """框住这些时刻里所有要画的东西：躯干、腿、重心、残影。"""
    pts = []
    for dt in times:
        i = idx(s, dt)
        for k in (NOSE, L_SHO, R_SHO, L_HIP, R_HIP, L_KNE, R_KNE,
                  L_ANK, R_ANK):        # 含头顶：人升起来时不能把脑袋裁掉
            if np.isfinite(s["xy"][i, k]).all():
                pts.append(s["xy"][i, k])
        if np.isfinite(s["com"][i]).all():
            pts.append(s["com"][i])
        pts.append(np.array(ghost_xy(s, i)))
    p = np.array(pts)
    h, w = s["frames"][0].shape[:2]
    x0, x1, y0, y1 = p[:, 0].min(), p[:, 0].max(), p[:, 1].min(), p[:, 1].max()
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    bh = (y1 - y0) * 1.18
    bw = max(bh * aspect, (x1 - x0) * 1.45)
    return _fit(cx, cy, bw, bw / aspect, w, h, aspect)


def _fit(cx, cy, bw, bh, w, h, aspect):
    if bw > w:
        bw, bh = w, w / aspect
    if bh > h:
        bh, bw = h, h * aspect
    cx = min(max(cx, bw / 2), w - bw / 2)
    cy = min(max(cy, bh / 2), h - bh / 2)
    return (int(cx - bw / 2), int(cy - bh / 2),
            int(cx + bw / 2), int(cy + bh / 2))


def common_boxes(srcs, aspect, times):
    """多段取同一个框尺寸：比例尺不同的话，几段之间就没法直接比大小。"""
    raw = [crop_box(s, aspect, times) for s in srcs]
    bw = max(b[2] - b[0] for b in raw)
    out = []
    for s, b in zip(srcs, raw):
        h, w = s["frames"][0].shape[:2]
        if bw > w or bw / aspect > h:
            out.append(b)
            continue
        out.append(_fit((b[0] + b[2]) / 2, (b[1] + b[3]) / 2,
                        bw, bw / aspect, w, h, aspect))
    return out


GHOST = (150, 150, 150)       # 踩实瞬间的重心位置——中性灰，不占序列色


def draw_marks(s, i, col, ghost=True):
    """在第 i 帧上画出被测量的两个量，返回原分辨率的标注帧。

    铅垂线到重心的**水平**箭头 ＝ 力的方向对不对；
    残影到重心的**垂直**箭头 ＝ 从踩实到现在，腿把人送高了多少。
    覆盖在花墙面上，每一笔都先画暗包边再画本体，否则会糊掉。
    """
    from climbanno.viz import CASE, cased

    img = s["frames"][i].copy()
    a = (int(s["ax"][i]), int(s["ay"][i]))
    c = s["com"][i]
    if not np.isfinite(c).all():
        return img
    c = (int(c[0]), int(c[1]))
    g = ghost_xy(s, i)
    g = (int(g[0]), int(g[1]))

    cased(lambda k, t: cv2.line(img, (a[0], min(c[1], g[1]) - 70), a, k, t,
                                cv2.LINE_AA), col, 7, 3)
    cased(lambda k, t: cv2.circle(img, a, 13, k, t, cv2.LINE_AA), col, 8, 4)
    cased(lambda k, t: cv2.arrowedLine(img, c, (a[0], c[1]), k, t,
                                       cv2.LINE_AA, tipLength=0.2), col, 8, 4)
    if ghost:
        for k in range(0, 360, 30):
            cv2.ellipse(img, g, (13, 13), 0, k, k + 16, CASE, 6, cv2.LINE_AA)
            cv2.ellipse(img, g, (13, 13), 0, k, k + 16, GHOST, 3, cv2.LINE_AA)
        if abs(c[1] - g[1]) > 34:
            tip = c[1] - 16 * np.sign(c[1] - g[1])      # 收在圆点外侧
            cased(lambda k, t: cv2.arrowedLine(img, g, (g[0], int(tip)), k, t,
                                               cv2.LINE_AA, tipLength=0.16),
                  col, 13, 7)
    cv2.circle(img, c, 12, CASE, -1, cv2.LINE_AA)
    cv2.circle(img, c, 9, (255, 255, 255), -1, cv2.LINE_AA)
    return img


def crop_to(img, box, w_out, h_out):
    x0, y0, x1, y1 = box
    return cv2.resize(img[y0:y1, x0:x1], (w_out, h_out))
