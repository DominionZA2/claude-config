# Jira Context Push Command

Upload the current local task context folder to the matching Jira task as attachments.

## What this command does

Uploads every root-level file in `.temp/{TASK_NUMBER}/` to Jira issue `{TASK_NUMBER}` using the exact local filename. If Jira already has an attachment with the same filename, it is replaced. Local files win.

**Usage:** `/jira:cosoft-jira-context-push {TASK_NUMBER}`

## Instructions for the AI

When this command is invoked:

1. Parse the task number from the first token of the input.
   - Example: `API-763`
   - If no task number is provided, ask the user for it and stop.
2. Determine the project root exactly like the existing Jira commands:
   - Search the workspace(s) for `.temp/{TASK_NUMBER}/`.
   - If found, set `PROJECT_ROOT` to the parent directory of `.temp`.
   - If not found, stop with: `Task folder .temp/{TASK_NUMBER}/ not found. Run /jira:cosoft-jira-01-setup {TASK_NUMBER} first.`
3. Set `TASK_FOLDER` to `{PROJECT_ROOT}/.temp/{TASK_NUMBER}`.
4. Verify the helper exists at `~/.claude/scripts/jira_context_sync.py`.
   - If missing, stop and report the missing helper path.
5. Run the helper from `PROJECT_ROOT`:

   ```bash
   python ~/.claude/scripts/jira_context_sync.py push "{TASK_NUMBER}" "{TASK_FOLDER}"
   ```

6. If the helper fails, show the error and stop.
7. If the helper succeeds, summarize:
   - Jira issue key
   - Task folder
   - Uploaded filenames

## Rules

- Do not use `jira_fetch.py`.
- Do not change filenames.
- Do not create archives.
- Do not write comments.
- Do not sync subfolders.
- Same attachment filename on Jira means replace it.

