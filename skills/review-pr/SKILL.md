---
name: review-pr
description: Structured single-pass PR code review. Use when asked to review or code-review a pull request. Every observation becomes a comment on the PR with reasoning so nothing is re-discovered in a future session.
argument-hint: <pr-number-or-url>
disable-model-invocation: true
allowed-tools: Bash(gh *) Bash(git *) Read Grep Glob Edit
---

# Code Review — Pull Request

Structured single-pass code review for pull request **$ARGUMENTS**.

The goal: a definitive review that catches real issues, records every observation on the PR itself, and leaves the PR in a state where a future review session can see exactly what was considered and why — without re-deriving anything.

## Core principle

**Every observation that could plausibly be re-raised by a future reviewer must become a comment on the PR with reasoning.** Not just real findings. Also style nits being ignored, suspected issues verified as pre-existing, deliberate trade-offs being signed off on, and non-obvious things verified as correct.

**Why:** Observations that live only in chat evaporate. The next session re-discovers them and either re-raises them or wastes cycles re-concluding they're fine. The PR is the durable record of the review, not the conversation.

## Procedure

### Step 1 — Pre-flight and restart protection

Before reading any code:

1. Identify the repository. If in a worktree with multiple projects, check which repo the PR belongs to (`gh pr view <num>` succeeds only in the correct repo).
2. Get PR metadata: `gh pr view <num> --json number,title,state,headRefOid,headRefName,baseRefName,body,url,mergeable,reviewDecision`
3. **Restart check** — look for prior reviews by the current user:
   - `gh pr view <num> --json reviews` and filter for my own login
   - If there's a prior review from me at the current `headRefOid`: STOP. Report "Already reviewed at `<sha>` — no new commits since. Nothing to do."
   - If there's a prior review from me at an older SHA: limit the new review scope to commits in `<old-sha>..HEAD`, not the full PR diff.

**Why the restart check exists:** Without it, every fresh conversation re-scans the full PR and produces a different set of nits each time. This is the #1 failure mode this skill exists to prevent.

### Step 2 — Ingest all existing discussion

Read everything on the PR before reading any code:

1. PR description (the `body` from step 1) — understand the intent.
2. Existing reviews: `gh pr view <num> --json reviews,comments` — who reviewed, what state, what they said.
3. Full inline comment history: `gh api repos/<owner>/<repo>/pulls/<num>/comments --paginate` — every inline comment from every prior session, not just the summary view.
4. Build a mental map: for every file + line in the diff, is there an existing comment thread? If yes, what was the conclusion? Anything already discussed is off-limits to re-raise.

**Why:** Re-flagging things that already have author-reply threads is the main cause of the review loop. Reading prior comments first prevents it.

### Step 3 — Read the diff systematically

1. Full list of changed files: `gh pr diff <num> --patch` or `git diff <base>...HEAD --stat`.
2. For each file:
   - Read the hunks in the diff.
   - Read enough surrounding context to understand the change — use the `Read` tool on the actual files, not just the diff output.
   - For non-trivial changes, trace call sites of modified functions.
   - Check error paths and edge cases, not just happy paths.
3. If the PR description mentions companion repos (e.g., a backend PR for a frontend change), check those too — integration issues live at the boundary.
4. Check CI status: `gh pr checks <num>` — failing checks are free findings.

### Step 4 — Finding discipline

Strict threshold for what counts as a finding. This is the gate that prevents noise.

**Real findings (require action):**
- Bugs, regressions, correctness issues
- Security issues
- Type or lint errors
- Missing tests for new behavior
- Broken integration with companion code

**Not findings (but still get a comment — see Step 5):**
- Style nits (redundant wrappers, formatting, minor naming)
- Pre-existing issues that predate this PR — **MUST verify** via `git show <base>:<file>` before even mentioning
- Scope creep observations ("while you're here you should also...")
- Hypothetical concerns without evidence
- Things you checked and are correct but a future reviewer might flag

**Why the pre-existing verification is mandatory:** Retracting a finding in chat leaves no record. The next session re-discovers and re-raises. Verification + a "noted, pre-existing" comment on the PR breaks this loop.

### Step 5 — Every observation becomes a comment

For **every** observation — real finding or not — post a comment on the PR with reasoning. Use these templates:

**Real finding to fix (new finding, not yet addressed):**
```
[Problem description in specific terms]

[Why it matters — user impact, correctness risk]

[Suggestion or question]
```

**Real finding — fixed by me in this session:**
```
**[One-line problem summary] — fixed in `<sha>`.**

[Problem description]

Fix: [what I changed]
```
Post this AFTER committing the fix, with the actual commit SHA.

**Style nit, intentionally not fixed:**
```
**Noted — style nit, intentionally not fixed.**

[The observation]

Not changing it: [reason — style only, functionally correct, scope creep]. Anchoring this so a future review pass doesn't re-raise it.
```

**Pre-existing issue, verified:**
```
**Noted — pre-existing, out of scope.**

[The observation]

Verified via `git show <base>:<file>` — [what the verification showed]. Not a regression introduced by this PR.

[Why not fixing it here — scope creep, separate cleanup PR]. Anchoring this so future reviewers don't re-discover and re-raise it.
```

**Non-obvious thing checked and correct:**
```
**Verified — [thing].**

[What was checked and why it's not obviously right]

[The reasoning that makes it correct]

Anchoring this so the next reviewer doesn't re-derive.
```

**Reviewer sign-off on an existing author "deliberate" thread** (reply on the existing thread):
```
**Reviewer: Accepted.** [reason]
```
or
```
**Reviewer: Reject.** [reason and what I want instead]
```

### Step 6 — Posting mechanics

**Grouped review with inline comments** (new observations on specific lines):
```bash
gh api repos/<owner>/<repo>/pulls/<num>/reviews --method POST --input - <<'EOF'
{
  "commit_id": "<full 40-char SHA>",
  "event": "COMMENT",
  "body": "<overall review body>",
  "comments": [
    {
      "path": "path/to/file.ts",
      "line": 123,
      "side": "RIGHT",
      "body": "<comment markdown>"
    }
  ]
}
EOF
```

**PR-level comment** (meta concerns not tied to a specific line):
```bash
gh api repos/<owner>/<repo>/issues/<num>/comments --method POST -f body="..."
```

**Reply to an existing comment thread**:
```bash
gh api repos/<owner>/<repo>/pulls/<num>/comments/<comment_id>/replies --method POST -f body="..."
```

**Gotchas:**
- `commit_id` must be the full 40-char SHA, not the short form. The API rejects short SHAs with a 422 Unprocessable Entity.
- Inline comment `line` must point to a line that actually appears in the diff on the `side` specified (`RIGHT` = new version, `LEFT` = old version).
- If a thread was resolved previously, replying re-opens it. That's fine — sign-offs should do that.

### Step 7 — Fix loop for real findings

For each finding fixed in this session:

1. Make the edit locally with the `Edit` tool.
2. Verify no unrelated changes in working tree: `git status`, `git diff --stat`.
3. Commit single-purpose: `git commit -m "fix(area): <specific change>"`. Clean, focused message. **Do not** batch multiple unrelated fixes into one commit.
4. Push: `git push origin <branch>`.
5. Capture the new full SHA: `git rev-parse HEAD`.
6. Post the inline comment with `Fixed in <sha>` referencing that full SHA.

**Why single-purpose commits:** Future reviewers read commit history to understand what changed since the last review. Multi-purpose commits break that trail.

### Step 8 — Close every thread to a terminal state

Before finishing the review, every thread on the PR must be in one of these terminal states:

- **Fixed** — "Fixed in `<sha>`"
- **Rejected** — "Not fixing — `<reason>`"
- **Deferred** — "Deferring — `<reason>` — tracked in `<where>`"
- **Noted** — "Noted — `<reason why no action>`"
- **Verified** — "Verified — `<reason it's correct>`"
- **Still open** — unresolved finding requiring a human response

No thread in limbo. No "waiting for reviewer consensus" without an actual reviewer taking a position — if I'm functionally the reviewer, I take a position.

Mark conversations as resolved on GitHub for anything with a terminal state except "still open".

### Step 9 — Submit the review event

- `COMMENT` — advisory (observations + noted items, no blocking changes requested)
- `REQUEST_CHANGES` — unresolved real findings the author must address before merge
- `APPROVE` — review is clean OR every real finding is fixed and every observation is anchored

Only approve if the PR is actually in a mergeable state from a review perspective. An approval is a durable marker that the restart check in Step 1 will respect in future sessions.

## Hard rules (learned the hard way)

1. **Never re-review an already-approved PR at the same SHA.** Restart protection exists for this reason.
2. **Never raise a finding without verifying it's not pre-existing.** Run `git show <base>:<file>` before claiming something is a regression.
3. **Never let an observation live only in chat.** If I notice it, it goes on the PR as a comment with reasoning.
4. **Never batch unrelated fixes into one commit.** Each commit is single-purpose.
5. **Never silently drop a finding.** Retractions become "noted, verified pre-existing" comments so the next reviewer doesn't re-discover them.
6. **Source code is truth.** If the PR description disagrees with the code, update the description, not the code. Do it traceably — leave a PR-level comment explaining the edit.
7. **No scope creep.** Pre-existing cleanups, style improvements on untouched code, "while you're here" refactors — NOT findings.
8. **Take reviewer positions on open author trade-offs.** Don't leave "waiting for human reviewer" threads in limbo.

## Instructions for the AI

When this skill is invoked:

1. Execute Steps 1–2 (pre-flight + ingest existing discussion) before reading any code. If restart protection triggers, stop and report.
2. Execute Step 3 (systematic diff reading) in full. Do not skim files that look routine.
3. While reading, collect observations. For each, classify per Step 4 — real finding, nit, pre-existing (verify via `git show <base>:<file>`!), verified-correct, or scope creep.
4. Group observations into the comment templates from Step 5.
5. For real findings being fixed in this session, run the Step 7 fix loop.
6. Post the grouped review (Step 6) with all inline comments. Post PR-level comments for meta concerns. Post thread replies for reviewer sign-offs on existing author threads.
7. Close every thread per Step 8.
8. Submit the review event per Step 9.
9. Report final state to the user: what was found, what was fixed, what was noted, what's still open, review event submitted.

Never debate findings with the user before posting them. Post first, discuss after. The PR is the source of truth, not the chat.
