---
id: FAULT-PULL-FIRST-011
type: fault
name: 用手拉代替用腿蹬
aliases: [全靠手, 引体上墙, 手主导]
status: active
user_language:
  - 我爬两条线前臂就废了
  - 感觉全程都在做引体向上
  - 腿完全不累但手废了
observables:
  - 向上位移时手臂是否长期处于屈曲状态
  - 膝关节在位移过程中是否有蹬伸
  - 位移启动时先动的是手还是脚/髋
  - 前臂疲劳表现出现的时间点（甩手、频繁换握）
candidate_explanations:
  - explanation: 默认动作模式是手主导，没有建立腿部启动的习惯
    evidence_required: 多次位移中均为手先动、膝无蹬伸
    technique: TEC-MOV-ROCKOVER-002
  - explanation: 知道要用腿，但躯干刚度不足，腿的力传不到手上，只好用手补
    evidence_required: 能观察到蹬伸的同时髋部下坠
    technique: TEC-POS-TENSION-003
  - explanation: 脚点没有被有效加载，腿实际上使不上力
    evidence_required: 能观察到脚在点上但无承重迹象
    technique: TEC-CON-LOAD-002
techniques: [TEC-MOV-ROCKOVER-002, TEC-POS-TENSION-003, TEC-CON-LOAD-002]
physics: [PHY-KCHAIN-006, PHY-ECONOMY-008]
hints:
  - 这一步试试先蹬腿，手只负责扶住方向。
  - 蹬的时候把肚子收紧，不然腿的力传不上来。
  - 先确认那只脚真的踩住了，再考虑往上。
tasks: [TASK-NO-HAND-STEP-012, TASK-WEIGHT-FOOT-003]
safety:
  - 长期手主导会显著增加手指和肘部负荷，出现肘部内外侧疼痛应当减量
  - 前臂过早力竭会降低对掉落的控制能力，泵感明显时应当结束该线路
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

「用腿爬，别用手拉」是岩馆里最常听到的建议，也是**最常被解释得不完整的一条**。

三个解释对应三种完全不同的处理：

1. **不知道要用腿** → 教学问题，任务和提示有效；
2. **用了但传不上来** → 张力问题，光说「用腿」没用；
3. **脚根本没踩住** → 加载问题，前两条都白搭。

产品只说「多用腿」，对第二、三种用户是无效建议。
必须先看髋部有没有下坠、脚上有没有承重，再决定给哪一句。
