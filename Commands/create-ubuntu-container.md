---
description: Create an Ubuntu container with SSH access, persistent storage, and auto-restart
---

# Create Ubuntu SSH Container

This command creates a Docker container running Ubuntu with SSH access.

## Instructions

1. First, use `AskUserQuestion` to gather the following information from the user:
   - **Container name**: A unique name for the container (e.g., "dad-ubuntu", "son-ubuntu")
   - **SSH port**: The port to expose for SSH access (e.g., 2222, 2223, 2224)
   - **Username**: The username for SSH login
   - **Password**: The password for SSH login

2. After collecting the information, perform these steps:

### Step 1: Build the Docker image (if needed)

Check if the image exists, if not build it:

```bash
docker images ubuntu-ssh --format "{{.Repository}}" | grep -q ubuntu-ssh || docker build -t ubuntu-ssh ~/.claude/commands/docker-ubuntu-ssh
```

### Step 2: Check if container already exists

If a container with the same name exists, ask the user if they want to remove it first.

### Step 3: Create and start the container

Run the container with:
- `--name <container-name>`: The container name provided by user
- `--restart=always`: Auto-start with Docker/host machine
- `-p <port>:22`: Map SSH port
- `-v <container-name>-home:/home/<username>`: Persistent home directory volume
- `-e SSH_USERNAME=<username>`: Username environment variable
- `-e SSH_PASSWORD=<password>`: Password environment variable

```bash
docker run -d \
  --name <container-name> \
  --restart=always \
  -p <port>:22 \
  -v <container-name>-home:/home/<username> \
  -e SSH_USERNAME=<username> \
  -e SSH_PASSWORD=<password> \
  ubuntu-ssh
```

### Step 4: Create Windows Firewall rule

Create a firewall rule to allow inbound SSH connections on the specified port:

```powershell
New-NetFirewallRule -DisplayName "Docker-SSH-<container-name>" -Direction Inbound -Protocol TCP -LocalPort <port> -Action Allow
```

**Note**: This requires administrator privileges. If not running as admin, inform the user they need to run this command manually in an elevated PowerShell.

### Step 5: Verify and report

1. Verify the container is running: `docker ps --filter name=<container-name>`
2. Get the host machine's IP address for network access
3. Report success with connection instructions:
   - Local: `ssh <username>@localhost -p <port>`
   - Network: `ssh <username>@<host-ip> -p <port>`

## Error Handling

- If the Docker image fails to build, show the build output
- If the container fails to start, show the container logs
- If the firewall rule fails (not admin), provide manual instructions
- If a container with the same name already exists, offer to remove and recreate

## Example Usage

After running `/create-ubuntu-container`:
- Container name: dad-ubuntu
- SSH port: 2222
- Username: dad
- Password: secure123

Results in:
```
Container 'dad-ubuntu' created successfully!

Connect via SSH:
  Local:   ssh dad@localhost -p 2222
  Network: ssh dad@192.168.1.100 -p 2222

The container will auto-start when Docker/your machine restarts.
Home directory data persists in volume: dad-ubuntu-home
```
