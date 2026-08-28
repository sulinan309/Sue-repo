---
id: TEC-POS-ORIENT-002
type: technique
name: 正身与侧身
aliases: [frontal and side-on, 转髋, 开胯, 侧拉姿势, twist lock]
layer: 身体位置
status: active
one_liner: 通过转髋改变身体朝向，把肩膀送近目标点，同时让髋靠近墙面减轻手上负荷。
solves:
  - 正对墙面时够不到斜上方的点
  - 手上负荷太重、前臂很快就泵
  - 侧拉点用不上力
prerequisites: [TEC-POS-COM-001, TEC-CON-LOAD-002]
applies_to:
  wall_angle: [vertical, overhang, roof]
  hold_types: [sidepull, undercling, crimp, pinch]
  move_direction: [up, lateral]
  grade_range: "V1-V10"
not_applicable:
  - 板墙上大部分情况，正身站立更能把重量压在脚上
  - 需要双手同时正向下拉的对称动作
principles: [PRIN-STABLE-002, PRIN-COM-003]
physics: [PHY-TORQUE-003, PHY-OPPOSITION-005, PHY-ECONOMY-008]
phases:
  prepare: 判断要够的点在哪一侧，确定用同侧的脚外侧还是异侧的脚内侧承重。
  execute: 转动骨盆使一侧髋部靠向墙面，同侧肩膀随之向上向前送出，手臂尽量保持伸直。
  stabilize: 转体到位后髋部贴住墙面，用这个姿势完成抓握，再决定是否转回正身。
observables:
  - 骨盆是否发生明显旋转（看髋部朝向而不是肩膀）
  - 髋部与墙面的距离在转体前后有没有变化
  - 够点的那只手臂是伸直的还是屈着的
  - 承重脚用的是内侧还是外侧
  - 两脚水平间距是否长期大于一倍躯干长（宽对称站姿会迫使身体保持正对墙面）
faults: [FAULT-SQUARE-REACH-008, FAULT-HIP-SAG-004, FAULT-PRESET-TWIST-017]
hints:
  - 试试把够点那一侧的髋转向墙面。
  - 转个身，用脚的外侧踩。
  - 手别拉，先让髋贴上去。
tasks: [TASK-SIDE-ON-009, TASK-STRAIGHT-ARM-010, TASK-TWIST-WHILE-MOVING-019]
safety:
  - 转髋需要一定的髋关节活动度，热身不足时容易造成内收肌或髋屈肌拉伤
  - 转体状态下掉落时身体是侧向的，落地缓冲比正身掉落更难控制，练习时降低高度
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

侧身同时改善两件事，这是它值得单独成为一个技巧单元的原因。

**第一，缩短力臂，减轻手上负荷。**

按 [PHY-TORQUE-003](../physics/PHY-TORQUE-003.md)，把手点近似为转轴，
体重对手点产生的力矩正比于**重心到墙面的水平距离**。

正身面对仰角墙时，髋部被身体厚度顶在离墙较远的位置；
转髋侧身之后，一侧髋部可以贴到墙面上，重心到墙的距离显著缩短，
手上需要承担的拉力随之下降。这就是「髋部贴墙让手更省力」的机制。

**第二，增加有效触及距离。**

转髋会把同侧肩膀向上向前送出。手臂长度没变，但**肩关节的起点位置变了**，
所以指尖能到的位置更远。同时手臂可以保持相对伸直，
按 [PHY-ECONOMY-008](../physics/PHY-ECONOMY-008.md)，直臂比屈臂省，
因为不需要肱二头肌持续等长收缩。

**第三个附带好处**：侧身姿势下，承重脚外侧蹬和手拉之间天然形成对抗
（[PHY-OPPOSITION-005](../physics/PHY-OPPOSITION-005.md)），
这让侧拉点变得可用。

## 动作要点

1. **判断方向**：要够右上方的点，就转成右髋贴墙。
2. **转的是骨盆，不是肩膀**。只扭肩膀不转髋，力臂没有缩短，白转。
3. **承重脚换成外侧**。正身用内侧，侧身用外侧，这是配套的。
4. **手臂保持伸直**。侧身的价值有一半在于让手能直着挂住。

**什么时候不该侧身**：板墙上正身站立才能把重量压在脚上
（见 [PHY-FRICTION-004](../physics/PHY-FRICTION-004.md)），
侧身反而会减少脚上的法向力。**侧身是陡墙技巧，不是通用姿势。**

## 常见问题

**「我转了但没觉得省力」** → 检查转的是不是骨盆。
只扭上半身是最常见的无效版本，见 [FAULT-SQUARE-REACH-008](../faults/FAULT-SQUARE-REACH-008.md)。

**「侧身之后脚掉了」** → 转体过程中核心松掉，髋部下坠，
见 [FAULT-HIP-SAG-004](../faults/FAULT-HIP-SAG-004.md)。

**「我站得很宽很稳，为什么手还是累？」** → 宽的对称站姿确实稳，
但它把骨盆锁在正对墙面的方向上，转髋的空间被两条腿撑没了。
稳定性来自站姿，代价记在手臂上——这时候要做的不是站得更稳，
是**收窄一只脚、把空间让给转髋**。

判断依据：两脚水平间距长期大于一倍躯干长，同时双肘长时间同时弯曲。
两个都是从普通视频能直接量的。

**「我知道要转髋，但什么时候转？」** → 这个单元讲的是**位置**，不是**时序**。
转体应当与出手同时发生、髋先贴墙手后出，先侧好再出手在仰角上会失败。
时序单独存在 [TEC-MOV-TWIST-004](TEC-MOV-TWIST-004.md)——
那部分是教学共识，与本单元的研究证据等级不同，按规范拆开。

**「侧身和折膝是一回事吗？」** → 不是。侧身是身体朝向，折膝是一种更强的髋部旋转，
额外建立了两脚之间的对抗，见 [TEC-MOV-DROPKNEE-003](TEC-MOV-DROPKNEE-003.md)。
折膝可以看作侧身的加强版，但膝关节负荷高得多。

## 科普脚本素材

> **钩子**：为什么髋部贴墙会让手更省力？
>
> **类比**：拎一个箱子，贴着身体拎 vs 伸直手臂拎。箱子一样重，
> 但伸直手臂拎不了几秒——因为力臂变长了。
> 你挂在墙上时，**你就是那个箱子**，你的髋离墙多远，手就多累。
>
> **演示**：同一个仰角动作，正身做——手臂弯着，5 秒就想掉。
> 转髋侧身，髋贴墙——手臂是直的，可以挂很久。
>
> **结论**：陡墙上觉得手快废了，先别加握力——**转个髋，让它贴上去。**
