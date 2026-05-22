# Business Delivery Orchestrator

业务需求交付编排 skill。它负责把需求从分类、契约、实现、验证到 handoff 串成一个可控流程，默认单主代理执行，必要时才引入受控子代理。

## 关键资产

- `SKILL.md`：主流程、fast path、委派策略和验证门禁
- `references/`：契约、委派矩阵、验证门禁
- `templates/`：contract、reviewer prompt、handoff、gate checklist、`MEMORY.md` 模板
- `examples/`：最小端到端示例
- `tools/bdo.py`：本地 CLI，生成 state、scan、mine、contract、review、verify、handoff、memory 产物

## CLI 速览

```text
python3 tools/bdo.py init|classify|phase|scan|mine|contract-what|contract-how|contract|review|verify|handoff|memory|delta|status
```

## 使用建议

- 小任务走 fast path；大任务先写 contract，再实现，再 verify，再 handoff。
- `scan` 是启发式，不是完整依赖图。
- `contract-what` / `contract-how` 用于 L/XL 的两段式契约。
- `review` 记录轻量 adversarial review 结果，供 `handoff` 复用。
- `schema/bdo-state.schema.json` 定义了 state 结构。

## 备注

- 默认单 agent 执行，子代理只在边界清晰且收益明确时启用。
- 模板文件是推荐默认值，不是强制格式；宿主规范优先。
