# Business Delivery Orchestrator

业务需求交付编排 skill。

它用于帮助 agent 把一个业务需求从分析推进到交付：先判断任务复杂度，再选择轻量路径或完整交付流程，必要时才引入受控的子代理协作。

## 用途

- 将业务需求从分析推进到实现、验证和交付总结。
- 判断任务应该走 fast path、轻量交付契约，还是完整交付流程。
- 判断是否需要创建子代理，并限制子代理数量、职责和文件边界。
- 降低多代理带来的上下文浪费、接口漂移和集成成本。

## 适合场景

- 中等到复杂的业务功能开发
- 前后端联动需求
- 涉及 API、数据结构、权限、UI 状态或测试验收的改动
- 需要判断是否应该拆给多个子代理的任务
- 希望让 agent 从需求分析走到可验证交付的任务

## 不适合场景

- 简单问答
- 单文件小改动
- 文案调整
- 用户明确只想要快速结果、不需要流程分析的任务

这些场景会优先走 skill 内部定义的 fast path，而不是完整交付流程。

## 安装/依赖

无额外运行依赖。

将整个目录放到支持 skills 的 agent 环境中，或在需要时让 agent 读取 `SKILL.md`。

## 使用/验证

执行细节以 `SKILL.md` 为准。README 只用于人类快速理解这个 skill 的用途。

可以用 Codex 的 skill 校验脚本验证：

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

## 文件说明

```text
SKILL.md
  Agent 读取的主说明文件，包含触发条件、主流程、fast path、子代理策略和上下文预算。

references/delegation-matrix.md
  子代理使用判断、复杂度等级、角色边界和 prompt 模板。

references/delivery-contract.md
  业务需求交付契约模板，包括轻量版和完整版。

references/verification-gates.md
  验证深度、测试策略、低风险快捷验证和交付格式。

agents/openai.yaml
  Codex UI 元数据。
```

## 备注

- 默认单 agent 执行。
- 只有复杂度达到阈值，且子任务边界清晰时，才建议或触发子代理。
- 主 agent 始终负责最终结果、代码集成、验证和交付总结。
- 子代理输出只作为受控输入，不能直接替代主 agent 判断。
- 小任务不强行套完整流程。
