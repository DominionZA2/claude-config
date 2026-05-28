#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError:
    print("ERROR: Missing Python dependency: requests", file=sys.stderr)
    print("Install it with: python -m pip install requests", file=sys.stderr)
    sys.exit(1)


def load_jira_env():
    values = {
        "JIRA_URL": os.environ.get("JIRA_URL"),
        "JIRA_EMAIL": os.environ.get("JIRA_EMAIL"),
        "JIRA_TOKEN": os.environ.get("JIRA_TOKEN"),
    }

    env_file = Path.home() / ".claude" / "jira.env"
    if env_file.exists():
        text = env_file.read_text(encoding="utf-8")
        for key, value in re.findall(r'export\s+(JIRA_[A-Z]+)="([^"]*)"', text):
            if key in values:
                values[key] = value

    missing = [key for key, value in values.items() if not value]
    if missing:
        print("ERROR: Missing Jira environment variables:", file=sys.stderr)
        for key in missing:
            print(f"  - {key}", file=sys.stderr)
        print("Edit ~/.claude/jira.env and populate the missing values.", file=sys.stderr)
        sys.exit(1)

    return values


def jira_request(method, url, auth, **kwargs):
    response = requests.request(method, url, auth=auth, timeout=120, **kwargs)
    if response.status_code >= 400:
        print(f"ERROR: Jira request failed: {method} {url}", file=sys.stderr)
        print(f"Status: {response.status_code}", file=sys.stderr)
        print(response.text, file=sys.stderr)
        sys.exit(1)
    return response


def get_attachments(base_url, issue_key, auth):
    issue_url = f"{base_url}/rest/api/3/issue/{issue_key}"
    response = jira_request(
        "GET",
        issue_url,
        auth,
        params={"fields": "attachment"},
        headers={"Accept": "application/json"},
    )
    fields = response.json().get("fields", {}) or {}
    attachments = fields.get("attachment", []) or []
    return sorted(attachments, key=lambda item: item.get("created", ""))


def push_context(issue_key, task_folder, base_url, auth):
    if not task_folder.exists() or not task_folder.is_dir():
        print(f"ERROR: Task folder not found: {task_folder}", file=sys.stderr)
        sys.exit(1)

    local_files = sorted(path for path in task_folder.iterdir() if path.is_file())
    if not local_files:
        print(f"ERROR: No files found in task folder: {task_folder}", file=sys.stderr)
        sys.exit(1)

    existing = get_attachments(base_url, issue_key, auth)
    existing_by_name = {}
    for attachment in existing:
        existing_by_name.setdefault(attachment.get("filename"), []).append(attachment)

    uploaded = []
    for path in local_files:
        for attachment in existing_by_name.get(path.name, []):
            attachment_id = attachment.get("id")
            if attachment_id:
                delete_url = f"{base_url}/rest/api/3/attachment/{attachment_id}"
                jira_request("DELETE", delete_url, auth)

        upload_url = f"{base_url}/rest/api/3/issue/{issue_key}/attachments"
        with path.open("rb") as handle:
            response = jira_request(
                "POST",
                upload_url,
                auth,
                headers={"X-Atlassian-Token": "no-check", "Accept": "application/json"},
                files={"file": (path.name, handle, "application/octet-stream")},
            )

        data = response.json()[0]
        uploaded.append({
            "filename": data.get("filename"),
            "id": data.get("id"),
            "size": data.get("size"),
        })

    print(json.dumps({
        "action": "push",
        "issue": issue_key,
        "task_folder": str(task_folder),
        "uploaded": uploaded,
    }, indent=2))


def pull_context(issue_key, task_folder, base_url, auth):
    task_folder.mkdir(parents=True, exist_ok=True)
    attachments = get_attachments(base_url, issue_key, auth)

    downloaded = []
    for attachment in attachments:
        filename = attachment.get("filename")
        content_url = attachment.get("content")
        if not filename or not content_url:
            continue

        target = task_folder / Path(filename).name
        response = jira_request("GET", content_url, auth)
        target.write_bytes(response.content)
        downloaded.append({
            "filename": target.name,
            "id": attachment.get("id"),
            "size": len(response.content),
        })

    print(json.dumps({
        "action": "pull",
        "issue": issue_key,
        "task_folder": str(task_folder),
        "downloaded": downloaded,
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Sync .temp task context files with Jira attachments.")
    parser.add_argument("action", choices=["push", "pull"])
    parser.add_argument("issue_key")
    parser.add_argument("task_folder")
    args = parser.parse_args()

    env = load_jira_env()
    base_url = env["JIRA_URL"].rstrip("/")
    auth = HTTPBasicAuth(env["JIRA_EMAIL"], env["JIRA_TOKEN"])
    task_folder = Path(args.task_folder).resolve()

    if args.action == "push":
        push_context(args.issue_key, task_folder, base_url, auth)
    else:
        pull_context(args.issue_key, task_folder, base_url, auth)


if __name__ == "__main__":
    main()
