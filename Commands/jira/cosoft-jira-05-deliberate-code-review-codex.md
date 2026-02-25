# Jira Task Code Review with Codex Command

Perform iterative code review deliberation between AI and Codex over actual implementation changes, implement agreed recommendations, and verify final code quality.

## What this command does

Initiates an iterative code review and deliberation system where the AI and Codex review actual implementation changes, deliberate over recommendations, implement agreed changes, and verify final code quality.

**Usage:** `/deliberate-code-review-with-codex {TASK_NUMBER} [optional additional prompt]`

- The task number is required (e.g., "ACR-678" or "API-708")
- An optional additional prompt can be provided after the task number to give the AI extra instructions to follow during code review
- Example: `/deliberate-code-review-with-codex ACR-678 Pay special attention to performance implications`

The system works through multiple phases:

1. Setup: Identify changed files via git diff
2. Initial Code Review: AI reviews changed files, creates `codereview.md` with recommendations
3. Deliberation: Codex reviews recommendations, AI and Codex deliberate until consensus
4. Implementation: Implement agreed changes
5. Post-Implementation Review: Review all changes again, deliberate if needed
6. Final Consensus: Both agree no more changes needed

The deliberation conversation is tracked in `deliberation.md` (reused from plan deliberation if exists), code review recommendations in `codereview.md`, and the process continues until consensus is reached or limits are hit (6 total rounds, 3 per side).

## Instructions for the AI

When this command is invoked with a task number:

### CRITICAL REQUIREMENT: CODE UNDERSTANDING

**BEFORE making ANY recommendations or decisions, you and Codex MUST thoroughly understand the code:**

- Read and comprehend ALL changed files identified from git diff
- Understand the existing implementation, architecture, and patterns
- Understand dependencies, relationships, and data flow
- Understand why the code works the way it does
- **NO GUESSES. NO ASSUMPTIONS. NO SHORTCUTS.**
- Every decision must come from a deeply informed point of view
- If you don't understand something, examine it further until you do
- Both you and Codex must operate from complete code comprehension

**"THOROUGH UNDERSTANDING" MEANS PERFORMING ALL MANDATORY FUNCTIONAL CHECKS BELOW. Reading the code is NOT sufficient - you MUST trace flows, verify regression, test edge cases, verify end-to-end, and cover all code paths. Superficial understanding that misses functional bugs is UNACCEPTABLE.**

**STAY FOCUSED ON TASK-RELATED CODE:**

- Only review code that is DIRECTLY related to the task at hand
- Do NOT drift into reviewing general surrounding code or unrelated areas
- Keep code review focused on what needs to be reviewed for THIS task
- If reviewing context code, make it clear why it's relevant to the task
- Avoid scope creep - stay on target

**This is non-negotiable. Lack of thorough understanding leads to mistakes that cannot happen.**

### MANDATORY CODE REVIEW REQUIREMENTS - NON-NEGOTIABLE

**Code review MUST verify functional correctness, not just cosmetic issues. The following checks are MANDATORY and must be performed for EVERY code review:**

1. **FLOW TRACING:**
   - Trace all key variables/data structures from creation through ALL usages
   - Follow filtered data (e.g., `candidateItemIds`, `itemIds`) from creation → filtering → every usage point
   - Verify filtering logic is maintained at EVERY point where filtered data is used
   - Check ALL loops that process filtered data to ensure they respect the filter
   - Identify ALL code paths affected by changes, not just changed lines

2. **REGRESSION VERIFICATION:**
   - Compare before/after behavior for ALL affected code paths
   - Verify existing filtering logic is preserved and not broken
   - Check that changes don't break existing functionality
   - Ensure no data leaks outside filtered sets
   - Verify all conditional branches still work correctly

3. **EDGE CASE VALIDATION:**
   - Test empty sets (empty `candidateItemIds`, empty `stockTakeItemIds`, empty collections after filtering)
   - Test null values and null handling
   - Test boundary conditions (all items excluded by filters, single item scenarios)
   - Test stock list filtering scenarios (all items included, all items excluded, partial filtering)
   - Verify short-circuit logic works correctly for empty sets

4. **END-TO-END VERIFICATION:**
   - Verify the complete flow: data creation → filtering → processing → calculation → response generation
   - Ensure filtering is respected at EVERY step of the flow
   - Check that filtered data doesn't leak into unfiltered processing
   - Verify all transformations maintain filtering constraints

5. **CODE PATH COVERAGE:**
   - Review ALL code paths affected by changes, not just the changed lines
   - Check ALL loops that process filtered data
   - Verify ALL usages of key variables (e.g., `candidateItemIds`, `itemIds`, filtered collections)
   - Ensure ALL methods called with filtered data respect the filter
   - Check ALL branches and conditional logic that uses filtered data

**FAILURE TO PERFORM THESE CHECKS IS NOT ACCEPTABLE. These checks must be documented in codereview.md. Superficial reviews that only check comments, naming, or cosmetic issues are INSUFFICIENT and will result in bugs being missed.**

### SETUP PHASE

- Parse the user's input to extract:
  - Task number: First token/word (e.g., "ACR-678" or "API-708")
  - Additional prompt (optional): Any text after the task number
  - Example: Input "ACR-678 Pay special attention to performance" → Task number: "ACR-678", Additional prompt: "Pay special attention to performance"
  - If no additional text exists after the task number, `ADDITIONAL_PROMPT` is empty/undefined
- Store `ADDITIONAL_PROMPT` for use throughout deliberation (if provided)
- Determine the project root and verify the task folder exists:
  - Search for the task folder `.temp/{TASK_NUMBER}/` in the workspace(s)
  - If the folder does not exist, inform the user: "Task folder `.temp/{TASK_NUMBER}/` not found. Please run `/setup-plan {TASK_NUMBER}` first."
  - Once found, extract the PROJECT ROOT from the task folder path:
    - If task folder is at `/path/to/project/.temp/{TASK_NUMBER}/`, then PROJECT ROOT is `/path/to/project/`
    - The PROJECT ROOT is the parent directory of the `.temp` folder
  - Check if the main task file exists: `.temp/{TASK_NUMBER}/{TASK_NUMBER}-task-details.md` (relative to PROJECT ROOT)
  - Check if the implementation plan file exists: `.temp/{TASK_NUMBER}/{TASK_NUMBER}-implementation-plan.md`
  - If the task file does not exist, inform the user and halt execution
  - If the implementation plan file does not exist, inform the user: "No `{TASK_NUMBER}-implementation-plan.md` file found. Please run `/plan-task {TASK_NUMBER}` first to create an implementation plan."
- **Workspace mode detection:**
  - Run `git rev-parse --is-inside-work-tree` from PROJECT ROOT
  - **If it IS a git repo:** Set `WORKSPACE_MODE` to `false` (single-project mode)
  - **If it is NOT a git repo (command fails/errors):** Scan immediate subdirectories of PROJECT ROOT for git repos (run `git rev-parse --is-inside-work-tree` in each). If any subdirectory is a git repo, set `WORKSPACE_MODE` to `true` (multi-repo workspace). Store the list of git sub-repo directory names as `GIT_REPOS`.
- Get git diff to identify changed files:
  - **If `WORKSPACE_MODE` is `false` (single-project mode):**
    - Determine BASE_BRANCH: Try `master` first, if it doesn't exist try `develop`, if neither exists use current branch
    - From PROJECT ROOT, run: `git diff {BASE_BRANCH} --name-only`
    - Capture the list of changed files
  - **If `WORKSPACE_MODE` is `true` (multi-repo workspace):**
    - For each sub-repo in `GIT_REPOS`:
      - From the sub-repo directory, determine BASE_BRANCH: Try `master` first, if it doesn't exist try `develop`, if neither exists use current branch
      - Run: `git diff {BASE_BRANCH} --name-only` from the sub-repo directory
      - Prefix each changed file path with the sub-repo directory name (e.g., `cloud_backend/SomeFile.cs`)
    - Combine all results into a single list
  - Optionally filter files to only those relevant to the task (can use `{TASK_NUMBER}-implementation-plan.md` to identify relevant paths/patterns)
  - Store list of changed files as `CHANGED_FILES`
  - If no changed files found, inform user: "No changed files found. Ensure implementation has been completed." and STOP

### ADDITIONAL PROMPT HANDLING

- If `ADDITIONAL_PROMPT` was provided during SETUP PHASE:
  - The additional prompt contains extra instructions for the AI to follow during code review and deliberation
  - These instructions supplement (do not replace) the standard command instructions
  - The AI must incorporate these instructions into its behavior throughout all deliberation rounds
  - The additional prompt will be documented in `deliberation.md` so Codex can see it (transparency)
  - If the additional prompt conflicts with standard instructions, standard instructions take precedence (document this in deliberation.md if conflict occurs)
  - The additional prompt persists throughout all deliberation rounds - it is not round-specific
- If `ADDITIONAL_PROMPT` was not provided:
  - Proceed with standard command instructions only
  - No special handling needed

### DELIBERATION INITIALIZATION

- Check if `deliberation.md` exists in `.temp/{TASK_NUMBER}/`
- If it exists, read it to determine current round number:
  - Count occurrences of "## Round" headers to determine how many rounds have been completed
  - Extract the last round number to continue from there
  - Count AI rounds (rounds with "### AI Analysis:" sections)
  - Count Codex rounds (total rounds)
  - Check if `### Additional Instructions:` section exists - if `ADDITIONAL_PROMPT` was provided but not documented, document it now
- If deliberation.md doesn't exist, this is Round 1:
  - Create `deliberation.md` with header: `# Deliberation: {TASK_NUMBER} - Code Review`
  - If `ADDITIONAL_PROMPT` exists, add section immediately after header: `### Additional Instructions:` followed by the full additional prompt text
  - This makes the additional prompt visible to Codex in all subsequent rounds
- Check deliberation limits:
  - If total rounds >= 6, STOP immediately and inform user: "Deliberation limit reached (6 rounds). Cannot continue."
  - If AI rounds >= 3, STOP immediately and inform user: "AI deliberation limit reached (3 rounds). Cannot continue."
- Check if `codereview.md` exists:
  - If it exists, read it to understand current state of code review
  - If it doesn't exist and this is Round 1, initialize it (will be created in INITIAL CODE REVIEW phase)

### INITIAL CODE REVIEW (AI)

- Read all changed files identified from git diff (`CHANGED_FILES`)
- **MANDATORY: Perform ALL checks from MANDATORY CODE REVIEW REQUIREMENTS section above**
- **CRITICAL: This is NOT optional. You MUST:**
  1. Trace all key variables through the entire code flow
  2. Verify filtering logic is maintained at every usage point
  3. Check all loops process filtered data correctly
  4. Test edge cases (empty sets, nulls, boundaries)
  5. Verify end-to-end flow maintains filtering
  6. Review all affected code paths, not just changed lines
- Perform comprehensive code review considering:
  - **FUNCTIONAL CORRECTNESS (MANDATORY):**
    - Flow tracing: Follow all filtered variables through complete code paths
    - Regression verification: Ensure existing functionality isn't broken
    - Edge case validation: Empty sets, nulls, boundary conditions
    - End-to-end verification: Complete flow maintains filtering
    - Code path coverage: All affected paths reviewed
  - Code quality, best practices, patterns
  - Task requirements alignment (reference task.md and `{TASK_NUMBER}-implementation-plan.md`)
  - Potential bugs, edge cases
  - Performance implications
  - Maintainability, readability
  - Any additional prompt requirements
  - Consistency with existing codebase patterns
- **Document in codereview.md that you have performed ALL mandatory checks:**
  - List which variables you traced and through which code paths
  - Document edge cases you verified
  - Note any code paths you reviewed beyond changed lines
  - If you find issues, they MUST be documented as recommendations
- Create or update `codereview.md` with:
  - Header: `# Code Review: {TASK_NUMBER}`
  - Section: `## Changed Files`
    - List all files being reviewed with their full paths (relative to PROJECT ROOT)
  - Section: `## Code Review Recommendations`
    - Numbered list of recommendations
    - Each recommendation includes:
      - **File**: File path and line numbers (if applicable)
      - **Issue**: Description of the issue found
      - **Recommendation**: Specific recommended change
      - **Rationale**: Justification for the recommendation
      - **Status**: Initially `[PENDING]` (will be updated during deliberation)
- Document in `deliberation.md` Round N:
  - Add `## Round {N} - {Current Timestamp}` if not already present
  - Add `### AI Request:` section
  - Document: "I have completed initial code review of the changed files. Please review my recommendations in codereview.md. For each recommendation, indicate whether you AGREE, DISAGREE (with reasoning), or propose a MODIFICATION."
  - If `ADDITIONAL_PROMPT` exists: Reference that additional instructions are being followed
  - Ensure the AI incorporates the additional prompt when performing code review

### ROUND N: CODEX CONSULTATION

- Update or create `deliberation.md` with new round header if needed:
  - Add `## Round {N} - {Current Timestamp}` if starting new round
  - Add `### AI Request:` section if not already present
  - If Round > 1: Reference previous round, explain your response to Codex's recommendations, and ask for Codex's thoughts on your reasoning
- Construct the Codex prompt:
  - "Read the following files:"
  - "- `.temp/{TASK_NUMBER}/{TASK_NUMBER}-task-details.md` (the original Jira task)"
  - "- `.temp/{TASK_NUMBER}/{TASK_NUMBER}-implementation-plan.md` (the implementation plan)"
  - "- `.temp/{TASK_NUMBER}/codereview.md` (the code review recommendations)"
  - "- `.temp/{TASK_NUMBER}/deliberation.md` (our deliberation history)"
  - "- [List all changed files from CHANGED_FILES with their paths]"
  - ""
  - "**CRITICAL: You must thoroughly understand the code before making recommendations:**"
  - "- Examine ALL changed files mentioned in codereview.md"
  - "- Read and comprehend the implementation completely"
  - "- Understand the context, patterns, and dependencies"
  - "- NO GUESSES. NO ASSUMPTIONS. Every recommendation must be based on complete code understanding."
  - "- If you need to examine additional files to understand the code, do so"
  - ""
  - "**MANDATORY FUNCTIONAL CODE REVIEW REQUIREMENTS - YOU MUST PERFORM THESE CHECKS:**"
  - "- **FLOW TRACING:** Trace all key variables (e.g., filtered collections like candidateItemIds) from creation through ALL usages. Verify filtering logic is maintained at EVERY usage point. Check ALL loops that process filtered data."
  - "- **REGRESSION VERIFICATION:** Compare before/after behavior for ALL affected code paths. Verify existing filtering logic is preserved. Check that changes don't break existing functionality."
  - "- **EDGE CASE VALIDATION:** Test empty sets (empty filtered collections), null values, boundary conditions (all items excluded, single item scenarios). Verify short-circuit logic works correctly."
  - "- **END-TO-END VERIFICATION:** Verify complete flow from data creation → filtering → processing → response. Ensure filtering is respected at EVERY step."
  - "- **CODE PATH COVERAGE:** Review ALL code paths affected by changes, not just changed lines. Check ALL loops processing filtered data. Verify ALL usages of key variables."
  - "- **DO NOT** focus only on cosmetic issues (comments, naming, date operators). Functional correctness is MANDATORY."
  - ""
  - "**STAY FOCUSED ON TASK-RELATED CODE:**"
  - "- Only discuss code DIRECTLY related to this task"
  - "- Do NOT drift into general surrounding code or unrelated areas"
  - "- Keep recommendations focused on what needs to be reviewed for THIS task"
  - ""
  - "Review the code review recommendations in codereview.md."
  - "**CRITICAL:** Verify that the AI has performed ALL mandatory functional checks. If the review only addresses cosmetic issues, you MUST identify missing functional checks and add them as recommendations."
  - "For each recommendation, indicate:"
  - "- **AGREE**: The recommendation is valid and should be implemented (provide brief confirmation)"
  - "- **DISAGREE**: The recommendation has issues (provide reasoning with code evidence)"
  - "- **MODIFY**: You agree with the concern but propose a different solution (describe the alternative)"
  - "- If you have additional recommendations not in codereview.md, list them with the same format"
  - "- If you agree with all recommendations and have no additional concerns, state that clearly"
  - "Structure your response in markdown format with clear sections."
- Invoke Codex:
  - Change directory to PROJECT ROOT
  - Run: `cd {PROJECT_ROOT}; codex exec --skip-git-repo-check "<prompt>" -o .temp/{TASK_NUMBER}/codex-analysis.tmp`
  - The `-o` flag writes clean response to temporary file
  - Read the response from `{PROJECT_ROOT}/.temp/{TASK_NUMBER}/codex-analysis.tmp`
  - If Codex fails, inform user: "Codex analysis failed. Error: {error message}" and STOP
- Append Codex response to deliberation.md:
  - Add `### Codex Response:` section
  - Include the full Codex response

### ANALYSIS: EVALUATE CODEX RESPONSE

- **BEFORE evaluating Codex's response, verify YOUR OWN code understanding:**
  - Have you thoroughly examined all changed files?
  - Do you completely understand the implementation?
  - Are you operating from complete code comprehension, not assumptions?
  - If not, examine the code further before proceeding
- **VERIFY FOCUS ON TASK-RELATED CODE:**
  - Is Codex discussing code directly related to the task?
  - If Codex has drifted to surrounding/unrelated code, note that in your analysis
  - Keep your own analysis focused on task-related code only
- **CONSIDER ADDITIONAL PROMPT (if provided):**
  - If `ADDITIONAL_PROMPT` exists, consider its instructions alongside standard verification checklist
  - Apply any specific focus areas or requirements from the additional prompt when evaluating Codex's response
  - Ensure the additional prompt requirements are addressed in your evaluation and decisions
- Parse Codex response for each recommendation:
  - **AGREE**: Codex agrees with the recommendation
  - **DISAGREE**: Codex disagrees (with reasoning)
  - **MODIFY**: Codex proposes modification
  - Additional recommendations: Codex found new issues
- **Consensus Logic:**
  - If Codex agrees with recommendation → Mark as `[AGREED]`, ready for implementation
  - If Codex disagrees and you agree with Codex's reasoning → Remove recommendation from codereview.md or mark as `[REJECTED]`, document in deliberation
  - If Codex disagrees but you insist → Document your reasoning, mark as `[IN DELIBERATION]`, continue deliberation
  - If Codex proposes modification → Evaluate alternative, if you agree update recommendation in codereview.md, if not mark as `[IN DELIBERATION]` and continue deliberation
  - If Codex provides additional recommendations → Add them to codereview.md with status `[PENDING]`
- Update `codereview.md` to reflect current state:
  - Mark agreed recommendations as `[AGREED]`
  - Keep disagreed recommendations as `[IN DELIBERATION]` or `[REJECTED]` based on consensus
  - Add new recommendations from Codex with status `[PENDING]`
  - Update modified recommendations with new text

### UPDATE: DOCUMENT AI RESPONSE

- Add `### AI Analysis:` section to deliberation.md
- Document your evaluation:
  - List each recommendation from codereview.md
  - For agreements: Explain why you agree and what will change
  - For disagreements: Explain your reasoning - do you agree with Codex's disagreement or do you insist?
  - For modifications: Explain whether you accept the modification or continue deliberation
  - For new recommendations from Codex: Explain whether you accept them
  - **If `ADDITIONAL_PROMPT` exists and influenced your evaluation or decisions**: Note this explicitly in the analysis (e.g., "Note: The additional instruction to [X] influenced my evaluation of this recommendation because [Y].")
- Update `codereview.md` with status changes based on consensus
- Add section separator in deliberation.md: `\n---\n\n`

### ITERATION: NEXT ROUND CHECK

- Increment round counters:
  - Total rounds = Total rounds + 1
  - AI rounds = AI rounds + 1 (you just responded)
- Check limits:
  - If AI rounds >= 3:
    - Add final note to deliberation.md: "AI deliberation limit reached (3 rounds)."
    - Summarize points of agreement and disagreement
    - List agreed vs disagreed recommendations in codereview.md
    - Proceed to IMPLEMENTATION PHASE with agreed recommendations only
    - Inform user: "Deliberation limit reached. Some recommendations remain unresolved: [list]"
    - STOP after implementation
  - If total rounds >= 6:
    - Add final note to deliberation.md: "Total deliberation limit reached (6 rounds)."
    - Summarize points of agreement and disagreement
    - List agreed vs disagreed recommendations in codereview.md
    - Proceed to IMPLEMENTATION PHASE with agreed recommendations only
    - Inform user: "Deliberation limit reached. Some recommendations remain unresolved: [list]"
    - STOP after implementation
- Check if there are recommendations still in deliberation:
  - If there are `[IN DELIBERATION]` recommendations → Continue deliberation (go back to ROUND N+1)
  - If all recommendations are `[AGREED]` or `[REJECTED]` → Proceed to IMPLEMENTATION PHASE

### IMPLEMENTATION PHASE

- **Only proceed if there are AGREED recommendations:**
  - If all recommendations are still `[IN DELIBERATION]` or `[PENDING]` → Continue deliberation, skip implementation
  - If some recommendations are `[AGREED]` → Implement agreed ones, continue deliberating on rest after implementation
- For each `[AGREED]` recommendation:
  - Read the relevant file(s) mentioned in the recommendation
  - Implement the change as specified in the recommendation
  - Verify the change is correct and doesn't introduce new issues
  - Test the change mentally/logically to ensure it works
- After implementing all agreed recommendations:
  - Update `codereview.md` to mark implemented recommendations as `[IMPLEMENTED]`
  - Document in `deliberation.md`: "Implemented agreed recommendations: [list recommendation numbers]"
  - Get fresh git diff to see new changes:
    - **If `WORKSPACE_MODE` is `false`:** Run `git diff {BASE_BRANCH} --name-only` from PROJECT ROOT
    - **If `WORKSPACE_MODE` is `true`:** For each sub-repo in `GIT_REPOS`, run `git diff {BASE_BRANCH} --name-only` from the sub-repo directory and prefix paths with the sub-repo name
    - Update `CHANGED_FILES` list to include newly changed files
  - Proceed to POST-IMPLEMENTATION REVIEW

### POST-IMPLEMENTATION REVIEW

- Review ALL changed files again (original + newly changed from implementation):
  - Read all files in `CHANGED_FILES` (updated list)
  - Perform fresh code review as if starting from scratch
- Check for:
  - New issues introduced by implemented changes
  - Whether all changes work together correctly
  - Any remaining issues in the original changes
  - Edge cases that may have been missed
- Update `codereview.md`:
  - Add new recommendations if any found (status `[PENDING]`)
  - Mark previous `[IMPLEMENTED]` recommendations as `[REVIEWED]` if they look good
  - If implemented changes introduced issues, add recommendations for those
- If new recommendations found:
  - Document in `deliberation.md`: "Post-implementation review found new recommendations: [list]"
  - Continue deliberation (go back to ROUND N+1: CODEX CONSULTATION)
- If no new recommendations found:
  - Document in `deliberation.md`: "Post-implementation review completed. No new issues found."
  - Proceed to FINAL CONSENSUS CHECK

### FINAL CONSENSUS CHECK

- Both AI and Codex must agree:
  - All recommendations have been addressed (implemented as `[IMPLEMENTED]` and `[REVIEWED]`, or removed/rejected by consensus)
  - No new issues found in post-implementation review
  - Code is ready and meets quality standards
- To verify consensus:
  - Check codereview.md: All recommendations should be `[IMPLEMENTED]` and `[REVIEWED]`, `[REJECTED]`, or removed
  - If there are any `[PENDING]` or `[IN DELIBERATION]` recommendations → Continue deliberation
  - Ask Codex one final time: "Please confirm that all code review recommendations have been addressed and you have no additional concerns."
- If consensus reached:
  - Document in deliberation.md: "Final consensus reached. Code review complete. All recommendations addressed."
  - Display summary (see DISPLAY SUMMARY section)
  - STOP - Code review complete
- If not reached → Continue deliberation (go back to ROUND N+1: CODEX CONSULTATION)

### DISPLAY SUMMARY

When code review completes (consensus or limit), display:

- **Task:** {TASK_NUMBER} - {Task Title}
- **Outcome:** Code Review Complete / Limit Reached (X rounds)
- **Rounds Completed:** {AI rounds} AI rounds, {Total rounds} total rounds
- **Files Reviewed:** [List of changed files]
- **Recommendations:**
  - Implemented: [Count]
  - Rejected: [Count]
  - Unresolved (if limit reached): [Count and list]
- **Files:**
  - Code Review: `.temp/{TASK_NUMBER}/codereview.md`
  - Deliberation: `.temp/{TASK_NUMBER}/deliberation.md`
- Do NOT display raw Codex responses
- When consensus is reached, finish with a success line that points to the final hand-off, e.g. `✅ Code review complete. Next step: merge & release changes (Codex Jira workflow complete)`

### ERROR HANDLING

- If task number not provided: Ask the user for it
- If task folder not found: Inform user: "Task folder `.temp/{TASK_NUMBER}/` not found. Please run `/setup-plan {TASK_NUMBER}` first." and STOP
- If `{TASK_NUMBER}-implementation-plan.md` doesn't exist: Inform user: "No `{TASK_NUMBER}-implementation-plan.md` file found. Please run `/plan-task {TASK_NUMBER}` first to create an implementation plan." and STOP
- If no changed files found: Inform user: "No changed files found. Ensure implementation has been completed." and STOP
- If deliberation.md exists but is malformed: Try to parse best-effort, default to Round 1 if parsing fails
- If Codex returns empty response: Treat as error, inform user: "Codex analysis failed. Error: {error message}" and STOP
- If unable to write to deliberation.md or codereview.md: Inform user: "Unable to write to {filename}. Check file permissions." and STOP
- If round counting fails: Default to safe limits (assume at limit) and STOP with message: "Unable to parse deliberation rounds. Assuming limit reached."
- If git diff fails: Inform user: "Unable to determine changed files. Check git repository status." and STOP

## Codex Command Syntax

The command uses `codex exec` from the dynamically determined PROJECT root:

```powershell
cd {PROJECT_ROOT}; codex exec --skip-git-repo-check "Your prompt here" -o .temp/{TASK_NUMBER}/codex-analysis.tmp
```

For multi-line prompts in PowerShell, use backtick-n for newlines:

```powershell
# Example: If task folder found at C:\Source\cloud_backend\.temp\ACR-678
# Then PROJECT_ROOT = C:\Source\cloud_backend
cd C:\Source\cloud_backend; codex exec --skip-git-repo-check "Read the following files:`n- .temp/ACR-678/ACR-678-task-details.md`n- .temp/ACR-678/ACR-678-implementation-plan.md`n- .temp/ACR-678/codereview.md`n- .temp/ACR-678/deliberation.md`nReview the code review recommendations..." -o .temp/ACR-678/codex-analysis.tmp
```

Key points:

- **CRITICAL:** Dynamically determine the PROJECT root by finding the parent directory of `.temp`
- When you find `.temp/{TASK_NUMBER}/`, extract the PROJECT root as the parent of `.temp`
- Example: If task folder is `/path/to/project/.temp/ACR-678/`, then PROJECT root is `/path/to/project/`
- Run Codex from the PROJECT root directory, NOT from arbitrary workspace locations
- Use relative paths from project root in the prompt (e.g., `.temp/ACR-678/ACR-678-task-details.md`, `.temp/ACR-678/codereview.md`)
- Output goes to temporary file: `.temp/{TASK_NUMBER}/codex-analysis.tmp` (overwritten each round)
- The `-o` flag writes only the agent's response (without metadata) to the specified file
- Do NOT use the `-C` flag as it causes issues with the `-o` output path
- Always include all required files in the prompt: task-details.md file, plan file, codereview.md, deliberation.md, and changed files

## Codereview.md Format Specification

The `codereview.md` file tracks code review recommendations using this structure:

```markdown
# Code Review: {TASK_NUMBER}

## Changed Files

- `path/to/file1.cs`
- `path/to/file2.cs`
- `path/to/file3.cs`

## Code Review Recommendations

### 1. [PENDING] / [AGREED] / [IN DELIBERATION] / [REJECTED] / [IMPLEMENTED] / [REVIEWED]

**File:** `path/to/file1.cs` (lines 42-45)

**Issue:** Description of the issue found

**Recommendation:** Specific recommended change

**Rationale:** Justification for the recommendation

---

### 2. [PENDING] / [AGREED] / [IN DELIBERATION] / [REJECTED] / [IMPLEMENTED] / [REVIEWED]

**File:** `path/to/file2.cs` (line 78)

**Issue:** Another issue description

**Recommendation:** Another recommended change

**Rationale:** Another justification

---
```

**Status Values:**

- `[PENDING]` - Initial state, awaiting Codex review
- `[AGREED]` - Both AI and Codex agree, ready for implementation
- `[IN DELIBERATION]` - Disagreement exists, under discussion
- `[REJECTED]` - Consensus reached to not implement
- `[IMPLEMENTED]` - Change has been implemented
- `[REVIEWED]` - Implemented change has been reviewed and confirmed good

**Key Points:**

- Each recommendation is clearly numbered
- File paths and line numbers are specified when applicable
- Status is clearly marked and updated as deliberation progresses
- Recommendations are separated by horizontal rules for clarity

## Deliberation.md Format Specification

The `deliberation.md` file tracks the full conversation between AI and Codex using this structure (same as 03 command, but for code review):

```markdown
# Deliberation: {TASK_NUMBER} - Code Review

### Additional Instructions:
[Optional section - only present if additional prompt was provided]
[Full text of the additional prompt instructions for the AI]

## Round 1 - {Timestamp}

### AI Request:
[What the AI is asking Codex to review/consider in this round]

### Codex Response:
[Full response from Codex - agreements, disagreements, modifications, etc.]

### AI Analysis:
[AI's evaluation of Codex's response]

**Agreements:**
- [List of recommendations where AI agrees with Codex]

**Disagreements:**
- [List of recommendations where AI disagrees with Codex and reasoning]

**Modifications:**
- [Any modified recommendations or alternative approaches]

---

## Round 2 - {Timestamp}

[Additional rounds as needed, up to 6 total]

## Final Outcome

[Added when deliberation completes]
- **Result:** Consensus Reached / Limit Reached
- **Total Rounds:** X
- **Status:** [Summary of final state]
```

**Key Points:**

- Same structure as plan deliberation, but focused on code review
- Full context preserved for Codex to read in subsequent rounds
- Final outcome documented when code review completes

## Notes

### System Design

- This is an **iterative code review and deliberation system**, not a single-shot review
- AI and Codex are **equal partners** - neither is "king", both contribute thinking
- AI must **genuinely disagree** with Codex when appropriate - this is not rubber-stamping
- Consensus requires BOTH parties agreeing on recommendations
- Code review is only complete when there is **NOTHING LEFT TO REVIEW** - all recommendations addressed, no new issues found
- Implementation happens incrementally - agreed changes are implemented, then code is reviewed again

### Code Understanding Requirement - NON-NEGOTIABLE

- **THOROUGH code understanding is mandatory** - no shortcuts, no guesses, no assumptions
- Both AI and Codex must **deeply comprehend** the code before making recommendations
- **Read and understand ALL changed files** completely
- Understand existing implementation, architecture, patterns, dependencies, data flow
- **Every recommendation must come from a completely informed position**
- If you don't understand something, examine it further until you do
- **Lack of thorough understanding leads to mistakes that cannot happen**
- This requirement applies to EVERY round, EVERY recommendation, EVERY decision

### Focus Requirement - STAY ON TARGET

- **Only review code DIRECTLY related to the task at hand**
- Do NOT drift into reviewing general surrounding code or unrelated areas
- Keep code review focused on what needs to be reviewed for THIS SPECIFIC task
- If reviewing context code, explicitly state why it's relevant to the task
- Avoid scope creep - stay laser-focused on the task requirements
- If either party drifts off target, the other must bring focus back to task-related code

### File Management

- `codereview.md` - Code review recommendations, status tracking
- `deliberation.md` - Full conversation history (reused from plan deliberation if exists)
- `codex-analysis.tmp` - Temporary file for Codex output, overwritten each round
- Changed files - Actual implementation files being reviewed (identified via git diff)
- PROJECT root is dynamically determined by finding parent of `.temp` folder
- All files use relative paths from PROJECT root

### Deliberation Process

- Maximum 3 rounds per side (6 total rounds)
- Codex reads all required files (task, plan, codereview, deliberation, changed files) for full context each round
- AI evaluates Codex responses and responds with agreements/disagreements
- Process continues until consensus reached or limits hit
- Implementation happens incrementally as recommendations are agreed upon
- Post-implementation review ensures no new issues introduced

### Implementation Strategy

- Implement agreed recommendations immediately (don't wait for all recommendations to be agreed)
- After implementation, perform fresh code review of all changes
- Continue deliberation on any remaining disagreements
- Repeat until all recommendations are addressed and no new issues found

### Context Strategy

- Codex gets full conversation history via deliberation.md (mimics manual workflow)
- AI doesn't bloat its own context by re-reading files unnecessarily
- Codex can handle large context - deliberation.md can grow
- Temporary output file prevents accumulation of old responses
- Changed files are explicitly listed in prompts so Codex can read them

### Multiple Concurrent Agents

- All task-specific files live in `.temp/{TASK_NUMBER}/` folder
- Different tasks can run code reviews simultaneously without conflict
- Each task has its own codereview.md, deliberation.md, and codex-analysis.tmp
- Git diff is task-agnostic but filtered to task-relevant files when possible
