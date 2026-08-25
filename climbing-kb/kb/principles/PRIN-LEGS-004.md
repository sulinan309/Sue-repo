---
id: PRIN-LEGS-004
type: principle
name: 由腿部启动
aliases: [initiate from the legs, 用腿爬, 腿部驱动]
status: active
one_liner: 主要的位移由腿和髋产生，手臂负责维持方向和平衡，不负责把身体拉上去。
meaning: >
  下肢的肌肉体积和可持续输出功率远大于前臂和上肢。
  用腿产生位移、用手维持平衡，是同一条线路上最省力的分工。
  这条原则同时解释了两件事：为什么新手爬两条线就前臂泵爆，
  以及为什么高手看起来「没怎么用力」。
physics: [PHY-KCHAIN-006, PHY-ECONOMY-008]
observables:
  - 向上移动时膝关节是否有明显蹬伸
  - 手臂在移动过程中是长期屈臂，还是保持相对伸直
  - 位移开始的瞬间，先动的是脚/髋还是手
  - 前臂是否过早出现明显疲劳表现（甩手、频繁调整握姿）
techniques: [TEC-MOV-ROCKOVER-002, TEC-POS-TENSION-003, TEC-CON-LOAD-002]
sources:
  - type: research
    ref: "Biomechanical Principles and Techniques—A Systematization for Sport Climbing"
    url: https://pmc.ncbi.nlm.nih.gov/articles/PMC13027491/
  - type: research
    ref: "Sport climbing performance determinants and functional testing methods"
    url: https://pubmed.ncbi.nlm.nih.gov/39216626/
evidence_level: 研究证据
review:
  status: pending
  fact: null
  climb: null
  teaching: null
  version: 0.1.0
  updated: 2026-08-25
---

## 原则含义

「用腿爬，不要用手拉」是岩馆里最常听到的一句建议，但它常常没被解释清楚，
所以用户听完还是不知道该做什么。

准确的表述是：

> **位移由腿产生，方向由手控制。**

手不是不用力——陡墙上手的负荷很大——而是手的力主要用来**把身体维持在墙上**
（法向、防止旋转），不是用来**把身体提上去**（切向位移）。

## 为什么这样更省力

两个原因叠加：

1. **肌肉体积**：下肢伸肌群的横截面积远大于前臂屈指肌群，同样的相对负荷下，
   腿的绝对输出高得多。
2. **疲劳恢复**：前臂屈指肌在持续等长收缩时，血流受阻，恢复慢；
   这是攀岩「泵感」的主要来源。腿部动作多为动态收缩，代谢条件好得多。

所以把负荷从前臂转到腿，不只是这一步更轻松，是**整场攀爬的续航都变长**。

## 张力是传递条件

腿产生的力要变成重心位移，必须经过骨盆和躯干传到接触点。
如果核心松掉，髋部下坠，腿蹬出来的力大部分消耗在身体自身变形上，
传不到手上。这是「明明蹬了但身体没上去」的常见机制。

因此这条原则和 [PHY-KCHAIN-006](../physics/PHY-KCHAIN-006.md)（动作链）、
[TEC-POS-TENSION-003](../techniques/TEC-POS-TENSION-003.md)（身体张力）必须一起看。
