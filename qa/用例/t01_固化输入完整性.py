#!/usr/bin/env python3
"""T01 · 固化输入完整性：qa/fixtures 有没有被动过。

后面所有数值基线都建立在 `qa/fixtures/` 上。如果 fixtures 本身变了而基线没变，
那基线就是在为一个不存在的输入背书——这正是「out5 换 out6」那次事故的形状，
只不过换的是输入而不是输出目录。

所以先把四类文件逐个 SHA-256 钉死，再检查结构不变量：
帧数、fps、npz 数组形状、evidence 行数三者互相对得上。

用 --bless 重新生成哈希清单（只在人确认过输入该变的时候用）。
"""
from __future__ import annotations

import json
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import qalib as Q                                            # noqa: E402

FILES = ("keypoints.npz", "evidence.jsonl", "holds.json", "summary.json")
DIRS = ("out5", "out7")
BLESS = "--bless" in sys.argv


def run():
    r = Q.Runner("T01 固化输入完整性")
    manifest = {}

    c = r.case("四类文件齐全，且不含任何视频")
    for d in DIRS:
        p = Q.FIXTURES / d
        r.check(p.is_dir(), f"{d}/ 存在", p.is_dir(), True)
        got = sorted(x.name for x in p.iterdir() if x.is_file())
        r.eq(got, sorted(FILES), f"{d}/ 的文件集合")
        for f in FILES:
            manifest[f"{d}/{f}"] = {"sha256": Q.sha256(p / f),
                                    "bytes": (p / f).stat().st_size}
    vids = list(Q.FIXTURES.rglob("*.mp4")) + list(Q.FIXTURES.rglob("*.mov"))
    r.eq([str(v) for v in vids], [], "fixtures 下没有任何视频文件")

    c = r.case("SHA-256 与基线一致")
    base = Q.read_baseline("fixtures.sha256.json")
    if base is None or BLESS:
        Q.write_baseline("fixtures.sha256.json", manifest)
        r.skip("基线首次生成（或 --bless 重建），本轮不比对")
    else:
        for k in sorted(manifest):
            r.eq(manifest[k]["sha256"], (base.get(k) or {}).get("sha256"),
                 f"{k} 的 SHA-256")
            r.eq(manifest[k]["bytes"], (base.get(k) or {}).get("bytes"),
                 f"{k} 的字节数")
        r.eq(sorted(base), sorted(manifest), "基线里的文件清单")

    c = r.case("结构不变量：帧数 / fps / 数组形状互相对得上")
    for d in DIRS:
        p = Q.FIXTURES / d
        s = json.loads((p / "summary.json").read_text(encoding="utf-8"))
        z = np.load(p / "keypoints.npz")
        n_ev = sum(1 for _ in (p / "evidence.jsonl").open(encoding="utf-8"))
        src = s.get("source") or {}
        r.eq(int(src.get("frames", -1)), len(z["xy"]),
             f"{d}: summary.source.frames == keypoints 行数")
        r.eq(n_ev, len(z["xy"]), f"{d}: evidence 行数 == keypoints 行数")
        r.eq(z["xy"].shape[1:], (33, 2), f"{d}: xy 形状为 (n,33,2)")
        r.eq(z["vis"].shape[1:], (33,), f"{d}: vis 形状为 (n,33)")
        r.eq(z["com"].shape[1:], (2,), f"{d}: com 形状为 (n,2)")
        r.eq(float(z["fps"]), float(src.get("fps")),
             f"{d}: npz.fps == summary.source.fps")
        for k in ("pose_reliable_rate", "analyzable_windows"):
            r.check(s.get(k) is not None,
                    f"{d}: summary 含当前管线字段 {k}", s.get(k), "非 None")

    # 已知缺陷 D-004：summary.source 不记录 --range 的起点。
    # out5 的原视频有 299 帧，npz 只有 258 行（跑的是 --range :8.6）。
    # 起点为 0 时凑巧对齐；起点非 0 时 anchor.load() 会拿全片第 i 帧
    # 去配 npz 第 i 行，画面和数字全部错位，且不报错。
    c = r.case("summary 是否足以还原 --range 偏移（已知缺陷 D-004）")
    for d in DIRS:
        s = json.loads((Q.FIXTURES / d / "summary.json").read_text(encoding="utf-8"))
        src = s.get("source") or {}
        has_off = any(k in src for k in ("range", "offset", "start_frame", "t0"))
        r.known_defect(has_off, "D-004",
                       f"{d}: summary.source 未记录帧偏移，"
                       f"非零 --range 的产物无法与原视频对齐")
    return r.report()


if __name__ == "__main__":
    Q.main_guard(run)
