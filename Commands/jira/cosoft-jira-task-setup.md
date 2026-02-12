# Jira Task Setup Pipeline

Run the Jira task workflow from setup through code review — sequentially, stopping on any failure.

**Note:** Worktree creation (`/jira:cosoft-jira-00-create-worktree`) must be run manually before this command, as it creates a new working directory that you need to switch to first.

## What this command does

Executes the Jira task pipeline in order:

1. **01 - Setup** (`/jira:cosoft-jira-01-setup`) — Fetch all task details, linked tasks, branch status analysis, create task markdown
2. **02 - Plan** (`/jira:cosoft-jira-02-plan`) — Analyze task and codebase, create implementation plan
3. **03 - Deliberate Plan** (`/jira:cosoft-jira-03-deliberate-plan-codex`) — AI/Codex deliberation over the plan until consensus
4. **04 - Implement** (`/jira:cosoft-jira-04-implement`) — Implement code changes according to the agreed plan
5. **05 - Code Review** (`/jira:cosoft-jira-05-deliberate-code-review-codex`) — AI/Codex code review deliberation, implement fixes, verify

**Usage:** `/jira:jira-task-setup {TASK_NUMBER} [optional additional prompt]`

- `{TASK_NUMBER}`: Required. The Jira task key (e.g., "ACR-678" or "API-708")
- `[optional additional prompt]`: Optional. Passed through to every step that supports it (02-05)

**Example:** `/jira:jira-task-setup ACR-678 Pay special attention to performance implications`

## Instructions for the AI

When this command is invoked:

### INPUT PARSING

- Parse the user's input to extract:
  - **Task number:** First token/word (e.g., "ACR-678" or "API-708")
  - **Additional prompt (optional):** Any text after the task number
- If no task number is provided, ask the user for it and STOP until they provide one
- Store the task number as `TASK_NUMBER` and any extra text as `ADDITIONAL_PROMPT`

### PIPELINE EXECUTION

Execute each step below **in order**. After each step, check whether it succeeded. If any step fails, **STOP the entire pipeline immediately** — do not proceed to the next step. Report which step failed and the error details.

Between steps, display a clear separator so the user can see progress:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Step {N} complete. Proceeding to Step {N+1}...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If a step fails, display:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Step {N} FAILED. Pipeline halted.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

#### STEP 1: Setup (01)

- **What to do:** Execute the full instructions from `/jira:cosoft-jira-01-setup` with `TASK_NUMBER`
- **Additional prompt:** If `ADDITIONAL_PROMPT` exists, pass it through
- **Success criteria:** Task details markdown file exists at `.temp/{TASK_NUMBER}/{TASK_NUMBER}-task-details.md`, summary is displayed
- **On failure:** STOP pipeline. Display the error.

---

#### STEP 2: Plan (02)

- **What to do:** Execute the full instructions from `/jira:cosoft-jira-02-plan` with `TASK_NUMBER`
- **Additional prompt:** If `ADDITIONAL_PROMPT` exists, pass it through
- **Success criteria:** Implementation plan file exists at `.temp/{TASK_NUMBER}/{TASK_NUMBER}-implementation-plan.md`, summary is displayed
- **On failure:** STOP pipeline. Display the error.

---

#### STEP 3: Deliberate Plan with Codex (03)

- **What to do:** Execute the full instructions from `/jira:cosoft-jira-03-deliberate-plan-codex` with `TASK_NUMBER`
- **Additional prompt:** If `ADDITIONAL_PROMPT` exists, pass it through
- **Success criteria:** Deliberation completed (agreement reached or limit reached), plan updated with deliberation history
- **On failure:** STOP pipeline. Display the error.
- **Note:** This step involves multiple rounds of AI/Codex deliberation. Let the full deliberation process run to completion.

---

#### STEP 4: Implement (04)

- **What to do:** Execute the full instructions from `/jira:cosoft-jira-04-implement` with `TASK_NUMBER`
- **Additional prompt:** If `ADDITIONAL_PROMPT` exists, pass it through
- **Success criteria:** Implementation is complete, files created/modified as per plan, summary is displayed
- **On failure:** STOP pipeline. Display the error.

---

#### STEP 5: Code Review with Codex (05)

- **What to do:** Execute the full instructions from `/jira:cosoft-jira-05-deliberate-code-review-codex` with `TASK_NUMBER`
- **Additional prompt:** If `ADDITIONAL_PROMPT` exists, pass it through
- **Success criteria:** Code review deliberation complete, all agreed recommendations implemented, final consensus reached (or limit reached)
- **On failure:** STOP pipeline. Display the error.
- **Note:** This step involves multiple rounds of code review deliberation. Let the full process run to completion.

---

### PIPELINE COMPLETION

When all 5 steps complete successfully, display a final summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ JIRA TASK SETUP PIPELINE COMPLETE: {TASK_NUMBER}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Steps completed:
  1. ✅ Task details fetched
  2. ✅ Implementation plan created
  3. ✅ Plan deliberation complete
  4. ✅ Implementation complete
  5. ✅ Code review complete

Task files: .temp/{TASK_NUMBER}/
Next step: Merge & release changes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### CRITICAL RULES

1. **Sequential execution only.** Never skip ahead or run steps in parallel.
2. **Stop on failure.** If any step fails, halt immediately. Do not attempt the next step.
3. **Each step uses its own command's full instructions.** You are not summarizing or shortcutting the individual commands — you execute each one as if the user had typed it directly. Follow every instruction, every validation, every phase defined in each command.
4. **Preserve context between steps.** The task number and project root carry forward through all steps. Each step's output feeds into the next step's input.
5. **Pass the additional prompt through.** If the user provided extra instructions, pass them to every step that accepts an additional prompt (Steps 1-5).

### ERROR HANDLING

- If Python/scripts are missing: STOP at the failing step, display instructions
- If Jira credentials are missing: STOP at the failing step, display setup instructions
- If git operations fail: STOP at the failing step, display the git error
- If Codex is not available (Steps 4, 6): STOP at the failing step, inform the user
- If any file cannot be read or written: STOP at the failing step, display the file error
- For any other error: STOP at the failing step, display full error details

The user can fix the issue and re-run the pipeline, or run the individual step command that failed.
