---
id: PHY-ECONOMY-008
type: physics
name: 功、功率与动作经济性
aliases: [work, power, economy, 动作经济性, 省力]
status: active
one_liner: 同一条线路可以用差别很大的能量代价爬完，省下来的部分决定你还能不能爬第二条。
strict_definition: >
  功 W = ∫F·ds，只有沿位移方向的力分量做功。
  功率 P = dW/dt 是做功速率。
  值得注意的是：维持一个静止姿势时，外力做功为零，
  但肌肉的等长收缩仍在持续消耗代谢能量——生理代价与力学功不等同。
plain_explanation: >
  提着一桶水站着不动，物理上你没对水做功，但你的手会酸。
  攀岩里挂在墙上「想一想」也是这样：动作没进展，体力照样在烧。
  所以省力不只是「动作做得漂亮」，是直接决定你今天能试几次。
model_assumptions:
  - 力学功与代谢能耗不等价，等长收缩是主要差异来源
  - 忽略肌肉效率随疲劳的变化
  - 忽略呼吸、循环系统的基础消耗
key_variables:
  - 重心竖直位移：决定必须做的最小重力功
  - 维持时间：等长收缩的代谢代价随时间累积
  - 多余动作：重心的水平往复、试探性伸手都是额外消耗
climbing_manifestation:
  - 直臂悬挂比屈臂悬挂省，因为屈臂需要肱二头肌持续等长收缩
  - 长时间停在墙上犹豫，体力消耗和实际爬升不成比例
  - 重心路径越接近直线，重力功越接近理论最小值
  - 反复调整脚、试探性伸手都在消耗前臂
techniques: [TEC-PER-READ-001, TEC-STR-SPEED-001, TEC-POS-ORIENT-002]
misconceptions:
  - 「站着不动不费力」——等长收缩的代谢消耗很实在，尤其是前臂
  - 「爬得慢比较安全」——慢意味着维持时间长，对前臂是更大的负担
  - 「省力就是少用力」——省力是把力用在必要的方向和时间上，不是全程放松
sources:
  - type: research
    ref: "Sport climbing performance determinants and functional testing methods"
    url: https://pubmed.ncbi.nlm.nih.gov/39216626/
  - type: research
    ref: "Efficacy of pre-ascent climbing route visual inspection in indoor sport climbing"
    url: https://pubmed.ncbi.nlm.nih.gov/20561271/
evidence_level: 研究证据
review:
  status: pending
  fact: null
  climb: null
  teaching: null
  version: 0.1.0
  updated: 2026-08-25
---

## 力学功和体力消耗不是一回事

这条区分对攀岩特别重要，因为攀岩里有大量**等长收缩**（肌肉发力但长度不变）。

挂在墙上不动，物理上对身体不做功，但屈指肌持续收缩，血流受阻，
代谢产物堆积——这正是「泵」的来源。

所以攀岩的经济性有两个独立维度：

| 维度 | 减少方法 |
| --- | --- |
| **必要的重力功** | 重心路径尽量接近直线，减少无谓的上下和左右往复 |
| **等长收缩的时间积累** | 减少停顿、减少犹豫、减少反复试探 |

新手往往只优化第一个（「别乱动」），却在第二个上大量失分（挂在墙上想很久）。

## 「读线省下的是前臂」

这是把 [TEC-PER-READ-001](../techniques/TEC-PER-READ-001.md)（读线）
放进技巧库主体、而不是当附属内容的理由。

路线预看研究显示，上墙前的视觉检查会影响攀爬过程中的停顿与流畅度。
换成这里的语言：**读线减少的是墙上的等长收缩时间。**

对一条 V3 来说，在墙上多想 20 秒的代价，可能比一个不够标准的动作大得多。

## 用在产品里

「动作经济性」很难从单机位视频直接量化，但有两个**可观察的代理指标**：

- **停顿时长**：在同一姿势维持超过一定时间的次数和总时长；
- **无效试探**：伸手够出去又收回来的次数。

这两个都是`可确认事实`，可以进入产品反馈。
而「你这次比上次省力 15%」不是——它需要代谢测量，视频给不出来。
