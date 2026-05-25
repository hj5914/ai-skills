# Business Delivery Orchestrator

业务需求交付编排 skill。

它把需求从分类、契约、实现、验证到 handoff 串成一个可控流程，默认单主代理执行，必要时才引入受控子代理。附带的 `tools/bdo.py` 提供本地状态、contract、review、verify 和 handoff 产物生成能力。

## 用途

- 统一业务需求从分析到交付的执行节奏。
- 生成 contract、review、verify、handoff、memory 等交付产物。
- 记录 clarify quiz、impact scan、constraints 和 review 结果，减少过程信息丢失。
- 在高风险或大任务场景下提供轻量提醒和最小门禁。

## 适合场景

- 中大型业务需求、跨前后端需求或需要共享 contract 的任务。
- 需要 handoff、review 记录或 `MEMORY.md` 沉淀的交付场景。
- 想在单 agent 为主的前提下控制多 agent 成本和边界的任务。

## 不适合场景

- 单文件机械改动、纯文案调整或直接问答。
- 不需要 contract、verify 或 handoff 产物的临时性修改。
- 期望它自动完成审批、自动回答 clarifying questions 或自动编排复杂多 agent 工作流的场景。

## 安装/依赖

- 运行 `tools/bdo.py` 时需要 Python 3。
- 无额外 Python 包依赖。
- 无外部服务必需依赖；`scan`、`quiz`、`contract`、`review`、`verify`、`handoff` 都可本地执行。

## 使用/验证

最小入口：

```bash
python3 tools/bdo.py --help
```

快速验证：

```bash
python3 tools/bdo.py init --objective "Demo delivery"
python3 tools/bdo.py status
```

常用命令：

```text
python3 tools/bdo.py init|classify|phase|quiz|scan|mine|contract-what|contract-how|contract|review|verify|handoff|memory|delta|status
```

执行规则、fast path、委派策略和验证门禁以 `SKILL.md` 为准。

## 文件说明

```text
SKILL.md
  Agent 执行规范，包含 fast path、task sizing、hard gates、workflow 和 CLI 边界。

tools/bdo.py
  本地 CLI 入口，生成或查询 state、quiz、scan、contract、review、verify、handoff、memory、delta、status 产物。

references/
  契约、委派矩阵、验证门禁等参考资料。

templates/
  contract、reviewer prompt、handoff、gate checklist、MEMORY 模板。

schema/bdo-state.schema.json
  `.bdo.state.json` 的结构定义。

examples/
  最小端到端示例。
```

## 备注

- 默认单 agent 执行，子代理只在边界清晰且收益明确时启用。
- 只有在准备做委派决策时才需要读取 `references/delegation-matrix.md`；single-agent 和 fast-path 不需要为此增加流程负担。
- `auth`、`data`、`payment`、`migration` 这类敏感 surface 在 CLI 中都会强制要求 full contract，且 handoff 前会校验 contract / verify 产物文件仍然存在。
- `scan` 是启发式，不是完整依赖图；它会区分 direct/import/code/test/doc 命中，并对敏感关键词做小幅 size 上调。
- `contract-what` / `contract-how` 用于 L/XL 两段式契约。
- `classify` 和 contract 命令会在大任务或高风险任务上给出 `quiz` 的软提示。
- `delta --follow-up` 可把实现中发现但不应并入当前范围的问题显式带到 handoff。
- 模板文件是推荐默认值，不是强制格式；宿主规范优先。
