# cosoft-jira-fetch-for-monday

Stand-up helper for Monday 09:30: list every Jira issue currently assigned to you that still needs attention (In Progress -> Selected for Development -> To Do -> Backlog). The heavy lifting happens in `jira-search.py`, which simply relays whatever JQL you pass to Jira.

## Prerequisites
1. Helper script: `%USERPROFILE%\.cursor/scripts/jira-search.py` (shared across every workspace)
2. Jira credentials exposed to the current shell:
   ```powershell
   $env:JIRA_URL   = [System.Environment]::GetEnvironmentVariable('JIRA_URL','User')
   $env:JIRA_EMAIL = [System.Environment]::GetEnvironmentVariable('JIRA_EMAIL','User')
   $env:JIRA_TOKEN = [System.Environment]::GetEnvironmentVariable('JIRA_TOKEN','User')
   ```
   (Set them permanently once via `SetEnvironmentVariable`, then reload Cursor/PowerShell.)

## Run: Monday planning query

```powershell
$cursorRoot = Join-Path $env:USERPROFILE ".cursor"
$scriptPath = "$cursorRoot/scripts/jira-search.py"
$statuses = @(
  '"In Progress"',
  '"Selected for Development"',
  '"To Do"',
  '"Backlog"'
)
$jql = @"
assignee = currentUser()
AND status in ($($statuses -join ', '))
ORDER BY status ASC, updated DESC
"@.Trim()

python $scriptPath `
  --jql "$jql" `
  --max-results 200 `
  --verbose
```

- Change the `$statuses` array if your board uses different columns.
- Append extra clauses (`AND project = ACP`, `AND updated >= -30d`, etc.) before the `ORDER BY` when you need a narrower slice.
- Add `--output json` to capture the raw response for further processing or `--dry-run` to verify the generated JQL without hitting Jira.

## Optional: clickable markdown snapshot

```powershell
$cursorRoot = Join-Path $env:USERPROFILE ".cursor"
$scriptPath = "$cursorRoot/scripts/jira-search.py"
$tempJson = Join-Path $env:TEMP "jira_monday.json"
$tempMd   = Join-Path $env:TEMP "jira_monday_clickable.md"

python $scriptPath --jql "$jql" --output json > $tempJson

python - <<'PY'
import json
from pathlib import Path
from collections import defaultdict
priority = {'In Progress':0, 'Selected for Development':1, 'To Do':2, 'Backlog':3}
data = json.loads(Path(r"$tempJson").read_text())
sections = defaultdict(list)
for issue in data.get("issues", []):
    f = issue.get("fields", {})
    status = (f.get("status") or {}).get("name", "Unknown")
    updated = (f.get("updated") or "").replace("T", " ")[:16]
    summary = (f.get("summary") or "").strip()
    key = issue.get("key")
    url = f"https://cosoft.atlassian.net/browse/{key}"
    sections[status].append((updated, key, summary, url))
lines = []
for status in sorted(sections, key=lambda s: (priority.get(s, 99), s)):
    lines.append(f"## {status}")
    for updated, key, summary, url in sorted(sections[status], key=lambda x: x[0], reverse=True):
        lines.append(f"- [{key}]({url}) — {updated} — {summary}")
    lines.append("")
Path(r"$tempMd").write_text("\n".join(lines), encoding="utf-8")
print("Saved:", r"$tempMd")
PY
```

Opening `$tempMd` in Cursor gives you grouped, clickable links for the stand-up discussion. Adjust the template as needed once priorities change.

## Failure handling
- If running `python $scriptPath ...` produces any error (missing file, HTTP/Jira error, invalid JQL, etc.), stop immediately and surface the exact message to me. Do **not** try to auto-fix credentials, rewrite the query, or retry with modified inputs—manual confirmation is required before proceeding.


