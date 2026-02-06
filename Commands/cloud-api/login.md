# Cloud API Login Command

Authenticates with the Cloud API and obtains a JWT token for subsequent requests.

## Usage
```
/cloud-api:login
```

## Required Environment Variables

Stored in `~/.claude/cloud-api.env`:

| Variable | Description |
|----------|-------------|
| `CLOUD_API_URL` | Base URL for Cloud API |
| `CLOUD_API_USERNAME` | Email address for authentication |
| `CLOUD_API_PASSWORD` | Password for authentication |

## Instructions for the AI

When this command is invoked:

### 1. Source Environment Variables

```bash
source ~/.claude/cloud-api.env
```

### 2. Check Environment Variables

Verify required variables are set. If missing, inform user and stop.

### 3. Perform Login

Send a POST request to the login endpoint:

```bash
curl -s -k -X POST \
  -H "Content-Type: application/json" \
  -d "{\"emailAddress\": \"${CLOUD_API_USERNAME}\", \"password\": \"${CLOUD_API_PASSWORD}\"}" \
  "${CLOUD_API_URL}/Auth/login"
```

### 4. Extract and Store Token

Parse the JSON response to extract the token. The token may be in one of these fields:
- `token`
- `accessToken`
- `access_token`
- `jwt`
- `authToken`

If a token is found:
1. Display success message
2. Store the token for use in subsequent requests
3. Update the environment: `export CLOUD_API_TOKEN="<token>"`

### 5. Display Result

**On success:**
```
Successfully logged in to Cloud API
Token: <first 20 chars>...
Token stored in CLOUD_API_TOKEN environment variable
```

**On failure:**
```
Login failed: <error message>
```

## Notes

- The token is a JWT and should be included in the `Authorization: Bearer <token>` header for authenticated requests
- The `/cloud-api:call-endpoint` command will automatically attempt login if it receives a 401 response
