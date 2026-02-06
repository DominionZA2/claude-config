---
description: Sync reports from Dropbox to cloud_reports repo and push to remote
allowed-tools: Bash(git *), Bash(rm *), Bash(mkdir *), Bash(cp *), Bash(curl *), Bash(source *)
---

# Report Sync Deploy

## Steps

1. Source the environment file:
   ```bash
   source ~/.claude/report-sync.env
   ```

2. Ensure the cloud_reports repo at `/Users/michaelsmit/source/cloud_reports` is on the `develop` branch. If not, switch to it automatically. Then pull latest to ensure we're up to date.

3. Delete the Reports folder at `/Users/michaelsmit/source/cloud_reports/Reports`

4. Copy from Dropbox (`/Users/michaelsmit/Dropbox/Cloud_Reports/Main`) to destination:
   - `User/Reports` -> `Reports/User/Reports`
   - `User/Dashboards` -> `Reports/User/Dashboards`
   - `Support/Reports` -> `Reports/Support/Reports`
   - `Support/Dashboards` -> `Reports/Support/Dashboards`

5. Check git status for changes. If no changes, notify "No changes detected" and stop.

6. Show the user what changed and commit with message "Updated reports"

7. Ask user to confirm push. If confirmed, push to remote.

8. On successful push, send Slack notifications:
   ```bash
   curl -s -X POST -H 'Content-type: application/json' --data '{"text":"Reports deployed."}' "$REPORT_SYNC_SLACK_WEBHOOK_MIKE"
   # curl -s -X POST -H 'Content-type: application/json' --data '{"text":"Reports deployed."}' "$REPORT_SYNC_SLACK_WEBHOOK_FRANK"
   ```
