#!/usr/bin/env python3
"""列出 CDP 所有标签页，可选按关键词过滤"""
import urllib.request, json, sys, urllib.parse

keyword = sys.argv[1] if len(sys.argv) > 1 else ""

try:
    resp = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
    tabs = json.loads(resp.read())
except Exception as e:
    print(f"CDP_UNAVAILABLE: {e}", file=sys.stderr)
    sys.exit(1)

found = False
for i, tab in enumerate(tabs):
    if tab.get("type") != "page":
        continue
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
    print(f"NO_MATCH: no tab contains '{keyword}'", file=sys.stderr)
    sys.exit(1)
elif not found:
    print("NO_PAGES: no page tabs found", file=sys.stderr)
    sys.exit(1)
