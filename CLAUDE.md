# Working rules
Follow the rules in ai-working-rules.md and ai-checkpoint-protocol.md (both in this .claude directory) for all work in every session.

# Bitbucket PRs

Repos on `bitbucket.org` use an Atlassian API token stored in Windows Credential Manager. Do NOT spend time probing env vars, `gh`, or asking the user — go straight to this recipe.

Auth recipe (PowerShell):

```powershell
$cred = "protocol=https`nhost=bitbucket.org`n`n" | git credential fill 2>$null
$p = (($cred | Select-String '^password=').ToString() -replace '^password=','')
$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("msmit@cosoft.co.za`:$p"))
$headers = @{ Authorization = "Basic $b64" }
```

Key points:
- The password from `git credential fill` is an Atlassian API token (starts with `ATAT...`).
- Basic-auth username MUST be the Atlassian email `msmit@cosoft.co.za`, NOT the Bitbucket username (`michael_smit`). Using the Bitbucket username returns 401.
- Workspace is `cosoft-ondemand`. Get the repo slug from `git remote -v` if not obvious.

Endpoints:
- PR metadata: `GET https://api.bitbucket.org/2.0/repositories/cosoft-ondemand/{repo}/pullrequests/{id}`
- PR diff: `GET .../pullrequests/{id}/diff`
- PR comments: `GET .../pullrequests/{id}/comments`
- PR activity: `GET .../pullrequests/{id}/activity`

# Local services (Docker)

MySQL, Redis, and CouchDB all run locally as Docker containers. Do NOT look for a system-installed `mysql` / `redis-cli` / etc. — they're inside containers. Run commands via `docker exec`. All credentials below are local-dev only.

## MySQL

| Field      | Value                                    |
|------------|------------------------------------------|
| Container  | `MySql`                                 |
| Host:Port  | `localhost:3306`                         |
| Root login | `root` / `P@ssw0rd1`                     |
| App login  | `aura` / `P@ssw0rd1`                     |

Databases on the instance (from `CloudGatewayApi/appsettings.json` `ConnectionStrings`):
`aura_cloud_auth`, `aura_cloud_brand`, `aura_cloud_device`, `aura_cloud_invoicing`, `aura_cloud_lookup`, `aura_cloud_menu`, `aura_cloud_online_ordering`, `aura_cloud_payment`, `aura_cloud_reports`, `aura_cloud_stock`, `syncmanager`.

Run a query:
```bash
docker exec -i MySql mysql -uroot -pP@ssw0rd1 aura_cloud_auth -e "SELECT 1;"
```

For multi-line / parameterised SQL, prefer stdin:
```bash
docker exec -i MySql mysql -uroot -pP@ssw0rd1 aura_cloud_auth <<'SQL'
SELECT COUNT(*) FROM StoreGroup;
SQL
```

## Redis

| Field     | Value           |
|-----------|-----------------|
| Container | `redis`         |
| Host:Port | `localhost:6379`|
| Auth      | none            |

Run a command:
```bash
docker exec -i redis redis-cli PING
docker exec -i redis redis-cli KEYS '*'
```

## CouchDB

| Field     | Value                          |
|-----------|--------------------------------|
| Container | `couchdb-mobile-integration`   |
| Base URL  | `http://localhost:5984`        |
| Auth      | `aura` / `P@ssw0rd1` (basic)   |

HTTP API — no exec needed:
```bash
curl -u aura:P@ssw0rd1 http://localhost:5984/_all_dbs
```

PowerShell:
```powershell
$pair = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('aura:P@ssw0rd1'))
Invoke-RestMethod -Uri 'http://localhost:5984/_all_dbs' -Headers @{ Authorization = "Basic $pair" }
```

Verify with `docker ps` if a container appears down — names above are what's running today.
