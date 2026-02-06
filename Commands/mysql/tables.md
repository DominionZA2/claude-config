# MySQL Show Tables Command

Quick command to list all tables in a database.

## Usage
```
/mysql:tables [options]
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--server` | Server to use: `local` or `test` | `local` |
| `--db` | Database name | `aura_cloud_brand` |

## Instructions for the AI

When this command is invoked:

### 1. Source Environment Variables

```bash
source ~/.claude/mysql.env
```

### 2. Parse Arguments

- **server**: `local` or `test` (default: `local`)
- **db**: Database name (default: from env)

### 3. Execute Query

```bash
# For local
mysql -h "${MYSQL_LOCAL_HOST}" -P "${MYSQL_LOCAL_PORT}" -u "${MYSQL_LOCAL_USER}" -p"${MYSQL_LOCAL_PASS}" "${DB}" -t -e "SHOW TABLES"

# For test
mysql -h "${MYSQL_TEST_HOST}" -P "${MYSQL_TEST_PORT}" -u "${MYSQL_TEST_USER}" -p"${MYSQL_TEST_PASS}" "${DB}" -t -e "SHOW TABLES"
```

### 4. Display Results

Show the list of tables in a clean format with the server and database info.

## Examples

```
/mysql:tables
/mysql:tables --server test
/mysql:tables --db other_database
```
