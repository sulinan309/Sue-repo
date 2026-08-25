---
id: FAULT-HESITATE-013
type: fault
name: 在墙上犹豫太久
aliases: [不敢动, 停很久, 想太久, hesitation]
status: active
user_language:
  - 我到那一步就不敢动了
  - 挂在那儿想半天，然后力竭掉下来
  - 每次都是想太久
observables:
  - 单次停顿的时长和全程停顿总时长
  - 停顿发生的位置是否固定在同一步
  - 停顿期间是否有伸出去又收回的试探
  - 停顿之后是完成动作还是掉落
candidate_explanations:
  - explanation: 上墙前没有读出这一步的解法，在墙上现想
    evidence_required: 上墙前无地面读线；停顿位置与线路难点一致
    technique: TEC-PER-READ-001
  - explanation: 知道要做什么，但对动作没有把握，属于动作承诺问题
    evidence_required: 有多次试探性伸手又收回
    technique: null
  - explanation: 当前身体位置不稳定，客观上不具备发起动作的条件
    evidence_required: 停顿期间能观察到持续的微调和摆动
    technique: TEC-POS-COM-001
techniques: [TEC-PER-READ-001, TEC-POS-COM-001, TEC-STR-SPEED-001]
physics: [PHY-ECONOMY-008]
hints:
  - 上墙前把这一步的手序在地面过一遍。
  - 停在那儿也在耗前臂，想清楚就上。
  - 先把身体稳住再决定动不动——现在这个位置本来就发不出力。
tasks: [TASK-READ-BEFORE-017, TASK-BACKWARD-READ-018]
safety:
  - 长时间悬挂会加速前臂力竭，力竭状态下掉落控制能力下降
  - 第二个候选解释属于心理层面，本单元只做识别不做心理干预，相关内容由心理库承接
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

犹豫的代价是可以量化的：按 [PHY-ECONOMY-008](../physics/PHY-ECONOMY-008.md)，
停顿不产生位移，但屈指肌的等长收缩在持续消耗。**停 15 秒的代价可能大于一个不标准的动作。**

三个解释分属三个不同领域：

| 解释 | 归属 | 处理 |
| --- | --- | --- |
| 没读出解法 | 技巧库（读线） | 给读线任务 |
| 没有动作承诺 | **心理库** | 首期不处理，只识别 |
| 位置本来就不稳 | 技巧库（重心） | 给稳定提示 |

第二个明确划给心理库，**技巧库不越界给心理建议**。
产品在识别出这一类时应当只陈述事实，不做心理诊断。
