#!/usr/bin/env python3
"""Open or reuse a URL in the local CDP browser and print its target."""
import argparse
import json
import sys
import time
import urllib.error
import urllib.parse

from lanhu_guard import fetch_cdp_json, require_lanhu_url


def fetch_json(path, timeout=5, method="GET"):
    return fetch_cdp_json(path, timeout=timeout, method=method)


def list_page_tabs():
    tabs = fetch_json("/json", timeout=5)
    return [tab for tab in tabs if tab.get("type") == "page"]


def normalize_url(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("URL must start with http:// or https://")
    return require_lanhu_url(urllib.parse.urlunparse(parsed))


def same_url(left, right):
    return left.rstrip("/") == right.rstrip("/")


def find_existing_tab(url):
    for tab in list_page_tabs():
        tab_url = tab.get("url", "")
        if same_url(tab_url, url):
            return tab
    return None


def create_tab(url):
    encoded_url = urllib.parse.quote(url, safe="")
    try:
        return fetch_json(f"/json/new?{encoded_url}", timeout=10, method="PUT")
    except urllib.error.HTTPError as exc:
        # Older Chromium builds accepted GET for this endpoint.
        if exc.code not in (405, 501):
            raise
    return fetch_json(f"/json/new?{encoded_url}", timeout=10)


def wait_for_tab(target_id, url, timeout):
    deadline = time.time() + timeout
    last_match = None
    while time.time() < deadline:
        for tab in list_page_tabs():
            if target_id and tab.get("id") == target_id:
                return tab
            if same_url(tab.get("url", ""), url):
                last_match = tab
        if last_match:
            return last_match
        time.sleep(0.5)
    return last_match


def print_tab(tab):
    title = tab.get("title", "")
    url = tab.get("url", "")
    ws = tab.get("webSocketDebuggerUrl", "")
    print(title[:80])
    print(f"    {url}")
    if ws:
        print(f"    ws: {ws}")


def main():
    parser = argparse.ArgumentParser(
        description="Open or reuse a URL in the local CDP browser."
    )
    parser.add_argument("url", help="URL to open, such as a Lanhu share link")
    parser.add_argument(
        "--wait",
        type=float,
        default=10.0,
        help="seconds to wait for the new tab target, default: 10",
    )
    args = parser.parse_args()

    try:
        url = normalize_url(args.url)
        existing = find_existing_tab(url)
        if existing:
            print("REUSED_TAB")
            print_tab(existing)
            return

        created = create_tab(url)
        tab = wait_for_tab(created.get("id"), url, args.wait)
        if not tab:
            print("OPENED_TAB_BUT_NOT_LISTED", file=sys.stderr)
            print(json.dumps(created, ensure_ascii=False, indent=2), file=sys.stderr)
            sys.exit(1)

        print("OPENED_TAB")
        print_tab(tab)
    except Exception as exc:
        print(f"CDP_OPEN_URL_FAILED: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
