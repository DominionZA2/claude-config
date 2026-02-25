# Ask Gemini

Send a prompt to Gemini and return the response.

## Usage

`/ask-gemini <prompt>`

## Instructions

When this command is invoked:

1. The entire argument string after `/ask-gemini` is the prompt to send to Gemini.
2. Spawn a new agent using the Task tool (subagent_type: "Bash") to run the Gemini command. This keeps all intermediate output out of the main context.
3. The agent must:
   - Run: `gemini -p "<prompt>"` from the current working directory
   - Capture the full output
   - Return ONLY the Gemini response text
4. Once the agent returns, display the Gemini response to the user. Do not add commentary — just show what Gemini said.

### Agent Prompt Template

Use this prompt when spawning the agent:

```
Run the following command and return ONLY the output (no commentary):

gemini -p "<ESCAPED_PROMPT>"

Return the complete response text exactly as Gemini outputs it. Nothing else.
```

### Notes

- If no prompt is provided, ask the user what they want to ask Gemini.
- If Gemini fails or returns an error, report the error message to the user.
- Do not interpret or modify the Gemini response. Return it verbatim.
