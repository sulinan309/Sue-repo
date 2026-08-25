---
id: TEC-POS-COM-001
type: technique
name: 重心转移
aliases: [center of mass shift, 重心移动, 移重心, weight shift]
layer: 身体位置
status: active
one_liner: 在松开任何一个接触点之前，先把身体的重量移动到剩下的接触点撑得住的位置。
solves:
  - 手已经离目标很近却不敢松手
  - 够不到下一个点
  - 释放脚的瞬间身体被拽走
  - 横移时中途卡住进退两难
prerequisites: [TEC-CON-LOAD-002]
applies_to:
  wall_angle: [slab, vertical, overhang]
  hold_types: [any]
  move_direction: [up, lateral, down]
  grade_range: "V0-V10"
not_applicable:
  - 距离超出静态可达范围、必须靠动量完成的动作
principles: [PRIN-COM-003, PRIN-STABLE-002]
physics: [PHY-GRAVITY-COM-001, PHY-EQUILIBRIUM-002, PHY-TORQUE-003]
phases:
  prepare: 判断释放哪个接触点之后，剩下的接触点围出的支撑范围在哪里。
  execute: 主动把髋部移向那个支撑范围，通常是先横向、再竖向，而不是直接斜着伸手。
  stabilize: 确认在新位置上不需要靠即将释放的那个点也能稳住，然后再释放。
observables:
  - 髋部在伸手之前有没有先移动
  - 移动顺序是「先移重心后伸手」还是「先伸手身体被拖过去」
  - 释放脚之前重心是否已经离开那只脚
  - 横移过程中髋部是否贴着一条连续路径，还是分几次跳跃式调整
faults: [FAULT-REACH-FIRST-005, FAULT-BARNDOOR-016, FAULT-STUCK-TRAVERSE-006]
hints:
  - 伸手之前，先把髋往那边送一点。
  - 试试先把重量换到另一只脚上，再松手。
  - 你的手其实够得到，问题是重心还在原来的位置。
tasks: [TASK-HIP-FIRST-005, TASK-TRAVERSE-COM-006]
safety:
  - 重心转移过程中身体处于过渡状态，若判断失误容易产生非预期摆荡，练习时确认落区无人
  - 大幅重心转移对髋关节活动度要求较高，热身不足时容易拉伤内收肌群
beta_refs: []
cases: []
sources:
  - type: research
    ref: "Biomechanical Principles and Techniques—A Systematization for Sport Climbing"
    url: https://pmc.ncbi.nlm.nih.gov/articles/PMC13027491/
evidence_level: 研究证据
review:
  status: pending
  fact: null
  climb: null
  teaching: null
  version: 0.1.0
  updated: 2026-08-25
---

## 物理原理

这是整个技巧库的枢纽，因为它直接对应 [PRIN-COM-003](../principles/PRIN-COM-003.md)：
**攀岩是在搬运重心，手脚只是支点。**

按 [PHY-EQUILIBRIUM-002](../physics/PHY-EQUILIBRIUM-002.md)，
身体静止需要合力和合力矩同时为零。释放一个接触点，等于删掉一个约束。
删掉之后如果两个条件不再满足，身体就会开始运动——不管你握力多大。

所以「先移动，再释放」不是风格建议，是一个**几何上的必要条件**：

> 松手之前，重心必须已经进入「剩下接触点」所围出的支撑范围。

「够不到」在多数情况下也是这个问题的另一种表现。
手臂长度是固定的，但**重心到目标点的距离是可变的**——
髋往目标侧移动 20 厘米，手就少伸 20 厘米。
这解释了为什么身高相近的两个人，一个够得到一个够不到。

## 动作要点

1. **先问：松开哪个点？** 明确要释放的是哪只手或哪只脚。
2. **再问：剩下的点围出什么范围？** 两点是一条线，三点是一个面。
3. **把髋送进那个范围**。髋是重心的视觉代理，送髋就是送重心。
4. **确认能稳住，再释放**。测试方法：轻轻放松那只手，看身体动不动。

**移动顺序很重要**：先横向把重心换到支撑侧，再向上，通常比斜着一步到位更可控。

## 常见问题

**「我知道要移重心，但不知道往哪移」** → 支撑范围在哪，就往哪移。
两点支撑时移向两点的连线；三点支撑时移向三角形内部。

**「一移重心就开门」** → 说明移动的方向和支撑范围不一致，
或者需要旗式提供反向力矩，见 [TEC-MOV-FLAG-001](TEC-MOV-FLAG-001.md)。

**「横移到一半卡住了」** → 见 [FAULT-STUCK-TRAVERSE-006](../faults/FAULT-STUCK-TRAVERSE-006.md)。
典型原因是重心提前离开了出发脚，但还没进入目标脚的支撑范围。

## 科普脚本素材

> **钩子**：你以为你够不到，其实你只是站错了地方。
>
> **演示**：同一个人，同一条线，同一个点。第一次直接伸手——差 10 厘米。
> 第二次先把髋往左送一下再伸手——碰到了。手臂没变长，变的是重心的位置。
>
> **类比**：拿高处柜子上的东西，你不会站在原地把手臂拉长，你会**先走过去**。
> 墙上是一样的，只是那一步是用髋走的。
>
> **结论**：下次觉得够不到的时候，别急着更用力——**先看看你的髋在哪。**
