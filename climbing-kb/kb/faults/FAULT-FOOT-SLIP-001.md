---
id: FAULT-FOOT-SLIP-001
type: fault
name: 脚打滑
aliases: [脚滑, foot slip, 踩不住]
status: active
user_language:
  - 我脚老是滑
  - 踩上去就滑下来
  - 这个点根本站不住
observables:
  - 脚在岩点上发生可见的滑动位移
  - 滑动前脚的落点位置（是否在岩点边缘或圆弧下沿）
  - 滑动瞬间髋部相对墙面的位置
  - 是否伴随身体重心向墙面靠近
candidate_explanations:
  - explanation: 落点在岩点的无效受力面上（边缘、圆弧下沿）
    evidence_required: 视频中能看清鞋与岩点的接触位置
    technique: TEC-CON-FOOT-001
  - explanation: 法向力不足——板墙上身体贴墙导致重量转移到手上
    evidence_required: 能观察到髋部靠向墙面、上半身前倾
    technique: TEC-CON-LOAD-002
  - explanation: 加载方向与岩点可承受方向不一致
    evidence_required: 能看清岩点朝向与脚的施力方向
    technique: TEC-CON-LOAD-002
  - explanation: 鞋底或岩点表面状态问题（磨损、灰、汗、镁粉残留）
    evidence_required: 视频通常看不出，需要用户自述或现场确认
    technique: null
techniques: [TEC-CON-FOOT-001, TEC-CON-LOAD-002]
physics: [PHY-FRICTION-004]
hints:
  - 看看脚是不是踩在点的边上，试试往中间踩一点。
  - 板墙上别贴着墙，站直一点，把重量压到脚上。
  - 踩上去之后先把重量交给它，再动手。
tasks: [TASK-SILENT-FEET-001, TASK-WEIGHT-FOOT-003]
safety:
  - 连续踩空或打滑是疲劳的可靠信号，出现三次以上应当休息而不是继续尝试
  - 板墙脚滑通常是面朝下摔，注意保护手腕，不要用手撑地
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

按这个顺序排查，因为前面的更常见也更容易改：

1. **看落点**——踩在边缘还是有效面上？这是最常见的，也是视频最容易看清的。
2. **看髋部**——板墙上是不是贴着墙？贴墙会减少脚上的法向力，是反直觉但高频的原因。
3. **看方向**——岩点朝哪边开口，脚往哪边压？
4. **问装备**——前三项都排除了，才考虑鞋和岩点状态。视频看不出来，只能问。

**表达边界**：前三项可以从视频给出`可确认事实`（「你的脚踩在点的下缘」）。
第四项视频给不出，产品不应该猜，应当直接说「我看不准，也可能是鞋底的问题」。
