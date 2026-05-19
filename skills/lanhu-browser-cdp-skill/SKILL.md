---
name: lanhu-browser-cdp-skill
description: Browser CDP workflow and scripts for inspecting Lanhu and Axure design/prototype pages. Use when the user asks Codex or another agent to view, analyze, extract, screenshot, or debug Lanhu design files, Axure prototypes, design annotations, iframe content, or Lanhu browser tabs through a local Chrome or Edge remote debugging port.
---

# Browser CDP 蓝湖查看 Skill

通过 Chrome DevTools Protocol (CDP) 连接用户浏览器，查看蓝湖设计稿的完整标注和交互说明。

**访问边界**：本 Skill 只允许访问 `lanhuapp.com` 及其子域名（例如 `axure-file.lanhuapp.com`）下的蓝湖链接。不得列出、打开、读取、截图或执行 JS 于非蓝湖页面；若用户提供 TAPD、Jira、Confluence、普通网页或其它非蓝湖链接，应要求用户提供对应的蓝湖链接或改用其它工具/Skill。

**路径约定**：本 Skill 根目录为 SKILL.md 所在目录（即包含 SKILL.md 和 scripts/ 的文件夹）。所有脚本路径相对于该根目录，命令中统一使用 `{SKILL_DIR}/scripts/xxx.py` 的形式，运行时替换为实际绝对路径。脚本文件统一放在 `scripts/` 子目录下。

**如何定位 SKILL_DIR**：首次使用时，Agent 应根据自身的 Skill 存储机制找到 SKILL.md 文件的实际路径，其所在目录即为 `{SKILL_DIR}`。也可直接询问用户 Skill 的安装位置。

---
## 触发场景

- 用户要求查看/分析蓝湖设计稿
- 用户提到"蓝湖"、"设计稿"、"原型"、"需求文档"等

---

## 推荐高可靠操作链路

优先使用这条链路。它不依赖蓝湖 iframe 是否随左侧页面切换，也能在主页面出现登录态提示但前端状态仍可读时继续分析。

### 第一步：检测当前平台和 CDP 端口

先判断运行环境，再检测端口：

```bash
python3 {SKILL_DIR}/scripts/check_cdp.py
```

- 输出 JSON → 端口已开启，跳到第三步
- 报错 `CDP_UNAVAILABLE` → 执行第二步

### 第二步：引导用户开启调试模式（仅端口未开启时）

先判断用户操作系统，然后给出对应的启动命令。

**检测平台方法**：通过 `check_cdp.py` 的错误信息无法判断平台，直接在对话中询问用户，或执行 `uname -s`（macOS 输出 `Darwin`）或检查 `%OS%`（Windows）。

向用户说明：

> 你的浏览器还没有开启远程调试模式，需要用特殊参数重启浏览器。
>
> **操作步骤：**
> 1. 先完全退出浏览器
> 2. 根据你的系统和浏览器，在终端/命令行执行以下命令启动

#### macOS Chrome
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 '--remote-allow-origins=*'
```

#### macOS Edge
```bash
"/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" --remote-debugging-port=9222 '--remote-allow-origins=*'
```

#### Windows Chrome
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=*
```

#### Windows Edge
```cmd
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --remote-allow-origins=*
```

**注意：**
- `--remote-allow-origins=*` 必须带，否则 WebSocket 403
- macOS 用引号包裹 `'*'` 防 zsh glob 展开报错，Windows 不需要
- 退出浏览器：macOS 用 `Cmd + Q`，Windows 用 Alt+F4 或任务栏右键关闭
- 启动后等几秒让页面恢复完再操作

### 第三步：打开用户给出的蓝湖链接（仅当链接尚未打开时）

如果用户直接给了蓝湖链接，或 `list_tabs.py` 找不到目标页面，但 CDP 端口已可用，先用 CDP 在调试浏览器中打开或复用该链接：

```bash
python3 {SKILL_DIR}/scripts/open_url.py "https://lanhuapp.com/xxx"
```

该脚本会：

1. 拒绝非 `*.lanhuapp.com` 链接
2. 检查同 URL 的蓝湖页面是否已经打开，已打开则复用
3. 未打开则通过 CDP 创建新标签页
4. 等待页面 target 出现并输出 `ws:` 后面的 WebSocket URL

拿到 `ws:` 后可直接进入第四步。如果用户没有给链接，再继续列出已打开的蓝湖标签页。

### 第四步：列出蓝湖标签页

```bash
# 只列出蓝湖相关页面
python3 {SKILL_DIR}/scripts/list_tabs.py

# 可选：按 URL 关键词进一步过滤
python3 {SKILL_DIR}/scripts/list_tabs.py lanhuapp
```

从结果中找到目标蓝湖标签页，记下 `ws:` 后面的 WebSocket URL。脚本只输出蓝湖页面，不会展示其它浏览器标签页。

### 第五步：提取 Axure manifest（首选）

```bash
python3 {SKILL_DIR}/scripts/extract_axure_manifest.py "ws://localhost:9222/devtools/page/xxx"

# 可选：按路径关键词过滤，比如只看应用端
python3 {SKILL_DIR}/scripts/extract_axure_manifest.py "ws://localhost:9222/devtools/page/xxx" 应用端
```

该脚本会：

1. 通过 CDP 读取蓝湖页面的 `window.doc.currentAxureData.versions`
2. 选择最新版本的 `jsonUrl`
3. 下载 Axure manifest JSON
4. 展开 `sitemap.rootNodes`
5. 输出每个页面的 `path`、`htmlUrl`、`dataJsUrl`、`mappingUrl`

后续分析优先直接请求输出中的 `htmlUrl`：

```bash
curl -sS "https://axure-file.lanhuapp.com/xxx.html"
```

页面 HTML 中通常包含页面标题、按钮文案、字段名称、标注、注释、交互逻辑说明等。按模块分析时，先从 manifest 的 `path` 定位目标模块（例如“应用端”），再批量读取该模块下每个页面的 `htmlUrl`。

### 第六步（可选）：CDP 截图查看 UI 布局

```bash
# 全页截图
python3 {SKILL_DIR}/scripts/screenshot.py "ws://localhost:9222/devtools/page/xxx" /path/to/output.png

# 区域截图（x y width height scale）
python3 {SKILL_DIR}/scripts/screenshot.py "ws://localhost:9222/devtools/page/xxx" /path/to/output.png 0 100 260 2000 2
```

截图后用 Read/View Image 工具查看图片进行视觉分析。

---

## 兼容链路：iframe 当前页提取

当只需要当前打开页面，或 `extract_axure_manifest.py` 无法读取蓝湖前端状态时，再使用这条链路。

### 第一步：检测当前平台和 CDP 端口

先判断运行环境，再检测端口：

```bash
python3 {SKILL_DIR}/scripts/check_cdp.py
```

- 输出 JSON → 端口已开启，跳到第三步
- 报错 `CDP_UNAVAILABLE` → 执行第二步

### 第二步：引导用户开启调试模式（仅端口未开启时）

先判断用户操作系统，然后给出对应的启动命令。

**检测平台方法**：通过 `check_cdp.py` 的错误信息无法判断平台，直接在对话中询问用户，或执行 `uname -s`（macOS 输出 `Darwin`）或检查 `%OS%`（Windows）。

向用户说明：

> 你的浏览器还没有开启远程调试模式，需要用特殊参数重启浏览器。
>
> **操作步骤：**
> 1. 先完全退出浏览器
> 2. 根据你的系统和浏览器，在终端/命令行执行以下命令启动

#### macOS Chrome
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 '--remote-allow-origins=*'
```

#### macOS Edge
```bash
"/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" --remote-debugging-port=9222 '--remote-allow-origins=*'
```

#### Windows Chrome
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=*
```

#### Windows Edge
```cmd
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --remote-allow-origins=*
```

**注意：**
- `--remote-allow-origins=*` 必须带，否则 WebSocket 403
- macOS 用引号包裹 `'*'` 防 zsh glob 展开报错，Windows 不需要
- 退出浏览器：macOS 用 `Cmd + Q`，Windows 用 Alt+F4 或任务栏右键关闭
- 启动后等几秒让页面恢复完再操作

### 第三步：打开用户给出的蓝湖链接（仅当链接尚未打开时）

如果用户直接给了蓝湖链接，或 `list_tabs.py` 找不到目标页面，但 CDP 端口已可用，先用 CDP 在调试浏览器中打开或复用该链接：

```bash
python3 {SKILL_DIR}/scripts/open_url.py "https://lanhuapp.com/xxx"
```

脚本输出 `ws:` 后，可直接进入第五步提取 iframe URL。

### 第四步：列出蓝湖标签页，找到蓝湖页面

```bash
# 只列出蓝湖相关页面
python3 {SKILL_DIR}/scripts/list_tabs.py

# 可选：按 URL 关键词进一步过滤
python3 {SKILL_DIR}/scripts/list_tabs.py lanhuapp
```

从结果中找到蓝湖标签页，记下 `ws:` 后面的 WebSocket URL。

### 第五步：提取蓝湖页面中的 Axure iframe URL

```bash
python3 {SKILL_DIR}/scripts/extract_lanhu_iframe.py "ws://localhost:9222/devtools/page/xxx"
```

目标：找到 `id` 为 `lan-mapping-iframe`、`src` 为 `https://axure-file.lanhuapp.com/xxx.html` 的 URL。

### 第六步：获取 Axure 当前页内容

直接请求上一步拿到的 Axure URL。Codex 环境优先用 `curl -sS`；如果当前环境提供 WebFetch，也可以使用 WebFetch。

```bash
curl -sS "https://axure-file.lanhuapp.com/xxx.html"
```

WebFetch 示例：

```
WebFetch URL: https://axure-file.lanhuapp.com/xxx.html
WebFetch Prompt: "提取这个 Axure 原型页面的所有文本内容，包括页面标题、标注、注释、按钮文案、字段名称、交互逻辑说明等。"
```

注意：iframe URL 往往只代表当前 Axure 页，且蓝湖左侧页面树切换后 iframe 地址不一定同步变化。完整需求分析优先使用“推荐高可靠操作链路”中的 manifest。

### 第七步（可选）：CDP 截图查看 UI 布局

```bash
# 全页截图
python3 {SKILL_DIR}/scripts/screenshot.py "ws://localhost:9222/devtools/page/xxx" /path/to/output.png

# 区域截图（x y width height scale）
python3 {SKILL_DIR}/scripts/screenshot.py "ws://localhost:9222/devtools/page/xxx" /path/to/output.png 0 100 260 2000 2
```

截图后用 Read 工具查看图片进行视觉分析。

### 额外工具：执行任意 JS

```bash
python3 {SKILL_DIR}/scripts/eval_js.py "ws://localhost:9222/devtools/page/xxx" "document.title"
```

---

## 脚本说明

| 脚本 | 用法 |
|------|------|
| `check_cdp.py` | 检测 9222 端口是否可用 |
| `open_url.py <url> [--wait seconds]` | 在 CDP 浏览器中打开或复用 URL，并输出页面 `ws:` |
| `list_tabs.py [keyword]` | 只列出蓝湖页面标签，可按 URL 关键词过滤 |
| `extract_lanhu_iframe.py <ws_url>` | 提取蓝湖页面的 iframe src 列表 |
| `extract_axure_manifest.py <ws_url> [keyword]` | 从蓝湖前端状态提取 Axure 最新版本 manifest，并输出页面树与每页静态资源 URL |
| `screenshot.py <ws_url> [output] [x y w h scale]` | 截图，支持全页或指定区域 |
| `eval_js.py <ws_url> <js>` | 在页面中执行 JS 并返回结果 |

依赖：`websocket-client`（`pip3 install websocket-client`）

---

## 注意事项

1. **编码问题**：CDP 传输中文可能乱码，核心信息优先走 Axure 静态资源 HTML/JSON，而非 DOM 提取
2. **跨域限制**：蓝湖的 Axure iframe 跨域，无法直接读 DOM，必须通过提取 URL + WebFetch 间接获取
3. **标签页索引不稳定**：每次 `open_url.py` 或 `list_tabs.py` 都要重新获取，不要缓存 WebSocket URL
4. **页面恢复延迟**：浏览器刚启动时标签页可能还在恢复，等 5-10 秒再操作
5. **多个蓝湖标签页**：蓝湖可能打开多个标签页，每个对应不同的 Axure 页面，按需处理
6. **跨平台兼容**：Python 脚本在 macOS 和 Windows 均可运行；启动浏览器命令需区分平台和浏览器（Chrome/Edge）
7. **浏览器路径**：Windows 默认安装路径如上，若用户自定义安装路径需手动调整
8. **复杂 JS 返回值**：`eval_js.py` 只打印 CDP `Runtime.evaluate` 的 `value` 字段。返回对象、数组等复杂结构时，表达式必须包 `JSON.stringify(...)`，否则可能输出空。
9. **蓝湖登录态提示**：如果页面出现“由于打开过分享页，用户状态发生变化...”等提示，不要立刻停止。先尝试读取 `window.doc.currentAxureData` 和 `window.axureSidebar`，很多情况下页面树和 Axure 静态资源仍可访问。
10. **iframe 不等于完整文档**：iframe HTML 常常只是当前页。完整分析优先读取最新版本 `jsonUrl` 中的 manifest，再按 `sitemap` 和 `pages` 批量抓取页面 HTML。
11. **蓝湖访问限制**：所有脚本入口都会校验目标是否属于 `lanhuapp.com` 或其子域名。`open_url.py` 会拒绝打开非蓝湖链接；`list_tabs.py` 只输出蓝湖标签；`eval_js.py`、`screenshot.py`、`extract_lanhu_iframe.py`、`extract_axure_manifest.py` 会拒绝非蓝湖标签页的 `ws_url`。

---

## 信息获取策略

| 需要的信息 | 获取方式 |
|-----------|---------|
| 蓝湖页面列表/树结构 | CDP 截图 + 视觉识别 |
| Axure 原型页面树与所有静态资源 | `extract_axure_manifest.py` |
| Axure 原型的标注/注释/交互说明 | manifest 页面 `htmlUrl` → `curl -sS`/WebFetch；当前页可用 iframe URL |
| UI 视觉布局确认 | CDP 截图 + Read 查看 |
| 中文文本内容 | Axure 静态 HTML/JSON 或 WebFetch（CDP 传中文可能乱码） |
