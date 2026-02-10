# Report Sync Deploy

Run this exactly. Do not interpret, modify, or handle errors yourself. Just run it and show the output.

```bash
source ~/.claude/report-sync.env && python3 ~/.claude/scripts/report-sync-deploy.py --notify-frank
```

For test mode (uses test branch, no Frank notification):

```bash
source ~/.claude/report-sync.env && python3 ~/.claude/scripts/report-sync-deploy.py --test
```
