#!/usr/bin/env python3
"""T03 · 陈旧输出目录必须告警（annotator/README「输出目录会过期，而且不报错」）。

原始事故：`out5` 与 `out6` 是同一段视频的两次运行，out6 早于「关节可信度」
那次改动。拿 out6 做了对比视频、静态卡片和案例单元的数字——**没有任何报错**，
只是 `+2.0s 高度变化` 从 -0.50 悄悄变成了 -0.38，最小间距从 0.37 变成 0.26。

`anchor.check_fresh()` 是针对它加的防线：summary.json 缺 `pose_reliable_rate`
或 `analyzable_windows` 就往 stderr 喊一句。

本用例要回答两件事：
  1. 它到底喊没喊——「print 到 stderr」这种防线最容易在重构里静静消失
  2. 喊完之后发生了什么——喊完照常返回完整数字，调用方拿不到任何信号

第 2 条是缺陷 D-001 的证据，见 qa/缺陷清单.md。本用例不改代码，只把行为钉死。
"""
from __future__ import annotations

import contextlib
import io
import json
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import qalib as Q                                            # noqa: E402

FRESH_KEYS = ("pose_reliable_rate", "analyzable_windows")


def make_dir(td, name, mutate):
    """从 out5 fixture 复制一份，按 mutate 改 summary.json。"""
    p = pathlib.Path(td) / name
    shutil.copytree(Q.FIXTURES / "out5", p)
    sp = p / "summary.json"
    s = json.loads(sp.read_text(encoding="utf-8"))
    s = mutate(s)
    if s is None:
        sp.unlink()
    else:
        sp.write_text(json.dumps(s, ensure_ascii=False), encoding="utf-8")
    return p


def run():
    from climbanno import anchor

    r = Q.Runner("T03 陈旧输出目录告警")

    c = r.case("当前管线的目录：不该有任何告警")
    _, err = Q.capture_stderr(anchor.check_fresh, Q.FIXTURES / "out5")
    r.eq(err, "", "out5 fixture 上 check_fresh 的 stderr 为空")
    _, err = Q.capture_stderr(anchor.check_fresh, Q.FIXTURES / "out7")
    r.eq(err, "", "out7 fixture 上 check_fresh 的 stderr 为空")

    with tempfile.TemporaryDirectory() as td:
        c = r.case("两个字段都缺（out6 的形状）：必须告警且点名字段")
        d = make_dir(td, "stale_both",
                     lambda s: {k: v for k, v in s.items() if k not in FRESH_KEYS})
        _, err = Q.capture_stderr(anchor.check_fresh, d)
        r.check(err.strip() != "", "stderr 非空", repr(err), "非空告警")
        r.check("[警告]" in err, "告警带 [警告] 前缀", repr(err), "含 [警告]")
        for k in FRESH_KEYS:
            r.check(k in err, f"告警点名了 {k}", repr(err), f"含 {k}")
        r.check("重跑" in err, "告警给出了处置动作（重跑 annotate.py）",
                repr(err), "含「重跑」")

        c = r.case("只缺一个字段：也要告警，且只点名缺的那个")
        d = make_dir(td, "stale_one",
                     lambda s: {k: v for k, v in s.items()
                                if k != "pose_reliable_rate"})
        _, err = Q.capture_stderr(anchor.check_fresh, d)
        r.check("pose_reliable_rate" in err, "点名 pose_reliable_rate",
                repr(err), "含该字段")
        r.check("analyzable_windows" not in err,
                "不误报仍然存在的 analyzable_windows", repr(err), "不含该字段")

        c = r.case("字段在但值为 null：同样算陈旧")
        d = make_dir(td, "stale_null",
                     lambda s: {**s, "pose_reliable_rate": None})
        _, err = Q.capture_stderr(anchor.check_fresh, d)
        r.check("pose_reliable_rate" in err, "值为 null 时仍然告警",
                repr(err), "含该字段")

        c = r.case("告警只走 stderr —— 这正是它容易被吞掉的原因")
        d = make_dir(td, "stale_stdout",
                     lambda s: {k: v for k, v in s.items() if k not in FRESH_KEYS})
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            _, err = Q.capture_stderr(anchor.check_fresh, d)
        r.eq(buf.getvalue(), "", "stdout 上没有任何字样")
        r.check(err.strip() != "", "stderr 上有告警", repr(err), "非空")

        c = r.case("告警之后：管线照常给出完整数字（缺陷 D-001 的证据）")
        d = make_dir(td, "stale_flow",
                     lambda s: {k: v for k, v in s.items() if k not in FRESH_KEYS})
        s, err = Q.capture_stderr(Q.load_nv, d)
        r.check(err.strip() != "", "load 路径上确实转发了告警", repr(err), "非空")
        r.check(s is not None and "dy" in s,
                "然而 load 仍然返回了完整结果", type(s).__name__, "dict")
        # 调用方拿不到任何程序可读的信号：返回值是 None，也不抛异常。
        ret, _ = Q.capture_stderr(anchor.check_fresh, d)
        r.known_defect(ret is not None, "D-001",
                       "check_fresh 只 print，不返回状态也不抛异常，"
                       "调用方无法在程序里判断目录是否陈旧")

        raised = False
        try:
            Q.capture_stderr(Q.load_nv, d)
        except Exception:
            raised = True
        r.known_defect(raised, "D-001",
                       "陈旧目录不会中断流程，make_case --update-measured "
                       "可以把旧版数字写进知识库")

        c = r.case("summary.json 整个缺失：目前完全沉默（缺陷 D-002）")
        d = make_dir(td, "no_summary", lambda s: None)
        ret, err = Q.capture_stderr(anchor.check_fresh, d)
        r.known_defect(err.strip() != "", "D-002",
                       "summary.json 不存在时 check_fresh 直接 return，"
                       "一个残缺目录能一路走到出数")

    return r.report()


if __name__ == "__main__":
    Q.main_guard(run)
