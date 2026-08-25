---
id: TEC-PER-READ-001
type: technique
name: 读线与动作排序
aliases: [route reading, previewing, 看线, 预演, beta reading, 读图]
layer: 感知与决策
status: active
one_liner: 上墙之前先看出手脚顺序和关键点，把决策放在地面完成，减少墙上的停顿。
solves:
  - 爬到一半不知道下一步该抓哪里
  - 在墙上停很久想办法，体力耗光
  - 上错手序，到关键点时手不对、动不了
  - 每次尝试都从头重新试，没有积累
prerequisites: []
applies_to:
  wall_angle: [slab, vertical, overhang, roof]
  hold_types: [any]
  move_direction: [up, lateral, down]
  grade_range: "V0-V12"
not_applicable:
  - 需要靠身体实际感受才能确定的细节（岩点的具体摩擦、确切握感）
  - flash 或 onsight 之外的多次尝试中，读线应当结合上次的实际反馈而不是重新空想
principles: [PRIN-SPEED-005, PRIN-COM-003]
physics: [PHY-ECONOMY-008, PHY-GRAVITY-COM-001]
phases:
  prepare: 从地面找出起步点和结束点，确认线路的颜色标记和边界。
  execute: 从下往上把线路分成 2-4 段，逐段确定手序、脚点和身体朝向；对关键段做一次身体预演。
  stabilize: 上墙前在脑中过一遍完整顺序，特别是关键段之前的那两三步。
observables:
  - 上墙前是否有可见的地面观察和预演动作
  - 墙上的停顿次数和总停顿时长
  - 是否出现明显的「上错手」后回退或换手
  - 同一线路的第二次尝试，动作顺序是否与第一次不同
faults: [FAULT-NO-PLAN-014, FAULT-WRONG-HAND-015, FAULT-HESITATE-013]
hints:
  - 先从结束点倒着看回来，看哪只手需要抓最后那个点。
  - 这条线的脚点你看了吗？只看手点会漏掉一半信息。
  - 上次你卡在第三步，这次上墙前把前三步的手序在地面过一遍。
tasks: [TASK-READ-BEFORE-017, TASK-BACKWARD-READ-018]
safety:
  - 读线时站在墙下观察，注意避开正在攀爬者的落区
  - 地面预演动作幅度不宜过大，避免在垫子边缘失去平衡
beta_refs: []
cases: []
sources:
  - type: research
    ref: "Efficacy of pre-ascent climbing route visual inspection in indoor sport climbing"
    url: https://pubmed.ncbi.nlm.nih.gov/20561271/
  - type: research
    ref: "Cognitive-behavioural processes during route previewing in bouldering"
    url: https://pubmed.ncbi.nlm.nih.gov/38740079/
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

读线是十个技巧里唯一一个**不发生在墙上**的，但它有明确的物理收益。

按 [PHY-ECONOMY-008](../physics/PHY-ECONOMY-008.md)，
挂在墙上「想一想」时，外力做功为零，但屈指肌的等长收缩在持续消耗代谢能量。
换句话说：**停顿不产生任何位移，却在全速消耗你的前臂。**

对一条 V3 来说，在墙上多想 20 秒的代价，往往比一个不够标准的动作大得多。

路线预看研究显示，上墙前的视觉检查会影响攀爬过程中的停顿和流畅度；
更高水平的攀岩者在线索获取、动作序列记忆和行动能力判断上也表现更好。
这两条支持一个结论：**读线是可以练的技能，不是天赋，也不是可有可无的准备动作。**

第二个收益是**减少无效尝试**。上错手序意味着到关键点时手不对，
只能回退或强行换手——两者都是额外消耗。

## 动作要点

1. **先找起点和终点**。确认颜色标记和线路边界，避免爬串线。
2. **分段，不要逐步**。把线路分成 2-4 段记，比记 15 个独立动作可靠得多
   （这利用了动作组块）。
3. **倒着读关键段**。从结束点往回推：最后那个点需要哪只手？
   往前一步呢？这样能算出手序，避免到顶才发现手反了。
4. **一定要看脚点**。新手读线最大的漏洞是只读手点。
   脚点决定了重心能到哪里，而重心决定了手够不够得到。
5. **做一次身体预演**。在地面用手比划关键段，比纯粹在脑子里想记得牢。
6. **第二次尝试要用上次的信息**。读线不是每次从零开始空想，
   是把上次实际爬到的反馈加进来。

## 常见问题

**「我读了但一上墙就忘」** → 通常是记了太多独立动作。改成分段记，
每段只记一个关键点和一个身体朝向。

**「读线要读多久？」** → 没有统一答案。但一个实用判据是：
**能不能说出关键段的手序**。说不出来，读线还没完成。

**「我读的和实际爬的不一样，是不是白读了」** → 不是。
读线的价值有一半是建立预期，实际和预期不符本身就是重要信息——
它告诉你哪一步的判断需要修正。这正是产品把「上次卡在哪里」
带回下一次读线的价值所在。

## 科普脚本素材

> **钩子**：你在墙上想的每一秒，都在花前臂的钱。
>
> **对比**：两个人爬同一条 V3。
> A 上去就爬，卡在第四步，停了 15 秒想办法，然后掉了。
> B 在地面看了 40 秒，上去一口气爬完。
> B 不是力气比 A 大——**B 把想的部分放在了不用挂着的时候。**
>
> **实操**：读线记三件事就够了——
> ①结束点用哪只手；②中间哪一步最难；③那一步的脚踩哪儿。
> 倒着往回推，手序自然就出来了。
>
> **结论**：下次上墙前多花 30 秒。这 30 秒是免费的，墙上那 15 秒不是。
