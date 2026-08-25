---
id: FAULT-STUCK-TRAVERSE-006
type: fault
name: 横移到一半卡住
aliases: [横着爬卡住, 进退两难, stuck traverse]
status: active
user_language:
  - 横移到中间就上不去也下不来
  - 卡在两个点中间
observables:
  - 髋部在横移过程中的路径是否连续
  - 是否出现停在两个脚点中间、双腿都不完全承重的状态
  - 停顿位置与两个脚点的相对关系
candidate_explanations:
  - explanation: 重心提前离开出发脚，但还没进入目标脚的支撑范围
    evidence_required: 能观察到髋部停在两个脚点之间
    technique: TEC-POS-COM-001
  - explanation: 中途缺少一个过渡脚点或旗式配平，几何上没有连续路径
    evidence_required: 能看清可用脚点的分布
    technique: TEC-MOV-FLAG-001
  - explanation: 手序错了，到中途时手不对，无法继续交替
    evidence_required: 能看清手的交替顺序
    technique: TEC-PER-READ-001
techniques: [TEC-POS-COM-001, TEC-MOV-FLAG-001, TEC-PER-READ-001]
physics: [PHY-EQUILIBRIUM-002, PHY-GRAVITY-COM-001]
hints:
  - 横移的时候髋要走一条连续的路，不要停在两只脚中间。
  - 中间这一步可能需要旗一下腿配平。
  - 上墙前把这一段的手序倒着推一遍。
tasks: [TASK-TRAVERSE-COM-006, TASK-ONE-FOOT-TRAVERSE-008]
safety:
  - 横移掉落时身体是侧向移动的，落点会偏离起跳位置，确认整条横移段下方的垫子连续
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

横移卡住的本质是**支撑范围出现了断点**。

按 [PHY-EQUILIBRIUM-002](../physics/PHY-EQUILIBRIUM-002.md)，
身体在任何时刻都需要落在某个支撑范围内。
横移时如果两个脚点之间的距离超出了重心可以连续移动的范围，
中间就存在一段「哪边都撑不住」的区域——停在那里必然卡住。

解法有两类：**让路径连续**（找过渡脚点、用旗式扩大有效支撑），
或者**不要停**（速度足够快地通过断点）。第二类风险高，优先第一类。
