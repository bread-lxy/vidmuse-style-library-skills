# VidMuse 风格素材采集（中文审核版）
<!-- source: SKILL.md -->
<!-- source_sha256: f13587d8f126da1b61e191b0f3e8914d30e0f964c7a7b0b17f6ac0cffa5ba51f -->

> 本文件用于中文审核和修改意见收集。运行时以英文主文件 `SKILL.md` 为准；收到中文意见后，先修改英文版，再同步更新本文件及源文件哈希。

## 用途

调研并采集公开或本地视觉素材来源，再将图片、艺术作品、空间视图、游戏截图、影视或动画静帧、连续视频及其他可审阅视觉单元标准化为可追溯、去重、与来源形态解耦的 VidMuse `EvidenceRecord` 证据库。采集方法应适配来源，但输出合同保持稳定；来源标签不得被当成风格事实。

## 1. 先理解来源，再开始采集

阅读 [source-reconnaissance.md](references/source-reconnaissance.md) 和 [evidence-contract.md](references/evidence-contract.md)。使用随附的来源评估与数据质量模板，并根据 `references/collection-plan.schema.json` 校验采集计划。

通过浏览器、公开 API、可下载数据集或本地文件检查真实来源。在第一轮来源方案确认前，查询本次运行所选环境的实时官方风格库并保存为 `official-style-catalog.json`，同时校验配置 endpoint 与所选环境一致。汇报库内可见的视觉形态构成、明显缺口及该判断的局限。该快照只作为阶段汇报背景，不得改变本来源的采集范围、采样分层、采集优先级或停止条件。

同时明确：

- 可发现实体和可能的 Anchor；
- 搜索、浏览、详情、分页和素材下载路径；
- 哪些元数据是观察值、推断值、缺失值或不可靠值；
- 证据单位，以及它能支持静态外观、连续运动、剪辑结构或哪些其他明确声明的结论；
- 该来源的 source group、context 和独立性定义；
- 目标覆盖、采样分层和明确停止条件；
- 条款、许可、署名、登录、速率与发布事实，供溯源和后续使用判断。

编写 `official-style-catalog.json`、`source-assessment.md`、`collection-plan.json`，并在 `sample/` 下建立真实试采。运行 `python scripts/validate_collection_plan.py <collection-plan.json>` 校验计划。试采证明提取和证据标准化可行后即可放量。人工可以对范围和方法提出意见，但 `research_only`、`unknown` 或后续发布限制本身不能缩小或终止研究采集。

## 2. 自适应采集

为来源选择最可靠的路径：浏览器自动化、公开或有文档的接口、数据集下载或本地导入。模型可以设计来源专用提取方式，但必须保持以下不变量：

- 保存来源 URL 或稳定来源 ID 以及采集时间；
- 保存本地素材，以及发现它的每个查询或 Anchor 关系；
- 支持断点续跑且不重复素材；
- 标准化前保留原始来源值；
- 隔离缺失、损坏、不可访问或含义不明的记录；
- 不绕过访问控制，也不隐瞒来源限制；如实记录，但不把“能否作为公开参考图”当成采集过滤器。

[shotdeck-case-study.md](references/shotdeck-case-study.md) 只是案例，不是通用 Schema。

## 3. 标准化证据

建立来源字段到通用合同的映射文件，可从 [mapping.example.json](references/mapping.example.json) 开始。当来源元数据没有可观察视觉特征时，在严格校验前按 [visual-feature-extraction.md](references/visual-feature-extraction.md) 对素材提取视觉特征。

```powershell
python scripts/normalize_evidence.py `
  --input <raw.jsonl-or-csv> `
  --mapping <mapping.json> `
  --asset-root <asset-root> `
  --output <evidence.jsonl> `
  --quarantine <quarantine.json> `
  --report <data-quality.md>

python scripts/validate_evidence.py <evidence.jsonl> --asset-root <asset-root> --strict

python scripts/build_evidence_contact_sheet.py `
  --evidence <evidence.jsonl> `
  --asset-root <asset-root> `
  --output <stage-dir>/review/contact-sheet.html
```

必须分开：

- `styleFeatures`：肉眼可观察、可作为 membership 依据的视觉特征；
- `contentFeatures`：人物、物体、故事、地点或场景内容；
- `provenance`：来源实体、创作者、作品、查询和采集事实。

不得为了提高聚类效果而把值在三个通道之间挪用。

## 4. 交付证据阶段

交付：

- `raw-manifest.jsonl`；
- `evidence.jsonl`；
- `quarantine.json`；
- `data-quality.md`；
- `mapping.json`、本地 `assets/` 目录，以及由 `build_evidence_contact_sheet.py` 生成的 contact sheet；
- 按媒介、来源组、上下文、视觉特征字段、权利状态和证据能力统计的覆盖报告。

人工审核的是证据质量和覆盖度，不是宣称每条记录都是风格，也不是宣称每个采集素材都能公开复用。`research_only` 或 `unknown` 的证据仍可采集，其状态继续传递到后续使用判断。
