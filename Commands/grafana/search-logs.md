# Grafana Search Logs Command

Search Grafana Loki logs using LogQL queries with flexible time parameters.

## Usage
```
/grafana:search-logs [query] [options]
```

## Arguments

The command accepts the following as arguments (can be provided inline or interactively):

| Argument | Description | Default |
|----------|-------------|---------|
| `query` | LogQL query or search term | Required |
| `--env` | Deployment environment: `test`, `production`, or `none` | `test` |
| `--time` | Time range: `1h`, `3h`, `6h`, `12h`, `1d`, `3d`, `7d`, `14d`, `30d` | `7d` |
| `--limit` | Maximum log entries to return (1-1000) | `100` |
| `--direction` | Search direction: `backward` (newest first) or `forward` | `backward` |
| `--correlation-id` | Shortcut to search for a specific correlation ID | - |

## Required Environment Variables

Stored in `~/.claude/grafana.env`:

| Variable | Description |
|----------|-------------|
| `GRAFANA_LOKI_URL` | Base URL for Grafana Loki (e.g., `https://logs-prod-008.grafana.net`) |
| `GRAFANA_LOKI_USERNAME` | Username for Grafana authentication |
| `GRAFANA_LOKI_PASSWORD` | Password/API token for Grafana authentication |

## Instructions for the AI

When this command is invoked:

### 0. Source Environment Variables

First, source the Grafana environment file to load credentials:

```bash
source ~/.claude/grafana.env
```

### 1. Check Environment Variables

Verify required environment variables are set. If any are missing, inform the user and stop.

### 2. Parse Arguments

Parse the user's input to extract:
- **Query/search term**: The LogQL query or text to search for
- **Options**: Any flags like `--env`, `--time`, `--limit`, etc.

If no query is provided, ask the user interactively:
- "What would you like to search for? (Enter a LogQL query, search term, or correlation ID)"

### 3. Build the LogQL Query

#### If correlation ID is provided:
```
{deployment_environment="<env>"} |= "<correlation_id>"
```

#### If a simple search term is provided (not starting with `{`):
Auto-inject the deployment environment filter:
```
{deployment_environment="<env>"} |= "<search_term>"
```

#### If a full LogQL query is provided (starting with `{`):
- If `deployment_environment` is NOT already in the query AND `--env` is not `none`:
  - Inject `deployment_environment="<env>"` into the label selector
- Otherwise, use the query as-is

### 4. Calculate Time Range

Convert the time range to nanosecond timestamps:
- `end_time`: Current time in nanoseconds
- `start_time`: Current time minus the time range in nanoseconds

Time range conversions:
- `1h` = 3600 seconds
- `3h` = 10800 seconds
- `6h` = 21600 seconds
- `12h` = 43200 seconds
- `1d` = 86400 seconds
- `3d` = 259200 seconds
- `7d` = 604800 seconds
- `14d` = 1209600 seconds
- `30d` = 2592000 seconds

### 5. Execute the Query

Use curl to query the Grafana Loki API:

```bash
# Calculate timestamps
END_TIME=$(date +%s)000000000
START_TIME=$(( ($(date +%s) - <seconds>) ))000000000

# URL encode the query
ENCODED_QUERY=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$LOGQL_QUERY'))")

# Execute query
curl -s \
  -u "${GRAFANA_LOKI_USERNAME}:${GRAFANA_LOKI_PASSWORD}" \
  "${GRAFANA_LOKI_URL}/loki/api/v1/query_range?query=${ENCODED_QUERY}&start=${START_TIME}&end=${END_TIME}&limit=<limit>&direction=<direction>"
```

### 6. Format and Display Results

Parse the JSON response and display results in a readable format:

```
Found <count> log entries

Query: <logql_query>
Time Range: <time_range>
Environment: <env>

--- Entry 1 ---
Time: 2025-01-15 10:30:45 UTC
Message: <log message>

--- Entry 2 ---
Time: 2025-01-15 10:30:44 UTC
Message: <log message>
...
```

If no results found:
```
No log entries found for the given query

Query: <logql_query>
Time Range: <time_range>
Environment: <env>

Suggestions:
- Try a broader time range (e.g., --time 14d)
- Check if the search term is correct
- Try a different environment (--env production)
```

### 7. Error Handling

- **Missing environment variables**: List which are missing and how to set them
- **Invalid time range**: Show valid options
- **API error**: Display the error message and HTTP status code
- **No results**: Suggest ways to broaden the search

## Examples

### Search for errors in test environment (last 7 days)
```
/grafana:search-logs error
```

### Search for a specific correlation ID
```
/grafana:search-logs --correlation-id abc-123-def-456
```

### Search in production with custom time range
```
/grafana:search-logs "payment failed" --env production --time 1d --limit 50
```

### Full LogQL query
```
/grafana:search-logs {service_name="api-gateway"} |= "timeout" |~ "user_id=\\d+"
```

## LogQL Quick Reference

| Pattern | Description |
|---------|-------------|
| `\|= "text"` | Line contains "text" |
| `\|~ "regex"` | Line matches regex |
| `!= "text"` | Line does NOT contain "text" |
| `!~ "regex"` | Line does NOT match regex |
| `\| json` | Parse JSON logs |
| `\| line_format` | Format output |

### Common Label Selectors
- `{deployment_environment="test"}` - Filter by environment
- `{service_name="api"}` - Filter by service
- `{level="error"}` - Filter by log level
