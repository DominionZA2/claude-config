---
description: Analyze disk usage in current directory
argument-hint: [directory-path]
allowed-tools: Bash(du:*), Bash(find:*)
---

# Disk Usage Analysis

Analyze disk usage for: ${ARGUMENTS:-current directory}

```bash
du -h --max-depth=2 ${ARGUMENTS:-.} | sort -hr | head -15
echo "---"
find ${ARGUMENTS:-.} -type f -size +10M -exec ls -lh {} \; | head -10
```

Show the largest directories and files to identify space usage patterns.