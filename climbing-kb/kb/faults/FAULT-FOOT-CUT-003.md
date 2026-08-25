---
id: FAULT-FOOT-CUT-003
type: fault
name: 一伸手脚就掉
aliases: [脚掉了, foot cut, 甩脚, 脚脱落]
status: active
user_language:
  - 我脚明明踩住了，一伸手脚就掉
  - 陡墙上脚老是掉出来
  - 手一动腿就飞了
observables:
  - 脚脱落与伸手动作之间的时间关系（是否同步发生）
  - 脱落瞬间髋部是否下坠或远离墙面
  - 脱落是滑出（沿墙面）还是掉出（离开墙面）
  - 脱落前脚上是否有可见的加载
candidate_explanations:
  - explanation: 伸手瞬间躯干刚度下降，脚到手的传递路径断裂，脚上法向力归零
    evidence_required: 能观察到伸手同时髋部下坠或离墙
    technique: TEC-POS-TENSION-003
  - explanation: 张力建立的时机太晚——伸到一半才想起来收紧
    evidence_required: 能看出收紧动作发生在伸手之后
    technique: TEC-POS-TENSION-003
  - explanation: 脚点朝向本身不支持这个方向的对抗，换脚点或换身体朝向才有解
    evidence_required: 能看清脚点形状与身体朝向的关系
    technique: TEC-POS-ORIENT-002
  - explanation: 身体位置需要折膝或旗式配平，单纯加张力解决不了
    evidence_required: 能观察到脱落同时伴随身体旋转
    technique: TEC-MOV-FLAG-001
techniques: [TEC-POS-TENSION-003, TEC-CON-LOAD-002, TEC-POS-ORIENT-002]
physics: [PHY-OPPOSITION-005, PHY-KCHAIN-006]
hints:
  - 伸手之前先收紧肚子，把髋拉向墙面。
  - 移动的时候脚上的力别松掉。
  - 试试先转个髋，让脚的方向能撑住。
tasks: [TASK-NO-CUT-004, TASK-TENSION-HOLD-014]
safety:
  - 陡墙上脚脱落会产生摆荡，身体可能甩向侧方，落区判断要预留侧向空间
  - 反复的脚脱落会加大手指负荷，指部出现酸胀感应当停止该线路
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

**这是最容易被误判成「核心太弱」的卡点。** 产品尤其要克制。

从视频能得到的`可确认事实`是：「伸手的瞬间髋部下坠、脚脱落」。
「你核心力量不足」是`专家假设`，按《知识库框架》9.2 **不进入产品自动输出**。

四个候选解释里，前两个是张力问题（能力 vs. 时机），后两个是身体位置问题。
区分方法：

- 脱落时身体**平着掉下去** → 张力问题；
- 脱落时身体**转开了** → 位置问题，需要旗式或换朝向。

这两类给的提示完全不同，混在一起会让用户练错方向。
