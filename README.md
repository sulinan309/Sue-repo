# Sue-repo

## climbing-kb — 攀岩知识库

AI 攀岩搭子产品的领域知识底座，对应《AI 攀岩搭子｜MVP 产品文档》14.1 的**项目一**。

首期建设技巧库：57 个知识单元，覆盖 5 个底层动作原则、8 个物理原理、
10 个核心技巧、16 个常见卡点和 18 项现实任务。

见 [climbing-kb/README.md](climbing-kb/README.md)。

## annotator — 攀岩动作标注 demo

感知层 P0–P3 档的可运行实现：姿态骨架、岩点检测、接触判定、动作阶段，
输出带覆盖层的视频和逐帧证据记录。见 [annotator/README.md](annotator/README.md)。

```bash
cd climbing-kb
python3 tools/validate.py    # 校验结构完整性
python3 tools/query.py 脚滑   # 按用户的一句话检索
python3 climbing-kb/tools/perception_audit.py   # 感知能力需求审计
```
