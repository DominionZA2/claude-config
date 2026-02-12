# Worktree Provisioning Command

Automate Jira issue lookup, branch discovery or creation, and git worktree provisioning for this project.

## How to Setup

This command is self-contained; it talks to Jira directly through the helper at `~/.claude/scripts/jira_fetch.py`. Prerequisites:

1. The helper script must exist at `~/.claude/scripts/jira_fetch.py`. If missing, stop and instruct the user to restore it.
2. Jira credentials are stored in `~/.claude/jira.env`. At runtime, source them into the current shell:
   ```bash
   source ~/.claude/jira.env
   ```
   - If any variable (`JIRA_URL`, `JIRA_EMAIL`, `JIRA_TOKEN`) is blank after sourcing, print `Missing Jira environment variables:` followed by the missing entries. Instruct the user to edit `~/.claude/jira.env` and populate the values.
     Include a clickable link to generate tokens: `[Get Jira API Token](https://id.atlassian.com/manage-profile/security/api-tokens)`
   - After updating the env file, instruct the user to restart the session so the new values load, then stop the command.
3. Python 3 must be available on PATH. If `python3 --version` fails, stop and tell the user to install Python 3.

## What this command does

- Fetches Jira issue details via the python helper (no MCP dependency).
- Discovers matching git branches for the Jira key, handles multi-branch selection, or gathers inputs for creating a new branch when absent.
- Builds the worktree path using the project directory name with a `-worktrees` suffix and the branch name.
- Provides the exact git commands the user must run (branch creation when needed, worktree creation) and confirms successful execution.
- Summarises the actions, including issue details, branch used, and worktree location.

## Instructions for the AI

When invoked (example: `/cosoft-create-worktree ACR-678`):

1. Parse the Jira key from the input. If missing, ask the user for it.
2. Load the Jira environment variables by running `source ~/.claude/jira.env`. If any value is empty after loading, list the missing variable(s), tell the user to edit `~/.claude/jira.env`, and stop.
3. Fetch the Jira issue directly (no references to other commands):
   - Confirm that `~/.claude/scripts/jira_fetch.py` exists. If not, stop with an explicit error.
   - Source `~/.claude/jira.env` to load credentials.
   - Determine the project root (workspace containing `.temp`). Do NOT create `.temp/{JIRA_KEY}` at this stage since `--metadata-only` is used and no files will be downloaded.
   - Execute (note the `--metadata-only` flag to skip attachment downloads):
     ```bash
     cd {PROJECT_ROOT}
     python3 ~/.claude/scripts/jira_fetch.py "{JIRA_KEY}" ".temp/{JIRA_KEY}" --metadata-only
     ```
     Capture stdout (JSON) and stderr.
   - If the script exits non-zero or stderr is non-empty, display the error (including stderr text) and stop. Remind the user to verify `JIRA_URL`, `JIRA_EMAIL`, and `JIRA_TOKEN`.
   - Parse the JSON result. Extract at least `summary` and `status`; store any other fields you want to display later. If parsing fails or summary is blank, stop with a descriptive error.
4. Determine the project root (workspace root containing `.temp`). Extract the project directory name. Define the worktree root as `{projectParent}\{projectName}-worktrees` (use platform-appropriate separators).
5. Refresh branch references:
   - From the project root, run:
     ```
     git fetch --all --prune
     ```
     (Ignore non-fatal warnings such as deleted refs.)
6. Check current branch before discovery:
   - Run `git rev-parse --abbrev-ref HEAD` from the project root to capture the current branch.
   - If the current branch name already contains the Jira key (case-insensitive), warn the user: `Current branch '{currentBranch}' already matches {JIRA_KEY}. Creating a worktree from the same branch may be redundant. Continue? (yes/no)`
     - If the user responds "no", stop gracefully, explaining the branch already matches the task.
     - If "yes", continue with the standard discovery flow (some teams may still want a separate worktree even if currently on the branch).
6. Discover existing branches:
   - Still at the project root, run:
     ```
     git branch -a
     ```
   - Capture the output and filter it yourself, matching any entry that contains the Jira key, case-insensitive (e.g., `bugfix/ACR-678-reminder...`, `remotes/origin/feature/acr-678-...`).
   - Normalise remote names by stripping the `remotes/` prefix when presenting options.
7. Analyse the branch list:
   - If exactly one branch appears, use it automatically but announce the selection so the user knows what happened.
   - If multiple branches appear, number them in the order returned and ask the user to pick one.
   - If no branches appear, ask whether to create a new branch. When the user agrees:
     - Ask only for a branch prefix, offering the explicit choices `feature`, `bugfix`, `hotfix`, `chore`, or `none` (blank behaves the same as `none`).
     - Generate the rest of the branch name from the Jira key and summary: lowercase everything, strip punctuation, collapse whitespace, and build a kebab-case slug. The combined part after the prefix (i.e., `{jiraKey-lower}-{slug}`) must not exceed 40 characters. Truncate the slug portion if necessary to meet this limit. Combine it as `{prefix}/{jiraKey-lower}-{slug}`; if the prefix is `none`/blank, omit the prefix and slash.
     - Display the generated branch name for confirmation and collect the base branch that should be used for creation.
     - If the user declines at any step, stop gracefully.
8. When branch creation is required:
   - Present a confirmation prompt: "Create local tracking branch `{newBranchName}` from `{baseBranch}`?"
   - If the user approves, run from the project root:
     ```
     git branch {newBranchName} {baseBranch}
     ```
     Report success or failure. On failure, surface the error and stop.
   - If the user declines, stop gracefully.
9. Ensure the worktree root directory exists:
   - If the directory is missing, create it automatically:
     ```
     mkdir "{projectParent}\{projectName}-worktrees"
     ```
   - Report that the directory was created (or already existed); only prompt the user if creation fails or the target path is ambiguous.
10. Form the final worktree path `{projectParent}\{projectName}-worktrees\{branchName}`.
    - If that path already exists, alert the user and ask how to proceed.
    - Otherwise, run automatically from the project root (no confirmation needed):
      ```
      git worktree add "{worktreePath}" {branchName}
      ```
      Report the command output. On failure, surface the error and stop.
    - After the worktree is created successfully, execute within the new worktree directory:
      ```
      cd "{worktreePath}"
      git submodule update --init --recursive
      ```
      Surface any errors from the submodule update; if it fails, instruct the user to rerun the command manually inside the worktree.
    - Install dependencies (detect project type and run the appropriate command):
      - Check for marker files in the worktree root to determine the project type:
        - If `package.json` exists → run `npm install`
        - If `*.sln` or `*.csproj` exists → run `dotnet restore`
        - If none of the above exist → skip dependency installation and report "No recognised dependency manifest found; skipping dependency install."
      - Report success or failure. On failure, surface the error but continue to the summary.
11. Present a summary including:
    - Jira key with summary
    - Branch used or created
    - Worktree path
    - A clickable VS Code link to open the worktree folder: `[Open in VS Code](vscode://file/{worktreePath})`
    - Any remaining manual actions (if applicable)

If any step fails (missing script, invalid issue, git errors), report the problem and stop without attempting subsequent actions. Never assume branch names or IDs; rely on actual outputs or explicit user input.

