---
id: TEC-CON-FOOT-001
type: technique
name: 精准踩点
aliases: [precise footwork, 静音脚, silent feet, 踩点, 脚法]
layer: 手脚组件
status: active
one_liner: 上墙前先看好脚点，一次把鞋尖放到位，放上去之后不再调整。
solves:
  - 踩上去之后需要二次调整，浪费时间和前臂
  - 脚踩在岩点边缘导致打滑
  - 注意力全在手上，脚随便乱蹬
prerequisites: []
applies_to:
  wall_angle: [slab, vertical, overhang]
  hold_types: [foothold, edge, smear, volume]
  move_direction: [up, lateral, down]
  grade_range: "V0-V10"
not_applicable:
  - 协调类动作中脚点只是短暂借力的过渡步
  - 需要在脚点上主动滑动调整的抹蹭长距离移动
principles: [PRIN-CONTACT-001]
physics: [PHY-FRICTION-004, PHY-GRAVITY-COM-001]
phases:
  prepare: 在移动之前，用眼睛确定要踩的那个点，以及要用鞋的哪个部位（内侧、外侧还是尖端）。
  execute: 眼睛跟着脚走，鞋尖直接落到选好的位置，落点一次到位。
  stabilize: 落点之后不再挪动，直接开始加载重量；脚踝保持稳定，不因为身体移动而跟着晃。
observables:
  - 脚落到岩点之后 0.5 秒内有没有二次调整
  - 踩上去时有没有声音（撞击声通常意味着落点不受控）
  - 眼睛在放脚的时候是否在看脚
  - 鞋接触的是岩点的有效受力面还是边缘
faults: [FAULT-FOOT-SLIP-001, FAULT-FOOT-READJUST-002]
hints:
  - 这一步放脚的时候，眼睛跟着脚看到它落上去。
  - 先想好用鞋的哪一侧，再放上去。
  - 踩上去之后不要再挪，直接把重量交给它。
tasks: [TASK-SILENT-FEET-001, TASK-FOOT-EYES-002]
safety:
  - 精准踩点要求放脚时短暂低头，注意不要在下方有人时长时间失去对落区的观察
  - 疲劳时脚的控制精度下降明显，出现连续踩空应当结束当次尝试而不是继续硬试
beta_refs: []
cases: []
sources:
  - type: research
    ref: "Biomechanical Principles and Techniques—A Systematization for Sport Climbing"
    url: https://pmc.ncbi.nlm.nih.gov/articles/PMC13027491/
  - type: teaching
    ref: "BMC Indoor Climbing Videos — footwork fundamentals"
    url: https://thebmc.co.uk/en/indoor-climbing-videos
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

精准踩点解决的是 [PHY-FRICTION-004](../physics/PHY-FRICTION-004.md) 里的一个前提问题：
**摩擦力上限 μN 只在有效接触面上才成立。**

踩在岩点边缘或圆弧下沿时，接触面的法线方向不再朝向你施力的方向，
你压下去的力大部分变成了让脚滑出去的切向分量。这时候增加力气不但无效，还会加速打滑。

第二个作用是省时间。每一次二次调整都在延长脚未加载的时间，
而这段时间里体重全压在手上——按 [PHY-ECONOMY-008](../physics/PHY-ECONOMY-008.md) 的说法，
这是纯粹的等长收缩消耗，不产生任何位移。

## 动作要点

1. **先选点，再放脚**。移动之前就确定要踩哪里、用鞋的哪一部分。
2. **眼睛跟着脚**。放脚的全过程视线跟随，直到脚落上去。新手最常见的问题是眼睛还在看手。
3. **一次到位**。落点即最终位置，不再调整。
4. **落点之后立刻加载**。踩上去却不敢把重量交出去，等于没踩。

关于鞋的部位：

| 部位 | 适用 |
| --- | --- |
| 内侧（大拇趾一侧） | 正身移动、需要稳定支撑 |
| 外侧（小趾一侧） | 侧身、折膝、需要转髋的动作 |
| 正前方尖端 | 小点、口袋、需要精确落点 |
| 大面积贴合 | 斜面、圆包、体积块 |

## 常见问题

**「我脚老是滑」** → 见 [FAULT-FOOT-SLIP-001](../faults/FAULT-FOOT-SLIP-001.md)。
先区分是落点错（踩在边缘）、加载方向错（法向力不足），还是单纯鞋底脏了。

**「踩上去要动好几次才踏实」** → 见 [FAULT-FOOT-READJUST-002](../faults/FAULT-FOOT-READJUST-002.md)。
通常是没有在移动前选好点，属于读线问题不是脚法问题。

**「静音脚是不是要故意放很慢」** → 不是。目标是**受控**，不是慢。
慢只是初期为了建立控制感的过渡手段，熟练之后速度会自然回来。

## 科普脚本素材

> **钩子**：为什么高手爬墙几乎没声音，而你踩一下整面墙都在响？
>
> **类比**：把脚想成放一个易碎的杯子到桌上。你不会「扔」上去，会看着它落到你想放的位置。
> 岩点也一样——不同的是，杯子摔了只是碎，脚放错了你要用前臂去补。
>
> **结论**：下次上墙，只做一件事——**放脚的时候看着脚**。
> 一整条线都这样爬完，你会发现手比平时轻很多。
