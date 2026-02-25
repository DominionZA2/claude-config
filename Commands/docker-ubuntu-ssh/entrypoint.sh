#!/bin/bash
set -e

# Check required environment variables
if [ -z "$SSH_USERNAME" ]; then
    echo "ERROR: SSH_USERNAME environment variable is required"
    exit 1
fi

if [ -z "$SSH_PASSWORD" ]; then
    echo "ERROR: SSH_PASSWORD environment variable is required"
    exit 1
fi

# Create user if it doesn't exist
if ! id "$SSH_USERNAME" &>/dev/null; then
    echo "Creating user: $SSH_USERNAME"
    useradd -m -s /bin/bash "$SSH_USERNAME"
fi

# Set password
echo "$SSH_USERNAME:$SSH_PASSWORD" | chpasswd

# Add user to sudo group
usermod -aG sudo "$SSH_USERNAME"

# Allow sudo without password (optional, can be removed for stricter security)
echo "$SSH_USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$SSH_USERNAME

# Ensure proper permissions on home directory
chown -R "$SSH_USERNAME:$SSH_USERNAME" /home/"$SSH_USERNAME"

echo "SSH server starting for user: $SSH_USERNAME"

# Start SSH daemon in foreground
exec /usr/sbin/sshd -D
