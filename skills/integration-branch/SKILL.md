---
name: integration-branch
description: Create a throwaway integration branch off the current branch, merge the appropriate target into it, and surface conflicts for resolution — without polluting the original branch. Auto-detects GitHub (staging/main) vs Bitbucket (develop/master) from the remote URL.
argument-hint: [testing|production]
disable-model-invocation: true
allowed-tools: Bash(git *) Read
---

# Integration branch

Create a sibling branch for merging **$ARGUMENTS** into, so the conflict-resolution work doesn't contaminate the original feature/hotfix branch.

## When to use

The user is on a feature/hotfix branch based off production. They want to PR it into a pre-production testing branch (develop on Bitbucket, staging on GitHub), but that target has diverged and the PR shows conflicts.

Merging the target *into* the feature branch would pollute it with unrelated changes that shouldn't go to production later. Instead, create a disposable integration branch off the feature branch, merge the target there, and PR *that* into the testing target.

The feature branch stays clean for its eventual PR into production.

## Terminology

- **Source branch**: the current branch (typically `feature/<suffix>` or `hotfix/<suffix>`). Stays untouched.
- **Integration branch**: new branch created off the source, prefixed `dev/<suffix>`. Disposable.
- **Target branch**: what we merge into the integration branch. Depends on argument + remote host:

  | Intent     | Bitbucket | GitHub    |
  |------------|-----------|-----------|
  | testing    | `develop` | `staging` |
  | production | `master`  | `main`    |

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
4. Candidate integration branch: `dev/<suffix>`. Stop and ask if it already exists:
   - Local: `git show-ref --verify --quiet refs/heads/dev/<suffix>`
   - Remote: `git ls-remote --heads origin dev/<suffix>`

### Step 2 — Detect host and pick the target branch

1. `git remote get-url origin` (fall back to any upstream remote if origin is missing).
2. Classify:
   - URL contains `github.com` → **GitHub**
   - URL contains `bitbucket.org` → **Bitbucket**
   - Anything else → stop and ask the user which convention applies.
3. Default the argument to `testing` if none was provided.
4. Map using the table above to pick the target branch.

### Step 3 — Fetch and verify the target

1. `git fetch origin <target>` — must succeed.
2. `git show-ref --verify --quiet refs/remotes/origin/<target>` — must exist.

### Step 4 — Create the integration branch

1. `git checkout -b dev/<suffix>` (from the current source-branch HEAD).
2. Sanity check: `git branch --show-current` returns `dev/<suffix>`.

### Step 5 — Merge the target

1. `git merge origin/<target> --no-commit --no-ff`.
2. If clean → Step 6.
3. If conflicts:
   - `git status --short` — capture every line with `UU`/`AU`/`UA`/`DU`/`UD`/`DD`/`AA`.
   - For each conflicted file, read both sides (`git show HEAD:<path>` and `git show MERGE_HEAD:<path>`) and explain the conflict with a proposed resolution.
   - **STOP and report** the full conflict analysis to the user. Wait for explicit approval before resolving anything.
   - After the user approves, resolve each file, `git add` it, and continue.

### Step 6 — Commit and offer to push

1. Once the index is clean (`git status --short` shows no unmerged paths):
   - `git commit -m "Merge branch '<target>' into dev/<suffix>"`
2. Ask the user before pushing. If approved:
   - `git push -u origin dev/<suffix>`

## Output format

End with a one-screen summary:

- **Source branch** (untouched): `<source>`
- **Integration branch**: `dev/<suffix>` — pushed / not pushed
- **Target merged in**: `<target>` (host: GitHub / Bitbucket)
- **Conflicts**: `<n>` (resolved / none)
- **Next step**: "Open a PR from `dev/<suffix>` → `<target>` in `<host>`."

## Hard rules

- **Never merge the target into the source branch.** This skill exists specifically to prevent that contamination.
- **Never push the source branch.** Only the integration branch is pushed, and only with user approval.
- **Never reuse an existing `dev/<suffix>`.** It may have its own history — blowing it away could lose work.
- **Never guess the host.** If the remote URL isn't clearly GitHub or Bitbucket, stop and ask.
- **Never resolve conflicts without the user's explicit approval** of the proposed resolutions, file by file.
