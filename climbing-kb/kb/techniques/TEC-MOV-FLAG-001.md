---
id: TEC-MOV-FLAG-001
type: technique
name: 旗式
aliases: [flagging, 挂旗, 外旗, 内旗, 后旗, back flag]
layer: 具体技巧
status: active
one_liner: 用一条不承重的腿改变重心位置或蹬住墙面，抵消让身体转开的力矩。
solves:
  - 有效支撑点集中在身体同一侧时的开门
  - 只有一个脚点可用、又必须横向移动
  - 换脚成本太高但需要改变身体朝向
prerequisites: [TEC-POS-COM-001]
applies_to:
  wall_angle: [slab, vertical, overhang]
  hold_types: [sidepull, crimp, jug, pinch]
  move_direction: [lateral, up]
  grade_range: "V0-V8"
not_applicable:
  - 双脚都必须承重的高张力仰角段
  - 旗腿无处可蹬且身体已经完全展开、重心无法再调整时
principles: [PRIN-STABLE-002, PRIN-COM-003]
physics: [PHY-TORQUE-003, PHY-EQUILIBRIUM-002, PHY-GRAVITY-COM-001]
phases:
  prepare: 判断身体会往哪个方向转开——通常是有效接触点连线的另一侧。
  execute: 把非承重的那条腿送向开门的反方向，或者送到墙面上可以蹬住的位置。
  stabilize: 旗腿保持张力不松垮，确认身体停止旋转趋势之后再释放手。
observables:
  - 非承重腿是否越过身体中线送到另一侧
  - 旗腿是悬空（靠质量）还是蹬在墙上（靠反作用力）
  - 送出旗腿之后身体的旋转和摆动是否减少
  - 旗腿是绷住的还是松垂的
faults: [FAULT-BARNDOOR-016, FAULT-LIMP-FLAG-007]
hints:
  - 试试把另一条腿送到身体的另一侧。
  - 你被转开的方向，就是旗腿要去的方向。
  - 旗腿别松着，让它蹬住墙。
tasks: [TASK-FLAG-SWITCH-007, TASK-ONE-FOOT-TRAVERSE-008]
safety:
  - 旗腿蹬墙时确认蹬的位置不是松动的岩点或体积块边缘
  - 开门失控时身体会绕轴甩出，落区判断应当按「会被甩向侧面」预估，不是垂直下落
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

旗式是 [PHY-TORQUE-003](../physics/PHY-TORQUE-003.md) 最直接的应用。

**开门的成因**：当左手和左脚都在身体左侧时，这两个接触点连成一条近似竖直的轴。
重心落在轴的右侧，水平距离 d，重力产生力矩 **τ = mg · d**，把身体绕轴向右后方转开。
没有反向力矩，身体必然转走——这与握力无关。

式子里 **mg 改不了，d 可以改**。旗式提供两条路径：

| 类型 | 做法 | 机制 |
| --- | --- | --- |
| **内旗** | 非承重腿送到承重腿的墙面一侧、身体前方 | 主要靠腿的质量把重心拉向轴，**减小 d** |
| **外旗 / 后旗** | 非承重腿从身后交叉送到另一侧，蹬住墙面 | 蹬墙的反作用力产生**反向力矩 τ'** |

外旗的效果通常更强，因为蹬墙力可以主动调节，而腿的质量是固定的。
内旗更容易做，适合板墙和直墙上的小幅调整。

**关键判断**：旗腿要去的方向 = 身体被转开的方向。
新手最常见的错误是把腿送错边，结果 d 变大，开门更严重。

## 动作要点

1. **先判断转开方向**。接触点在左侧，身体就往右转开，旗腿送右边。
2. **腿要送过中线**。送出去半步没有意义，质量分布没有实质改变。
3. **旗腿要绷住**。松垮的腿只贡献质量不贡献力矩，效果打对折。
   见 [FAULT-LIMP-FLAG-007](../faults/FAULT-LIMP-FLAG-007.md)。
4. **能蹬墙就蹬墙**。哪怕只是脚尖点在光墙面上，摩擦也能提供可观的反向力矩。

## 常见问题

**「我旗了但还是开门」** → 三种可能：方向送反了、腿没过中线、腿是松的。
按这个顺序检查。

**「旗式和换脚，什么时候用哪个？」** → 换脚更稳但成本高（需要一个能站两次的点，
且换脚过程本身是不稳定窗口）。旗式更快、不需要额外脚点，但维持时间有限。
短距离横移优先旗式，需要长时间停留优先换脚。

**「内旗外旗怎么选？」** → 看旗腿有没有地方蹬。有墙面可蹬且需要强力矩 → 外旗；
只是微调平衡、或者外旗空间不够 → 内旗。

## 科普脚本素材

> **钩子**：为什么你一松手就像一扇门一样被甩开？
>
> **演示**：手和脚都在左边，松右手——身体绕着「左手到左脚」这条线转开。
> 这不是力气问题，是你少了一样东西：**反方向的重量**。
>
> **类比**：拎一桶水走路，你会自然把另一只手甩到另一边。
> 没人教过你，但你的身体知道要配平。旗式就是把这件事在墙上做出来。
>
> **结论**：记一句话就够了——**你被转开的方向，就是那条腿要去的方向。**
