# VidMuse 重复与高关联风格保留审核

## 1. 审核目的与口径

本文只审核第二阶段 24 条候选中已经确认同名重复或与后台风格高度关联的 20 条，回答三个问题：

1. 该候选是否能作为一个独立、可选择、可生成的产品风格；
2. 它与后台已有条目应当合并、父子共存、替换旧定义，还是暂缓；
3. 保留后，Planner 和生成链是否能得到与相邻风格稳定不同的结果。

判断基于：

- 后台快照中的 79 条风格及其 `name`、`tags`、`description`、预览图；
- 第二阶段候选的 `name`、`tags`、`description`、`analysis`、`promptSample` 和参考图 Prompt；
- 当前插件以 `name + tags` 做全库选择、以 `analysis + promptSample` 执行生成的实际调用方式。

后台快照没有保存这些旧条目的 `analysis` 和 `promptSample`，因此本文不推测旧值，只根据可见字段和预览图判断旧条目当前实际代表的风格。

### 1.1 保留标准

高关联不等于重复。一条作品叶子只有同时满足以下条件，才值得与导演、摄影师或系列父风格共存：

- **独立用户意图**：用户会明确想要这一作品效果，而不只是泛指父 Anchor；
- **稳定视觉增量**：至少在色彩、光线、构图空间、镜头动态、纹理媒介中有三项稳定差异；
- **可迁移**：这些差异换成人物、场景和项目后仍成立，不依赖角色、道具或名场面；
- **可路由**：Planner 只看 `name + tags` 时能够区分；读取 description 后能够解释为什么选它；
- **可执行**：同一中性内容生成时，结果能与父风格或近邻稳定拉开。

如果只是在父风格后增加地点、年代、颜色或作品名，而生成方法没有改变，则不应独立入库。

## 2. 总体结论

| 处理结论 | 数量 | 风格 |
|---|---:|---|
| 保留现有记录，合并新稿，不新增重复记录 | 6 | Wong Kar-wai、Blade Runner 2049、Amélie、The Matrix、Stanley Kubrick、David Fincher |
| 保留为独立作品叶子，但需先修正父项或近邻 | 12 | Dune、2001、The Tree of Life、All About Lily Chou-Chou、Song to Song、Fight Club、Blade Runner、The Shining、Frankenstein (2025)、Seven Samurai、High and Low、Ivan's Childhood |
| 条件保留为跨作品父风格 | 1 | Terrence Malick |
| 暂缓入库，先证明独立增量 | 1 | Asteroid City |

这里的“保留现有记录”指保留后台原记录身份和历史关系，新稿作为内容升级来源；不允许创建第二条同名记录。

## 3. 六条同名重复风格

### 3.1 Wong Kar-wai Inspired

**后台现状**：旧 tags 只有 `Film grain`、`Wong Kar-wai style`、`Street photography style`。description 能表达都市忧郁、浓郁调色、运动模糊和 step-printing，但后半段依赖霓虹招牌、烟雾、雨街等常见母题。预览图能表现湿街、彩光和运动拖影，但文字招牌很多，且更像“香港夜景”而不是完整的亲密空间语法。

**新稿增量**：补足了混合实景彩光、反射层次、长焦压缩、遮挡式近距构图和时间拖影，能够解释它为何不同于普通 neon noir。

**保留建议**：**保留后台原记录并合并新稿，不新增。** name 沿用；tags、description、analysis、promptSample 以新稿为主要基础，但避免把红、绿、青、琥珀和长焦写成每个镜头必须同时满足的固定模板；预览图重新生成。

**理由**：身份完全相同，双条目没有任何路由价值。新稿更有利于生成，旧稿保留了用户熟悉的 step-printing 认知，两者应合成一个更完整的记录。

### 3.2 Blade Runner 2049 Inspired

**后台现状**：旧 tags 使用 `Neo-Noir`、`Roger Deakins Style` 等宽泛标签；description 和预览图把 2049 表现成粉青霓虹、雨街、中文招牌和密集城市，实际上更接近原版 Blade Runner 或通用 cyberpunk。

**新稿增量**：强调巨大负空间、孤立人物尺度、扩散荧光、工业雾和安静巨构，准确建立了与原版 Blade Runner 的边界。

**保留建议**：**保留后台原记录，整体采用新稿方向，不新增。** 旧预览图必须替换；新稿还需在最终执行前补充琥珀荒漠、冷白室内等可选色彩状态，不能把整部作品压缩成灰绿一种色调。

**理由**：新稿不是另一个风格，而是在纠正旧条目的错误定义。保留旧记录身份可避免历史引用断裂，同时能为后续新增原版 Blade Runner 腾出清晰边界。

### 3.3 Amélie Inspired

**后台现状**：旧 tags 简短且有 `Whimsical Realism`，但 description 依赖红房间、勺子、复古道具等作品内容。预览图直接接近女主外貌、发型和咖啡馆，辨识主要来自角色复刻。

**新稿增量**：把效果抽象为黄绿与暖红的组织关系、广角近距、正面视觉、图形化插入和触感室内，更适合迁移到原创 MV。

**保留建议**：**保留后台原记录，采用新稿的视觉机制并重新生成原创预览，不新增。** 旧版 `Whimsical Realism` 可继续作为高价值通用标签；黄色和绿色应描述色彩关系，不能成为覆盖肤色的统一滤镜。

**理由**：新稿解决的是旧条目“认出角色而不是认出风格”的问题。名称和用户意图完全相同，应升级而不是并列。

### 3.4 The Matrix Inspired

**后台现状**：旧 tags 中 `Commercial` 没有风格价值；description 依赖绿色代码、黑皮衣和 bullet time，预览图也高度依赖类似 Trinity 的服装和姿态。

**新稿增量**：提炼出绿黑 tech-noir、荧光实景光、湿反射、广角几何、空间可读的精准动作，以及暗色现实与白色构造空间的对照。

**保留建议**：**保留后台原记录并用新稿升级，不新增。** 绿色暗空间与白色构造空间应作为两种可切换状态，不要求每个镜头同时出现；参考图应使用原创表演者和非标志性服装。

**理由**：旧条目靠 IP 符号命中，新稿才是可迁移的执行规则。二者服务同一个用户选择，必须合并。

### 3.5 Stanley Kubrick Inspired

**后台现状**：旧条目将 Kubrick 主要概括为广角、单点透视、对称、冷感和走廊；预览图是带明显上下黑边的机构走廊，实际高度偏向 The Shining。

**新稿增量**：增加深焦调度、色调块、仪式化人物关系、材质清晰度和冷静的时间控制，并承认跨作品色彩变化。

**保留建议**：**保留后台原记录，重写为真正跨作品父风格，不新增同名记录。** 父项以 formal control、空间秩序和疏离调度为不变量；对称与单点透视只能是常见方法，不能成为每个镜头的硬约束。预览图必须替换。

**理由**：Kubrick 作为导演 Anchor 有独立用户需求，值得保留父项；但只有先去除 The Shining 偏置，2001 和 The Shining 两个作品叶子才有共存空间。

### 3.6 David Fincher Inspired

**后台现状**：旧 tags 只有低饱和、纪录片风格和 Fincher 名称，其中 `Documentary style` 会造成误召回。description 偏向绿黄犯罪片、地下室和档案柜，预览图是通用绿色侦探 noir。

**新稿增量**：补充可读暗部、受控低调曝光、硬实景光池、精密空间、干净暗质感和近乎无感的机位控制。

**保留建议**：**保留后台原记录并用新稿升级，不新增。** 将稳定核心放在“克制色彩、精确构图、受控暗部和程序性张力”，绿琥珀只作为常见色彩状态，避免把父风格锁死在 Fight Club 或 Se7en 时期。

**理由**：新旧稿指向同一个导演级选择。父项清理后，Fight Club 才能以更脏、更身体化的作品叶子独立存在。

## 4. 高关联作品叶子与父风格

### 4.1 Dune Film Series Inspired 与 Denis Villeneuve Inspired

**后台现状**：现有 Denis 条目的 tags 直接包含 `Dune Style`，description 写沙尘、巨大 brutalist 建筑、漂浮香料颗粒和未来荒原，预览图也是沙色飞船与巨构。它名为导演父风格，实际内容已经是 Dune。

**候选独立性**：Dune 新稿的硬暖日光、沙丘地平线、微小剪影、风沙和仪式尺度是清晰、可迁移的作品语法；用户也会明确搜索 Dune，而不是只搜索导演。

**保留建议**：**保留 Dune 为独立作品风格，但不得与当前 Denis 条目原样共存。** 上线前必须先把 Denis 重写为真正跨作品的“纪念碑尺度、受控负空间、严肃科幻和大气体积”父风格，移除香料、沙漠和 Dune 专属内容；若暂时无法重写父项，则优先将现有 Denis 条目迁移为 Dune，暂缓导演父项。

**理由**：Dune 本身有足够独立价值，问题来自旧父项命名错误。直接新增会让 Planner 面对两个几乎相同的候选，先修父项是硬前置条件。

### 4.2 2001: A Space Odyssey Inspired 与 Stanley Kubrick Inspired

**后台现状**：现有 Kubrick 偏对称走廊和心理恐惧，缺少跨作品范围。

**候选独立性**：2001 具有临床白红几何、圆形空间系统、科技极简、尺度跃迁和受控光学失真，至少在色彩、空间、题材媒介和情绪上明显不同于导演父项。

**保留建议**：**保留 2001 作品叶子，同时保留并重写 Stanley Kubrick 父项。** 父项 tags 强调 formalist cinema、deep-focus staging、controlled geometry；2001 强调 clinical sci-fi、white-red geometry、monumental minimalism 和 optical distortion。

**理由**：用户既可能要求“像 Kubrick”，也可能明确要求“2001 式临床科幻”。两种选择会产生不同项目结果，作品叶子不是简单添加太空场景。

### 4.3 The Tree of Life Inspired 与 Emmanuel Lubezki Inspired

**后台现状**：现有 Lubezki 虽名为摄影师父风格，tags 和 description 实际集中于 The Revenant：冰雪、皮毛、寒冷生存、超广角和自然光；预览图也是结霜人物特写。

**候选独立性**：The Tree of Life 的自然逆光、低地平线、家庭近距、阈限空间和元素性扩张，与冰雪求生在用户意图和可见效果上不同。

**保留建议**：**保留 The Tree of Life。** 现有 Lubezki 条目应优先改名和收敛为 `The Revenant Inspired`；只有取得跨作品证据并重写后，才适合继续以 Emmanuel Lubezki 为父项名称。

**理由**：二者共享摄影方法，但不是同一个产品风格。当前冲突主要是旧条目 Anchor 层级错误，而非 Tree of Life 缺少独立性。

### 4.4 All About Lily Chou-Chou Inspired 与 Shunji Iwai Inspired

**后台现状**：现有 Shunji Iwai 使用高键、过曝、柔焦、逆光空气感和温柔青春叙事，预览图也是明亮窗边人物。

**候选独立性**：Lily Chou-Chou 使用冷绿日光、开阔远距、人物孤立、脆弱高光和早期数码低保真，情绪更疏离、更不稳定。它与父项在色彩、距离、媒介纹理和情绪上都有稳定差异。

**保留建议**：**保留两者。** Shunji Iwai 负责明亮、柔焦、易碎的青春浪漫；Lily Chou-Chou 负责冷绿、远距、数码不稳定和青春异化。两者 description 必须互相写明边界。

**理由**：这是成立的导演父项与作品叶子关系。删除作品叶子会失去 shoegaze、dream pop 和疏离青春项目所需要的具体生成控制。

### 4.5 Song to Song Inspired 与 Emmanuel Lubezki Inspired

**后台现状**：旧 Lubezki 条目被 The Revenant 的冰雪生存内容占据，不能代表其在 Malick 合作中的摄影方式。

**候选独立性**：Song to Song 的超广角身体近距、现代玻璃室内、窗洗日光、非对称流动和关系性躁动是明确的当代亲密风格，与旧条目的寒冷荒野差异很大。

**保留建议**：**保留 Song to Song。** 与 The Tree of Life 共存时，前者必须稳定指向当代室内和躁动身体距离，后者稳定指向低地平线、元素自然和精神扩张；旧 Lubezki 按上一条处理。

**理由**：它不是“另一种自然光”，而是利用镜头距离、现代空间和身体运动形成不同的项目效果，适合完全不同的 MV 意图。

### 4.6 Fight Club Inspired 与 David Fincher Inspired

**后台现状**：现有 Fincher 条目已经包含低饱和绿黄、低调光、精确机位和心理惊悚，但又混入地下室等特定犯罪片内容。

**候选独立性**：Fight Club 的脏荧光、湿暗表面、绿青化学偏色、近距身体压力和粗粝胶片感，比 Fincher 父项更肮脏、更不稳定、更具肉身冲突。

**保留建议**：**保留 Fight Club 叶子，同时先完成 David Fincher 父项合并升级。** 父项保持干净、受控、克制和程序性；作品叶子强调化学污染、身体压迫和工业粗粝。

**理由**：如果父项继续以地下室和绿黄犯罪片定义，两者会重复；父项清理后，它们会服务“精密心理控制”和“脏污反叛压力”两种不同项目需求。

### 4.7 Asteroid City Inspired 与 Wes Anderson Inspired

**后台现状**：现有 Wes Anderson 已由完美对称、平面构图、粉彩、deadpan、精确几何运动定义；预览图进一步强化了粉彩布景、正面群像和玩具屋感。

**候选增量**：Asteroid City 增加硬质高键沙漠光、桃色与青绿色、舞台式荒原和更薄的景深层次。但其中沙漠和建筑很容易退化为场景内容，剩余构图方法仍高度属于通用 Wes Anderson。

**保留建议**：**暂缓入库。** 先用相同的非沙漠中性主体，对 Wes Anderson 与 Asteroid City 做多轮生成；只有在去掉沙漠母题后仍能稳定表现更硬、更平、更明亮、更舞台化的视觉差异，才保留作品叶子。否则把这些特征作为 Wes Anderson 的可选表达，不新增条目。

**理由**：这是 20 条中独立增量最不确定的一条。仅凭作品名和沙漠配色不足以承担新的风格选择。

### 4.8 Blade Runner Inspired 与 Blade Runner 2049 Inspired

**后台现状**：旧 2049 条目和预览图错误地偏向密集霓虹雨街，使它与原版 Blade Runner 看起来重复。

**候选独立性**：原版 Blade Runner 的密集街面、潮湿反射、混合实景光、垂直拥挤和 retro-futurist grit，与新稿 2049 的空旷巨构、孤立尺度、扩散照明和安静大气可以稳定区分。

**保留建议**：**保留两部作品风格，但按顺序处理：先修正现有 2049，再新增原版 Blade Runner。** 两条 description 必须互相点名边界，预览图使用同类中性主体展示“密集潮湿”与“空旷纪念碑”差异。

**理由**：同系列不等于同风格，两部作品对应的音乐、节奏和空间意图不同。当前冲突来自旧 2049 定义错误，修正后双条目有明确产品价值。

### 4.9 The Shining Inspired 与 Stanley Kubrick Inspired

**后台现状**：现有 Kubrick 条目已经大量使用 The Shining 的对称走廊、稳定跟拍、冷感和心理恐惧，预览图也直接呈现走廊。

**候选独立性**：The Shining 叶子进一步由红绿饱和室内、重复图案、家庭空间异化、走廊节奏和持续追踪构成，独立用户意图很强。

**保留建议**：**条件保留两者：先重写 Kubrick 父项，再新增 The Shining。** 父项不得继续使用走廊、浴室镜子等作品母题，也不能让 `one-point perspective` 和 `axial symmetry` 同时成为每次生成的硬约束；叶子则可明确承担走廊、图案和饱和室内压力。

**理由**：The Shining 值得独立，但当前父项占用了它的全部辨识特征。先修父项是避免伪重复的必要条件。

### 4.10 Terrence Malick Inspired 与 Emmanuel Lubezki Inspired

**后台现状**：现有 Lubezki 是 The Revenant 化的摄影师条目，与真正的跨作品 Malick 语法并不等价。

**候选独立性**：Terrence Malick 新稿具备跨作品证据，核心是自然逆光、宽角身体近距、阈限、风水运动、探索式摄影和人与环境之间的精神联系。它不仅是摄影参数，也包含导演层面的调度与情绪组织。

**保留建议**：**条件保留 Terrence Malick 为父风格。** 前提是先把旧 Lubezki 改名为 The Revenant 或重写为真正的摄影师父项，并验证 Planner 能把“泛 Malick 诗性自然主义”交给父项、把元素性自然和当代关系分别交给 The Tree of Life 与 Song to Song。若当前 Planner 无法稳定执行父子精排，则首批先上两个作品叶子，Malick 父项暂缓。

**理由**：它在内容上成立，但产品价值取决于父子检索是否真正可用。这里不能只凭跨作品证据就忽略选择链的互相抢召回。

### 4.11 Frankenstein (2025) Inspired 与 Guillermo del Toro Inspired

**后台现状**：现有 Guillermo del Toro 是暖琥珀、深阴影、机械钟表、旧工业室内和华丽哥特；预览图也以青橙楼梯、齿轮和古董空间为主。

**候选独立性**：Frankenstein (2025) 使用冷青灰、阴天扩散光、冰水石材、海洋气候和孤立巨尺度，至少在色彩、光线、空间、材质和自然力量上与父项不同。

**保留建议**：**保留两者。** Guillermo 父项继续负责暖色、繁复布景和机械哥特；Frankenstein 叶子负责冷色、气候现实、海洋尺度和肃穆浪漫。叶子不得依赖怪物造型或原作服装。

**理由**：虽然同导演、同属哥特，但实际生成结果和适用音乐明显不同，是具有独立价值的作品叶子。

### 4.12 Seven Samurai Inspired 与 Akira Kurosawa Inspired

**后台现状**：旧 Kurosawa 条目描述远摄压缩、风雨、泥地、草地和军队运动，已经明显偏向历史动作片；预览图是彩色武士队伍，既不够跨作品，也没有准确代表 Seven Samurai 的黑白质感。

**候选独立性**：Seven Samurai 新稿由黑白硬日光、湿地形、群体几何、清晰动作关系和高颗粒构成，可迁移到乐队、群舞和集体冲突，不依赖武士角色。

**保留建议**：**保留 Seven Samurai，同时重写 Akira Kurosawa 父项。** 父项应保留天气、群体调度、空间清晰度和静动转换等跨作品规律，移除军队、武士等内容偏置；Seven Samurai 叶子承担黑白、湿地和集体动作压力。

**理由**：作品叶子有独立价值，但当前父项错误占用了它的内容。重写后，泛 Kurosawa 与 Seven Samurai 明确查询可以共存。

### 4.13 High and Low Inspired 与 Akira Kurosawa Inspired

**后台现状**：旧 Kurosawa 偏户外、天气和历史动作，并不能覆盖 High and Low 的现代室内社会压力。

**候选独立性**：High and Low 依靠宽银幕群体阻挡、深焦室内、建筑负空间、硬图形反差和静态谈判张力，在场景、镜头、运动和用户意图上都与旧父项显著不同。

**保留建议**：**保留 High and Low，并与上一条共同推动 Kurosawa 父项重写。** 父项负责跨作品调度原则；Seven Samurai 和 High and Low 分别承担“天气驱动的群体行动”和“室内程序性社会压力”。

**理由**：这是非常有说服力的作品叶子。即使用户不知道片名，它也能为谈判、层级、群体决策和爵士叙事 MV 提供当前库中缺少的生成方案。

### 4.14 Ivan's Childhood Inspired 与 Andrei Tarkovsky Inspired

**后台现状**：现有 Tarkovsky 由大地色、自然光、雨火水、湿土、乡野室内和极慢长镜头构成，属于较宽的诗性元素风格。

**候选独立性**：Ivan's Childhood 使用单色、垂直自然节奏、反射水光、小人物景观尺度、高角度空间和梦境式明暗转换，与父项在色彩、构图和情绪视角上具有稳定差异。

**保留建议**：**保留两者。** Tarkovsky 父项继续承担元素、时间和物质触感；Ivan 叶子承担单色、垂直线性、小人物尺度和脆弱记忆。父项 description 应去除会锁定单部作品的具体乡野道具。

**理由**：这不是把父项变成黑白版本，而是改变了空间组织和观看主体，能够产生不同的 MV 叙事效果。

## 5. 推荐的实际处理顺序

1. **先合并六条同名重复**：不创建新记录，避免库内立即出现硬重复。
2. **先纠正四个写偏的父项**：Denis Villeneuve、Stanley Kubrick、David Fincher、Akira Kurosawa。
3. **纠正两个错误层级条目**：现有 Emmanuel Lubezki 优先收敛为 The Revenant；现有 Blade Runner 2049 改为真正的 2049 视觉语法。
4. **再放行边界最清楚的作品叶子**：2001、The Tree of Life、All About Lily Chou-Chou、Song to Song、Fight Club、Blade Runner、Frankenstein、Seven Samurai、High and Low、Ivan's Childhood。
5. **依赖父项修正后放行**：Dune、The Shining。
6. **单独验证**：Terrence Malick 做父子检索测试；Asteroid City 做去沙漠母题的同题生成测试。

## 6. 上线前的最低证明

每个计划共存的父子或近邻组合，都应在双方声明适用范围的交集中选择相同可比内容生成对照，再在各自适用范围内更换内容验证迁移。人物、表演、室内和环境只在双方都适用时选用，不作为所有媒介的固定题目。只有同时满足以下结果才可以共存：

- 不使用来源特有角色和标志性场景时，仍能被视觉审核者稳定区分；
- Planner 面对宽泛 Anchor 需求时选父项，面对明确叶子 Anchor 或视觉意图时选叶子项；
- 两条的 tags 不只是换了同义词，promptSample 不只是增加作品名；
- 每条至少有三项稳定可见差异，且不会因在适用范围内更换可比内容而消失；
- 参考图展示的是生成结果差异，而不是来源识别差异。

若同题测试只能靠来源特有角色、服装、地点、名场面或其他偶然内容区分，应判定为尚未建立独立风格。内容依赖型风格中已经被边界审核确认为风格本体的通用母题不在此列，但其适用范围必须相应收窄。
