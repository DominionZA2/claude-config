# Cosoft Environment Initialization

```bash
# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    exit 1
fi

echo "Docker found - proceeding with initialization..."
```