# 固化输入（fixtures）

> 回归基线的唯一输入。测试只读这里，**不读视频**。

## 这里是什么

`annotator/out5/` 与 `annotator/out7/` 两次管线运行的产物，各取四类文件。

| 目录 | 对应素材 | 角色 | 帧数 | 来源 |
|---|---|---|---|---|
| `out5/` | `b4e0b99f.mp4` | **没站起来**（`CASE-2608-001`） | 258 / 8.6s | `annotator/out5` |
| `out7/` | `82a02e78.mp4` | **站起来了**（`CASE-2608-002`） | 95 / 3.2s | `annotator/out7` |

每个目录四个文件，合计 **534,853 字节**：

| 文件 | 内容 | out5 | out7 |
|---|---|---:|---:|
| `keypoints.npz` | 逐帧 33 点关键点、可见度、2D 质心代理、髋中点、fps | 105,358 | 40,940 |
| `evidence.jsonl` | 逐帧证据记录，每行一帧 | 270,595 | 98,415 |
| `holds.json` | 稳定岩点（参考帧坐标） | 853 | 1,860 |
| `summary.json` | 汇总 + 知识库能力对照 | 10,914 | 5,918 |

四个文件的 SHA-256 钉在 `qa/回归基线/fixtures.sha256.json`，由 `t01` 每轮核对。
输入变了而基线没变，等于基线在为一个不存在的输入背书——那正是
「out5 换成 out6」那次事故的形状，只不过换的是输入端。

## 为什么只存这四类

**决定：只固化派生数据，原始视频不进 git。**

原始视频是可识别的真人攀岩影像。一旦提交，就永久写进 git 历史，
`git rm` 删不掉（要 rewrite history，而分支是共享的）。
这条是人做的决定，不是权衡出来的默认值。

被排除的还有 `annotated.mp4`（out5 12MB / out7 4.4MB）——那是**产物不是输入**，
带覆盖层的渲染视频不能作为回归的输入源，重新渲染它也不构成对数字的验证。

原始视频当前在 `/root/.claude/uploads/8ef81b05-.../` 下，
那是**容器级目录，会随容器回收消失**。所以任何依赖它的基线都是一次性的。

## 不存视频，覆盖不到哪一层

这是这份 fixtures 最重要的一段。**下面这三层没有回归保护：**

### 1. 从像素到关键点：`pose.py`

`PoseTracker` / `backfill` / `smooth` 的输入是 BGR 帧。没有帧就跑不了，
也就无法验证 ROI 追踪、重捕获策略、检出率。
`keypoints.npz` 是这一层的**输出**，我们只能把它当成给定值。

后果：**如果 MediaPipe 版本变了、ROI 策略被改坏，本套测试一条都不会响。**
检出率从 100% 掉到 46.7% 也照样全绿——因为测试读的是旧的 npz。

### 2. 从像素到岩点与墙面：`holds.py`

`detect_stable()` 同时产出岩点列表和**逐帧单应 `Hs`（墙面坐标系）**。
`holds.json` 只存了岩点，`Hs` 没有被写进任何文件，只活在内存里。

后果比第 1 条更重：`drive.detect` / `detect_stalls` / `detect_rises`
在管线里都是**带着 `Hs` 跑的**，而测试只能在图像坐标下跑它们。
实测同一段停滞，墙面坐标净上升 **−0.03**，图像坐标 **−0.24**——
差 8 倍，而 −0.03 正是 `CASE-2608-001` 的头条数字。
这条记在 `qa/缺陷清单.md` 的 **D-006**：建议把 `wall_H` 写进 `keypoints.npz`。

### 3. 接触判定：`contact.py`

`analyse()` 的输入是姿态帧 + 岩点 + `Hs`。同样跑不了。
`evidence.jsonl` 是它的输出，测试只能把接触状态序列当成给定值。

### 还有：渲染层

`render.py` / `viz.py` / `compare.py` / `card.py` 的画面部分需要真帧。
测试覆盖的是它们**印在画面上的数字**（`anchor.py` 那一层），
不覆盖任何一个像素。「卡片好不好看」「有没有把脑袋裁掉」不在本套测试内。

## 能覆盖到哪一层

从 `keypoints.npz` + `evidence.jsonl` 往后的纯计算，全部可复现，且不需要视频：

- `anchor.py` 全部（T0 定位、承重踝归一、`dx` / `dy` / `rise`）——
  compare.py 与 card.py 上屏的每一个数字都出自这里
- `pose.reliability()` / `reliable_windows()` / `joint_reliability()`
- `drive._unreliable()` / 三个检测器的**图像坐标**行为与拒答逻辑
- `review.py` 全部（含基线对比与 z 检验）
- `make_case.collect()` / `anchor_measures()` —— 知识库 `measured` 的来源
- `climbing-kb/tools/subs.py` 的 `text_mask()` / `find_band()` / `extract()`
  （用合成图，本来就不需要真视频）

## 怎么重建

fixtures 不该被随手改。真要更新（例如管线改了、需要新的基准）：

```bash
# 1. 用当前管线重跑，得到新的 outN/
cd annotator && python3 annotate.py 视频.mp4 -o out8

# 2. 复制四类文件（不要复制 annotated.mp4）
for f in keypoints.npz evidence.jsonl holds.json summary.json; do
  cp "out8/$f" "../qa/fixtures/out8/$f"
done

# 3. 重建哈希与数值基线，并在提交信息里写清哪个数变了、为什么
./qa/用例/run.sh --bless
```

`--bless` 会覆盖 `qa/回归基线/` 下的全部快照。**它不是「让测试变绿」的按钮**：
基线变了必须由改动者说明**哪个数变了、为什么**，
「重构不改行为」这句话要用哈希证明，不能靠声明。

## 无视频加载器

`climbanno.anchor.load()` 会读视频。`qa/用例/qalib.py` 里的 `load_nv()`
是它摘掉读帧那一段的版本，算法（`medf` / T0 定位 / `idx` / `rise`）
直接 import 真模块，不重写。

2026-08-28 在视频还在的机器上做过逐位交叉验证（`t00_视频交叉验证.py`）：
out5 / out7 上 `t0`、`t_end`、`n`、`fps` 完全相同，
`dx` / `dy` / `torso` / `ax` / `ay` 五条序列的最大绝对差均为 **0.0**，
NaN 位置一致。视频消失之后 `t00` 会自动 SKIP——它是一次性取证，不是常驻门禁。
