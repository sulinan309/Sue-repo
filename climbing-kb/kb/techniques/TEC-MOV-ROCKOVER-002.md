---
id: TEC-MOV-ROCKOVER-002
type: technique
name: 高脚与压脚站起
aliases: [high step, rock over, 压脚, 站起, rockover]
layer: 具体技巧
status: active
one_liner: 把脚踩到很高的点上，然后把重心移到这只脚的正上方，用腿把身体站起来。
solves:
  - 高脚踩上去了但站不起来
  - 下一个手点太远、需要靠腿争取高度
  - 板墙上没有好手点，只能靠脚站上去
prerequisites: [TEC-POS-COM-001, TEC-CON-LOAD-002]
applies_to:
  wall_angle: [slab, vertical, overhang]
  hold_types: [foothold, edge, volume, jug]
  move_direction: [up]
  grade_range: "V0-V8"
not_applicable:
  - 髋关节活动度不足以把脚放到该高度时，应当先找中间脚点分两步完成
  - 高脚点位于身体正下方、无法让重心移过去的情况
principles: [PRIN-COM-003, PRIN-LEGS-004]
physics: [PHY-GRAVITY-COM-001, PHY-KCHAIN-006, PHY-EQUILIBRIUM-002]
phases:
  prepare: 把脚精准放到高点上，同时判断重心需要往哪个方向移动才能到达这只脚的上方。
  execute: 先横向把髋移到高脚的上方（通常伴随转髋），确认重量已经在这只脚上，再蹬伸膝关节。
  stabilize: 站起过程中用手维持平衡而不是往上拉，站直之后再考虑下一个手点。
observables:
  - 髋部是否移动到高脚的上方（横向位移）
  - 站起的启动是从腿开始还是从手开始
  - 膝关节是否有明显蹬伸
  - 站起过程中另一条腿在做什么（是否提供了配平）
faults: [FAULT-ROCKOVER-STALL-010, FAULT-PULL-FIRST-011, FAULT-REACH-FIRST-005]
hints:
  - 脚已经在上面了，现在把髋送到那只脚的正上方。
  - 别用手拉，先把重量换到高脚上。
  - 试试转一下髋，让身体侧过来，膝盖会更容易伸开。
tasks: [TASK-ROCKOVER-011, TASK-NO-HAND-STEP-012]
safety:
  - 深度屈膝下的蹬伸对膝关节负荷较高，热身不足或膝部有旧伤时降低高脚高度
  - 高脚需要较大髋关节外展和外旋活动度，强行完成容易拉伤内收肌
  - 站起失败时身体重心已经很高，掉落距离比一般动作大，确认落区
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

「高脚以后为什么站不起来」是新手最高频的问题之一，答案几乎总是同一个：

> **重心没有移动到那只脚的上方。**

按 [PHY-GRAVITY-COM-001](../physics/PHY-GRAVITY-COM-001.md)，
腿蹬伸产生的力沿着腿的方向。如果重心在高脚的**侧后方**，
这个力的主要分量是把身体**推离墙面**，只有很小的分量向上——所以蹬了也不上升。

只有当重心移到高脚正上方时，蹬伸方向才与需要的位移方向一致。

第二个因素是**力学劣势**。膝关节在深度屈曲时，伸膝肌群的力臂很短，
可输出的有效力矩最小。这意味着：

- 起始阶段本来就是最费力的；
- 如果同时还要对抗「重心不在脚上」造成的额外负荷，多数人根本推不动。

所以解法不是「腿再用力一点」，是**先把重心送过去，把这个动作变简单**。

第三，[PHY-KCHAIN-006](../physics/PHY-KCHAIN-006.md) 的时序在这里特别关键：

| 顺序 | 结果 |
| --- | --- |
| 移重心 → 蹬腿 → 手维持平衡 | 腿的力转化为向上位移 |
| 先用手拉 → 身体被拉向手 → 重心偏离高脚 | 腿失去有效发力角度，手也很快泵掉 |

两种顺序用的力气一样多，结果完全不同。

## 动作要点

1. **脚要放准放稳**。高脚点通常小，落点错了后面全错。
2. **先横向移髋，再向上**。这是整个动作的核心。多数人卡在这一步。
3. **常常需要转髋**。侧身能让髋更靠近脚的上方，也给膝盖让出伸展空间。
4. **手是平衡器不是发动机**。手向下压比向上拉更有效。
5. **另一条腿配平**。可以外旗，也可以蹬住墙面，防止转开。

## 常见问题

**「踩上去了，身体就是上不去」** → 见 [FAULT-ROCKOVER-STALL-010](../faults/FAULT-ROCKOVER-STALL-010.md)。
先检查髋是否在脚的上方，这一项能解释大部分情况。

**「我用手拉能上去，但特别累」** → 你在用手替腿干活，
见 [FAULT-PULL-FIRST-011](../faults/FAULT-PULL-FIRST-011.md)。短线路能过，长线路会泵死。

**「我腿抬不了那么高」** → 这是活动度问题，不是技巧问题。
先找中间脚点分两步走；长期可以做髋关节活动度练习。**不要靠硬拉硬掰去够**。

## 科普脚本素材

> **钩子**：高脚踩上去了，为什么就是站不起来？
>
> **地面演示**：找一级台阶。脚放上去，身体保持在后面——试着站起来。
> 站不起来，或者非常费劲。
> 现在把身体往前送，让肩膀在膝盖上方——轻松就上去了。
> **台阶没变，你的重心变了。**
>
> **原理一句话**：腿的力是顺着腿的方向出去的。
> 重心在脚的后面，你蹬出去的力是在把自己往墙外推，不是往上送。
>
> **结论**：下次高脚卡住，别加力气——**把髋送到那只脚的正上方**，然后再蹬。
