# SeestarS50 MCP Server

[![CI/CD Pipeline](https://github.com/taco-ops/seestar-mcp/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/taco-ops/seestar-mcp/actions/workflows/ci-cd.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.10.6-green.svg)](https://pypi.org/project/fastmcp/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://github.com/taco-ops/seestar-mcp/pkgs/container/seestar-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Coverage](https://codecov.io/gh/taco-ops/seestar-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/taco-ops/seestar-mcp)
[![GitHub release](https://img.shields.io/github/release/taco-ops/seestar-mcp.svg)](https://github.com/taco-ops/seestar-mcp/releases)
[![GitHub release date](https://img.shields.io/github/release-date/taco-ops/seestar-mcp.svg)](https://github.com/taco-ops/seestar-mcp/releases)
[![Changelog](https://img.shields.io/badge/changelog-keep%20a%20changelog-E05735)](CHANGELOG.md)

> 🚧 **PUBLIC BETA**: This project is in active development and public beta testing. While all tests pass and core functionality works, we're still gathering user feedback and making improvements. Use with caution in production environments. Please report any issues on GitHub!

A Model Context Protocol (MCP) server for controlling SeestarS50 telescopes using Python FastMCP and complete UDP+TCP protocol implementation. Designed for both developers and astrophotographers who want to control their telescope through natural language interfaces like Claude Desktop, Warp Terminal, or other MCP-compatible clients.

**⚠️ Beta Notice**: This software is currently in public beta. While extensively tested and functionally complete, we're actively gathering user feedback to improve stability and user experience. Please test thoroughly before relying on it for critical astrophotography sessions.

## 🌟 What This Does

**For Astrophotographers:**
- Control your SeestarS50 telescope using natural language through Claude or other AI assistants
- Say "point to M31" or "start imaging the Eastern Veil Nebula" and it just works
- Automatic target resolution - no need to look up coordinates manually
- Real-time telescope status monitoring and imaging progress tracking
- Timezone-aware horizon checking prevents pointing at objects below the horizon
- Mosaic imaging support for wider field of view captures

**For Developers:**
- Complete MCP server implementation with robust TCP communication
- FastMCP 2.10.6 framework with comprehensive error handling
- Pydantic models for type safety and validation
- Docker containerization for easy deployment
- Extensive logging and debugging capabilities
- Pre-commit hooks and code quality tools


## 🚀 Current Features

### 🌟 New to MCP? Start Here!

**What is this?** This lets you control your SeestarS50 telescope using natural language through AI assistants like Claude. Instead of manually entering coordinates, you can say things like:

- "Point my telescope to the Andromeda Galaxy"
- "Start imaging the Ring Nebula for 10 minutes"
- "Is Saturn visible right now?"
- "Create a mosaic of the Orion Nebula"

**How it works:**
1. Your SeestarS50 connects to WiFi in Station mode
2. This server connects to your telescope via TCP
3. Claude (or other AI) sends commands to the server
4. Server translates commands into telescope actions
5. You get real-time updates on what's happening

**Requirements:**
- SeestarS50 telescope in Station mode
- Computer/server on same WiFi network
- Docker (recommended) or Python 3.10+
- Your geographic location for accurate targeting

### Core Telescope Control
- **Complete UDP+TCP Protocol**: Full implementation with UDP initialization (port 4720) + TCP control (port 4700)
- **Connection Management**: Robust connection handling with TCP keepalive, exponential backoff, and heartbeat monitoring
- **Real-time Status**: Monitor telescope position, imaging progress, and system status
- **Comprehensive Operations**: Full support for slewing, imaging, calibration, parking/unparking
- **Hardware Control**: Direct focuser and filter wheel control with position feedback

### Smart Target Management
- **Natural Language Targets**: Say "M31", "Andromeda Galaxy", "Eastern Veil Nebula" - automatic coordinate resolution
- **Multiple Catalog Support**: SIMBAD, NED, and Astropy coordinate resolution with intelligent fallbacks
- **Geographic Location Awareness**: Configure telescope location for accurate horizon calculations
- **Timezone Support**: Proper local time handling prevents targeting objects below horizon
- **Visibility Checking**: Automatic altitude/azimuth calculations with 10° minimum elevation safety

### Advanced Imaging Features
- **Mosaic Imaging**: Capture wider fields of view with 2x2 mosaic support (up to 2x wider FOV)
- **High-Precision Coordinates**: 6-decimal place coordinate precision for improved targeting accuracy
- **Auto-Centering**: Automatic plate solving and centering for precise target acquisition
- **Progress Monitoring**: Real-time imaging progress and status updates

### Developer & Integration Tools
- **Model Context Protocol**: Full MCP 2024-11-05 specification compliance
- **FastMCP Framework**: Built on FastMCP 2.10.6 with robust error handling
- **Docker Support**: Complete containerization with health checks and persistent connections
- **Comprehensive Logging**: TCP message tracing, operation logging, and debug capabilities
- **Type Safety**: Full Pydantic model validation and type checking
- **Testing Suite**: Comprehensive test coverage with integration and unit tests

### AI Assistant Integration
- **Claude Desktop Ready**: Pre-configured for Claude Desktop with natural language control
- **Warp Terminal Compatible**: Works with Warp's AI command features
- **MCP Client Support**: Compatible with any MCP-compliant client or framework
- **Error Recovery**: Intelligent error handling and user-friendly error messages

## 📦 Installation & Quick Start

> **📖 Complete Setup Guide**: For detailed installation instructions, Docker deployment, and Claude Desktop integration, see our comprehensive [Setup Guide](docs/SETUP.md).

### Quick Start (Docker - Recommended)

**🚀 Using Pre-built Docker Images (Simplest)**
```bash
# Pull and run the latest release - no cloning required!
docker run -d \
  --name seestar-mcp \
  -e SEESTAR_HOST=192.168.1.100 \
  -e TELESCOPE_LATITUDE=34.0522 \
  -e TELESCOPE_LONGITUDE=-118.2437 \
  -e TELESCOPE_TIMEZONE=America/Los_Angeles \
  ghcr.io/taco-ops/seestar-mcp:latest
```

**📦 Using Production Docker Compose**
```bash
# Download just the production compose file
curl -O https://raw.githubusercontent.com/taco-ops/seestar-mcp/main/docker-compose.prod.yml

# Start with your telescope's IP and location
SEESTAR_HOST=192.168.1.100 \
TELESCOPE_LATITUDE=34.0522 \
TELESCOPE_LONGITUDE=-118.2437 \
TELESCOPE_TIMEZONE=America/Los_Angeles \
docker-compose -f docker-compose.prod.yml up -d
```

**🔧 Development Setup (Build Locally)**
```bash
git clone https://github.com/taco-ops/seestar-mcp.git
cd seestar-mcp

# Start with your telescope's IP and location
SEESTAR_HOST=192.168.1.100 \
TELESCOPE_LATITUDE=34.0522 \
TELESCOPE_LONGITUDE=-118.2437 \
TELESCOPE_TIMEZONE=America/Los_Angeles \
docker-compose up -d
```

### Quick Start (Python Development)
```bash
# Requires uv package manager (see Setup Guide for installation)
git clone https://github.com/taco-ops/seestar-mcp.git
cd seestar-mcp
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uv run seestar-mcp --host 192.168.1.100
```

### � Claude Desktop Integration
For complete Claude Desktop setup instructions, including configuration file locations and JSON setup, see the [Setup Guide - Claude Desktop Integration](docs/SETUP.md#claude-desktop-integration) section.

## 🎯 Example Natural Language Commands

### Target Control
- "Point to M31" / "Slew to the Andromeda Galaxy"
- "Go to NGC 6992" / "Find the Eastern Veil Nebula"
- "Is the Ring Nebula above the horizon?"
- "What's the current altitude of Jupiter?"

### Imaging Operations
- "Start imaging for 2 minutes with 30-second exposures"
- "Begin a mosaic capture of the Horse Head Nebula"
- "Stop the current imaging session"
- "What's the progress on my imaging?"

### Status and Information
- "What's my telescope's current position?"
- "Is the telescope connected and ready?"
- "Show me the current imaging status"
- "Park the telescope when done"

## 📍 Critical: Configure Your Location

**⚠️ Location configuration is essential for proper operation!** Without it:
- Targets may appear "below horizon" even when visible
- Timezone calculations will be incorrect
- Coordinate accuracy may be reduced

### 🗺️ How to Find Your Coordinates

**Method 1: Google Maps (Easiest)**
1. Open [Google Maps](https://maps.google.com) in your browser
2. Right-click on your telescope's location
3. Select "What's here?" or click the coordinates that appear
4. Copy the latitude, longitude values (format: `34.0522, -118.2437`)

**Method 2: Your Phone's GPS**
- **iPhone**: Open Compass app, swipe to see coordinates
- **Android**: Use GPS Coordinates app or Google Maps "Share location"

**Method 3: Online Tools**
- [LatLong.net](https://www.latlong.net/) - Enter your address
- [GPS Coordinates](https://gps-coordinates.org/) - Multiple lookup methods

**Method 4: SeestarS50 App**
- Check if your telescope app displays location information
- Some astronomy apps show observer coordinates

### 📍 Quick Examples
```bash
# Major cities for reference:
# Los Angeles: 34.0522, -118.2437 (America/Los_Angeles)
# New York: 40.7128, -74.0060 (America/New_York)
# Austin, TX: 30.2672, -97.7431 (America/Chicago)
# London: 51.5074, -0.1278 (Europe/London)
# Tokyo: 35.6762, 139.6503 (Asia/Tokyo)
# Sydney: -33.8688, 151.2093 (Australia/Sydney)
```

> **📖 Complete Location Setup**: For detailed location configuration, timezone setup, and common locations, see the [Setup Guide - Configuration Reference](docs/SETUP.md#configuration-reference).

## � Release Management

### Creating New Releases

**GitHub Actions Release (Recommended)**

1. **Navigate to GitHub Actions**:
   - Go to your repository: `https://github.com/taco-ops/seestar-mcp`
   - Click "Actions" tab
   - Select "Create Release" workflow

2. **Run Release Workflow**:
   - Click "Run workflow" button
   - Choose version type:
     - `patch` - Bug fixes (1.0.1)
     - `minor` - New features (1.1.0)
     - `major` - Breaking changes (2.0.0)
     - `prerelease` - Alpha/Beta versions
   - Click "Run workflow"

   ```
   GitHub Actions → Create Release → Run workflow
   ┌─────────────────────────────────────────┐
   │ Use workflow from: Branch: main    ▼    │
   │ Type of version increment: minor   ▼    │
   │ [ Run workflow ]                        │
   └─────────────────────────────────────────┘
   ```

3. **Automatic Process**:
   - ✅ Runs all tests (Python + MCP integration)
   - ✅ Updates version and generates changelog
   - ✅ Creates GitHub release with notes
   - ✅ Publishes Docker image: `ghcr.io/taco-ops/seestar-mcp:latest`
   - ✅ Publishes to PyPI (if configured)

**No local setup required!** 🎉

> **📖 Complete Release Guide**: For detailed release instructions, troubleshooting, and repository setup, see the [Release Guide](docs/RELEASE_GUIDE.md).

### Available Docker Images (After Release)

Each release automatically creates Docker images with multiple tags:

```bash
# Latest release
docker pull ghcr.io/taco-ops/seestar-mcp:latest

# Specific version
docker pull ghcr.io/taco-ops/seestar-mcp:v1.2.3

# Major version (always latest 1.x.x)
docker pull ghcr.io/taco-ops/seestar-mcp:1

# Minor version (always latest 1.2.x)
docker pull ghcr.io/taco-ops/seestar-mcp:1.2
```

## �🔍 Monitoring & Troubleshooting

> **📖 Complete Troubleshooting Guide**: For detailed troubleshooting, network diagnostics, and debugging procedures, see the [Setup Guide - Troubleshooting](docs/SETUP.md#troubleshooting).

### Quick Debug Commands
```bash
# Enable debug logging
LOG_LEVEL=DEBUG docker-compose up

# Monitor telescope communication
docker-compose logs -f seestar-mcp

# Test connection safely (no telescope movement)
python discovery/test_timezone_accuracy.py
```

### Common Issues
- **"Connection refused"**: Check telescope IP and Station mode
- **"Target below horizon"**: Verify location configuration
- **"Module not found"**: Reinstall with `uv sync --reinstall`

## 👨‍💻 For Maintainers

### Creating Your First Release

Ready to publish? Here's how to create the first release:

1. **Go to GitHub Actions**: Visit `https://github.com/taco-ops/seestar-mcp/actions`
2. **Find "Create Release"**: Click on the "Create Release" workflow
3. **Run Workflow**:
   - Click "Run workflow"
   - Select `minor` for your first release (will create v0.1.0)
   - Click "Run workflow"
4. **Wait for Completion**: The workflow will run tests and create the release
5. **Docker Images Available**: After ~5 minutes, users can pull `ghcr.io/taco-ops/seestar-mcp:latest`

### Repository Secrets Setup

For full automation, add these repository secrets:
- `PYPI_TOKEN`: For publishing to PyPI (optional)
- `GITHUB_TOKEN`: Already available by default for Docker publishing

## Usage

## 🛠️ Available MCP Tools

### Connection Management
- **`connect_telescope(host, port, timeout)`** - Connect to telescope with automatic location integration
- **`disconnect_telescope()`** - Safely disconnect from telescope
- **`configure_telescope_location(lat, lon, elevation, timezone)`** - Set geographic location for accurate calculations

### Status and Information
- **`get_telescope_status()`** - Current position, connection state, and operational status
- **`get_system_info()`** - Server status, uptime, and system information

### Enhanced Device Information (New!)
- **`get_device_state()`** - Comprehensive device state and hardware information
- **`get_station_state()`** - Network connection and WiFi station status
- **`get_view_state()`** - Current telescope view and imaging state
- **`get_stack_settings()`** - Image stacking configuration and parameters

### Target Operations
- **`goto_target(target_name)`** - Slew to named target with automatic coordinate resolution and visibility checking
- **`search_target(target_name)`** - Look up target coordinates without moving telescope
- **`find_target(target_name)`** - Resolve target and execute goto with progress monitoring

### Imaging Control
- **`start_imaging(exposure_time, count, target_name)`** - Begin standard imaging session
- **`start_mosaic_imaging(target_name, exposure_time, count, width, height)`** - Capture mosaic images (2x wider FOV)
- **`stop_imaging()`** - Stop current imaging session
- **`get_imaging_status()`** - Real-time imaging progress and statistics

### Hardware Control (New!)
- **`control_focuser(position)`** - Set focuser to specific position (0-65000)
- **`get_focuser_position()`** - Get current focuser position
- **`control_filter_wheel(position)`** - Set filter wheel position (1-10)
- **`get_wheel_state()`** - Get filter wheel state and current position

### Telescope Operations
- **`start_calibration()`** - Begin telescope calibration sequence (⚠️ *Note: Some calibration must be done via SeestarS50 app*)
- **`park_telescope()`** - Park telescope in safe position
- **`unpark_telescope()`** - Unpark telescope for operations
- **`emergency_stop()`** - Immediately halt all telescope operations

### Enhanced Features (Latest Release)
- **Complete UDP+TCP Protocol** - Proper UDP initialization on port 4720 before TCP control on port 4700
- **Enhanced coordinate precision** - 6-decimal place accuracy for improved targeting
- **Hardware control** - Direct focuser and filter wheel control
- **Comprehensive device monitoring** - Real-time status of all telescope subsystems
- **Visibility checking** - Automatic horizon calculations prevent below-horizon targets
- **Timezone awareness** - Proper local time handling for accurate object visibility
- **Mosaic imaging** - Support for 1x1 to 2x2 mosaics with automatic parameter handling
- **Connection stability** - TCP keepalive, heartbeat monitoring, and exponential backoff reconnection

## 🚨 Current Limitations & Known Issues

### SeestarS50 Firmware Limitations
- **Calibration Restriction**: Polar alignment and some advanced calibrations must be done through the official SeestarS50 app
- **Station Mode Required**: Telescope must be in Station mode for TCP communication (not Auto mode)
- **WiFi Dependency**: Requires stable WiFi connection between telescope and computer running MCP server

### Current Development Status
- **Mosaic Support**: Implemented but not extensively tested with all telescope configurations
- **Coordinate Accuracy**: Recent improvements added but may need fine-tuning based on user feedback
- **Error Recovery**: Robust but some edge cases may require manual reconnection
- **Performance**: TCP communication is fast but some operations (like plate solving) can take 30-60 seconds

### Planned Improvements
- **Enhanced Mosaic Patterns**: Support for larger mosaic grids and custom patterns
- **Guiding Integration**: Support for autoguiding during long exposures
- **Weather Integration**: API hooks for weather monitoring and safety shutdowns
- **Focus Control**: Automated focusing routines and focus position management
- **Filter Wheel Support**: Control for telescopes with automated filter wheels

### What Works Well
- ✅ Basic telescope control and slewing
- ✅ Target name resolution and coordinate lookup
- ✅ Standard imaging operations
- ✅ Real-time status monitoring
- ✅ Docker deployment and containerization
- ✅ Claude Desktop integration
- ✅ Connection stability and error recovery

### Example Usage with MCP Client

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    # Connect to the MCP server
    server_params = StdioServerParameters(
        command="seestar-mcp", args=["--host", "192.168.1.100"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()

            # Connect to telescope
            result = await session.call_tool(
                "connect_telescope", {"host": "192.168.1.100", "port": 4700}
            )

            # Goto target
            result = await session.call_tool("goto_target", {"target_name": "M31"})

            # Start imaging
            result = await session.call_tool(
                "start_imaging", {"exposure_time": 120, "count": 10}
            )


if __name__ == "__main__":
    asyncio.run(main())
```

## ⚙️ Configuration

> **📖 Complete Configuration Reference**: For detailed environment variables, command line options, and integration guides, see the [Setup Guide - Configuration Reference](docs/SETUP.md#configuration-reference).

## 🐳 Docker Usage

> **📖 Complete Docker Guide**: For detailed Docker deployment, configuration options, and troubleshooting, see the [Docker Migration Guide](docs/DOCKER_MIGRATION.md).

### Quick Docker Commands

```bash
# Start with Docker Compose (recommended)
SEESTAR_HOST=192.168.1.100 docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Manual Docker build
docker build -t seestar-mcp .
docker run -e SEESTAR_HOST=192.168.1.100 seestar-mcp
```

## 💻 Development

> **📖 Development Guide**: For comprehensive development information, testing procedures, and contribution guidelines, see:
> - [Development Guide](docs/DEVELOPMENT.md) - Technical architecture and development phases
> - [Contributing Guide](CONTRIBUTING.md) - Code standards and workflow
> - [Pre-commit Guide](docs/PRE_COMMIT_GUIDE.md) - Code quality tools and manual commands

### Quick Development Setup
```bash
git clone https://github.com/taco-ops/seestar-mcp.git
cd seestar-mcp
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uv run pre-commit install
```

### Testing
```bash
uv run pytest                    # Python tests
npm test                         # JavaScript integration tests
uv run pre-commit run --all-files  # Code quality checks
```

## 🏗️ Architecture & Technical Details

### Core Components

**🧠 SeestarClient** (`telescope_client.py`)
- **Complete UDP+TCP protocol implementation** with UDP initialization on port 4720
- TCP socket communication with SeestarS50 on port 4700 (after UDP initialization)
- Connection management with TCP keepalive and heartbeat monitoring
- Automatic reconnection with exponential backoff
- Enhanced coordinate precision (6 decimal places) and auto-centering
- Integration with location manager for visibility checking
- **Hardware control support** for focuser and filter wheel operations

**🎯 TargetResolver** (`target_resolver.py`)
- Multi-catalog target resolution (SIMBAD, NED, Astropy)
- Intelligent fallback and alternative suggestions
- Geographic location awareness for visibility calculations
- Timezone-aware horizon checking with 10° minimum elevation
- Comprehensive target caching and performance optimization

**📍 LocationManager** (`location_manager.py`)
- Geographic location and timezone management
- Astropy EarthLocation integration for accurate calculations
- Local time conversion and timezone handling
- Horizon visibility calculations and altitude/azimuth tracking

**🚀 FastMCP Server** (`server.py`)
- FastMCP 2.10.6 framework with full MCP 2024-11-05 compliance
- Comprehensive tool suite with progress monitoring
- Robust error handling and user-friendly error messages
- Integration between all components with shared state management

**📊 Pydantic Models** (`models.py`)
- Type-safe data structures with comprehensive validation
- Response models for all operations with detailed status information
- Configuration models with environment variable integration
- Enhanced imaging parameters including mosaic support

### Communication Protocol

**Transport Layer:**
- **UDP initialization on port 4720** (required before TCP connection)
- **TCP control socket on port 4700** (after successful UDP initialization)
- Persistent connections with automatic reconnection
- TCP keepalive for connection health monitoring
- Message-based communication with JSON-RPC 2.0 protocol
- **Complete SeestarS50 protocol compliance** based on seestar_alp analysis

**Message Format:**
```json
// Outgoing commands
{"id": 1001, "method": "scope_get_equ_coord"}

// Incoming responses
{
  "jsonrpc": "2.0",
  "result": {"ra": 12.863333, "dec": -30.129167},
  "code": 0,
  "id": 1001
}

// Event notifications
{
  "Event": "AutoGoto",
  "state": "complete",
  "result": {"success": true}
}
```

**Enhanced Features:**
- High-precision coordinate handling (6 decimal places)
- Automatic plate solving integration (`auto_center: true`)
- Extended timeouts for accurate operations (120 seconds)
- Comprehensive error detection and recovery
- Real-time progress monitoring and status updates

### Supported SeestarS50 Operations

| Operation | MCP Tool | TCP Methods | Status |
|-----------|----------|-------------|---------|
| Connection | `connect_telescope` | `test_connection` | ✅ Stable |
| Status | `get_telescope_status` | `scope_get_equ_coord` | ✅ Stable |
| Slewing | `goto_target` | `iscope_start_view` | ✅ Enhanced |
| Imaging | `start_imaging` | `iscope_start_view` | ✅ Stable |
| Mosaic | `start_mosaic_imaging` | `iscope_start_view` + mosaic params | 🧪 Beta |
| Calibration | `start_calibration` | Various calibration methods | ⚠️ Limited |
| Park/Unpark | `park_telescope` | `scope_park`/`scope_unpark` | ✅ Stable |

### Development Architecture

**Code Quality:**
- Pre-commit hooks (Black, isort, flake8, bandit, mypy)
- Comprehensive test suite with pytest
- Type safety with Pydantic and mypy
- Automated CI/CD with GitHub Actions

**Containerization:**
- Multi-stage Docker builds with Python 3.11
- Health checks and graceful shutdown handling
- Development and production configurations
- Non-root user for security

**Monitoring & Observability:**
- Structured logging with configurable levels
- TCP message tracing for debugging
- Performance metrics and operation timing
- Error tracking and recovery monitoring

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass (`pytest`)
6. Format your code (`black src tests`)
7. Lint your code (`flake8 src tests`)
8. Commit your changes (`git commit -m 'Add amazing feature'`)
9. Push to the branch (`git push origin feature/amazing-feature`)
10. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [FastMCP](https://gofastmcp.com/) - The MCP framework (v2.10.6) used for this server
- [seestar_alp](https://github.com/smart-underworld/seestar_alp) - Reference implementation for SeestarS50 TCP communication protocol
- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol standard
- SeestarS50 telescope community for protocol documentation and testing

## Support

- **Setup & Usage**: See [Complete Setup Guide](docs/SETUP.md)
- **Development**: See [Development Guide](docs/DEVELOPMENT.md)
- **Code Quality**: See [Pre-commit Guide](docs/PRE_COMMIT_GUIDE.md)
- Open an issue on [GitHub](https://github.com/taco-ops/seestar-mcp/issues)
- Check the [seestar_alp documentation](https://github.com/smart-underworld/seestar_alp/wiki)
- Join the SeestarS50 community discussions

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.

---

## 📋 Project Status Summary

**🟢 Production Ready - Complete Implementation:**
- **Complete UDP+TCP protocol** with proper handshake sequence
- **20+ MCP tools** for comprehensive telescope control
- **Hardware control** for focuser and filter wheel
- **Enhanced device monitoring** with state information
- **Target name resolution** and coordinate lookup
- **Advanced imaging operations** with mosaic support
- **Docker deployment** and containerization
- **Claude Desktop integration** with natural language control
- **Geographic location** and timezone support
- **Enhanced coordinate precision** (6 decimal places) and auto-centering
- **Robust connection management** with automatic recovery

**✅ Fully Implemented Features:**
- UDP initialization protocol (port 4720) + TCP control (port 4700)
- Complete SeestarS50 protocol compatibility based on seestar_alp analysis
- Hardware control: focuser positioning and filter wheel control
- Advanced status monitoring: device state, station state, view state
- Enhanced error handling with SeestarConnectionError exceptions
- Repository cleanup and documentation updates

**🔴 Known Limitations:**
- Some calibration operations require SeestarS50 app
- Filter wheel positions depend on telescope configuration
- Mosaic patterns limited to 2x2 maximum
- Performance depends on WiFi stability
- Limited testing across all telescope configurations

**🚧 Under Development:**
- Larger mosaic patterns and custom grids
- Enhanced error recovery and user guidance
- Performance optimizations for imaging workflows
- Integration with weather monitoring systems

**🎯 Perfect For:**
- Astrophotographers who want natural language telescope control
- Developers building astronomy automation tools
- Users of Claude Desktop, Warp Terminal, or other MCP clients
- Anyone wanting to integrate telescope control into AI workflows

**❓ Questions or Issues?**
- Open an issue on [GitHub](https://github.com/taco-ops/seestar-mcp/issues)
- Check existing discussions and documentation
- Test with the safe `discovery/test_timezone_accuracy.py` script first

> Remember: This is a rapidly evolving project. Always test new features carefully and keep your SeestarS50 app handy for calibration operations!
