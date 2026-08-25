---
id: FAULT-REACH-FIRST-005
type: fault
name: 先伸手后移重心
aliases: [用手够, 拉过去, reach first]
status: active
user_language:
  - 我够不到
  - 差一点点就摸到了
  - 感觉手不够长
observables:
  - 伸手动作与髋部移动的先后顺序
  - 伸手时髋部是否仍停在原来的位置
  - 是否出现伸出去又收回来的试探
  - 身体是否被伸出的手拖动
candidate_explanations:
  - explanation: 动作模式是手主导——先伸手，重心没有先移过去
    evidence_required: 视频中髋部在伸手之前没有可见位移
    technique: TEC-POS-COM-001
  - explanation: 重心移过去会开门，所以不敢移，本质是稳定性问题
    evidence_required: 尝试移动时能观察到身体旋转趋势
    technique: TEC-MOV-FLAG-001
  - explanation: 身体朝向是正身，转成侧身能多出可观的触及距离
    evidence_required: 能看清骨盆朝向和目标点的相对位置
    technique: TEC-POS-ORIENT-002
  - explanation: 距离确实超出静态范围，需要死点或动态
    evidence_required: 重心已经到位、身体完全展开后仍有明显距离
    technique: TEC-STR-SPEED-001
techniques: [TEC-POS-COM-001, TEC-POS-ORIENT-002, TEC-STR-SPEED-001]
physics: [PHY-GRAVITY-COM-001, PHY-TORQUE-003]
hints:
  - 伸手之前，先把髋往那边送一点。
  - 试试转个髋侧过来，肩膀会送出去不少。
  - 重心已经到位了还差一截的话，这一步可能需要借一点势。
tasks: [TASK-HIP-FIRST-005, TASK-SIDE-ON-009]
safety:
  - 极限伸展状态下掉落时身体是展开的，缓冲能力差，练习时降低高度
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

「够不到」是用户语言里出现频率最高的一句，也是**最容易给错建议的一句**——
因为它听起来像身高问题，实际上大部分时候不是。

排查顺序很重要，前三项是可以改的，第四项才是真的需要换方法：

1. **髋有没有先动？** 没动 → 这是动作模式问题，收益最大。
2. **敢不敢移？** 不敢 → 是开门风险，先解决稳定。
3. **是不是正身？** 是 → 转髋能多出可观距离。
4. **以上都做了还差** → 这一步确实需要动态。

**只有走完前三步，才可以说「这一步需要动态」。**
直接建议用户跳，会让本来能静态解决的动作变成高风险动作。
