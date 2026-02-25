# Setup Cloud Workspace Command

Automate multi-project workspace provisioning for v2-portal + cloud_backend into a shared workspace folder with VS Code workspace file and AI context file.

## What this command does

- Accepts a Jira key (e.g., `ACP-1077`) as input.
- Validates environment configuration, repo paths, and template files.
- Discovers matching branches across both repos or creates new ones.
- Creates git worktrees for both projects in a shared workspace folder.
- Copies VS Code workspace file, `.vscode` settings, and `Agents.md` context file.
- Optionally installs dependencies.

## Instructions for the AI

When invoked (example: `/setup-cloud-workspace ACP-1077`):

### Step 1 — Parse input

Extract `{KEY}` from the first argument. If missing, ask the user for it.

The user may also include additional instructions after the key in plain English. Look for anything that specifies a branch name to use, e.g.:
- `/setup-cloud-workspace ACP-1053 use branch feature/my-branch`
- `/setup-cloud-workspace ACP-1053 branch name is hotfix/acp-1053-fix`

If a branch name is provided this way, store it and skip Steps 5 and 6 entirely — go straight to Step 7 using that branch name. The branch must already exist in both repos (or at least one, in which case create it in the other from that repo's default branch).

### Step 2 — Pre-flight validation

Run this exact script to validate. Do NOT improvise your own validation logic — use this verbatim:

```bash
ENV_FILE="$HOME/.claude/cloud-workspace.env"
ERRORS=""
if [ ! -f "$ENV_FILE" ]; then
  ERRORS="${ERRORS}\n- Env file missing: $ENV_FILE"
else
  source "$ENV_FILE"
fi
if [ -z "$CLOUD_WS_PORTAL_REPO" ]; then ERRORS="${ERRORS}\n- CLOUD_WS_PORTAL_REPO is not set"; fi
if [ -z "$CLOUD_WS_BACKEND_REPO" ]; then ERRORS="${ERRORS}\n- CLOUD_WS_BACKEND_REPO is not set"; fi
if [ -z "$CLOUD_WS_ROOT" ]; then ERRORS="${ERRORS}\n- CLOUD_WS_ROOT is not set"; fi
if [ -z "$CLOUD_WS_TEMPLATES" ]; then ERRORS="${ERRORS}\n- CLOUD_WS_TEMPLATES is not set"; fi
if [ -n "$CLOUD_WS_PORTAL_REPO" ] && [ ! -d "$CLOUD_WS_PORTAL_REPO/.git" ]; then ERRORS="${ERRORS}\n- Not a git repo: $CLOUD_WS_PORTAL_REPO"; fi
if [ -n "$CLOUD_WS_BACKEND_REPO" ] && [ ! -d "$CLOUD_WS_BACKEND_REPO/.git" ]; then ERRORS="${ERRORS}\n- Not a git repo: $CLOUD_WS_BACKEND_REPO"; fi
if [ -n "$CLOUD_WS_TEMPLATES" ] && [ ! -f "$CLOUD_WS_TEMPLATES/Agents.md" ]; then ERRORS="${ERRORS}\n- Template missing: $CLOUD_WS_TEMPLATES/Agents.md"; fi
if [ -n "$CLOUD_WS_TEMPLATES" ] && [ ! -f "$CLOUD_WS_TEMPLATES/template.code-workspace" ]; then ERRORS="${ERRORS}\n- Template missing: $CLOUD_WS_TEMPLATES/template.code-workspace"; fi
if [ -n "$ERRORS" ]; then
  echo "PREFLIGHT_FAILED"
  echo -e "$ERRORS"
else
  echo "PREFLIGHT_OK"
  echo "PORTAL_REPO=$CLOUD_WS_PORTAL_REPO"
  echo "BACKEND_REPO=$CLOUD_WS_BACKEND_REPO"
  echo "WS_ROOT=$CLOUD_WS_ROOT"
  echo "TEMPLATES=$CLOUD_WS_TEMPLATES"
fi
```

If `PREFLIGHT_FAILED`, show all the errors to the user with actionable fix instructions, then **stop**.

### Step 3 — Gather information (non-interactive)

Run Steps 3a–3d without asking the user anything. Collect all results, then proceed to Step 4 (consolidated prompt).

#### 3a. Check existing workspace

Check if `${CLOUD_WS_ROOT}/${KEY}` already exists. Store the result (exists / does not exist).

#### 3b. Fetch branches

Run `git fetch --all --prune` in **both** repos. Ignore non-fatal warnings about deleted refs. Run these in parallel if possible.

```bash
cd "$CLOUD_WS_PORTAL_REPO" && git fetch --all --prune
cd "$CLOUD_WS_BACKEND_REPO" && git fetch --all --prune
```

#### 3c. Discover branches

Run `git branch -a` in both repos. Filter for branches containing `{KEY}` (case-insensitive). Classify results into categories:

**Category A — Branches in BOTH repos:** These are primary candidates.
- If exactly one match exists in both repos, auto-select it (no question needed).
- If multiple matches exist, note them — the user must pick one.

**Category B — Branches in ONE repo only:** These are "partial matches".
- Selecting one means the branch will be created in the other repo.

**Category C — No matches in either repo:** A new branch will need to be created.

When presenting branches, normalise remote names by stripping the `remotes/` prefix. Deduplicate local and remote refs that point to the same branch name.

#### 3d. Fetch Jira metadata (if branch creation may be needed)

If Step 3c resulted in Category C (no matches), fetch the Jira issue now so the branch slug can be shown in the consolidated prompt:

```bash
source ~/.claude/jira.env && python3 ~/.claude/scripts/jira_fetch.py "{KEY}" "/tmp/{KEY}" --metadata-only
```

Parse the JSON output, extract the `summary` field, and pre-generate the branch slug using this logic:
1. Start with `{KEY-lowered}` (e.g., `acp-1083`).
2. Take the Jira summary, convert to lowercase, replace spaces and special characters with hyphens, collapse multiple hyphens, strip leading/trailing hyphens.
3. Append the slugified summary to the key: `{KEY-lowered}-{slugified-summary}`.
4. Truncate the entire slug (key + summary) to a maximum of **40 characters**. The 40-char limit excludes the prefix and the `/` separator. If truncation is needed, cut at a word boundary (hyphen) to avoid partial words.

Example: Jira summary "Fix login redirect loop on timeout" → slug `acp-1083-fix-login-redirect-loop-on` → branch `bugfix/acp-1083-fix-login-redirect-loop-on`.

**Do NOT ask the user for a slug or description.** The branch name is always auto-generated from the Jira title.

### Step 4 — Consolidated user prompt

Present **one single prompt** containing all questions the user needs to answer, based on the results gathered in Step 3. The goal is to ask everything upfront so the user can answer once and walk away.

Build the prompt dynamically — only include sections that apply:

1. **If workspace already exists** (from 3a): "Workspace `${CLOUD_WS_ROOT}/${KEY}` already exists. Continue and overwrite? (yes/no)"
2. **If multiple matching branches found** (from 3c, Category A with multiple matches): "Multiple matching branches found — pick one:" followed by a numbered list.
3. **If no matching branches found** (from 3c, Category C): Show the auto-generated slug from 3d and ask: "No branches matching `{KEY}` found. Branch will be created from the Jira title: `{slug}`. Pick a prefix: `feature` (1), `bugfix` (2), `hotfix` (3), `chore` (4), or `none` (5)."
4. **Always**: "Install dependencies after setup? (yes/no)"

If only the dependency question applies (branch auto-selected, workspace doesn't exist), still present it as a single prompt.

Wait for **one response** answering all questions. Parse the answers, then proceed through all remaining steps without further interaction.

- If the user says no to the workspace overwrite, **stop**.
- If the user picks a branch prefix, that is implicit approval to create the branch — **do not ask for separate confirmation**.

### Step 5 — Branch creation (if needed)

Only enter this step if no matching branches were found (Category C from 3c), or the user selected a partial match (Category B) that needs creation in one repo.

Use the prefix from Step 4 and the slug from Step 3d to form the branch name.

The default base branches are:
- **v2-portal:** `main`
- **cloud_backend:** `master`

Announce the branch being created and proceed (no confirmation needed — the user already approved via the prefix selection in Step 4):

```bash
cd "$CLOUD_WS_PORTAL_REPO" && git branch {branchName} origin/{portalDefault}
cd "$CLOUD_WS_BACKEND_REPO" && git branch {branchName} origin/{backendDefault}
```
Report success or failure for each. On failure, surface the error and stop.

### Step 6 — Create workspace root

```bash
mkdir -p "${CLOUD_WS_ROOT}/${KEY}"
```

### Step 7 — Create worktrees

From each source repo, create the worktree in the workspace directory:

```bash
cd "$CLOUD_WS_PORTAL_REPO" && git worktree add "${CLOUD_WS_ROOT}/${KEY}/v2-portal" {branchName}
cd "$CLOUD_WS_BACKEND_REPO" && git worktree add "${CLOUD_WS_ROOT}/${KEY}/cloud_backend" {branchName}
```

Report success or failure for each. On failure, surface the error and stop.

### Step 8 — Submodule init (cloud_backend only)

Run submodule initialization in the **cloud_backend** worktree only. Skip v2-portal — it has no submodules and the command always fails there. This is **non-blocking** — if it fails, report the warning but continue.

```bash
cd "${CLOUD_WS_ROOT}/${KEY}/cloud_backend" && git submodule update --init --recursive
```

### Step 9 — Copy .vscode settings

For each repo, check if `.vscode` exists in the source repo root. If so, copy it into the corresponding worktree:

```bash
# Only if .vscode exists in source
cp -R "$CLOUD_WS_PORTAL_REPO/.vscode" "${CLOUD_WS_ROOT}/${KEY}/v2-portal/.vscode"
cp -R "$CLOUD_WS_BACKEND_REPO/.vscode" "${CLOUD_WS_ROOT}/${KEY}/cloud_backend/.vscode"
```

Report which files were copied, or skip silently if `.vscode` doesn't exist in a source repo.

### Step 10 — Copy templates

Copy the template files into the workspace root:

```bash
cp "$CLOUD_WS_TEMPLATES/Agents.md" "${CLOUD_WS_ROOT}/${KEY}/Agents.md"
cp "$CLOUD_WS_TEMPLATES/template.code-workspace" "${CLOUD_WS_ROOT}/${KEY}/${KEY}.code-workspace"
```

Then patch the workspace file for the current OS. The template uses `/usr/local/share/dotnet/dotnet` for the build command (macOS path). On Windows, replace it with `dotnet` (from PATH):

```bash
WS_FILE="${CLOUD_WS_ROOT}/${KEY}/${KEY}.code-workspace"
if [[ "$(uname -s)" == MINGW* || "$(uname -s)" == MSYS* || "$(uname -s)" == CYGWIN* || "$OS" == "Windows_NT" ]]; then
  sed -i 's|"command": "/usr/local/share/dotnet/dotnet"|"command": "dotnet"|g' "$WS_FILE"
fi
```

On macOS the template is used as-is with no patching needed.

### Step 11 — Dependency installation

Use the dependency install answer from Step 4 (already collected upfront). **Do not ask again.**

- If the user opted in, run both:
  - **v2-portal:** `cd "${CLOUD_WS_ROOT}/${KEY}/v2-portal" && npm install`
  - **cloud_backend:** `cd "${CLOUD_WS_ROOT}/${KEY}/cloud_backend" && dotnet restore AuraServices.sln`
  Report success or failure for each.

- If the user opted out, include the manual commands in the summary.

### Step 12 — Summary

Present a complete summary:

```
Cloud Workspace Setup Complete!

Branch: {branchName}
Workspace: ${CLOUD_WS_ROOT}/${KEY}

Files created:
  - ${KEY}/${KEY}.code-workspace
  - ${KEY}/Agents.md
  - ${KEY}/v2-portal/        (worktree)
  - ${KEY}/cloud_backend/    (worktree)

Dependencies: {installed | skipped}
{If skipped, show:
  Manual install:
    cd "${CLOUD_WS_ROOT}/${KEY}/v2-portal" && npm install
    cd "${CLOUD_WS_ROOT}/${KEY}/cloud_backend" && dotnet restore AuraServices.sln
}

Open in VS Code:
  [Open Workspace](vscode://file/${CLOUD_WS_ROOT}/${KEY}/${KEY}.code-workspace)
```

## cloud_backend solution file

The `cloud_backend` repo contains multiple `.sln` files. **`AuraServices.sln` is the primary solution file.** Always target it explicitly for any dotnet operation — restore, build, test, publish, etc. Running `dotnet` commands without specifying the solution will fail with `MSB1011`.

Examples:
- `dotnet restore AuraServices.sln`
- `dotnet build AuraServices.sln`
- `dotnet test AuraServices.sln`

## Error handling

If any step fails with a git error or filesystem error, report the problem clearly and stop. Do not attempt subsequent steps after a critical failure (worktree creation, branch creation). Non-critical failures (submodule init, dependency install) should be reported as warnings but not block the process.

Never assume branch names or paths — rely on actual command outputs and explicit user input.
