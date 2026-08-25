---
id: FAULT-LIMP-FLAG-007
type: fault
name: 旗式无效
aliases: [旗了但没用, 腿是松的, limp flag]
status: active
user_language:
  - 我旗了腿但还是被转开
  - 旗式对我好像没用
observables:
  - 旗腿是否越过身体中线
  - 旗腿是绷直的还是松垂的
  - 旗腿的方向与身体转开的方向是否相反
  - 旗腿是否有蹬在墙面或岩点上
candidate_explanations:
  - explanation: 旗腿方向送反了，反而增大了重力的力臂
    evidence_required: 能看清身体旋转方向与旗腿方向
    technique: TEC-MOV-FLAG-001
  - explanation: 旗腿没有过中线，质量分布没有实质改变
    evidence_required: 能看清旗腿相对躯干中线的位置
    technique: TEC-MOV-FLAG-001
  - explanation: 旗腿松垮，只贡献质量不贡献蹬墙的反向力矩
    evidence_required: 能观察到旗腿是否绷紧、是否接触墙面
    technique: TEC-MOV-FLAG-001
  - explanation: 这一步的开门力矩过大，旗式不足以抵消，需要换脚或换解法
    evidence_required: 旗式做对之后仍有明显旋转
    technique: null
techniques: [TEC-MOV-FLAG-001]
physics: [PHY-TORQUE-003]
hints:
  - 你被转开的方向，就是那条腿要去的方向。
  - 腿要送过身体中线才有用，半步没效果。
  - 旗腿别松着，让它蹬住墙。
tasks: [TASK-FLAG-SWITCH-007]
safety:
  - 旗腿蹬墙时确认蹬点不是松动岩点或体积块边缘
  - 开门失控时身体绕轴甩出，落区按侧向甩出预估
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

三个执行错误按发生频率排序：**方向反 > 没过中线 > 腿是松的**。

前两个从视频很容易看清，属于`可确认事实`，可以直接给提示。

第四个解释（力矩过大、旗式不够）只有在**前三项都做对之后**才能成立。
产品不应该在用户明显做错方向时就说「这一步旗式不管用」——
那会让用户放弃一个本来有效的工具。
