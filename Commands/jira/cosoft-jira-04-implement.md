# Jira Task Implementation Command

Implement the code changes according to the agreed-upon plan, including tests if specified.

## What this command does

Reads the implementation plan from `{TASK_NUMBER}-implementation-plan.md` and implements all code changes step by step according to the plan. This includes implementing the main functionality and generating tests if they were included in the plan.

**Usage:** `/cosoft-jira-04-implement {TASK_NUMBER} [optional additional prompt]`

- The task number is required (e.g., "ACR-678" or "API-708")
- An optional additional prompt can be provided after the task number to give the AI extra instructions to follow during implementation
- Example: `/cosoft-jira-04-implement ACR-678 Pay special attention to performance implications`

The command follows the plan step by step, implementing code changes and tests as specified.

## Instructions for the AI

When this command is invoked with a task number:

### CRITICAL REQUIREMENT: CODE UNDERSTANDING

**BEFORE making ANY code changes, you MUST thoroughly understand the code:**

- Read and comprehend ALL relevant source files mentioned in the plan
- Understand the existing implementation, architecture, and patterns
- Understand dependencies, relationships, and data flow
- Understand why the code works the way it does
- **NO GUESSES. NO ASSUMPTIONS. NO SHORTCUTS.**
- Every change must come from a deeply informed point of view
- If you don't understand something, examine it further until you do

**STAY FOCUSED ON TASK-RELATED CODE:**

- Only implement code that is DIRECTLY related to the task at hand
- Do NOT drift into implementing general improvements or unrelated areas
- Keep implementation focused on what needs to be changed for THIS task
- Follow the plan exactly - do not deviate unless the plan is incorrect

**This is non-negotiable. Lack of thorough understanding leads to mistakes that cannot happen.**

### SETUP PHASE

- Parse the user's input to extract:
  - Task number: First token/word (e.g., "ACR-678" or "API-708")
  - Additional prompt (optional): Any text after the task number
  - Example: Input "ACR-678 Pay special attention to performance" → Task number: "ACR-678", Additional prompt: "Pay special attention to performance"
  - If no additional text exists after the task number, `ADDITIONAL_PROMPT` is empty/undefined
- Store `ADDITIONAL_PROMPT` for use during implementation (if provided)
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

### PLAN REVIEW PHASE

- Read `{TASK_NUMBER}-implementation-plan.md` completely:
  - Understand the full scope of work
  - Identify all files that need to be created or modified
  - Understand the implementation steps in order
  - Note any dependencies between steps
  - Identify test requirements if included in the plan
- Verify the plan is complete and implementable:
  - Check that all file paths are specified
  - Verify that implementation steps are clear
  - Ensure dependencies are understood
  - If the plan is incomplete or unclear, inform the user: "Plan appears incomplete or unclear. Please review and update `{TASK_NUMBER}-implementation-plan.md` or run `/cosoft-jira-03-deliberate-plan-codex {TASK_NUMBER}` to refine the plan."
- If `ADDITIONAL_PROMPT` exists, incorporate those instructions into the implementation approach

### MANDATORY PLAN VERIFICATION PHASE

**CRITICAL: This phase MUST be completed before starting implementation. Do NOT skip or rush through this phase.**

- **Read the ENTIRE `{TASK_NUMBER}-implementation-plan.md` file from start to finish, line by line:**
  - Do not skip any sections
  - Do not assume constraints from one section apply to another
  - Read every word to understand the complete plan
- **Identify ALL top-level sections:**
  - Look for all `##` headers (top-level sections)
  - Common sections include:
    - `## Detailed Implementation Steps` (or similar)
    - `## Testing Strategy`
    - `## Investigation Phase` (or similar)
    - Any other actionable sections
  - Create a list of all top-level sections found
- **For each top-level section, determine:**
  - **What it requires:** What needs to be done in this section?
  - **Constraints:** Does this section have any constraints (wait conditions, dependencies, "do not implement until X", etc.)?
  - **Constraint scope:** Does the constraint apply only to this section, or to subsequent sections?
    - **CRITICAL:** If a constraint is stated within a section, it applies ONLY to that section unless explicitly stated otherwise
    - **CRITICAL:** If Section A says "wait for X", this applies ONLY to Section A, NOT to Section B unless explicitly stated
- **Create an implementation checklist:**
  - List ALL sections that require implementation:
    - [ ] Implementation Steps (from "Detailed Implementation Steps" or similar section)
    - [ ] Testing Strategy (if "Testing Strategy" section exists)
    - [ ] Any other actionable sections
  - For each checklist item:
    - Verify what needs to be done
    - Check for constraints (wait conditions, dependencies)
    - If no constraints are found, mark as "READY TO IMPLEMENT"
    - If constraints exist, note what they are and when they apply
    - Determine if the constraint blocks implementation or if the section can proceed independently
- **Section Independence Rules - Apply these rules when analyzing sections:**
  - **Top-level sections (## headers) are independent unless explicitly linked**
  - A constraint in Section A does NOT apply to Section B unless explicitly stated
  - If Section A says "wait for X", this applies ONLY to Section A, not to Section B
  - Each section must be checked for its own constraints
  - If a section has no constraints, it can be implemented independently
  - **Testing Strategy is ALWAYS independent unless explicitly stated otherwise**
  - If Testing Strategy section exists and has no "wait" constraint, it MUST be implemented
- **CRITICAL Verification Checks:**
  - **Treat each top-level section independently unless explicitly stated otherwise**
  - **If Testing Strategy section exists, it MUST be implemented unless explicitly excluded**
  - **Constraints in one section do NOT apply to peer sections unless explicitly stated**
  - **Do NOT assume constraints apply across sections**
  - **If a section has no constraints, it is ready to implement**
- **Document the verification results:**
  - List all sections found
  - For each section, document: what it requires, constraints (if any), and implementation readiness
  - Create the implementation checklist with status for each item
  - If any section was found to have constraints, document what they are and how they affect implementation

### IMPLEMENTATION PHASE

**CRITICAL: Follow the implementation checklist created during MANDATORY PLAN VERIFICATION PHASE. Do NOT skip any checklist items unless explicitly excluded in the plan.**

- **Use the implementation checklist from MANDATORY PLAN VERIFICATION PHASE:**
  - Work through each checklist item in order
  - For each item marked "READY TO IMPLEMENT", proceed with implementation
  - For items with constraints, respect those constraints (wait if needed, or implement if constraints don't block)
  - **Do NOT skip any checklist items unless explicitly excluded in the plan**
  - **CRITICAL:** If Testing Strategy exists in the checklist and has no "wait" constraint, it MUST be implemented

- **Implement Implementation Steps section (if present in checklist):**
  - Follow the plan's implementation steps in order
  - For each step:
    - Read the relevant file(s) that need to be modified
    - Understand the current code structure
    - Implement the changes as specified in the plan
    - Verify the changes are correct and don't break existing functionality
    - Ensure code follows existing patterns and conventions
  - Create new files if specified in the plan
  - Modify existing files as specified
  - Ensure all changes align with the plan's requirements
  - Mark this checklist item as complete when done

- **Implement Testing Strategy section (if present in checklist and ready to implement):**
  - **CRITICAL:** If Testing Strategy section exists in the plan and has no "wait" constraint, it MUST be implemented
  - **CRITICAL:** Do NOT skip Testing Strategy unless it is explicitly excluded in the plan (e.g., "Testing: Excluded per user request")
  - Implement all unit tests specified in the plan
  - Implement all integration tests specified in the plan
  - Implement edge case tests as specified
  - Follow the test file locations and naming conventions from the plan
  - Ensure tests follow existing test patterns in the codebase
  - Mark this checklist item as complete when done

- **Implement any other actionable sections from the checklist:**
  - Work through each section independently based on its own constraints
  - Follow the same process: read, understand, implement, verify
  - Mark each checklist item as complete when done

- **Document implementation progress:**
  - Keep track of which checklist items have been completed
  - Note any deviations from the plan (if necessary) and why
  - Document any issues encountered during implementation
  - If any checklist item was skipped, document why and get explicit confirmation if needed

### VERIFICATION PHASE

**CRITICAL: Before declaring implementation complete, verify that ALL plan sections were addressed.**

- **Verify all plan sections were addressed:**
  - Review the implementation checklist from MANDATORY PLAN VERIFICATION PHASE
  - For each checklist item:
    - Verify it was completed (if it was marked "READY TO IMPLEMENT")
    - If it was skipped, verify it was explicitly excluded in the plan or had blocking constraints
    - Document the status of each checklist item
  - **CRITICAL Checks:**
    - All implementation steps from plan were completed (if Implementation Steps section existed)
    - All tests from Testing Strategy were implemented (if Testing Strategy section existed and was ready)
    - No sections were skipped or ignored without explicit justification
    - Any "wait" conditions were properly handled (either waited for, or determined not to block)
  - **If any section was skipped:**
    - Document why it was skipped
    - Verify it was explicitly excluded in the plan OR had blocking constraints
    - If skipped without clear justification, STOP and inform the user before declaring completion
- **Verify implementation completeness:**
  - Verify all files mentioned in the plan have been created or modified
  - Check that implementation matches the plan's requirements
  - Ensure code compiles (if applicable)
  - Verify no obvious syntax errors or issues
  - Check that existing functionality hasn't been broken (where possible)
- **If `ADDITIONAL_PROMPT` exists, verify those requirements have been met**
- **Final verification:**
  - Confirm that every top-level section identified in MANDATORY PLAN VERIFICATION PHASE was either:
    - Implemented completely
    - Explicitly excluded in the plan
    - Blocked by constraints (and those constraints were respected)
  - If any section doesn't meet these criteria, do NOT declare implementation complete

### COMPLETION SUMMARY

- Display a summary of implementation:
  - **Task:** {TASK_NUMBER} - {Task Title}
  - **Files Created:** [List of new files]
  - **Files Modified:** [List of modified files]
  - **Tests Created:** [List of test files, if applicable] or "Tests excluded per plan"
  - **Implementation Status:** Complete / Partial (if some steps couldn't be completed)
  - **Next Steps:** Suggest running `/cosoft-jira-05-deliberate-code-review-codex {TASK_NUMBER}` to review the implementation
- If Implementation Status is **Complete**, end with an explicit success line so operators know the workflow continues, e.g. `✅ Implementation complete. Next step: /cosoft-jira-05-deliberate-code-review-codex {TASK_NUMBER}`

### ERROR HANDLING

- If task number not provided: Ask the user for it
- If task folder not found: Inform user: "Task folder `.temp/{TASK_NUMBER}/` not found. Please run `/cosoft-jira-01-setup {TASK_NUMBER}` first." and STOP
- If `{TASK_NUMBER}-implementation-plan.md` doesn't exist: Inform user: "No `{TASK_NUMBER}-implementation-plan.md` file found. Please run `/cosoft-jira-02-plan {TASK_NUMBER}` first to create an implementation plan." and STOP
- If plan is incomplete: Inform user and suggest running deliberation command
- If implementation fails at a step: Document the issue, inform the user, and STOP
- If unable to read or write files: Inform user: "Unable to access {filename}. Check file permissions." and STOP

## Notes

### Implementation Strategy

- Follow the plan exactly - do not add features not in the plan
- Implement step by step - complete each step before moving to the next
- Maintain existing code patterns and conventions
- Ensure code quality matches the existing codebase
- If the plan is unclear, ask for clarification rather than guessing

### Test Implementation

- **CRITICAL:** Tests MUST be implemented if the plan includes a Testing Strategy section
- **CRITICAL:** Testing Strategy is a top-level section and is independent unless explicitly constrained
- **CRITICAL:** Do NOT skip Testing Strategy unless it is explicitly excluded in the plan (e.g., "Testing: Excluded per user request")
- If Testing Strategy section exists and has no "wait" constraint, it MUST be implemented
- Follow the test structure and organization specified in the plan
- Use existing test patterns from the codebase
- Ensure tests are comprehensive and cover the scenarios specified in the plan
- The MANDATORY PLAN VERIFICATION PHASE will identify Testing Strategy as a checklist item if it exists

### File Management

- All implementation files are in the PROJECT ROOT (not in `.temp` folder)
- Task-specific planning files remain in `.temp/{TASK_NUMBER}/`
- Implementation creates/modifies actual source code files
- PROJECT root is dynamically determined by finding parent of `.temp` folder

### Additional Prompt Handling

- If `ADDITIONAL_PROMPT` is provided, incorporate those instructions into implementation
- Additional prompt can guide focus areas, coding style preferences, or specific requirements
- Additional prompt supplements but does not replace the plan
