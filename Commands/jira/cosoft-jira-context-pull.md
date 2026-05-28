# Jira Context Pull Command

Download the Jira task attachments into the current local task context folder.

## What this command does

Downloads Jira attachments from issue `{TASK_NUMBER}` into `.temp/{TASK_NUMBER}/` using the exact attachment filenames. Existing local files with the same names are overwritten. Jira wins.

**Usage:** `/jira:cosoft-jira-context-pull {TASK_NUMBER}`

## Instructions for the AI

When this command is invoked:

1. Parse the task number from the first token of the input.
   - Example: `API-763`
   - If no task number is provided, ask the user for it and stop.
2. Determine the project root using the existing Jira command convention:
   - Search the workspace(s) for `.temp/{TASK_NUMBER}/`.
   - If found, set `PROJECT_ROOT` to the parent directory of `.temp`.
   - If not found, search for an existing `.temp` folder in the workspace and use its parent as `PROJECT_ROOT`.
   - If no `.temp` folder exists, use the workspace root as `PROJECT_ROOT`.
3. Set `TASK_FOLDER` to `{PROJECT_ROOT}/.temp/{TASK_NUMBER}`.
4. Verify the helper exists at `~/.claude/scripts/jira_context_sync.py`.
   - If missing, stop and report the missing helper path.
5. Run the helper from `PROJECT_ROOT`:

   ```bash
   python ~/.claude/scripts/jira_context_sync.py pull "{TASK_NUMBER}" "{TASK_FOLDER}"
   ```

6. If the helper fails, show the error and stop.
7. If the helper succeeds, summarize:
   - Jira issue key
   - Task folder
   - Downloaded filenames

## Rules

- Do not use `jira_fetch.py`.
- Do not change filenames.
- Do not create archives.
- Do not write comments.
- Existing local files with matching names are overwritten.

