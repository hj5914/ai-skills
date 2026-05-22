# Business Delivery Orchestrator

业务需求交付编排 skill。它帮助 agent 把一个需求从分析推进到交付：先判断复杂度，再选择轻量路径或完整流程，必要时才引入受控子代理。

## 核心升级特性

- **澄清测验 (Clarify Quiz)**：在设计前强制要求 AI 识别并解决 3-5 个技术模糊点，变“被动提问”为“主动排雷”。
- **自动化影响扫描 (Impact Scan)**：定级前自动扫描依赖图，防止低估逻辑改动对上游文件的连锁影响。
- **动态宪法挖掘 (Constitution Mining)**：自动从项目配置文件提取技术底线，实现零配置的规范对齐。
- **微任务化 (Micro-Tasking)**：引入 5 分钟准则，要求将任务拆解为可快速验证的原子单元，确保 TDD 节奏。
- **对抗性评审 (Adversarial Review)**：针对 L/XL 任务，强制通过派生**独立 Reviewer 子代理**进行自我攻击。
- **影子分支隔离 (Branch Isolation)**：委派写权限子代理时，优先使用临时分支或 Worktree 确保物理层源码安全。
- **长效记忆增强 (Knowledge Update)**：交付后自动提取 Lessons Learned 存入 `MEMORY.md`，实现项目的持续学习。
- **强制触发器 (Hard Triggers)**：明确规定涉及 Auth、支付、迁移等敏感逻辑时严禁走 Fast Path。
- **宪法优先权**：明确任务级 Constitution 是项目级全局规范的严格子集。

## 关键资产

- `examples/minimal-feature-delivery-example.md`：最小完整示例流程
- `templates/`：contract、handoff、`MEMORY.md` 和 gate checklist 模板
- `references/`：选型规则、契约规则、验证门禁和 stop conditions

## 文件索引

```text
SKILL.md
  主流程、fast path、子代理策略和上下文预算。

references/
  规则文档：delivery-contract.md、verification-gates.md、delegation-matrix.md。

templates/
  可复用产物：contract、handoff、gate checklist、MEMORY entry。

examples/
  最小端到端示例流程。

agents/openai.yaml
  Codex UI 元数据。
```

## 使用顺序

1. 先读 `SKILL.md` 判断 fast path、轻量契约还是完整流程。
2. `M` 任务优先复用 `templates/lightweight-contract-template.md`。
3. `L/XL` 任务复用 `templates/full-delivery-contract-template.md`，必要时参考 `references/delivery-contract.md`。
4. 交付时复用 `templates/handoff-gate-checklist-template.md`、`templates/handoff-template.md` 和 `templates/memory-entry-template.md`。
5. 不熟悉时先看 `examples/minimal-feature-delivery-example.md`。

## 备注

- 默认单 agent 执行，子代理只在边界清晰且收益明确时启用。
- 模板文件是推荐默认值，不是强制格式；宿主规范优先。
