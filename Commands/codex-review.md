# Codex Review

Point Codex at specific files, a plan, or a topic in the codebase and get a critical review.

## Usage

`/codex-review <file-or-topic> [optional additional instructions]`

## Instructions

When this command is invoked:

1. Parse the argument:
   - The first argument can be a file path, a task number (e.g., "API-759"), or a topic description
   - Any text after the first argument is treated as additional instructions for the review
2. Determine what to review:
   - **If a task number is provided** (matches pattern like `ABC-123`): Review the implementation plan at `.temp/{TASK_NUMBER}/{TASK_NUMBER}-implementation-plan.md` plus the task details at `.temp/{TASK_NUMBER}/{TASK_NUMBER}-task-details.md`
   - **If a file path is provided**: Review that specific file
   - **If a topic/description is provided**: Pass it as-is and let Codex explore the codebase
3. Determine the project root:
   - Search for `.temp/` in the workspace to find the project root
   - If found, the project root is the parent directory of `.temp`
   - Otherwise, use the current working directory
4. Construct the review prompt (see Prompt Templates below)
5. Run Codex using the Bash tool directly (do NOT spawn a sub-agent):
   - Pipe the prompt via stdin using a heredoc
   - Use `--full-auto` for autonomous execution
   - Use `--skip-git-repo-check` for worktree compatibility
   - Use `-o` to write the response to a file in the task folder (if task number) or a temp location
   - Run in background since Codex can take several minutes
6. When Codex completes, read the output file and display the response to the user verbatim.

### Prompt Templates

#### For Task Number Reviews

```
Read the following files:
- .temp/{TASK_NUMBER}/{TASK_NUMBER}-task-details.md (the original task requirements)
- .temp/{TASK_NUMBER}/{TASK_NUMBER}-implementation-plan.md (the implementation plan)

CRITICAL: You must thoroughly understand the code before making any assessment:
- Examine ALL relevant source files mentioned in the plan
- Read and comprehend the existing implementation completely
- Understand the architecture, patterns, dependencies, and data flow
- NO GUESSES. NO ASSUMPTIONS. Every assessment must be based on complete code understanding.
- If you need to examine additional files to understand the code, do so

STAY FOCUSED ON TASK-RELATED CODE:
- Only discuss code DIRECTLY related to this task
- Do NOT drift into general surrounding code or unrelated areas

Critically review the implementation plan:
a. Is the root cause analysis correct? Are there any unverified assumptions?
b. Is the proposed fix sufficient and correct?
c. Are there any other possible root causes we might be missing?
d. Does the test strategy correctly reproduce the bug (if applicable)?
e. Are the test scenarios comprehensive enough?
f. Are there any issues with the test class structure or mocking setup?
g. Any other concerns, gaps, or errors in the plan?

Be thorough and critical. Challenge any assumptions you find. If you disagree with anything, explain why with evidence from the code.

{ADDITIONAL_INSTRUCTIONS}

Structure your response in markdown format with clear sections.
```

#### For File Path Reviews

```
Read and critically review the following file:
- {FILE_PATH}

CRITICAL: Thoroughly understand the code before making assessments. Read related files if needed for context. NO GUESSES. NO ASSUMPTIONS.

{ADDITIONAL_INSTRUCTIONS}

Provide your assessment in markdown format with clear sections.
```

#### For Topic/Description Reviews

```
{TOPIC_DESCRIPTION}

CRITICAL: Thoroughly understand the code before making assessments. Read all relevant files. NO GUESSES. NO ASSUMPTIONS.

{ADDITIONAL_INSTRUCTIONS}

Provide your assessment in markdown format with clear sections.
```

### Command Template

```bash
cd {PROJECT_ROOT} && cat <<'CODEX_PROMPT_EOF' | codex exec --skip-git-repo-check --full-auto -o {OUTPUT_FILE} -
{CONSTRUCTED_PROMPT}
CODEX_PROMPT_EOF
```

Where:
- `{PROJECT_ROOT}` is the project root directory
- `{OUTPUT_FILE}` is:
  - For task reviews: `.temp/{TASK_NUMBER}/codex-review.md`
  - For file/topic reviews: `/tmp/codex-review-{timestamp}.md`
- `{CONSTRUCTED_PROMPT}` is the fully constructed prompt from the templates above

### Key Details

- **Heredoc stdin**: The prompt is piped via `cat <<'CODEX_PROMPT_EOF'` with single-quoted delimiter to prevent shell expansion.
- **`--full-auto`**: Runs Codex autonomously without interactive prompts.
- **`--skip-git-repo-check`**: Required for worktrees or non-git directories.
- **`-o {file}`**: Writes only the final agent response to the specified file.
- **Background execution**: Use `run_in_background: true` on the Bash tool since Codex typically takes 1-5 minutes.
- **Timeout**: Set the Bash timeout to 600000 (10 minutes).

### Error Handling

- If the task folder doesn't exist: "Task folder `.temp/{TASK_NUMBER}/` not found. Please run `/cosoft-jira-01-setup {TASK_NUMBER}` first."
- If the plan file doesn't exist: "No implementation plan found. Please run `/cosoft-jira-02-plan {TASK_NUMBER}` first."
- If Codex fails: Report the error message to the user.
- If the output file is empty: Report that Codex produced no output.

### Notes

- This skill is purpose-built for getting critical reviews of plans, files, or code topics.
- For general-purpose prompts, use `/codex` instead.
- The review prompt explicitly instructs Codex to challenge assumptions and find gaps — it's designed to be a critical second opinion.
