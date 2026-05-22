# Create Todo

Build an HTML punch-list of work items and drive them through a strict per-item cycle (deliberate → implement → review → test → pause → commit).

## Usage

`/create-todo [scope-or-items]`

- **First invocation in a workstream** — pass a description of the work, a paste of items, or a pointer to a code review / Codex output that lists items. The command generates the HTML list.
- **Subsequent invocations** — invoke with no argument (or `continue`) to pick up where you left off and run the next unchecked item through its cycle.

The user invokes this explicitly. Never trigger it on your own.

## When this command is invoked

### PHASE A — Setup (only if no existing list)

1. Locate the workspace `.temp/` folder. From the current working directory walk up until you find one. If no `.temp/` exists at the workspace root, create it there. **Do not** create it inside a project subdirectory; `.temp/` lives at the workspace root.
2. Look for an existing punch-list HTML file in `.temp/` (default filename: `.temp/todo.html`). If one exists and has unchecked items, treat this as a continuation — go to PHASE B with that file.
3. If no list exists and the user passed no argument, ask the user what work they want listed. Do not guess a scope.
4. Take the scope/items the user provided and produce a punch list:
   - Group items by difficulty: **Easy → Medium → Hard**, easy first.
   - Each item must carry: a stable identifier (a short kebab-case `data-id`), a title, a difficulty badge, the locations/context (file paths and line numbers where applicable), the **problem**, the **fix intent**, and any **hidden coupling/risk** notes.
   - Items that are flagged but outside the current scope are grouped at the bottom in a separate "Outside scope" section with disabled checkboxes (tracked, not actionable).
   - Where the source material is ambiguous, ask the user — do not silently guess difficulty or risk.
5. Write the HTML file (see HTML template below). Suggested filename: `.temp/todo.html` for a single-workstream workspace. If the user wants the artifact named for the workstream (e.g. `.temp/auth-optimizations.html`), honour that.
6. Tell the user the file path, summarise the items it contains, and **stop**. Wait for them to review the list before starting any item.

### PHASE B — Per-item cycle

When the user gives the green light (or invokes `/create-todo continue`), pick the **next unchecked actionable item** from the HTML in document order. Always work top-down — never reorder for convenience.

Do every item through this exact cycle. Do not skip steps. Do not batch.

1. **Announce the item.** State the item's `data-id`, title, and what it touches. One sentence.
2. **Pre-implementation deliberation with Codex.** Send Codex a focused brief containing only this item's title, location, problem, proposed fix, and coupling notes. Ask Codex to either confirm the approach or push back with specifics. **Wait for Codex's reply before writing any code.** If Codex pushes back, reconcile and re-deliberate until both agree on the approach.
3. **Apply the change.** Single-purpose. Do not touch other items, do not refactor adjacent code "while you're there", do not rename unrelated things.
4. **Build.** Build the affected project(s). If the build fails, fix and rebuild — do not proceed with a broken build.
5. **Post-implementation code review with Codex.** Send Codex the actual diff (or the relevant file at HEAD) and the original brief. Ask for a sign-off on what was actually written. If Codex finds problems, address them and re-review. Do not move on with unresolved Codex feedback.
6. **Run targeted tests.** Run the test suite(s) covering the affected code. If anything fails, fix it before moving on.
7. **Live verification (if applicable).** If the change touches a runtime execution path (a controller, a service the running stack depends on, a sync-doc refresh, etc.), restart the relevant local services and exercise the path via curl / a real client. If the change is purely internal logic exercised by unit tests, this step is skipped — say so explicitly.
8. **Pause for human review.** Tell the user: which files changed, what tests ran (with pass count), and what live verification was or wasn't done. Wait. Do not propose to commit. Do not start the next item.
9. **Commit only on explicit human ask.** When the user says to commit, write a single-purpose commit message describing only this item's change. Never bundle multiple items into one commit.
10. **Tick the box and report progress.** After the commit lands, edit the HTML file directly to mark this item complete: add `done` to the `.item` element's class list (`class="item done"`), add `checked` to its checkbox (`<input type="checkbox" checked>`), and bump the progress count in the header if it's a hard-coded number. Tell the user the next item up and wait for their go. The HTML file is the authoritative state — the user refreshes the browser and sees the new state.

### Hard rules — non-negotiable

- **One item at a time.** Never start the next item before the current item is fully closed out (committed or explicitly deferred by the user).
- **Two Codex touchpoints per item.** Pre-implementation deliberation AND post-implementation review. Skipping either is a failure of the protocol.
- **Two human gates per item.** Human reviews before commit, human explicitly asks for commit. No auto-commit, ever.
- **Never expand scope inside an item.** If the work reveals a new issue, flag it for a follow-up item — do not fix it inline. Add the follow-up to the HTML's outside-scope section if appropriate, or just note it in chat.
- **HTML is the canonical workstream state.** Never track items in chat memory only. If something matters, it goes in the HTML.

## Codex deliberation — invocation pattern

For both the pre-implementation deliberation and the post-implementation review, run Codex from the project root (the directory containing the codebase being worked on, NOT the workspace root). Use synchronous invocation — Codex stalls when backgrounded for reasons that don't matter here.

```bash
codex exec --skip-git-repo-check -s read-only --cd "{PROJECT_ROOT}" "$(cat {PROMPT_FILE})" 2>&1 | tail -200
```

Where:
- `{PROJECT_ROOT}` is the codebase directory (the parent of the affected source files).
- `{PROMPT_FILE}` is a temporary file under `.temp/` containing the prompt for this Codex round.
- `-s read-only` for the deliberation step (Codex is reviewing, not modifying).
- The `tail -200` keeps the rendered output manageable.

**Pre-implementation prompt template:**

```
# Pre-implementation deliberation for item {DATA_ID}

## Item context
{TITLE}

Location: {FILE_PATHS_AND_LINES}

## Problem
{PROBLEM}

## Proposed fix
{FIX_INTENT}

## Hidden coupling / risks
{COUPLING_NOTES}

## Constraints
- Only this item is in scope. Do not propose changes outside the listed locations.
- Match the existing codebase conventions; do not introduce foreign abstractions.
- {OTHER_PROJECT_SPECIFIC_CONSTRAINTS}

## What I need from you
1. Do you agree with the proposed fix as stated? Yes / No / Yes-with-caveats.
2. If yes-with-caveats, name the caveats specifically (file:line, what changes).
3. If no, name the alternative and why.
4. Anything I missed in the coupling notes? Be specific.

Lead with the verdict. No restating my brief back to me.
```

**Post-implementation review prompt template:**

```
# Post-implementation review for item {DATA_ID}

## What was supposed to change
{ORIGINAL_FIX_INTENT}

## What actually changed
The diff is at {DIFF_PATH} (or read the current state of {FILE_PATHS}).

## What I need from you
1. Does the change match the agreed approach?
2. Are there bugs, missed edge cases, or scope creep?
3. Is anything broken or weakened that wasn't part of this item?

Lead with the verdict: ship / iterate / abort. If iterate, list the specific lines to revisit.
```

## HTML template

The HTML file is self-contained: inline CSS, inline JS. **The file itself is the authoritative state** — completion is encoded as `class="item done"` on the wrapper and a `checked` attribute on the checkbox. The JS does not persist anything; in-browser toggles are ephemeral and disappear on refresh. This keeps the file and the visual state in lockstep with what's actually been committed.

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{WORKSTREAM_TITLE}</title>
<style>
  :root {
    --bg: #0f1418;
    --panel: #161c22;
    --panel-2: #1d242b;
    --text: #d8dee4;
    --muted: #8a949e;
    --rule: #2a3138;
    --accent: #6cb6ff;
    --easy: #4ade80;
    --medium: #facc15;
    --hard: #fb923c;
    --done: #6b7280;
    --code-bg: #0b0f12;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 32px 24px 96px;
    background: var(--bg);
    color: var(--text);
    font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    max-width: 1080px;
    margin-left: auto;
    margin-right: auto;
  }
  h1 { font-size: 22px; font-weight: 600; margin: 0 0 8px; }
  .lede { color: var(--muted); margin: 0 0 28px; }
  .summary {
    background: var(--panel); border: 1px solid var(--rule); border-radius: 8px;
    padding: 14px 18px; margin-bottom: 28px; color: var(--muted); font-size: 14px;
  }
  .summary strong { color: var(--text); }
  h2 {
    font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em;
    color: var(--muted); margin: 32px 0 12px;
    border-bottom: 1px solid var(--rule); padding-bottom: 8px;
  }
  .item {
    background: var(--panel); border: 1px solid var(--rule); border-radius: 8px;
    padding: 18px 20px; margin-bottom: 14px; transition: opacity 0.15s ease;
  }
  .item.done { opacity: 0.45; }
  .item.done .title { text-decoration: line-through; text-decoration-color: var(--done); }
  .item-head { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 12px; }
  .item-head input[type=checkbox] {
    margin: 4px 0 0; width: 18px; height: 18px;
    accent-color: var(--accent); flex-shrink: 0; cursor: pointer;
  }
  .title { flex: 1; font-weight: 600; font-size: 16px; }
  .id { color: var(--muted); font-weight: 400; margin-right: 6px; }
  .badge {
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    padding: 3px 8px; border-radius: 4px; letter-spacing: 0.04em;
    background: var(--panel-2); color: var(--muted); flex-shrink: 0;
  }
  .badge.easy { background: rgba(74, 222, 128, 0.15); color: var(--easy); }
  .badge.medium { background: rgba(250, 204, 21, 0.15); color: var(--medium); }
  .badge.hard { background: rgba(251, 146, 60, 0.15); color: var(--hard); }
  .field { margin: 10px 0; }
  .field-label {
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--muted); margin-bottom: 4px;
  }
  .field-body { font-size: 14px; }
  code, .path {
    font-family: "JetBrains Mono", "Consolas", "Menlo", monospace;
    font-size: 13px; background: var(--code-bg); padding: 1px 6px;
    border-radius: 3px; color: #c1d3e4;
  }
  .paths { display: flex; flex-wrap: wrap; gap: 6px; }
  .controls { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; font-size: 13px; }
  .controls button {
    background: var(--panel); color: var(--text); border: 1px solid var(--rule);
    border-radius: 4px; padding: 6px 12px; cursor: pointer; font-size: 13px;
  }
  .controls button:hover { background: var(--panel-2); }
  .progress { color: var(--muted); margin-left: auto; }
  .progress strong { color: var(--accent); }
</style>
</head>
<body>

<h1>{WORKSTREAM_TITLE}</h1>
<p class="lede">{ONE_LINE_DESCRIPTION}</p>

<div class="summary">
<strong>Working rules</strong> — one item at a time, full test pass between items, each verified before moving to the next. Easy items first.
</div>

<div class="controls">
  <button onclick="resetAll()">Reset all</button>
  <span class="progress" id="progress">0 / {TOTAL} complete</span>
</div>

<h2>Easy</h2>
<!-- repeat .item blocks for each easy item -->

<h2>Medium</h2>
<!-- repeat for medium items -->

<h2>Hard</h2>
<!-- repeat for hard items -->

<h2>Outside scope — tracked, not actionable</h2>
<!-- items here use input type=checkbox with `disabled` attribute -->

<!-- .item template:
<div class="item" data-id="{KEBAB_ID}">
  <div class="item-head">
    <input type="checkbox">
    <span class="title"><span class="id">#{N}</span>{TITLE}</span>
    <span class="badge {easy|medium|hard}">{Easy|Medium|Hard}</span>
  </div>
  <div class="field">
    <div class="field-label">Location</div>
    <div class="field-body paths"><span class="path">file.cs:123</span> <span class="path">other.cs:45-67</span></div>
  </div>
  <div class="field">
    <div class="field-label">Problem</div>
    <div class="field-body">{PROBLEM}</div>
  </div>
  <div class="field">
    <div class="field-label">Fix</div>
    <div class="field-body">{FIX_INTENT}</div>
  </div>
  <div class="field">
    <div class="field-label">Coupling</div>
    <div class="field-body">{RISKS_OR_COUPLING}</div>
  </div>
</div>
-->

<script>
// The HTML file is the authoritative state — items marked done via `class="done"`
// on the `.item` and `checked` on the checkbox are the source of truth.
// In-browser toggles are ephemeral and reset on refresh.
(function () {
  const items = Array.from(document.querySelectorAll(".item"));
  const checkboxes = items.map(i => i.querySelector("input[type=checkbox]"));
  const progress = document.getElementById("progress");

  function updateProgress() {
    const total = checkboxes.filter(cb => !cb.disabled).length;
    const done = checkboxes.filter(cb => !cb.disabled && cb.checked).length;
    progress.innerHTML = `<strong>${done}</strong> / ${total} complete`;
  }
  checkboxes.forEach((cb, idx) => {
    cb.addEventListener("change", () => {
      items[idx].classList.toggle("done", cb.checked);
      updateProgress();
    });
  });
  window.resetAll = function () {
    if (!confirm("Reset all checkboxes in-browser only? (File state is unchanged — refresh to restore.)")) return;
    checkboxes.forEach((cb, idx) => {
      if (cb.disabled) return;
      cb.checked = false;
      items[idx].classList.remove("done");
    });
    updateProgress();
  };
  updateProgress();
})();
</script>

</body>
</html>
```

## Notes

- The HTML's checkbox state lives in `localStorage` in the user's browser. The file itself doesn't change as items are completed — the user ticks them off in the browser, you read the state by asking. Do not try to script the file's HTML to "mark items done"; that would clobber the source of truth.
- If you need to add a newly discovered item to an existing list, append a new `.item` block to the appropriate difficulty section. Use a fresh kebab-case `data-id` that hasn't been used before.
- If the user wants to abandon a workstream, leave the HTML in place. Don't auto-delete.
- This command is workstream-agnostic. The items can be optimizations, refactors, bug fixes, PR feedback, backlog items, code-review findings — anything that benefits from one-at-a-time discipline with Codex sign-off.
- When in doubt about scope, slow down and ask. The cost of asking is a sentence; the cost of guessing is a tangled commit.
