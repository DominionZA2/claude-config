#!/usr/bin/env python3
"""
Thin wrapper over the Jira search API.

Whatever JQL string you pass in is sent to /rest/api/3/search/jql unchanged so you
can iterate on queries quickly without reimplementing auth/printing glue.

Environment variables (optional convenience):
  - JIRA_BASE_URL or JIRA_URL
  - JIRA_EMAIL
  - JIRA_API_TOKEN or JIRA_TOKEN
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Dict, Iterable, List, Optional


class JiraError(RuntimeError):
    """Raised when the JIRA API returns a non-success response."""


def _env(key: str) -> Optional[str]:
    value = os.environ.get(key)
    return value.strip() if value else None


def _env_any(*keys: str) -> Optional[str]:
    for key in keys:
        value = _env(key)
        if value:
            return value
    return None


def build_jql(args: argparse.Namespace) -> str:
    if args.jql:
        return args.jql
    raise JiraError("Missing JQL. Pass --jql so the script can relay it unchanged.")


def build_request_payload(args: argparse.Namespace, jql: str) -> Dict[str, object]:
    fields = args.fields or ["key", "summary", "status", "assignee", "updated"]
    payload: Dict[str, object] = {
        "jql": jql,
        "maxResults": args.max_results,
        "fields": fields,
    }
    if args.expand:
        payload["expand"] = args.expand
    return payload


def _auth_header(email: str, token: str) -> str:
    auth = f"{email}:{token}".encode("utf-8")
    return base64.b64encode(auth).decode("ascii")


def call_jira_search(
    base_url: str, email: str, token: str, payload: Dict[str, object]
) -> Dict[str, object]:
    # Atlassian removed the legacy /search endpoint (CHANGE-2046). Use the new JQL endpoint.
    url = base_url.rstrip("/") + "/rest/api/3/search/jql"
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Basic {_auth_header(email, token)}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request) as response:
            body = response.read()
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise JiraError(f"JIRA API error ({exc.code}): {detail}") from exc
    except urllib.error.URLError as exc:
        raise JiraError(f"Failed to contact JIRA: {exc.reason}") from exc


def summarize_issue(issue: Dict[str, object]) -> str:
    fields = issue.get("fields", {})
    summary = (fields.get("summary") or "").strip()
    status = (
        (fields.get("status") or {}).get("name")
        if isinstance(fields.get("status"), dict)
        else ""
    )
    assignee = ""
    if isinstance(fields.get("assignee"), dict):
        assignee = fields["assignee"].get("displayName") or ""
    updated = (fields.get("updated") or "")[:19].replace("T", " ")
    key = issue.get("key", "")
    return f"{key:<12} | {status:<15} | {assignee:<25} | {updated:<19} | {summary}"


def print_table(issues: Iterable[Dict[str, object]]) -> None:
    header = "Key          | Status          | Assignee                 | Updated             | Summary"
    print(header)
    print("-" * len(header))
    for issue in issues:
        print(summarize_issue(issue))


def print_json(data: Dict[str, object]) -> None:
    print(json.dumps(data, indent=2))


def validate_credentials(base_url: Optional[str], email: Optional[str], token: Optional[str]) -> None:
    missing = [
        name
        for name, value in (
            ("base-url", base_url),
            ("email", email),
            ("token", token),
        )
        if not value
    ]
    if missing:
        joined = ", ".join(f"--{item}" for item in missing)
        raise JiraError(f"Missing required arguments: {joined}.")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Wrapper around Jira's /rest/api/3/search/jql endpoint."
    )
    parser.add_argument("--base-url", default=_env_any("JIRA_BASE_URL", "JIRA_URL"), help="JIRA instance URL, e.g. https://example.atlassian.net.")
    parser.add_argument("--email", default=_env("JIRA_EMAIL"), help="Account email for the API token.")
    parser.add_argument("--token", default=_env_any("JIRA_API_TOKEN", "JIRA_TOKEN"), help="API token (https://id.atlassian.com/manage-profile/security/api-tokens).")
    parser.add_argument("--jql", required=True, help="Exact JQL string to relay to Jira.")
    parser.add_argument("--max-results", type=int, default=100, help="Upper bound on returned issues.")
    parser.add_argument("--fields", nargs="+", help="Fields to request from the API.")
    parser.add_argument("--expand", nargs="+", help="Optional expand params.")
    parser.add_argument("--output", choices=["table", "json"], default="table", help="Pretty-print results as a table or emit raw JSON.")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved JQL and exit without calling the API.")
    parser.add_argument("--verbose", action="store_true", help="Echo the payload for debugging.")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    base_url = args.base_url
    email = args.email
    token = args.token
    validate_credentials(base_url, email, token)

    jql = build_jql(args)
    if args.verbose or args.dry_run:
        print(f"[jira-fetch] JQL: {jql}")

    if args.dry_run:
        return 0

    payload = build_request_payload(args, jql)

    try:
        response = call_jira_search(base_url, email, token, payload)
    except JiraError as exc:
        print(f"[jira-fetch] {exc}", file=sys.stderr)
        return 1

    issues = response.get("issues", [])
    if args.output == "json":
        print_json(response)
    else:
        print_table(issues)
        print()
        print(f"Total issues: {response.get('total', len(issues))}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
