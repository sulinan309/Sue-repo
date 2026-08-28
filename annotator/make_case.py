#!/usr/bin/env python3
"""从管线输出草拟一个真实案例单元。

    python3 make_case.py out5 --id CASE-2608-001 --outcome failed \
        --climber A --video 原视频.mp4 --pair CASE-2608-002

设计原则：**管线能测的自动填，人必须填的留空并标出来。**

案例是知识库唯一会被现实推翻的部分。其余单元讲原理和方法，
案例记录「这套方法用在具体的人身上发生了什么」。
所以两类信息必须分开存：

  measured      管线实测量，不允许手填估计值
  expert_notes  人的判断、岩馆线路等管线测不到的事实

混在一起，用一段时间之后就分不清哪些数字是量出来的、哪些是猜的。
"""
from __future__ import annotations

import argparse
import json
import pathlib
from datetime import date


def rd(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def ystr(v):
    """按需加引号。以 [ { 等字符开头或含 ": " 的标量会被 YAML 误读成结构。

    事实行形如 `[2.2–6.1s] 右脚踩上去了` —— 不加引号 YAML 会把方括号当流式序列，
    然后在后面的中文上报语法错误。
    """
    v = str(v)
    if v[:1] in "[{&*!%@`>|#-?,'\"" or ": " in v or v.endswith(":"):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return v


ANCHOR_TIMES = (0.5, 1.0, 1.5, 2.0)
ANCHOR_WIN = 2.0


def anchor_measures(outdir: pathlib.Path, video: str):
    """踩实锚点口径的实测量。

    刻意复用 climbanno.anchor —— 知识库里的数字必须和产物里的出自同一条
    代码路径，否则「0.43」在 README、卡片和 KB 里会慢慢变成三个数。
    """
    import numpy as np
    from climbanno.anchor import load, idx, rise

    s = load(str(outdir), video)
    fps, t0 = s["fps"], s["t0"]
    n = int(ANCHOR_WIN * fps)
    if min(s["t_end"], s["n"]) - t0 < n:
        raise SystemExit(f"{outdir} 从 T0 起不足 {ANCHOR_WIN}s，无法用锚点口径")
    dxw = np.abs(s["dx"][t0:t0 + n])
    dxw = dxw[np.isfinite(dxw)]
    return {
        "踩实锚点秒": round(t0 / fps, 2),
        "踩实后持续接触秒": round((s["t_end"] - t0) / fps, 2),
        "踩实时横向偏": round(float(abs(s["dx"][t0])), 2),
        "横向偏移": {
            "窗口": f"T0~+{ANCHOR_WIN:.1f}s",
            "中位": round(float(np.median(dxw)), 2),
            "p10": round(float(np.percentile(dxw, 10)), 2),
            "p90": round(float(np.percentile(dxw, 90)), 2),
            "全距": [round(float(dxw.min()), 2), round(float(dxw.max()), 2)],
            "帧数": int(len(dxw)),
        },
        # 键加引号：以 + 开头的裸标量 YAML 解析起来太脆
        "相对承重脚高度变化": {f'"+{t:.1f}s"': round(float(rise(s, idx(s, t))), 2)
                       for t in ANCHOR_TIMES},
    }


def collect(outdir: pathlib.Path):
    """从 summary.json 里抽出可复用的量与事实。"""
    s = rd(outdir / "summary.json")
    measured, facts, knowledge = {}, [], set()

    measured["姿态检出率"] = s.get("pose_rate")
    if s.get("pose_reliable_rate") is not None:
        measured["姿态可信率"] = s["pose_reliable_rate"]
    if s.get("analyzable_windows"):
        measured["可分析区间"] = s["analyzable_windows"]

    for st in s.get("stalls", []):
        facts.append(f"{st['leg']}腿高脚停滞 {st['t0']}–{st['t1']}s"
                     f"（{st['t1'] - st['t0']:.1f} 秒），净上升 {st['net_rise']:+.2f} 倍躯干长")
        measured.setdefault("停滞段", []).append({
            "腿": st["leg"], "起止": [st["t0"], st["t1"]],
            "膝角中位": st["knee_med"], "膝角峰值": st["knee_max"],
            "净上升": st["net_rise"], "重心相对承重踝": st["offset_med"],
            "另一腿膝角中位": st["other_knee_med"]})
        for c in st.get("candidates", []):
            if c.get("知识单元"):
                knowledge.add(c["知识单元"])

    for r in s.get("rises", []):
        facts.append(f"重心上升 {r['t0']}–{r['t1']}s，净升 {r['net']:+.2f} 倍躯干长"
                     + (f"，出手比起升晚 {r['lead_s']:+.2f}s" if r.get("lead_s") is not None else ""))
        measured.setdefault("上升段", []).append({
            "起止": [r["t0"], r["t1"]], "净上升": r["net"],
            "出手时间差": r.get("lead_s"),
            "重心相对承重踝": [r.get("off_start"), r.get("off_end")]})

    for d in s.get("drives", []):
        if d.get("chain"):
            knowledge.add("PHY-KCHAIN-006")

    hints = []
    for c in s.get("coach_cards", []):
        facts.append(f"[{c['时间']}] {c['标题']}")
        hints += c.get("下次这样试", [])
        knowledge.update(c.get("依据", []))

    return measured, facts, sorted(knowledge), hints, s


def emit_measured(measured, ind="  "):
    """把实测量渲染成 YAML 行。嵌套字典按层缩进，字典列表用 - 起头。"""
    out = []
    for k, v in measured.items():
        if isinstance(v, dict):
            out.append(f"{ind}{k}:")
            out += emit_measured(v, ind + "  ")
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            out.append(f"{ind}{k}:")
            for it in v:
                first = True
                for kk, vv in it.items():
                    out.append((ind + "  - " if first else ind + "    ")
                               + f"{kk}: {json.dumps(vv, ensure_ascii=False)}")
                    first = False
        else:
            out.append(f"{ind}{k}: {json.dumps(v, ensure_ascii=False)}")
    return out


def update_measured(case_path: pathlib.Path, outdir: pathlib.Path, video: str):
    """就地替换已有案例单元的 measured 块，正文和人工字段一概不动。

    重算而不是重新草拟：叙述、expert_notes、审核状态都是人写的，
    重新生成会把它们抹掉。
    """
    txt = case_path.read_text(encoding="utf-8")
    lines = txt.split("\n")
    try:
        a = lines.index("measured:")
    except ValueError:
        raise SystemExit(f"{case_path.name} 里找不到 measured 块")
    b = a + 1
    while b < len(lines) and (lines[b].startswith(" ") or not lines[b].strip()):
        if not lines[b].strip() and b + 1 < len(lines) and \
                not lines[b + 1].startswith(" "):
            break
        b += 1

    old = collect(outdir)[0]
    old.update(anchor_measures(outdir, video))
    new = lines[:a] + ["measured:"] + emit_measured(old) + lines[b:]
    case_path.write_text("\n".join(new), encoding="utf-8")
    return len(old)


def main():
    ap = argparse.ArgumentParser(description="从管线输出草拟案例单元")
    ap.add_argument("outdir")
    ap.add_argument("--id")
    ap.add_argument("--outcome",
                    choices=["success", "failed", "partial"])
    ap.add_argument("--climber", help="匿名标识，同一人跨案例复用")
    ap.add_argument("--video", default=None, help="原视频文件名，只记名不记路径")
    ap.add_argument("--pair", default=None, help="配对案例 ID（正反对照）")
    ap.add_argument("--name", default=None)
    ap.add_argument("-o", "--out", default="../climbing-kb/kb/cases")
    ap.add_argument("--update-measured", metavar="案例文件",
                    help="只重算已有单元的 measured 块，正文不动")
    ap.add_argument("--anchor-video", help="锚点口径需要读原视频")
    a = ap.parse_args()

    if a.update_measured:
        if not a.anchor_video:
            raise SystemExit("--update-measured 需要 --anchor-video")
        p = pathlib.Path(a.update_measured)
        n = update_measured(p, pathlib.Path(a.outdir), a.anchor_video)
        print(f"已更新 {p.name} 的 measured 块：{n} 项")
        return

    missing = [f for f, v in (("--id", a.id), ("--outcome", a.outcome),
                              ("--climber", a.climber)) if not v]
    if missing:
        raise SystemExit("草拟新单元需要 " + "、".join(missing))
    outdir = pathlib.Path(a.outdir)
    measured, facts, knowledge, hints, s = collect(outdir)
    src = s.get("source", {})

    def y(v, ind=2):
        return json.dumps(v, ensure_ascii=False)

    lines = [
        "---",
        f"id: {a.id}",
        "type: case",
        "status: active",
        f"name: {a.name or '（待补：一句话说明这次尝试）'}",
        f"outcome: {a.outcome}",
        "",
        "# --- 管线测不到，需要人填 ---",
        "gym: null              # 岩馆",
        "route: null            # 线路编号或颜色",
        "grade: null            # 难度",
        "expert_notes: []       # 人的判断；不要写进 measured",
        "",
        "climber:",
        f"  ref: {a.climber}          # 匿名标识，同一人跨案例复用",
        "  background: null      # 攀岩时长、身高臂展等，待补",
        "",
        "video:",
        f"  file: {a.video or 'null'}",
        f"  frames: {src.get('frames')}",
        f"  fps: {src.get('fps')}",
        f"  size: {y(src.get('size'))}",
        "",
        "# --- 以下由 annotator/make_case.py 从管线输出生成 ---",
        "measured:",
    ]
    for k, v in measured.items():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            lines.append(f"  {k}:")
            for it in v:
                first = True
                for kk, vv in it.items():
                    lines.append(("    - " if first else "      ")
                                 + f"{kk}: {y(vv)}")
                    first = False
        else:
            lines.append(f"  {k}: {y(v)}")

    lines.append("")
    lines.append("facts:")
    lines += [f"  - {ystr(f)}" for f in facts] or ["  - 无"]
    lines.append("")
    lines.append(f"knowledge: {y(knowledge)}")
    lines.append("hints_given:")
    lines += [f"  - {ystr(h)}" for h in dict.fromkeys(hints)] or ["  []"]
    if a.pair:
        lines.append(f"paired_with: {a.pair}")
    lines += [
        "",
        "# --- 待观察：用户看到建议之后发生了什么 ---",
        "adopted: null          # 用户是否采纳",
        "next_result: null      # 下一次是否改变动作、推进或完攀",
        "",
        "versions:",
        f"  pipeline: {pathlib.Path(__file__).parent.name}",
        f"  generated: {date.today().isoformat()}",
        "",
        "evidence_level: 可确认事实",
        "review:",
        "  status: pending",
        "  fact: null",
        "  climb: null",
        "  teaching: null",
        "  version: 0.1.0",
        f"  updated: {date.today().isoformat()}",
        "---",
        "",
        "## 这次发生了什么",
        "",
        "（待补：用两三句话说明这次尝试的经过。管线只给量，故事要人写。）",
        "",
        "## 为什么值得留档",
        "",
        "（待补：这个案例支持或推翻了哪条知识？"
        "如果它推翻了什么，写清楚——知识库需要能记录「建议无效」。）",
        "",
    ]
    dst = pathlib.Path(a.out) / f"{a.id}.md"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(lines), encoding="utf-8")
    print(f"已草拟 {dst}")
    print(f"  实测量 {len(measured)} 项   事实 {len(facts)} 条   "
          f"关联知识单元 {len(knowledge)} 个")
    print("  待人填：gym / route / grade / expert_notes / climber.background / 正文两节")


if __name__ == "__main__":
    main()
