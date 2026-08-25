---
id: TEC-CON-LOAD-002
type: technique
name: 脚点加载
aliases: [loading the foothold, 踩实, 压脚, 加载, weighting the feet]
layer: 手脚组件
status: active
one_liner: 踩准之后，主动把重量和压力交给这只脚，让它真正变成支点而不是摆设。
solves:
  - 踩到了但站不起来
  - 踩到了但一伸手脚就掉
  - 明明有脚点，重量却全挂在手上
prerequisites: [TEC-CON-FOOT-001]
applies_to:
  wall_angle: [slab, vertical, overhang, roof]
  hold_types: [foothold, edge, smear, volume, pocket]
  move_direction: [up, lateral]
  grade_range: "V0-V10"
not_applicable:
  - 脚点确实无法承重的极小点，此时应当调整解法而不是硬加载
principles: [PRIN-CONTACT-001, PRIN-LEGS-004]
physics: [PHY-FRICTION-004, PHY-OPPOSITION-005, PHY-KCHAIN-006]
phases:
  prepare: 确认脚已经在有效受力面上，判断这面墙需要的是重力加载（板墙、直墙）还是主动对抗加载（仰角）。
  execute: 板墙和直墙上把髋部移到脚的上方，让体重压下去；仰角墙上主动蹬压并同时收紧核心把髋部拉向墙面。
  stabilize: 加载建立之后再开始移动手，移动过程中持续维持这个压力，不因为伸手而放松。
observables:
  - 踩上去之后脚踝和小腿是否明显承力（形态变化）
  - 髋部是否移动到脚的上方（板墙、直墙）
  - 仰角墙上髋部是否被主动拉向墙面，还是下坠
  - 伸手的瞬间脚是否脱落
faults: [FAULT-FOOT-CUT-003, FAULT-HIP-SAG-004, FAULT-FOOT-SLIP-001]
hints:
  - 先把重量压到那只脚上，再考虑伸手。
  - 试试把髋往那只脚的正上方送一点。
  - 伸手的时候，脚上的力不要松。
tasks: [TASK-WEIGHT-FOOT-003, TASK-NO-CUT-004]
safety:
  - 仰角墙上主动加载对核心和髋屈肌负荷较高，出现下背部不适应当停止
  - 脚点加载失败导致的脚脱落会产生摆荡，摆荡时优先保护落地姿势而不是继续抓点
beta_refs: []
cases: []
sources:
  - type: research
    ref: "Biomechanical Principles and Techniques—A Systematization for Sport Climbing"
    url: https://pmc.ncbi.nlm.nih.gov/articles/PMC13027491/
evidence_level: 专家共识
review:
  status: pending
  fact: null
  climb: null
  teaching: null
  version: 0.1.0
  updated: 2026-08-25
---

## 物理原理

「踩准」和「踩住」是两件不同的事。踩准解决的是接触位置，
加载解决的是**法向力 N 从哪里来**。

按 [PHY-FRICTION-004](../physics/PHY-FRICTION-004.md)，可用摩擦上限是 μN。
脚放在点上但 N ≈ 0，摩擦上限也 ≈ 0，这只脚等于不存在。

关键在于：**不同墙角，N 的来源完全不同。**

| 墙面 | N 的来源 | 操作 |
| --- | --- | --- |
| 板墙 / 直墙 | 重力的法向分量 | 把髋移到脚的上方，站直，让体重压下去 |
| 仰角 / 屋檐 | 身体主动产生的对抗力 | 蹬压 + 收紧核心把髋拉向墙面 |

这是同一个技巧在两种条件下的两套操作。混在一起讲，用户在陡墙上会用板墙的方法，
结果就是脚一直掉——这是新手上仰角墙最典型的挫败来源。

仰角上的机制属于 [PHY-OPPOSITION-005](../physics/PHY-OPPOSITION-005.md)：
脚蹬出去的力和手拉回来的力构成一对对抗，这对力互相「压紧」，
脚上的 N 由此产生。核心一松，传递路径断掉，N 归零，脚立刻脱落。

## 动作要点

1. **踩准之后先加载，再动手**。顺序反了，见 [PHY-KCHAIN-006](../physics/PHY-KCHAIN-006.md)。
2. **板墙上：把髋送到脚上方**。不是身体贴墙，是重心压在脚上。
3. **仰角上：主动蹬 + 收核心**。想象用脚尖「勾着」把髋往墙上拉。
4. **移动时不要松**。伸手是身体形状改变最大的时刻，也是最容易漏掉压力的时刻。

## 常见问题

**「踩到了但站不起来」** → 多半不是加载问题，是重心还没移到脚上方，
见 [TEC-POS-COM-001](TEC-POS-COM-001.md) 和 [TEC-MOV-ROCKOVER-002](TEC-MOV-ROCKOVER-002.md)。

**「一伸手脚就掉」** → 见 [FAULT-FOOT-CUT-003](../faults/FAULT-FOOT-CUT-003.md)。
典型的传递路径断裂，不是脚的问题。

**「陡墙上我怎么用力脚都掉」** → 检查髋部是否下坠，
见 [FAULT-HIP-SAG-004](../faults/FAULT-HIP-SAG-004.md)。

## 科普脚本素材

> **钩子**：你踩上去了，为什么它还是不算一个脚点？
>
> **类比**：把一张纸按在墙上，手一松纸就掉。纸没变，你按的力变了。
> 脚点也一样——**脚放上去只是「碰到」，压下去才是「踩住」**。
>
> **转折**：而且板墙和仰角墙上，这个「压」的来源完全不一样。
> 板墙靠体重，你要站起来把重量交给它；
> 仰角靠核心，你要主动把髋拉向墙面。
> 在仰角墙上用板墙那套，脚就会一直掉。
>
> **结论**：下一条线，注意一件事——**伸手的时候，脚上的力有没有松掉**。
