---
id: PHY-KCHAIN-006
type: physics
name: 动作链与力量传递
aliases: [kinetic chain, 动力链, 力量传递, 发力顺序]
status: active
one_liner: 腿产生的力要经过髋、躯干、肩才能变成重心位移，中间任何一节松掉，力就漏掉了。
strict_definition: >
  动作链指多个环节按顺序传递力与动量的运动学结构。
  近端环节（下肢、髋）先产生力，通过刚性连接依次传向远端环节（躯干、肩、手）。
  链上任一环节的刚度不足，都会使该处发生形变吸收能量，降低传递到末端的有效力与动量。
plain_explanation: >
  用鞭子甩出去，力是从手腕一路传到鞭梢的。
  如果中间有一段是软绳打了结，力到那儿就散了。
  你在墙上蹬腿，力要经过髋、腰、背、肩才能真正把身体送上去；
  腰一软，腿使多大劲都白费。
model_assumptions:
  - 把身体简化为若干刚性节段通过关节连接
  - 假设发力顺序为近端到远端（实际中攀岩存在多种发力模式）
  - 忽略肌肉—肌腱的弹性储能（实际中它对动态动作有实质贡献）
key_variables:
  - 各环节刚度（主要由主动肌力维持）
  - 发力时序（先后顺序错了会互相抵消）
  - 关节活动范围（不够就传不过去）
climbing_manifestation:
  - 蹬腿的同时髋部下坠 → 力在腰部漏掉，身体没有上升
  - 高脚站起时先用手拉 → 发力顺序反了，腿的贡献被浪费
  - 动态起跳的力来自腿的蹬伸，经躯干传到手；核心松则跳不高
  - 「手臂很泵但腿完全不累」是链条断在髋部的典型信号
techniques: [TEC-MOV-ROCKOVER-002, TEC-POS-TENSION-003, TEC-STR-SPEED-001, TEC-CON-LOAD-002, TEC-MOV-DROPKNEE-003, TEC-MOV-TWIST-004]
misconceptions:
  - 「用腿爬就是脚多使劲」——腿使劲只是第一节，传不过去等于没使
  - 「核心训练就是练腹肌」——链条要的是整段刚度和时序控制，孤立练腹肌迁移有限
  - 「发力顺序是天生的」——它是可以在具体线路上练的，属于技巧不是天赋
sources:
  - type: research
    ref: "Biomechanical Principles and Techniques—A Systematization for Sport Climbing"
    url: https://pmc.ncbi.nlm.nih.gov/articles/PMC13027491/
  - type: research
    ref: "Development of Specific Motor Skills through System Wall Bouldering Training"
    url: https://pmc.ncbi.nlm.nih.gov/articles/PMC11250695/
cases: ["CASE-2608-001", "CASE-2608-002"]
evidence_level: 研究证据
review:
  status: pending
  fact: null
  climb: null
  teaching: null
  version: 0.1.0
  updated: 2026-08-25
---

## 「蹬了但没上去」

这是动作链问题最典型的用户描述，也是它区别于力量问题的关键。

如果是**力量不足**，表现是蹬不动、腿抖、动作停在中途。
如果是**链条断了**，表现是腿明明伸直了、动作也做完了，但身体没有上升多少——
因为腿产生的位移被髋部下坠和躯干形变吃掉了。

产品在这里要小心：从单机位视频能观察到的是「膝盖伸直了但髋部高度没变」，
这是`可确认事实`；「你的核心不够强」是`专家假设`，不该自动输出。

## 顺序错了会互相抵消

高脚站起是最能说明时序的例子。

正确顺序：**重心先移到高脚正上方 → 腿蹬伸 → 手在末端维持平衡。**

常见错误顺序：**先用手往上拉 → 身体被拉向手的方向 → 重心偏离高脚 → 腿失去有效发力角度。**

两种顺序用的肌肉一样多，结果完全不同。这就是为什么「更用力」解决不了这个问题，
而「换个顺序」立刻见效——也是攀岩技巧值得单独建库的原因。

## 与「由腿部启动」的关系

[PRIN-LEGS-004](../principles/PRIN-LEGS-004.md) 说「主要位移由腿产生」，
这条原理补上了后半句：**并且必须传得到**。

两者合起来才是完整的指令：

> 用腿发力，同时保持躯干刚度，让力传得到手上。

只讲前半句，用户会得到一个做不出效果的建议。
