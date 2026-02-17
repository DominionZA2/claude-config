# Switch to Dev Branch Command

Create or switch to a `dev/` branch for merge conflict resolution, then merge the integration branch.

## What this command does

- Detects the current branch and derives a `dev/` branch name from it.
- Creates the `dev/` branch (or checks it out if it already exists).
- Detects the project to determine the correct integration branch (`staging` or `develop`).
- Fetches and merges the integration branch.
- If there are conflicts, resolves them by keeping both sides of changes.
- Stops before committing so the user can review.

## Important rules

- **Never make code fixes in the dev branch** — it is purely for conflict resolution.
- **Never run builds** in the dev branch.
- **Never commit or push** — the user decides when to do that.

## Instructions for the AI

When invoked (example: `/switch-to-dev`):

1. **Detect the current branch**:
   ```
   git rev-parse --abbrev-ref HEAD
   ```
   - Strip the first path segment (everything before and including the first `/`) and prepend `dev/`.
   - Examples:
     - `hotfix/ACP-1077-foo` → `dev/ACP-1077-foo`
     - `feature/ACP-999-bar` → `dev/ACP-999-bar`
     - `bugfix/ACP-123-baz` → `dev/ACP-123-baz`
   - If the branch has no `/` prefix (e.g. `main`, `staging`), warn the user that this doesn't look like a feature/hotfix/bugfix branch and ask whether to proceed. If they decline, stop.
   - If the current branch already starts with `dev/`, inform the user they are already on a dev branch and skip to step 4 (fetch and merge).

2. **Check if the dev branch already exists locally**:
   ```
   git branch --list dev/BRANCH_NAME
   ```
   - If output is non-empty → the branch exists. Check it out:
     ```
     git checkout dev/BRANCH_NAME
     ```
   - If output is empty → create the branch from the current branch:
     ```
     git checkout -b dev/BRANCH_NAME
     ```
   - Report which action was taken.

3. **Detect the integration branch**:
   - Get the remote URL:
     ```
     git remote get-url origin
     ```
   - If the URL contains `v2-portal` → integration branch is `staging`.
   - If the URL contains `cloud` → integration branch is `develop`.
   - If neither pattern matches, ask the user which integration branch to use (suggest `staging` or `develop`).
   - Report the detected integration branch.

4. **Fetch and merge**:
   ```
   git fetch origin
   git merge origin/{integration-branch}
   ```
   - If the merge completes cleanly, report success and stop. Remind the user: "Merge completed cleanly. Review the changes, then commit and push when ready."

5. **Handle merge conflicts**:
   - If the merge reports conflicts, list the conflicted files.
   - For each conflicted file, resolve by keeping **both** sets of changes (ours + theirs). Use conflict markers in the file to identify both sides and combine them.
   - After resolving, stage the files with `git add` but **do not commit**.
   - Report which files were resolved and how.
   - Remind the user: "All conflicts have been resolved and staged. Please review the changes, then commit and push when you are satisfied."

6. **Stop** — do not commit, do not push. Hand control back to the user.

If any step fails (git errors, unexpected state), report the problem and stop without attempting subsequent actions.
