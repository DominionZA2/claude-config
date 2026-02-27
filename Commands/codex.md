# Codex

Send a prompt to Codex and return the response.

## Usage

`/codex <prompt>`

## Instructions

When this command is invoked:

1. The entire argument string after `/codex` is the prompt to send to Codex.
2. If no prompt is provided, ask the user what they want to ask Codex.
3. Determine the working directory:
   - Use the current project root (parent of `.temp` if it exists, otherwise current working directory)
4. Run Codex using the Bash tool directly (do NOT spawn a sub-agent — run it yourself):
   - Pipe the prompt via stdin using a heredoc to avoid quoting issues with special characters
   - Use `--full-auto` for autonomous execution
   - Use `--skip-git-repo-check` for worktree compatibility
   - Use `-o` to write the response to a temporary file
   - Run in background since Codex can take several minutes
5. When Codex completes, read the output file and display the response to the user verbatim.
6. Do not interpret or modify the Codex response — show exactly what Codex said.

### Command Template

```bash
cd {PROJECT_ROOT} && cat <<'CODEX_PROMPT_EOF' | codex exec --skip-git-repo-check --full-auto -o {OUTPUT_FILE} -
{PROMPT}
CODEX_PROMPT_EOF
```

Where:
- `{PROJECT_ROOT}` is the project root directory
- `{OUTPUT_FILE}` is a temporary file for the response (e.g., `/tmp/codex-response-{timestamp}.md`)
- `{PROMPT}` is the user's prompt, inserted verbatim between the heredoc delimiters

### Key Details

- **Heredoc stdin**: The prompt is piped via `cat <<'CODEX_PROMPT_EOF'` with single-quoted delimiter to prevent shell expansion. This handles any special characters, newlines, backticks, or quotes in the prompt.
- **`--full-auto`**: Runs Codex autonomously without interactive prompts (sandbox: workspace-write).
- **`--skip-git-repo-check`**: Required when running from worktrees or non-git directories.
- **`-o {file}`**: Writes only the final agent response (no metadata) to the specified file.
- **Background execution**: Use `run_in_background: true` on the Bash tool since Codex typically takes 1-5 minutes. You'll be notified when it completes.
- **Timeout**: Set the Bash timeout to 600000 (10 minutes) to accommodate longer analyses.

### Error Handling

- If Codex is not installed or not in PATH, inform the user: "Codex command not found. Please ensure Codex is installed and available in your PATH."
- If Codex fails or returns an error, report the error message to the user.
- If the output file is empty after Codex completes, report that Codex produced no output.

### Notes

- This replaces the older `/ask-codex` skill which had quoting issues with special characters.
- For reviewing implementation plans or code, consider `/codex-review` instead — it has a structured prompt template.
