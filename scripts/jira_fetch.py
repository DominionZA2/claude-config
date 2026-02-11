#!/usr/bin/env python3
import sys
import subprocess
import os
import json
from pathlib import Path
import site
if not site.ENABLE_USER_SITE:
    site.ENABLE_USER_SITE = True
    site.addsitedir(site.getusersitepackages())


def install_dependencies(metadata_only=False):
    """Self-install required dependencies if not already installed."""
    packages_to_check = {
        'atlassian-python-api': 'atlassian'
    }
    if not metadata_only:
        packages_to_check['requests'] = 'requests'

    for package_name, import_name in packages_to_check.items():
        try:
            __import__(import_name)
        except ImportError:
            print(f"Installing {package_name}...", file=sys.stderr)
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', package_name])


def check_env_vars():
    """Check for required environment variables in system environment."""
    required_vars = ['JIRA_URL', 'JIRA_EMAIL', 'JIRA_TOKEN']

    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if not value or value.strip() == '':
            missing_vars.append(var)

    if missing_vars:
        print("ERROR: Missing required environment variables:", file=sys.stderr)
        for var in missing_vars:
            print(f"  - {var}", file=sys.stderr)
        print("\nEnsure ~/.claude/jira.env is sourced before running this script:", file=sys.stderr)
        print("  source ~/.claude/jira.env", file=sys.stderr)
        print("\nOr edit ~/.claude/jira.env and set:", file=sys.stderr)
        print('  export JIRA_URL="https://cosoft.atlassian.net"', file=sys.stderr)
        print('  export JIRA_EMAIL="your-email@example.com"', file=sys.stderr)
        print('  export JIRA_TOKEN="your-api-token"', file=sys.stderr)
        print("\nGet your Jira API token here: https://id.atlassian.com/manage-profile/security/api-tokens", file=sys.stderr)
        sys.exit(1)


def fetch_issue(issue_key, download_dir, metadata_only=False):
    """
    Fetch Jira issue data. Attachments download only when metadata_only is False.
    """
    try:
        from atlassian import Jira

        jira = Jira(
            url=os.environ['JIRA_URL'],
            username=os.environ['JIRA_EMAIL'],
            password=os.environ['JIRA_TOKEN'],
            cloud=True
        )

        issue = jira.issue(
            issue_key,
            fields='summary,status,description,comment,attachment,issuelinks',
            expand='renderedFields'
        )

        if not issue:
            print("ERROR: Failed to fetch issue - empty response", file=sys.stderr)
            sys.exit(1)

        fields = issue.get('fields', {}) or {}
        summary = fields.get('summary', '')
        description = fields.get('description', '')
        status = fields.get('status', {}).get('name', '')

        comments = fields.get('comment', {})
        if isinstance(comments, dict):
            comments = comments.get('comments', [])
        elif not isinstance(comments, list):
            comments = []

        download_path = Path(download_dir)
        download_path.mkdir(parents=True, exist_ok=True)

        attachments_raw = fields.get('attachment', []) or []
        if not isinstance(attachments_raw, list):
            attachments_raw = []

        issue_links_raw = fields.get('issuelinks', []) or []
        linked_issues = []
        for link in issue_links_raw:
            link_type = link.get('type', {}).get('name', '')
            inward_desc = link.get('type', {}).get('inward', '')
            outward_desc = link.get('type', {}).get('outward', '')
            if 'inwardIssue' in link:
                linked = link['inwardIssue']
                direction = 'inward'
                relationship = inward_desc or link_type
            elif 'outwardIssue' in link:
                linked = link['outwardIssue']
                direction = 'outward'
                relationship = outward_desc or link_type
            else:
                continue

            linked_key = linked.get('key')
            linked_summary = linked.get('fields', {}).get('summary', '')
            linked_status = linked.get('fields', {}).get('status', {}).get('name', '')
            linked_issues.append({
                'key': linked_key,
                'summary': linked_summary,
                'status': linked_status,
                'direction': direction,
                'relationship': relationship,
                'url': f"{os.environ['JIRA_URL'].rstrip('/')}/browse/{linked_key}" if linked_key else None
            })

        remote_links = []
        try:
            remote_links_data = jira.issue_remote_links(issue_key)
            for link in remote_links_data:
                remote_links.append({
                    'title': link.get('object', {}).get('title', ''),
                    'url': link.get('object', {}).get('url', ''),
                    'relationship': link.get('relationship', '')
                })
        except Exception:
            pass

        attachments = []
        for attachment in attachments_raw:
            if not isinstance(attachment, dict):
                continue

            filename = attachment.get('filename', '')
            size = attachment.get('size', 0)
            content_url = attachment.get('content', '')
            attachment_id = attachment.get('id', '')

            download_info = {
                'filename': filename,
                'size': size,
                'content_url': content_url,
                'attachment_id': attachment_id,
                'downloaded': False,
                'file_path': None,
                'error': None
            }

            if not metadata_only and content_url and filename:
                try:
                    import requests
                    from requests.auth import HTTPBasicAuth

                    target_file = download_path / f"{issue_key}-{filename}"
                    response = requests.get(
                        content_url,
                        auth=HTTPBasicAuth(os.environ['JIRA_EMAIL'], os.environ['JIRA_TOKEN']),
                        stream=True,
                        timeout=30
                    )
                    response.raise_for_status()

                    with open(target_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    download_info['downloaded'] = True
                    download_info['file_path'] = str(target_file)
                except Exception as e:
                    download_info['error'] = str(e)

            attachments.append(download_info)

        result = {
            'issue_key': issue_key,
            'summary': summary,
            'description': description,
            'comments': [
                {
                    'author': c.get('author', {}).get('displayName', ''),
                    'created': c.get('created', ''),
                    'body': c.get('body', '')
                }
                for c in comments
            ],
            'attachments': attachments,
            'remote_links': remote_links,
            'issue_links': linked_issues,
            'status': status,
            'url': f"{os.environ['JIRA_URL'].rstrip('/')}/browse/{issue_key}"
        }

        if not summary:
            print("ERROR: Issue summary is blank; cannot continue.", file=sys.stderr)
            sys.exit(1)

        return result

    except Exception as e:
        print(f"ERROR: Failed to fetch issue: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        print("Usage: python jira_fetch.py <issue_key> <download_dir> [--metadata-only]", file=sys.stderr)
        sys.exit(1)

    issue_key = sys.argv[1]
    download_dir = sys.argv[2]
    metadata_flag = sys.argv[3] if len(sys.argv) == 4 else None
    metadata_only = False
    if metadata_flag:
        metadata_only = metadata_flag.lower() in {"--metadata-only", "metadata-only"}
        if not metadata_only:
            print(f"ERROR: Unknown flag '{metadata_flag}'. Supported flag: --metadata-only", file=sys.stderr)
            sys.exit(1)

    install_dependencies(metadata_only=metadata_only)
    check_env_vars()

    result = fetch_issue(issue_key, download_dir, metadata_only=metadata_only)
    print(json.dumps(result, indent=2))
