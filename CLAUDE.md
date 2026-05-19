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
