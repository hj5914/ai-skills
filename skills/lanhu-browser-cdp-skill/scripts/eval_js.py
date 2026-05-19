#!/usr/bin/env python3
"""CDP 执行 JS 并返回结果"""
import json, sys
from lanhu_guard import require_lanhu_ws_target

try:
    import websocket
except ImportError:
    print("MISSING_DEP: pip3 install websocket-client", file=sys.stderr)
    sys.exit(1)

if len(sys.argv) < 3:
    print("USAGE: python3 eval_js.py <ws_url> <js_expression>", file=sys.stderr)
    sys.exit(1)

ws_url = sys.argv[1]
js_expr = sys.argv[2]

try:
    require_lanhu_ws_target(ws_url)
    ws = websocket.create_connection(ws_url, timeout=15)
    try:
        ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {
            "expression": js_expr
        }}))
        resp = json.loads(ws.recv())
        result = resp.get("result", {}).get("result", {}).get("value", "")
        print(result if result else "")
    finally:
        ws.close()
except Exception as exc:
    print(f"LANHU_ONLY_ACCESS_DENIED: {exc}", file=sys.stderr)
    sys.exit(1)
