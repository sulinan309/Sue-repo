---
id: PRIN-SPEED-005
type: principle
name: 选择合适速度
aliases: [choose appropriate speed, 动作速度, 静态动态选择]
status: active
one_liner: 根据距离、岩点质量和当前稳定性，决定这一步该慢慢够、借一点势，还是整个人跳过去。
meaning: >
  静态和动态不是水平高低之分，是两种适用条件不同的工具。
  静态适合可控、需要精确落点、下一个点难抓的情况；
  动态适合距离超出静态可达范围、或者维持静态的代价过高的情况。
  选错速度，比动作本身做得不标准更容易掉。
physics: [PHY-MOMENTUM-007, PHY-ECONOMY-008]
observables:
  - 动作是匀速可控，还是有明显加速与释放
  - 到达新岩点时身体是否还在移动（有无残余速度）
  - 动态之前有没有预备下沉动作
  - 是否出现长时间停顿后才启动（犹豫）
techniques: [TEC-STR-SPEED-001, TEC-PER-READ-001]
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

## 原则含义

速度选择本质上是在两种成本之间取舍：

| | 静态 | 动态 |
| --- | --- | --- |
| **优点** | 落点精确、可以中途放弃、抓不住能收回 | 可达距离更远、不需要长时间维持高负荷 |
| **代价** | 全程需要维持支撑，负荷时间长 | 落点误差大、抓不住通常直接掉、对新点冲击力大 |

所以判据不是「哪个更高级」，而是：

> **这一步用静态需要维持多久的高负荷？超出能力，就该借势。**

## 中间档：死点

死点（deadpoint）是最常被忽略的一档。它不是全身腾空的跳跃，
而是**有手还在点上的受控上升**：身体向上运动，在轨迹最高点竖直速度为零，
此时抓住新点所需的额外力最小。

死点的价值在于：拿到了动态的可达距离，同时保留了静态的一部分可控性。
它是新手从「全静态」过渡到「敢动态」之间最实用的一档，
也是首批技巧里 [TEC-STR-SPEED-001](../techniques/TEC-STR-SPEED-001.md) 的重点。

## 犹豫的代价是可以量化的

停顿本身在消耗体力——维持一个姿势是持续做功的。
路线预看研究显示，读线质量会影响攀爬过程中的停顿和流畅度。
这意味着「速度选择」有相当一部分在上墙之前就已经决定了，
属于 [TEC-PER-READ-001](../techniques/TEC-PER-READ-001.md)（读线）的范围。
