# MySQL Backup Command

Creates a full backup of all databases from the test MySQL server.

## Usage
```
/mysql:backup [options]
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--server` | Server to backup from: `local` or `test` | `test` |
| `--db` | Specific database to backup (or `all` for all databases) | `all` |
| `--output` | Custom output filename | Auto-generated with timestamp |

## Required Environment Variables

Stored in `~/.claude/mysql.env`:

| Variable | Description |
|----------|-------------|
| `MYSQL_TEST_HOST` | Test server hostname |
| `MYSQL_TEST_PORT` | Test server port |
| `MYSQL_TEST_USER` | Test server username |
| `MYSQL_TEST_PASSWORD` | Test server password |
| `MYSQL_BACKUP_DIR` | Directory to store backups |
| `MYSQL_DUMP_PATH` | Path to mysqldump 8.0 executable |
| `MYSQL_PATH` | Path to mysql 8.0 executable |

**Note:** Uses MySQL 8.0 client (`/opt/homebrew/opt/mysql-client@8.0/bin/`) for compatibility with `mysql_native_password` authentication.

## Instructions for the AI

When this command is invoked:

### 1. Source Environment Variables

```bash
source ~/.claude/mysql.env
```

### 2. Parse Arguments

- **server**: `local` or `test` (default: `test`)
- **db**: Database name or `all` (default: `all`)
- **output**: Custom filename (default: auto-generated)

### 3. Set Server Configuration

**For test (default):**
```bash
HOST="${MYSQL_TEST_HOST}"
PORT="${MYSQL_TEST_PORT}"
USER="${MYSQL_TEST_USER}"
PASS="${MYSQL_TEST_PASSWORD}"
```

**For local:**
```bash
HOST="${MYSQL_LOCAL_HOST}"
PORT="${MYSQL_LOCAL_PORT}"
USER="${MYSQL_LOCAL_USER}"
PASS="${MYSQL_LOCAL_PASSWORD}"
```

### 4. Create Backup Directory and Generate Filename

```bash
mkdir -p "${MYSQL_BACKUP_DIR}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${MYSQL_BACKUP_DIR}/backup_${TIMESTAMP}.sql"
```

### 5. Get List of Databases

```bash
DATABASES=$("${MYSQL_PATH}" -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS" -N -e "SHOW DATABASES" 2>/dev/null | grep -Ev "^(information_schema|mysql|performance_schema|sys)$")
```

### 6. Execute Backup

**For all databases:**
```bash
"${MYSQL_DUMP_PATH}" -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS" \
  --single-transaction \
  --quick \
  --lock-tables=false \
  --set-gtid-purged=OFF \
  --skip-triggers \
  --databases $DATABASES > "$BACKUP_FILE" 2>/dev/null
```

**For specific database:**
```bash
"${MYSQL_DUMP_PATH}" -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS" \
  --single-transaction \
  --quick \
  --lock-tables=false \
  --set-gtid-purged=OFF \
  --skip-triggers \
  "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null
```

### 7. Compress and Show Results

```bash
gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"
ls -lh "$BACKUP_FILE"
```

### 8. Display Summary

```
Backup completed successfully!

Server: <server> (<host>:<port>)
Databases: <count> databases
Output: <filepath>
Size: <filesize>
```

## Examples

```
/mysql:backup                      # Backup all from test
/mysql:backup --db aura_cloud_brand   # Backup specific database
/mysql:backup --server local       # Backup from local
```
