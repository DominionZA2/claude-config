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

Read everything on the PR before reading any code. **Use all three endpoints** — inline comments, PR-level issue comments, and reviews — because anchoring notes often live at PR level when the offending lines are outside the diff hunks:

1. PR description (the `body` from step 1) — understand the intent.
2. Existing reviews: `gh pr view <num> --json reviews,comments` — who reviewed, what state, what they said.
3. **Full inline comment history**: `gh api repos/<owner>/<repo>/pulls/<num>/comments --paginate` — every inline comment from every prior session, not just the summary view.
4. **Full PR-level comment history**: `gh api repos/<owner>/<repo>/issues/<num>/comments --paginate` — PR-level notes (out-of-scope anchors, drift notes, verified-intentional behaviour changes) are issue comments on the PR, not inline review comments. Skipping this endpoint is how the review loop gets re-seeded with things that were already anchored.
5. Build a mental map: for every file + line in the diff, is there an existing comment thread? If yes, what was the conclusion? Anything already discussed — inline OR at PR level — is off-limits to re-raise.

**Why:** Re-flagging things that already have author-reply threads is the main cause of the review loop. Reading prior comments first prevents it. Half the terminal-state notes end up at PR level (not inline) because GitHub's inline-review API rejects lines outside the diff hunks — if you only read inline comments, you miss those anchors.

### Step 3 — Read the diff systematically

1. **Authoritative file list**: `git diff <base>...HEAD --stat`. This is the scope boundary. Capture it and keep it in mind — any finding MUST reference a file in this list. Files not in this list are out of scope regardless of how interesting the code looks.
2. Full diff: `gh pr diff <num> --patch` or `git diff <base>...HEAD`.
3. For each file in the scope list:
   - Read the hunks in the diff.
   - Read enough surrounding context to understand the change — use the `Read` tool on the actual files, not just the diff output.
   - For non-trivial changes, trace call sites of modified functions.
   - Check error paths and edge cases, not just happy paths.
4. If the PR description mentions companion repos (e.g., a backend PR for a frontend change), check those too — integration issues live at the boundary. This is the ONLY valid way to expand scope beyond the base diff.
5. Check CI status: `gh pr checks <num>` — failing checks are free findings.

**Scope-bleed hard rule:** Do not raise findings for files outside the `git diff <base>...HEAD --stat` output. External reviewers (especially AI reviewers) will sometimes hallucinate findings in unrelated files or in files they can see but which aren't actually being changed in this PR. When that happens, the correct response is to anchor a PR-level comment marking the finding as out-of-scope (with the verification command that showed the file isn't in the diff), NOT to try to fix it in this PR.

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
- Files not in the PR diff — external/AI reviewers sometimes raise findings for unrelated files. Verify against `git diff <base>...HEAD --stat` and reject outright, with a PR-level anchor so the next reviewer doesn't re-raise.
- Scope creep observations ("while you're here you should also...")
- Hypothetical concerns without evidence
- Things you checked and are correct but a future reviewer might flag

**Why the pre-existing verification is mandatory:** Retracting a finding in chat leaves no record. The next session re-discovers and re-raises. Verification + a "noted, pre-existing" comment on the PR breaks this loop.

**Why the scope-bleed check is mandatory:** Codex (and similar AI reviewers) occasionally raise findings for files that aren't in the PR diff because they scanned the broader checkout. If you fix those, you expand the PR scope and invite reviewer noise. If you silently reject them, the next AI pass re-raises the same thing. Anchor as PR-level comment with `git diff <base>...HEAD --stat` as the verification.

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
- `commit_id` must be the full 40-char SHA, not the short form. The API rejects short SHAs with a 422 Unprocessable Entity (`Variable $commitOID of type GitObjectID was provided invalid value`). Use `git rev-parse HEAD` not the short hash.
- Inline comment `line` must point to a line that actually appears in the diff on the `side` specified (`RIGHT` = new version, `LEFT` = old version). If the line is outside every hunk in the diff, the API returns 422 `Line could not be resolved`. **This is the main reason to use PR-level issue comments**: when you want to anchor a pre-existing issue, an out-of-scope finding, or any note tied to code that wasn't modified by this PR, the line is almost certainly outside the diff hunks. Post the anchor as a PR-level issue comment instead and explain in the body why it's PR-level (e.g., "the affected line is outside the diff hunks of this PR, so GitHub's inline-review API rejects it with 'Line could not be resolved'").
- If a thread was resolved previously, replying re-opens it. That's fine — sign-offs should do that.
- Self-approval is blocked by GitHub. If you are the PR author, a review with `event: "APPROVE"` returns `Can not approve your own pull request`. Use `event: "COMMENT"` and report that the PR needs a non-author human reviewer's formal approval to merge. Do not try to work around this.

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

Only approve if the PR is actually in a mergeable state from a review perspective. An approval is a durable marker that the restart check in Step 1 will respect in future sessions. **Self-approval is blocked by GitHub** — if you authored the PR, the APPROVE event fails. Use COMMENT and report that the PR needs a non-author reviewer.

## Iterative review loops with external reviewers (Codex / etc.)

This skill is designed for a single-pass review by me. But in practice, complex PRs often go through multiple review rounds: I review → I fix → an external reviewer (Codex, another human, another AI) finds more → I fix more → repeat. This section is the protocol for running those loops cleanly so they actually terminate instead of finding new stuff forever.

### Invoking an external reviewer

Use the `codex` skill (not the deprecated `ask-codex`). Pass a prompt that tells Codex:

1. The PR URL and the current HEAD SHA.
2. To read the full review history first via BOTH `gh api .../pulls/<num>/comments --paginate` AND `gh api .../issues/<num>/comments --paginate` before raising any findings.
3. To run `git diff <base>...HEAD --stat` first and only raise findings for files in that list.
4. What commits landed since the last Codex pass (so Codex knows it's verifying the latest fixes, not re-reviewing old state).
5. Explicitly: "If you find no new issues, say so with the phrase `NO NEW ISSUES`". This gives you a clean termination signal.

Run Codex in the background via `run_in_background: true` on the Bash tool. Codex takes minutes, not seconds — do NOT sleep/poll. Wait for the task-completion notification.

### The loop

1. Codex round finds N issues
2. For each issue: verify it's real (not scope bleed, not pre-existing, not already anchored). If real, fix → commit (single-purpose) → push → anchor with "Fixed in `<sha>`". If not real, anchor as out-of-scope with verification command.
3. Invoke Codex again with the new HEAD SHA and a summary of what landed since the last pass.
4. Repeat until Codex returns `NO NEW ISSUES` explicitly.

### Termination — do a proactive bug-class audit after the third reactive round

**This is the most important rule in this section.** Reactive review loops do not terminate by finding "the last bug". Each fix addresses the specific case the reviewer pointed at, and the next reviewer pass finds the next permutation of the same bug class in a different file or code path. The loop only terminates when you catch up to the bug CLASS, not the individual finding.

**Trigger:** If you are on the third reactive round on the same PR and at least two of the rounds produced findings from the same categories (e.g., tri-state conflation in round 1 and again in round 3), **stop the reactive loop and do a proactive audit** before invoking Codex again.

**The audit:** Take the list of bug classes you have seen in prior rounds. For each class, grep the ENTIRE PR diff for every potential instance and verify each one. Fix everything you find in single-purpose commits. Anchor every fix with a commit SHA and every pre-existing / intentional / out-of-scope instance with verification reasoning.

**The known bug classes worth auditing:**

1. **Silent error swallowing** — every `catch` block that converts a real error into an empty/default/placeholder value. Does it distinguish real failure from legitimate empty result? Does it propagate via a callback the caller expects?
2. **Tri-state conflation** — every place where `undefined` (unknown) is coerced into `false` (confirmed no) via `!!`, `?? false`, or truthy checks. Rendering layers are the usual offenders.
3. **In-flight state races** — every cache or mutable ref where a write can happen after an invalidation. Every `.set(cache, key)` after an `await`. Every `useRef` that holds async results. Look for missing generation tokens, missing epoch counters, missing request-id guards.
4. **Missing parent notification** — every server-side mutation (POST/PUT/DELETE) in child components. Does it trigger the parent's refresh path so sibling views update? Or does it only refresh the local view and leave siblings stale?
5. **Persisted-state backward compat** — every `localStorage` / `IndexedDB` / cookie read whose shape changed in this PR. Does the reader reject pre-change persisted entries cleanly? Use `'newField' in parsed` (not truthy check) to distinguish missing-key from explicit-null.
6. **Router plumbing** — every new parameter added to a service method. Does every caller pass it? Does it reach the backend in the request body/URL? Are there type-narrowing guards on the callers?

**After the audit:** invoke Codex one final time as a **verification pass, not a discovery pass**. Tell Codex explicitly that this is verification, that you want an explicit `NO NEW ISSUES` response, and that you specifically want each recent fix verified.

If Codex returns `NO NEW ISSUES`, the loop is closed. Post a final review comment documenting the verification and hand off.

If Codex finds more issues, the audit bug-class list was incomplete. Extend the list with the new class, re-audit the whole diff for that class, fix findings, verify again. This is recursion with a finite base case — new bug classes are discovered rarely, and each iteration leaves the PR strictly cleaner than before.

### Why this works

Reactive loops are infinite because each fix is narrower than the bug class it addresses. Proactive audits terminate because the set of bug classes is small (usually 4–8 for any given PR) and finite. Once every class has been swept, the only remaining findings are new classes you hadn't thought of — and those are rare.

Don't try to hack-terminate the loop by just marking the PR approved without fixing everything. That just ships bugs and burns the next reviewer.

## Hard rules (learned the hard way)

1. **Never re-review an already-approved PR at the same SHA.** Restart protection exists for this reason.
2. **Never raise a finding without verifying it's not pre-existing.** Run `git show <base>:<file>` before claiming something is a regression.
3. **Never raise a finding for a file outside the PR diff.** Run `git diff <base>...HEAD --stat` first and reject anything outside the list — including findings from external AI reviewers.
4. **Never let an observation live only in chat.** If I notice it, it goes on the PR as a comment with reasoning (inline if the line is in a diff hunk, PR-level issue comment otherwise).
5. **Never batch unrelated fixes into one commit.** Each commit is single-purpose.
6. **Never silently drop a finding.** Retractions become "noted, verified pre-existing" or "out of scope" comments so the next reviewer doesn't re-discover them.
7. **Source code is truth.** If the PR description disagrees with the code, update the description, not the code. Do it traceably — leave a PR-level comment explaining the edit.
8. **No scope creep.** Pre-existing cleanups, style improvements on untouched code, "while you're here" refactors — NOT findings.
9. **Take reviewer positions on open author trade-offs.** Don't leave "waiting for human reviewer" threads in limbo.
10. **After three reactive rounds, stop chasing and do a bug-class audit.** Don't invoke the external reviewer again until every known bug class has been swept across the whole PR diff. See the "Iterative review loops" section.
11. **The final external-reviewer invocation is a verification pass, not a discovery pass.** Require an explicit `NO NEW ISSUES` response to terminate the loop.
12. **Never try to self-approve.** If you are the PR author, submit review events as `COMMENT` only and report that the PR needs a non-author formal approval to merge.

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
