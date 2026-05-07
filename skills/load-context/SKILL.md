---
name: load-context
description: Load a previously-saved working context file from <git-root>/.temp/<branch>-context.md and resume work from its Next section. Treats the file as source of truth — does not re-derive state from git log or codebase.
disable-model-invocation: true
allowed-tools: Bash(git *) Bash(stat *) Read
---

# Load context

Resume work in a fresh session by loading the persisted context file written by `/save-context`.

## When to use

First thing in a session that follows a `/clear`, when a saved context file exists for the current branch.

## Procedure

### Step 1 — Resolve target file

1. `git rev-parse --show-toplevel` — git root. If this fails, stop and ask the user for the path.
2. `git branch --show-current` — current branch (or `detached-<short-sha>` if detached).
3. Sanitise the branch name: replace `/` with `-`.
4. Default file path: `<git-root>/.temp/<sanitised-branch>-context.md`.
5. If the user passed an argument, treat it as an override path.

### Step 2 — Check existence

If the file does not exist: stop and tell the user. Suggest running `/save-context` at the end of a session to create one. Do not search the codebase or git log to manufacture state.

### Step 3 — Read and present

1. Read the file.
2. Note its mtime (filesystem timestamp). If older than 7 days, flag it as potentially stale.
3. Output:
   - The file path.
   - File age.
   - The **Next** section as a one-liner — that is the action to start from.

### Step 4 — Treat as source of truth

After loading, do not re-derive state. The file's State and Constraints sections are authoritative as of the timestamp inside it. If something in the live codebase later contradicts the file, prefer the live state and offer to update the file via `/save-context`.

## Hard rules

- Never search the codebase to "verify" the loaded context unless the user asks. The point of the file is to skip that re-discovery.
- Never auto-update the file on load — that is `/save-context`'s job.
- If the file is older than 7 days, surface that explicitly so the user can decide whether the state is still trustworthy.
