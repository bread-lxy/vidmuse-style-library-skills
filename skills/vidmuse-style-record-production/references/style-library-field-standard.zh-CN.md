# VidMuse 风格库六字段内容规范

## 1. 这份规范解决什么

回答一个具体问题：

> 一个已经通过聚类验证的风格候选，怎样写成能被 Planner 正确选择、被生成链路正确执行、并让用户实际感知到效果的六字段风格。

风格是否成立，应先按照 [风格定义与批量聚类规则](style-clustering-rules.zh-CN.md)判断。本规范不能通过文案创造风格，也不能把视觉规律不稳定的 Anchor 包装成可入库风格。

后台只保留以下六个生产字段：

```json
{
  "name": "string",
  "tags": ["string"],
  "description": "string",
  "analysis": "string",
  "promptSample": "string",
  "imageUrl": "string"
}
```

六字段只承载风格本身。模型名称、质量灌水词、权重语法、画幅和分辨率、负向提示、生成命令、素材来源、工作流备注以及具体角色、剧情和名场面，都不属于风格内容。

生产字段使用英文；本规范使用中文解释字段职责和审核方法。

## 2. 六字段如何共同工作

### 2.1 边界-它们分别服务于六个不同决策

| 字段 | 唯一职责 | 进入生成 Prompt | 不能代替它的字段 |
|---|---|---:|---|
| `name` | 给用户和 Planner 一个稳定、可理解的 Anchor 身份 | 默认不进入 | tags 不能代替用户可读名称 |
| `tags` | 用短而有序的视觉指纹完成全库路由，并在 Prompt 前端建立最高优先级方向 | 原样置于前端 | description 太长，analysis 太细 |
| `description` | 解释适用项目、用户意图、推荐理由和近邻边界 | 不进入 | tags 不能表达“为什么选它” |
| `analysis` | 告诉 Agent 怎样把风格规律迁移到适用范围内的不同内容与输出 | 用于推理与扩写，不整段照抄 | promptSample 无法容纳条件和机制 |
| `promptSample` | 把完整规律编译成可复用、协调一致的执行壳 | 置于项目内容之后 | tags 只有离散方向，不能说明组合关系 |
| `imageUrl` | 向用户和审核者证明应用后的可见结果 | 不进入 | 文字不能代替用户的视觉判断 |

六字段来自同一套视觉规律，但不是同一段话的长、中、短改写：

- `name` 负责身份，不负责描述画面。
- `tags` 负责路由和高优先级视觉方向，不负责项目适用性说明。
- `description` 负责选择理由，不负责指导模型绘图。
- `analysis` 负责完整机制和迁移方法，允许解释条件、关系和边界。
- `promptSample` 只保留每次生成都应执行的画面方法，不承担知识说明。
- 能直接改变画面的核心特征进入 `tags`，更完整的组合方式进入 `promptSample`。
- `imageUrl` 负责证明上述内容确实能成为可见结果。

若同一信息在多个字段出现，必须是为了不同调用目的。例如“自然逆光”可以作为 tags 中的高优先级方向，在 analysis 中解释光源、曝光和空间作用，在 promptSample 中与镜头和质感组成完整配方；description 只在它构成项目选择理由时提及。

### 2.2 当前链路与目标链路

当前默认插件的真实行为是：

1. `style list --view summary` 一次返回全库的 `name + tags + imageUrl`，Planner 依靠 `name + tags` 选择候选。
2. `style get --view full` 返回 `description + analysis + promptSample` 等完整信息；当前主要在用户确认后读取，S2 单一精确命中时会读取 description 展示。
3. T2I、T2V、I2I 会原样把 `visualStyle.tags` 放在 Prompt 前端；T2I、T2V、I2I 和部分参考图链路以 `promptSample` 形成末端 Style 内容，并用 `analysis` 扩写缺失的视觉细节。
4. description 不会写入 DSL，也不会进入生成 Prompt。

因此，库规模扩大后的目标选择链应是：

```text
全库 name + 分层 tags 粗筛
→ 对 Top K 候选读取 description 精排
→ 用户或 Planner 确认
→ 读取 analysis + promptSample 执行
→ imageUrl 供用户选择与结果预期校准
```

当前插件尚未对多个 Top K 候选批量读取 description。若未来仍只在确认后读取，description 写得再好也不能提高自动匹配；扩大风格库时应同步把“Top K description 精排”落实到 Planner 调用逻辑。本文先规定内容合同，不把尚未实现的调用写成当前事实。

CLI 本身已经支持 `style list --tag`、多个 tag 交集以及 `limit/offset` 分页，但默认 selector 目前仍使用 `--limit 100` 读取全量摘要。库规模超过 100 条后，分层 tags 只是内容基础，Planner 还必须使用前两层 tag 粗筛或分页；否则部分风格不会进入候选上下文，后续精排无从发生。

生成链的目标组织方式是：

```text
图片 Prompt = tags → 项目内容 → promptSample
视频 Prompt = tags → 镜头内容与动态 → analysis 中与当前镜头有关的规律
```

模型适配、质量要求和输出参数由调用层添加，不写入风格库。

## 3. 六字段内容标准

### 3.1 `name`：用户可理解的风格身份

`name` 是已经通过聚类验证的 Anchor 的用户可读名称，同时承担目录识别、搜索命中和选择展示。它不只是内部 Anchor 层级标签。

一个合格名称需要同时做到：

- **准确**：不把作品级规律夸大成导演级，不把普通 trait 包装成子风格。
- **可理解**：用户能认出公共名称，或至少知道它指向人物、作品、流派还是媒介。
- **可区分**：与库内近邻不会同名、误导或只有无意义后缀差异。
- **可预期**：名称与 imageUrl、tags 呈现的是同一个风格，不靠内部编号或聚类术语解释。

人物、作品和 IP 通常使用 `Inspired`，例如 `David Fincher Inspired`、`The Tree of Life Inspired`。已有稳定公共名称的流派、媒介和社区审美直接使用通用名称，例如 `Claymation`、`Dreamcore`、`Poolcore`。

若导演跨作品不稳定，就使用具体作品；若作品内部也不稳定，就不建立该名称。颜色、柔光、情绪或单一镜头 trait 不能单独包装成新 name。

### 3.2 `tags`：分层的短视觉指纹

tags 同时被 Planner 读取并被生成链原样置于 Prompt 前端，因此只能使用“既能帮助匹配、又能直接改变画面”的词。项目用途、音乐类型、受众说明等纯检索词不能放入 tags。

为支持大库中的粗筛和精排，tags 在同一个数组内按语义分层。无需增加后台字段，也不写 `medium:`、`mood:` 一类会污染 Prompt 的前缀。

| 顺序 | 层级 | 作用 | 示例 |
|---|---|---|---|
| 1 | 视觉形态 | 先区分真人影像、摄影、绘画、2D、3D、平面设计、建筑空间、混合媒介等大类 | `Live-Action Cinematography` |
| 2 | 风格家族 | 建立可被用户意图召回的常见审美方向 | `Poetic Naturalism` |
| 3–5 | 核心差异 | 写决定近邻边界的色光、空间、镜头、造型或动态规律 | `Natural Backlight`、`Wide-Angle Intimacy` |
| 末位（按需） | 质感或可视氛围 | 补充确实改变结果的表面质感或画面感受 | `Organic Film Texture` |

这是一种**位置约定**，不是要求每条机械凑满四层。通常 5–8 个简短词组已足够。优先使用模型和用户都容易理解的常见视觉词，再用少数真正特殊的词建立区分；不要为了显得专业，把每个 tag 写成复合长标题。

第 1–2 层应使用受控、稳定的常用词，同义含义统一一种写法，例如统一使用 `Live-Action Cinematography`，不同时出现 `Cinematic Photography`、`Cinematic Film`、`Film Still Style` 作为同一大类。视觉形态词表是可扩展的常用词表，不是封闭的媒介名单；维护时应参考实时官方库已有 tags，将稳定的媒介同义词归并到标准词，但不把流派、情绪、技法或具体风格名误升为首层形态。新形态经人工确认后统一命名并加入词表。这样 Planner 才能把项目意图映射成可用于 `--tag` 粗筛的确定词；第 3 层可以保留风格自身的特殊差异。

`dreamy`、`nostalgic`、`cinematic`、`emotional` 等常见词并非一律禁止，但它们只能作为末层补充，不能替代视觉形态、风格家族和核心差异。`Good for Sad Songs`、`Story MV` 等只说明用途，应进入 description。

#### Anchor 是否写进 tags

一般不把 `name` 原样复制为 tag，原因有三点：summary 已同时提供 name；完整名称不能增加新的路由维度；tags 会被原样注入生成 Prompt，重复会挤占高优先级位置。

只有以下情况才在 tags 中保留一次 Anchor 词：

- name 使用作品名，但常用人物、流派或别名对检索不可替代；
- 该 Anchor 词本身能稳定提高风格还原，且视觉描述词无法等价替代。

#### Planner 如何使用分层 tags

1. 用第 1–2 层按项目需要的视觉形态和风格家族建立候选池。
2. 用第 3 层以用户具体意图、项目内容和近邻差异排序。
3. 对 Top K 读取 description，确认适用场景和排除边界。
4. name 用于 Anchor 精确命中和用户展示，不参与替代视觉特征。

库较小时可一次读取 summary 后按上述顺序推理；库较大时，先把项目意图映射到第 1–2 层受控词，通过 `--tag` 或分页取得候选，再执行第 2–3 步。分层描述的是同一套匹配逻辑，不要求后台新增 taxonomy 字段。

### 3.3 `description`：项目匹配与选择理由

description 面向 Planner 和用户，回答：

1. 这套视觉身份是什么；
2. 它适合怎样的 MV、音乐情绪、叙事方式和用户意图；
3. 根据项目特点、内容和用户意图，为什么应当选它，而不是最容易混淆的相邻风格。

它不需要重复列出全部 tags，也不写可直接生成的长 Prompt。边界必须落到项目选择有意义的可见差异上，例如“元素性自然尺度”对比“当代室内亲密感”，而不是 `more unique`、`more cinematic`。

只有真实近邻会造成混淆时才点名比较；否则用正面的适用意图建立边界即可。

### 3.4 `analysis`：可迁移的完整视觉知识

analysis 是六字段中的事实源和 Agent 说明书。它从 evidence 中完整解释视觉规律如何形成、如何协同、怎样迁移到适用范围内的不同内容与输出，以及什么变化会使风格失真。

分析维度随媒介自适应：

- **真人影像**：成像与镜头、色彩与曝光、光源逻辑、构图与空间、材质与后期，以及有证据支持的镜头运动与时间组织。
- **摄影**：摄影过程、构图、色调、光线、光学与表面处理。
- **绘画与绘图**：笔触、线条、形体、颜料或纸面、色彩关系和画面空间。
- **2D 插画与动画**：线条、形变、色彩、平面层次、绘制质感，以及有证据支持的动画表现。
- **3D**：建模比例、形体简化、材质响应、灯光与渲染、空间和完成质感。
- **平面设计**：版式、图形、文字关系、色彩系统、印刷或数字表面。
- **建筑与空间**：体量、几何、材料、尺度、空间秩序以及光线对空间的作用。
- **混合媒介与后期技法**：图层关系、媒介边缘、图形元素、色光处理、合成逻辑和材质关系。

维度用于防止遗漏，不是固定标题模板。静态规律和动态规律都可以写：只要 evidence、连续影像、创作资料或聚类结论能够支持，并且它们会影响 VidMuse 的分镜或生成效果。规范不因当前某一素材只有静帧而限制未来更完整的资料。

### 3.5 `promptSample`：协调后的风格执行壳

promptSample 比 tags 完整、比 analysis 凝练。它追加在项目内容之后，负责说明这些离散视觉方向如何共同作用。

它应当：
- 从 Anchor 开始，依辨识度展开主要视觉控制；
- 把 tags 中相互独立的关键词组织成一套协调的画面方法；
- 只说明媒介、色光、空间、镜头、纹理和必要的动态气质；
- 与 analysis 保持一致，但不复制整段分析。
它不得包含具体主体、角色、演员、动作、剧情、地点、名场面、受保护道具，也不得包含模型名称、质量词、权重、画幅、分辨率、负向提示或生成命令。

一个简单判断是：把 promptSample 接到完全不同的项目内容后面，它仍应表达同一种风格，而不会强迫项目重演原作品。

### 3.6 `imageUrl`：风格的视觉证据

imageUrl 指向最终展示给用户的原创参考图。它不是素材出处，也不是从 evidence 中随手挑一张“最像”的截图。

合格参考图需要：

- 合格参考图应做到可以认出视觉语法，而不是只展示颜色滤镜。
- 使用原创、无明确身份的内容，不出现演员肖像、受保护角色、作品标题、名场面、标志性道具或可识别文字。
- 内容为主要色光、构图、空间和质感提供发挥空间，并与风格适用的项目类型一致。
- 图片本身应清晰、完整、无水印、黑边、文字污染和明显生成瑕疵。
- 用户看完预览后，应能合理预期这种风格应用到自己项目的大致结果。

内容依赖型风格允许保留必要母题。例如 Poolcore 如果去掉水体、瓷砖和人造水空间就不再成立，可以保留这些通用配置，但不能复刻具体作品或地点。

## 4. 从聚类候选到六字段

### 4.1 撰写顺序

撰写顺序不是后台字段顺序，而是从证据到压缩结果的推导顺序：

1. 确认候选边界：读取主 Anchor、代表 evidence、跨素材不变量、内容偏差和最近邻结论。候选尚未成立就停止。
2. 确定 name：把已验证的 Anchor 层级翻译成用户能理解、能选择的名称，不改变聚类结论。
3. 写 analysis：先完整记录 evidence 能支持的静态、动态和媒介规律，建立本条风格的事实源。
4. 压缩 tags：从 analysis 中抽取“形态 → 家族 → 核心差异 → 按需质感/氛围”，不引入 analysis 之外的新特征。
5. 写 description：结合聚类边界和 VidMuse 项目语境，补充适用意图、推荐理由和近邻差异；这些信息不反塞进 tags。
6. 编译 promptSample：从 analysis 中保留跨内容都应执行的控制，并把 tags 的离散方向组织成协调配方，不引入主体内容。
7. 做文本闭环检查：只看 name + tags 能否正确粗筛；再看 description 能否精排；analysis 与 promptSample 是否能分别完成扩写和执行。
8. 同题生成与近邻对照：使用双方适用范围内的相同可比内容，验证 tags、analysis、promptSample 是否产生稳定可分结果；范围受限的风格再在其范围内更换内容验证迁移性。
9. 批量生成参考图候选：通过统一的 Preview Prompt Compiler 自动产出候选图；审核、上传后才填写 imageUrl。

这一顺序的核心逻辑是：analysis 保存证据支持的完整知识，tags 和 promptSample 是两种不同用途的压缩，description 则来自项目匹配和边界。

### 4.2 AI 批量起草输入与约束

AI 输入至少包含：聚类结论、代表 evidence 或其客观摘要、最近邻边界、内容偏差、适用范围。不得只给 Anchor 名称，让 AI 根据常识自由补写。

AI 按 4.1 顺序在内部推导，最终只输出六个生产字段。人工审核依次检查：

1. name 是否对用户清楚且忠实于 Anchor 层级；
2. tags 是否能完成分层召回和近邻区分；
3. description 是否提供真实的项目选择理由；
4. analysis 是否完整、可迁移且没有内容偏差；
5. promptSample 是否纯净、协调并能稳定执行；
6. imageUrl 是否证明了文本承诺。

## 5. 参考图的批量生成规范

### 5.1 不逐条人工写 Prompt

参考图由独立的批处理生成，不在编辑某条风格时临时手写或临时生图。标准流程是：

```text
已审核的五个文本字段 + evidence 摘要 + 内容依赖判断
→ Preview Prompt Compiler 为每条风格批量生成 1 个原创内容 Prompt
【下方内容你暂时不用管，写好prompt即可】
→ 生图调用层补充模型参数并批量生成
→ 自动检查风格覆盖、近邻区分、来源复刻和图像质量
→ 人工抽查；未通过项重写 Prompt 或重新生成并替换
→ 每条风格保留 1 张正式图，上传后回填 imageUrl
```

Preview Prompt 不是第七个后台字段，只是可重建的流水线中间产物。模型参数、画幅、质量词和负向配置由生图调用层统一管理，不回写风格库。

### 5.2 原创内容模式

Compiler 根据媒介和适用范围自动选择内容，不要求所有风格使用同一个主体：

| 模式 | 适用 | 内容要求 |
|---|---|---|
| 人物与环境 | 真人摄影、叙事 MV、表演型风格 | 无明确身份的成年表演者，原创服装与空间，同时展示人物、光线和景深关系 |
| 空间与环境 | 建筑、Liminal、景观、环境型 visualizer | 原创空间，包含前中后景、主要材质和光源，不复刻具体地点 |
| 图形与物质 | 2D、3D、定格、拼贴、抽象技法 | 原创形体或对象组合，充分展示线条、材质、渲染和层次 |

内容依赖型风格保留成立所必需的通用母题；其他风格优先使用不抢夺风格注意力的中性内容。每条 Prompt 应选择最能展示该媒介最高优先级视觉规律的原创构图，不机械要求人物、环境、光线或镜头同时出现；若自动校检或人工抽查不通过，则重写并替换，而不是在最终交付中保留多张候选。

### 5.3 Preview Prompt Compiler 模板

下面模板可由批处理逐条填入，不需要人工为每个风格撰写图像 Prompt：

```text
You are the VidMuse Preview Prompt Compiler.

INPUT
Name: {{name}}
Ordered tags: {{tags}}
Description: {{description}}
Analysis: {{analysis}}
Prompt sample: {{promptSample}}
Evidence summary: {{evidence_summary}}
Nearest-style boundary: {{nearest_style_boundary}}
Content dependency: {{content_dependency}}
Excluded source content: {{characters_scenes_props_to_avoid}}

TASK
Create one English image prompt for the style's final original reference image.
1. Select the most suitable content mode: person-in-environment, environment, or graphic-material.
2. Use an original, non-branded subject and setting. Keep only motifs marked necessary by Content dependency.
3. Each prompt must visibly demonstrate at least three of the highest-priority style traits, including one lighting/color trait and one composition/form trait when applicable.
4. Choose content and composition that make the style identity legible without depending on one source-specific motif.
5. Use the ordered tags as high-priority style direction and the prompt sample as the coordinated rendering method. The style name may be retained once when it is the prompt sample's Anchor; do not add further repetitions.
6. Do not reproduce source characters, actors, costumes, locations, props, text, titles, or recognizable scenes.
7. Do not add traits that are absent from Analysis and Evidence summary.

OUTPUT
Return JSON with exactly two keys: `"name"` must repeat the input Name exactly, and `"prompt"` must be one plain English prompt string. Return no commentary.
```

每条生成结果按同一规则校检：是否覆盖核心 tags、是否符合 analysis、是否与 evidence 的视觉规律一致、是否与最近邻可分、是否存在来源复刻或画面瑕疵。自动校检不代替最终视觉抽查；不通过时应重写 Prompt 或重新生成并替换该图。

## 6. 完整试写：The Tree of Life Inspired

本例以第二阶段 `full-hyp-0146` 的 review 结论为主体，并使用同阶段已确认的 Malick 父风格规律。作品候选在自然、室内、身体、水与抽象光线中保持诗性自然主义；作品叶子的新增价值是元素性自然尺度、低地平线、身体近距和阈限空间，与 Song to Song 的当代亲密空间区分。

这是五个文本字段和参考图方案的内容试写。正式预览尚未批量生成、审核和上传，因此不伪造 imageUrl，也不包装成可导入 JSON。

### `name`

```text
The Tree of Life Inspired
```

作品名对用户可识别，且忠实于已验证的作品级 Anchor；没有把它包装成未经验证的“自然逆光风”。

### `tags`

```text
Live-Action Cinematography
Poetic Naturalism
Natural Backlight
Wide-Angle Intimacy
Low-Horizon Landscapes
Elemental Scale
Organic Film Texture
```

前两项用于形态和风格家族粗筛，后四项建立作品叶子的生成特征与近邻边界，末项补充完成质感。词组保持常见、短且可执行；name 已在 summary 中提供，因此不在 tags 重复。

### `description`

```text
The Tree of Life Inspired turns intimate human memory and elemental nature into luminous poetic naturalism through natural backlight, close wide-angle perspective, low horizons, and layered thresholds. It suits reflective narrative MVs, spiritual or memory-led tracks, and projects that need private emotion to open into a larger natural scale; compared with Song to Song's contemporary interior intimacy, it is more elemental, expansive, and contemplative.
```

### `analysis`

```text
**Image Formation & Lens Language:** Live-action poetic naturalism built through wide-angle lenses used close to bodies, preserving immediate physical presence while allowing the surrounding world to remain active. The image feels discovered from within the moment rather than staged from a detached distance.

**Color, Exposure & Light:** Natural daylight is the main visual engine. Backlight, rimmed highlights, dappled exposure, gentle flare, and luminous transitions between interior shadow and exterior brightness create a living atmosphere. Color remains organic and restrained, with warm sunlit highlights, cooler open shadows, and no glossy commercial grading.

**Composition & Spatial Scale:** Low horizons, layered thresholds, open sky, reflective water, and shifts between bodily proximity and expansive landscape connect private experience to elemental scale. Figures may become small inside the environment, but the composition retains intimacy rather than turning into remote spectacle.

**Texture & Material Presence:** Skin, fabric, grass, water, wood, dust, and air retain tactile irregularity. The finish is filmic and organic without relying on heavy vintage damage, decorative grain, or a fixed period look.

**Camera & Temporal Language:** The camera may drift, arc, follow, or change height responsively with bodies, wind, light, and space. The temporal feeling is exploratory and lyrical rather than mechanically stabilized, aggressively handheld, or driven by flashy rhythmic effects.

**Atmosphere & Boundary:** The result is intimate, elemental, contemplative, and quietly transcendent. It must not collapse into generic pastoral imagery, inspirational lifestyle photography, or the contemporary glass-and-interior romantic restlessness associated with Song to Song.
```

### `promptSample`

```text
The Tree of Life-inspired elemental poetic naturalism, luminous natural backlight with gentle flare, intimate wide-angle perspective, low horizons opening into elemental landscape scale, layered thresholds and deep spatial continuity, tactile organic film texture, contemplative fluid visual rhythm
```

### `imageUrl` 批量生成方案

本例进入统一 Preview Prompt Compiler 后，选择“人物与环境”模式。最终 Prompt 应使用无明确身份的成年表演者与原创空间，同时证明自然逆光、宽角近距、阈限深度和低地平线尺度，但不复制亲子关系、年代服装、住宅陈设或原片构图。

批处理生成、近邻对照和人工审核完成后，才上传正式图片并填写真实 imageUrl。

## 7. 两个边界短例

### 7.1 作品叶子与人物父风格

三者不能只写成同一组 `Natural Light / Wide Angle / Poetic`：

| 候选 | 应保留的区别 |
|---|---|
| `The Tree of Life Inspired` | 元素性自然尺度、低地平线、阈限深度、亲密经验向宏大景观展开 |
| `Song to Song Inspired` | 当代亲密关系、通透窗光、超广角身体近距、流动不对称和室内玻璃层次 |
| `Terrence Malick Inspired` | 跨作品成立的父语法：自然逆光、广角身体距离、阈限、水、风与抒情运动 |

如果中性同题生成无法让作品叶子与父风格稳定区分，作品叶子不应仅凭名称入库。

### 7.2 内容依赖型：Poolcore

Poolcore 的水体、瓷砖网格、人造水空间和湿润反射是风格本体，不是应被清除的偶然场景。按 tags 分层可写为：

```text
3D Environment
Liminal Space
Aquatic Architecture
Ceramic Tile Grid
Blue Water Reflections
Sterile Lighting
Uncanny Emptiness
```

把它清洗成 `Blue 3D Render` 会失去风格身份和 Planner 的匹配能力。description 应明确它适合空间型 visualizer、环境和超现实概念，而不是把它描述成能无条件迁移到任何人物或产品的通用风格。

## 8. 入库前最终判断

- name 对用户是否清楚、可选择，并准确代表已验证的 Anchor 层级？
- Planner 只看 name + tags，能否召回正确的大类？再看完整 tags，能否与最近邻区分？
- tags 是否简短、具备区分度、按层排序，并且每项都能原样进入 Prompt？
- description 是否解释项目为何匹配、用户为何选择，而不是重复生成词？
- analysis 是否覆盖 evidence 支持的完整视觉特征，并能指导风格在适用范围内迁移？
- promptSample 是否只组织视觉执行方法，按执行需要决定是否重复 name，且不引入主体和模型配置？
- 参考图是否让用户看到风格规律，而不是只认出出处、角色或名场面？
- 在双方适用范围内的相同可比内容下，它与近邻是否产生稳定、可感知且对项目选择有意义的差异？

其中任何一项只能依靠“Anchor 很有名”或“画面很好看”回答，都还没有达到入库标准。

## 9. 本轮核对依据

- 后台快照共有 78 条可解析风格记录；tags 以 3–5 项最常见，完整 name 原样出现在 tags 的记录为 35 条。现有库说明短标签更符合产品阅读习惯，但其顺序和质量并不统一，因此本规范保留短词体验并补充分层顺序。
- 默认插件 `select-visual-style` 明确 summary 返回 `name + tags + imageUrl`，full 返回六字段，并规定 tags 原样注入、analysis 用于扩写、promptSample 作为 Style Shell。
- `vidmuse-cli` 风格命令 已支持单 tag、多 tag 过滤和 offset 分页；默认 selector 尚未利用这些能力进行分层检索。
- `T2I`、`T2V` 和 `I2I` 编译规则 证明 tags 与 promptSample 位于不同注入位置，analysis 承担扩写而非整段照抄。
- 后台快照 官方风格库管理后台快照 用于核对当前 name、description、tags 和预览图的实际展示形态。
