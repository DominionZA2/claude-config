# MySQL Restore Command

Run this exactly. Do not interpret, modify, or handle errors yourself. Just run it and show the output.

The user must provide a backup file path as the argument: /mysql:restore {BACKUP_FILE}

```bash
source ~/.claude/mysql.env && python3 ~/.claude/scripts/mysql-restore.py "{BACKUP_FILE}"
```

If no backup file was provided, list the available files and ask which one:

```bash
ls -lht ~/Backups/mysql/*.sql 2>/dev/null
```
