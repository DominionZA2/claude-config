# MySQL Query Command

Execute SQL queries against local or test MySQL databases.

## Usage
```
/mysql:query [sql] [options]
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `sql` | SQL query to execute | Required (or interactive) |
| `--server` | Server to use: `local` or `test` | `local` |
| `--db` | Database name to use | `aura_cloud_brand` |
| `--format` | Output format: `table`, `json`, `csv` | `table` |
| `--limit` | Auto-add LIMIT clause if not present | No limit |

## Required Environment Variables

Stored in `~/.claude/mysql.env`:

**Local Server:**
| Variable | Description |
|----------|-------------|
| `MYSQL_LOCAL_HOST` | Host (127.0.0.1) |
| `MYSQL_LOCAL_PORT` | Port (3306) |
| `MYSQL_LOCAL_USER` | Username |
| `MYSQL_LOCAL_PASS` | Password |
| `MYSQL_LOCAL_DB` | Default database |

**Test Server:**
| Variable | Description |
|----------|-------------|
| `MYSQL_TEST_HOST` | Host (clouddb.test.aurapos.com) |
| `MYSQL_TEST_PORT` | Port (3306) |
| `MYSQL_TEST_USER` | Username |
| `MYSQL_TEST_PASS` | Password |
| `MYSQL_TEST_DB` | Default database |

## Instructions for the AI

When this command is invoked:

### 1. Source Environment Variables

```bash
source ~/.claude/mysql.env
```

### 2. Parse Arguments

Extract from user input:
- **sql**: The SQL query to execute
- **server**: `local` or `test` (default: `local`)
- **db**: Database name (default: from env)
- **format**: Output format (default: `table`)

If no SQL is provided, ask the user interactively:
- "What SQL query would you like to run?"

### 3. Select Server Configuration

Based on `--server` flag:

**For local:**
```bash
HOST="${MYSQL_LOCAL_HOST}"
PORT="${MYSQL_LOCAL_PORT}"
USER="${MYSQL_LOCAL_USER}"
PASS="${MYSQL_LOCAL_PASS}"
DB="${MYSQL_LOCAL_DB}"
```

**For test:**
```bash
HOST="${MYSQL_TEST_HOST}"
PORT="${MYSQL_TEST_PORT}"
USER="${MYSQL_TEST_USER}"
PASS="${MYSQL_TEST_PASS}"
DB="${MYSQL_TEST_DB}"
```

### 4. Safety Checks

**IMPORTANT:** Before executing, check for dangerous operations:
- If query contains `DROP`, `DELETE`, `TRUNCATE`, `UPDATE` without WHERE, or `ALTER`:
  - Warn the user and ask for confirmation
  - Never run destructive queries without explicit approval

### 5. Execute the Query

```bash
mysql -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS" "$DB" -e "<sql_query>"
```

**For table format (default):**
```bash
mysql -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS" "$DB" -t -e "<sql_query>"
```

**For JSON format:**
```bash
mysql -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS" "$DB" -e "<sql_query>" | python3 -c "import sys,csv,json; print(json.dumps(list(csv.DictReader(sys.stdin, delimiter='\t')), indent=2))"
```

**For CSV format:**
```bash
mysql -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS" "$DB" -B -e "<sql_query>" | tr '\t' ','
```

### 6. Display Results

Show:
- Server used (local/test)
- Database name
- Query executed
- Results in requested format
- Row count

```
Server: local (127.0.0.1:3306)
Database: aura_cloud_brand
Query: SELECT * FROM companies LIMIT 5

Results (5 rows):
+----+------------+--------+
| id | name       | code   |
+----+------------+--------+
| 1  | Company A  | COMPA  |
| 2  | Company B  | COMPB  |
...
```

### 7. Error Handling

- **Connection refused**: Server not running or wrong host/port
- **Access denied**: Wrong username/password
- **Unknown database**: Database doesn't exist
- **Syntax error**: Invalid SQL

## Examples

### Basic query (local server)
```
/mysql:query SELECT * FROM companies LIMIT 10
```

### Query test server
```
/mysql:query SELECT COUNT(*) FROM users --server test
```

### Use different database
```
/mysql:query SHOW TABLES --db information_schema
```

### JSON output
```
/mysql:query SELECT id, name FROM companies LIMIT 5 --format json
```

### Show all tables
```
/mysql:query SHOW TABLES
```

### Describe a table
```
/mysql:query DESCRIBE companies
```

### Complex query
```
/mysql:query SELECT c.name, COUNT(u.id) as user_count FROM companies c LEFT JOIN users u ON c.id = u.company_id GROUP BY c.id
```

## Quick Reference

| Action | Query |
|--------|-------|
| List tables | `SHOW TABLES` |
| Describe table | `DESCRIBE table_name` |
| Count rows | `SELECT COUNT(*) FROM table_name` |
| Sample data | `SELECT * FROM table_name LIMIT 10` |
| Find columns | `SHOW COLUMNS FROM table_name` |
| Current database | `SELECT DATABASE()` |
| All databases | `SHOW DATABASES` |
