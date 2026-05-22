# Business Delivery Orchestrator

业务需求交付编排 skill。它帮助 agent 把一个需求从分析推进到交付：先判断复杂度，再选择轻量路径或完整流程，必要时才引入受控子代理。

## 核心升级特性

- **澄清测验 (Clarify Quiz)**：在设计前要求主代理主动识别 3-5 个关键技术模糊点；必要时再结构化提问，避免样板化噪音。
- **影响扫描 (Impact Scan)**：定级前可用 CLI 做启发式 impact scan，优先识别路径命中和 import/use 引用，再回退到文本匹配；它能帮助发现可能受影响的 importer、schema consumer 和路径边界，但结果仍需人工确认。
- **宪法挖掘 (Constitution Mining)**：CLI 可从常见项目配置文件提取轻量技术约束，减少 contract 初稿与仓库实际技术栈脱节。
- **微任务化 (Micro-Tasking)**：引入 5 分钟准则，要求将任务拆解为可快速验证的原子单元，确保 TDD 节奏。
- **对抗性评审 (Adversarial Review)**：针对 L/XL 任务，要求有独立的 adversarial review pass；宿主支持子代理时优先用独立 Reviewer。
- **影子分支隔离 (Branch Isolation)**：委派写权限子代理时，如果宿主环境支持临时分支或 Worktree，优先隔离；skill 本身不自动创建。
- **长效记忆增强 (Knowledge Update)**：交付后自动提取 Lessons Learned 存入 `MEMORY.md`，实现项目的持续学习。
- **强制触发器 (Hard Triggers)**：明确规定涉及 Auth、支付、迁移等敏感逻辑时严禁走 Fast Path。
- **宪法优先权**：明确任务级 Constitution 是项目级全局规范的严格子集。

## 关键资产

- `examples/minimal-feature-delivery-example.md`：最小完整示例流程
- `templates/`：contract、handoff、`MEMORY.md` 和 gate checklist 模板
- `references/`：选型规则、契约规则、验证门禁和 stop conditions
- `tools/bdo.py`：本地半自动 CLI，可生成 state、impact scan、constraints、contract、verify、handoff 和 memory 产物

## 文件索引

```text
SKILL.md
  主流程、fast path、子代理策略和上下文预算。

references/
  规则文档：delivery-contract.md、verification-gates.md、delegation-matrix.md。

schema/
  `.bdo.state.json` 的正式结构定义。

templates/
  可复用产物：contract、handoff、gate checklist、MEMORY entry。

examples/
  最小端到端示例流程。

tools/
  本地 CLI 入口 `bdo.py` 及其 `core/` 辅助模块。

agents/openai.yaml
  Codex UI 元数据。
```

## 使用顺序

1. 先读 `SKILL.md` 判断 fast path、轻量契约还是完整流程。
2. `M` 任务优先复用 `templates/lightweight-contract-template.md`。
3. `L/XL` 任务复用 `templates/full-delivery-contract-template.md`，必要时参考 `references/delivery-contract.md`。
4. 交付时复用 `templates/handoff-gate-checklist-template.md`、`templates/handoff-template.md` 和 `templates/memory-entry-template.md`。
5. 不熟悉时先看 `examples/minimal-feature-delivery-example.md`。
6. 如果想减少手工复制模板，可直接用 `python3 tools/bdo.py` 驱动本地产物生成；`classify` 支持重复传入 `--surface` 标记改动面，`phase` 可显式记录 `plan` / `implement` / `review` / `verify` 等阶段，`scan` 支持重复传入 `--target` 记录启发式 impact scan，优先匹配路径和 import/use 引用，再回退到文本匹配，`mine` 会从支持的配置文件中提取轻量 constraints，`delta` 会自动生成结构化 summary，`contract` 会据此预填默认块和已检测 constraints，`verify` 支持 `--evidence` / `--gap` 并把真实验证证据写入 state，`handoff` 会优先消费最新 delta 和验证证据，`memory` 支持 `--context` / `--lesson` / `--rule` / `--evidence` 并把交付经验回写到 state，state 写入采用原子替换避免半写入 JSON。
7. CLI 现在会做最小 hard-gate 校验：`auth/data` 任务要求 full contract，`M/L/XL` 任务在 verify 前必须先生成 contract，handoff 前必须先生成 verify 产物。
8. 如果要让其他 agent 或脚本消费结果，可加 `--json` 获取统一结构化输出。

## 备注

- 默认单 agent 执行，子代理只在边界清晰且收益明确时启用。
- 模板文件是推荐默认值，不是强制格式；宿主规范优先。
