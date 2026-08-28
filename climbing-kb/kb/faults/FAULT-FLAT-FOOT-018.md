---
id: FAULT-FLAT-FOOT-018
type: fault
name: 脚横着踩
aliases: [脚踩平了, 顺着岩点形状踩, 脚尖朝外, flat foot placement]
status: active
user_language:
  - 我踩得挺稳的，但身体转不过去
  - 侧身的时候脚上使不上劲
  - 换脚之后感觉支撑不住
observables:
  - 鞋的长轴与墙面水平线的夹角（横着踩接近 0 度）
  - 踩点姿态是顺着岩点的形状，还是主动选了角度
  - 转体过程中脚踝是否被迫扭转或脚是否离位
  - 承重是落在拇趾一侧（内侧）、小趾一侧（外侧），还是整个脚掌摊平
candidate_explanations:
  - explanation: 顺着岩点的形状放脚，横向的岩点就带出横着的脚，脚踝失去可转动的余量，身体转不起来
    evidence_required: 能看清岩点长轴方向与鞋长轴方向大致平行
    technique: TEC-CON-FOOT-001
  - explanation: 脚掌摊平使受力分散到整个脚掌，蹬墙时缺少一个明确的着力边，对身体的支撑不足
    evidence_required: 能看清承重是否集中在鞋的内侧或外侧边缘
    technique: TEC-CON-FOOT-001
  - explanation: 脚的角度没问题，是这一步根本不需要转体，横踩是合理选择
    evidence_required: 该步的目标点在正上方而非斜上方
    technique: null
  - explanation: 脚点本身太小或太滑，只能整脚摊上去争取摩擦，与角度选择无关
    evidence_required: 能看清脚点尺寸与鞋接触面的关系
    technique: TEC-CON-FOOT-001
techniques: [TEC-CON-FOOT-001, TEC-POS-ORIENT-002]
hints:
  - 别顺着岩点的形状踩，脚尖斜着放，大概 45 度。
  - 用鞋的内侧或外侧边缘吃力，不要整个脚掌摊上去。
  - 放脚之前先想好等下要往哪边转，脚就朝那个方向留出余量。
tasks: [TASK-SIDE-ON-009, TASK-FOOT-EYES-002]
safety:
  - 斜向踩点时踝关节处于非中立位，热身不足或疲劳时容易崴脚
  - 45 度只是常用起点，不要为凑角度把脚放到岩点的无效受力面上
evidence_level: 专家共识
review:
  status: pending
  fact: null
  climb: null
  teaching: null
  version: 0.1.0
  updated: 2026-08-28
---

## 岩点的形状会骗你

很多脚点是横向的长条形。顺着这个形状放脚是最自然的反应——
接触面积最大，踩上去也确实最「稳」。

但横着踩的脚**没有给转体留余量**。侧身要求骨盆转动，
骨盆转动会经小腿传到脚踝；脚已经横在那里，脚踝没有可动的角度，
于是要么身体转不过去，要么脚被扭下来。

所以这一条和 [TEC-CON-FOOT-001](../techniques/TEC-CON-FOOT-001.md) 是配套的：
精准踩点解决「踩哪里」，这一条解决「以什么角度踩」。

## 做法

**不管脚点是什么形状，尽量让脚在大约 45 度的状态下去踩。**

45 度是一个便于记忆的起点，不是精确阈值——
它的作用是让鞋有一条明确的着力边（内侧或外侧），
同时给脚踝留出向两侧转动的余量。

判断标准不是角度本身，而是：**放上去之后，身体还能不能转。**

## 一个提醒

这条规则服务于转体。板墙上正身站立、需要把重量整个压在脚上时，
摊平反而是对的（见 [PHY-FRICTION-004](../physics/PHY-FRICTION-004.md)）。
**这是陡墙上的踩法，不是通用踩法**——和侧身本身一样。
