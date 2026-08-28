#!/usr/bin/env python3
"""T00 · 交叉验证：无视频加载器与真 `anchor.load()` 必须逐位相同。

整套数值基线建立在 `qalib.load_nv()` 上，因为原始视频存在容器级目录里、
会随容器回收消失，而且是可识别的真人影像，不能进 git。

`load_nv()` 只是 `anchor.load()` 摘掉读帧那一段的版本，但「只是」这两个字
需要证据。本用例在**视频还在**的机器上把两者跑一遍逐位比对；
视频不在时整条用例 SKIP——它是一次性的取证，不是常驻门禁。

2026-08-28 的取证结果记在 qa/报告/2026-08-28.md：
out5 / out7 上 t0、t_end、n、fps 完全相同，dx / dy / torso / ax / ay
五条序列的最大绝对差均为 0.0，NaN 位置一致。
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import qalib as Q                                            # noqa: E402


def run():
    from climbanno import anchor

    r = Q.Runner("T00 无视频加载器交叉验证")

    for d in ("out5", "out7"):
        c = r.case(f"{d}: load_nv 与 anchor.load 逐位相同")
        s = json.loads((Q.FIXTURES / d / "summary.json").read_text(encoding="utf-8"))
        video = (s.get("source") or {}).get("video")
        if not video or not pathlib.Path(video).exists():
            r.skip(f"原视频不在本机（{video}）——这是预期的，基线不依赖它")
            continue
        # 真 load() 读的是 annotator/ 下的原目录；fixtures 是它的副本，
        # 四类文件哈希已在 T01 钉死，所以两边的输入是同一份。
        real = anchor.load(str(Q.ANNOTATOR / d), video)
        nv = Q.load_nv(Q.FIXTURES / d)
        for k in ("t0", "t_end", "n", "fps"):
            r.eq(nv[k], real[k], f"{d}.{k}")
        for k in ("dx", "dy", "torso", "ax", "ay"):
            a, b = np.asarray(real[k], float), np.asarray(nv[k], float)
            r.eq(a.shape, b.shape, f"{d}.{k} 形状")
            r.eq(np.array_equal(np.isnan(a), np.isnan(b)), True,
                 f"{d}.{k} NaN 位置一致")
            md = float(np.nanmax(np.abs(a - b))) if a.size else 0.0
            r.eq(md, 0.0, f"{d}.{k} 最大绝对差")
        for t in (0.4, 0.5, 0.8, 1.0, 1.5, 2.0):
            r.eq(anchor.rise(nv, anchor.idx(nv, t)),
                 anchor.rise(real, anchor.idx(real, t)),
                 f"{d}: +{t:.1f}s 的 rise")
    return r.report()


if __name__ == "__main__":
    Q.main_guard(run)
