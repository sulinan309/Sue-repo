---
id: FAULT-SQUARE-REACH-008
type: fault
name: 正身硬够
aliases: [不会转髋, 一直正对墙, square on]
status: active
user_language:
  - 我爬起来手特别累
  - 陡墙上撑不了几下
  - 别人轻松够到的点我够不到
observables:
  - 骨盆朝向在整条线路中是否始终正对墙面
  - 髋部与墙面的距离
  - 够点时手臂是伸直还是屈曲
  - 承重脚用的是内侧还是外侧
candidate_explanations:
  - explanation: 动作模式默认正身，没有建立转髋的习惯
    evidence_required: 整条线路中骨盆朝向基本不变
    technique: TEC-POS-ORIENT-002
  - explanation: 转了上半身但骨盆没转，力臂没有缩短
    evidence_required: 能分别看清肩线和髋线的朝向
    technique: TEC-POS-ORIENT-002
  - explanation: 髋关节活动度不足，转不到位
    evidence_required: 视频难以区分「不会转」和「转不动」，需要结合用户自述
    technique: null
techniques: [TEC-POS-ORIENT-002, TEC-MOV-DROPKNEE-003]
physics: [PHY-TORQUE-003, PHY-ECONOMY-008]
hints:
  - 试试把够点那一侧的髋转向墙面，手会轻很多。
  - 转的是骨盆不是肩膀，脚也要换成外侧踩。
tasks: [TASK-SIDE-ON-009, TASK-STRAIGHT-ARM-010]
safety:
  - 转髋需要髋关节活动度，热身不足时容易拉伤内收肌或髋屈肌
  - 第三个候选解释涉及活动度限制，不应当鼓励用户强行转到疼痛位置
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

关键区分是「**不会转**」还是「**转不动**」——两者给的建议完全相反。

- 不会转 → 教学问题，提示和任务有效；
- 转不动 → 活动度限制，应当先做活动度练习，硬转会受伤。

**单机位视频很难可靠区分这两者。** 按证据等级，
这时候产品应当收缩到`证据不足`，问一句而不是猜：
「你是不知道要转，还是转不到那个位置？」

这是一个很好的例子：产品不需要什么都能看出来，**需要知道自己看不出什么。**
