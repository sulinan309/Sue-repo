---
id: FAULT-WRONG-HAND-015
type: fault
name: 手序错了
aliases: [上错手, 手不对, wrong hand sequence]
status: active
user_language:
  - 到那儿发现手反了
  - 该用右手的时候是左手在上面
  - 只好换手，一换就掉
observables:
  - 是否出现同一个岩点上的换手动作
  - 换手发生的位置是否在难点附近
  - 是否出现伸手后收回、改用另一只手
  - 换手过程中是否掉落
candidate_explanations:
  - explanation: 读线时没有从结束点倒推手序
    evidence_required: 上墙前有观察但无倒推迹象；错手发生在后段
    technique: TEC-PER-READ-001
  - explanation: 中途临时改变了动作顺序，与预演不一致
    evidence_required: 同一线路多次尝试的顺序不一致
    technique: TEC-PER-READ-001
  - explanation: 原计划的手序在实际中做不出来，被迫改变
    evidence_required: 需要结合用户自述；视频难以单独区分
    technique: null
techniques: [TEC-PER-READ-001]
physics: []
hints:
  - 从结束点倒着推回来，看最后那个点该用哪只手。
  - 上次你在这儿换了手，这次上墙前先确认前三步的手序。
tasks: [TASK-BACKWARD-READ-018]
safety:
  - 换手是不稳定窗口，在难点附近换手掉落风险较高，确认落区
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

手序错误是**读线质量最直接的可观察结果**，因为它留下了明确的证据：
一次换手动作。

这对产品特别有价值：换手动作在视频里容易识别，
而且能定位到具体是哪一步出的问题——
「你在第 4 步换了手」是`可确认事实`，可以直接进入下一次的读线任务。

第三个解释（计划本身不可行）提醒产品不要过度归因于读线：
有时候用户读得没错，是那条 Beta 对他的身体条件不成立。
这属于「多种 Beta」的范围，MVP 阶段不承诺解决。
