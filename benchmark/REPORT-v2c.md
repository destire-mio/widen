# Benchmark 结果：带记忆的 AI 是不是只在记忆里打圈

5 个用户 × 10 个问题 × 6 组 × 3 次，每次 5 个点子，共 4500 个点子。回答、评委都是 DeepSeek，存在同源偏差（见 SPEC.md 第 6 节）。

## 总表

| 组 | 打圈率 | 被喜好带跑 | 踩陷阱 | 被过时信息带跑 | 合适率 | 好点子率（合适且跳出记忆） | 点子种类数（满分 15） |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A_none | 7% | 0% | 0% | 2% | 47% | 43% | 9.0 |
| B_memory | 52% | 9% | 3% | 4% | 69% | 33% | 8.1 |
| C_memory_nudge | 38% | 8% | 2% | 2% | 69% | 44% | 8.6 |
| D_memory_hot | 51% | 9% | 3% | 4% | 67% | 33% | 8.5 |
| E1_widen | 48% | 7% | 2% | 5% | 83% | 43% | 8.4 |
| E2_widen_hint | 45% | 6% | 1% | 3% | 82% | 45% | 8.2 |

## 每个用户的打圈率

| 用户 | A_none | B_memory | C_memory_nudge | D_memory_hot | E1_widen | E2_widen_hint |
| --- | --- | --- | --- | --- | --- | --- |
| 陈同学 | 13% | 43% | 35% | 49% | 69% | 53% |
| 小林 | 7% | 46% | 29% | 37% | 43% | 47% |
| 老马 | 2% | 44% | 37% | 47% | 38% | 40% |
| 阿叶 | 10% | 63% | 48% | 66% | 53% | 45% |
| 周老师 | 3% | 65% | 43% | 54% | 35% | 39% |

## 被哪一类信息带跑（占全部点子的比例）

| 组 | 只是喜好 | 会的技能 | 手上的资源 | 讨厌的 | 限制条件 | 背景 | 对不上人设的记忆 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A_none | 0% | 2% | 0% | 1% | 0% | 0% | 2% |
| B_memory | 9% | 11% | 5% | 3% | 5% | 6% | 13% |
| C_memory_nudge | 8% | 8% | 3% | 2% | 3% | 4% | 10% |
| D_memory_hot | 9% | 10% | 5% | 3% | 5% | 5% | 13% |
| E1_widen | 7% | 6% | 5% | 6% | 8% | 6% | 10% |
| E2_widen_hint | 6% | 7% | 6% | 5% | 7% | 5% | 10% |

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
- E1_widen：合适率 83%（标准 ≥ 70%），好点子率 43%（标准 ≥ 55%）→ **未达标**
- E2_widen_hint：合适率 82%（标准 ≥ 70%），好点子率 45%（标准 ≥ 55%）→ **未达标**

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
    - 用宿舍公共微波炉做零油烟小实验：微波炉蒸蛋、烤红薯、马克杯蛋糕，成本低又不用久盯屏幕。（来自记忆「User recently started learning to cook and has already learned several dishes, finding it rewarding; they used to genuinely dislike cooking but now find themselves somewhat addicted to it」）
    - 周末用电饭煲或小锅炖一锅土豆胡萝卜炖鸡腿，分装几份当轮班后的夜宵储备。（来自记忆「User recently started learning to cook and has already learned several dishes, finding it rewarding; they used to genuinely dislike cooking but now find themselves somewhat addicted to it」）
    - 整理精简宿舍里的锅碗刀具，做一次“一人份炊具清单”，只留最常用几件，减少收拾负担。（来自记忆「User recently started learning to cook and has already learned several dishes, finding it rewarding; they used to genuinely dislike cooking but now find themselves somewhat addicted to it」）
    - 用手机在宿舍附近拍一组“夜班后清晨”主题照片，练构图和光线，不花钱也不久坐电脑前。
    - 给自己做一份“夜班后快速夜宵食谱卡”，用现有锅具写 5 个十分钟内能搞定的组合，贴在冰箱上。（来自记忆「User recently started learning to cook and has already learned several dishes, finding it rewarding; they used to genuinely dislike cooking but now find themselves somewhat addicted to it」）

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
    - 帮女朋友做一个「护嗓提醒」小程序，定时提醒喝水、少说话，并记录每天用嗓时长。（来自记忆「User has a girlfriend who is a primary school Chinese language teacher (小学语文老师) and has recently been losing her voice/getting hoarse」）
    - 做一个家庭水果箱管理小工具，记录每箱水果的购买日期和最佳食用期，快到期时提醒优先吃掉。（来自记忆「User buys apples by the box and eats about one every day, but the later ones in the box lose texture and become mealy (面)」）
    - 写一个把小学数学应用题自动生成图示的脚本，比如用线段图解释「3支笔+2本本子=24元」这类题。（来自记忆「User asked how to explain to their child a math word problem: Xiaoming bought 3 pens and 2 notebooks for 24 yuan, and 5 pens and 2 notebooks for 32 yuan — find the price of one pen」）
    - 做一个「借钱请求委婉拒绝」话术生成器，输入关系亲疏和金额，输出几种不伤面子的回复模板。（来自记忆「User has an acquaintance (不太熟的朋友) who asked to borrow money; the user does not want to lend it but worries about damaging the relationship/face (伤面子)」）
    - 用旧手机做一个厨房定时器+菜谱语音播报小站，做饭时不用动手就能查下一步。

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
    - 用手机在店里随手拍学生和街景练构图和光线，拍完只挑一张发朋友圈，不折腾修图软件。
    - 在店里做点折纸或串珠小挂件这类简单手工，坐着慢慢做，成品送给常来的学生当小礼物。
    - 在窗台或店门口用几个小盆种点好养的香草和绿植，每天浇点水，薄荷叶还能自己泡水喝。
    - 用纸藤或旧报纸编个小收纳筐，坐着编、材料轻便，成品放家里装杂物。
    - 把店后面那间空着的小仓库收拾一下，量好尺寸、规划成放杂物或给学生临时寄存东西的小角落。（来自记忆「User owns or runs a shop (店里) that has a small unused storage room (小仓库) at the back which has been sitting empty, and asked what it could be used for」）

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
    - 用纸黏土捏一只小狐狸摆件，每天抽一两个小时分段做，做完拍照存成作品集。（来自记忆「User recently took on a job illustrating a children's picture book (儿童绘本) whose main character is a little fox, and the client wants the artwork to look gentle and warm」）
    - 用手机在合租房窗边拍一组光影静物小品，每天随手拍几张，不用买设备。
    - 和室友在小厨房包一次饺子，用现成馅料和面皮，成本低还有成品吃。
    - 用手机记录榆林本地一条街或一个市场的日常，整理成配短文字的图片小故事。
    - 把最近喝过的几款精酿啤酒做一张手绘风味小卡片，配简短的品饮笔记。（来自记忆「User enjoys drinking craft beer (精酿啤酒)」）

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
    - 用家里的盐、糖和密封罐做几组小份腌制或糖渍对比实验，记录哪种配比更耐放，材料几乎不花钱。（来自记忆「User wants to pickle vegetables (腌咸菜) at home for winter and asked for a reliable method」）
    - 在阳台用废弃塑料瓶和菜市场要来的种子种几盆香草或小葱，每周日固定浇水记录生长。
    - 做多肉或绿萝的小型扦插繁殖，用一次性杯子和园土试不同基质，观察生根差异。
    - 跟着网上教程折纸，只拍手和桌面做步骤图解或无声短视频，材料只需几张纸。
    - 把家里旧衣服剪成布条编一个地垫或收纳篮，边做边记录尺寸和用布量，零成本又实用。

