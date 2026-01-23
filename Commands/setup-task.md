# Task Setup Command

Creates a task-specific markdown file from user-provided task information.

## What this command does

Accepts a task number and summary as command arguments, then collects the description interactively. Creates a task-specific markdown file (`.temp/{TASK_NUMBER}/{TASK_NUMBER}-task-details.md`) with the provided data.

**Usage:** `/setup-task {TASK_NUMBER} {TASK_SUMMARY}`

- `{TASK_NUMBER}`: The task number (e.g., "ACR-678" or "API-708")
- `{TASK_SUMMARY}`: A brief summary/title of the task (can contain spaces)
- Description will be collected interactively after the command is invoked

## Instructions for the AI

When this command is invoked:

### SETUP PHASE

- Parse the user's input to extract:
  - Task number: First token/word (e.g., "ACR-678" or "API-708")
  - Task summary: All remaining text after the task number (can contain spaces)
  - Example: Input "ACR-678 Fix login bug" → Task number: "ACR-678", Task summary: "Fix login bug"
  - If task summary is missing, inform the user and STOP
- Determine the project root:
  - Search for the task folder `.temp/{TASK_NUMBER}/` in the workspace(s)
  - If the folder exists, extract the PROJECT ROOT from the task folder path:
    - If task folder is at `/path/to/project/.temp/{TASK_NUMBER}/`, then PROJECT ROOT is `/path/to/project/`
    - The PROJECT ROOT is the parent directory of the `.temp` folder
  - If the folder doesn't exist, search for any `.temp` folder in the workspace to determine PROJECT ROOT
  - If no `.temp` folder exists, use the workspace root as PROJECT ROOT
- Create `.temp` folder in PROJECT ROOT if it doesn't exist
- Create `.temp/{TASK_NUMBER}/` folder if it doesn't exist
- Determine the full path to the task folder: `{PROJECT_ROOT}/.temp/{TASK_NUMBER}/`

### CREATE INITIAL MARKDOWN FILE

- **CRITICAL:** Create the markdown file immediately after SETUP PHASE, before collecting description
- Create or overwrite `{TASK_NUMBER}-task-details.md` in `.temp/{TASK_NUMBER}/` folder
- Initial file structure (description section will be empty initially):
  - **Task number as header/title:** `# {TASK_NUMBER}`
  - **## Summary**
    - Task summary text provided by user
  - **## Description**
    - Leave empty or add placeholder text like "Description to be added..."
- Format the markdown file clearly with proper headers and structure

### COLLECT TASK DATA

- Parse task number from first token of user input (already done in SETUP PHASE)
- Parse task summary from remaining tokens (already done in SETUP PHASE)
- If task summary is empty or missing, inform the user that both task number and summary are required and STOP
- Prompt the user interactively for the task description:
  - Ask: "Please provide the description for task {TASK_NUMBER}:"
  - Wait for user input
  - Store the description text
- **Update the markdown file** with the description in the Description section
- Allow the user to add or update the description interactively during the conversation - each time the description is updated, update the markdown file accordingly

### DISPLAY SUMMARY

- Display a summary including:
  - Task number: {TASK_NUMBER}
  - Summary: {TASK_SUMMARY}
  - Description preview: First 100-200 characters of description (or "No description yet" if not provided)
  - File location: `.temp/{TASK_NUMBER}/{TASK_NUMBER}-task-details.md`
- End with a clear success message, e.g. `Task file created at .temp/{TASK_NUMBER}/{TASK_NUMBER}-task-details.md. You can continue to update the description during our conversation.`

### ERROR HANDLING

- If the task number is not provided: Inform user that task number is required and STOP
- If the task summary is not provided: Inform user that task summary is required and STOP
- If folder creation fails: Display error message and STOP
- If description collection fails or is interrupted: The file has already been created, inform user they can provide description later and continue conversation
