# Benchmark 结果：带记忆的 AI 是不是只在记忆里打圈

5 个用户 × 10 个问题 × 6 组 × 3 次，每次 5 个点子，共 4500 个点子。回答、评委都是 DeepSeek，存在同源偏差（见 SPEC.md 第 6 节）。

## 总表

| 组 | 打圈率 | 被喜好带跑 | 踩陷阱 | 被过时信息带跑 | 合适率 | 好点子率（合适且跳出记忆） | 点子种类数（满分 15） |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A_none | 7% | 0% | 0% | 2% | 47% | 43% | 9.0 |
| B_memory | 52% | 9% | 3% | 4% | 69% | 33% | 8.1 |
| C_memory_nudge | 38% | 8% | 2% | 2% | 69% | 44% | 8.6 |
| D_memory_hot | 51% | 9% | 3% | 4% | 67% | 33% | 8.5 |
| E1_widen | 55% | 14% | 1% | 2% | 71% | 31% | 8.4 |
| E2_widen_hint | 53% | 16% | 2% | 3% | 73% | 31% | 8.4 |

## 每个用户的打圈率

| 用户 | A_none | B_memory | C_memory_nudge | D_memory_hot | E1_widen | E2_widen_hint |
| --- | --- | --- | --- | --- | --- | --- |
| 陈同学 | 13% | 43% | 35% | 49% | 47% | 41% |
| 小林 | 7% | 46% | 29% | 37% | 53% | 49% |
| 老马 | 2% | 44% | 37% | 47% | 48% | 44% |
| 阿叶 | 10% | 63% | 48% | 66% | 58% | 66% |
| 周老师 | 3% | 65% | 43% | 54% | 67% | 66% |

## 被哪一类信息带跑（占全部点子的比例）

| 组 | 只是喜好 | 会的技能 | 手上的资源 | 讨厌的 | 限制条件 | 背景 | 对不上人设的记忆 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A_none | 0% | 2% | 0% | 1% | 0% | 0% | 2% |
| B_memory | 9% | 11% | 5% | 3% | 5% | 6% | 13% |
| C_memory_nudge | 8% | 8% | 3% | 2% | 3% | 4% | 10% |
| D_memory_hot | 9% | 10% | 5% | 3% | 5% | 5% | 13% |
| E1_widen | 14% | 8% | 4% | 2% | 8% | 4% | 14% |
| E2_widen_hint | 16% | 8% | 4% | 1% | 8% | 3% | 12% |

## 出现次数的影响（B 组）

每条信息平均带出多少个点子，按“聊天里实际出现几次”分组。

| 种类 | 出现 1 次 | 出现 2 次 | 出现 4 次以上 |
| --- | --- | --- | --- |
| 只是喜好 | 0.8（10 条） | 1.9（11 条） | 10.2（4 条） |
| 会的技能 | 1.3（10 条） | 7.7（6 条） | 6.2（4 条） |
| 手上的资源 | 0.3（10 条） | 3.0（12 条） | 0.0（3 条） |
| 讨厌的 | 0.4（5 条） | 2.4（5 条） | 1.8（5 条） |
| 限制条件 | 1.0（5 条） | 2.4（10 条） | 1.0（5 条） |
| 背景 | 2.2（11 条） | 2.2（9 条） | - |

## 判定（标准事先写在 SPEC.md 第 1 节）

- 带记忆比不带记忆，打圈率平均高 45%；5/5 个用户高出 20 个百分点以上。→ **打圈成立**
- C_memory_nudge：把多出来的打圈率降回去 31%。→ **补救无效**
- D_memory_hot：把多出来的打圈率降回去 4%。→ **补救无效**
- E1_widen：合适率 71%（标准 ≥ 70%），好点子率 31%（标准 ≥ 55%）→ **未达标**
- E2_widen_hint：合适率 73%（标准 ≥ 70%），好点子率 31%（标准 ≥ 55%）→ **未达标**

## 例子：第 1 个问题，不带记忆 vs 带记忆

**陈同学：周末想做个小项目，有什么点子？**
- A_none：
    - 用 Python 写一个自动整理下载文件夹的小工具，按文件类型分类归档。（来自记忆「User wants to record their fish tank water temperature daily and set up a Python script to scrape the data from an online data page and save it into a spreadsheet」）
    - 做一个个人读书笔记网页，支持 Markdown 编辑和本地存储。
    - 用树莓派或旧手机搭建一个家庭天气与日程显示面板。
    - 写一个命令行番茄钟，带桌面通知和每日专注统计。
    - 做一个简易记账小应用，支持分类统计并生成月度图表。
- B_memory：
    - 用 Python 写一个自动整理手机照片的小脚本，按拍摄日期和地点分类归档。（来自记忆「User wants to record their fish tank water temperature daily and set up a Python script to scrape the data from an online data page and save it into a spreadsheet」）
    - 做一个个人记账小网页，手动录入每天开销并自动生成月度饼图。
    - 搭建一个简单的每日英语单词推送机器人，每天早上发到自己的微信或邮箱。
    - 用 Excel 或表格工具做一份个人年度阅读/观影记录表，带自动统计和进度条。
    - 写一个批量重命名与压缩图片的小工具，方便整理旅行照片后发给朋友。
- E1_widen：
    - 拍一条记录你周末小项目的短视频发到 YouTube，从构思到完成全程记录，既能督促自己动手，也能积累一点创作经验。
    - 用 Wi-Fi 在家搭一个小型家庭网络监测工具，记录各设备连接情况并做简单可视化，动手门槛低又有成就感。（来自记忆「User's home Wi-Fi signal is poor and drops significantly when passing through a single wall; the router is currently located in a corner of the living room」）
    - 用贝叶斯定理写一个小程序，根据你每天的学习时长和睡眠情况估算第二天的专注概率，既练手又能帮自己调整作息。
    - 在社交媒体上发起一个周末小挑战，比如连续两天分享一件小确幸，顺便练习写朋友圈文案，不必纠结措辞完美。（来自记忆「User struggles with writing WeChat Moments (朋友圈) captions and often doesn't know what to post」）
    - 做一个简单的记账小表格或小脚本，把这两周的开销分类统计并画个饼图，看看钱都花在哪儿了。（来自记忆「User is financially tight this month — their stipend/subsidy (补助) hasn't been paid yet and they have just over 2,000 yuan to live on, so they plan to buy only inexpensive gifts」）

**小林：周末想做个小项目，有什么点子？**
- A_none：
    - 用 Python 写一个命令行工具，自动整理下载文件夹并按文件类型分类。（来自记忆「User was advised to learn Rust by building a small project rather than reading a book, and was recommended to write a command-line tool such as a text word counter or a batch file renamer」）
    - 做一个极简的个人书签管理网页，支持标签筛选和本地存储。
    - 用树莓派或旧手机做一个桌面天气时钟，定时拉取天气 API 并显示。
    - 写一个脚本把 Markdown 笔记批量转换为带样式的静态 HTML 博客。（来自记忆「User has over 2,000 notes in Obsidian, most of them technical, and was looking for a tagging/organization approach because searching returned too many results」）
    - 做一个浏览器扩展，每天随机展示一条英语单词或冷知识。
- B_memory：
    - 用手机拍一段家里老物件的短视频，配上旁白讲它的来历
    - 把冰箱里的食材整理成一个'一周不重样早餐'清单并试做第一天
    - 用免费工具给女朋友做一个小程序或网页，用来记录她每天嗓子状态和喝水提醒（来自记忆「User has a girlfriend who is a primary school Chinese language teacher (小学语文老师) and has recently been losing her voice/getting hoarse」）
    - 整理手机相册，按时间线挑出 20 张照片做成一份可打印的年度小相册
    - 在阳台或窗台用几个旧瓶子做一个简易香草种植角，记录一周生长变化
- E1_widen：
    - 用手机记录一周的室内温度和湿度，再写个简单脚本做回归分析，看看闷热房间的温湿度变化规律。（来自记忆「User lives in shared housing (合租) where roommates often run the air conditioner at night, making their room uncomfortably hot」）
    - 做一个只属于自己的极简单页网站，把待办和灵感卡片放上去，不用费心整理笔记也能随手记录。
    - 写个小程序生成斐波那契数列，并把它画成螺旋图形，做成一个能在周末碎片时间里完成的可视化小项目。
    - 实现一个判断西瓜成熟度的小算法，把敲击声音或外观特征作为输入，用规则或简单模型给出参考结论。（来自记忆「User often struggles to tell whether a watermelon is ripe and says buying one is usually a matter of luck」）
    - 做一个水果保鲜小助手：记录买回的一箱水果的存放天数与口感变化，提醒最佳食用期，避免放久变面。（来自记忆「User typically buys fruit by the box (一箱), preferring a thin-skinned variety that is sweet and slightly translucent in the middle when cut open, but which gets mealy (面) and loses texture if stored too long」）

**老马：周末想做个小项目，有什么点子？**
- A_none：
    - 用 Python 写一个命令行工具，自动整理下载文件夹并按文件类型分类归档。
    - 做一个极简的番茄钟网页应用，支持自定义时长和本地存储统计。
    - 用树莓派或旧手机搭建一个家庭天气显示面板，定时抓取天气 API 并展示。
    - 写一个浏览器书签整理脚本，自动检测失效链接并生成报告。
    - 做一个本地 Markdown 笔记转静态博客的小工具，一键生成并预览网页。
- B_memory：
    - 把店里后面的小仓库彻底收拾一遍，量好尺寸，规划成分类收纳区或简易维修工作台。（来自记忆「User owns or runs a shop (店里) that has a small unused storage room (小仓库) at the back which has been sitting empty, and asked what it could be used for」）
    - 给店里做一块手写风格的价目表或招牌，用黑板漆或木牌，周末两小时能搞定。（来自记忆「User plans to write a price list (价目表) for their shop's repair services」）
    - 把平时修电饭锅、小台灯的工具和零件整理成一个便携工具箱，按用途分格收纳。（来自记忆「User also casually repairs small appliances for students, such as rice cookers (电饭锅) and small desk lamps (小台灯)」）
    - 周末试做一次臊子扯面，提前一晚炒好臊子，第二天专门练扯面手法，记录面团醒发时间。（来自记忆「User plans to try making 扯面 and 臊子 on Monday afternoon, which is the only free time they have since they are busy running their shop the rest of the week」）
    - 在店里角落装一个简易的手机充电站，用旧插排和收纳盒改造，方便学生顾客顺手充电。
- E1_widen：
    - 用手机浏览器打开一个免费国际象棋网站，周末花一两个小时学会基本走法并和电脑下一盘。
    - 把冰箱清空做一次彻底整理，用手机拍下现有食材列个简单清单，为下周备餐做准备。
    - 挑《黑道家族》的一两集试看，用手机浏览器在线观看，看完随手记几句观后感。
    - 如果家里有宠物，用现成材料给它做一个简单玩具或重新布置休息角。
    - 把店里那个空着的小仓库收拾出来，量好尺寸，规划成放工具和杂物的收纳角。（来自记忆「User owns or runs a shop (店里) that has a small unused storage room (小仓库) at the back which has been sitting empty, and asked what it could be used for」）

**阿叶：周末想做个小项目，有什么点子？**
- A_none：
    - 用 Python 写一个命令行工具，自动整理下载文件夹并按文件类型分类。
    - 做一个极简的个人书签管理网页，支持标签和全文搜索。
    - 用树莓派或旧手机搭一个家庭网络监控面板，显示网速和设备列表。
    - 写一个每日一句的 Telegram/Discord 机器人，从名言 API 拉取并定时推送。
    - 做一个本地照片去重工具，用感知哈希找出相似图片并生成报告。
- B_memory：
    - 给外婆做一本照片小册子，把老照片扫描后用手机修图软件排版，打印出来寄回去（来自记忆「User will likely need to return to Guizhou for one month in the second half of 2026 to care for their sick grandmother (外婆), which means no more sleeping in」）
    - 用剪映把手机里攒的美食照片做成一条15秒的小视频，配字幕发朋友圈（来自记忆「User often posts photos of food on WeChat Moments and asked what captions suit them」）
    - 给儿童绘本里的小狐狸画一套四季表情包，练手又能当作品集（来自记忆「User recently took on a job illustrating a children's picture book (儿童绘本) whose main character is a little fox, and the client wants the artwork to look gentle and warm」）
    - 整理一份贵州家乡小吃的图文清单，配上自己拍的或网上的图，做成简易电子手册（来自记忆「User's hometown is in Guizhou, China, an area with heavy dampness, and they wondered whether the damp climate contributes to their wrist discomfort」）
    - 试着用手机拍一条精酿啤酒开瓶到倒进杯子的慢镜头，练练拍摄和剪辑（来自记忆「User enjoys drinking craft beer (精酿啤酒)」）
- E1_widen：
    - 用纸牌或手机麻将App练几局本地规则，再整理一份适合和家人视频时玩的简化麻将计分表。
    - 用现成的在线模板做一张给奶奶看的家庭活动海报，不装任何软件也能完成。
    - 用手机逐帧拍摄手绘小纸片，做一个十几秒的翻页小动画，手腕不适就分几次慢慢画。
    - 用家里现有的水彩或食用色素在纸上做一组混色小样卡，记录配比做成配色参考。
    - 给儿童绘本里的小狐狸画一组暖色调的配色小样，顺便测试哪几种搭配最显温柔。（来自记忆「User recently took on a job illustrating a children's picture book (儿童绘本) whose main character is a little fox, and the client wants the artwork to look gentle and warm」）

**周老师：周末想做个小项目，有什么点子？**
- A_none：
    - 用 Python 写一个命令行工具，自动整理下载文件夹并按文件类型分类。
    - 做一个极简的个人网页，展示你最近读的书和听的音乐。
    - 用树莓派或旧手机搭建一个家庭天气与空气质量显示屏。
    - 写一个浏览器扩展，每天提醒你喝水并记录饮水量。
    - 做一个 Markdown 笔记转静态博客的小脚本，一键发布到 GitHub Pages。
- B_memory：
    - 整理一份县城老段子清单，按单口、对口分类，配上你舅舅文化馆的演出资源，方便在群里组织活动。（来自记忆「User's uncle (舅舅) manages the quyi (曲艺) performance team at the county cultural center (县文化馆) and can arrange activities; user considered organizing such activities in the group chat to improve the atmosphere」）
    - 给大黄做一个掉毛记录表，每天拍照加简单记录，看看换毛期到底持续多久。（来自记忆「User has a dog named 大黄 (Dahuang), a 土狗 (Chinese native/mixed breed), who has been shedding a lot recently, leaving hair all over the house」）
    - 把《静夜思》里“床”的几种说法做成一张小科普卡片，发到群里让大家投票猜谜。（来自记忆「User asked about the meaning of "床" (chuáng) in Li Bai's poem "床前明月光", wondering whether it refers to a bed for sleeping; the assistant explained that scholars interpret it variously as a sleeping bed, a well railing (井栏), or a folding stool (胡床/马扎), with no scholarly consensus」）
    - 拍一段县城晚上八九点空街的短视频，配上老段子音频，做成“县城夜生活”小短片。（来自记忆「User lives in a county town (县城) where there is little evening entertainment — the streets are empty by 8-9 PM — so they rely on old comedy/storytelling routines (老段子) to pass the time」）
    - 整理一份周末看球零食清单，顺便记下大黄每次来讨食的时间规律。（来自记忆「User watches Premier League (英超) football, often staying up until the middle of the night and getting very hungry」）
- E1_widen：
    - 用盐、糖、醋按不同配比腌一小批当季蔬菜做快手泡菜，每天观察记录保存变化。（来自记忆「User wants to pickle vegetables (腌咸菜) at home for winter and asked for a reliable method」）
    - 挑一个日常好奇的小现象，用手机和家里现成物品设计简单对照实验并记录数据。
    - 用家里的醋做小型对比实验，比如泡蛋壳或比较不同醋的酸度，用杯子和标签记录结果。
    - 用手机免费调音或示波器应用测量身边声音或摆动的频率，做成一张频率对照小表。
    - 把手机音量调大听几段老段子，记录不同音量下听清的段子数量，找出最适合自己的音量档位。（来自记忆「User listens to old comedy routines (老段子) and needs the volume turned up loud to hear them clearly」）

