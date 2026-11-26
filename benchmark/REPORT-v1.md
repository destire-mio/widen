# Benchmark 结果：带记忆的 AI 是不是只在记忆里打圈

5 个用户 × 10 个问题 × 4 组 × 3 次，每次 5 个点子，共 2995 个点子。回答、评委都是 DeepSeek，存在同源偏差（见 SPEC.md 第 6 节）。

## 总表

| 组 | 打圈率 | 被喜好带跑 | 踩陷阱 | 被过时信息带跑 | 合适率 | 好点子率（合适且跳出记忆） | 点子种类数（满分 15） |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A_none | 8% | 0% | 0% | 1% | 48% | 43% | 9.0 |
| B_memory | 54% | 10% | 3% | 4% | 73% | 34% | 8.2 |
| C_memory_nudge | 35% | 6% | 3% | 2% | 67% | 44% | 9.0 |
| D_memory_hot | 50% | 8% | 3% | 4% | 64% | 31% | 8.4 |

## 每个用户的打圈率

| 用户 | A_none | B_memory | C_memory_nudge | D_memory_hot |
| --- | --- | --- | --- | --- |
| 陈同学 | 9% | 68% | 49% | 56% |
| 小林 | 9% | 33% | 14% | 31% |
| 老马 | 6% | 61% | 30% | 53% |
| 阿叶 | 11% | 63% | 39% | 60% |
| 周老师 | 4% | 44% | 42% | 52% |

## 被哪一类信息带跑（占全部点子的比例）

| 组 | 只是喜好 | 会的技能 | 手上的资源 | 讨厌的 | 限制条件 | 背景 | 对不上人设的记忆 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A_none | 0% | 2% | 0% | 1% | 0% | 1% | 3% |
| B_memory | 10% | 8% | 8% | 2% | 5% | 4% | 17% |
| C_memory_nudge | 6% | 4% | 6% | 1% | 3% | 3% | 10% |
| D_memory_hot | 8% | 8% | 7% | 1% | 4% | 5% | 18% |

## 出现次数的影响（B 组）

每条信息平均带出多少个点子，按“聊天里实际出现几次”分组。

| 种类 | 出现 1 次 | 出现 2 次 | 出现 4 次以上 |
| --- | --- | --- | --- |
| 只是喜好 | 1.3（10 条） | 2.5（11 条） | 8.0（4 条） |
| 会的技能 | 0.6（10 条） | 4.5（6 条） | 6.8（4 条） |
| 手上的资源 | 0.5（10 条） | 4.4（12 条） | 0.7（3 条） |
| 讨厌的 | 0.6（5 条） | 1.6（5 条） | 0.8（5 条） |
| 限制条件 | 1.4（5 条） | 2.9（10 条） | 0.6（5 条） |
| 背景 | 2.0（11 条） | 1.2（9 条） | - |

## 判定（标准事先写在 SPEC.md 第 1 节）

- 带记忆比不带记忆，打圈率平均高 46%；5/5 个用户高出 20 个百分点以上。→ **打圈成立**
- C_memory_nudge：把多出来的打圈率降回去 41%。→ **补救无效**
- D_memory_hot：把多出来的打圈率降回去 7%。→ **补救无效**

## 例子：第 1 个问题，不带记忆 vs 带记忆

**陈同学：周末想做个小项目，有什么点子？**
- A_none：
    - 做一个个人书影音记录网页，支持打分和写短评。
    - 用 Python 写一个自动整理下载文件夹、按类型归档的小脚本。
    - 做一个每日天气与穿衣建议的桌面小组件。
    - 搭一个简易的番茄钟 + 待办清单网页应用。（来自记忆「User plans to make a to-do list to manage their graduation and PhD application tasks, and was advised not to overfill the list and to leave buffer time」）
    - 写一个把长文章自动生成摘要和关键词的小工具。
- B_memory：
    - 用 Python 写一个小工具，自动整理并重命名下载文件夹里的文件。
    - 做一个简单的个人记账网页，记录每天的开销并生成月度图表。
    - 用手机拍一组主题照片（比如“我的一天”），再用免费工具剪成 1 分钟小视频。
    - 学做一道从没做过的菜，比如红烧类的，把过程和成品拍下来发朋友圈。（来自记忆「User was advised to start cooking with quick beginner dishes like 番茄炒蛋 and 青椒土豆丝, then move on to braised (红烧) dishes once more skilled」）
    - 读一篇自己专业相关的中文文献，用几句话总结成一张思维导图或卡片。

**小林：周末想做个小项目，有什么点子？**
- A_none：
    - 用 Python 写一个命令行工具，自动整理下载文件夹并按文件类型分类。（来自记忆「User was advised to learn Rust by building a small project rather than reading a book, and was recommended beginner projects like a command-line tool that counts text words or batch-renames files」）
    - 做一个极简的个人书签管理网页，支持标签筛选和搜索。（来自记忆「User wrote a small tool and recently wanted to add a web interface to it, but got stuck on styling for a long time — a button wouldn't align no matter how they adjusted it」）
    - 用树莓派或旧手机搭建一个家庭天气与室内温湿度显示屏。
    - 写一个浏览器扩展，每天随机展示一张你收藏的摄影作品作为新标签页。
    - 做一个番茄钟小应用，记录每日专注时长并生成简单的周报图表。
- B_memory：
    - 用手机拍下家里旧物，整理成一份带照片的断舍离清单
    - 给阳台或窗台做一个迷你香草小花园，种薄荷、罗勒和葱
    - 把一周的菜谱和采购清单做成一张冰箱贴表格
    - 整理手机相册，挑出 20 张做成一本小照片书
    - 用旧玻璃罐和蜡烛做几个简单香薰蜡烛送朋友

**老马：周末想做个小项目，有什么点子？**
- A_none：
    - 用 Python 写一个命令行工具，自动整理下载文件夹里的文件按类型分类。
    - 做一个简单的个人网页，展示你最近读的书和电影评分。
    - 用树莓派或旧手机搭一个家庭天气和日历显示屏。
    - 写一个浏览器扩展，每天提醒你喝水并记录饮水量。
    - 做一个迷你记账应用，用本地存储记录每日开销并生成月度图表。（来自记忆「User was advised to use their phone's built-in notes app for simple bookkeeping (e.g., writing 'breakfast 15') and add up totals at month's end instead of installing an app」）
- B_memory：
    - 用旧手机做个家庭监控或天气时钟，摆在客厅挺实用。
    - 给家里做一本拿手面食的图文菜谱，把扯面和臊子的做法记下来。（来自记忆「User has been making wheat-based foods (面食) for over ten years, including hand-pulled noodles (扯面) and making saozi (臊子) topping」）
    - 用纸箱和木板搭个小钓鱼装备收纳架，手竿和配件都能归位。（来自记忆「User has a hand rod (手竿) type fishing rod and asked whether it needs no further care once collapsed」）
    - 整理一个周末追剧清单，把《亮剑》《我的团长我的团》这类经典排个顺序慢慢看。（来自记忆「User was recommended the classic 抗战剧 《亮剑》 and 《我的团长我的团》 as options for evening viewing」）
    - 做一锅臊子分装冷冻，试几种花椒面的用量，找出最香的那一版。（来自记忆「User's store uses Sichuan peppercorn powder (花椒面) in making 臊子 (minced meat topping), and a sprinkle of it makes the flavor right; the user feels homemade versions fall short of the store's」）

**阿叶：周末想做个小项目，有什么点子？**
- A_none：
    - 用树莓派做一个家庭温湿度监测仪，把数据实时显示在网页上。
    - 写一个命令行工具，自动整理下载文件夹里的文件并按类型归档。
    - 用 Python 做一个每日单词推送机器人，定时发到微信或 Telegram。
    - 搭一个本地照片相册网站，支持按地点和日期自动分类浏览。（来自记忆「User was advised to organize phone photos using the built-in gallery features or a '相册管家'-type app that auto-sorts by date and location, and to use batch rename functions in gallery apps or the right-click '批量重命名' menu on a computer instead of command-line tools」）
    - 做一个简易的番茄钟网页应用，带统计图表记录每天专注时长。（来自记忆「User was advised to put their phone far away before drawing, use a 25-minute focus timer, and set small goals like finishing one hand or one color block before taking a break」）
- B_memory：
    - 用手机拍一组'周末早餐'照片，配上你惯用的反差式文案发朋友圈（来自记忆「User was advised to make WeChat Moments captions fun by adding contrast or light self-deprecation, e.g. '今日份的快乐，保质期三分钟', keeping humor without complaining」）
    - 把儿童绘本里的小狐狸单独画一张水彩小插画，练手又攒素材（来自记忆「User recently took on a job illustrating a children's picture book (儿童绘本) whose main character is a little fox; the client wants the artwork to look gentle and soft」）
    - 学做一道新菜（比如麻婆豆腐升级版），全程拍照记录（来自记忆「User asked how to make mapo tofu (麻婆豆腐); was advised to blanch cubed tofu in salt water, stir-fry minced meat and doubanjiang, add water, add tofu, then thicken with starch and finish with ground Sichuan pepper」）
    - 整理快递签收纠纷的聊天记录和证据，写成一份维权时间线备忘（来自记忆「User's package was marked as delivered (签收) around November 26, 2026, but nothing was at their door; the courier said it was placed in a parcel locker (快递柜) but the user never received a pickup code」）
    - 做一张'100元能买什么'的物价小调查表，直观感受通货膨胀（来自记忆「User asked what inflation (通货膨胀) means and was told it means money is worth less — the same 100 yuan buys less — usually because more money is circulating or goods are scarcer, i.e., a general rise in prices」）

**周老师：周末想做个小项目，有什么点子？**
- A_none：
    - 用 Python 写一个命令行待办事项工具，支持增删改查和本地文件存储。
    - 做一个简单的个人记账网页，用 localStorage 保存数据并展示月度统计图表。
    - 用树莓派或旧手机搭建一个家庭网络监控面板，显示设备在线状态。
    - 写一个浏览器扩展，把当前网页的正文提取出来导出为 Markdown 文件。
    - 做一个番茄钟小应用，带桌面通知和每日专注时长记录。
- B_memory：
    - 给大黄做一个自动喂食提醒小装置，到点响铃并记录喂食时间。（来自记忆「User has a dog named 大黄 (Dahuang), a 土狗 (Chinese native dog), who has been shedding a lot recently, leaving hair all over the house」）
    - 整理你常听的老段子，做一个按演员、年代分类的私人播放列表小网页。（来自记忆「User mainly listens to old comedy routines (老段子) — both solo stand-up and two-person dialogue (相声-style) performances」）
    - 用手机拍大黄掉毛的日常，剪一支一分钟的搞笑短片配上相声台词。（来自记忆「User has a dog named 大黄 (Dahuang), a 土狗 (Chinese native dog), who has been shedding a lot recently, leaving hair all over the house」）
    - 做一个家庭群用的周末活动投票小工具，帮舅舅的曲艺队排节目。（来自记忆「User's uncle manages the quyi (曲艺, traditional folk performance) team at the county cultural center (县文化馆), and the user considered organizing activities through him to improve the group chat atmosphere」）
    - 写一个简单的记账小表格，记录看球时的零食开销和给大黄买狗粮的花费。

