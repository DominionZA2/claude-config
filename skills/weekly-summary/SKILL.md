# Weekly Commit Summary Command

Generate a concise, meeting-ready summary of my personal commits across all tracked repositories.

## Arguments

- **time range** (optional): Any git-compatible time expression passed after the command. Defaults to `7 days ago` if not specified.
- Examples:
  - `/weekly-summary` → last 7 days
  - `/weekly-summary 14 days` → last 14 days
  - `/weekly-summary 1 month` → last month
  - `/weekly-summary 2026-02-01` → since a specific date

## What this command does

- Pulls the latest changes from each repository on its correct branch.
- Retrieves the user's git identity from the repo config.
- Collects all personal commits for the specified time range (excluding merges). Defaults to last 7 days.
- Groups and summarizes commits by topic/feature into a concise bullet-pointed format suitable for a standup or status meeting.

## Repositories and branches

| Repository | Path | Branch |
|---|---|---|
| cloud_backend | `~/source/cloud_backend` | `develop` |
| v2-portal | `~/source/v2-portal` | `staging` |

## Instructions for the AI

When invoked (example: `/weekly-summary` or `/weekly-summary 14 days`):

1. **Parse the time range**:
   - If the user provided an argument, use it as the `--since` value for git log.
     - If it looks like a number + unit (e.g. `14 days`, `1 month`), use `--since="<value> ago"`.
     - If it looks like a date (e.g. `2026-02-01`), use `--since="<date>"`.
   - If no argument was provided, default to `--since="7 days ago"`.
   - Store this as `<since-value>` for use in subsequent steps.

2. **Checkout and pull each repository**:
   - For each repo in the table above, checkout the specified branch and pull latest:
     ```
     cd <path> && git checkout <branch> && git pull
     ```
   - Run these in parallel where possible.
   - If a checkout or pull fails, report the error and continue with other repos.

3. **Determine the git user identity**:
   - Read `git config user.name` and `git config user.email` from any of the repos.
   - Use both name and email as `--author` filters to catch all commits.

4. **Collect commits for the time range**:
   - For each repo, run:
     ```
     git log --author="<name>" --author="<email>" --since="<since-value>" --oneline --no-merges <branch>
     ```
   - Also check for any very recent commits on feature branches that haven't been merged yet:
     ```
     git log --author="<email>" --since="<since-value>" --oneline --no-merges --all --not <branch>
     ```
   - If unmerged feature branch commits are found, include them in the summary and note they are not yet merged.

5. **Generate the meeting summary**:
   - Group related commits together by feature or area (e.g. "Recipe Management", "Menu Import", "Reports").
   - Use this format:
     ```
     ## My Contributions — Last <time range>

     ### <Repo Name> (<repo folder>)
     - **<Feature/Area>** — Brief description of what was done
       - Sub-bullet for individual changes if there were multiple related commits
     ```
   - Keep it concise — this is for a quick verbal update in a meeting.
   - Highlight performance improvements and bug fixes clearly.
   - For commits not yet merged to the main branch, append *(not yet merged)*.

6. **Report the applied time range**:
   - Before the summary, display the exact time range that was used, e.g.:
     ```
     **Time range:** 2026-02-12 → 2026-02-19 (last 7 days)
     ```
   - Always show the resolved start date and today's date, plus the original range expression in parentheses.

7. **Present the summary** to the user, ready to read aloud in a meeting.

## Important rules

- **Always checkout and pull before reading logs** — stale local branches will give incomplete results.
- **Always use the correct branch per repo** as specified in the table above.
- **Exclude merge commits** — only show actual work commits.
- **Check for unmerged feature branch work** — recent commits may not have landed on the main branch yet.
- **Do not editorialize** — summarize what was committed, don't add opinions or suggestions.
