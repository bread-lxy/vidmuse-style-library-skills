# VidMuse 六字段与参考图生产（中文审核版）
<!-- source: SKILL.md -->
<!-- source_sha256: d17b96984b8da3d0722dd22b36636bce4c3d231ceab76fb80bb286f9b4cd235b -->

> 本文件用于中文审核和修改意见收集。运行时以英文主文件 `SKILL.md` 为准；收到中文意见后，先修改英文版，再同步更新本文件及源文件哈希。

## 用途

把已批准的 VidMuse 风格概念按完整权威字段规范转换为后台六字段，验证 Planner 与生成行为，为每条风格编译并打包一张最终参考图；随后上传已批准的参考图，形成经验证、`imageUrl` 完整的最终 JSON/CSV。只从已批准的视觉证据和边界写字段，不能用文案拯救无效概念。

## 必读资料

在当前任务中，起草任何记录前必须完整阅读 [style-library-field-standard.zh-CN.md](references/style-library-field-standard.zh-CN.md)。它是内容权威；本 Skill 摘要、Schema、校验器、批量 Prompt 和示例都不能替代它。随后阅读 [product-consumption.md](references/product-consumption.md) 和 [preview-generation.md](references/preview-generation.md)。批量起草使用 [record-authoring-prompt.md](references/record-authoring-prompt.md) 时必须同时使用完整规范；[quality-example.md](references/quality-example.md) 只用于理解字段职责分离。开始最终 URL 回填阶段前，上传任何文件前还必须阅读 [image-url-backfill.md](references/image-url-backfill.md)。

## 1. 确认概念

必须具备：

- 已通过概念阶段批准的 `advance` 决定；
- 已验证的 Anchor 范围；
- 可迁移不变量和允许变化；
- 排除的来源母题；
- 最近邻区分规则；
- 概念阶段实时目录对比已经确认该候选具有足够新增价值。

不能只根据 Anchor 名称起草。

## 2. 推导字段

每个字段都必须使用完整字段规范。下面只是证据推导顺序，不能替代规范中的内容规则、字段边界、排序原则、例外和检查清单：

1. `name`：把已验证的 Anchor 层级转成清晰、面向用户的身份。
2. `analysis`：保存完整、适配媒介的视觉形成机制和迁移边界。
3. `tags`：从 Analysis 压缩出有序的形态大类、风格家族、核心差异和可选的完成质感。
4. `description`：补充适用项目、用户意图、推荐理由和有意义的近邻差异。
5. `promptSample`：编译可迁移视觉配方；首个短语可以重复 name。
6. `imageUrl`：staging 输出保持空字符串。

字段中不得包含来源元数据、项目特有主体与剧情、模型名、质量灌水词、权重、画幅、分辨率、负向提示或生成命令。内容依赖型风格只保留已在概念边界中确认必要的通用母题。

校验草稿：

```powershell
python scripts/validate_style_record.py <records.json-or-jsonl> --staging --strict
```

## 3. 生成参考图前测试

针对每条风格，在目标风格与最近邻都适用的范围内选择相同可比内容进行对照；随后在目标风格声明的适用范围内更换内容，验证迁移性。不适用于人物、表演、室内或环境的风格无需机械通过这些测试。该测试只验证六字段是否保留已批准差异，不重新进行官方库查重或概念准入判断。字段无法保留边界时，修改字段，或退回概念阶段。

编写 `field-review.md` 和 `neighbor-review.md`。生成完整参考图前取得人工确认。

## 4. 编译参考图 Prompt

使用 `preview-generation.md` 中的编译器，为每条风格生成恰好一个英文 Prompt。它必须使用原创、无明确身份的内容，并在不复制来源内容的前提下让已批准视觉身份清晰可见。每条风格在 `preview-prompt-source.jsonl` 中保存一行：

```json
{"name": "Exact Style Name", "prompt": "..."}
```

## 5. 导出记录与生图任务

在生图前先运行导出器，为每个 Prompt 分配最终稳定文件名：

```powershell
python scripts/export_records.py `
  --records <style-records.staging.jsonl> `
  --prompts <preview-prompt-source.jsonl> `
  --output-dir <delivery-dir> `
  --strict
```

该命令生成 `styles.json`、`styles.csv`、`preview-prompts.jsonl`、`preview-manifest.csv` 和空的 `previews/` 目录。

## 6. 生成并校验图片

从 `preview-manifest.csv` 逐行读取 Prompt 和文件名，使用可用的图像生成工具为每条风格生成一张图片。研究截图只用于理解上下文，绝不能直接作为输出参考图或图生图输入。

按 manifest 中的精确文件名保存，例如：

```text
001__the-tree-of-life-inspired__preview.png
```

校验每条风格一张图的交付包。图片未通过风格或图像质量检查时，重写 Prompt 或重新生成并替换失败文件；最终交付中不增加额外候选：

```powershell
python scripts/package_previews.py `
  --manifest <delivery-dir/preview-manifest.csv> `
  --preview-dir <delivery-dir/previews> `
  --strict
```

交付已批准的 `preview-export` 目录和审核报告，其中 `imageUrl` 仍保持为空。这个冻结的 staging 包是正式第六阶段的输入。本 Skill 不写入后台。

## 7. 上传并回填图片 URL

每条风格一张图的交付包获批后，执行这个正式的下一阶段。必须完整遵循 `image-url-backfill.md`。

- 显式使用 dev CLI 配置，并通过 `--plugin-id Evals-bread-img` 创建 VidMuse 线程。
- 按 manifest 稳定顺序上传每条风格唯一的最终参考图，并根据线程队列状态节流。
- 要求 Planner 把每个附件复制到真实的 `workspace/assets/images/` 目录，并返回有序映射。
- 独立验证每个 CDN URL；本地文件存在不能证明 URL 可用。
- 运行 `scripts/backfill_image_urls.py`，按精确的 `styleIndex`、`name` 和 `fileName` 三重对应关系回填。
- 把 Planner 原始响应保存为 `06-url-backfill/planner-image-url-map.json`，再把标准化结果写入同一阶段目录；不改写已批准的 preview-export 交付包。

回填交付包含 `imageUrl` 完整的六字段 `styles.json` 和 `styles.csv`、Planner 原始 URL 映射、标准化 URL 映射和网络校验报告。随后运行带图片检查的生产记录校验，并把完整的 `06-url-backfill/` 提交第六阶段批准。该步骤仍不创建风格，也不写入后台。
