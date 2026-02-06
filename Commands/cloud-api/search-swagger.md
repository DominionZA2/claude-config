# Cloud API Search Swagger Command

Searches the Swagger/OpenAPI documentation to find endpoint information, schemas, and API details.

## Usage
```
/cloud-api:search-swagger <query>
```

## Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `query` | Search term (endpoint path, schema name, description text) | Yes |

## Required Environment Variables

Stored in `~/.claude/cloud-api.env`:

| Variable | Description |
|----------|-------------|
| `CLOUD_API_URL` | Base URL for Cloud API |
| `CLOUD_API_SWAGGER_ENDPOINT` | Path to Swagger JSON (e.g., `/swagger/v1/swagger.json`) |

## Instructions for the AI

When this command is invoked:

### 1. Source Environment Variables

```bash
source ~/.claude/cloud-api.env
```

### 2. Parse Arguments

Extract the search query from user input. If no query provided, ask interactively:
- "What would you like to search for in the API documentation?"

### 3. Fetch Swagger Documentation

```bash
curl -s -k "${CLOUD_API_URL}${CLOUD_API_SWAGGER_ENDPOINT}"
```

### 4. Search the Documentation

Parse the Swagger JSON and search for the query in:
- Endpoint paths (e.g., `/companies`, `/auth/login`)
- Operation summaries and descriptions
- Schema/model names
- Parameter names
- Response descriptions

### 5. Display Results

For each match found, display relevant context:

**For endpoint matches:**
```
Endpoint: <METHOD> <path>
Summary: <summary>
Description: <description>
Parameters:
  - <param_name> (<param_type>): <description>
Request Body: <schema reference>
Responses:
  - 200: <description>
  - 400: <description>
```

**For schema matches:**
```
Schema: <schema_name>
Properties:
  - <property_name> (<type>): <description>
```

### 6. No Results

If no matches found:
```
No results found for "<query>" in Swagger documentation.

Suggestions:
- Try a different search term
- Search for partial matches (e.g., "company" instead of "companies")
- Common endpoints: /Auth, /Companies, /Users
```

## Examples

### Search for company endpoints
```
/cloud-api:search-swagger companies
```

### Search for authentication
```
/cloud-api:search-swagger auth
```

### Search for a specific schema
```
/cloud-api:search-swagger CompanyDto
```

### Search for specific functionality
```
/cloud-api:search-swagger login
```

## Tips

- Use partial words to find more matches
- Schema names are typically PascalCase (e.g., `CompanyDto`, `UserResponse`)
- Endpoint paths use lowercase with hyphens or camelCase
