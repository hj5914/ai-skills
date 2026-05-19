#!/usr/bin/env python3
"""Extract Lanhu Axure manifest URLs from an open Lanhu tab.

Usage:
  python3 extract_axure_manifest.py <ws_url> [keyword]

The optional keyword filters flattened sitemap paths, for example:
  python3 extract_axure_manifest.py ws://... 应用端
"""
import json
import sys
import urllib.request

from lanhu_guard import require_lanhu_url, require_lanhu_ws_target

try:
    import websocket
except ImportError:
    print("MISSING_DEP: pip3 install websocket-client", file=sys.stderr)
    sys.exit(1)


AXURE_FILE_HOST = "https://axure-file.lanhuapp.com/"


def cdp_eval(ws_url, expression):
    require_lanhu_ws_target(ws_url)
    ws = websocket.create_connection(ws_url, timeout=15)
    try:
        ws.send(json.dumps({
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {"expression": expression},
        }))
        resp = json.loads(ws.recv())
    finally:
        ws.close()

    if "exceptionDetails" in resp.get("result", {}):
        details = resp["result"]["exceptionDetails"]
        text = details.get("text", "Runtime exception")
        raise RuntimeError(text)

    result = resp.get("result", {}).get("result", {})
    if "value" in result:
        return result["value"]
    return ""


def fetch_json(url):
    require_lanhu_url(url, "manifest URL")
    with urllib.request.urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def flatten_sitemap(nodes, pages, ancestors=None):
    ancestors = ancestors or []
    rows = []
    for node in nodes:
        name = node.get("pageName", "")
        path = ancestors + [name]
        page_url = node.get("url", "")
        page = pages.get(page_url, {}) if page_url else {}

        row = {
            "name": name,
            "type": node.get("type", ""),
            "id": node.get("id", ""),
            "path": " / ".join([p for p in path if p]),
            "sourceUrl": page_url,
        }

        html_md5 = page.get("html", {}).get("sign_md5")
        data_md5 = page.get("dataJs", {}).get("sign_md5")
        mapping_md5 = page.get("mapping_md5")
        if html_md5:
            row["htmlUrl"] = AXURE_FILE_HOST + html_md5
        if data_md5:
            row["dataJsUrl"] = AXURE_FILE_HOST + data_md5
        if mapping_md5:
            row["mappingUrl"] = AXURE_FILE_HOST + mapping_md5

        rows.append(row)
        rows.extend(flatten_sitemap(node.get("children", []), pages, path))
    return rows


def main():
    if len(sys.argv) < 2:
        print("USAGE: python3 extract_axure_manifest.py <ws_url> [keyword]", file=sys.stderr)
        sys.exit(1)

    ws_url = sys.argv[1]
    keyword = sys.argv[2] if len(sys.argv) > 2 else ""

    state_expr = r"""
    JSON.stringify((function() {
      var current = window.doc && window.doc.currentAxureData;
      var selected = window.doc && (window.doc.selectAxurePageData || window.doc.selectPage);
      return {currentAxureData: current || null, selectedPage: selected || null};
    })())
    """
    raw_state = cdp_eval(ws_url, state_expr)
    if not raw_state:
        print("NO_AXURE_STATE: window.doc.currentAxureData not found", file=sys.stderr)
        sys.exit(1)

    state = json.loads(raw_state)
    current = state.get("currentAxureData") or {}
    versions = current.get("versions") or []
    if not versions:
        print("NO_AXURE_VERSIONS: currentAxureData.versions is empty", file=sys.stderr)
        sys.exit(1)

    latest = versions[0]
    json_url = latest.get("jsonUrl")
    if not json_url:
        print("NO_JSON_URL: latest version has no jsonUrl", file=sys.stderr)
        sys.exit(1)
    require_lanhu_url(json_url, "latest version jsonUrl")

    manifest = fetch_json(json_url)
    rows = flatten_sitemap(manifest.get("sitemap", {}).get("rootNodes", []), manifest.get("pages", {}))
    if keyword:
        rows = [row for row in rows if keyword in row.get("path", "")]

    output = {
        "document": {
            "name": current.get("name", ""),
            "id": current.get("id", ""),
            "latestVersionId": latest.get("id", ""),
            "latestVersionInfo": latest.get("versionInfo", ""),
            "jsonUrl": json_url,
            "selectedPage": state.get("selectedPage"),
        },
        "pages": rows,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
