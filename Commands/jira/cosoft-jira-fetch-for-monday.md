# cosoft-jira-fetch-for-monday

Stand-up helper for Monday 09:30: list every Jira issue currently assigned to you that still needs attention (In Progress -> Selected for Development -> To Do -> Backlog). The heavy lifting happens in `jira-search.py`, which simply relays whatever JQL you pass to Jira.

## Prerequisites
1. Helper script: `~/.claude/scripts/jira-search.py`
2. Jira credentials sourced from env file:
   ```bash
   source ~/.claude/jira.env
   ```
   (Edit `~/.claude/jira.env` to set `JIRA_URL`, `JIRA_EMAIL`, `JIRA_TOKEN`.)

## Run: Monday planning query

```bash
source ~/.claude/jira.env

SCRIPT_PATH="$HOME/.claude/scripts/jira-search.py"

JQL='assignee = currentUser()
AND status in ("In Progress", "Selected for Development", "To Do", "Backlog")
ORDER BY status ASC, updated DESC'

python3 "$SCRIPT_PATH" \
  --jql "$JQL" \
  --max-results 200 \
  --verbose
```

- Change the status list if your board uses different columns.
- Append extra clauses (`AND project = ACP`, `AND updated >= -30d`, etc.) before the `ORDER BY` when you need a narrower slice.
- Add `--output json` to capture the raw response for further processing or `--dry-run` to verify the generated JQL without hitting Jira.

## Optional: clickable markdown snapshot

```bash
source ~/.claude/jira.env

SCRIPT_PATH="$HOME/.claude/scripts/jira-search.py"
TEMP_JSON="/tmp/jira_monday.json"
TEMP_MD="/tmp/jira_monday_clickable.md"

python3 "$SCRIPT_PATH" --jql "$JQL" --output json > "$TEMP_JSON"

python3 - <<'PY'
import json
from pathlib import Path
from collections import defaultdict
priority = {'In Progress':0, 'Selected for Development':1, 'To Do':2, 'Backlog':3}
data = json.loads(Path("/tmp/jira_monday.json").read_text())
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
Path("/tmp/jira_monday_clickable.md").write_text("\n".join(lines), encoding="utf-8")
print("Saved: /tmp/jira_monday_clickable.md")
PY
```

Opening the markdown file gives you grouped, clickable links for the stand-up discussion. Adjust the template as needed once priorities change.

## Failure handling
- If running `python3 "$SCRIPT_PATH" ...` produces any error (missing file, HTTP/Jira error, invalid JQL, etc.), stop immediately and surface the exact message to me. Do **not** try to auto-fix credentials, rewrite the query, or retry with modified inputs—manual confirmation is required before proceeding.
