#!/usr/bin/env python3
"""提取蓝湖页面中的 iframe src（主要是 Axure 原型 URL）"""
import json, sys
try:
    import websocket
except ImportError:
    print("MISSING_DEP: pip3 install websocket-client", file=sys.stderr)
    sys.exit(1)

if len(sys.argv) < 2:
    print("USAGE: python3 extract_lanhu_iframe.py <ws_url>", file=sys.stderr)
    sys.exit(1)

ws_url = sys.argv[1]
ws = websocket.create_connection(ws_url, timeout=15)

ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {
    "expression": """
    (function() {
        var iframes = Array.from(document.querySelectorAll('iframe')).map(function(f) {
            return {id: f.id, src: f.src, className: f.className};
        });
        return JSON.stringify(iframes);
    })()
    """
}}))
resp = json.loads(ws.recv())
result = resp.get("result", {}).get("result", {}).get("value", "")
print(result)
ws.close()
