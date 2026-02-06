# MySQL Restore Command

Restores a backup file to the local MySQL server. This is a DESTRUCTIVE operation that drops existing databases.

## Usage
```
/mysql:restore [backup_file] [options]
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `backup_file` | Path to the backup file (.sql or .sql.gz) | Latest backup |
| `--server` | Server to restore to: `local` or `test` | `local` |
| `--confirm` | Skip confirmation prompt | `false` |

## Required Environment Variables

Stored in `~/.claude/mysql.env`:

| Variable | Description |
|----------|-------------|
| `MYSQL_LOCAL_HOST` | Local server hostname |
| `MYSQL_LOCAL_PORT` | Local server port |
| `MYSQL_LOCAL_USER` | Local server username |
| `MYSQL_LOCAL_PASSWORD` | Local server password |

## Instructions for the AI

When this command is invoked:

### 1. Source Environment Variables

```bash
source ~/.claude/mysql.env
```

### 2. Parse Arguments

- **backup_file**: Path to the backup file (optional — if omitted, auto-selects the latest backup)
- **server**: Target server (default: `local` - NEVER default to test for restore!)
- **confirm**: Whether to skip confirmation

### 3. Resolve Backup File

**If a backup file was provided:** validate that it exists.

```bash
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi
```

**If NO backup file was provided:** automatically find the most recent backup in `MYSQL_BACKUP_DIR` (by file modification time):

```bash
BACKUP_FILE=$(ls -t "${MYSQL_BACKUP_DIR}"/*.sql.gz "${MYSQL_BACKUP_DIR}"/*.sql 2>/dev/null | head -1)
```

If no backups are found, display an error and stop:

```
No backup files found in ${MYSQL_BACKUP_DIR}
```

### 4. Confirmation Prompt

**CRITICAL:** Before any restore operation, use the `AskUserQuestion` tool to confirm the selected backup file. Display:

- The resolved backup file path and size
- The target server
- Whether the file was auto-selected (latest) or explicitly provided

Example prompt:

```
Restore this backup?

File: ~/Backups/mysql/backup_20250205_120000.sql.gz
Size: 42 MB
Source: Auto-selected (latest backup)
Target: local (127.0.0.1:3306)

WARNING: This will DROP all existing non-system databases on the target server.
```

Options: **"Yes, restore"** / **"No, cancel"**

- **NEVER** proceed without explicit user confirmation via the prompt
- **NEVER** restore to test server without extra warnings
- If the user cancels, stop immediately and list available backups for reference

### 5. Select Server Configuration

**For local (default for restore):**
```bash
HOST="${MYSQL_LOCAL_HOST}"
PORT="${MYSQL_LOCAL_PORT}"
USER="${MYSQL_LOCAL_USER}"
PASS="${MYSQL_LOCAL_PASSWORD}"
```

### 6. Drop Existing Databases

```bash
# Get list of non-system databases
DATABASES=$(mysql -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS" -N -e "SHOW DATABASES" | grep -Ev "^(information_schema|mysql|performance_schema|sys)$")

# Disable foreign key checks and drop each database
mysql -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS" -e "SET foreign_key_checks = 0;"

for DB in $DATABASES; do
    echo "Dropping database: $DB"
    mysql -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS" -e "DROP DATABASE IF EXISTS \`$DB\`;"
done

mysql -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS" -e "SET foreign_key_checks = 1;"
```

### 7. Create Default Users

```bash
mysql -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS" << 'EOF'
CREATE USER IF NOT EXISTS 'frank'@'%' IDENTIFIED BY 'P@ssw0rd1';
CREATE USER IF NOT EXISTS 'admin'@'%' IDENTIFIED BY 'P@ssw0rd1';
CREATE USER IF NOT EXISTS 'aura'@'%' IDENTIFIED BY 'P@ssw0rd1';
GRANT ALL PRIVILEGES ON *.* TO 'frank'@'%' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON *.* TO 'admin'@'%' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON *.* TO 'aura'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
EOF
```

### 8. Execute Restore

**For .sql.gz files:**
```bash
gunzip -c "$BACKUP_FILE" | mysql -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS"
```

**For .sql files:**
```bash
mysql -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS" < "$BACKUP_FILE"
```

### 9. Display Results

```
Restore completed successfully!

Target: local (127.0.0.1:3306)
Backup: <filename>
Duration: <time taken>

Users created/verified:
- frank@%
- admin@%
- aura@%

Databases restored:
<list of databases>
```

## Examples

### Restore the latest backup (auto-selected)
```
/mysql:restore
```

### Restore a specific backup file
```
/mysql:restore ~/Backups/mysql/backup_20250205_120000.sql.gz
```

## Safety Warnings

- **DESTRUCTIVE**: This command drops ALL existing non-system databases
- **LOCAL ONLY**: Defaults to local server - be VERY careful with --server test
- **CONFIRMATION REQUIRED**: Always confirms before proceeding
- **NO UNDO**: There is no way to undo a restore operation

## Typical Workflow

1. Create backup from test: `/mysql:backup`
2. Restore latest backup to local: `/mysql:restore`
