---
id: FAULT-BARNDOOR-016
type: fault
name: 开门
aliases: [barn door, 被转开, 像门一样甩开, 转出去]
status: active
user_language:
  - 我一松手整个人就转开了
  - 像一扇门一样被甩出去
  - 抓着但身体自己转走
observables:
  - 身体绕两个接触点连线旋转的方向和幅度
  - 旋转发生在释放哪个接触点之后
  - 有效接触点是否集中在身体同一侧
  - 是否有非承重腿参与配平
candidate_explanations:
  - explanation: 有效接触点集中在身体同侧，重心在支撑轴外，无反向力矩
    evidence_required: 能看清接触点分布与身体旋转方向
    technique: TEC-MOV-FLAG-001
  - explanation: 重心没有先移向支撑轴就释放了接触点
    evidence_required: 释放前髋部无向支撑侧的移动
    technique: TEC-POS-COM-001
  - explanation: 做了旗式但方向、幅度或张力不对
    evidence_required: 能看清旗腿位置与旋转方向的关系
    technique: TEC-MOV-FLAG-001
  - explanation: 身体朝向是正身，转成侧身能改变接触点的几何关系
    evidence_required: 能看清骨盆朝向
    technique: TEC-POS-ORIENT-002
techniques: [TEC-MOV-FLAG-001, TEC-POS-COM-001, TEC-POS-ORIENT-002]
physics: [PHY-TORQUE-003, PHY-EQUILIBRIUM-002]
hints:
  - 你被转开的方向，就是那条腿要送去的方向。
  - 松手之前先把髋移向另外两个点的连线。
  - 试试转个髋侧过来，接触点的关系会变。
tasks: [TASK-FLAG-SWITCH-007, TASK-ONE-FOOT-TRAVERSE-008]
safety:
  - 开门失控时身体绕轴甩出，落点会明显偏离起始位置，落区判断要预留侧向空间
  - 开门过程中不要用单手硬挂对抗，肩关节在这个姿势下负荷方向不利
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

开门是抱石里**最典型的力矩失衡**，也是最值得优先教的一个卡点，
因为它的直觉解法（抓紧一点）**基本无效**。

按 [PHY-TORQUE-003](../physics/PHY-TORQUE-003.md)，
τ = mg · d：体重改不了，力臂 d 可以改。所以四个解释里，
前三个都在处理 d 或者反向力矩，没有一个是「用力抓」。

**这一条对产品的意义**：当视频里观察到明显的身体旋转时，
提示应当指向配平和重心，不应当指向握力。
把「开门」和「握力不足」混淆，是新手长期停滞的常见原因之一。
