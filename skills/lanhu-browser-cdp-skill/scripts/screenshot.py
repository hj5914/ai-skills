#!/usr/bin/env python3
"""CDP 截图：全页面或指定区域"""
import json, base64, sys, os
try:
    import websocket
except ImportError:
    print("MISSING_DEP: pip3 install websocket-client", file=sys.stderr)
    sys.exit(1)

if len(sys.argv) < 2:
    print("USAGE: python3 screenshot.py <ws_url> [output_path] [x y w h scale]", file=sys.stderr)
    sys.exit(1)

ws_url = sys.argv[1]
output = sys.argv[2] if len(sys.argv) > 2 else "screenshot.png"
clip = None
if len(sys.argv) > 6:
    clip = {
        "x": int(sys.argv[3]),
        "y": int(sys.argv[4]),
        "width": int(sys.argv[5]),
        "height": int(sys.argv[6]),
        "scale": int(sys.argv[7]) if len(sys.argv) > 7 else 2
    }

ws = websocket.create_connection(ws_url, timeout=15)

ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
ws.recv()

params = {"format": "png"}
if clip:
    params["clip"] = clip

ws.send(json.dumps({"id": 2, "method": "Page.captureScreenshot", "params": params}))
resp = json.loads(ws.recv())

if "result" in resp and "data" in resp["result"]:
    img_data = base64.b64decode(resp["result"]["data"])
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    with open(output, "wb") as f:
        f.write(img_data)
    print(f"OK: {output} ({len(img_data)} bytes)")
else:
    print(f"ERROR: {json.dumps(resp, ensure_ascii=False)}", file=sys.stderr)
    sys.exit(1)

ws.close()
