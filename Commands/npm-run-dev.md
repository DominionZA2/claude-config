# NPM Run Dev Command

## Description
The npm-run-dev command kills all existing Node.js processes and starts a fresh development server. This ensures a clean start without port conflicts from lingering processes.

## Usage
```
/npm-run-dev
```

## Behavior
When the `/npm-run-dev` command is executed, the system will:

1. **Check Project Directory**: Verify that package.json exists in the current directory
2. **Kill All Node Processes**: Forcefully terminate any running Node.js processes to prevent port conflicts
3. **Wait for Cleanup**: Pause briefly to ensure all processes are fully terminated
4. **Start Development Server**: Execute `npm run dev` to start the development server
5. **Verify Port**: Ensure the server starts on the expected port (typically 3000)

## Implementation Steps

### 1. Verify Project Directory
```bash
if [ ! -f package.json ]; then
    echo "Error: No package.json found in current directory"
    echo "Please navigate to your Node.js project directory first"
    exit 1
fi
```

### 2. Terminate Node Processes
```powershell
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
```
This PowerShell command finds all Node.js processes and forcefully terminates them.

### 3. Wait for Process Cleanup
Wait approximately 1-2 seconds to ensure all processes are fully terminated and ports are released.

### 4. Start Development Server
```bash
npm run dev
```
Execute the development script defined in the project's package.json file.

## Error Handling
- **No package.json**: Check if package.json exists in the current directory
- **Missing dev script**: Verify that a "dev" script is defined in package.json
- **Port Still in Use**: If the port is still occupied after killing processes:
  - Wait additional time
  - Check for other processes using the port
  - Try alternative kill methods
- **npm not found**: Ensure Node.js and npm are installed and in PATH

## Example Output
```
✓ Killed 3 Node.js processes
✓ Waiting for port cleanup...
✓ Starting development server...

> project-name@1.0.0 dev
> nodemon server.js

[nodemon] starting `node server.js`
Server running on http://localhost:3000
```

## Complete Implementation

Here's the complete sequence of commands to execute:

```bash
# Check for package.json
if not exist package.json (
    echo Error: No package.json found in current directory
    echo Please navigate to your Node.js project directory first
    exit /b 1
)

# Kill all Node processes
powershell -Command "Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force"

# Wait for cleanup
timeout /t 2 /nobreak > nul

# Start the dev server
npm run dev
```

## Notes
- This command is designed for Windows environments using PowerShell
- The default expected port is 3000, but this may vary based on the project configuration
- Always ensure you're in the correct project directory before running this command
- The command assumes `npm run dev` is the correct script for starting the development server
- If the command fails, check that you have a valid Node.js project with a dev script in package.json