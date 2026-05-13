# Stop Services

Stop all running Cloud Backend services.

## Usage
```
/stop-services
```

## Steps

### 1. List and kill running cloud_backend services

```powershell
$existing = Get-CimInstance Win32_Process -Filter "Name='dotnet.exe'" |
    Where-Object { $_.CommandLine -match 'cloud_backend' } |
    ForEach-Object { [pscustomobject]@{ PID = $_.ProcessId; Dll = ($_.CommandLine -replace '.*\\([\w\.]+\.dll).*','$1') } }
$existing | Format-Table -AutoSize
$existing | ForEach-Object { Stop-Process -Id $_.PID -Force }
Start-Sleep -Seconds 2
```

Report in chat:
- If none were running: `No services were running — nothing to stop.`
- If some were: `Stopped N running service(s):` followed by a bulleted list of `<DllName> (PID <pid>)`. Example:
  ```
  Stopped 3 running service(s):
    - CloudGatewayApi.dll (PID 12345)
    - Aura.Microservice.Auth.dll (PID 12346)
    - Aura.Microservice.Brand.dll (PID 12347)
  ```

### 2. Verify

```powershell
$remaining = Get-CimInstance Win32_Process -Filter "Name='dotnet.exe'" |
    Where-Object { $_.CommandLine -match 'cloud_backend' }
```

If any remain, list them and surface that the kill didn't take effect.
