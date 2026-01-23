# Jira Task Codex Analysis Command

Analyze a Jira task using Codex AI and update the implementation plan based on the analysis.

## What this command does

Initiates an iterative deliberation system where the AI and Codex exchange perspectives on the implementation plan until both reach agreement or hit the 3-attempt limit per side (maximum 6 rounds total).

**Usage:** `/cosoft-jira-03-deliberate-plan-codex {TASK_NUMBER} [optional additional prompt]`

- The task number is required (e.g., "ACR-678" or "API-708")
- An optional additional prompt can be provided after the task number to give the AI extra instructions to follow during deliberation
- Example: `/cosoft-jira-03-deliberate-plan-codex ACR-678 Pay special attention to performance implications`

The system works through multiple rounds:

1. AI asks Codex to review the implementation plan and all task files
2. Codex provides analysis with recommendations or indicates agreement
3. AI evaluates Codex's response - agreeing, disagreeing, or proposing alternatives (incorporating any additional prompt instructions)
4. The conversation continues through `deliberation.md` until:
   - Agreement is reached (Codex has no recommendations and comprehensive verification passes) - Plan is finalized
   - 3 rounds per side completed (6 total) - Deliberation stops, disagreements documented

Agreement requires both Codex having no actionable recommendations AND passing comprehensive verification. The deliberation conversation is tracked in `deliberation.md`, and once complete, the agreed-upon plan is saved to `{TASK_NUMBER}-implementation-plan.md` (the file at `.temp/{TASK_NUMBER}/{TASK_NUMBER}-implementation-plan.md`) with deliberation history appended at the end.

## Instructions for the AI

When this command is invoked with a task number:

### CRITICAL REQUIREMENT: CODE UNDERSTANDING

**BEFORE making ANY recommendations or decisions, you and Codex MUST thoroughly understand the code:**

- Read and comprehend ALL relevant source files in the area affected by the task
- Understand the existing implementation, architecture, and patterns
- Understand dependencies, relationships, and data flow
- Understand why the code works the way it does
- **NO GUESSES. NO ASSUMPTIONS. NO SHORTCUTS.**
- Every decision must come from a deeply informed point of view
- If you don't understand something, examine it further until you do
- Both you and Codex must operate from complete code comprehension

**STAY FOCUSED ON TASK-RELATED CODE:**

- Only discuss code that is DIRECTLY related to the task at hand
- Do NOT drift into discussing general surrounding code or unrelated areas
- Keep deliberation focused on what needs to change or be understood for THIS task
- If discussing context code, make it clear why it's relevant to the task
- Avoid scope creep - stay on target

**This is non-negotiable. Lack of thorough understanding leads to mistakes that cannot happen.**

### SETUP PHASE

- Parse the user's input to extract:
  - Task number: First token/word (e.g., "ACR-678" or "API-708")
  - Additional prompt (optional): Any text after the task number
  - Example: Input "ACR-678 Pay special attention to performance" → Task number: "ACR-678", Additional prompt: "Pay special attention to performance"
  - If no additional text exists after the task number, `ADDITIONAL_PROMPT` is empty/undefined
- Store `ADDITIONAL_PROMPT` for use throughout deliberation (if provided)
- Determine the project root and verify the task folder exists:
  - Search for the task folder `.temp/{TASK_NUMBER}/` in the workspace(s)
  - If the folder does not exist, inform the user: "Task folder `.temp/{TASK_NUMBER}/` not found. Please run `/cosoft-jira-01-setup {TASK_NUMBER}` first."
  - Once found, extract the PROJECT ROOT from the task folder path:
    - If task folder is at `/path/to/project/.temp/{TASK_NUMBER}/`, then PROJECT ROOT is `/path/to/project/`
    - The PROJECT ROOT is the parent directory of the `.temp` folder
  - Check if the main task file exists: `.temp/{TASK_NUMBER}/{TASK_NUMBER}-task-details.md` (relative to PROJECT ROOT)
  - Check if the implementation plan file exists: `.temp/{TASK_NUMBER}/{TASK_NUMBER}-implementation-plan.md`
  - If the task file does not exist, inform the user and halt execution
  - If the implementation plan file does not exist, inform the user: "No `{TASK_NUMBER}-implementation-plan.md` file found. Please run `/cosoft-jira-02-plan {TASK_NUMBER}` first to create an implementation plan."

### ADDITIONAL PROMPT HANDLING

- If `ADDITIONAL_PROMPT` was provided during SETUP PHASE:
  - The additional prompt contains extra instructions for the AI to follow during deliberation
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
  - Create `deliberation.md` with header: `# Deliberation: {TASK_NUMBER}`
  - If `ADDITIONAL_PROMPT` exists, add section immediately after header: `### Additional Instructions:` followed by the full additional prompt text
  - This makes the additional prompt visible to Codex in all subsequent rounds
- Check deliberation limits:
  - If total rounds >= 6, STOP immediately and inform user: "Deliberation limit reached (6 rounds). Cannot continue."
  - If AI rounds >= 3, STOP immediately and inform user: "AI deliberation limit reached (3 rounds). Cannot continue."

### ROUND N: CODEX CONSULTATION

- Update or create `deliberation.md` with new round header:
  - Add `## Round {N} - {Current Timestamp}`
  - Add `### AI Request:` section
  - Document what you're asking Codex to review in this round
  - If Round 1: "Please review the implementation plan and all task files. Focus on the plan - do you agree with the approach? Provide recommendations with specific reasoning if you have concerns."
  - If Round > 1: Reference previous round, explain your response to Codex's recommendations, and ask for Codex's thoughts on your reasoning
  - If `ADDITIONAL_PROMPT` exists: Reference that additional instructions are being followed (e.g., "Note: I am also following additional instructions provided at the start of deliberation - see 'Additional Instructions' section above.")
  - Ensure the AI incorporates the additional prompt when formulating requests to Codex (apply any specific focus areas or requirements from the additional prompt)
- Construct the Codex prompt:
  - "Read the following files:"
  - "- `.temp/{TASK_NUMBER}/{TASK_NUMBER}-task-details.md` (the original Jira task)"
  - "- `.temp/{TASK_NUMBER}/{TASK_NUMBER}-implementation-plan.md` (the current implementation plan)"
  - "- `.temp/{TASK_NUMBER}/deliberation.md` (our conversation history)"
  - ""
  - "**CRITICAL: You must thoroughly understand the code before making recommendations:**"
  - "- Examine ALL relevant source files mentioned in the plan"
  - "- Read and comprehend the existing implementation completely"
  - "- Understand the architecture, patterns, dependencies, and data flow"
  - "- NO GUESSES. NO ASSUMPTIONS. Every recommendation must be based on complete code understanding."
  - "- If you need to examine additional files to understand the code, do so"
  - ""
  - "**STAY FOCUSED ON TASK-RELATED CODE:**"
  - "- Only discuss code DIRECTLY related to this task"
  - "- Do NOT drift into general surrounding code or unrelated areas"
  - "- Keep recommendations focused on what needs to change for THIS task"
  - ""
  - "Focus on the implementation plan. Review our deliberation history to understand the context."
  - "Provide your analysis:"
  - "- If you agree with the current plan and have no recommendations, state that clearly"
  - "- If you have recommendations or concerns, provide them with specific reasoning based on your code examination"
  - "- Address any points from my previous response (if this is not Round 1)"
  - "Structure your response in markdown format with clear sections."
- Invoke Codex:
  - Change directory to PROJECT ROOT
  - Run: `cd {PROJECT_ROOT}; codex exec "<prompt>" -o .temp/{TASK_NUMBER}/codex-analysis.tmp`
  - The `-o` flag writes clean response to temporary file
  - Read the response from `{PROJECT_ROOT}/.temp/{TASK_NUMBER}/codex-analysis.tmp`
  - If Codex fails, inform user: "Codex analysis failed. Error: {error message}" and STOP
- Append Codex response to deliberation.md:
  - Add `### Codex Response:` section
  - Include the full Codex response

### ANALYSIS: EVALUATE CODEX RESPONSE

- **BEFORE evaluating Codex's response, verify YOUR OWN code understanding:**
  - Have you thoroughly examined all relevant source files?
  - Do you completely understand the existing implementation?
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
- Parse Codex response for recommendations vs agreement:
  - Look for specific recommendations, concerns, suggestions, issues, or disagreements
  - Look for indicators of agreement: phrases like "agree", "looks good", "no concerns", "no recommendations"
  - **Key**: If Codex provides no actionable recommendations or concerns, infer potential agreement (but DO NOT declare completion yet)
- If NO recommendations found (potential agreement):
  - **CRITICAL: BEFORE declaring deliberation complete, perform comprehensive verification:**
  - **MANDATORY VERIFICATION CHECKLIST - All must pass:**
    1. **Code Understanding Verification:**
       - Have you AND Codex thoroughly examined ALL relevant source files mentioned in the plan?
       - Have you verified the actual implementation matches what the plan assumes?
       - Are there any code sections referenced in the plan that haven't been examined?
       - If any answer is "no" or "unsure", examine those files NOW before proceeding
    2. **Plan Completeness Verification:**
      - Read through the ENTIRE `{TASK_NUMBER}-implementation-plan.md` file line by line
       - For each step in the plan, verify: Is it clear what needs to be done? Are all edge cases covered?
       - Check for logical inconsistencies: Do different steps reference the same variables/entities consistently?
       - Verify all data flows: Are inputs/outputs clearly defined? Are transformations unambiguous?
       - Check for missing steps: Are there gaps between steps where something is assumed but not stated?
    3. **Variable/Entity Consistency Check:**
       - Identify all variables, entities, collections, and data structures referenced in the plan
       - Verify each is defined before use
       - Check for naming inconsistencies (e.g., `candidateItemIds` vs `stockTakeItemIds`)
       - Verify filtering/transformation steps are applied consistently (e.g., if Step 5 filters `candidateItemIds`, verify Step 6 uses the filtered version, not the original)
    4. **Edge Cases and Conditions Verification:**
       - Identify all conditional branches in the plan (if/then, when/otherwise)
       - Verify each branch is fully specified with clear actions
       - Check for missing conditions: Are there scenarios not covered?
       - Verify conditional logic is consistent across steps
    5. **Implementation Clarity Check:**
       - Can each step be implemented without further clarification?
       - Are there any ambiguous instructions that could be interpreted multiple ways?
       - Are all file paths, method names, and code locations clearly specified?
       - Are there any "TODO" or "TBD" items that need resolution?
    6. **Integration and Flow Verification:**
       - Verify step transitions: Does Step N's output properly feed into Step N+1?
       - Check for circular dependencies or missing dependencies
       - Verify all referenced code locations exist and are correct
       - Ensure the plan addresses the complete task scope, not just parts of it
  - **If ANY item in the checklist reveals issues, gaps, or ambiguities:**
    - Add `### AI Analysis:` section to deliberation.md
    - Document: "Codex has no recommendations, but verification reveals the following issues that must be addressed:"
    - List each issue found during verification with specific details
    - Update the Codex prompt to ask Codex to review these specific issues
    - Continue to next round - DO NOT declare completion
  - **If ALL checklist items pass AND Codex has no recommendations:**
    - Add `### AI Analysis:` section to deliberation.md
    - Document: "Codex has no recommendations. Comprehensive verification completed - all checks passed. Agreement reached."
    - Update `{TASK_NUMBER}-implementation-plan.md`:
      - Keep the existing plan intact
      - Append delimiter: `\n\n---\n\n## Deliberation History\n\n`
      - Append the full contents of deliberation.md
    - Display success summary (see DISPLAY SUMMARY section)
    - STOP - Deliberation complete
- If recommendations found:
  - **CRITICAL**: Analyze each recommendation based on THOROUGH code understanding:
    - Re-examine the relevant code if needed to verify Codex's recommendation
    - Ensure you fully understand WHY Codex is suggesting this change
    - Verify the recommendation against the actual implementation, not assumptions
    - Consider the existing plan with complete code context
    - Consider best practices and potential issues with full code knowledge
    - **If `ADDITIONAL_PROMPT` exists**: Consider how the additional prompt requirements relate to each recommendation
  - For each recommendation, determine (from informed position):
    - **AGREE**: The recommendation is valid based on your code examination and should be incorporated
    - **DISAGREE**: The recommendation has issues or doesn't apply based on your code understanding (provide reasoning with code evidence)
    - **ALTERNATIVE**: Propose a different approach that addresses the concern (based on your code knowledge)

### UPDATE: DOCUMENT AI RESPONSE

- Add `### AI Analysis:` section to deliberation.md
- Document your evaluation:
  - List each recommendation from Codex
  - For agreements: Explain why you agree and what will change
  - For disagreements: Explain your reasoning and why you disagree
  - For alternatives: Explain your counter-proposal
  - **If `ADDITIONAL_PROMPT` exists and influenced your evaluation or decisions**: Note this explicitly in the analysis (e.g., "Note: The additional instruction to [X] influenced my evaluation of this recommendation because [Y].")
- Update `{TASK_NUMBER}-implementation-plan.md` with any agreed changes:
  - Make the actual changes to the plan
  - Keep the plan clean (don't add deliberation notes to plan yet)
  - Ensure any additional prompt requirements are addressed in plan updates
  - Save the updated plan
- Add section separator in deliberation.md: `\n---\n\n`

### ITERATION: NEXT ROUND CHECK

- Increment round counters:
  - Total rounds = Total rounds + 1
  - AI rounds = AI rounds + 1 (you just responded)
- Check limits:
  - If AI rounds >= 3:
    - Add final note to deliberation.md: "AI deliberation limit reached (3 rounds)."
    - Summarize points of agreement and disagreement
    - Update `{TASK_NUMBER}-implementation-plan.md` with agreed portions only
    - Note unresolved items in plan under "## Unresolved Deliberation Items"
    - Append deliberation history to plan
    - Display summary indicating limit reached
    - STOP
  - If total rounds >= 6:
    - Add final note to deliberation.md: "Total deliberation limit reached (6 rounds)."
    - Summarize points of agreement and disagreement
    - Update `{TASK_NUMBER}-implementation-plan.md` with agreed portions only
    - Note unresolved items in plan under "## Unresolved Deliberation Items"
    - Append deliberation history to plan
    - Display summary indicating limit reached
    - STOP
- If limits not reached and disagreements remain:
  - Inform user: "Round {N} complete. Continuing deliberation..."
  - Go back to ROUND N+1 (repeat from "ROUND N: CODEX CONSULTATION")

### DISPLAY SUMMARY

When deliberation completes (agreement or limit), display:

- **Task:** {TASK_NUMBER} - {Task Title}
- **Outcome:** Agreement Reached / Limit Reached (X rounds)
- **Rounds Completed:** {AI rounds} AI rounds, {Total rounds} total rounds
- **Key Changes Agreed:** [List major changes incorporated]
- **Unresolved Items:** [List if limit reached with disagreements]
- **Files:**
  - Task Details: `.temp/{TASK_NUMBER}/{TASK_NUMBER}-task-details.md`
  - Implementation Plan: `.temp/{TASK_NUMBER}/{TASK_NUMBER}-implementation-plan.md`
  - Deliberation: `.temp/{TASK_NUMBER}/deliberation.md`
- Do NOT display raw Codex responses
- When agreement is reached, end with a clear success line so the team knows what to run next, e.g. `✅ Plan deliberation complete. Next step: /cosoft-jira-04-implement {TASK_NUMBER}`

### ERROR HANDLING

- If task number not provided: Ask the user for it
- If deliberation.md exists but is malformed: Try to parse best-effort, default to Round 1 if parsing fails
- If Codex returns empty response: Treat as error, inform user
- If unable to write to deliberation.md or `{TASK_NUMBER}-implementation-plan.md`: Inform user of file system error and STOP
- If round counting fails: Default to safe limits (assume at limit) and STOP

## Codex Command Syntax

The command uses `codex exec` from the dynamically determined PROJECT root:

```powershell
cd {PROJECT_ROOT}; codex exec "Your prompt here" -o .temp/{TASK_NUMBER}/codex-analysis.tmp
```

For multi-line prompts in PowerShell, use backtick-n for newlines:

```powershell
# Example: If task folder found at C:\Source\cloud_backend\.temp\ACR-678
# Then PROJECT_ROOT = C:\Source\cloud_backend
cd C:\Source\cloud_backend; codex exec "Read the following files:`n- .temp/ACR-678/ACR-678-task-details.md (the original task)`n- .temp/ACR-678/ACR-678-implementation-plan.md (the implementation plan)`n- .temp/ACR-678/deliberation.md (our conversation history)`nFocus on the plan - do you agree with the approach? Provide recommendations with reasoning if you have concerns." -o .temp/ACR-678/codex-analysis.tmp
```

Key points:

- **CRITICAL:** Dynamically determine the PROJECT root by finding the parent directory of `.temp`
- When you find `.temp/{TASK_NUMBER}/`, extract the PROJECT root as the parent of `.temp`
- Example: If task folder is `/path/to/project/.temp/ACR-678/`, then PROJECT root is `/path/to/project/`
- Run Codex from the PROJECT root directory, NOT from arbitrary workspace locations
- Use relative paths from project root in the prompt (e.g., `.temp/ACR-678/ACR-678-task-details.md`)
- Output goes to temporary file: `.temp/{TASK_NUMBER}/codex-analysis.tmp` (overwritten each round)
- The `-o` flag writes only the agent's response (without metadata) to the specified file
- Do NOT use the `-C` flag as it causes issues with the `-o` output path
- Always include all three files in the prompt: task file, plan file, and deliberation file

## Deliberation.md Format Specification

The `deliberation.md` file tracks the full conversation between AI and Codex using this structure:

```markdown
# Deliberation: {TASK_NUMBER}

### Additional Instructions:
[Optional section - only present if additional prompt was provided]
[Full text of the additional prompt instructions for the AI]

## Round 1 - {Timestamp}

### AI Request:
[What the AI is asking Codex to review/consider in this round]

### Codex Response:
[Full response from Codex - recommendations, agreement, concerns, etc.]

### AI Analysis:
[AI's evaluation of Codex's response]

**Agreements:**
- [List of points where AI agrees with Codex and what will change]

**Disagreements:**
- [List of points where AI disagrees with Codex and reasoning]

**Alternatives:**
- [Any counter-proposals or alternative approaches]

---

## Round 2 - {Timestamp}

[Additional rounds as needed, up to 6 total]

## Final Outcome

[Added when deliberation completes]
- **Result:** Agreement Reached / Limit Reached
- **Total Rounds:** X
- **Status:** [Summary of final state]
```

**Key Points:**

- Each round is clearly marked with timestamp
- Speaker labels (AI Request, Codex Response, AI Analysis) are always present
- Agreements/disagreements are explicitly listed
- Full context preserved for Codex to read in subsequent rounds
- Final outcome documented when deliberation ends

## Prompt Structure for Codex

The prompt sent to Codex evolves based on the round:

**Round 1 (Initial Review):**

```text
Read the following files:
- .temp/{TASK_NUMBER}/{TASK_NUMBER}-task-details.md (the original Jira task)
- .temp/{TASK_NUMBER}/{TASK_NUMBER}-implementation-plan.md (the implementation plan)
- .temp/{TASK_NUMBER}/deliberation.md (our conversation - just started)

**CRITICAL REQUIREMENT - CODE UNDERSTANDING:**
Before making ANY recommendations, you MUST thoroughly understand the code:
- Examine ALL relevant source files mentioned in the plan
- Read and fully comprehend the existing implementation
- Understand the architecture, patterns, dependencies, and data flow
- NO GUESSES. NO ASSUMPTIONS. NO SHORTCUTS.
- Every recommendation must come from complete code understanding
- If you need to read additional files to understand the code, do so

**STAY FOCUSED ON TASK-RELATED CODE:**
- Only discuss code DIRECTLY related to this task
- Do NOT drift into general surrounding code or unrelated areas
- Keep your analysis focused on what needs to change for THIS task

Focus on the implementation plan. This is your first review.
- Do you agree with the approach based on your thorough code examination?
- Are there issues, risks, or improvements you'd recommend (backed by code understanding)?

**CRITICAL: Before indicating agreement, perform comprehensive verification:**
- Read through the ENTIRE plan line by line
- Check for logical inconsistencies, variable naming mismatches, missing steps
- Verify all data flows are clear and unambiguous
- Check for edge cases and conditional branches that aren't fully specified
- Ensure each step can be implemented without further clarification
- Verify step transitions and dependencies are correct
- If you find ANY gaps, inconsistencies, or ambiguities, list them as recommendations
- Only indicate agreement if you've verified the plan is complete and implementable without further questions

- If you have no concerns or recommendations after thorough verification, state that clearly
- Provide specific reasoning for any recommendations with code evidence

Structure your response in markdown format with clear sections.
```

**Round 2+ (Continuing Deliberation):**

```text
Read the following files:
- .temp/{TASK_NUMBER}/{TASK_NUMBER}-task-details.md (the original Jira task)
- .temp/{TASK_NUMBER}/{TASK_NUMBER}-implementation-plan.md (the updated implementation plan)
- .temp/{TASK_NUMBER}/deliberation.md (our full conversation history)

**CRITICAL REQUIREMENT - CODE UNDERSTANDING:**
Continue to base ALL responses on thorough code understanding:
- Re-examine relevant code sections if needed to verify reasoning
- Ensure your response is backed by actual code comprehension, not assumptions
- NO GUESSES. Every point must be informed by complete code knowledge.

**STAY FOCUSED ON TASK-RELATED CODE:**
- Keep discussion on code DIRECTLY related to this task
- Do NOT drift into unrelated areas or general surrounding code
- Stay on target with what needs to change for THIS task

Review our deliberation history in deliberation.md to see what we've discussed.

In the previous round, I [explained AI's response to Codex's recommendations].

Please respond (based on thorough code examination):
- Do you agree with my reasoning when examined against the actual code?
- Do you have additional concerns or recommendations backed by code understanding?

**CRITICAL: Before indicating satisfaction, perform comprehensive verification:**
- Re-read the ENTIRE updated plan line by line
- Verify all previously identified issues have been properly addressed
- Check for any NEW gaps, inconsistencies, or ambiguities introduced by changes
- Verify variable/entity consistency across all steps
- Check that all conditional branches and edge cases are fully specified
- Ensure each step can be implemented without further clarification
- Verify step transitions and data flows are correct
- If you find ANY remaining issues, gaps, or ambiguities, list them as recommendations
- Only indicate satisfaction if you've verified the plan is complete and implementable without further questions

- If you're satisfied with the plan now after thorough verification, state that clearly

Structure your response in markdown format with clear sections.
```

**Key Principles:**

- Always include all three files (task, plan, deliberation)
- Focus instruction on the plan review
- Reference previous rounds when Round > 1
- Ask for clear indication of agreement or continued concerns
- Let Codex read files directly - don't include content in prompt

## Error Handling

- **Codex not available**: If Codex is not installed or not in PATH, inform the user: "Codex command not found. Please ensure Codex is installed and available in your PATH." and STOP
- **Task folder not found**: If the task folder is not found, inform user: "Task folder `.temp/{TASK_NUMBER}/` not found. Please run `/cosoft-jira-01-setup {TASK_NUMBER}` first." and STOP
- **Plan not found**: If `{TASK_NUMBER}-implementation-plan.md` doesn't exist, inform user: "No `{TASK_NUMBER}-implementation-plan.md` file found. Please run `/cosoft-jira-02-plan {TASK_NUMBER}` first to create an implementation plan." and STOP
- **Codex execution failure**: If Codex returns an error or empty response, inform user: "Codex analysis failed. Error: {error message}" and STOP
- **Malformed deliberation.md**: If deliberation.md exists but cannot be parsed, try best-effort parsing. If parsing fails completely, warn user and default to Round 1
- **File write failures**: If unable to write to deliberation.md or `{TASK_NUMBER}-implementation-plan.md`, inform user: "Unable to write to {filename}. Check file permissions." and STOP
- **Round counting errors**: If round counting fails, default to safe limits (assume at maximum) and STOP with message: "Unable to parse deliberation rounds. Assuming limit reached."
- **Limit reached**: If deliberation limits are reached (6 total rounds or 3 AI rounds), document in deliberation.md, finalize plan with agreed portions, and display summary

## Notes

### System Design

- This is an **iterative deliberation system**, not a single-shot analysis
- AI and Codex are **equal partners** - neither is "king", both contribute thinking
- AI must **genuinely disagree** with Codex when appropriate - this is not rubber-stamping
- Agreement is **NOT** simply inferred from lack of recommendations
- **Agreement requires BOTH:**
  - Codex has no recommendations after thorough code examination
  - **AND** comprehensive verification checklist passes (code understanding, plan completeness, variable consistency, edge cases, implementation clarity, integration flow)
- Deliberation is only complete when there is **NOTHING LEFT TO CLARIFY** - no gaps, no ambiguities, no inconsistencies
- If verification reveals ANY issues, they must be addressed in another round before completion

### Code Understanding Requirement - NON-NEGOTIABLE

- **THOROUGH code understanding is mandatory** - no shortcuts, no guesses, no assumptions
- Both AI and Codex must **deeply comprehend** the code before making decisions
- **Read and understand ALL relevant source files** in the area affected by the task
- Understand existing implementation, architecture, patterns, dependencies, data flow
- **Every recommendation must come from a completely informed position**
- If you don't understand something, examine it further until you do
- **Lack of thorough understanding leads to mistakes that cannot happen**
- This requirement applies to EVERY round, EVERY recommendation, EVERY decision

### Focus Requirement - STAY ON TARGET

- **Only discuss code DIRECTLY related to the task at hand**
- Do NOT drift into discussing general surrounding code or unrelated areas
- Keep deliberation focused on what needs to change or be understood for THIS SPECIFIC task
- If discussing context code, explicitly state why it's relevant to the task
- Avoid scope creep - stay laser-focused on the task requirements
- If either party drifts off target, the other must bring focus back to task-related code

### File Management

- `{TASK_NUMBER}-implementation-plan.md` - Clean implementation plan, updated as agreements are reached
- `deliberation.md` - Full conversation history, grows with each round
- `codex-analysis.tmp` - Temporary file for Codex output, overwritten each round
- PROJECT root is dynamically determined by finding parent of `.temp` folder
- All files use relative paths from PROJECT root

### Deliberation Process

- Maximum 3 rounds per side (6 total rounds)
- Codex reads all three files (task, plan, deliberation) for full context each round
- AI evaluates Codex recommendations and responds with agreements/disagreements
- Process continues until agreement reached or limits hit
- Final plan includes deliberation history appended at end after delimiter

### Context Strategy

- Codex gets full conversation history via deliberation.md (mimics manual workflow)
- AI doesn't bloat its own context by re-reading files unnecessarily
- Codex can handle large context - deliberation.md can grow
- Temporary output file prevents accumulation of old responses

### Multiple Concurrent Agents

- All task-specific files live in `.temp/{TASK_NUMBER}/` folder
- Different tasks can run deliberations simultaneously without conflict
- Each task has its own `{TASK_NUMBER}-implementation-plan.md`, deliberation.md, and codex-analysis.tmp

