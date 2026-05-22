# Business Delivery Orchestrator

业务需求交付编排 skill。

它用于帮助 agent 把一个业务需求从分析推进到交付：先判断任务复杂度，再选择轻量路径或完整交付流程，必要时才引入受控的子代理协作。

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

## 多环境兼容性 (Harness Neutral)

本 Skill 采用平台中立设计，可在以下主流环境及任何支持 Markdown 指令的 Agent 中生效：

- **Codex / Gemini CLI**：支持原生 Subagent 调用，自动适配上下文预算。
- **Claude Code**：支持 `Task` 指令、临时分支隔离及 `Confirm Word` 协议。
- **Cursor / Copilot**：在单代理环境下，将“委派”自动降级为“角色化自我评审”，确保逻辑闭环。
- **其他环境**：只要 Agent 能读取 `SKILL.md`，即可根据任务规模自动切换交付模式。

## 用途

- 将业务需求从分析推进到实现、验证和交付总结。
- 判断任务应该走 fast path、轻量交付契约，还是完整交付流程。
- 判断是否需要创建子代理，并限制子代理数量、职责和文件边界（最小特权原则）。
- 降低多代理带来的上下文浪费、接口漂移和集成成本。

## 适合场景

- 中等到复杂的业务功能开发
- 前后端联动需求
- 涉及 API、数据结构、权限、UI 状态或测试验收的改动
- 需要判断是否应该拆给多个子代理的任务
- 希望让 agent 从需求分析走到可验证交付的任务

## 不适合场景

- 简单问答
- 单文件小改动（且不涉及 Hard Triggers）
- 文案调整
- 用户明确只想要快速结果、不需要流程分析的任务

这些场景会优先走 skill 内部定义的 fast path，而不是完整交付流程。

## 安装/依赖

无额外运行依赖。

将整个目录放到支持 skills 的 agent 环境中，或在需要时让 agent 读取 `SKILL.md`。

## 文件说明

```text
SKILL.md
  Agent 读取的主说明文件，包含触发条件、主流程、fast path、子代理策略和上下文预算。

references/delegation-matrix.md
  子代理使用判断、复杂度等级、角色边界和基于“最小特权”的 prompt 模板。

references/delivery-contract.md
  业务需求交付契约模板，包括“项目宪法”约束及全局规范优先权说明。

references/verification-gates.md
  验证深度、测试策略、对抗性评审流程和交付格式。

agents/openai.yaml
  Codex UI 元数据。
```

## 备注

- 默认单 agent 执行。
- 只有复杂度达到阈值，且子任务边界清晰时，才建议或触发子代理。
- 主 agent 始终负责最终结果、代码集成、验证和交付总结。
- **最小特权原则**：委派子代理时必须显式指定读写文件范围，禁止全局扫描。
- 小任务不强行套完整流程，但敏感操作强制升级。
