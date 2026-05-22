# AI Skills

这是一个多 Skill 仓库，用来集中管理可复用的 AI agent skills。

目前目标是兼容 Codex、Claude Code、Gemini 以及类似的 agent harness。每个 skill 都保持自包含，后续可以单独复制、安装或发布。

`business-delivery-orchestrator` skill 内还包含一个零依赖的本地辅助 CLI，用于半自动生成 contract、verify、handoff 和 `MEMORY.md` 产物。

## 当前 Skills

### business-delivery-orchestrator

业务需求交付编排 skill。

它用于把一个业务需求从分析推进到交付：判断需求复杂度、选择轻量路径或完整交付流程、建立交付契约、决定是否需要子代理、约束子代理职责、执行验证并输出交付总结。

默认不创建子代理。只有当任务复杂度、文件边界和并行收益都足够明确时，才建议或触发受控的子代理协作。

路径：`skills/business-delivery-orchestrator/`

### lanhu-browser-cdp-skill

Lanhu / Axure 页面调试和提取 skill。

它通过浏览器 CDP 辅助检查 Lanhu 页面、列出浏览器 tab、提取 iframe 数据、执行 JavaScript、截图，以及分析 Axure 相关页面结构。

路径：`skills/lanhu-browser-cdp-skill/`

### gitlab-internal-access

内网 GitLab 访问 skill。

它通过 `GITLAB_TOKEN` 访问用户对话、AI 上下文、环境变量或其他方式提供的 GitLab base URL，用于只读查询 GitLab 项目、仓库、文件、MR、pipeline、job、group 或用户信息。group path 和 project path 不是必需项，只在访问对应资源接口时需要。

路径：`skills/gitlab-internal-access/`

## 目录结构

```text
LICENSE
README.md
SKILL_README_GUIDE.md
skills/
  business-delivery-orchestrator/
    SKILL.md
    examples/
    references/
    templates/
    tools/
    agents/
  gitlab-internal-access/
    SKILL.md
    scripts/
    agents/
  lanhu-browser-cdp-skill/
    SKILL.md
    scripts/
```

## BDO CLI

本地辅助命令入口：`python3 skills/business-delivery-orchestrator/tools/bdo.py`

常用流程：

```bash
python3 skills/business-delivery-orchestrator/tools/bdo.py init --objective "Add bulk archive"
python3 skills/business-delivery-orchestrator/tools/bdo.py classify --size M --risk medium
python3 skills/business-delivery-orchestrator/tools/bdo.py contract
python3 skills/business-delivery-orchestrator/tools/bdo.py verify
python3 skills/business-delivery-orchestrator/tools/bdo.py handoff
python3 skills/business-delivery-orchestrator/tools/bdo.py memory
python3 skills/business-delivery-orchestrator/tools/bdo.py status
```

## 安装示例

使用 Codex skill installer 安装单个 skill：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo hj5914/ai-skills \
  --path skills/business-delivery-orchestrator
```

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo hj5914/ai-skills \
  --path skills/lanhu-browser-cdp-skill
```

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo hj5914/ai-skills \
  --path skills/gitlab-internal-access
```

`lanhu-browser-cdp-skill` 还需要安装自己的 Python 依赖，详见它的 README。

## 维护约定

- 每个 skill 放在 `skills/<skill-name>/` 下。
- 每个 skill 至少包含一个 `SKILL.md`。
- 新增 skill 的 README 结构参考 [SKILL_README_GUIDE.md](SKILL_README_GUIDE.md)。
- skill 内部的脚本、引用文档、元数据都放在自己的目录里，不和其他 skill 混用。
- 不把单个 skill 自己的 `.git` 目录提交进这个聚合仓库。
- 仓库默认使用根目录 [LICENSE](LICENSE)，单个 skill 不单独放 LICENSE，除非它确实需要不同许可证。
- 如果某个 skill 需要安装依赖，在它自己的 README 或 SKILL.md 中说明。
