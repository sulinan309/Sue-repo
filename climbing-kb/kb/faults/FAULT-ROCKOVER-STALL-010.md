---
id: FAULT-ROCKOVER-STALL-010
type: fault
name: 高脚站不起来
aliases: [压不上去, 高脚卡住, rockover stall]
status: active
user_language:
  - 脚踩上去了但站不起来
  - 高脚就是压不上去
  - 感觉腿没劲
observables:
  - 髋部是否移动到高脚的上方（横向位移）
  - 膝关节是否有蹬伸动作
  - 站起的启动是从腿开始还是从手开始
  - 另一条腿在做什么
candidate_explanations:
  - explanation: 重心没有移到高脚正上方，蹬伸方向主要把身体推离墙面
    evidence_required: 髋部在蹬伸前没有向高脚一侧的横向位移
    technique: TEC-MOV-ROCKOVER-002
  - explanation: 发力顺序反了——先用手拉，身体被拉向手，重心偏离高脚
    evidence_required: 能看出手的拉动早于腿的蹬伸
    technique: TEC-MOV-ROCKOVER-002
  - explanation: 没有转髋，膝盖缺少伸展空间
    evidence_required: 骨盆保持正对墙面且膝盖被躯干挡住
    technique: TEC-POS-ORIENT-002
  - explanation: 另一条腿没有配平，一发力身体就转开
    evidence_required: 蹬伸时能观察到身体旋转
    technique: TEC-MOV-FLAG-001
  - explanation: 髋关节活动度不足以完成该高度，属于身体条件限制不是技巧问题
    evidence_required: 需要结合用户自述；视频难以单独区分
    technique: null
techniques: [TEC-MOV-ROCKOVER-002, TEC-POS-ORIENT-002, TEC-MOV-FLAG-001]
physics: [PHY-GRAVITY-COM-001, PHY-KCHAIN-006]
hints:
  - 脚已经在上面了，现在把髋送到那只脚的正上方。
  - 别先用手拉，先把重量换到高脚上再蹬。
  - 试试转一下髋，膝盖会更容易伸开。
tasks: [TASK-ROCKOVER-011, TASK-NO-HAND-STEP-012]
safety:
  - 深度屈膝下蹬伸对膝关节负荷高，热身不足或有膝部旧伤时降低高脚高度
  - 高脚需要较大髋外展外旋活动度，不要靠硬掰去够
  - 站起失败时重心已经很高，掉落距离比一般动作大
evidence_level: 专家共识
review:
  status: pending
  fact: null
  climb: null
  teaching: null
  version: 0.1.0
  updated: 2026-08-25
---

## 怎么区分

**第一个解释能覆盖大部分情况**，所以排查从它开始：
看髋部在蹬伸之前有没有横向移动过去。没有 → 提示指向重心，收益最大。

「感觉腿没劲」是用户最常见的自我归因，但它几乎总是错的——
按 [PHY-GRAVITY-COM-001](../physics/PHY-GRAVITY-COM-001.md)，
重心在高脚侧后方时，腿蹬出去的力主要方向是把身体推离墙面，
不是腿没劲，是**力的方向不对**。

第五个解释（活动度限制）触发时不应当给技巧提示，
而应当建议找中间脚点分两步完成。
