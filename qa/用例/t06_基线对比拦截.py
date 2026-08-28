#!/usr/bin/env python3
"""T06 · 基线对比是不是真的拦得住。

annotator/README 里最刺眼的一条：

    「脚脱落与伸手同步 71%」像个发现 —— 没跑基线，基线是 78%。

review.py 存在的主要理由就是这条：攀岩视频里很多量天然高频，
不跟基线比，「本来就常见」会被当成「这个人的问题」。
**一条没过基线的观察，不是弱发现，是不是发现。**

所以本用例测的不是「review.py 能跑」，而是：

  1. 71% 对 78% 这组真实数字，**必须**被判成「不构成发现」
  2. 同样的 71%，换一个低基线就**必须**变成发现——
     证明拦截依据是基线，不是「百分比看着高不高」
  3. 判定与证据等级的映射不能松动：p ≥ 0.05 时永远不许出现「可确认事实」
  4. review.py 端到端跑在 fixtures 上的输出做哈希快照
"""
from __future__ import annotations

import hashlib
import subprocess
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import qalib as Q                                            # noqa: E402

BLESS = "--bless" in sys.argv

# annotator/README「时序类在 33 秒素材上两条候选都没有通过」那张表。
# 33 秒素材（out2）的产物不在 fixtures 里，但这两条是纯函数，可以直接复现。
HISTORY = [
    # k,  n,  base,   z,      p,      verdict,                  level
    (15, 20, 0.57, 1.63, 0.052, "样本不足，仅为倾向", "证据不足"),
    (12, 17, 0.78, -0.74, 0.770, "与基线无实质差异，不构成发现", "证据不足"),
]


def run():
    sys.path.insert(0, str(Q.ANNOTATOR))
    import review

    r = Q.Runner("T06 基线对比拦截")

    c = r.case("复现 README 里那两条候选的判定")
    for k, n, base, z, p, verdict, level in HISTORY:
        f = review.finding("x", "U", k, n, base)
        r.close(f["z"], z, 0.005, f"{k}/{n} 对基线 {base:.0%}: z")
        r.close(f["p"], p, 0.005, f"{k}/{n} 对基线 {base:.0%}: p")
        r.eq(f["verdict"], verdict, f"{k}/{n} 对基线 {base:.0%}: 判定")
        r.eq(f["evidence_level"], level, f"{k}/{n} 对基线 {base:.0%}: 证据等级")
        r.eq(f["observed"], f"{k}/{n} ({k / n * 100:.0f}%)",
             f"{k}/{n} 对基线 {base:.0%}: 观察值表述")

    c = r.case("71% 这个数本身不构成任何东西——全看基线")
    hi = review.finding("同步", "FAULT-FOOT-CUT-003", 12, 17, 0.78)
    lo = review.finding("同步", "FAULT-FOOT-CUT-003", 12, 17, 0.30)
    r.eq(hi["observed"], lo["observed"], "两次的观察值是同一个 71%")
    r.eq(hi["evidence_level"], "证据不足", "基线 78% → 证据不足")
    r.eq(lo["evidence_level"], "可确认事实", "基线 30% → 可确认事实")
    r.check("不构成发现" in hi["verdict"], "基线 78% 的判定明说不构成发现",
            hi["verdict"], "含「不构成发现」")
    r.eq(lo["verdict"], "高于基线", "基线 30% 的判定是高于基线")

    c = r.case("判定与证据等级的映射不许松动（网格扫描）")
    bad_level = bad_verdict = 0
    grid = 0
    for n in (5, 10, 17, 20, 40, 100):
        for k in range(0, n + 1):
            for b in (0.05, 0.30, 0.57, 0.78, 0.92):
                f = review.finding("x", "U", k, n, b)
                grid += 1
                sig = f["p"] < 0.05
                if (f["evidence_level"] == "可确认事实") != sig:
                    bad_level += 1
                want = ("高于基线" if sig else
                        "样本不足，仅为倾向" if f["p"] < 0.2 else
                        "与基线无实质差异，不构成发现")
                if f["verdict"] != want:
                    bad_verdict += 1
    r.eq(bad_level, 0,
         f"扫描 {grid} 组：证据等级「可确认事实」当且仅当 p<0.05")
    r.eq(bad_verdict, 0, f"扫描 {grid} 组：判定文案与 p 的三档划分一致")

    c = r.case("退化输入不许伪装成发现")
    for k, n, b, why in ((0, 0, 0.5, "样本量为 0"),
                         (5, 10, 0.0, "基线为 0（标准差为 0）"),
                         (5, 10, 1.0, "基线为 1（标准差为 0）")):
        f = review.finding("x", "U", k, n, b)
        r.eq(f["evidence_level"], "证据不足", f"{why} → 证据不足")
        r.eq(f["z"], 0.0, f"{why} → z 归零而不是 inf/nan")
        r.eq(f["p"], 1.0, f"{why} → p 取 1.0")

    c = r.case("z_test 的方向性：观察低于基线时 z 必须为负")
    z_lo, _ = review.z_test(3, 20, 0.50)
    z_hi, _ = review.z_test(17, 20, 0.50)
    r.check(z_lo < 0 < z_hi, "低于/高于基线的 z 符号相反",
            (round(z_lo, 2), round(z_hi, 2)), "一负一正")
    r.check(review.z_test(3, 20, 0.50)[1] > 0.5,
            "单尾检验：远低于基线时 p 接近 1", round(review.z_test(3, 20, 0.5)[1], 3),
            "> 0.5")

    def run_review(d):
        return subprocess.run(
            [sys.executable, "review.py", str(Q.FIXTURES / d / "evidence.jsonl")],
            cwd=str(Q.ANNOTATOR), capture_output=True, text=True)

    c = r.case("review.py 端到端：每条候选都必须带基线与 z/p")
    snap = {}
    for d in ("out5",):
        cp = run_review(d)
        r.eq(cp.returncode, 0, f"{d}: review.py 退出码")
        r.eq(cp.stderr, "", f"{d}: review.py 没有 stderr 输出")
        out = cp.stdout
        snap[d] = {"sha256": hashlib.sha256(out.encode()).hexdigest(),
                   "行数": out.count("\n"),
                   "可确认事实条数": out.count("证据等级：可确认事实"),
                   "证据不足条数": out.count("证据等级：证据不足")}
        # 每条候选发现都必须带上「基线」「z=」「p=」三样，缺一样就说明
        # 有人绕过了基线对比直接报结论。
        n_cand = out.count("知识单元 ")
        r.check(n_cand > 0, f"{d}: 至少输出了一条候选发现", n_cand, "> 0")
        for token in ("基线 ", "z=", "p="):
            r.eq(out.count(token), n_cand,
                 f"{d}: 每条候选都带 {token.strip()}（{n_cand} 条）")

    # --- 缺陷 D-007：review.py 在「结尾就是最高点」的素材上直接崩 ---------
    # posture() 用髋部最高帧把素材切成上攀/下攀两段。最高点落在最后一帧时，
    # 下攀段长度为 0，np.nanmean(空) 得 NaN，round(float(nan)) 抛 ValueError。
    # out7 正是这种素材——一次成功的 rockover，结尾就是全片最高处。
    # 也就是说：**每一段成功的尝试都跑不了 review.py。**
    c = r.case("review.py 在成功素材（结尾即最高点）上的表现（缺陷 D-007）")
    cp7 = run_review("out7")
    import numpy as np
    hip = np.load(Q.FIXTURES / "out7" / "keypoints.npz")["hip"]
    peak = int(np.nanargmin(hip[:, 1]))
    r.eq(peak, len(hip) - 1, "out7 的髋部最高帧就是最后一帧（触发条件）")
    r.known_defect(cp7.returncode == 0, "D-007",
                   f"review.py qa/fixtures/out7/evidence.jsonl 退出码 "
                   f"{cp7.returncode}，抛 ValueError: cannot convert float "
                   f"NaN to integer（review.py:134，下攀段长度为 0）")
    r.check("ValueError" in cp7.stderr,
            "崩溃形态仍是 ValueError（复现路径未变）",
            cp7.stderr.strip().splitlines()[-1] if cp7.stderr else "",
            "含 ValueError")

    c = r.case("review.py 端到端输出哈希快照（fixtures，无视频）")
    base = Q.read_baseline("review_golden.json")
    if base is None or BLESS:
        Q.write_baseline("review_golden.json", snap)
        r.skip("基线首次生成（或 --bless 重建），本轮不比对")
    else:
        for d in snap:
            for k in snap[d]:
                r.eq(snap[d][k], base.get(d, {}).get(k), f"{d}.{k}")
    return r.report()


if __name__ == "__main__":
    Q.main_guard(run)
