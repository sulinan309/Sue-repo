#!/usr/bin/env python3
"""T04 · 口径一致性：知识库案例的 measured 必须与管线重算逐项相同。

QA 章程点名的既有先例：「案例单元的 `measured` 与 `compare.py` 输出曾用不同口径」。
`make_case.py --update-measured` 的设计意图是消灭这件事——知识库里的数字必须和
产物出自**同一条代码路径**，否则「0.45」会在 README、卡片和 KB 里慢慢变成三个数。

本用例不重写那条路径，而是**直接调用 `make_case.collect()` 与
`make_case.anchor_measures()`**，只把里面读视频的 `anchor.load` 换成
无视频版本（数值已证明逐位相同，见 T02 与测试报告）。
所以测的是真的 make_case 口径，不是我复述的口径。

三层：
  1. measured 块 vs 管线重算 —— 必须逐项相等
  2. measured 块 vs summary.json —— 检出率/可信率/可分析区间同源
  3. facts 与正文里的叙述数字 vs measured —— 人手写的那几行最容易漂
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import yaml

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import qalib as Q                                            # noqa: E402

CASES = {                       # 案例 -> fixture 目录
    "CASE-2608-001": "out5",
    "CASE-2608-002": "out7",
}
CASE_DIR = Q.KB / "kb" / "cases"

# 已知正文与 measured 口径不一致的案例（缺陷 D-003）。修好一个就从这里删一个，
# 删晚了会 XPASS 报警，删早了会硬失败——两个方向都会响。
NARRATIVE_MISMATCH = {"CASE-2608-002"}


def split_front(path):
    raw = pathlib.Path(path).read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if not m:
        raise AssertionError(f"{path} 没有 YAML front matter")
    return yaml.safe_load(m.group(1)), m.group(2)


def unquote_keys(d):
    """anchor_measures 为了 YAML 安全把键写成 '"+0.5s"'，解析回来是 +0.5s。"""
    return {k.strip('"'): v for k, v in d.items()}


def flat(d, pre=""):
    out = {}
    for k, v in d.items():
        key = f"{pre}{k}"
        if isinstance(v, dict):
            out.update(flat(unquote_keys(v), key + "."))
        else:
            out[key] = v
    return out


def run():
    Q.patch_anchor_load()
    import make_case

    r = Q.Runner("T04 案例单元口径一致性")

    for cid, outdir in CASES.items():
        p = CASE_DIR / f"{cid}.md"
        fx = Q.FIXTURES / outdir
        fm, body = split_front(p)

        # --- 1. measured vs 管线重算 ---------------------------------------
        c = r.case(f"{cid} · measured 与 make_case 重算逐项相同（源：{outdir}）")
        recomputed = make_case.collect(fx)[0]
        recomputed.update(make_case.anchor_measures(fx, None))
        got, want = flat(fm.get("measured") or {}), flat(recomputed)
        r.eq(sorted(got), sorted(want), f"{cid}: measured 的字段集合")
        for k in sorted(set(got) & set(want)):
            r.eq(got[k], want[k], f"{cid}: measured.{k}")

        # --- 2. measured vs summary.json ----------------------------------
        c = r.case(f"{cid} · 检出率/可信率/可分析区间与 summary.json 同源")
        s = json.loads((fx / "summary.json").read_text(encoding="utf-8"))
        m = fm.get("measured") or {}
        r.eq(m.get("姿态检出率"), s.get("pose_rate"), f"{cid}: 姿态检出率")
        r.eq(m.get("姿态可信率"), s.get("pose_reliable_rate"), f"{cid}: 姿态可信率")
        r.eq(m.get("可分析区间"), s.get("analyzable_windows"),
             f"{cid}: 可分析区间")
        v = fm.get("video") or {}
        src = s.get("source") or {}
        r.eq(v.get("frames"), src.get("frames"), f"{cid}: video.frames")
        r.eq(float(v.get("fps")), float(src.get("fps")), f"{cid}: video.fps")
        r.eq(v.get("size"), src.get("size"), f"{cid}: video.size")
        r.eq(v.get("file"), pathlib.Path(src.get("video", "")).name.split("-")[0]
             + ".mp4", f"{cid}: video.file 与 summary.source.video 指向同一段")

        # --- 3. 管线生成的 facts 必须仍在案例里 -----------------------------
        c = r.case(f"{cid} · 管线生成的 facts 仍逐条出现在案例里")
        gen_facts = make_case.collect(fx)[1]
        have = set(fm.get("facts") or [])
        for f in gen_facts:
            r.check(f in have, f"{cid}: facts 含「{f}」", f in have, True)

        # --- 4. 叙述里的数字 vs measured ------------------------------------
        # 这一层是人手写的，也是最容易和 measured 漂开的一层。
        c = r.case(f"{cid} · facts 与正文的叙述数字回指 measured")
        anchor_m = unquote_keys(m.get("相对承重脚高度变化") or {})
        text = "\n".join(fm.get("facts") or []) + "\n" + body
        rules = [
            (r"踩实高脚锚点 T0=([\d.]+)s", m.get("踩实锚点秒"), "T0"),
            (r"其后持续接触 ([\d.]+) 秒", m.get("踩实后持续接触秒"), "持续接触秒"),
            (r"踩实瞬间重心横向偏出 ([\d.]+) 倍躯干长",
             m.get("踩实时横向偏"), "踩实时横向偏"),
            (r"T0 起 2\.0 秒内横向偏移中位 ([\d.]+) 倍躯干长",
             (m.get("横向偏移") or {}).get("中位"), "横向偏移中位"),
        ]
        for pat, want_v, label in rules:
            hits = re.findall(pat, text)
            r.check(len(hits) >= 1, f"{cid}: 正文里找得到「{label}」", hits, "≥1 处")
            for h in hits:
                r.close(float(h), want_v, 0.005,
                        f"{cid}: 叙述里的 {label}={h} 与 measured 一致")

        # 「T0 起 2.0 秒内相对承重脚高度变化」——两处口径不同，见缺陷 D-003
        #
        #   measured["+2.0s"] = rise(idx(s, 2.0)) = 第 T0+60 帧的点采样
        #   叙述里的数字        = 60 帧窗口 range(60) 的末帧，即 T0+59
        #
        # 差一帧。out5 上两者都四舍五入到 -0.50，看不出来；
        # out7 上是 +0.99 对 +0.97，同一个案例的 measured 和正文各说各的。
        c = r.case(f"{cid} · 「T0 起 2.0 秒内高度变化」口径（缺陷 D-003）")
        from climbanno import anchor
        s_nv = Q.load_nv(fx)
        point = Q.r2(anchor.rise(s_nv, anchor.idx(s_nv, 2.0)))       # T0+60
        win_last = Q.r2(anchor.rise(s_nv, s_nv["t0"] + 59))          # T0+59
        hits = re.findall(
            r"T0 起 2\.0 秒内相对承重脚高度变化 ([+\-−][\d.]+) 倍躯干长", text)
        r.check(len(hits) == 1, f"{cid}: 该表述出现 1 次", hits, "1 处")
        r.close(point, anchor_m.get("+2.0s"), 1e-9,
                f"{cid}: measured 的 +2.0s 就是 T0+60 点采样")
        told = float(hits[0].replace("−", "-")) if hits else None
        matches_measured = told is not None and abs(told - point) <= 0.005
        matches_window = told is not None and abs(told - win_last) <= 0.005
        if cid in NARRATIVE_MISMATCH:
            r.known_defect(
                matches_measured, "D-003",
                f"{cid}: 正文写 {told:+.2f}（＝T0+59 窗口末帧），"
                f"measured 写 {point:+.2f}（＝T0+60 点采样）")
            r.check(matches_window, f"{cid}: 正文的数字来自 60 帧窗口末帧（复现路径）",
                    told, win_last)
        else:
            r.close(told, point, 0.005,
                    f"{cid}: 正文数字与 measured 的 +2.0s 一致")

    # --- 5. 两个案例之间的配对数字 ----------------------------------------
    c = r.case("配对论断：最小间距 0.37、各 57 帧同号")
    fm2, body2 = split_front(CASE_DIR / "CASE-2608-002.md")
    txt = "\n".join(fm2.get("facts") or []) + "\n" + body2
    base = Q.read_baseline("anchor_golden.json")
    r.check(base is not None, "T02 的锚点基线已存在", base is not None, True)
    if base:
        gap = base["pair"]["最小间距"]
        hits = re.findall(r"最小间距 ([\d.]+) 倍躯干长", txt)
        r.check(len(hits) >= 1, "案例正文写了最小间距", hits, "≥1 处")
        for h in hits:
            r.close(float(h), gap, 0.005, f"案例里的最小间距 {h} 与重算一致")
        for pat, want_v, label in (
                (r"失败那 (\d+) 帧\*\*全部为负\*\*", base["pair"]["窗口帧数"], "失败侧帧数"),
                (r"本例 (\d+) 帧\*\*全部为正\*\*", base["pair"]["窗口帧数"], "成功侧帧数")):
            hits = re.findall(pat, txt)
            r.check(len(hits) >= 1, f"案例正文写了{label}", hits, "≥1 处")
            for h in hits:
                r.eq(int(h), want_v, f"{label}={h}")

    c = r.case("互指完整：paired_with 双向")
    fm1, _ = split_front(CASE_DIR / "CASE-2608-001.md")
    r.eq(fm1.get("paired_with"), "CASE-2608-002", "001 指向 002")
    r.eq(fm2.get("paired_with"), "CASE-2608-001", "002 指向 001")

    # --- CASE-2608-003：评测集的第一条「易误判」样本 ----------------------
    # 它整份 measured 都来自 annotator/out7（＝ qa/fixtures/out7）的
    # npz + evidence.jsonl，所以可以完全脱离视频重算。这里挑四个不依赖
    # 「放开阈值的 detect_bent_adjust」的量核对——那部分改了阈值跑，
    # 本轮不复现（见测试计划「明确不测什么」）。
    p3 = CASE_DIR / "CASE-2608-003.md"
    c = r.case("CASE-2608-003 · 可重算的量与 fixtures/out7 一致")
    if not p3.exists():
        r.skip("CASE-2608-003 不存在")
    else:
        from climbanno import pose
        fm3, _ = split_front(p3)
        m3 = fm3.get("measured") or {}
        fr3, fps3 = Q.frames_from_npz(Q.FIXTURES / "out7")
        s7 = json.loads((Q.FIXTURES / "out7" / "summary.json")
                        .read_text(encoding="utf-8"))
        r.eq(fm3.get("versions", {}).get("source_dir"), "annotator/out7",
             "声明的来源目录就是 out7")
        r.eq(m3.get("姿态可信率"), s7["pose_reliable_rate"], "姿态可信率")
        r.eq(m3.get("可分析区间"), s7["analyzable_windows"], "可分析区间")
        el = m3.get("肘角可信率") or {}
        for cn, joint in (("左", "L_ELBOW"), ("右", "R_ELBOW")):
            got = round(float(pose.joint_reliability(fr3, joint).mean()), 2)
            r.eq(el.get(cn), got, f"{cn}肘角可信率")
        ct3 = Q.contacts_from_evidence(Q.FIXTURES / "out7")
        import numpy as np
        for seg in m3.get("脚离点段") or []:
            a, b = seg["帧区间"]
            other = "RF" if seg["脚"] == "左" else "LF"
            rate = float(np.mean([ct3[other][i] == "contact"
                                  for i in range(a, b)]))
            r.close(seg["另一只脚接触率"], rate, 1e-9,
                    f"帧 {a}-{b}：另一只脚接触率")
        lo = int(round(m3["可分析区间"][0][0] * fps3))
        hi = min(int(round(m3["可分析区间"][0][1] * fps3)), len(ct3["LF"]))
        both = sum(1 for i in range(lo, hi)
                   if ct3["LF"][i] != "contact" and ct3["RF"][i] != "contact")
        r.eq(m3.get("可分析区间内双脚同时非接触帧"), [both, hi - lo],
             "可分析区间内双脚同时非接触帧 [满足数, 总数]")
    return r.report()


if __name__ == "__main__":
    Q.main_guard(run)
