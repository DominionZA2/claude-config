# Create Worktree Command

Automate branch discovery or creation and git worktree provisioning for this project.

## What this command does

- Accepts a branch name as input.
- Discovers matching git branches, handles multi-branch selection, or gathers inputs for creating a new branch when absent.
- Builds the worktree path using the project directory name with a `-worktrees` suffix and the branch name.
- Provides the exact git commands the user must run (branch creation when needed, worktree creation) and confirms successful execution.
- Summarises the actions, including branch used and worktree location.

## Instructions for the AI

When invoked (example: `/create-worktree feature/my-branch`):

1. Parse the branch name from the input. If missing, ask the user for it.
2. Determine the project root (workspace root containing `.temp`). Extract the project directory name. Define the worktree root as `{projectParent}\{projectName}-worktrees` (use platform-appropriate separators).
3. Refresh branch references:
   - From the project root, run:
     ```
     git fetch --all --prune
     ```
     (Ignore non-fatal warnings such as deleted refs.)
4. Check current branch before discovery:
   - Run `git rev-parse --abbrev-ref HEAD` from the project root to capture the current branch.
   - If the current branch name already matches the provided branch name (case-insensitive), warn the user: `Current branch '{currentBranch}' already matches {BRANCH_NAME}. Creating a worktree from the same branch may be redundant. Continue? (yes/no)`
     - If the user responds "no", stop gracefully, explaining the branch already matches.
     - If "yes", continue with the standard discovery flow (some teams may still want a separate worktree even if currently on the branch).
5. Discover existing branches:
   - Still at the project root, run:
     ```
     git branch -a
     ```
   - Capture the output and filter it yourself, matching any entry that contains the branch name, case-insensitive (e.g., `bugfix/my-branch`, `remotes/origin/feature/my-branch`).
   - Normalise remote names by stripping the `remotes/` prefix when presenting options.
6. Analyse the branch list:
   - If exactly one branch appears, use it automatically but announce the selection so the user knows what happened.
   - If multiple branches appear, number them in the order returned and ask the user to pick one.
   - If no branches appear, ask whether to create a new branch. When the user agrees:
     - Ask only for a branch prefix, offering the explicit choices `feature`, `bugfix`, `hotfix`, `chore`, or `none` (blank behaves the same as `none`).
     - Generate the branch name as `{prefix}/{branchName}`; if the prefix is `none`/blank, use just `{branchName}`.
     - Display the generated branch name for confirmation and collect the base branch that should be used for creation.
     - If the user does not provide a base branch, default to `master`.
     - If the user declines at any step, stop gracefully.
7. When branch creation is required:
   - Use the base branch exactly as provided by the user (or `master` if not provided). The user can specify `origin/master`, `origin/my-branch`, or just `master`/`my-branch` - use it as-is.
   - Present a confirmation prompt: "Create local tracking branch `{newBranchName}` from `{baseBranch}`?"
   - If the user approves, run from the project root:
     ```
     git branch {newBranchName} {baseBranch}
     ```
     Report success or failure. On failure (e.g., base branch does not exist), surface the error and stop.
   - If the user declines, stop gracefully.
8. Ensure the worktree root directory exists:
   - If the directory is missing, create it automatically:
     ```
     mkdir "{projectParent}\{projectName}-worktrees"
     ```
   - Report that the directory was created (or already existed); only prompt the user if creation fails or the target path is ambiguous.
9. Form the final worktree path `{projectParent}\{projectName}-worktrees\{branchName}`.
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
     Report success or failure. On failure, surface the error and stop.
10. Present a summary including:
    - Branch used or created
    - Worktree path
    - Any remaining manual actions (if applicable)
    - Reminder to open the new folder in Cursor or VS Code

If any step fails (git errors), report the problem and stop without attempting subsequent actions. Never assume branch names or IDs; rely on actual outputs or explicit user input.

