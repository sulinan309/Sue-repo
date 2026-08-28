"""测试公共库：不依赖视频的加载器 + 极简断言框架。

## 为什么要有这个文件

`climbanno.anchor.load()` 会 `cv2.VideoCapture(video)` 把整段视频读进内存。
原始视频存放在容器级目录（`/root/.claude/uploads/...`），**会随容器回收消失**，
而且是可识别的真人攀岩影像，人已决定不进 git。

所以数值基线不能依赖 `load()` 的完整形态。这里的 `load_nv()` 把 `load()` 里
**读帧的那一段**摘掉，其余逐行照抄——`medf` 直接 import 真模块，
`idx` / `rise` / `ghost_xy` 也全部复用真模块。
也就是说：被测的仍然是 `annotator/climbanno/anchor.py` 里的算法，
只有「从 mp4 解码出 BGR 数组」这一步被替换成「从 npz 的行数推出帧数」。

**这不是等价物，是子集。** `load()` 里 `n = min(len(frames), len(xy))`，
去掉 frames 之后 n 只能取 `len(xy)`。所以 `load_nv()` 会强制校验
`summary.json` 的 `source.frames == len(xy)`，不成立就直接失败——
一旦哪天出现「视频比关键点短」的产物，这里会响，而不是安静地给出不同的 n。

已用真视频交叉验证过：out5 / out7 上 `load_nv()` 与 `load()` 的
t0 / t_end / n / dx / dy 完全一致（见 `qa/报告/2026-08-28.md`）。
"""
from __future__ import annotations

import io
import json
import pathlib
import sys
import time
import traceback

import numpy as np

QA = pathlib.Path(__file__).resolve().parent.parent          # qa/
ROOT = QA.parent                                             # 仓库根
ANNOTATOR = ROOT / "annotator"
KB = ROOT / "climbing-kb"
FIXTURES = QA / "fixtures"
BASELINE = QA / "回归基线"

if str(ANNOTATOR) not in sys.path:
    sys.path.insert(0, str(ANNOTATOR))
if str(KB) not in sys.path:
    sys.path.insert(0, str(KB))


# --- 不依赖视频的加载器 ---------------------------------------------------

def load_nv(outdir, foot=None, limb="RF"):
    """`anchor.load()` 的无视频版本。除读帧外逐行对应，算法全部复用真模块。"""
    from climbanno import anchor

    outdir = pathlib.Path(outdir)
    if foot is None:
        foot = anchor.R_ANK

    anchor.check_fresh(outdir)      # 与 load() 第一行一致，陈旧目录同样要喊
    d = np.load(outdir / "keypoints.npz")
    xy, com = d["xy"], d["com"]
    fps = float(d["fps"]) if "fps" in d else 30.0
    ev = [json.loads(x) for x in
          (outdir / "evidence.jsonl").open(encoding="utf-8")]
    st = [{c["limb"]: c["state"] for c in e["contacts"]} for e in ev]

    ax, ay = anchor.medf(xy[:, foot, 0]), anchor.medf(xy[:, foot, 1])
    torso = anchor.medf(np.linalg.norm(
        (xy[:, anchor.L_SHO] + xy[:, anchor.R_SHO]) / 2 -
        (xy[:, anchor.L_HIP] + xy[:, anchor.R_HIP]) / 2, axis=1))

    # load() 里 n = min(len(frames), len(xy))。没有 frames 就必须证明
    # 帧数与关键点行数一致，否则 n 会悄悄变成另一个值。
    src = json.loads((outdir / "summary.json").read_text(encoding="utf-8"))
    n_video = (src.get("source") or {}).get("frames")
    if n_video is not None and int(n_video) != len(xy):
        raise AssertionError(
            f"{outdir.name}: summary.source.frames={n_video} 与 "
            f"keypoints 行数 {len(xy)} 不一致——无视频加载器的 n 口径不再成立")

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
    return {"xy": xy, "com": com, "frames": None, "fps": fps, "torso": torso,
            "ax": ax, "ay": ay, "t0": t0, "t_end": t_end,
            "n": len(xy),
            "dx": (com[:, 0] - ax) / torso,
            "dy": (ay - com[:, 1]) / torso}


def patch_anchor_load():
    """把 climbanno.anchor.load 换成无视频版本。

    `make_case.anchor_measures()` 在函数体内部 `from climbanno.anchor import load`，
    所以在调用前替换模块属性就能让**真的 make_case 代码**跑在 fixtures 上。
    这样测的是 make_case 的口径，不是我重写的口径。
    """
    from climbanno import anchor
    orig = anchor.load
    anchor.load = lambda outdir, video=None, foot=anchor.R_ANK, limb="RF": \
        load_nv(outdir, foot=foot, limb=limb)
    return orig


def frames_from_npz(outdir):
    """从 fixtures 造出 `pose.Frame` 列表，供 pose/drive 的纯计算函数使用。"""
    from climbanno import pose

    d = np.load(pathlib.Path(outdir) / "keypoints.npz")
    xy, vis = d["xy"], d["vis"]
    fps = float(d["fps"])
    out = []
    for i in range(len(xy)):
        ok = bool(np.isfinite(xy[i]).all()) and float(vis[i].max()) > 0
        out.append(pose.Frame(i, i / fps, ok,
                              xy[i] if ok else None,
                              vis[i] if ok else None))
    return out, fps


def contacts_from_evidence(outdir, n=None):
    """从 evidence.jsonl 还原 {limb: [state per frame]}，drive.* 需要这个形状。"""
    ev = [json.loads(x) for x in
          (pathlib.Path(outdir) / "evidence.jsonl").open(encoding="utf-8")]
    limbs = ["LH", "RH", "LF", "RF"]
    out = {L: [] for L in limbs}
    for e in ev:
        m = {c["limb"]: c["state"] for c in e["contacts"]}
        for L in limbs:
            out[L].append(m.get(L, "uncertain"))
    return out


# --- 极简断言框架（不依赖 pytest，本环境的 python3 里没有）-----------------

class Case:
    def __init__(self, name):
        self.name, self.checks, self.fails = name, [], []
        self.skipped = None


class Runner:
    def __init__(self, title):
        self.title, self.cases = title, []
        self._cur = None
        self.xfail, self.xpass = [], []

    def case(self, name):
        self._cur = Case(name)
        self.cases.append(self._cur)
        return self._cur

    def skip(self, why):
        self._cur.skipped = why

    def check(self, ok, desc, got=None, want=None):
        self._cur.checks.append(desc)
        if not ok:
            self._cur.fails.append((desc, got, want))
        return bool(ok)

    def eq(self, got, want, desc):
        return self.check(got == want, desc, got, want)

    def close(self, got, want, tol, desc):
        ok = (got is not None and want is not None
              and abs(float(got) - float(want)) <= tol)
        return self.check(ok, f"{desc}（容差 ±{tol}）", got, want)

    def known_defect(self, fixed, defect_id, desc):
        """已知缺陷的复现检查。

        `fixed=False`（缺陷仍在）→ 记 XFAIL，不算失败，但会打印出来。
        `fixed=True`（行为已改）→ 记 XPASS，**整套算失败**——
        因为缺陷修好了却没人来关掉这条记录，说明清单和代码脱节了。
        这样一条检查在两个方向上都会响。
        """
        self._cur.checks.append(f"[已知缺陷 {defect_id}] {desc}")
        if fixed:
            self.xpass.append((defect_id, desc))
            self._cur.fails.append(
                (f"[已知缺陷 {defect_id}] 行为已改变，请更新 qa/缺陷清单.md",
                 "缺陷似乎已修复", f"清单记为未修复：{desc}"))
        else:
            self.xfail.append((defect_id, desc))
        return not fixed

    def report(self):
        n_c = sum(len(c.checks) for c in self.cases)
        n_f = sum(len(c.fails) for c in self.cases)
        n_s = sum(1 for c in self.cases if c.skipped)
        print(f"\n{'=' * 70}\n{self.title}\n{'=' * 70}")
        for c in self.cases:
            if c.skipped:
                print(f"[SKIP] {c.name}  —— {c.skipped}")
                continue
            mark = "FAIL" if c.fails else " OK "
            print(f"[{mark}] {c.name}  （{len(c.checks)} 项断言，"
                  f"{len(c.fails)} 项失败）")
            for desc, got, want in c.fails:
                print(f"       ✗ {desc}")
                print(f"         实际 = {got!r}")
                print(f"         期望 = {want!r}")
        for did, desc in self.xfail:
            print(f"[XFAIL] {did} 未修复（预期）：{desc}")
        print(f"—— {self.title}：{len(self.cases)} 个用例"
              f"（{n_s} 跳过），{n_c} 项断言，{n_f} 项失败，"
              f"{len(self.xfail)} 项已知缺陷")
        return n_f


def capture_stderr(fn, *a, **kw):
    """跑一次并抓走 stderr——`check_fresh()` 只 print 到 stderr，
    要断言它「确实喊了」就必须把喊声接住。"""
    buf, old = io.StringIO(), sys.stderr
    sys.stderr = buf
    try:
        r = fn(*a, **kw)
    finally:
        sys.stderr = old
    return r, buf.getvalue()


def sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def read_baseline(name):
    p = BASELINE / name
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def write_baseline(name, obj):
    p = BASELINE / name
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2,
                            sort_keys=True) + "\n", encoding="utf-8")
    return p


def r2(v, k=2):
    if v is None:
        return None
    return round(float(v), k)


def main_guard(fn):
    """统一入口：异常也算失败，并且贴原始 traceback。"""
    t = time.time()
    try:
        n_f = fn()
    except Exception:
        traceback.print_exc()
        print("\n!! 用例因异常中止，计为失败")
        sys.exit(1)
    print(f"   用时 {time.time() - t:.1f}s")
    sys.exit(1 if n_f else 0)
