---
description: Quick deployment check and build
argument-hint: [environment]
allowed-tools: Bash(npm:*), Bash(git:*), Bash(docker:*)
---

# Quick Deploy

Prepare and validate deployment for: ${ARGUMENTS:-dev}

Run these checks:

```bash
git status
echo "---"
npm run lint
echo "---"
npm run test
echo "---"
npm run build
```

If all checks pass, confirm the deployment is ready for: ${ARGUMENTS:-dev}