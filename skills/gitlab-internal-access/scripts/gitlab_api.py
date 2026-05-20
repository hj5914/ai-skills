#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import subprocess
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlsplit, urlunsplit
import urllib.error
import urllib.request


READ_ONLY_METHODS = {"GET", "HEAD"}
PROTECTED_HEADERS = {"private-token", "authorization"}


def infer_base_url_from_git_remote() -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return None

    if result.returncode != 0:
        return None

    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        remote_url = parts[1]
        lower_remote_url = remote_url.lower()
        if "gitlab" not in lower_remote_url:
            continue

        parsed = urlparse(remote_url)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"

        ssh_match = re.match(r"^(?:ssh://)?git@([^/:]+)[:/].+", remote_url)
        if ssh_match:
            return f"https://{ssh_match.group(1)}"

    return None


def set_query_param(url: str, name: str, value: str) -> str:
    parts = urlsplit(url)
    query = [(key, query_value) for key, query_value in parse_qsl(parts.query, keep_blank_values=True) if key != name]
    query.append((name, value))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def normalize_base_url(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    if base_url.endswith("/api/v4"):
        base_url = base_url[: -len("/api/v4")]
    return base_url


def resolve_base_url(cli_base_url: Optional[str]) -> Optional[str]:
    base_url = cli_base_url or os.environ.get("GITLAB_BASE_URL") or infer_base_url_from_git_remote()
    return normalize_base_url(base_url) if base_url else None


def parse_extra_headers(header_values: List[str]) -> Dict[str, str]:
    headers = {}
    for value in header_values:
        if ":" not in value:
            raise ValueError(f"Invalid header {value!r}; expected 'Name: value'.")
        name, header_value = value.split(":", 1)
        name = name.strip()
        if not name:
            raise ValueError("Header name cannot be empty.")
        if name.lower() in PROTECTED_HEADERS:
            raise ValueError(f"Header {name!r} cannot override GitLab credentials.")
        headers[name] = header_value.strip()
    return headers


def build_opener(no_proxy: bool, proxy_url: Optional[str]) -> urllib.request.OpenerDirector:
    if no_proxy and proxy_url:
        raise ValueError("--no-proxy and --proxy-url cannot be used together.")
    if no_proxy:
        return urllib.request.build_opener(urllib.request.ProxyHandler({}))
    if proxy_url:
        return urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
        )
    return urllib.request.build_opener()


def redact_sensitive(text: str, token: Optional[str], proxy_url: Optional[str]) -> str:
    if token:
        text = text.replace(token, "<redacted>")
    if proxy_url:
        text = text.replace(proxy_url, redact_url_credentials(proxy_url))
    return re.sub(r"(https?://)([^/@\s:]+):([^/@\s]+)@", r"\1<redacted>:<redacted>@", text)


def redact_url_credentials(url: str) -> str:
    return re.sub(r"(https?://)([^/@\s:]+):([^/@\s]+)@", r"\1<redacted>:<redacted>@", url)


def format_error(error: urllib.error.HTTPError) -> str:
    hints = {
        401: "Unauthorized. Check that GITLAB_TOKEN is set, valid, and has the required scope.",
        403: "Forbidden. The token is valid but lacks permission for this resource.",
        404: "Not found. Check the GitLab base URL, project/group path, and token access.",
        405: "Method not allowed. This skill is read-only and only supports GET/HEAD.",
    }
    return hints.get(error.code, f"HTTP error {error.code}.")


def print_missing_token_guidance() -> None:
    print("GITLAB_TOKEN_MISSING", file=sys.stderr)
    print("Set a GitLab access token in the GITLAB_TOKEN environment variable, then retry.", file=sys.stderr)
    print("Do not paste the token into chat or pass it as a command-line argument.", file=sys.stderr)
    print("Minimum scopes: read_api for API reads; read_repository may be needed for repository files.", file=sys.stderr)
    print("Permanent setup examples. Replace <your_gitlab_token> locally before running:", file=sys.stderr)
    print("  macOS/Linux zsh:  printf \"\\nexport GITLAB_TOKEN='%s'\\n\" '<your_gitlab_token>' >> ~/.zshrc && source ~/.zshrc", file=sys.stderr)
    print("  macOS/Linux bash: printf \"\\nexport GITLAB_TOKEN='%s'\\n\" '<your_gitlab_token>' >> ~/.bashrc && source ~/.bashrc", file=sys.stderr)
    print("  Windows PowerShell: [Environment]::SetEnvironmentVariable('GITLAB_TOKEN', '<your_gitlab_token>', 'User')", file=sys.stderr)
    print("  Restart the terminal after running the Windows PowerShell command.", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Call a GitLab API with the fixed GITLAB_TOKEN environment variable."
    )
    parser.add_argument("path", help="API path or full URL, e.g. /api/v4/groups/<group_path>/projects")
    parser.add_argument(
        "--base-url",
        help="GitLab root URL. If omitted, GITLAB_BASE_URL or git remote inference is used. Not required when path is a full URL.",
    )
    parser.add_argument("--method", type=str.upper, choices=sorted(READ_ONLY_METHODS), default="GET")
    parser.add_argument("--data", help="Rejected for safety: this read-only skill does not send request bodies.")
    parser.add_argument("--header", action="append", default=[], help="Extra read-only request header as 'Name: value'. Cannot override credentials.")
    parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout in seconds.")
    parser.add_argument("--no-proxy", action="store_true", help="Disable system/environment proxies and connect directly.")
    parser.add_argument("--proxy-url", help="Use this explicit proxy URL for HTTP and HTTPS requests.")
    parser.add_argument("--paginate", action="store_true", help="Follow GitLab X-Next-Page headers and combine JSON array responses. Only valid with GET.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON responses")
    args = parser.parse_args()

    method = args.method.upper()
    if method not in READ_ONLY_METHODS:
        print("READ_ONLY_METHOD_REQUIRED", file=sys.stderr)
        print("This skill only permits GET and HEAD requests.", file=sys.stderr)
        return 2
    if args.data:
        print("REQUEST_BODY_NOT_ALLOWED", file=sys.stderr)
        print("This skill is read-only and does not send request bodies.", file=sys.stderr)
        return 2
    if args.paginate and method == "HEAD":
        print("PAGINATION_REQUIRES_GET", file=sys.stderr)
        print("--paginate is only valid with GET requests.", file=sys.stderr)
        return 2

    token = os.environ.get("GITLAB_TOKEN")
    if not token:
        print_missing_token_guidance()
        return 2

    try:
        extra_headers = parse_extra_headers(args.header)
    except ValueError as error:
        print(f"HEADER_ERROR {error}", file=sys.stderr)
        return 2
    try:
        opener = build_opener(args.no_proxy, args.proxy_url)
    except ValueError as error:
        print(f"PROXY_ERROR {error}", file=sys.stderr)
        return 2

    if args.path.startswith(("http://", "https://")):
        url = args.path
    else:
        base_url = resolve_base_url(args.base_url)
        if not base_url:
            print("GITLAB_BASE_URL_MISSING", file=sys.stderr)
            print("Provide --base-url or set GITLAB_BASE_URL, or pass a full API URL.", file=sys.stderr)
            return 2
        url = base_url + "/" + args.path.lstrip("/")

    def fetch(page_url: str) -> Tuple[str, Optional[str]]:
        request = urllib.request.Request(page_url, method=method)
        request.add_header("PRIVATE-TOKEN", token)
        for name, value in extra_headers.items():
            request.add_header(name, value)
        with opener.open(request, timeout=args.timeout) as response:
            body = response.read().decode("utf-8")
            next_page = response.headers.get("X-Next-Page") or None
            return body, next_page

    try:
        if args.paginate:
            bodies = []
            page_url = url
            while page_url:
                body, next_page = fetch(page_url)
                bodies.append(body)
                if not next_page:
                    break
                page_url = set_query_param(url, "page", next_page)
            try:
                combined = []
                for body in bodies:
                    parsed = json.loads(body)
                    if not isinstance(parsed, list):
                        raise ValueError("Paginated response is not a JSON array.")
                    combined.extend(parsed)
                print(json.dumps(combined, ensure_ascii=False, indent=2) if args.pretty else json.dumps(combined, ensure_ascii=False))
            except Exception:
                print("\n".join(bodies))
            return 0

        body, _ = fetch(url)
        if method == "HEAD":
            return 0
        if args.pretty:
            try:
                print(json.dumps(json.loads(body), ensure_ascii=False, indent=2))
            except json.JSONDecodeError:
                print(body)
        else:
            print(body)
        return 0
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        print(f"HTTP_ERROR {error.code}", file=sys.stderr)
        print(format_error(error), file=sys.stderr)
        print(redact_sensitive(body, token, args.proxy_url), file=sys.stderr)
        return 1
    except Exception as error:
        print(f"REQUEST_ERROR {redact_sensitive(str(error), token, args.proxy_url)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
