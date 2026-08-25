---
id: FAULT-HIP-SAG-004
type: fault
name: 髋部下坠离墙
aliases: [屁股掉下去, hip sag, 塌腰, 身体离墙]
status: active
user_language:
  - 我总感觉身体离墙越来越远
  - 挂在那儿腰是塌的
  - 陡墙上手特别累
observables:
  - 髋部与墙面的距离在移动过程中的变化
  - 下背部是否呈现明显反弓
  - 手臂是否被迫屈曲以维持位置
  - 脚是否随之逐渐失去加载
candidate_explanations:
  - explanation: 核心未主动收紧，重力把髋部拉离墙面
    evidence_required: 能观察到髋部随时间逐渐下坠而非突然脱落
    technique: TEC-POS-TENSION-003
  - explanation: 身体朝向是正身，髋部被身体厚度顶在离墙较远处
    evidence_required: 能看清骨盆朝向是正对墙面
    technique: TEC-POS-ORIENT-002
  - explanation: 脚点位置过低或过远，几何上无法把髋带到墙面附近
    evidence_required: 能看清脚点与手点的相对位置
    technique: null
  - explanation: 已经进入疲劳，维持张力的能力下降
    evidence_required: 需要结合本次到馆的尝试次数和时长，单条视频不足以判断
    technique: null
techniques: [TEC-POS-TENSION-003, TEC-POS-ORIENT-002, TEC-MOV-DROPKNEE-003]
physics: [PHY-TORQUE-003, PHY-OPPOSITION-005]
hints:
  - 试试把髋主动拉向墙面，手会立刻轻很多。
  - 转个髋侧过来，髋能贴得更近。
  - 这一步可以试试折膝，把髋压到墙上。
tasks: [TASK-TENSION-HOLD-014, TASK-SIDE-ON-009]
safety:
  - 长时间维持塌腰姿势对下背部负荷较大，出现腰部不适应当结束该线路
  - 第四个候选解释涉及疲劳，触发时产品应当优先给休息建议而不是技巧提示
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

髋部下坠是**手上负荷过重的直接几何原因**。
按 [PHY-TORQUE-003](../physics/PHY-TORQUE-003.md)，
髋离墙越远，体重对手点的力臂越长，手就越累。

四个解释里第三个和第四个特别重要，因为它们**不是技巧问题**：

- 脚点几何不支持 → 再练张力也贴不上去，应该换解法；
- 已经疲劳 → 这时候给技巧提示是错的，应该给休息建议。

第四项触发时，按 MVP 文档 07 章的负荷刹车规则，
产品应当优先输出休息建议，而不是继续推技巧任务。
