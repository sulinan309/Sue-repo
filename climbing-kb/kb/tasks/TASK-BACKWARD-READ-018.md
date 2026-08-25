---
id: TASK-BACKWARD-READ-018
type: task
name: 倒着读线
technique_refs: [TEC-PER-READ-001]
grade_range: "任意难度"
goal: >
  从结束点往回推手序，算出起步该用哪只手，再上墙验证。
steps:
  - 选一条没爬过的线路
  - 从结束点开始往回推：最后一个点用哪只手？前一个点呢？
  - 一直推到起步，得出起步该用哪只手
  - 上墙按这个手序爬
  - 记录实际爬的时候有没有需要换手
evidence: >
  上传视频，记录是否出现换手动作。
fallback: >
  只倒推最后 3 步，不推整条线。
safety:
  - 读线时避开正在攀爬者的落区
review:
  status: pending
  fact: null
  climb: null
  teaching: null
  version: 0.1.0
  updated: 2026-08-25
---

## 为什么这样设计

倒推是解决手序问题唯一可靠的方法——正着推很容易在中途走偏，
而结束点的用手通常是确定的。

「有没有换手」给了这个任务一个二值的、可从视频观察的成功标准。
