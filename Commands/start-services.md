# Start Services

Start the full Cloud Backend service set. Run from the `cloud_backend` repo root.

## Arguments

- `--monitor` (alias `-m`): after the services are up, start a Monitor on the gateway log and surface any errors that appear during testing. Without this flag the services just run in the background and no log watching is done.

Report which mode you're running in at the start. Either:
- `Starting services (no log monitoring).`
- `Starting services with gateway log monitoring enabled.`

## Steps

### 1. Kill any running services

List existing cloud_backend processes first, then kill them.

```powershell
$existing = Get-CimInstance Win32_Process -Filter "Name='dotnet.exe'" |
    Where-Object { $_.CommandLine -match 'cloud_backend' } |
    ForEach-Object { [pscustomobject]@{ PID = $_.ProcessId; Dll = ($_.CommandLine -replace '.*\\([\w\.]+\.dll).*','$1') } }
$existing | Format-Table -AutoSize
$existing | ForEach-Object { Stop-Process -Id $_.PID -Force }
Start-Sleep -Seconds 2
```

Then report in chat:
- If none were running: `No services were running — nothing to kill.`
- If some were: `Killed N running service(s):` followed by a bulleted list of `<DllName> (PID <pid>)`. Example:
  ```
  Killed 3 running service(s):
    - CloudGatewayApi.dll (PID 12345)
    - Aura.Microservice.Auth.dll (PID 12346)
    - Aura.Microservice.Brand.dll (PID 12347)
  ```

### 2. Build

```powershell
dotnet build AuraServices.sln -nr:false /property:GenerateFullPaths=true '/consoleloggerparameters:NoSummary;ForceNoAlign'
```

Report: `Building AuraServices.sln…` before, then `Build succeeded (N warnings)` or `Build failed — last 30 lines:` followed by the tail. If failed, stop.

### 3. Resolve repo root and discover which services exist

**Repo root is the current working directory** — not a hardcoded path. Branches may live in worktrees (e.g. `C:\Source\cloud-worktrees\<branch>\cloud_backend`), and the `Build` step ran against `AuraServices.sln` in the cwd, so the freshly built binaries are under the cwd. Use the cwd as the base for every project path below.

Before launching, **probe each project's built dll**. Branches can remove or rename microservices (the Auth project, for example, has been removed in some feature branches), so the candidate list below is not authoritative — the filesystem is. For each row, check `Test-Path '<cwd>\<Project>\bin\Debug\net8.0\<Dll>'`. Build the actual launch set from rows where the dll exists.

Candidate services:

| Project                               | Dll                                       | Port |
|---------------------------------------|-------------------------------------------|------|
| CloudGatewayApi                       | CloudGatewayApi.dll                       | 5000 |
| Aura.Microservice.Auth                | Aura.Microservice.Auth.dll                | 5002 |
| Aura.Microservice.Brand               | Aura.Microservice.Brand.dll               | 5003 |
| Aura.Microservice.ExternalIntegration | Aura.Microservice.ExternalIntegration.dll | 5011 |
| Aura.Microservice.Invoicing           | Aura.Microservice.Invoicing.dll           | 5010 |
| Aura.Microservice.Lookup              | Aura.Microservice.Lookup.dll              | 5004 |
| Aura.Microservice.Menu                | Aura.Microservice.Menu.dll                | 5006 |
| Aura.Microservice.OnlineOrdering      | Aura.Microservice.OnlineOrdering.dll      | 5007 |
| Aura.Microservice.Payment             | Aura.Microservice.Payment.dll             | 5008 |

Report which services were found and which were skipped, e.g.:
```
Found 8 services to launch. Skipping: Aura.Microservice.Auth (dll not present — likely removed in this branch).
```

The Gateway binds HTTPS on 5000 (HTTP fallback on 5001 also listens). All other services are HTTP.

### 4. Launch the discovered services

Report: `Launching N services in parallel…` (use the actual count from step 3), then launch each as a separate background PowerShell call (`run_in_background: true`). Run all in parallel.

For each row in the launch set, the command is:

```powershell
$env:ASPNETCORE_ENVIRONMENT = 'Development'
Set-Location '<cwd>\<Project>'
dotnet '<cwd>\<Project>\bin\Debug\net8.0\<Dll>'
```

### 5. Wait for ports to bind (up to 60s)

Report: `Waiting for ports to bind…`

Build `$expected` from the **launch set decided in step 3** (not the full 9), so a missing project doesn't make the wait time out forever.

```powershell
$expected = <ports of the services you actually launched>
$deadline = (Get-Date).AddSeconds(60)
while ((Get-Date) -lt $deadline) {
    $listening = (Get-NetTCPConnection -State Listen | Where-Object { $expected -contains $_.LocalPort }).LocalPort | Sort-Object -Unique
    if ($listening.Count -eq $expected.Count) { break }
    Start-Sleep -Seconds 2
}
```

If any background task reports `failed` before all ports bind, read its output file, surface the error, and stop. Name the service that died.

If the 60s deadline hits with ports still missing, list the missing ports/services explicitly — don't just say "timeout".

### 6. Print the summary

Sort by service name. Log file path is `%TEMP%\aura-<DllWithoutExtension><yyyyMMdd>.log`.

```
| Service                               | Port | Log file                                                                  |
|---------------------------------------|------|---------------------------------------------------------------------------|
| Aura.Microservice.Auth                | 5002 | C:\Users\msmit\AppData\Local\Temp\aura-Aura.Microservice.Auth<yyyyMMdd>.log |
| ...                                                                                                                          |
```

Then list the background-task IDs so logs can be tailed via the task output captures if the Serilog file is locked.

### 7. Start gateway log monitoring (only if `--monitor` was passed)

Skip this entire step if the flag wasn't passed.

Use the Monitor tool to tail the gateway Serilog file with a filter for error-level entries. Each matching line becomes a single notification, so context only grows when something actually goes wrong.

- **Target file**: `C:\Users\msmit\AppData\Local\Temp\aura-CloudGatewayApi<yyyyMMdd>.log` (compute today's date in `yyyyMMdd` for the suffix; this is also the gateway row from the summary table).
- **Filter regex**: `\[(ERR|FTL)\]|Unhandled exception`
  - Catches Serilog `[ERR]` and `[FTL]` level tokens plus any bare unhandled-exception lines.
  - Does **not** match stack-trace `at ...` lines on purpose — when a notification fires you can Read the log file around that timestamp to grab the surrounding stack.

After starting Monitor, report a single line: `Watching gateway log for errors — I'll surface anything that matches [ERR]/[FTL] or "Unhandled exception".`

When a notification arrives later in the session:
- Read the gateway log file around the matching line to capture the surrounding stack/context.
- Summarise the error in chat (file:line of the throwing code if identifiable, what triggered it, severity).
- Don't try to fix anything proactively — just surface it. The user will direct any follow-up.

Notes for the assistant:
- One Monitor on the gateway log is enough — errors from downstream microservices propagate through the gateway. Don't spin up Monitors on the other 8 services unless the user asks.
- The filename has today's date baked in. If services are still running past midnight Serilog rolls to a new file and the old Monitor goes silent; mention this if the user keeps services up across a day boundary.
