# Release Template

This template is used for creating releases. Copy this content when creating a new release.

## What's Changed

<!-- Describe the changes in this release -->

## 📦 Installation

### Python Package
```bash
pip install seestar-mcp
```

### Docker Image
```bash
docker pull ghcr.io/taco-ops/seestar-mcp:VERSION_TAG
```

## 🐳 Docker Usage

### Quick Start
```bash
# Set your telescope configuration
export SEESTAR_HOST=192.168.1.100
export TELESCOPE_LATITUDE=34.0522
export TELESCOPE_LONGITUDE=-118.2437
export TELESCOPE_TIMEZONE=America/Los_Angeles

# Run the container
docker run -e SEESTAR_HOST -e TELESCOPE_LATITUDE -e TELESCOPE_LONGITUDE -e TELESCOPE_TIMEZONE ghcr.io/taco-ops/seestar-mcp:VERSION_TAG
```

### Using Docker Compose
```bash
# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/taco-ops/seestar-mcp/VERSION_TAG/docker-compose.yml

# Configure and run
SEESTAR_HOST=192.168.1.100 docker-compose up -d
```

## 🔧 Claude Desktop Integration

Add to your Claude Desktop MCP configuration:
```json
{
  "mcpServers": {
    "seestar-mcp": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "SEESTAR_HOST=192.168.1.100",
        "-e", "TELESCOPE_LATITUDE=34.0522",
        "-e", "TELESCOPE_LONGITUDE=-118.2437",
        "-e", "TELESCOPE_TIMEZONE=America/Los_Angeles",
        "ghcr.io/taco-ops/seestar-mcp:VERSION_TAG"
      ]
    }
  }
}
```

## Full Changelog

<!-- Auto-generated changelog will be added here -->
