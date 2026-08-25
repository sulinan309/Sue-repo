---
id: FAULT-DYNO-CATCH-009
type: fault
name: 动态抓到了但没抓住
aliases: [抓到了还是掉, 弹开, dyno catch fail]
status: active
user_language:
  - 我明明摸到了那个点
  - 手碰到了但被拽下来
  - 抓住了又滑掉
observables:
  - 手接触目标点时身体是在上升、静止还是已经下落
  - 接触后手停留的时间（瞬间弹开 vs 停住片刻后脱落）
  - 接触后身体是否明显摆荡
  - 脚在腾空阶段的位置
candidate_explanations:
  - explanation: 时机偏晚——身体已在下落，手指要在极短时间内吃掉全部冲量
    evidence_required: 视频中能看出接触瞬间身体在向下运动
    technique: TEC-STR-SPEED-001
  - explanation: 时机偏早——身体还在上升，手要提供额外向下的力才能拉住自己
    evidence_required: 接触瞬间身体仍在向上运动
    technique: TEC-STR-SPEED-001
  - explanation: 水平方向残余动量没有被抵消，抓住后身体荡出去
    evidence_required: 接触后有明显侧向摆荡
    technique: TEC-POS-TENSION-003
  - explanation: 抓住之后张力没有立刻恢复，脚回不到墙上
    evidence_required: 能观察到抓住后脚长时间悬空
    technique: TEC-POS-TENSION-003
  - explanation: 目标点确实抓不住（握姿不对或握力不足），与时机无关
    evidence_required: 在静态可达的情况下单独测试该点是否能握住
    technique: null
techniques: [TEC-STR-SPEED-001, TEC-POS-TENSION-003]
physics: [PHY-MOMENTUM-007]
hints:
  - 试试早半拍启动，在身体最高的那一下抓。
  - 抓住之后马上收紧，把脚带回墙上。
  - 先在低一点的地方试试这个点单独抓得住吗。
tasks: [TASK-DEADPOINT-015]
safety:
  - 动态失败经常是背向或侧向落地，起跳前必须确认落区无人
  - 手指在接触瞬间承受的冲击远高于静态，指部有旧伤时不做大幅动态
  - 疲劳时动态失败率上升，连续三次未成功应当收工
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

这是**「同一个现象，五种机制」的典型案例**，也是知识库要求「不强行给出唯一原因」的最好例证。

从视频区分的关键是**接触之后发生了什么**：

| 现象 | 指向 |
| --- | --- |
| 碰到就弹开 | 时机问题（多为偏晚） |
| 抓住停一下才掉 | 握姿/握力，或张力没恢复 |
| 抓住但身体荡走 | 水平动量未抵消 |

三种给的提示完全不同：第一种改时机，第二种改握姿或降低目标，第三种改张力恢复。
把它们混成一句「多练握力」，用户练很久也不会好。
