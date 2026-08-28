---
id: PRIN-CONTACT-001
type: principle
name: 优化墙面接触
aliases: [optimize contact, 接触优化, 用好手脚点]
status: active
one_liner: 手脚以合适的方向和面积接触岩点，让岩点能提供这一步真正需要的那个方向的力。
meaning: >
  岩点本身不产生力，它只是提供一个可以承受特定方向受力的接触面。
  同一个岩点，向下压、向外拉、向内扣，可用的力完全不同。
  接触优化要解决的是：这一步需要什么方向的力，怎样接触才能拿到它。
physics: [PHY-FRICTION-004, PHY-OPPOSITION-005]
observables:
  - 脚是否踩在岩点的有效受力面上，还是踩在边缘或圆弧下沿
  - 踩上去之后脚有没有二次调整、滑动或抖动
  - 手的受力方向与岩点开口方向是否一致
  - 鞋底与岩点的接触面积是大面积贴合还是只有一个尖端
techniques: [TEC-CON-FOOT-001, TEC-CON-LOAD-002, TEC-CON-SWAP-003]
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
  version: 0.1.1
  updated: 2026-08-29
---

## 原则含义

新手最容易把岩点理解成「抓住就行」。实际上每个岩点都有一个**有效受力方向区间**：
超出这个区间，无论用多大力气，岩点都不给你支撑。

一个平坦的踩点，垂直向下压时可用力最大；斜面点（slab hold）只在持续施加法向压力时才有摩擦；
侧拉点（sidepull）必须配合一个反方向的力才能加载。

所以「接触优化」不是「抓紧一点」，而是**先判断这一步要什么方向的力，再决定怎么放手脚**。

## 在视频里怎么看

这是五个原则里最容易从普通手机视频观察的一个：

- **脚点**：看鞋尖落点和落点之后 0.5 秒内有没有微调；
- **手点**：看手腕角度——手腕方向大致指示了受力方向；
- **滑动**：脚滑是接触方向错误最直接的证据，不需要推断。

## 与其他原则的关系

接触优化是另外四个原则的前提。重心移不过去，常常不是因为不知道要移，
而是因为**脚点没踩住，不敢把重量交上去**。所以产品在给提示时，
应当优先检查接触问题，再讨论重心和速度。
