---
id: FAULT-SWAP-DROP-021
type: fault
name: 换脚就掉 / 换完站不住
aliases: [换脚失败, 倒脚掉了, 换脚站不住, foot swap failure, 换脚要跳一下]
status: active

user_language:
  - 换脚的时候整个人就掉了
  - 换脚之后感觉支撑不住
  - 脚是换过去了，但站不起来
  - 我换脚一定要跳一下，一跳就没了
  - 换脚的时候手上特别累

observables:
  - 旧脚离开岩点到新脚建立接触之间的间隔时长
  - 交接期间是否出现双脚同时离点的帧
  - 旧脚离开之前，重心的水平位移有没有先开始
  - 失稳发生在哪一段：卸载前、交接中，还是新脚落位之后
  - 新脚落位之后 0.5 秒内是否发生二次调整

candidate_explanations:
  - explanation: 交接之前重心还留在旧脚一侧。旧脚一走，支撑范围的下边界从两脚连线塌成一个点，重力立刻产生一个绕留守脚的力矩，人被转开
    evidence_required: 旧脚离开之前重心的水平位移尚未开始；离开后 0.5 秒内出现摆动或旋转
    technique: TEC-CON-SWAP-003
  - explanation: 交接期间出现了双脚同时离点的窗口，那一瞬间体重全部转到手上，手接不住
    evidence_required: 视频中存在两只脚同时判为非接触的帧；该窗口与失稳时刻重合
    technique: TEC-CON-SWAP-003
  - explanation: 新脚落点不准，落上去还要挪，交接窗口被拉长，手上的负荷时间跟着变长
    evidence_required: 新脚落位后 0.5 秒内发生位置调整；调整期间体重仍在手上
    technique: TEC-CON-FOOT-001
  - explanation: 新脚落位了但没有加载，重量始终没有交出去——交接其实没有完成
    evidence_required: 新脚接触后髋部没有向该脚方向移动；伸手瞬间该脚脱落
    technique: TEC-CON-LOAD-002
  - explanation: 这一步根本不该换脚。脚点站不下第二只脚，或这一步只需要短暂改变朝向，用旗式成本更低
    evidence_required: 能看清脚点尺寸与鞋的关系；该步的停留时间很短
    technique: TEC-MOV-FLAG-001
  - explanation: 换过去的脚踩的角度不对，站住了但转不动，被误当成「支撑不住」
    evidence_required: 鞋长轴与墙面水平线接近平行；转体过程中脚被迫扭转或离位
    technique: TEC-CON-FOOT-001

techniques: [TEC-CON-SWAP-003, TEC-CON-FOOT-001, TEC-CON-LOAD-002, TEC-MOV-FLAG-001]
physics: [PHY-EQUILIBRIUM-002, PHY-TORQUE-003]
hints:
  - 换脚之前先把重量挪到另一边，挪到旧脚能轻轻抬起来为止。
  - 别急着抬脚，先看好新脚落在哪。
  - 新脚落上去就压实，压实了才算换完。
tasks: [TASK-FOOT-TAP-021, TASK-WEIGHT-FOOT-003]
safety:
  - 换脚是刻意制造的不稳定窗口，掉落概率高于普通移动；先确认落区无人，再决定在这一步换脚
  - 反复失败的小跳换脚会累计踝关节冲击，连续两次没换成应当下墙调整解法，而不是继续硬试
  - 在难点上方或高处不要临时起意换脚——那里失手的代价和落地姿势都更差

evidence_level: 专家共识
review:
  status: pending
  fact: null
  climb: null
  teaching: null
  version: 0.1.0
  updated: 2026-08-29
---

## 先分清「掉在哪一段」

换脚有四段，掉在不同段，原因完全不同：

```
卸载旧脚 → 旧脚离开 → 新脚落位 → 加载新脚
   ①          ②           ③          ④
```

| 掉在哪 | 通常是什么问题 | 去哪张卡 |
| --- | --- | --- |
| ① 还没抬脚就晃 | 重心根本没挪，或这个姿势本来就不稳 | [TEC-POS-COM-001](../techniques/TEC-POS-COM-001.md) |
| ② 抬脚瞬间被转开 | 重心还在旧脚一侧，力矩没抵消 | [TEC-CON-SWAP-003](../techniques/TEC-CON-SWAP-003.md) |
| ③ 落位落不准、要挪 | 落点没看好，是踩点问题 | [TEC-CON-FOOT-001](../techniques/TEC-CON-FOOT-001.md) |
| ④ 踩上了但站不起来 | 没加载，重量还挂在手上 | [TEC-CON-LOAD-002](../techniques/TEC-CON-LOAD-002.md) |

**产品应当先问「掉在哪一段」，而不是先给建议。**
视频能区分 ②③④（时序和落点都看得见），① 需要看更早的一段。

## 一个反直觉的候选解释

第五条候选解释是「这一步不该换脚」。

新手把换脚当成一个必须练会的动作，于是在**不需要换脚的地方**换脚：
只是想改一下朝向、停留不到一秒，却花了一次交接的成本。
这种情况下正确的反馈不是「你换脚换得不好」，是
[TEC-MOV-FLAG-001](../techniques/TEC-MOV-FLAG-001.md)——
换一个成本更低的解法。

第六条同样容易误判：**站住了但转不动**，用户说出来也是「支撑不住」，
实际上是踩的角度问题（[FAULT-FLAT-FOOT-018](FAULT-FLAT-FOOT-018.md)），
和交接一点关系都没有。

## 这张卡目前的证据边界

- 六个候选解释来自库内已有的物理与技巧单元的组合推演 + 教学材料的一致说法，
  **没有一条有直接研究支撑**，也没有真人攀岩专家复核过。
- 我们自己的素材里**没有一次同点换脚**（见
  [CASE-2608-003](../cases/CASE-2608-003.md)），
  所以候选解释里关于「脚点站不站得下两只脚」的部分，
  目前既没有外部研究也没有内部数据。
- 「掉在哪一段」这个分段判据是可从视频观察的，但**分段本身还没有在真实失败案例上验证过**。
  第一个换脚失败案例进来之前，它是一个待验证的假设，不是结论。
