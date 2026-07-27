# VidMuse 风格库生产总控（中文审核版）
<!-- source: SKILL.md -->
<!-- source_sha256: b5a35080e0c01d0439f157f9047d9f9e9274dd2ab8f2d707b0fc140300eab771 -->

> 本文件用于中文审核和修改意见收集。运行时以英文主文件 `SKILL.md` 为准；收到中文意见后，先修改英文版，再同步更新本文件及源文件哈希。

## 用途

从新的视觉素材来源开始，编排一条可恢复的完整 VidMuse 风格库生产流程：证据标准化、结合实时官方库查重的 Anchor 概念审核、六字段生产、每条风格一张参考图，以及 JSON/CSV 交付。适用于新建、续跑、审计或重跑一批官方风格候选。人工审核保持轻量，但必须在阶段边界明确确认；不得写入线上后台。

协调三个阶段 Skill。判断工作留在对应阶段 Skill 中；本 Skill 只管理状态、批准、规范漂移和最终交付。

## 新建或恢复任务

1. 阅读 [pipeline-contract.md](references/pipeline-contract.md) 和 [source-of-truth.md](references/source-of-truth.md)。
2. 校验 Skill 内冻结的规范快照：

```powershell
python scripts/verify_standards.py check
```

3. 初始化一次运行，或检查已有运行：

```powershell
python scripts/run_pipeline.py init <run-dir> --name "<run name>" --source "<source>"
python scripts/run_pipeline.py status <run-dir>
```

4. 只处理状态为 `ready` 或 `in_progress` 的阶段。
5. 调用对应阶段 Skill，并把标准交付物放入该阶段目录。
6. 请人工审核者检查完整阶段包。只有审核者明确接受后才记录批准：

```powershell
python scripts/run_pipeline.py approve <run-dir> --stage <stage> --reviewer "<name>" --note "<decision>"
```

批准会冻结所有必需交付物的哈希。不得在阶段批准后静默重新生成内容。

## 阶段路由

| 阶段 | 使用的 Skill | 必须确认的事项 |
|---|---|---|
| `source-plan` | `vidmuse-style-source-mining` | 来源结构、采集可行性、试采策略，以及所选官方库的只读汇报快照；库内缺口和权利信息都不缩小研究采集 |
| `evidence` | `vidmuse-style-source-mining` | 证据质量、独立性和覆盖度 |
| `concept` | `vidmuse-style-concept-curation` | 实时官方库对比，以及推进、合并、拆分、暂缓或拒绝 |
| `records` | `vidmuse-style-record-production` | 六字段忠实度和近邻区分度 |
| `preview-export` | `vidmuse-style-record-production` | 每条风格一张最终参考图及交付包完整性 |

AI 预填完整的概念决策登记。人工按批次审核，只修改例外；阶段批准即表示接受所有未改动的 AI 建议。

## 安全回退

当已批准的输入、规范或决定发生变化时，从最早受影响阶段重新打开：

```powershell
python scripts/run_pipeline.py reopen <run-dir> --stage <stage> --reviewer "<name>" --note "<reason>"
```

该操作会把本阶段及所有下游批准标记为失效，但保留全部交付物、批准记录和备注。

## 不可违反的规则

- 研究证据必须与生成参考图和生产输出分开保存。
- 来源元数据不得进入视觉聚类特征或生产 Prompt。
- 第一轮来源方案确认前，查询本次运行所选环境的官方库，并校验配置 endpoint 与所选环境一致；该快照只供汇报，不得引导采集。概念审核时再次刷新，用于实时查重和非约束性的候选构成建议。静态后台快照只用于理解字段形态。
- 流程终点是六字段 JSON/CSV 加参考图包，`imageUrl` 保持为空。
- 不得上传素材、回填 URL、调用后台创建接口或修改 plugin。
- 按 `source-of-truth.md` 规定的优先级使用 Skill 内冻结的规范。
- 一旦发现规范漂移，立即停止并报告发生变化的来源。

## 完成条件

只有当五个阶段全部获批、`status` 未报告交付物漂移、所有 staging 记录通过严格校验、JSON/CSV 可以无损往返，并且每条风格恰好有一张命名正确的最终参考图时，任务才算完成。
