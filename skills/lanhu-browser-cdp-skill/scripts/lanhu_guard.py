"""Lanhu-only access guard for local CDP helper scripts."""
import json
import urllib.parse
import urllib.request


CDP_BASE = "http://localhost:9222"
ALLOWED_HOST = "lanhuapp.com"


def fetch_cdp_json(path, timeout=5, method="GET"):
    req = urllib.request.Request(f"{CDP_BASE}{path}", method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def is_lanhu_url(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False

    host = (parsed.hostname or "").lower().rstrip(".")
    return host == ALLOWED_HOST or host.endswith(f".{ALLOWED_HOST}")


def require_lanhu_url(url, label="URL"):
    if not is_lanhu_url(url):
        raise PermissionError(f"{label} must be a Lanhu URL under {ALLOWED_HOST}")
    return url


def list_lanhu_page_tabs():
    tabs = fetch_cdp_json("/json", timeout=5)
    return [
        tab
        for tab in tabs
        if tab.get("type") == "page" and is_lanhu_url(tab.get("url", ""))
    ]


def require_lanhu_ws_target(ws_url):
    for tab in list_lanhu_page_tabs():
        if tab.get("webSocketDebuggerUrl") == ws_url:
            return tab
    raise PermissionError(
        "ws_url must belong to an open Lanhu tab under lanhuapp.com"
    )
