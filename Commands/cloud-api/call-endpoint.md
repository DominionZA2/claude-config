# Cloud API Call Endpoint Command

Makes HTTP requests to Cloud API endpoints. Supports all HTTP methods and handles authentication automatically.

## Usage
```
/cloud-api:call-endpoint <method> <path> [options]
```

## Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `method` | HTTP method: GET, POST, PUT, DELETE, PATCH | Yes |
| `path` | API path (e.g., `/companies`, `/companies/17`) | Yes |
| `--params` | Query parameters as JSON (e.g., `{"page": 1}`) | No |
| `--body` | Request body as JSON for POST/PUT/PATCH | No |

## Required Environment Variables

Stored in `~/.claude/cloud-api.env`:

| Variable | Description |
|----------|-------------|
| `CLOUD_API_URL` | Base URL for Cloud API |
| `CLOUD_API_USERNAME` | Email for authentication |
| `CLOUD_API_PASSWORD` | Password for authentication |
| `CLOUD_API_TOKEN` | JWT token (set after login) |

## Instructions for the AI

When this command is invoked:

### 1. Source Environment Variables

```bash
source ~/.claude/cloud-api.env
```

### 2. Parse Arguments

Extract from user input:
- **method**: The HTTP method (GET, POST, PUT, DELETE, PATCH)
- **path**: The API endpoint path
- **params**: Optional query parameters (JSON object)
- **body**: Optional request body (JSON object or array)

If method or path is missing, ask the user interactively.

### 3. Build the Request

Construct the full URL:
```bash
URL="${CLOUD_API_URL}/<path>"
```

Add query parameters for GET/DELETE if provided.

### 4. Execute the Request

#### If no token is set, login first:
```bash
# Login to get token
TOKEN=$(curl -s -k -X POST \
  -H "Content-Type: application/json" \
  -d "{\"emailAddress\": \"${CLOUD_API_USERNAME}\", \"password\": \"${CLOUD_API_PASSWORD}\"}" \
  "${CLOUD_API_URL}/Auth/login" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('token') or d.get('accessToken') or d.get('authToken') or '')")
export CLOUD_API_TOKEN="$TOKEN"
```

#### Make the API request:

**GET request:**
```bash
curl -s -k -X GET \
  -H "Authorization: Bearer ${CLOUD_API_TOKEN}" \
  "${CLOUD_API_URL}/<path>?<params>"
```

**POST/PUT/PATCH request:**
```bash
curl -s -k -X <METHOD> \
  -H "Authorization: Bearer ${CLOUD_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '<body>' \
  "${CLOUD_API_URL}/<path>"
```

**DELETE request:**
```bash
curl -s -k -X DELETE \
  -H "Authorization: Bearer ${CLOUD_API_TOKEN}" \
  "${CLOUD_API_URL}/<path>"
```

### 5. Handle 401 Response

If the response is HTTP 401:
1. Attempt to login again to refresh the token
2. Retry the original request with the new token
3. If still failing, report the error

### 6. Display Results

Show the request details and response:

```
API Endpoint: <METHOD> <full_url>
Request Body: <body if provided>

Response (HTTP <status>):
<formatted JSON response>
```

## Examples

### Get all companies
```
/cloud-api:call-endpoint GET /companies
```

### Get a specific company
```
/cloud-api:call-endpoint GET /companies/17
```

### Create a new resource
```
/cloud-api:call-endpoint POST /companies --body {"name": "Test Company", "code": "TEST"}
```

### Update a resource
```
/cloud-api:call-endpoint PUT /companies/17 --body {"name": "Updated Name"}
```

### Delete a resource
```
/cloud-api:call-endpoint DELETE /companies/17
```

### With query parameters
```
/cloud-api:call-endpoint GET /companies --params {"page": 1, "pageSize": 10}
```

## Error Handling

- **401 Unauthorized**: Auto-login and retry
- **403 Forbidden**: User doesn't have permission
- **404 Not Found**: Resource or endpoint doesn't exist
- **400 Bad Request**: Invalid request body or parameters
- **500 Server Error**: Server-side issue
