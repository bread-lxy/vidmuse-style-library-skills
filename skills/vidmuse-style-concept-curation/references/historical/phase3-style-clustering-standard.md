# Historical Phase 3 Technical Standard

This file is retained only to reproduce the earlier Phase 3 experiment. Its numeric thresholds, ProductProfile fields, Q1/Q2/Q3 structures, and static-only policy are not active Skill requirements. D-024 and `../style-clustering-rules.zh-CN.md` govern current concept creation.

> **Bundled-use note:** This file is a technical ontology and evidence reference for concept curation. For official candidate creation, `style-clustering-rules.zh-CN.md` and D-024 take precedence. For the six production fields and preview policy, the record-production skill's current human field standard takes precedence over this file's older ProductProfile projection or numeric preview guidance.
# VidMuse 视觉风格聚类与产品入库规范

Version: 1.1  
Status: Gate 3 final candidate  
Date: 2026-07-14  
Applies to: 素材采集、AI 聚类、边界审核、命名、Planner 检索、生成配方、入库与存量治理

## 1. 目的与边界

本规范回答四个不同问题，并禁止把它们混成一个判断：

1. **什么是风格**：由 `StyleConcept` 的可观察视觉规律决定；
2. **如何证明风格**：由 `AnchorSet` 的正样本、反例与来源证明；
3. **产品如何使用风格**：由 `ProductProfile` 的名称、检索、生成和能力状态决定；
4. **AI 如何发现候选**：由证据单位、特征隔离和验证协议决定，不绑定某一种聚类算法。

本规范不规定具体 embedding、聚类算法、Planner 实现或生成模型。它规定这些实现必须接收和产出的语义契约，以及候选何时可以进入官方风格库。

配套文件：

- 工作模板：[style-concept-template.yaml](./style-concept-template.yaml)
- 机器结构约束：[style-concept.schema.json](./style-concept.schema.json)
- V1 候选目录：[style-anchor-catalog.md](./style-anchor-catalog.md)
- 边界与回归案例：[boundary-cases.md](../evaluation/boundary-cases.md)
- 决策记录：[decision-log.md](../decisions/decision-log.md)
- 反方审查：[adversarial-review.md](../evaluation/adversarial-review.md)

## 2. 规范用语

- `MUST / 必须`：对应 gate 的硬条件；
- `MUST NOT / 禁止`：违反即失败；
- `SHOULD / 应`：默认要求，例外必须写入 reviewer notes；
- `MAY / 可`：可选。

V1 中的数量阈值是统一的**试运行阈值**。团队可在积累真实评测数据后通过 decision log 整体调整，但禁止为单条候选临时放宽。

## 3. 操作性定义

> **VidMuse StyleConcept 是一组在声明适用范围内稳定共现、在隐藏来源名称和来源特有内容后仍可与最近邻区分的静态视觉形式规律。**

最小身份为：

```text
StyleConcept = Signature + Scope + Boundary
```

- `Signature`：哪些可观察形式规律稳定共现；
- `Scope`：该判断在哪些表现媒介和内容条件下成立；
- `Boundary`：最近邻是谁，如何正向区分，何时应合并。

概念成立与产品可用必须分开：

```text
Concept validity = Stability(Q1) + Separability(Q2)
Product readiness = Concept validity + Product value(Q3) + Current capability
```

一个真实风格可以因为 Planner 尚不能过滤、生成模型尚不能稳定表达、名称难以理解或预览不足而停留在 `concept_validated`；这不否认风格存在，也不允许它提前进入 Active。

## 4. V1 三块模型

### 4.1 StyleConcept

```yaml
styleConcept:
  signature: {}
  scope: {}
  boundary: {}
  parentStyleId: null
  relatedStyleIds: []
```

它只负责风格身份及轻量关系。V1 允许一个可选主父级、多个 related styles，不实施多父图推理。

### 4.2 AnchorSet

```yaml
anchorSet:
  positiveReferences: []
  negativeReferences: []
  provenance: {}
```

**Anchor 的唯一含义**：用于支持和识别某个风格的具体参考样本或参考来源。Anchor 是证据，不是类别定义。导演、作品、艺术家、流派、工作室和时期都是来源信息；只有完成 Q1/Q2 后，它们才可能成为显示名称或别名。

### 4.3 ProductProfile

```yaml
productProfile:
  displayName: "
  aliases: []
  plannerFacets: {}
  retrievalTags: []
  generationTags: []
  capabilityMatrix: {}
  validation: {}
```

它负责用户呈现、Planner 排序、生成控制、预览和生命周期。产品实现变化可以改变 ProductProfile，但不能反向改写已经验证的 StyleConcept 边界。

## 5. 什么默认不是风格

| 对象 | 默认角色 | 典型错误 |
|---|---|---|
| 导演、艺术家、工作室 | provenance / naming candidate | 把一个人的全部时期强行聚成一类 |
| 电影、动画、游戏、IP | evidence corpus / naming candidate | 学到角色、服装、世界观而非形式规律 |
| 流派、时期、亚文化词 | research hypothesis / alias | 因词语知名就假定视觉上单一 |
| 情绪、音乐类型、用途 | Planner ranking facet | 把 romantic、healing、cinematic 当视觉机制 |
| 人物、地点、道具、场景 | content signal | 把 desert、school rooftop、pool 当通用风格 |
| 单项 trait | Signature component | soft light、symmetry、blue、film grain 单独成库 |
| 相机、软件、分辨率 | provenance / technical facet | ARRI、Blender、HD 自动等于风格 |
| 单张截图或连续相邻帧 | evidence item | 以异常镜头代表整部作品 |

媒介技法或环境依赖型类别可以成为 StyleConcept，但必须形成多特征配置，并在 Scope 中诚实声明依赖。

## 6. Signature：AI 和人实际判断的对象

Signature 描述可观察形式规律，不描述来源名。

### 6.1 字段

Signature 包含：

- `summary`：不使用来源专名的一句话视觉身份；
- `transferableInvariants`：3-6 条共同形成身份的高信号规律；每条包含稳定 `id`、受控静态 `dimension`、正向 `rule` 和 `evidenceIds`；
- `realizationsByMedium`：跨媒介时，各媒介如何实现同一规律；
- `allowedVariation`：哪些差异仍属于本风格；
- `excludedSourceMotifs`：不得用于判断成员关系的角色、地点、道具、Logo 或名场面。

每条 invariant 必须能够直接从静帧、照片、作品或多视图集合中观察，并引用至少一个实际支持它的正样本。作者、作品、设备、日期、专业文献、生成测试和产品日志可用于来源核验、术语核验或产品价值，但不能进入视觉聚类向量，也不能替代静态可观察证据。

### 6.2 静态维度

按媒介选取相关维度，不要求机械填满。机器记录使用以下受控值：`color_tonality`、`lighting_shadow`、`composition_spatial`、`form_shape`、`material_texture`、`rendering_markmaking`、`optical_image_character`、`graphic_layering_typography`、`depth_scale`。

### 6.3 当前证据边界

V1 素材只有静态图像，因此只定义静态视觉外观。摄影机运动、镜头时长、剪辑、动画 timing、声画同步和其他依赖顺序的规律不进入 Signature、不参与聚类，也不能据此拆分风格。

静帧中可见的 motion blur、scanline、压缩拖影等可以作为**静态纹理结果**描述，但不得上升为对运动或剪辑机制的判断。仅凭非静态证据才能成立的候选写入通用拒绝记录：`status=out_of_scope`、`exclusionReason=requires_non_static_evidence`；不进入 StyleConcept 候选池，也不为其预留身份字段。

### 6.4 跨媒介

`realizationMedia` 出现两个及以上值不自动证明跨媒介。必须：

1. 指出至少三条跨媒介不变量；
2. 在 `realizationsByMedium` 分别记录实现方式；
3. `Scope.realizationMedia`、`realizationsByMedium` 和 Q1 `mediaCoverage` 的媒介键完全一致；
4. 每种媒介各自满足最低证据量并拥有独立 holdout。

只有题材或来源名称相同，不构成跨媒介风格。

## 7. Scope：正交而简洁

```yaml
scope:
  realizationMedia: [live_action]
  contentDomains:
    mode: none
    operator: any
    values: []
```

### 7.1 Realization media

它表示 StyleConcept 已被证明成立的**视觉实现媒介**，不是题材，也不是用户当前要生成 image 还是 video。

V1 受控值：

- `live_action`
- `photography`
- `animation_2d`
- `animation_3d`
- `illustration`
- `painting`
- `printmaking`
- `graphic_design`
- `mixed_media`
- `realtime_3d`

`architecture` 属于内容/设计领域，不是表现媒介；`cross_media` 是多个媒介通过验证后的派生事实，不作为枚举值；VHS、Risograph、datamosh 等是 Signature 中的媒介/技法机制，不再与媒介轴混写。

### 7.2 Content domains

它记录风格是否依赖可检测的内容类别：

- `none`：在声明媒介内不依赖指定内容；
- `preferred`：可迁移，但在指定内容上更强；
- `required`：去除该内容类别即不再是此概念。

`operator` 为 `any` 或 `all`。`values` 必须来自内容词表，V1 初始值为：

`people`、`performance`、`dance`、`built_environment`、`interior`、`landscape`、`product`、`typography`、`abstract_graphics`、`aquatic_space`。

新值必须先进入词表，不允许在生产记录中临时写自由文本。`required` 且 Planner 无法确认内容时，默认不进入主推荐；`preferred` 且内容未知时保持中性，已知匹配时才加权。

Q2 的“去内容”只移除来源特有角色、IP 道具和名场面；合法的 required content class 必须保留。例如 Poolcore 的 `aquatic_space` 可以保留，但某一部作品独有的泳池布局不能保留。

### 7.3 Scope 与产品能力分离

Scope 说明静态视觉概念在哪成立；`ProductProfile.capabilityMatrix` 只记录 `imageGeneration`、`storyboardFrameGeneration` 和 `videoFrameAppearance` 三种产品输出中的静态外观可用性。Planner 的硬过滤依据 Scope 与能力共同决定。输出用途不能反向扩张研究证据。

## 8. Boundary：怎样证明“这是另一种风格”

Boundary 包含：

- `nearestNeighbors`：最可能混淆的 1-5 个 StyleConcept；
- 每个邻居对应的 `distinguishingRules`；
- `mergeWhen`：何时只是别名、单项 trait 或不稳定变体。

区分规则必须是正向可观察差异，不能只写 `not X`。同一 Anchor 的不同时期、作品或媒介不自动 split；不同 Anchor 也不自动 split。

### 8.1 Q1 Stability

问题：差异是否在声明 Scope 内重复出现，而非只存在于一个人物、地点、IP、场景或样本？

#### 最低证据协议

| 声明范围 | 静态最低量 | 独立性要求 |
|---|---:|---|
| 单一作品/项目 | 12 个独立静态单元 | 至少 3 个场景/章节/内容上下文；单一场景不超过 40% |
| 人物/工作室/时期/艺术运动 | 18 个独立静态单元 | 至少 3 部作品/项目；单一作品不超过 50% |
| 技法/社区审美/内容依赖风格 | 18 个独立静态单元 | 至少 3 类内容上下文、2 个独立来源；单一上下文不超过 50% |
| 跨媒介 | 每种媒介至少 6 个静态单元 | 总量仍需达到上方对应范围；每种媒介均有 holdout |

#### 执行规则

1. 以最高层独立键拆分 75% development / 25% holdout，禁止把同一镜头相邻帧分到两侧；
2. 隐藏来源名称、查询标签和候选名称；
3. 两位审核者独立判断每条 invariant 是否出现；
4. 核心 invariant 在适用 holdout 中的支持率必须 `>=75%`；
5. 至少三条核心 invariant 同时通过，且审核者原始一致率 `>=80%`；
6. 未达到阈值时必须 narrow、merge 或 hold，不得用名称知名度补足。

机器记录必须填写 `basisType`、实际静态单位数、独立来源数、独立上下文数、最大来源/上下文集中度、每媒介 evidence/holdout ID、每条 invariant 支持率、审核人数和一致率。脚本以 evidence 的 `independenceKey/contextKey/sourceGroupKey` 重算这些值；手填数字不一致即失败。近重复算法与阈值必须记录在 review record 中；“已经去重”不是可接受的空泛结论。

### 8.2 Q2 Separability

问题：隐藏显示名称、来源 metadata 和来源特有 motif 后，是否仍能与最近邻稳定区分？

#### 邻居生成

1. 从 source-hidden style vector 的 Top-5 近邻中选最难的两个；
2. 人工可以补充一个 Active 易混淆项，但不能删除更难邻居来提高分数；
3. 每个邻居必须有逐项 `distinguishingRules`；
4. reciprocal nearest neighbors 必须共享一个 joint boundary test，两个新候选在该测试完成前不能同时 Active。

#### 盲测

- 每个邻居至少 12 组内容匹配的 pair/triplet；
- 两位审核者在不见名称和来源的情况下按 source-free Signature 分类；
- 每个邻居的正确识别至少 `9/12`；
- 审核者原始一致率至少 `80%`；
- 机器距离通过而人审失败时，以 `hold` 为默认，记录争议；
- required content class 保留，来源特有 motif 移除。

机器记录中的 `topKNeighborIds` 按相似度从难到易固定为 5 项，`testedNeighborIds` 必须恰好等于前两项；同时记录 `blindProtocolId`、`fixedInputSetId`、每邻居正确数、审核人数和一致率。不得人工重排后再提交。

若差异只剩一项可交换 trait，或两个 prompt/output 在产品上可互换，则 merge 或 parent_child，不做并列叶子。

### 8.3 Q3 Product value

问题：拆分后是否改变至少一个真实产品动作，并在选择或输出上产生可测差异？不要求 Planner 与生成两项都提升，但一次随机出图不同不算通过。

候选在测试前必须声明一个主要动作和合并基线：

| 动作 | 最低测试 | V1 通过阈值 |
|---|---|---|
| Planner 检索/排序 | 至少 20 条分层 brief；比较 split 与 merge baseline | 正确风格 Top-3 命中率提升 `>=10` 个百分点，且最近邻无超过 5 个百分点的回退 |
| 图像或视频帧的生成外观 | 至少 20 组成对输出；固定内容、模型、参数和 seed；盲评 | 至少 3 位评审多数票下，正确风格匹配/偏好率 `>=70%` |
| 用户选择 | 足够覆盖两类意图的在线/可用性测试 | 预先声明指标、基线和最小效应；不得事后挑指标 |

Q3 失败不否认 StyleConcept；它进入 `concept_validated` 或作为 parent/related/alias 管理，不进入 Active leaf。

所有 Q3 记录都必须保存 `mergeBaselineId`、`fixedInputSetId`、样本量、指标、基线值、候选值、效应值和预声明阈值。Planner 动作额外记录最近邻回退；生成外观额外记录盲评人数。名称测试单独要求至少 5 人、至少 4 人正确匹配目标预览。

### 8.4 五种结论

| Outcome | 条件 | 后续动作 |
|---|---|---|
| `merge` | 核心 Signature 和产品行为可互换 | 一个概念；其他名称作为 alias |
| `split` | Q1/Q2 通过，且 Q3 证明独立产品动作 | 独立 ProductStyle |
| `parent_child` | 共享核心，窄子类稳定且有产品价值 | 一个主父级；子类通过 Q3 后才展示 |
| `related` | 关联强但不包含，且边界已证实 | 对称 related 关系 |
| `hold` | 证据、边界、名称、能力或评测不足 | 不进入 Active；保留原因和下一证据需求 |

AI 无法分配的噪声和混合样本允许 unassigned，禁止为了覆盖率强塞。

## 9. AnchorSet 与证据单位

### 9.1 通用证据记录

每个正/负样本必须记录：

- `evidenceId`；
- `unitType`、`medium` 与 `independenceKey`；
- `contextKey` 与 `sourceGroupKey`，用于重算独立性和集中度；
- `source`、稳定链接或本地证据 ID；
- 支持或反驳的 invariant IDs；
- creator/work/project/year 等 provenance；
- `licenseStatus`；
- 是否只用于 research。

一个文件、一个裁切、一个 query hit 不等于一个独立观察。

### 9.2 V1 证据单位

| Unit type | 原子单位 | Independence key | 去重规则 |
|---|---|---|---|
| `film_shot` | 一个镜头的代表帧 | `work_id + shot_id` | 同镜头相邻帧、不同 query 返回均为一个单位 |
| `photograph` | 一张原始摄影作品 | 原作/底片/发布作品 ID | 转码、裁切、转载不新增单位 |
| `artwork` | 一件绘画、版画、插画或设计作品 | work/page/asset ID | 局部裁切不新增单位；系列按独立作品计 |
| `architecture_view_set` | 一个建筑/室内项目的多视图集合 | project/building ID | 同一项目所有角度合计一个单位，避免 20 个角度伪装 20 个项目 |
| `game_capture` | 一个版本和模式下的独立静态场景捕获 | title + build + mode + scene ID | 同一捕获段的相邻帧合并 |

所有单位都提供静态视觉表示。建筑的空间组织若依赖多视角，必须以 view set 评估，不能由一张立面图推断；但 view set 仍不提供镜头运动或时间关系。

### 9.3 正样本与反例

- 正样本必须覆盖声明 Scope，并标明支持哪条 invariant；
- `concept_validated` 前至少有一个 hard-negative set；
- 负例必须来自真实最近邻，不能选择明显无关风格；
- 研究截图与生产预览必须分离；ShotDeck 和影视截图默认为 `research_only`；
- 人物/作品/工作室级名称必须额外检查来源责任和范围，不得仅凭 credit 建立风格。

## 10. AI 聚类协议

### 10.1 聚类的对象

AI 聚类的是**去重后的证据单位及其可观察 style features**，不是导演、作品、文件夹、标签或候选名称。

V1 只接收静态视觉表示。任何无法由当前静态证据成立的候选在 ingest 阶段写入通用 `out_of_scope` 拒绝记录，reason 为 `requires_non_static_evidence`，不进入本轮聚类或 ProductStyle 候选池。

### 10.2 三通道隔离

1. **Style channel**：色彩、明度、光线、构图、镜头感、线/形/材质和静态纹理；
2. **Content channel**：人脸、人物、物体、场景、地点、文字、角色、语义题材；
3. **Provenance channel**：作者、作品、工作室、年份、query、genre、设备、网站。

只有 Style channel 进入初始相似度。Content 用于泄漏检测、样本平衡和 matched comparison；Provenance 在发现阶段隐藏，解释阶段才恢复。

### 10.3 禁止作为初始 membership 特征

- 导演、艺术家、作品、IP、工作室、时期名称；
- ShotDeck query、seed dimension、文件夹名；
- 现有 `name/tags/description/promptSample`；
- genre、mood、usage、actor、character、location；
- QA 状态或旧人工分类；
- 不能从该证据通道观察的作者论、历史影响、低成本制作等判断。

人工标签可作为待核验 measurement，不是 ground truth。矛盾标签不得按频率拼成 prompt。

### 10.4 Source-hidden discovery

1. 证据先获得匿名 ID；
2. AI 产出 anonymous `hypothesis_id`、prototype、boundary items、outliers、feature summary 和 uncertainty；
3. 完成初始聚类和 holdout 后才恢复 provenance；
4. V1 catalog 中的名人、作品和流派条目只用于覆盖采样、解释和命名候选，禁止作为预设 bins；
5. 聚类结果可以不对应任何 seed，也可使多个 seed 合并为一个概念。

为防止知名人物和作品主导候选池，每个新采样批次还必须满足覆盖配额：预设专名 query 产生的候选不超过 50%；至少 30% 候选来自不使用专名的 source-hidden feature discovery；至少 20% evidence group 来自当前官方名称未覆盖的长尾来源。配额只控制发现覆盖，不给任何候选增加 Q1/Q2 分数。

### 10.5 诊断与评测

silhouette、stability under resampling、cluster size 和 embedding distance 只用于诊断。它们不能替代 Q1 holdout、Q2 hard-neighbor 盲测或 Q3 产品评测。

每次批处理必须输出：

- 去重前后数量；
- 各 work/project/content context 的集中度；
- unassigned 比例；
- Top-5 邻居；
- 对随机种子/重采样的稳定度；
- 无法由当前证据判断的字段。

## 11. 命名规范

### 11.1 命名在概念之后

先用 source-free Signature 完成 Q1/Q2，再选择名字。显示名称不参与 membership 学习。

### 11.2 与当前 79 条保持一致的形式

| 可用的识别依据 | V1 形式 | 示例 |
|---|---|---|
| 经验证且认知明确的人物/创作集体 | `X Inspired` | `Shunji Iwai Inspired` |
| 经验证且认知明确的作品/IP | `X Inspired` | `Blade Runner 2049 Inspired` |
| 已建立的艺术运动/互联网审美 | 既有简短术语 | `Fauvism`, `Dreamcore` |
| 已建立的媒介/技法 | 技法名或短限定名 | `Claymation`, `Risograph Print` |
| 来源范围过宽 | `X + scope qualifier` | `UPA Modernist Animation` |

### 11.3 名称 gate

名称必须：

- 让用户形成的主要视觉预期与 Signature 相符；
- 在 Active 内唯一；
- 不用单一时期代表整段职业生涯、整个工作室、文化或世纪；
- 不使用 generic mood/quality 伪装视觉类别；
- 在无限定会误导时增加短 scope qualifier；
- 将翻译、拼写、旧名放 aliases，不复制 StyleConcept。

知名度只提高 recognition，不提高 Q1/Q2 分数。名称预期测试采用目标预览与两个 hard-neighbor 预览：至少 5 名与审核无关的目标用户/内部使用者盲选，至少 4/5 将名称匹配到目标预览；否则 rename 或 hold。

### 11.4 存量名称

79 个后台名称在 seed catalog 中保留以确保迁移可追溯，但不自动获得概念有效性。名称与当前预览、来源或 Signature 冲突的条目标为 `existing_review` 和 `legacy_active_review`，先保留 alias，再进行 rename/merge/retire 回归。

## 12. Planner 信息与生成信息

### 12.1 Planner facets 与 retrieval tags

`plannerFacets` 是结构化排序信息，不定义风格身份：

- usage type；
- audio emotion；
- 有限的 semantic motifs。

`retrievalTags` 可含显示名变体、用户常搜来源、正式审美术语、媒介、用途和情绪。它们只用于 recall/ranking，不进入视觉聚类，也不直接进入生成 prompt。当前静态资料不能证明的剪辑或运动词不得作为检索标签补写。

### 12.2 Generation tags

`generationTags` 只包含短而可执行的风格控制：

- 经测试有用的 anchor phrase；
- 媒介、渲染和纹理；
- 高信号色彩、光线、构图、材质或静态纹理规则；
- 具有具体视觉结果的氛围词。

禁止 workflow 状态、来源站点、证据路径、license、usage、plot、角色、场景复刻、相机清单、矛盾 trait。专名不是必填项；只有通过生成测试且风险可接受时才进入 generation tags。

每个 tag 必须是单一原子短语，禁止在一个元素里使用逗号、`/`、`·`、全角分隔符、完整句子或内部备注。

### 12.3 当前插件事实与目标契约

当前默认插件的 summary 只有 `id/name/tags/imageUrl`，确认后才取得 full fields；`tags` 又会被原样复制进 prompt。现状因此**无法**同时实现 Scope 硬过滤和检索/生成标签分离。

目标契约必须做到：

1. admin 持久化 `scopeProjection` 与 `capabilityMatrix`；
2. summary 在候选展示前返回 `retrievalTags + scopeProjection + capabilityMatrix`；
3. Planner 在排序前执行 media/action/content hard filters；
4. DSL 保存完整 Scope、Signature 摘要和 `generationTags`；
5. prompt compiler 只读取 `generationTags`，不读取 retrieval tags。

本项目只规定设计，不在本阶段修改 plugin/planner。但上线门槛必须通过 `ProductProfile.activationReadiness` 被机器记录：

```yaml
activationReadiness:
  targetContractVersion: vidmuse-static-style-v1
  scopeInSummary: false
  plannerScopeFilter: false
  scopeInDSL: false
  generationTagsOnlyProjection: false
  compilerContractVersion: null
  promptSmokeTest:
    status: not_run
  customStyleCreatePolicy: ephemeral_custom_only
```

`active` 必须要求四个布尔值为 true、compiler contract version 非空，并通过完整 prompt smoke test。测试必须证明 generation tags 位于 prompt 开头，retrieval tags、来源 metadata 和非静态声明均未进入 prompt。当前插件未实现这些条件，因此现有 79 条只能记录为 `legacy_active_review`，新记录只能停留在非 Active 状态。

- 在上述目标契约实现前，任何新风格均**不得 Active**；其中 `required` content style 还必须完成 content swap 与 Planner filter 测试；
- legacy admin `tags` 临时只投影审核后的 `generationTags`，不再使用“检索与生成的安全交集”假设；
- 情绪、用途、alias 和未经验证的专名不投影到 legacy `tags`；
- 每条 legacy `tags` 必须通过原样注入的完整 prompt smoke test；
- 若当前 create/select 规则强制写入未经生成验证的专名，或移除 retrieval-only tags 后 Planner recall 低于 Q3 阈值，该风格必须 `hold`，不能绕过字段分离；
- 把 Scope 写进 description 不能替代 Planner 过滤。
- Create 路径即时生成的风格一律标记 `ephemeral_custom`；未经完整 Q1-Q3 与 activation gate，不得自动晋升为官方库记录。

### 12.4 当前六字段投影

```yaml
name: string
tags: [prompt-safe generation tag]
description: string
analysis: string
promptSample: string
imageUrl: string
```

| Admin field | 来源 |
|---|---|
| `name` | `displayName` |
| `tags` | 过渡期 `generationTags` |
| `description` | 用户适配 + Signature/Scope 摘要 |
| `analysis` | 按媒介展开可执行视觉机制 |
| `promptSample` | 无主体、剧情和来源 metadata 的 Style Shell |
| `imageUrl` | 自有、授权或生成的 16:9 代表图 |

## 13. 验证、生命周期与 Active 容量

### 13.1 三层 gate

**Concept gate**：Q1 + Q2 通过。  
**Product gate**：Q3 + 当前动作 execution + preview/name consistency 通过。  
**Activation gate**：目标字段在 Planner/DSL/compiler 链路可见并通过回归，且未超过可见容量。

条件测试：

| Trigger | 必须测试 |
|---|---|
| 名称含人物/作品/IP/工作室/运动 | name expectation + source scope review |
| 两个以上 realization media | 每媒介 Q1 + cross-media holdout |
| content mode preferred/required | content swap + Planner filter |
| 与 Active 高相似 | matched hard-negative side-by-side |
| 生产预览 | rights、可访问性、16:9、裁切、无水印、代表性 |

### 13.2 生命周期

```text
candidate -> concept_validated -> product_validated -> active
        \-> hold
active -> retired
```

存量迁移另有事实状态 `legacy_active_review`：当前线上可见，但未通过本规范，不得作为 AI ground truth 或新条目的质量基线。

JSON Schema 和验证脚本必须阻止：

- `active` 但 Q1/Q2/Q3 为未运行或失败；
- `active` 但 Scope/Planner/DSL/compiler contract 或完整 prompt smoke test 未通过；
- 任何身份、边界、检索或生成字段依赖静态素材无法证明的作者、运动、剪辑或历史条件；
- invariant 引用不存在的 evidence ID；
- Scope、`realizationsByMedium` 和每媒介 evidence/holdout 覆盖不一致；
- nearest neighbor 没有对应区分规则；
- required content 使用自由文本；
- legacy tag 含复合分隔符或 prompt 污染。

人工起草可使用 YAML 模板；进入 gate 的记录必须序列化为 JSON。`evaluation/validate-style-record.ps1` 会先执行 Draft 2020-12 Schema，再执行跨字段 lint；二者不是两条可任选的检查。配套 valid fixture、Schema 负例、阈值绕过负例和可执行 R01-R12 boundary runner 用于防止校验器本身失效。

### 13.3 规模治理

- Evidence 与 candidate 数量不设产品上限；
- StyleConcept 数量由 Q1/Q2 决定；
- Active ProductStyle 数量由 Q3、能力、可维护性和检索容量共同决定。

当前后台有 79 个可见样式，默认插件一次读取 official summary 的上限为 100，因此在当前实现下只有 21 个额外可见位置。但这 79 条尚未通过新运行契约，目录统一记录为 `legacy_active_review + blocked_runtime_contract`，V1 `current_active` 数为 0。任何新增都必须先关闭运行契约 blocker，再检查 `backend visible count == summary visible count`。在可见条目超过 100 前必须先实现 indexed Top-K、分页或等价检索；不能让高质量风格存在但 Planner 永远看不到。

## 14. 端到端流程

1. 按覆盖计划采集素材，保留 provenance 和许可状态；
2. 转换为适合媒介的证据单位，记录 medium、independence/context/source-group keys；
3. 去重并隔离 style/content/provenance channels；
4. 隐藏来源，以 anonymous hypothesis ID 发现候选；
5. 恢复 provenance，只用于解释、证据补齐和命名候选；
6. 建立平衡正样本、Top-5 近邻和 hard negatives；
7. 无专名地起草 Signature、Scope、Boundary；
8. 按固定协议运行 Q1/Q2，记录 merge/split/parent_child/related/hold；
9. 建立 StyleConcept 与 AnchorSet；
10. 选择与 79 条风格库形式一致、但范围准确的名称和 aliases；
11. 分开建立 planner facets、retrieval tags、generation tags；
12. 运行 Q3、capability、名称预览、运行契约和完整 prompt smoke test；
13. 映射到当前六字段；任何 activation blocker 都不得借 description 或 legacy tags 绕过；
14. 小批量上线，验证 summary、full DSL、prompt compilation 和同题输出；
15. 监控 Top-K confusion、使用率、放弃率和生成可互换性，必要时 merge/narrow/hold/retire。

## 15. 最小审核记录

每次概念决策必须保存：

- candidate/hypothesis ID、审核人、日期和规范版本；
- source-free Signature 与 invariant evidence links；
- Scope 和每个媒介的证据覆盖；
- 去重方法、阈值、独立来源数、source concentration 和 holdout；
- Top-5 近邻、最终 hard neighbors 和逐邻居区分规则；
- Q1/Q2 样本量、分数、一致率和结论；
- Q3 动作、merge baseline、固定输入/seed、样本量、指标和效应；
- 最终 outcome、理由、limitations 与下一证据需求；
- 名称预期、预览、能力矩阵、`activationReadiness` 和 lifecycle state。

没有这些记录，`passed` 只是意见，不是可重复的 gate。

## 16. 研究依据

- 电影风格应分析系统性的形式选择，而非把作者名本身当风格：[David Bordwell, On the History of Film Style](https://www.davidbordwell.net/books/on-history-film-style-davidbordwell-180531.pdf)
- Getty 将 agents、works、styles/periods 分开管理，并强调 style 是艺术元素的特定配置：[AAT Guidelines](https://www.getty.edu/publications/vocabularies-editorial-guidelines/aat-guidelines/1_about_aat/1.1/), [CONA Style Field](https://www.getty.edu/publications/vocabularies-editorial-guidelines/cona-guidelines/3_editorial_rules/3.6_fields/3.6.2/)
- SKOS 区分 concept identity 与 preferred/alternative/hidden labels：[W3C SKOS Reference](https://www.w3.org/TR/skos-reference/)
- 视觉风格学习存在 content/style leakage，必须分离内容与形式：[ALADIN-NST](https://arxiv.org/abs/2304.05755), [DEADiff](https://openaccess.thecvf.com/content/CVPR2024/html/Qi_DEADiff_An_Efficient_Stylization_Diffusion_Model_with_Disentangled_Representations_CVPR_2024_paper.html)
- 聚类验证不能只依赖单一内部指标，应结合稳定性与外部/人工验证：[Rousseeuw](https://doi.org/10.1016/0377-0427(87)90125-7), [Ullmann et al.](https://arxiv.org/abs/2103.01281)
