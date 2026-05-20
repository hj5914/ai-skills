---
name: gitlab-internal-access
description: Access a user-provided GitLab instance using the fixed GITLAB_TOKEN environment variable. Use when Codex needs read-only GitLab API access to list/search projects, inspect repositories, read files, branches, merge requests, pipelines, jobs, users, groups, or other GitLab resources. The GitLab base URL is required and must come from the user, environment, repository remote, AI context, or another trustworthy source; group and project paths are optional and task-dependent.
---

# GitLab Internal Access

## Core Rules

- Use `GITLAB_TOKEN` from the environment. Never print the token, write it into files, or paste it into commands literally.
- `GITLAB_TOKEN` is the only supported token environment variable name. Do not invent alternate names and do not pass token values through CLI arguments.
- Do not assume or hardcode a GitLab base URL. Resolve it using the priority order below.
- If the GitLab base URL is unavailable and the task requires API access, ask the user for it before making the request.
- Do not assume whether a proxy is required. Start with system/environment proxy behavior unless the user or local context says direct access or a specific proxy is required.
- Prefer GitLab API calls over browser DOM scraping. Use browser/CDP only as a fallback for read-only page inspection.
- This skill is read-only. Do not create, update, trigger, approve, merge, retry, or delete GitLab resources.

## GitLab URL Resolution

Resolve the GitLab base URL in this order:

1. GitLab base URL explicitly provided by the user in the current conversation.
2. `GITLAB_BASE_URL` from the environment.
3. GitLab host inferred from the current repository's `git remote -v` when the remote URL clearly appears to be GitLab.
4. A trustworthy AI context or local project configuration.
5. Ask the user for the GitLab base URL.

Use the GitLab root URL, not an API URL. Good: `https://gitlab.example.com`. Avoid: `https://gitlab.example.com/api/v4`.
`scripts/gitlab_api.py` accepts `--base-url`, reads `GITLAB_BASE_URL`, and can infer the host from `git remote -v` when run inside a cloned repository whose remote URL clearly appears to be GitLab.
Remote inference is conservative. For self-hosted GitLab domains that do not visibly contain `gitlab`, use `--base-url` or `GITLAB_BASE_URL`.

## Proxy Handling

Some GitLab instances are only reachable through a proxy, while others fail unless the request bypasses proxies.

- Default behavior: use the system/environment proxy configuration. This includes standard variables such as `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, and `NO_PROXY`.
- If the user says direct access is required, or a proxy breaks access, use `scripts/gitlab_api.py --no-proxy`.
- If the user provides a proxy for this request, use `scripts/gitlab_api.py --proxy-url "<proxy_url>"`.
- If an internal GitLab host should bypass a configured system proxy, suggest adding the host to `NO_PROXY` or use `--no-proxy` for the single request.
- Do not hardcode proxy addresses in the skill. Get proxy requirements from the user, environment, or trustworthy local context.
- Treat proxy URLs with embedded credentials as sensitive. Do not print or commit them.

## Credential Safety

- Never reveal the value of `GITLAB_TOKEN` in chat, command output, logs, files, commits, comments, PR descriptions, issue bodies, screenshots, or copied snippets.
- Never ask the user to paste a token value into chat. Ask them to set `GITLAB_TOKEN` in their environment instead.
- Never pass the token value as a GitLab API CLI argument, URL query parameter, JSON body field, or request content. Reference it only as `$GITLAB_TOKEN` or read it from `os.environ`.
- If giving a local one-line setup command, keep the token as a placeholder and tell the user to replace it only on their own machine. Warn that commands containing real tokens may be stored in shell history.
- Before sharing command output, inspect it for token-like values and redact any credential material as `<redacted>`.
- If a command could echo environment variables, shell traces, request headers, or verbose HTTP logs, avoid it unless the output is filtered so credentials cannot appear.
- If a token is accidentally exposed, stop using it and tell the user it should be rotated.

## Quick Check

Verify the token exists without revealing it:

```bash
if [ -n "$GITLAB_TOKEN" ]; then echo GITLAB_TOKEN_PRESENT; else echo GITLAB_TOKEN_MISSING; fi
```

## Missing Token Guidance

When `GITLAB_TOKEN` is missing:

- Do not ask the user to paste the token into chat.
- Tell the user to create or locate a GitLab personal, project, or group access token with read-only scope.
- Give the user one of these complete local setup commands, and tell them to replace `<your_gitlab_token>` locally before running it. Mention that commands containing real tokens may be stored in shell history.

macOS/Linux zsh:

```bash
printf "\nexport GITLAB_TOKEN='%s'\n" '<your_gitlab_token>' >> ~/.zshrc && source ~/.zshrc
```

macOS/Linux bash:

```bash
printf "\nexport GITLAB_TOKEN='%s'\n" '<your_gitlab_token>' >> ~/.bashrc && source ~/.bashrc
```

Windows PowerShell:

```powershell
[Environment]::SetEnvironmentVariable('GITLAB_TOKEN', '<your_gitlab_token>', 'User')
```

Tell Windows users to restart their terminal after running the PowerShell command.
- Mention minimum scopes: `read_api` for API reads; `read_repository` may be needed for repository files.
- Ask the user to retry after setting the environment variable, or to run the quick check above.

## Common API Tasks

Use `scripts/gitlab_api.py` for repeatable read-only calls:

```bash
python3 scripts/gitlab_api.py \
  --base-url "<gitlab_base_url>" \
  "/api/v4/projects?per_page=100" \
  --paginate \
  --pretty
```

On Windows, use `py -3` or `python` instead of `python3` if `python3` is unavailable.

Force direct access without proxies:

```bash
python3 scripts/gitlab_api.py \
  --base-url "<gitlab_base_url>" \
  --no-proxy \
  "/api/v4/projects?per_page=100" \
  --pretty
```

Use a specific proxy for one request:

```bash
python3 scripts/gitlab_api.py \
  --base-url "<gitlab_base_url>" \
  --proxy-url "<proxy_url>" \
  "/api/v4/projects?per_page=100" \
  --pretty
```

List accessible projects without a group:

```bash
python3 scripts/gitlab_api.py \
  --base-url "<gitlab_base_url>" \
  "/api/v4/projects?per_page=100" \
  --paginate \
  --pretty
```

List projects in a group:

```bash
curl -sS \
  -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "<gitlab_base_url>/api/v4/groups/<group_path>/projects?include_subgroups=true&per_page=100&simple=true"
```

List project names, default branches, and URLs:

```bash
curl -sS \
  -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "<gitlab_base_url>/api/v4/groups/<group_path>/projects?include_subgroups=true&per_page=100&simple=true" \
  | jq -r '.[] | [.name, .default_branch, .web_url] | @tsv'
```

Get project details:

```bash
python3 scripts/gitlab_api.py \
  --base-url "<gitlab_base_url>" \
  "/api/v4/projects/<url_encoded_project_path>" \
  --pretty
```

List branches:

```bash
python3 scripts/gitlab_api.py \
  --base-url "<gitlab_base_url>" \
  "/api/v4/projects/<url_encoded_project_path>/repository/branches?per_page=100" \
  --paginate \
  --pretty
```

Read a repository file:

```bash
python3 scripts/gitlab_api.py \
  --base-url "<gitlab_base_url>" \
  "/api/v4/projects/<url_encoded_project_path>/repository/files/<url_encoded_file_path>?ref=<branch>" \
  --pretty
```

GitLab returns repository file content as base64 in the `content` field. Decode it before presenting file contents to the user.

Search projects:

```bash
python3 scripts/gitlab_api.py \
  --base-url "<gitlab_base_url>" \
  "/api/v4/projects?search=<query>&per_page=100" \
  --paginate \
  --pretty
```

List merge requests:

```bash
python3 scripts/gitlab_api.py \
  --base-url "<gitlab_base_url>" \
  "/api/v4/projects/<url_encoded_project_path>/merge_requests?state=opened&per_page=100" \
  --paginate \
  --pretty
```

List pipelines or jobs:

```bash
python3 scripts/gitlab_api.py \
  --base-url "<gitlab_base_url>" \
  "/api/v4/projects/<url_encoded_project_path>/pipelines?per_page=100" \
  --paginate \
  --pretty
```

```bash
python3 scripts/gitlab_api.py \
  --base-url "<gitlab_base_url>" \
  "/api/v4/projects/<url_encoded_project_path>/pipelines/<pipeline_id>/jobs?per_page=100" \
  --paginate \
  --pretty
```

## Pagination

- GitLab list APIs are often paginated. Use `per_page=100` for quick reads.
- When the user asks for a complete list, follow `X-Next-Page` until it is empty.
- Prefer `scripts/gitlab_api.py --paginate` for paginated JSON array responses.
- If only a quick existence check or sample is needed, fetch one page and say so.

## Read-Only Boundary

- Only `GET` and `HEAD` requests are allowed.
- `--paginate` is only valid with `GET`.
- Do not use this skill to create issues, open or merge merge requests, add comments, approve reviews, retry or trigger pipelines, modify files, update settings, or delete resources.
- If the user asks for a write operation, explain that this skill is read-only and ask them to use a separate write-capable workflow.

## Token Scopes

- Listing and reading GitLab API resources usually requires `read_api`.
- Reading repository files may require `read_repository`.
- This skill does not need write scopes because write operations are not allowed.

## Troubleshooting

- `401 Unauthorized`: `GITLAB_TOKEN` is missing, expired, revoked, or lacks required scope. For listing projects, `read_api` is sufficient; for reading repository files, use `read_repository` as needed.
- `404 Not Found`: check the GitLab base URL, resource path, URL encoding, and token access. For group/project endpoints, confirm the group or project path with the user or available context.
- Proxy or network failures: retry with the opposite proxy mode when appropriate: default/system proxy, `--no-proxy`, or `--proxy-url "<proxy_url>"`. If sandboxing blocks private network access, request permission to run the same read-only command outside the sandbox.
- `jq` missing: return raw JSON or use Python JSON parsing.
