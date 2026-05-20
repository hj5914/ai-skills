# GitLab Internal Access

GitLab 访问 skill。

它用于让 agent 通过环境变量中的 `GITLAB_TOKEN` 访问用户提供的 GitLab API，适合查询项目、检查仓库信息、读取文件、查看 MR/CI 信息或辅助定位 GitLab 相关问题。

## 用途

- 访问用户对话、AI 上下文、环境变量或本地仓库信息中提供的 GitLab 实例。
- 使用固定环境变量名 `GITLAB_TOKEN` 发起 GitLab API 请求。
- 提供可复用的 `scripts/gitlab_api.py` 脚本，减少重复 curl 命令。
- 只执行 GitLab 只读 API 请求。

## 适合场景

- 列出或搜索 GitLab 项目。
- 查询当前 token 可访问的项目，或按指定 group/project 继续深入。
- 读取 GitLab API 响应并辅助分析仓库、分支、文件或 CI 信息。
- 查看 merge requests、pipelines、jobs 等只读信息。

## 不适合场景

- 访问 GitHub 或其他非 GitLab 服务。
- 没有配置 `GITLAB_TOKEN` 的环境。
- 无法从用户、上下文、环境变量或本地仓库信息中确定 GitLab 地址的场景。
- 需要绕过权限读取用户无权访问的项目。
- 需要把 token 写入文件、日志或命令文本的操作。
- 创建、修改、触发、审批、合并、重试或删除 GitLab 资源的写操作。

## 安装/依赖

运行依赖：

- Python 3 标准库。
- 环境变量 `GITLAB_TOKEN`。
- GitLab 地址由用户对话、AI 上下文、`GITLAB_BASE_URL`、本地仓库 remote 或其他可信来源提供。
- 最小 token scope：一般只读 API 使用 `read_api`，读取仓库文件可能需要 `read_repository`。
- 代理按用户环境决定：默认使用系统/环境代理，也可单次请求使用 `--no-proxy` 或 `--proxy-url`。

无额外 Python 包依赖。

## 使用/验证

确认 token 存在，但不要打印 token 内容：

```bash
if [ -n "$GITLAB_TOKEN" ]; then echo GITLAB_TOKEN_PRESENT; else echo GITLAB_TOKEN_MISSING; fi
```

如果缺少 `GITLAB_TOKEN`，不要在对话里粘贴 token 明文。把下面命令中的 `<your_gitlab_token>` 在本地替换成自己的 token 后执行。注意：包含真实 token 的命令可能会被 shell 历史记录保存。

macOS/Linux zsh，永久写入 `~/.zshrc`：

```bash
printf "\nexport GITLAB_TOKEN='%s'\n" '<your_gitlab_token>' >> ~/.zshrc && source ~/.zshrc
```

macOS/Linux bash，永久写入 `~/.bashrc`：

```bash
printf "\nexport GITLAB_TOKEN='%s'\n" '<your_gitlab_token>' >> ~/.bashrc && source ~/.bashrc
```

Windows PowerShell，写入当前用户环境变量；执行后重启终端：

```powershell
[Environment]::SetEnvironmentVariable('GITLAB_TOKEN', '<your_gitlab_token>', 'User')
```

建议最小权限：一般只读 API 使用 `read_api`，读取仓库文件可能需要 `read_repository`。

调用 GitLab API：

```bash
python3 scripts/gitlab_api.py \
  --base-url "<gitlab_base_url>" \
  "/api/v4/projects?per_page=100&simple=true" \
  --paginate \
  --pretty
```

地址也可以通过 `GITLAB_BASE_URL` 或当前仓库中看起来明确属于 GitLab 的 remote 推断；传入的 base URL 应为 GitLab 根地址，不应包含 `/api/v4`。
remote 推断是保守的；如果自建 GitLab 域名中不包含明显的 `gitlab` 字样，请使用 `--base-url` 或 `GITLAB_BASE_URL`。
Windows 上如果没有 `python3` 命令，可以改用 `py -3` 或 `python`。group path 和 project path 不是必需项，只在访问对应资源接口时需要。

代理处理：

- 默认使用系统/环境代理配置，例如 `HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY`、`NO_PROXY`。
- 必须直连时，加 `--no-proxy`。
- 必须走指定代理时，加 `--proxy-url "<proxy_url>"`。
- 代理地址不要写死进 skill；如果 proxy URL 内含账号密码，也要按凭据处理，不能打印或提交。

执行细节和安全规则以 `SKILL.md` 为准。

## 文件说明

```text
SKILL.md
  Agent 读取的主说明文件，包含触发条件、访问规则、常用命令和排障方式。

scripts/gitlab_api.py
  使用 GITLAB_TOKEN 调用 GitLab 只读 API 的辅助脚本，支持 base URL 推断、分页、超时、代理策略和额外非凭据 header。

agents/openai.yaml
  Codex UI 元数据。
```

## 备注

- 不要打印、提交或记录 `GITLAB_TOKEN`。
- token 环境变量名固定为 `GITLAB_TOKEN`，不支持别名，也不通过命令行参数传 token 值。
- 不要让用户在对话中粘贴 token 明文；只提示用户在本地环境中设置 `GITLAB_TOKEN`。
- 不要把 token 放进 URL、请求体、日志、截图、提交信息、PR/Issue 内容；可复制的设置命令必须使用 `<your_gitlab_token>` 占位符。
- proxy URL 如果包含账号密码，也按凭据处理。
- 对外展示命令输出前要检查并脱敏疑似凭据；如果 token 意外暴露，应提示用户轮换。
- 不要把具体 GitLab 地址写死进 skill；由调用时的上下文提供。
- 示例命令只引用 `$GITLAB_TOKEN` 环境变量，不内联 token。
- 这个 skill 只允许读操作；写操作需要单独的、明确授权的工作流。
