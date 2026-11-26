# 相关工作：有没有人做过（2026-11-26 查）

## 1. 和我们撞车最多的：MemBubble（测量）

**[MemBubble: Benchmarking How Agent Memory Shapes LLM Response Diversity](https://arxiv.org/abs/2610.25127)**。中科院计算所 AI 安全全国重点实验室、百度，2026-10-18 提交到 arXiv。目前没有找到代码和数据。

- **测什么**：带了记忆以后，大模型的回答还剩多少种。同一个问题回答 10 次，由评委（DeepSeek-V4-Flash）把“意思等价”的回答归成一堆，再算有几堆、熵是多少。另外还算了一个“偏好命中率”：回答里出现用户偏好名词的比例。
- **数据**：用的是真实对话（LMSYS-Chat-1M、WildChat），共 1000 个实例，35 种语言。问题都是开放式的“推荐一个某类的东西”，平均 11.8 个词。
- **对比**：5 种记忆系统（NaiveRAG、MemoryBank、A-Mem、**mem0**、MemoryOS）× 6 个大模型，另有“不带记忆”和“整段历史都放进上下文”两个对照组。
- **结论**：
  - 带记忆以后，回答种类平均少了 25.0%，熵降了 34.1%。**mem0 最严重**：种类少 33.9%，熵降 46.7%。
  - 整段历史都放进去反而没事（+1.8%），问题出在记忆系统“抽取 + 检索”的方式上。
  - 有 34% 的样本，10 次回答全是同一个答案；不带记忆时这个比例只有 6%。
- **补救**：试了改写问题、系统提示要求多样、调温度、调检索条数，**都缩小不了差距**。论文没有提出新的解决方法。
- **没测的**：回答**合不合适、可不可行**（只测了多样性）；为什么会被带跑（没有标准答案，所以分不出喜好、技能、出现次数、过时信息各自的影响）。

**对我们的影响：**

- “带记忆会让回答变窄”这件事，已经有人发表了，我们的 benchmark 不再是第一个。但两边结论一致：我们测出 mem0 打圈率从 8% 涨到 54%，叮嘱一句、调高温度都拉不回来。
- 我们 benchmark 的独特之处：
  1. **合适率 / 好点子率**：防止“完全无视用户”反而得高分；
  2. **有标准答案的人设**：能分开喜好、技能、资源、限制、陷阱、过时信息、出现次数各自的影响；
  3. 测的是**出点子**，而不是“推荐一个东西”。
- **项目的重心应该放在“解决办法”**，也就是 Widen 插件。MemBubble 证明了问题存在，但没有给出解法。以后如果它公开了数据，可以直接拿来测 Widen。

## 2. 大模型当排序器：LLMRank（支持我们“精排用大模型”）

**[Large Language Models are Zero-Shot Rankers for Recommender Systems](https://arxiv.org/abs/2305.08845)**（ECIR 2024），代码：[RUCAIBox/LLMRank](https://github.com/RUCAIBox/LLMRank)（MIT 协议）。

- 结论：对于多路召回得到的候选，大模型不经训练直接排序，效果和传统推荐模型相当，甚至更好。
- 已知问题：会被**热度**和候选在提示词里的**位置**带偏。→ 我们精排时要**打乱候选顺序**，并且不把热度写进提示词。

## 3. 多阶段推荐系统的开源实现

- 搜到一个个人作品：[2u39u4/multi-stage-recommender](https://github.com/2u39u4/multi-stage-recommender)。多路召回 + DeepFM / DIN 排序 + MMR 重排，用的是 MovieLens 数据。
- 有名的开源推荐框架，比如 NVIDIA Merlin、Microsoft Recommenders、RecBole、Gorse、Twitter（X）开源的推荐算法，这次搜索**没有核实**，是凭印象列的。它们都是“物品推荐”框架，没有一个是给大模型的记忆用的。

## 4. 记忆层里做“探索”的开源项目

**没有找到。** 智能体记忆的几个合集（[awesome-agent-memory](https://github.com/tfatykhov/awesome-agent-memory)、[Awesome-Agent-Memory](https://github.com/TeleAI-UAGI/Awesome-Agent-Memory)）里，有用“新颖度”来决定一条信息要不要写进记忆的，比如 SAGE；也有在 GUI 智能体里把记忆和探索一起训练的，比如 [JAMEL](https://arxiv.org/abs/2606.01528)。但没有一个是在**检索记忆时，像推荐系统那样主动探索新方向**的。

**结论：** 问题已经被测量过了（MemBubble），解法还是空白。Widen 插件就是在补这个空白。
