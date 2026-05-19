#!/usr/bin/env python3
"""检查 CDP 端口是否可用"""
import urllib.request, json, sys

try:
    resp = urllib.request.urlopen("http://localhost:9222/json/version", timeout=2)
    data = json.loads(resp.read())
    print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"CDP_UNAVAILABLE: {e}", file=sys.stderr)
    sys.exit(1)
