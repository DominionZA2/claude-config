# MySQL Describe Table Command

Quick command to show the structure of a table.

## Usage
```
/mysql:describe <table_name> [options]
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `table_name` | Name of the table to describe | Required |
| `--server` | Server to use: `local` or `test` | `local` |
| `--db` | Database name | `aura_cloud_brand` |

## Instructions for the AI

When this command is invoked:

### 1. Source Environment Variables

```bash
source ~/.claude/mysql.env
```

### 2. Parse Arguments

- **table_name**: The table to describe (required)
- **server**: `local` or `test` (default: `local`)
- **db**: Database name (default: from env)

If no table name provided, ask the user.

### 3. Execute Query

```bash
mysql -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS" "$DB" -t -e "DESCRIBE <table_name>"
```

### 4. Display Results

Show the table structure with column names, types, nullability, keys, defaults, and extras.

## Examples

```
/mysql:describe companies
/mysql:describe users --server test
/mysql:describe orders --db other_database
```
