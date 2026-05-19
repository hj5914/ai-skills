#!/usr/bin/env python3
"""列出 CDP 蓝湖标签页，可选按关键词过滤"""
import sys

from lanhu_guard import list_lanhu_page_tabs

keyword = sys.argv[1] if len(sys.argv) > 1 else ""

try:
    tabs = list_lanhu_page_tabs()
except Exception as e:
    print(f"CDP_UNAVAILABLE: {e}", file=sys.stderr)
    sys.exit(1)

found = False
for i, tab in enumerate(tabs):
    url = tab.get("url", "")
    title = tab.get("title", "")
    if keyword and keyword not in url:
        continue
    found = True
    print(f"[{i}] {title[:60]}")
    print(f"    {url[:150]}")
    ws = tab.get("webSocketDebuggerUrl", "")
    if ws:
        print(f"    ws: {ws}")
    print()

if not found and keyword:
    print(f"NO_MATCH: no Lanhu tab contains '{keyword}'", file=sys.stderr)
    sys.exit(1)
elif not found:
    print("NO_LANHU_PAGES: no Lanhu page tabs found", file=sys.stderr)
    sys.exit(1)
