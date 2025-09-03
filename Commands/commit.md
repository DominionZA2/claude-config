# Commit Command

## Description
The commit command automatically stages all current changes and commits them with a concise but appropriate commit message. This is a quick way to commit work in progress without needing to manually stage files or write commit messages.

## Usage
```
/commit [message]
```

## Parameters
- `[message]`: Optional custom commit message. If not provided, an appropriate message will be generated automatically.

## Behavior
When the `/commit` command is executed, the LLM will:

1. **Stage All Changes**: Run `git add .` to stage all modified, new, and deleted files
2. **Generate Commit Message**: If no custom message is provided, create a concise but descriptive commit message based on:
   - Types of files changed (e.g., "Update configuration files", "Add new features", "Fix bugs")
   - Scope of changes (e.g., "Minor updates", "Major refactoring", "Documentation improvements")
   - Current context and file patterns
3. **Commit Changes**: Execute `git commit -m "<message>"` with the generated or provided message
4. **Report Results**: Show the commit hash and summary of what was committed

## Commit Message Generation Rules
The automatically generated commit message should follow these guidelines:

### Message Types
- **"Add"**: When new files or features are added
- **"Update"**: When existing files are modified
- **"Fix"**: When bug fixes are made
- **"Remove"**: When files are deleted
- **"Refactor"**: When code is restructured without changing functionality
- **"Configure"**: When configuration files are modified
- **"Document"**: When documentation is added or updated

### Message Format
- Use imperative mood (e.g., "Add feature" not "Added feature")
- Keep messages concise but descriptive (50 characters or less preferred)
- Capitalize the first letter
- No period at the end
- Include scope when relevant (e.g., "Update API endpoints", "Fix database connection")

### Example Generated Messages
- `"Add user authentication system"`
- `"Update configuration files"`
- `"Fix database connection issue"`
- `"Refactor API response handling"`
- `"Remove deprecated functions"`
- `"Configure CI/CD pipeline"`
- `"Document installation process"`
- `"Update dependencies"`
- `"Add error handling"`
- `"Fix typos in documentation"`

## Command Implementation

When the `/commit` command is invoked:

1. **Check Git Status**
   ```bash
   git status --porcelain
   ```
   - Verify there are changes to commit
   - If no changes, inform user and exit

2. **Stage All Changes**
   ```bash
   git add .
   ```

3. **Generate Commit Message** (if not provided)
   - Analyze changed files using `git diff --cached --name-only`
   - Determine change types and scope
   - Create appropriate message following the rules above

4. **Commit Changes**
   ```bash
   git commit -m "Generated or provided message"
   ```

5. **Report Success**
   - Show commit hash
   - Display commit message
   - Show number of files changed

## Error Handling
- **No Git Repository**: Inform user that current directory is not a git repository
- **No Changes**: Report that there are no changes to commit
- **Commit Failed**: Display git error message and suggest solutions
- **Merge Conflicts**: Detect ongoing merge and advise user to resolve conflicts first

## Example Usage

```bash
# Commit with auto-generated message
/commit

# Commit with custom message
/commit "Implement user dashboard feature"

# The command will NOT push - only add and commit locally
```

## Example Output
```
✓ Staged all changes
✓ Committed with message: "Update configuration and add new API endpoints"
✓ Commit hash: a1b2c3d
✓ Files changed: 5 files modified, 2 files added
```

## Integration Notes
- This command only handles local commits, never pushes to remote
- Works with the current branch
- Respects .gitignore rules
- Can be used in any git repository
- Should work alongside other git commands and workflows
