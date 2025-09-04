---
description: Quick git repository summary with status and recent commits
argument-hint: [optional-branch]
allowed-tools: Bash(git:*)
---

# Git Summary

Generate a comprehensive git summary for the current repository.

Run the following git commands to get repository status:

```bash
git log --oneline -10 ${1:-HEAD}
echo "---"
git status -s
echo "---"
git branch -v
```

Provide a brief analysis of:
- Recent commit activity
- Current working directory status
- Active branches