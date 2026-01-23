# Jira Task Setup Command

Fetches all available information about a Jira task and creates a task-specific markdown file.

## What this command does

Fetches ALL available information about a Jira task using a Python script. Includes EVERYTHING from the issue - summary, description, comments, attachments (downloaded to disk), and remote links. Creates a task-specific markdown file (.temp/{TASK_NUMBER}/{TASK_NUMBER}-task-details.md) with all the fetched data.

**Usage:** /cosoft-jira-01-setup {TASK_NUMBER} [optional additional prompt]

- {TASK_NUMBER}: The Jira task number (e.g., "ACR-678" or "API-708")
- [optional additional prompt]: Any additional instructions for formatting or organizing the content

## Instructions for the AI

When this command is invoked:

### SETUP PHASE

- Parse the user input to extract:
  - Task number: First token/word (e.g., "ACR-678" or "API-708")
  - Additional prompt (optional): Any text after the task number
  - Example: Input "ACR-678 Pay special attention to performance" -> Task number: "ACR-678", Additional prompt: "Pay special attention to performance"
  - If no additional text exists after the task number, ADDITIONAL_PROMPT is empty/undefined
- Store ADDITIONAL_PROMPT for use during setup (if provided)
- Determine the project root:
  - Search for the task folder .temp/{TASK_NUMBER}/ in the workspace(s)
  - If the folder exists, extract the PROJECT ROOT from the task folder path:
    - If task folder is at /path/to/project/.temp/{TASK_NUMBER}/, then PROJECT ROOT is /path/to/project/
    - The PROJECT ROOT is the parent directory of the .temp folder
  - If the folder does not exist, search for any .temp folder in the workspace to determine PROJECT ROOT
  - If no .temp folder exists, use the workspace root as PROJECT ROOT
- Create .temp folder in PROJECT ROOT if it does not exist
- Create .temp/{TASK_NUMBER}/ folder if it does not exist
- Determine the full path to the task folder: {PROJECT_ROOT}/.temp/{TASK_NUMBER}/
- Determine the shared Cursor home directory (global tooling lives at %USERPROFILE%\.cursor).

### LOAD ENVIRONMENT VARIABLES

- **CRITICAL:** Before executing Python, ensure environment variables are available in the current session:
  - Load permanent environment variables into the current session:
    - $env:JIRA_URL = [System.Environment]::GetEnvironmentVariable("JIRA_URL", "User")
    - $env:JIRA_EMAIL = [System.Environment]::GetEnvironmentVariable("JIRA_EMAIL", "User")
    - $env:JIRA_TOKEN = [System.Environment]::GetEnvironmentVariable("JIRA_TOKEN", "User")
  - If any of these are empty/null, inform the user that the environment variables need to be set permanently first

### EXECUTE PYTHON SCRIPT

- Execute the Python script (omit --metadata-only so attachments are downloaded): python $env:USERPROFILE\.cursor/scripts/jira_fetch.py {TASK_NUMBER} {FULL_FOLDER_PATH}
  - $env:USERPROFILE\.cursor is the shared Cursor config folder that exists regardless of workspace
  - {FULL_FOLDER_PATH} is the absolute path to .temp/{TASK_NUMBER}/
- Capture the script stdout output (JSON)
- Capture the script stderr output (for errors)
- **If the script exits with non-zero code or outputs errors:**
  - Display the error message from stderr
  - **CRITICAL:** Extract and display clickable links from stderr output:
    - If stderr contains the Jira API token URL, extract it and display as a clickable markdown link: [Get Jira API Token](https://id.atlassian.com/manage-profile/security/api-tokens)
  - Display these links prominently in the chat output (not just terminal output) so the user can click them directly
  - Inform the user about the failure
  - STOP execution
- **If the script succeeds:**
  - Parse the JSON output
  - Proceed to linked-task discovery before creating the main markdown file

### LINKED TASK DISCOVERY

- Scan the fetched content for references to other Jira tasks:
  - Collect text from the summary, description, comments, attachment/link metadata, and any additional fields returned by the script
  - Parse structured link data provided by Jira (fields.issuelinks, linkedIssues, "Linked work items", remote relations, etc.) so that relationships shown in the UI are captured even if not mentioned in free text
  - Use a regex such as (?i)([A-Z][A-Z0-9]+-\d+) to find potential Jira task keys within free text
  - Also look for explicit Jira URLs (https://cosoft.atlassian.net/browse/{KEY}) and extract the key
- For each unique referenced task key (excluding the primary {TASK_NUMBER}):
  - Create a dedicated subfolder for the linked task: .temp/{TASK_NUMBER}/{LINKED_TASK}/ (all linked-task markdown plus downloaded attachments belong here to keep the root folder uncluttered)
  - Determine the linked-task details path: .temp/{TASK_NUMBER}/{LINKED_TASK}/{LINKED_TASK}-task-details.md
  - Run the Python script pointing at that subfolder (still without --metadata-only to download attachments into that folder): python $env:USERPROFILE\.cursor/scripts/jira_fetch.py {LINKED_TASK} {FULL_FOLDER_PATH}/{LINKED_TASK}
  - On success, parse the JSON and create a task-details markdown file (same structure as the main task: Summary, Description, Comments, Attachments, Links)
  - Capture the linked task status (e.g., To Do, In Progress, Done) so the main file can flag unresolved dependencies
  - If the fetch fails, note the error and continue (the main setup file should document that the linked task could not be retrieved)
  - Avoid duplicate downloads by tracking keys already processed

### BRANCH STATUS ANALYSIS

- While processing each linked task, inspect its description, comments, and attachments for Git branch references:
  - Look for common patterns such as feature/..., bugfix/..., dev/..., or {PROJECT_KEY}-xxx branches using regex like ([A-Za-z0-9._/-]+/[A-Za-z0-9._-]+) and also {TASK_KEY}[A-Za-z0-9._/-]* branch names.
  - Record branch names along with the linked task that mentioned them.
- Determine the current Git branch with git rev-parse --abbrev-ref HEAD (run from the project root).
- Build a candidate branch list by combining:
  - Branch names explicitly extracted from linked-task content
  - Any branch in the repo whose name contains the linked task key (use pattern searches such as git branch -a | Select-String {LINKED_TASK} and git ls-remote --heads origin | Select-String {LINKED_TASK})
- For each candidate branch:
  - Check if it exists locally or remotely (pattern search output already proves existence; otherwise fall back to git show-ref / git ls-remote to confirm).
  - If it exists, check whether the current branch already contains it (e.g., git merge-base --is-ancestor {branch} {current}), and record the status explicitly as **Merged into {current_branch}** or **Not merged into {current_branch}** so the output reflects which branch was used as the base.
  - If no local/remote reference exists after pattern searches, mark it as **Missing** so the team knows to investigate.
- Keep a structured list: {Branch Name} - Source: {LINKED_TASK or "Repo Search"} - Status: Merged into {current_branch} / Not merged into {current_branch} / Missing. If the current branch is something unexpected (not main/master), note that alongside the status so mismatches are obvious.

### CREATE MARKDOWN FILE

- Create or overwrite {TASK_NUMBER}-task-details.md in .temp/{TASK_NUMBER}/ folder
- Include the following sections from the JSON data:
  - **## Summary**
    - Task key: {TASK_NUMBER}
    - Summary text from JSON
  - **## Description**
    - Full description from JSON (preserve formatting, convert HTML to markdown if needed)
    - If the description contains Jira attachment macros/images (exclamation-mark syntax like !filename|width=...! or similar), replace each macro with a clickable markdown link to the downloaded attachment using the relative path (for example: ![filename](./relative/path) for images or [filename](./relative/path) for non-images). Use the attachment metadata gathered below to resolve filenames to local paths.
  - **## Comments**
    - For each comment in the JSON comments array:
      - Author name
      - Created date/time
      - Comment body (preserve formatting, convert HTML to markdown if needed)
      - Perform the same attachment macro replacement described for the description so that any referenced files become clickable links
    - Order comments chronologically (oldest first)
    - If no comments, include: "No comments found for this issue"
  - **## Attachments**
    - For each attachment in the JSON attachments array:
      - Filename
      - Size
      - Download status (downloaded successfully or error message)
      - Replace the old multi-line listing with a single bullet per attachment where only the human-readable file name is clickable, followed by plain-text metadata. Use the format: - [Filename](./RELATIVE_PATH_WITH_SPACES_ESCAPED) - Size: {bytes} bytes - Status: {status}. This mirrors the linking style from the main task references (no duplicate URL text) while keeping size/status easy to read. Ensure spaces are URL-encoded or wrap the target in angle brackets. Reuse the same relative path when converting description/comment macros so there is a single consistent reference per attachment.
    - If no attachments, include: "No attachments found for this issue"
  - **## Links**
    - For each remote link in the JSON remote_links array:
      - Link title
      - URL (as clickable markdown link)
      - Relationship type if available
    - If no links, include: "No links found for this issue"
- Format the markdown file clearly with proper headers and structure
- **If ADDITIONAL_PROMPT exists:** Incorporate any instructions from the additional prompt when formatting, but still include ALL data
- After the core sections, add ## Linked Tasks
  - If linked task downloads were successful:
    - For each linked key, add a bullet that includes both the local details file (inside its subfolder) and the Jira URL so operators can jump directly to the issue, for example: - [{LINKED_TASK} Task Details](./{LINKED_TASK}/{LINKED_TASK}-task-details.md) - [View on Jira](https://cosoft.atlassian.net/browse/{LINKED_TASK}) - Status: {STATUS} - {one-line summary}
    - If the linked task status is not a resolved/done state, add a note such as "Warning: Dependency still active"
  - If a linked download failed, note it explicitly: - {LINKED_TASK}: Unable to fetch (reason)
  - If no linked tasks were detected, write "No linked tasks detected."
- Add ## Linked Branch Status
  - If branch references were discovered:
    - List each branch with its source task and merge status, explicitly mentioning the base branch used for the check: - {Branch Name} - Source: {LINKED_TASK} - Status: Merged into {current_branch} / Not merged into {current_branch} / Missing
    - If a branch was missing from the repo, call that out explicitly so branch management can follow up
  - If no branches were discovered, state "No branch references detected in linked tasks."

### DISPLAY SUMMARY

- Display a summary including:
  - Task key/number
  - Summary/title from JSON
  - **Jira Task URL:** Display as a clickable markdown link using format [{TASK_KEY}](https://cosoft.atlassian.net/browse/{TASK_KEY}) - for example: [ACR-678](https://cosoft.atlassian.net/browse/ACR-678) - this must be a clickable link, NOT a bare URL
  - File location: .temp/{TASK_NUMBER}/{TASK_NUMBER}-task-details.md
  - Number of comments found
  - Number of attachments found (and download status)
  - Number of remote links found
  - Number of linked tasks downloaded (and any failures)
  - Linked task URL list: display each linked key as a clickable Jira link (e.g., [ACR-123](https://cosoft.atlassian.net/browse/ACR-123))
  - Linked task status summary: counts of Done vs In Progress vs other states
  - Branch status summary: counts of branches merged into the current branch vs not merged vs missing, and display the name of the current branch so operators can verify they are on the expected base branch
- **IMPORTANT:** All URLs must be displayed as clickable markdown links using the format [link text](url) - never display bare URLs
- End with a clear success line so operators know what to run next, e.g. "Jira task setup complete. Next step: /cosoft-jira-02-plan {TASK_NUMBER}"

### ERROR HANDLING

- If Python script is not found: Inform user and STOP
- If script execution fails: Display error with clickable links and STOP
- If JSON parsing fails: Display error and STOP
- If folder creation fails: Display error and STOP
- If the task number is not provided: Ask the user for it
