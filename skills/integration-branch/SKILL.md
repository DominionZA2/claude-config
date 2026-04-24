---
name: integration-branch
description: Create a throwaway integration branch off the current feature/hotfix branch, merge the testing branch into it, and surface conflicts for resolution — without polluting the original branch. Auto-detects GitHub (staging) vs Bitbucket (develop) from the remote URL.
disable-model-invocation: true
allowed-tools: Bash(git *) Read
---

# Integration branch

Create a sibling branch for merging the testing branch into, so the conflict-resolution work doesn't contaminate the original feature/hotfix branch.

## When to use

The user is on a feature/hotfix branch based off production. They want to PR it into the pre-production testing branch (`develop` on Bitbucket, `staging` on GitHub), but that target has diverged and the PR shows conflicts.

Merging the testing branch *into* the feature branch would pollute it with unrelated changes that shouldn't go to production later. Instead, create a disposable integration branch off the feature branch, merge the testing branch there, and PR *that* into the testing branch.

The feature branch stays clean for its eventual PR into production.

## Terminology

- **Source branch**: the current branch (typically `feature/<suffix>` or `hotfix/<suffix>`). Stays untouched.
- **Integration branch**: new branch created off the source, prefixed `dev/<suffix>`. Disposable.
- **Testing branch**: what we merge into the integration branch. Depends on remote host:
  - Bitbucket → `develop`
  - GitHub → `staging`

## Procedure

### Step 1 — Verify preconditions

1. `git status --short` must be clean. If dirty, stop and ask the user.
2. Capture the source branch: `git branch --show-current`. If it's already a `dev/*` branch, stop — we're already on an integration branch.
3. Derive the suffix. Strip a recognized prefix from the source branch name:
   - `feature/<suffix>` → `<suffix>`
   - `hotfix/<suffix>` → `<suffix>`
   - `release/<suffix>` → `<suffix>`
   - `bugfix/<suffix>` → `<suffix>`
   - Anything else → stop and ask the user what to name the integration branch.
4. Candidate integration branch: `dev/<suffix>`. Check whether it already exists — this determines the path through Step 4:
   - Local: `git show-ref --verify --quiet refs/heads/dev/<suffix>`
   - Remote: `git ls-remote --heads origin dev/<suffix>`

### Step 2 — Detect host and pick the testing branch

1. `git remote get-url origin` (fall back to any upstream remote if origin is missing).
2. Classify:
   - URL contains `github.com` → **GitHub** → testing branch is `staging`
   - URL contains `bitbucket.org` → **Bitbucket** → testing branch is `develop`
   - Anything else → stop and ask the user which convention applies.

### Step 3 — Fetch and verify the testing branch

1. `git fetch origin <testing-branch>` — must succeed.
2. `git show-ref --verify --quiet refs/remotes/origin/<testing-branch>` — must exist.

### Step 4 — Create or switch to the integration branch

Two paths, depending on whether `dev/<suffix>` already exists (from Step 1.4). Remember which path was taken — Step 5 is skipped on Path A.

**Path A — branch does not exist (fresh create)**

1. `git checkout -b dev/<suffix>` from the current source-branch HEAD.
2. Sanity check: `git branch --show-current` returns `dev/<suffix>`.

**Path B — branch already exists (reuse)**

1. If the branch exists only on the remote: `git fetch origin dev/<suffix>` then `git checkout dev/<suffix>` (tracking is set up automatically).
2. If a local branch exists: `git checkout dev/<suffix>`, then `git pull --ff-only` if it tracks a remote.
3. If `git pull --ff-only` fails (local has diverged from the remote): stop and report. Do not force-update.
4. Sanity check: `git branch --show-current` returns `dev/<suffix>`.

### Step 5 — Merge the source branch into the integration branch (Path B only)

Skip this step on Path A — `dev/<suffix>` is already a fresh copy of the source branch at HEAD, so there's nothing to catch up.

On Path B, bring the source-branch commits that have landed since the integration branch was last updated into `dev/<suffix>`:

1. `git merge <source-branch> --no-commit --no-ff`.
2. If clean:
   - `git commit -m "Merge branch '<source-branch>' into dev/<suffix>"`
   - Continue to Step 6.
3. If conflicts, use the same protocol as Step 6:
   - `git status --short` — capture every line with `UU`/`AU`/`UA`/`DU`/`UD`/`DD`/`AA`.
   - For each conflicted file, read both sides (`git show HEAD:<path>` and `git show MERGE_HEAD:<path>`) and explain the conflict with a proposed resolution.
   - **STOP and report** the full conflict analysis to the user. Wait for explicit approval before resolving anything.
   - After the user approves, resolve each file, `git add` it, commit, then continue to Step 6.

### Step 6 — Merge the testing branch

1. `git merge origin/<testing-branch> --no-commit --no-ff`.
2. If clean → Step 7.
3. If conflicts:
   - `git status --short` — capture every line with `UU`/`AU`/`UA`/`DU`/`UD`/`DD`/`AA`.
   - For each conflicted file, read both sides (`git show HEAD:<path>` and `git show MERGE_HEAD:<path>`) and explain the conflict with a proposed resolution.
   - **STOP and report** the full conflict analysis to the user. Wait for explicit approval before resolving anything.
   - After the user approves, resolve each file, `git add` it, and continue.

### Step 7 — Commit and offer to push

1. Once the index is clean (`git status --short` shows no unmerged paths):
   - `git commit -m "Merge branch '<testing-branch>' into dev/<suffix>"`
2. Ask the user before pushing. If approved:
   - `git push -u origin dev/<suffix>`

## Output format

End with a one-screen summary:

- **Source branch** (untouched): `<source>`
- **Integration branch**: `dev/<suffix>` — created / reused · pushed / not pushed
- **Source merged in** (Path B only): `<source>` · conflicts `<n>` (resolved / none)
- **Testing branch merged in**: `<testing-branch>` (host: GitHub / Bitbucket) · conflicts `<n>` (resolved / none)
- **Next step**: "Open a PR from `dev/<suffix>` → `<testing-branch>` in `<host>`."

## Hard rules

- **Never merge the testing branch into the source branch.** This skill exists specifically to prevent that contamination.
- **Never push the source branch.** Only the integration branch is pushed, and only with user approval.
- **Never force-update an existing `dev/<suffix>`.** If fast-forward pull fails or local/remote have diverged, stop and report — do not reset, rebase, or force-push.
- **Never guess the host.** If the remote URL isn't clearly GitHub or Bitbucket, stop and ask.
- **Never resolve conflicts without the user's explicit approval** of the proposed resolutions, file by file.
