# Cloud API Test Connection Command

Tests the connection to the Cloud API to verify connectivity.

## Usage
```
/cloud-api:test-connection
```

## Required Environment Variables

Stored in `~/.claude/cloud-api.env`:

| Variable | Description |
|----------|-------------|
| `CLOUD_API_URL` | Base URL for Cloud API (e.g., `https://api.test.aurapos.com`) |
| `CLOUD_API_USERNAME` | Username/email for authentication |
| `CLOUD_API_PASSWORD` | Password for authentication |

## Instructions for the AI

When this command is invoked:

### 1. Source Environment Variables

```bash
source ~/.claude/cloud-api.env
```

### 2. Check Environment Variables

Verify that required environment variables are set:

```bash
echo "CLOUD_API_URL: ${CLOUD_API_URL:-(not set)}"
echo "CLOUD_API_USERNAME: ${CLOUD_API_USERNAME:-(not set)}"
echo "CLOUD_API_PASSWORD: ${CLOUD_API_PASSWORD:+(set)}"
```

If any are missing, inform the user and stop.

### 3. Test the Connection

Execute a curl request to the base URL:

```bash
curl -s -k -w "\nHTTP_CODE:%{http_code}" \
  -u "${CLOUD_API_USERNAME}:${CLOUD_API_PASSWORD}" \
  "${CLOUD_API_URL}"
```

Note: `-k` flag is used to allow self-signed certificates (localhost development).

### 4. Interpret Results

- **HTTP 200**: Connection successful
- **HTTP 401/403**: Authentication failed
- **Connection refused**: Server not running or wrong URL

### 5. Display Result

Provide a clear success or failure message with the HTTP status code.
