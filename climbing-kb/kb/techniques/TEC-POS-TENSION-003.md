---
id: TEC-POS-TENSION-003
type: technique
name: 身体张力与对抗
aliases: [body tension, core tension, 核心张力, 张力, 绷住]
layer: 身体位置
status: active
one_liner: 主动收紧从脚到手的整条身体，让脚上的力传得到手上，脚才不会掉出来。
solves:
  - 陡墙上一伸手脚就掉
  - 蹬了腿但身体没有上升
  - 髋部下坠、身体离墙越来越远
  - 抓住了新点但身体荡出去
prerequisites: [TEC-CON-LOAD-002]
applies_to:
  wall_angle: [overhang, roof, vertical]
  hold_types: [any]
  move_direction: [up, lateral]
  grade_range: "V1-V12"
not_applicable:
  - 板墙上大部分情况，过度绷紧反而消耗体力且减少脚上的法向力
  - 需要主动放松借助摆荡的协调类动作
principles: [PRIN-STABLE-002, PRIN-LEGS-004]
physics: [PHY-OPPOSITION-005, PHY-KCHAIN-006, PHY-MOMENTUM-007]
phases:
  prepare: 在开始移动之前先收紧核心，把髋部主动拉向墙面，建立脚到手的连接。
  execute: 移动手或脚的整个过程中维持这个收紧状态，不因为伸手而放松躯干。
  stabilize: 到达新位置后先确认张力仍在，再考虑释放下一个接触点。
observables:
  - 伸手的瞬间脚是否脱落
  - 髋部在移动过程中是保持贴墙还是逐渐下坠
  - 身体是否呈现连贯的整体移动，还是各部分分别动
  - 抓到新点后有没有明显摆荡
faults: [FAULT-FOOT-CUT-003, FAULT-HIP-SAG-004, FAULT-SWING-012]
hints:
  - 伸手之前先把肚子收紧，把髋拉向墙面。
  - 移动的时候脚上的力别松。
  - 试试整个身体一起动，而不是先伸手。
tasks: [TASK-NO-CUT-004, TASK-TENSION-HOLD-014]
safety:
  - 高张力动作对下背部和髋屈肌负荷较大，出现下背部疼痛应当停止
  - 张力练习容易在疲劳时代偿，动作变形后继续练习无效且增加受伤风险
  - 屋檐和大仰角上失去张力会导致身体突然摆出，落区判断要预留侧向和后向空间
beta_refs: []
cases: []
sources:
  - type: research
    ref: "Biomechanical Principles and Techniques—A Systematization for Sport Climbing"
    url: https://pmc.ncbi.nlm.nih.gov/articles/PMC13027491/
  - type: research
    ref: "Development of Specific Motor Skills through System Wall Bouldering Training"
    url: https://pmc.ncbi.nlm.nih.gov/articles/PMC11250695/
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

张力是**传递条件**，不是一块肌肉。

按 [PHY-OPPOSITION-005](../physics/PHY-OPPOSITION-005.md)，
陡墙上脚点的法向力不来自重力——重力在把你拉离墙面。
N 只能来自手拉、脚蹬构成的一对对抗力。

这对力要成立，两个接触点之间必须有一条**刚度足够的连接路径**。
路径就是身体本身：脚 → 小腿 → 大腿 → 骨盆 → 躯干 → 肩 → 手臂 → 手。

如果核心松掉，髋部下坠，脚蹬出去的力就消耗在躯干自身的形变上，
传不到手上。对抗关系断裂，脚上的 N 归零，脚立刻脱落。

这解释了那个最典型的抱怨：

> 「我脚明明踩住了，一伸手脚就掉。」

**不是脚踩得不准，是链断了。** 伸手的瞬间躯干形状改变，
如果没有主动维持刚度，传递路径失效。

同一个机制也解释了「蹬了但没上去」——
按 [PHY-KCHAIN-006](../physics/PHY-KCHAIN-006.md)，
腿的力被躯干形变吃掉，没有转化为重心位移。

## 动作要点

1. **张力是主动的，不是姿势**。摆好姿势不等于绷住了。
2. **收紧的时机在移动之前**。伸手到一半才想起来收，已经晚了。
3. **重点是把髋拉向墙面**。这是判断张力有没有建立最直观的标志。
4. **整条链一起收**。腹、背、髋、肩都参与；只收腹肌解决不了问题。
5. **移动全程维持**。到位之后才能松。

**注意**：张力不是越紧越好。板墙上过度绷紧既费体力，
又会让重心离开脚（减少法向力，见 [PHY-FRICTION-004](../physics/PHY-FRICTION-004.md)）。
**张力是陡墙工具。**

## 常见问题

**「张力是不是就是核心力量？」** → 有关但不等同。
张力是**整条链的刚度和时序控制**，属于技巧；核心力量是能力上限，属于力量库。
很多人核心力量不差，但不知道什么时候该收、收哪里——那是技巧问题。

**「我一伸手脚就掉，是核心太弱吗？」** → 先别下这个结论。
从视频能看到的是「伸手瞬间髋部下坠、脚脱落」——这是`可确认事实`。
「你核心弱」是`专家假设`，产品不应该自动输出。
可能的解释至少有三个：没有主动收紧、收紧时机晚、脚点方向本身不支持对抗。
见 [FAULT-FOOT-CUT-003](../faults/FAULT-FOOT-CUT-003.md)。

**「怎么知道张力够不够？」** → 一个可自测的标准：
伸手到最远的时候，**脚还在不在原来的点上，髋有没有掉下去**。

## 科普脚本素材

> **钩子**：为什么你一伸手，脚就掉了？
>
> **类比**：用一根木棍撑在两面墙之间，撑得住。
> 换成一根绳子——同样两面墙，同样长度，撑不住。
> 差别不在长度，在**刚度**。
>
> **在墙上**：你的脚要踩住陡墙上的点，靠的不是重力，是手和脚互相「撑开」。
> 你的身体就是中间那根棍子。
> 一伸手，如果肚子松了，棍子变成绳子——**脚不是滑掉的，是被松掉的。**
>
> **结论**：伸手之前，先收肚子，把髋拉向墙。顺序反过来就来不及了。
