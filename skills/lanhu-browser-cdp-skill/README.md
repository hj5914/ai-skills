# 蓝湖 Browser CDP Skill

一个用于读取蓝湖设计稿/原型页面的 Codex Skill。

它通过 Chrome DevTools Protocol (CDP) 连接本地 Chrome 或 Edge 浏览器，帮助 agent 定位蓝湖标签页、提取 Axure 原型资源，并按需截图进行 UI 分析。

访问边界：这个 skill 只允许访问 `lanhuapp.com` 及其子域名（例如 `axure-file.lanhuapp.com`）。脚本会拒绝打开、列出、读取、截图或执行 JS 于非蓝湖页面。

## 用途

- 检测本地浏览器 CDP 端口是否可用。
- 在 CDP 浏览器中打开或复用用户给出的蓝湖链接。
- 列出浏览器中已打开的蓝湖页面标签。
- 从蓝湖页面状态中提取 Axure manifest。
- 获取 Axure 页面树、页面 HTML、dataJs、mapping 资源地址。
- 提取当前蓝湖页面中的 Axure iframe 地址。
- 在蓝湖页面中执行 JS，读取可见文本或页面状态。
- 通过 CDP 截取整页或指定区域截图。

## 适合场景

- 需要让 agent 读取蓝湖设计稿或原型页面。
- 需要从 Axure 原型中提取页面树、HTML 或资源地址。
- 需要通过本地浏览器页面状态辅助 UI 分析。
- 需要截图并让 agent 基于页面视觉结果继续判断。

## 不适合场景

- 没有本地浏览器访问权限的远程环境。
- 不能开启 Chrome / Edge 远程调试端口的环境。
- 需要访问非蓝湖页面的场景。

## 安装/依赖

依赖：

- Python 3
- `websocket-client`

如果你只把仓库地址告诉 agent，可以使用下面这段说明：

```text
请从 https://github.com/hj5914/ai-skills 安装 Codex skill。
这个 skill 的安装路径为 `skills/lanhu-browser-cdp-skill`。
安装后请安装 Python 依赖 `websocket-client`，然后重启 Codex。
```

使用 Codex 自带的 skill installer 时，可以执行：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo hj5914/ai-skills \
  --path skills/lanhu-browser-cdp-skill
```

安装依赖：

```bash
python3 -m pip install -r ~/.codex/skills/lanhu-browser-cdp-skill/requirements.txt
```

手动安装：

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/hj5914/ai-skills.git /tmp/ai-skills
cp -R /tmp/ai-skills/skills/lanhu-browser-cdp-skill ~/.codex/skills/lanhu-browser-cdp-skill
python3 -m pip install -r ~/.codex/skills/lanhu-browser-cdp-skill/requirements.txt
```

安装完成后需要重启 Codex，新的 skill 才会被加载。

## 使用/验证

脚本需要连接到开启远程调试端口的浏览器。启动前请先完全退出浏览器。

macOS Chrome：

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 '--remote-allow-origins=*'
```

macOS Edge：

```bash
"/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" --remote-debugging-port=9222 '--remote-allow-origins=*'
```

Windows Chrome：

```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=*
```

Windows Edge：

```cmd
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --remote-allow-origins=*
```

快速验证：

```bash
python3 scripts/check_cdp.py
python3 scripts/open_url.py "https://lanhuapp.com/xxx"
python3 scripts/list_tabs.py lanhuapp
```

如果 CDP 可用，`open_url.py` 会打开或复用页面并打印 WebSocket URL；`list_tabs.py` 会打印匹配页面的 WebSocket URL。完整使用流程见 [SKILL.md](SKILL.md)。

## 文件说明

```text
SKILL.md
  Codex Skill 主说明。

requirements.txt
  Python 依赖。

scripts/check_cdp.py
  检测 CDP 端口。

scripts/open_url.py
  在 CDP 浏览器中打开或复用 URL。

scripts/list_tabs.py
  只列出蓝湖页面标签。

scripts/extract_axure_manifest.py
  提取 Axure manifest。

scripts/extract_lanhu_iframe.py
  提取蓝湖页面中的 Axure iframe。

scripts/eval_js.py
  在页面中执行 JavaScript。

scripts/screenshot.py
  通过 CDP 截图。
```

## 备注

- `--remote-allow-origins=*` 必须带上，否则 WebSocket 连接可能返回 403。
- macOS 下建议用 `'*'` 包住星号，避免 zsh glob 展开报错。
- CDP 是本地浏览器调试接口，只应在可信环境中开启。
