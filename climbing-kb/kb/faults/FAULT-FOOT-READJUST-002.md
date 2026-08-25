---
id: FAULT-FOOT-READJUST-002
type: fault
name: 踩上去要反复调整
aliases: [脚要挪好几次, 踩不实, 二次调整]
status: active
user_language:
  - 我踩上去总要动好几下才踏实
  - 老觉得没踩对，要重新放一次
observables:
  - 脚落到岩点后 0.5 秒内发生位置调整的次数
  - 放脚时视线是否在看脚
  - 调整期间体重是否仍挂在手上
candidate_explanations:
  - explanation: 移动之前没有选定落点，属于读线问题而不是脚法问题
    evidence_required: 上墙前有无地面读线动作；墙上放脚前有无停顿观察
    technique: TEC-PER-READ-001
  - explanation: 放脚时视线在看手，脚是盲放的
    evidence_required: 视频中能看清头部朝向
    technique: TEC-CON-FOOT-001
  - explanation: 选错了鞋的接触部位，放上去才发现方向不对
    evidence_required: 能看清是内侧、外侧还是尖端接触
    technique: TEC-CON-FOOT-001
techniques: [TEC-CON-FOOT-001, TEC-PER-READ-001]
physics: [PHY-ECONOMY-008]
hints:
  - 放脚的时候眼睛跟着脚看到它落上去。
  - 动之前先决定踩哪里、用鞋的哪一边。
tasks: [TASK-FOOT-EYES-002, TASK-SILENT-FEET-001]
safety:
  - 反复调整会延长手上负荷时间，前臂疲劳时更容易发生，注意不要为了「调好」而硬撑
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

这个卡点的代价常被低估：每次调整期间，**体重全挂在手上**，
按 [PHY-ECONOMY-008](../physics/PHY-ECONOMY-008.md) 是纯消耗、零位移。

关键区分点是**问题发生在上墙前还是墙上**：

- 上墙前没读脚点 → 这是读线问题，练脚法没用；
- 读了但放脚时没看 → 这是执行问题，练静音脚有效。

产品可以从「上墙前有无地面观察」这个可观察事实来区分这两者。
