# AI Checkpoint Protocol

The load-bearing safety. Rules in ai-working-rules.md will be followed imperfectly; these checkpoints
are where human judgment is inserted by design, not by luck. Enforce via harness/hooks where possible,
not by trusting the assistant to remember.

## Plan → show → approve → execute → verify
For any operation that is destructive, outward-facing, or hard to reverse:
1. State the plan and the exact command(s).
2. Wait for explicit approval.
3. Execute.
4. Show evidence it did what was claimed (status/diff/output).

Applies to: commits, merges, pushes, branch creation/deletion, PR create/edit/close, DB writes,
anything sent to an external service.

## Two-key for irreversible
Never do these as a default or a suggestion. Require explicit, specific confirmation each time:
- force-push, history rewrite (rebase/reset --hard), branch deletion
- database writes/deletes
- deleting or overwriting files not created this session

## Review gate before "done"
- External review (e.g. Codex) must pass BEFORE retesting, so test effort isn't wasted on code that
  will change.
- Never imply "tested and good" until the review gate has actually run and passed.

## Decision vs generation split
- Generative/mechanical work (scaffolding, conflict edits, running checks, bulk transforms): run freely.
- Judgment work (which strategy, which files, which approach): present options with evidence and let the
  human decide. Do not free-run on judgment calls.

## Hook bypass is a flagged event
- Bypassing a hook (--no-verify) or skipping a gate must be stated explicitly and only with approval.
- Note what was bypassed and why, every time. Bypasses are not silent.
