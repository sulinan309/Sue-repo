#!/usr/bin/env python3
"""审计知识库对感知能力的需求。

把每个单元的 observables 和 perception/observable-capability-map.yaml 对起来，
回答三个排期问题：

  1. 只用 P0/P1（姿态流）能覆盖多少条反馈——这是 MVP 第一批的可行区间
  2. 有多少条卡在 P3（双流融合）——这是双流架构的收益量
  3. 有多少条卡在 P4（墙体坐标系）——这是最大的单点缺口

同时校验映射与知识库是否同步：知识库改了 observables 而映射没跟上会报错。

用法：
    python3 tools/perception_audit.py            # 总览
    python3 tools/perception_audit.py --tier P4  # 列出某档位的全部条目
    python3 tools/perception_audit.py --unit     # 按单元看可解锁比例
"""
import json
import pathlib
import sys
from collections import Counter, defaultdict

try:
    import yaml
except ImportError:
    sys.exit("需要 PyYAML：pip install pyyaml")

ROOT = pathlib.Path(__file__).resolve().parent.parent
KBJSON = ROOT / "dist" / "kb.json"
MAPFILE = ROOT / "perception" / "observable-capability-map.yaml"

# 档位的解锁顺序。产品可用性按这个顺序累积。
ORDER = ["P0", "P1", "P2", "PX-AUDIO", "P3", "P4", "PX-OUT"]


def load():
    if not KBJSON.exists():
        sys.exit("找不到 dist/kb.json，先运行：python3 tools/build.py")
    kb = json.loads(KBJSON.read_text(encoding="utf-8"))
    cmap = yaml.safe_load(MAPFILE.read_text(encoding="utf-8"))
    return kb, cmap


def join(kb, cmap):
    """把 observables 和档位对起来，同时校验同步。"""
    rows, errors = [], []
    mapped = cmap["map"]
    hard = {tuple(x) for x in cmap.get("hard", [])}
    cross = {tuple(x) for x in cmap.get("cross_video", [])}

    for uid, u in kb["units"].items():
        obs = u.get("observables") or []
        if not obs:
            continue
        tiers = mapped.get(uid)
        if tiers is None:
            errors.append(f"{uid} 有 {len(obs)} 条 observables，但映射表里没有它")
            continue
        if len(tiers) != len(obs):
            errors.append(
                f"{uid} 映射 {len(tiers)} 条，知识库有 {len(obs)} 条——映射已过期")
            continue
        for i, (o, t) in enumerate(zip(obs, tiers)):
            if t not in cmap["tiers"]:
                errors.append(f"{uid}[{i}] 档位 {t!r} 未定义")
                continue
            rows.append({
                "unit": uid, "unit_name": u.get("name"), "type": u.get("type"),
                "idx": i, "text": o, "tier": t,
                "hard": (uid, i) in hard, "cross_video": (uid, i) in cross,
            })

    for uid in mapped:
        if uid not in kb["units"]:
            errors.append(f"映射表里的 {uid} 在知识库中不存在")
    return rows, errors


def overview(rows, cmap):
    total = len(rows)
    counts = Counter(r["tier"] for r in rows)

    print(f"\n知识库共 {total} 条 observables，按感知能力档位分布：\n")
    cum = 0
    for t in ORDER:
        n = counts.get(t, 0)
        if not n:
            continue
        cum += n
        info = cmap["tiers"][t]
        bar = "█" * round(n / total * 42)
        print(f"  {t:9s} {info['name']:14s} {n:3d} 条 ({n/total*100:4.1f}%)  {bar}")
        print(f"  {'':9s} {info['maturity']}")
        if t not in ("PX-OUT",):
            print(f"  {'':9s} {'累计可覆盖':10s} {cum:3d}/{total} ({cum/total*100:.1f}%)")
        print()

    p01 = counts.get("P0", 0) + counts.get("P1", 0) + counts.get("P2", 0) + counts.get("PX-AUDIO", 0)
    p3, p4 = counts.get("P3", 0), counts.get("P4", 0)
    print("排期含义")
    print(f"  纯姿态流 + 场景 + 音频就能覆盖   {p01:3d} 条 ({p01/total*100:.1f}%)  ← MVP 第一批可行区间")
    print(f"  必须等双流融合（P3）             {p3:3d} 条 ({p3/total*100:.1f}%)  ← 双流架构的收益量")
    print(f"  必须等墙体坐标系（P4）           {p4:3d} 条 ({p4/total*100:.1f}%)  ← 最大单点缺口")
    n_hard = sum(1 for r in rows if r["hard"])
    n_cross = sum(1 for r in rows if r["cross_video"])
    print(f"\n  其中标记为高难度               {n_hard:3d} 条（同档位内排最后）")
    print(f"  额外依赖跨视频线路对齐          {n_cross:3d} 条")


def by_unit(rows, cmap):
    """每个单元在各档位下能解锁多大比例——决定哪些卡点先能给建议。"""
    g = defaultdict(list)
    for r in rows:
        g[r["unit"]].append(r)

    print("\n按单元看：只用姿态流（P0/P1/P2/音频）能解锁多少条 observables\n")
    scored = []
    for uid, rs in g.items():
        easy = sum(1 for r in rs if r["tier"] in ("P0", "P1", "P2", "PX-AUDIO"))
        scored.append((easy / len(rs), easy, len(rs), uid, rs[0]["unit_name"], rs[0]["type"]))
    scored.sort(reverse=True)

    for ratio, easy, n, uid, name, utype in scored:
        bar = "█" * round(ratio * 20) + "·" * (20 - round(ratio * 20))
        flag = "  ← 姿态流即可" if ratio == 1.0 else ("  ← 完全依赖融合/坐标系" if ratio == 0 else "")
        print(f"  {bar} {easy}/{n}  {uid:26s} {name}{flag}")


def list_tier(rows, cmap, tier):
    sel = [r for r in rows if r["tier"] == tier]
    info = cmap["tiers"].get(tier)
    if not info:
        sys.exit(f"未定义的档位：{tier}")
    print(f"\n{tier} · {info['name']}（{len(sel)} 条）")
    print(f"依赖：{info['needs']}")
    print(f"成熟度：{info['maturity']}\n")
    for r in sel:
        marks = []
        if r["hard"]:
            marks.append("高难度")
        if r["cross_video"]:
            marks.append("跨视频")
        m = f"  [{'/'.join(marks)}]" if marks else ""
        print(f"  {r['unit']:26s} {r['text']}{m}")


def main():
    kb, cmap = load()
    rows, errors = join(kb, cmap)

    if errors:
        print("映射与知识库不同步：\n")
        for e in errors:
            print(f"  [错误] {e}")
        print(f"\n共 {len(errors)} 个问题。修好映射表后重跑。")
        return 1

    args = sys.argv[1:]
    if "--tier" in args:
        list_tier(rows, cmap, args[args.index("--tier") + 1])
    elif "--unit" in args:
        by_unit(rows, cmap)
    else:
        overview(rows, cmap)
    return 0


if __name__ == "__main__":
    sys.exit(main())
