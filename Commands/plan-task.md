# Task Planning Command

Analyze a task and create a detailed implementation plan.

## What this command does
Reads all files in the task folder, studies the codebase, and creates a comprehensive plan for implementing the task. This command should be run after the task setup is complete and all required files are available in the task folder.

**Usage:** `/plan-task {TASK_NUMBER} [optional additional prompt]`

- The task number is required (e.g., "ACR-678" or "API-708")
- An optional additional prompt can be provided after the task number to give the AI extra instructions to follow during planning
- Example: `/plan-task ACR-678 Pay special attention to performance implications`
- Example (exclude tests): `/plan-task ACR-678 exclude tests` or `/plan-task ACR-678 no tests needed`

By default, the plan will include comprehensive test coverage planning. You can opt out by including phrases like "exclude tests", "no tests", "skip tests", etc. in the additional prompt.

## Instructions for the AI
When this command is invoked with a task number:

### SETUP PHASE

- Parse the user's input to extract:
  - Task number: First token/word (e.g., "ACR-678" or "API-708")
  - Additional prompt (optional): Any text after the task number
  - Example: Input "ACR-678 Pay special attention to performance" → Task number: "ACR-678", Additional prompt: "Pay special attention to performance"
  - If no additional text exists after the task number, `ADDITIONAL_PROMPT` is empty/undefined
- Store `ADDITIONAL_PROMPT` for use during planning (if provided)
- Check for test opt-out in additional prompt:
  - Simple inference: Look for phrases indicating test exclusion (case-insensitive)
  - Common phrases: "exclude tests", "no tests", "skip tests", "no testing", "without tests", "don't test", "no test coverage", etc.
  - Use natural language understanding to detect intent to exclude tests
  - Set `INCLUDE_TESTS` flag: `true` by default, `false` if opt-out detected
- Verify that the task folder exists: `.temp/{TASK_NUMBER}/`
  - **If the task folder does not exist:** Inform the user that the task folder is not found and that they should run the setup command first (`/setup-task`)
  - **Only if the task folder exists:** Proceed with the following steps
- Planning Phase:
  - Read ALL files in the task folder (`.temp/{TASK_NUMBER}/`) to understand the task requirements:
    - Read the markdown file (`{TASK_NUMBER}-task-details.md`) to get task details
    - Read any attachment files (specifications, documentation, etc.)
    - Read any other files that may have been added to the folder
  - Treat API-specific instructions in the task as guidance, not absolute truth:
    - If the task describes particular API endpoints, payloads, or flows, verify them against the actual backend codebase before accepting them
    - Perform thorough code analysis in the relevant backend services to confirm how those APIs actually behave
    - Adjust the plan to match current backend practices and implementations if the documented API guidance is outdated or inaccurate
    - Document any discrepancies you discover so the plan reflects the true state of the system
  - Study the codebase to understand:
    - What needs to be implemented based on the task requirements
    - What code already exists that might be relevant
    - What might already be partially or fully implemented
    - Architecture and patterns used in the codebase
  - Compare documentation with code to reach an understanding:
    - Cross-reference task requirements with existing code
    - Identify gaps between requirements and current implementation
    - Identify any existing code that might be reused or modified
    - Understand the full scope of work needed
- Create or update the implementation plan file (`.temp/{TASK_NUMBER}/{TASK_NUMBER}-implementation-plan.md`) with:
    - Summary of task requirements
    - Analysis of existing code and what's already done
    - Gap analysis between requirements and current state
    - Detailed plan for implementing the task
    - Steps needed to complete the work
    - Any dependencies or prerequisites
    - File locations and code paths that need to be modified
    - **CRITICAL: Plan Structure Requirements:**
      - Use clear section headers: `##` for top-level sections (e.g., `## Detailed Implementation Steps`, `## Testing Strategy`)
      - Make section hierarchy explicit and unambiguous
      - **Section Independence:** Top-level sections (## headers) are independent unless explicitly linked
      - **Constraint Scoping:** If a constraint (e.g., "wait for investigation", "do not implement until X") applies only to a specific section, state it explicitly: "**Note:** This constraint applies only to [Section Name]"
      - If a constraint applies to the entire plan, state it clearly at the top
      - **Testing Strategy Section:**
        - Must be a top-level section: `## Testing Strategy` (not nested under implementation steps)
        - If Testing Strategy has constraints, state them explicitly within that section
        - If Testing Strategy has no constraints, make it clear it can be implemented independently
        - If Testing Strategy should wait for something, explicitly state: "**Note:** Testing Strategy should be implemented after [condition]"
    - **Testing Strategy** (by default, unless opted out):
      - **When `INCLUDE_TESTS` is true (default):**
        - Create a comprehensive "Testing Strategy" section in the implementation plan file as a top-level section (`## Testing Strategy`)
        - Include:
          - Unit test requirements for new/changed functionality
          - Integration test requirements if applicable
          - Test file locations and naming conventions (following project patterns)
          - Test coverage goals (aim for thorough coverage)
          - Specific test scenarios based on task requirements
          - Edge cases to test
          - Any test data setup requirements
          - Mocking requirements if applicable
          - Test structure and organization
          - Which files need tests created/modified
          - What functionality needs to be tested
          - Test types (unit, integration, etc.)
          - Key test scenarios and edge cases
        - If Testing Strategy has no constraints, add a note: "**Note:** This section can be implemented independently of other sections"
      - **When `INCLUDE_TESTS` is false (opted out):**
        - Skip test planning section entirely
        - Add a brief note in the implementation plan file: "Testing: Excluded per user request"
    - If `ADDITIONAL_PROMPT` exists and contains other instructions beyond test opt-out, incorporate those instructions into the planning process
- If the task number is not provided, ask the user for it

### COMPLETION SUMMARY

- After saving `{TASK_NUMBER}-implementation-plan.md`, display a short summary:
  - **Task:** {TASK_NUMBER} - {Task Title}
  - **Plan File:** `.temp/{TASK_NUMBER}/{TASK_NUMBER}-implementation-plan.md`
  - **Testing Strategy:** Included / Excluded (per instructions)
  - Call out any major constraints or follow-ups noted in the plan
- Finish with an explicit success line: `✅ Implementation plan ready.`

