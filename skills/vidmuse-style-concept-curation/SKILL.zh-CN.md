# VidMuse 风格概念策展（中文审核版）
<!-- source: SKILL.md -->
<!-- source_sha256: c28e569f95a6e44d7aad9e89b8f7b0a79d4f79adbe7fd8faea2f6d3f91e08024 -->

> 本文件用于中文审核和修改意见收集。运行时以英文主文件 `SKILL.md` 为准；收到中文意见后，先修改英文版，再同步更新本文件及源文件哈希。

## 用途

把已通过的 VidMuse `EvidenceRecord` 证据库转成视觉一致、基于 Anchor 的风格假设、盲审图板、近邻边界、实时官方库查重结果，以及由 AI 完整预审、供人工轻量检查的决策登记。Anchor 决定可以测试什么范围，视觉证据决定该 Anchor 最终支持零种、一种还是多种风格。

## 必读资料

先阅读 [style-clustering-rules.zh-CN.md](references/style-clustering-rules.zh-CN.md)，它是在 D-024 下生效的边界政策。创建机器记录前阅读 [concept-contract.md](references/concept-contract.md)，人工判断时使用 [concept-review-checklist.md](references/concept-review-checklist.md)。`references/historical/` 下的文件只用于复现历史实验，不是当前要求。

## 1. 确认输入

需要已经通过审核的 `evidence.jsonl` 及其数据质量报告。来源权利摘要作为 provenance 继续携带，不能成为删除研究证据的理由。当证据单位或溯源信息不足以支持独立比较时，停止概念判断。

在公开命名和最终建议前，为本次运行抓取实时官方库：

```powershell
python scripts/snapshot_official_catalog.py --environment dev --output <stage-dir>/official-style-catalog.json
```

该脚本默认查询 dev，并读取 `~/.vidmuse-dev/config.json`（也可通过 `VIDMUSE_DEV_CONFIG` 指定）；查询生产库时使用 `--environment prod`，也可用 `--config` 显式指定配置。脚本通过 `VIDMUSE_CONFIG` 将所选配置传给 CLI，校验 endpoint 与请求环境一致，再执行 `vidmuse style list --scope official` 分页读取。静态后台 HTML 只作为字段形态的补充材料。CLI 不可用时，证据工作可以继续，但概念阶段不能批准，除非审核者明确接受使用过期目录的风险。

## 2. 建立候选范围

- 从作品、人物、工作室、流派、技法、IP、社区审美或其他公认参照中建立具体、公开的 Anchor。
- Anchor 只是证据范围，不是必然成立的聚类。
- 视觉特征驱动的发现必须保持匿名，直到能够映射到有效公共 Anchor。无 Anchor 聚类可以支持研究，但不能直接成为官方风格。
- 在恢复 provenance 前，按 `references/anonymous-candidate.schema.json` 写入 `anonymous-candidates.jsonl`。只使用密封的非透明范围引用，不能使用公开名称。
- 初始视觉分组时隐藏专名和来源标签。

## 3. 聚类与解释

选择适合媒介的方法：

- 结构化元数据的视觉覆盖充分时才单独使用；
- 元数据稀疏时使用视觉向量或模型辅助比较；
- 不同通道互补而非重复时使用混合共识。

不能用内容特征、原始搜索标签、名称、热度或评论声誉作为 membership 依据。有效假设必须具有可重复的多特征语法、允许变化、排除的来源母题，以及可解释的最近邻边界。

## 4. 建立盲审包

锁定 `anonymous-candidates.jsonl`，恢复 provenance 后再编写标准 `hypotheses.jsonl`。校验二者并生成审阅材料：

```powershell
python scripts/validate_concepts.py `
  --evidence <evidence.jsonl> `
  --anonymous-candidates <anonymous-candidates.jsonl> `
  --hypotheses <hypotheses.jsonl> `
  --strict

python scripts/build_review_packet.py `
  --evidence <evidence.jsonl> `
  --anonymous-candidates <anonymous-candidates.jsonl> `
  --hypotheses <hypotheses.jsonl> `
  --asset-root <asset-root> `
  --output-dir <stage-dir>/review
```

每个审核包必须展示核心证据、允许变化和互不重叠的边界证据。父级/叶子级或创作者/项目范围重叠时，宽范围一侧必须排除子级来源组，并说明剩余的非子级覆盖。不能把一个 sibling 默认为整个父范围；缺少独立证据时应标记边界证据不足，不能重复使用同一批证据。

## 5. 与实时官方库比较

任何概念进入推进决定前，都要和已保存的实时官方库及同批候选比较：精确或标准化名称、alias、父子关系和高相似视觉配方。summary 信息不够时，使用 `vidmuse style get <styleId> --view full --output json` 获取官方完整记录。

编写 `catalog-comparison.md`，为每个假设记录最近官方风格、关系和一句新增价值结论；同时按视觉形态和 Anchor 类型汇总本批候选，并以数量或比例给出供人工判断的推进构成建议。该建议不设类别上限，也不能自动淘汰成立的概念。单条判断保持简单：精确或近似重复，以及不会改变 Planner 选择或生成结果的高相似概念，不得推进；若证据证明它能形成明确不同的用户选择和视觉配方，近邻叶子仍可以推进。不规定通用相似度阈值。如果审核期间官方库发生变化，在概念阶段批准前刷新实时快照。

## 6. 准备人工审核的决策

AI 只能提出以下决定：

- `advance`
- `merge`
- `split`
- `hold`
- `reject`

AI 根据证据建议，在 `decision-registry.jsonl` 中为每个假设预填完整一行。`parent_child`、`related` 和 `alias` 是关系，不是决定。人工检查审核包和目录对比，只修改例外，并按批次批准概念阶段。只有针对性确认或覆盖 AI 决策的行才需要填写审核人、时间和备注；阶段批准记录覆盖所有未修改的 AI 建议。
