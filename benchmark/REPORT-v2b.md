# Benchmark 结果：带记忆的 AI 是不是只在记忆里打圈

5 个用户 × 10 个问题 × 6 组 × 3 次，每次 5 个点子，共 4500 个点子。回答、评委都是 DeepSeek，存在同源偏差（见 SPEC.md 第 6 节）。

## 总表

| 组 | 打圈率 | 被喜好带跑 | 踩陷阱 | 被过时信息带跑 | 合适率 | 好点子率（合适且跳出记忆） | 点子种类数（满分 15） |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A_none | 7% | 0% | 0% | 2% | 47% | 43% | 9.0 |
| B_memory | 52% | 9% | 3% | 4% | 69% | 33% | 8.1 |
| C_memory_nudge | 38% | 8% | 2% | 2% | 69% | 44% | 8.6 |
| D_memory_hot | 51% | 9% | 3% | 4% | 67% | 33% | 8.5 |
| E1_widen | 45% | 8% | 2% | 3% | 72% | 39% | 8.2 |
| E2_widen_hint | 43% | 6% | 2% | 4% | 70% | 38% | 8.3 |

## 每个用户的打圈率

| 用户 | A_none | B_memory | C_memory_nudge | D_memory_hot | E1_widen | E2_widen_hint |
| --- | --- | --- | --- | --- | --- | --- |
| 陈同学 | 13% | 43% | 35% | 49% | 43% | 42% |
| 小林 | 7% | 46% | 29% | 37% | 47% | 37% |
| 老马 | 2% | 44% | 37% | 47% | 40% | 36% |
| 阿叶 | 10% | 63% | 48% | 66% | 53% | 57% |
| 周老师 | 3% | 65% | 43% | 54% | 44% | 43% |

## 被哪一类信息带跑（占全部点子的比例）

| 组 | 只是喜好 | 会的技能 | 手上的资源 | 讨厌的 | 限制条件 | 背景 | 对不上人设的记忆 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A_none | 0% | 2% | 0% | 1% | 0% | 0% | 2% |
| B_memory | 9% | 11% | 5% | 3% | 5% | 6% | 13% |
| C_memory_nudge | 8% | 8% | 3% | 2% | 3% | 4% | 10% |
| D_memory_hot | 9% | 10% | 5% | 3% | 5% | 5% | 13% |
| E1_widen | 8% | 5% | 4% | 4% | 9% | 4% | 11% |
| E2_widen_hint | 6% | 7% | 3% | 3% | 11% | 4% | 10% |

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
- E1_widen：合适率 72%（标准 ≥ 70%），好点子率 39%（标准 ≥ 55%）→ **未达标**
- E2_widen_hint：合适率 70%（标准 ≥ 70%），好点子率 38%（标准 ≥ 55%）→ **未达标**

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
    - 在阳台用几个花盆种薄荷和小葱，每天浇水观察发芽，给周末一个安静又具体的期待。
    - 做一个迷你香草小园，把薄荷、罗勒种在小盆里摆到窗台，既动手又能顺手改善心情。
    - 找几个简单折纸教程，从纸鹤或盒子开始折一整套小作品，专注折纸很适合放空脑子。
    - 带上手机在小区或公园拍一组「雨天之后」的主题照片，练习构图和光线。
    - 把手机里积攒的旧照片挑出几十张，按主题分类整理并简单修图，做成一个小相册。

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
    - 给女朋友做一个护嗓提醒小程序，定时提醒喝水、用嗓休息，还能记录每天的音量使用情况。（来自记忆「User has a girlfriend who is a primary school Chinese language teacher (小学语文老师) and has recently been losing her voice/getting hoarse」）
    - 做一个家庭水果成熟度追踪表，按箱记录购入日期和品种，到日子自动提醒先吃哪一箱，避免放面。（来自记忆「User buys apples by the box and eats about one every day, but the later ones in the box lose texture and become mealy (面)」）
    - 把孩子的数学应用题做成一张图文卡片，用画线段的方式讲清楚'两次购买差了多少支笔'这类题。（来自记忆「User asked how to explain to their child a math word problem: Xiaoming bought 3 pens and 2 notebooks for 24 yuan, and 5 pens and 2 notebooks for 32 yuan — find the price of one pen」）
    - 做一个'借钱请求应答助手'，预设几种不伤面子的婉拒话术，遇到熟人开口时直接挑一句用。（来自记忆「User has an acquaintance (不太熟的朋友) who asked to borrow money; the user does not want to lend it but worries about damaging the relationship/face (伤面子)」）
    - 周末花两小时搭一个极简的每日三件事打卡页面，手机打开就能勾，数据存在本地不用注册。

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
    - 用纸藤或旧布条编一个小收纳篮，坐在桌边就能完成，材料轻便又省钱。
    - 花一个下午做一张不用搬动的小木凳，材料在附近建材店一次买齐。
    - 缝一个布艺收纳袋，只用简单工具，做完当天就能用上。
    - 在阳台种几盆香草或小葱，周末只需浇水修剪，还能起身活动一下。
    - 用橡皮章或土豆刻几枚小印章，一两个小时就能刻好，成品马上能用。

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
    - 用家里的纸折一组仙鹤或小船，边折边用手机拍步骤，整理成一份不费手腕、不花钱的图文小教程。
    - 找一块旧布和几根线，绣一个巴掌大的小图案，每次只绣十几分钟，让画累的手腕换个轻缓的节奏。
    - 用彩铅或水彩临摹《神奈川沖浪裏》的一小块浪花局部，尺寸做小、分几次画完，练手又不累手腕。
    - 挑一幅前拉斐尔派的画，用免费图片和色卡做一张纯文字与配色分析的笔记页，不动手画也能完成小研究。
    - 把最近喝过的几款精酿啤酒按香气和苦度列成一张手写风味小卡片，配上酒标照片，做成自己的品鉴小档案。（来自记忆「User enjoys drinking craft beer (精酿啤酒)」）

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
    - 用冰棍棒或牙签在桌面上拼一个迷你相框，材料便宜、不占地方。（来自记忆「User enjoys doing small woodworking projects in their spare time and has several leftover pine boards on hand」）
    - 把家里的旧纸拿来折纸或做纸雕，几乎零成本，周末就能完成一件小作品。
    - 买一小块便宜的木方，用砂纸打磨后上油，练习手感、感受木纹。（来自记忆「User enjoys doing small woodworking projects in their spare time and has several leftover pine boards on hand」）
    - 用一个小花盆做简易堆肥或种一株香草，观察土壤变化，占地极小。
    - 整理一段老段子的文字稿或录音清单，做成自己的曲艺小档案，顺手练练嘴皮子。（来自记忆「User mainly listens to old comedy routines (老段子), both solo stand-up and two-person dialogue performances」）

