---
id: FAULT-NO-PLAN-014
type: fault
name: 上墙前没有计划
aliases: [不读线, 上去再说, no beta]
status: active
user_language:
  - 我一般直接上去爬
  - 爬到一半不知道下一步抓哪里
  - 每次尝试都不太一样
observables:
  - 上墙前是否有可见的地面观察或预演
  - 墙上停顿次数
  - 同一线路多次尝试之间动作顺序是否一致
  - 是否出现爬错线路或抓到其他线路的点
candidate_explanations:
  - explanation: 没有建立读线习惯
    evidence_required: 上墙前无地面观察动作
    technique: TEC-PER-READ-001
  - explanation: 读了但只读手点，漏掉脚点
    evidence_required: 有地面观察但墙上频繁找脚
    technique: TEC-PER-READ-001
  - explanation: 读了但记不住，动作太多没有分段
    evidence_required: 前段顺畅、中后段开始偏离
    technique: TEC-PER-READ-001
techniques: [TEC-PER-READ-001]
physics: [PHY-ECONOMY-008]
hints:
  - 上墙前花 30 秒，把结束点和最难那一步先看出来。
  - 也看一下脚点，脚决定了你的手够不够得到。
  - 把线路分成两三段记，比记十五个动作容易得多。
tasks: [TASK-READ-BEFORE-017, TASK-BACKWARD-READ-018]
safety:
  - 读线时站在墙下观察，避开正在攀爬者的落区
evidence_level: 专家共识
review:
  status: pending
  fact: null
  climb: null
  teaching: null
  version: 0.1.0
  updated: 2026-08-25
---

## 怎么区分

三个解释是**递进的三个阶段**，对应三种不同的任务：

1. 完全不读 → 先建立习惯（`TASK-READ-BEFORE-017`）；
2. 只读手 → 补脚点（提示层面就能纠正）；
3. 读了记不住 → 改记忆方式，分段和倒着读（`TASK-BACKWARD-READ-018`）。

产品可以从「上墙前有无地面观察」这个可观察事实区分第一阶段，
从「墙上找脚的频率」区分第二阶段，
从「前段顺畅、后段偏离」区分第三阶段。三者都是`可确认事实`级别。
