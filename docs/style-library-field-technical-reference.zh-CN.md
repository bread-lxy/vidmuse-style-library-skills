# VidMuse 风格库六字段技术参考

> 内容语义以 [风格库六字段内容规范](style-library-field-standard.zh-CN.md) 为唯一准则。本文只把主规范中可以稳定机器判断的部分转成工程合同，不用字符数、固定句式或固定 Analysis 标题反向决定内容质量。

## 1. 数据对象

正式风格对象仍只有六个字段：

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

正式记录六字段必填且不接受额外字段。本阶段尚未生成正式参考图的候选文档不是可导入记录，可以暂不提供 imageUrl，并单列非生产字段“参考图生成 Prompt”；上传后再形成正式六字段对象。

## 2. 可机器执行的合同

| 字段 | 确定性检查 | 需要人工判断 |
|---|---|---|
| `name` | 非空英文单行文本；批次内忽略大小写后唯一 | Anchor 层级准确、用户可理解、与近邻不误导 |
| `tags` | 5–8 个英文短词组；无重复、逗号、句子或模型污染 | 按“视觉形态 → 风格家族 → 核心差异 → 质感/氛围”排序，能同时检索和生成 |
| `description` | 非空英文文本；无模型和来源污染 | 说明视觉身份、适用项目/意图，并在必要时说明近邻差异 |
| `analysis` | 非空英文文本；允许与媒介匹配的自定义段落标题 | 覆盖 evidence 支持的视觉与媒介规律，解释适用范围、迁移与失真边界 |
| `promptSample` | 非空英文单行文本；模型、格式与来源污染为错误；具体内容词进入复核 | 组织可迁移的视觉控制；可重复或省略 name，内容依赖型风格可保留已确认的必要通用母题 |
| `imageUrl` | HTTPS URL；可选网络、媒体类型、尺寸与比例检查 | 原创、可见地证明风格、无版权复刻和视觉瑕疵 |

## 3. 纯净度规则

六字段不得包含：

- 模型、LoRA、checkpoint、sampler、steps、CFG、seed 等实现信息；
- `masterpiece`、`best quality`、`8K` 等无风格表意的质量词；
- 权重语法、分辨率、画幅、负向提示和生成命令；
- ShotDeck、文件路径、候选编号、evidence 备注和工作状态；
- 具体演员、角色、剧情、名场面和来源特有动作、地点、道具；内容依赖型风格经边界审核确认的通用母题除外；
- TODO、占位符、JSON 片段或中文标点。

promptSample 可以写 `The Tree of Life-inspired ...`、`David Fincher-inspired ...` 等 Anchor 短语。这是风格执行信息，不属于无意义重复；同一名称不应在后续短语继续反复出现。

## 4. 校验边界

Schema 和校验器负责结构、英文内容、tags 数量与短语形态、确定性污染、名称去重和 URL。已知视觉形态别名提示改用标准词；未知但合理的视觉形态和可能合理的内容词只产生人工复核提示，不直接阻断。以下问题必须人审或通过适用范围内的同题生成验证：

- Anchor 是否真实成立以及 name 是否适合用户展示；
- tags 的语义层级和特征优先级是否正确；
- description 是否足以支持 Planner 精排；
- analysis 是否忠实于 evidence、是否覆盖该媒介真正构成边界的规律；
- promptSample 是否能产生预期视觉结果并与近邻稳定区分；
- 参考图是否证明风格而不是复刻来源。

## 5. 使用

```powershell
python style-library-schema-taxonomy/validate_style_record.py records.json --strict
python style-library-schema-taxonomy/validate_style_record.py records.jsonl --format json
python style-library-schema-taxonomy/validate_style_record.py records.json --check-image
python -m unittest discover -s style-library-schema-taxonomy/tests -v
```

`--strict` 会把可立即修正的 warning 计为失败；开放词表和内容依赖判断产生的 advisory 不直接失败，但必须在风格边界审核中处理。通过 strict 仍不等于风格已通过视觉审核。

## 6. 历史兼容

`style-record.v1.schema.json` 只用于复现第一阶段历史数据。旧 Phase 2 的质量前后缀、首 tag 等于 name、固定两句 description、固定五段 Analysis 和固定字符范围均不再是当前准入规则。
