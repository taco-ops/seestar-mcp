# SeestarS50 MCP Server

[![CI/CD Pipeline](https://github.com/taco-ops/seestar-mcp/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/taco-ops/seestar-mcp/actions/workflows/ci-cd.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.10.6-green.svg)](https://pypi.org/project/fastmcp/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://github.com/taco-ops/seestar-mcp/pkgs/container/seestar-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 🚧 **PUBLIC BETA**: This project is in active development. While all tests pass and core functionality works, we're actively gathering user feedback. Use with caution in production environments and report issues on GitHub.

A Model Context Protocol (MCP) server that enables natural language control of SeestarS50 telescopes through AI assistants like Claude Desktop. Say "point to M31" or "start imaging the Ring Nebula" instead of manually entering coordinates.

## 🌟 What This Does

Control your SeestarS50 telescope using natural language through AI assistants. Instead of manual coordinate entry, simply say:
- "Point to the Andromeda Galaxy"
- "Start imaging the Ring Nebula for 10 minutes"
- "Is Saturn visible right now?"

**How it works:** Your SeestarS50 connects via WiFi in Station mode → This server connects via TCP → Claude (or other AI) sends commands → Server translates to telescope actions → Real-time updates.

**Requirements:** SeestarS50 in Station mode, computer on same network, Docker or Python 3.10+, geographic location for targeting.

## 🚀 Features

### Telescope Control
- **Complete UDP+TCP Protocol**: Full implementation with robust connection handling
- **Natural Language Targets**: Automatic coordinate resolution from target names
- **Smart Visibility**: Geographic location awareness with horizon checking
- **Hardware Control**: Direct focuser and filter wheel control
- **Real-time Status**: Monitor position, imaging progress, and system status

### Advanced Imaging
- **Standard & Mosaic Imaging**: Support for 2x2 mosaics with wider field of view
- **High-Precision Coordinates**: 6-decimal place accuracy for improved targeting
- **Auto-Centering**: Automatic plate solving and precise target acquisition
- **Progress Monitoring**: Real-time imaging status and statistics

### Integration & Development
- **MCP 2024-11-05 Compliant**: Full Model Context Protocol specification support
- **Claude Desktop Ready**: Pre-configured for natural language control
- **Docker Support**: Complete containerization with health checks
- **Type Safety**: Full Pydantic validation and comprehensive testing

## 📦 Quick Start

> **📖 Complete Setup Guide**: For detailed installation instructions, Docker deployment, and Claude Desktop integration, see [Setup Guide](docs/SETUP.md).

### Docker (Recommended)
```bash
# Using pre-built image (no cloning required)
docker run -d --name seestar-mcp \
  -e SEESTAR_HOST=192.168.1.100 \
  -e TELESCOPE_LATITUDE=34.0522 \
  -e TELESCOPE_LONGITUDE=-118.2437 \
  -e TELESCOPE_TIMEZONE=America/Los_Angeles \
  ghcr.io/taco-ops/seestar-mcp:latest

# Or with docker-compose
SEESTAR_HOST=192.168.1.100 docker-compose up -d
```

### Python Development
```bash
git clone https://github.com/taco-ops/seestar-mcp.git
cd seestar-mcp
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uv run seestar-mcp --host 192.168.1.100
```

### Claude Desktop Integration
For complete Claude Desktop setup instructions, see [Setup Guide - Claude Desktop Integration](docs/SETUP.md#claude-desktop-integration).

## 📍 Configure Your Location

**⚠️ Location configuration is essential!** Without it, targets may appear "below horizon" even when visible.

### Find Your Coordinates
- **Google Maps**: Right-click your location → "What's here?" → copy coordinates
- **Phone GPS**: iPhone Compass app or Android GPS apps
- **Cities**: LA: `34.0522,-118.2437`, NYC: `40.7128,-74.0060`, London: `51.5074,-0.1278`

> **📖 Complete location setup**: See [Setup Guide - Configuration](docs/SETUP.md#configuration-reference).

## 🛠️ Available MCP Tools

### Core Operations
- **Connection**: `connect_telescope()`, `disconnect_telescope()`
- **Status**: `get_telescope_status()`, `get_system_info()`
- **Targeting**: `goto_target()`, `search_target()`
- **Imaging**: `start_imaging()`, `start_mosaic_imaging()`, `stop_imaging()`, `get_imaging_status()`
- **Calibration**: `start_calibration()`, `get_calibration_status()`
- **Telescope Control**: `park_telescope()`, `unpark_telescope()`, `open_telescope_arm()`, `close_telescope_arm()`
- **Safety**: `check_solar_safety()`, `emergency_stop()`

### Latest Enhancements
- Complete UDP+TCP protocol with proper handshake
- Solar safety checking for safe sun observations
- Explicit telescope arm control (open/close operations)
- Enhanced calibration status monitoring
- Emergency stop functionality for immediate halt
- Improved error handling and recovery
## 🚨 Known Limitations

**⚠️ Beta Status**: While functional, this software is in public beta. Test thoroughly before critical use.

### Current Limitations
- **Calibration**: Polar alignment must be done through SeestarS50 app
- **Station Mode Required**: Telescope must be in Station mode (not Auto mode)
- **WiFi Dependency**: Requires stable network connection
- **Mosaic Support**: Limited to 2x2 patterns, not extensively tested across all configurations

### What Works Well
✅ Basic telescope control and slewing
✅ Target resolution and coordinate lookup
✅ Standard imaging operations
✅ Real-time status monitoring
✅ Docker deployment and Claude Desktop integration

## 💻 Development

> **📖 Complete Guides**: See [Development Guide](docs/DEVELOPMENT.md), [Contributing Guide](CONTRIBUTING.md), [Pre-commit Guide](docs/PRE_COMMIT_GUIDE.md)

### Quick Setup
```bash
git clone https://github.com/taco-ops/seestar-mcp.git
cd seestar-mcp
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uv run pre-commit install
```

### Testing
```bash
uv run pytest                           # Python tests
npm test                               # JavaScript integration tests
uv run pre-commit run --all-files      # Code quality checks
```

## 🏗️ Architecture

Built on **FastMCP 2.10.6** with complete **UDP+TCP protocol** implementation. Key components:
- **SeestarClient**: TCP communication with connection management
- **TargetResolver**: Multi-catalog coordinate resolution (SIMBAD, NED, Astropy)
- **LocationManager**: Geographic calculations and horizon visibility
- **Pydantic Models**: Type-safe data validation

**Protocol**: UDP initialization (port 4720) → TCP control (port 4700) → JSON-RPC 2.0 messaging
## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and add tests
4. Run tests (`uv run pytest`) and quality checks (`uv run pre-commit run --all-files`)
5. Commit changes and push to branch
6. Open a Pull Request

## 📋 Project Status

**🟢 Production Ready Features:**
- Complete UDP+TCP protocol implementation
- 20+ MCP tools for comprehensive telescope control
- Hardware control (focuser, filter wheel)
- Target resolution and coordinate lookup
- Docker deployment and Claude Desktop integration
- Geographic location and timezone support

**🔴 Known Limitations:**
- Some calibration requires SeestarS50 app
- Mosaic patterns limited to 2x2 maximum
- Performance depends on WiFi stability

**🚧 Under Development:**
- Larger mosaic patterns and custom grids
- Enhanced error recovery
- Weather monitoring integration

## 📚 Documentation & Support

- **Setup & Usage**: [Complete Setup Guide](docs/SETUP.md)
- **Development**: [Development Guide](docs/DEVELOPMENT.md)
- **Code Quality**: [Pre-commit Guide](docs/PRE_COMMIT_GUIDE.md)
- **Issues**: [GitHub Issues](https://github.com/taco-ops/seestar-mcp/issues)
- **Community**: [seestar_alp documentation](https://github.com/smart-underworld/seestar_alp/wiki)

## 📄 License & Acknowledgments

**License**: MIT - see [LICENSE](LICENSE) file

**Acknowledgments**:
- [FastMCP](https://gofastmcp.com/) - MCP framework (v2.10.6)
- [seestar_alp](https://github.com/smart-underworld/seestar_alp) - Protocol reference implementation
- [Model Context Protocol](https://modelcontextprotocol.io/) - Protocol standard
- SeestarS50 telescope community

**Changelog**: See [CHANGELOG.md](CHANGELOG.md) for version history.
