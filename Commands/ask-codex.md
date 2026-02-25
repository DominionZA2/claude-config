# Ask Codex

Send a prompt to Codex and return the response.

## Usage

`/ask-codex <prompt>`

## Instructions

When this command is invoked:

1. The entire argument string after `/ask-codex` is the prompt to send to Codex.
2. Spawn a new agent using the Task tool (subagent_type: "Bash") to run the Codex command. This keeps all intermediate output out of the main context.
3. The agent must:
   - Run: `codex exec --skip-git-repo-check "<prompt>"` from the current working directory
   - Capture the full output
   - Return ONLY the Codex response text
4. Once the agent returns, display the Codex response to the user. Do not add commentary — just show what Codex said.

### Agent Prompt Template

Use this prompt when spawning the agent:

```
Run the following command and return ONLY the output (no commentary):

codex exec --skip-git-repo-check "<ESCAPED_PROMPT>"

Return the complete response text exactly as Codex outputs it. Nothing else.
```

### Notes

- If no prompt is provided, ask the user what they want to ask Codex.
- If Codex fails or returns an error, report the error message to the user.
- Do not interpret or modify the Codex response. Return it verbatim.
