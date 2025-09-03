# Execute Runbook

This command configures Claude to execute Cosoft runbooks with proper tooling and context awareness.

## Instructions

When executing a runbook:

1. **Read the entire runbook first** to understand the scope and requirements
2. **Use available MCP tools** for Grafana log searches and Cloud API calls
3. **Create a todo list** to track runbook steps and progress
4. **Follow security best practices** - never expose credentials or sensitive data
5. **Document any deviations** from the runbook procedures
6. **Verify each step** before proceeding to the next
7. **Use appropriate timeouts** for API calls and log searches

## Available Tools

- `mcp__Cosoft__search_grafana_logs` - Search application logs
- `mcp__Cosoft__call_cloud_api_endpoint` - Make API calls
- `mcp__Cosoft__test_grafana_connection` - Verify log access
- `mcp__Cosoft__test_cloud_api_connection` - Verify API access

## Usage

To execute a runbook:
```
/execute-runbook @mybook.md
```

## Environment Requirements

Ensure these environment variables are configured:
- GRAFANA_LOKI_URL
- GRAFANA_LOKI_USERNAME  
- GRAFANA_LOKI_PASSWORD
- CLOUD_API_URL
- CLOUD_API_USERNAME
- CLOUD_API_PASSWORD
