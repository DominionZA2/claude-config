# Grafana Test Connection Command

Tests the connection to Grafana Loki API to verify credentials and connectivity.

## Usage
```
/grafana:test-connection
```

## Required Environment Variables

The following environment variables must be set. They are stored in `~/.claude/grafana.env`:

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

Verify that the required environment variables are set:

```bash
echo "Checking Grafana environment variables..."
echo "GRAFANA_LOKI_URL: ${GRAFANA_LOKI_URL:-(not set)}"
echo "GRAFANA_LOKI_USERNAME: ${GRAFANA_LOKI_USERNAME:-(not set)}"
echo "GRAFANA_LOKI_PASSWORD: ${GRAFANA_LOKI_PASSWORD:+(set)}"
```

If any variables are missing, inform the user and provide instructions on how to set them:
- They can be set in `~/.claude/session-env/` files
- Or exported in the terminal before starting Claude Code
- Or set in a `.env` file in the project

### 2. Test the Connection

Execute a curl request to the Grafana Loki labels endpoint to verify connectivity:

```bash
curl -s -w "\nHTTP_CODE:%{http_code}" \
  -u "${GRAFANA_LOKI_USERNAME}:${GRAFANA_LOKI_PASSWORD}" \
  "${GRAFANA_LOKI_URL}/loki/api/v1/labels"
```

### 3. Interpret Results

- **HTTP 200 with `"status":"success"`**: Connection successful
- **HTTP 401/403**: Authentication failed - check username and password
- **HTTP 404**: URL may be incorrect
- **Connection refused/timeout**: Network issue or incorrect URL

### 4. Display Result

Provide a clear success or failure message:
- On success: "Successfully connected to Grafana Loki API at {URL}"
- On failure: Explain the error and suggest remediation steps

## Example Output

### Success
```
Checking Grafana environment variables...
GRAFANA_LOKI_URL: https://logs-prod-008.grafana.net
GRAFANA_LOKI_USERNAME: 444103
GRAFANA_LOKI_PASSWORD: (set)

Testing connection to Grafana Loki API...

Successfully connected to Grafana Loki API
Available labels: deployment_environment, service_name, level, ...
```

### Failure
```
Checking Grafana environment variables...
GRAFANA_LOKI_URL: https://logs-prod-008.grafana.net
GRAFANA_LOKI_USERNAME: 444103
GRAFANA_LOKI_PASSWORD: (not set)

Error: GRAFANA_LOKI_PASSWORD is not set.
Please set the environment variable before using Grafana commands.
```
