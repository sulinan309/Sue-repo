---
id: FAULT-SWING-012
type: fault
name: 抓住之后身体荡出去
aliases: [摆荡, swing, 甩出去, barn door after catch]
status: active
user_language:
  - 抓住了但整个人荡出去
  - 一抓住脚就飞了然后掉
observables:
  - 抓住新点后身体的摆动幅度和方向
  - 脚在抓住瞬间是否已经离开墙面
  - 抓住后张力恢复的时间
  - 摆动是侧向还是沿墙面向外
candidate_explanations:
  - explanation: 水平方向的残余动量没有被抵消，抓住后动量转化为绕手点的摆动
    evidence_required: 能看出移动过程有明显水平速度分量
    technique: TEC-STR-SPEED-001
  - explanation: 抓住之后张力没有立刻恢复，脚回不到墙上
    evidence_required: 抓住后脚长时间悬空
    technique: TEC-POS-TENSION-003
  - explanation: 新的接触点分布集中在身体同侧，本来就会开门
    evidence_required: 能看清抓住后的接触点位置分布
    technique: TEC-MOV-FLAG-001
techniques: [TEC-POS-TENSION-003, TEC-STR-SPEED-001, TEC-MOV-FLAG-001]
physics: [PHY-MOMENTUM-007, PHY-TORQUE-003]
hints:
  - 抓住之后马上收紧，把脚带回墙上。
  - 起动方向尽量对着目标点，减少横向的势。
  - 抓住之后可能需要立刻旗一条腿配平。
safety:
  - 摆荡状态下掉落方向不可预测，落区要预留侧向空间
  - 摆荡时手指承受动态负荷，不要为了「挂住」而硬扣，优先控制落地
tasks: [TASK-TENSION-HOLD-014, TASK-DEADPOINT-015]
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

摆荡是**动量和力矩两个问题叠加**的结果：
水平动量把身体带出去（[PHY-MOMENTUM-007](../physics/PHY-MOMENTUM-007.md)），
接触点分布决定它会不会绕轴转开（[PHY-TORQUE-003](../physics/PHY-TORQUE-003.md)）。

从视频区分：

- **摆动方向沿墙面横向** → 残余水平动量为主，改起动方向；
- **身体绕着手点向外转开** → 接触点分布问题，需要配平；
- **脚一直悬着** → 张力恢复太慢。

三种都表现为「荡出去」，提示不同。
