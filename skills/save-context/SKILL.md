---
name: save-context
description: Save the current conversation's working context to a markdown file at <git-root>/.temp/<branch>-context.md. Captures Goal, State, Constraints, and Next so a future session can resume without /compact's lossy summary. Updates in place if the file already exists.
disable-model-invocation: true
allowed-tools: Bash(git *) Bash(test *) Bash(mkdir *) Bash(stat *) Read Write Edit Glob
---

# Save context

Persist the working context of the current conversation to disk so a future session (after /clear) can resume cleanly.

This is a deliberate alternative to /compact. /compact summarises what was *said*; this captures what is *true now*. Decisions and constraints are the load-bearing pieces — preserve them explicitly.

## When to use

- Mid-session checkpoint when context climbs past ~40% of the usable budget.
- Right before /clear at end of session.
- Whenever a meaningful decision is made that future-you would want to know without re-reading the transcript.

## Procedure

### Step 1 — Resolve target file

1. `git rev-parse --show-toplevel` — git root. If this fails (not in a repo), stop and ask the user for an explicit path.
2. `git branch --show-current` — current branch. If empty (detached HEAD), use `detached-<short-sha>` from `git rev-parse --short HEAD`.
3. Sanitise the branch name: replace `/` with `-`.
4. Default file path: `<git-root>/.temp/<sanitised-branch>-context.md`.
5. If the user passed an argument, treat it as an override path (absolute or relative to cwd).

### Step 2 — Check .gitignore

1. Read `<git-root>/.gitignore` if it exists.
2. If it does not list `.temp/` or `.temp`, warn the user once at the end of the run. Do NOT auto-edit `.gitignore`.

### Step 3 — Read or create

If the file exists:
- Read it. Edit in place to reflect what changed in this session.
- Preserve sections the user has manually customised.
- Update the timestamp line and refresh State / Next to reflect current reality.

If it does not exist:
- Create the `.temp/` directory if missing.
- Write the template below, filled in from current conversation context.

### Step 4 — Template

```markdown
# Context: <branch>

_Last updated: <YYYY-MM-DD HH:MM>_

## Goal
One paragraph: what we're actually trying to ship and why.

## State
What exists now — files touched, decisions locked in, what's been merged or PR'd. Bullet points, current as of the timestamp above.

## Constraints / decisions
The *why* behind choices that aren't obvious from the code or git log. This is the part /compact destroys. Each entry: short rule + reason.

## Next
The single concrete next action. Not a roadmap — just what's at the top of the pile.
```

### Step 5 — Confirm

Output the file path and a one-line summary of what was saved (created vs. updated, sections changed). Mention the `.gitignore` warning if applicable.

## Hard rules

- Never auto-edit `.gitignore` — warn only.
- Never delete sections the user has manually customised.
- Never stage or commit the file — leave it in the working tree.
- File contents are forward-looking state, not a transcript summary. If the conversation was mostly debate that didn't land, the file should reflect what was *decided*, not what was *discussed*.
- If the user invoked this skill and there is genuinely nothing new since the last save, say so plainly — do not invent changes to look productive.
