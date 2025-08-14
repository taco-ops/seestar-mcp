# SeestarS50 MCP Server - Setup & Usage Guide

This document provides complete setup instructions and usage examples for the SeestarS50 MCP Server.

## Quick Start

### 1. Prerequisites
- **Python 3.10+**
- **SeestarS50 telescope** on local network
- **UV package manager** (recommended) or pip
- **Claude Desktop** or compatible MCP client

### 2. Installation
```bash
# Clone repository
git clone https://github.com/taco-ops/seestar-mcp
cd seestar-mcp

# Install with UV (recommended)
uv sync

# Or install with pip
pip install -e .
```

### 3. Configuration
```bash
# Copy example configuration
cp config.env.example .env

# Edit configuration with your settings
vim .env
```

Required environment variables:
```bash
SEESTAR_HOST=192.168.1.100        # Your telescope's IP address
TELESCOPE_LATITUDE=34.0522        # Observer latitude (decimal degrees)
TELESCOPE_LONGITUDE=-118.2437     # Observer longitude (decimal degrees)
TELESCOPE_TIMEZONE=America/Los_Angeles  # IANA timezone name
```

### 🗺️ Finding Your Coordinates

**Don't know your latitude and longitude?** Here are several easy ways to find them:

#### Method 1: Google Maps (Recommended)
1. Go to [Google Maps](https://maps.google.com)
2. Navigate to your telescope's location (your backyard, observatory, etc.)
3. Right-click on the exact spot
4. Click on the coordinates that appear (e.g., "34.0522, -118.2437")
5. The coordinates will be copied to your clipboard

#### Method 2: Smartphone GPS
- **iPhone**: Open the Compass app, swipe left to see precise coordinates
- **Android**: Download "GPS Coordinates" app or use Google Maps "Share location"

#### Method 3: Online Coordinate Tools
- [LatLong.net](https://www.latlong.net/) - Enter your address to get coordinates
- [GPS-Coordinates.org](https://gps-coordinates.org/) - Multiple lookup methods
- Search "my coordinates" in Google for instant results

#### Method 4: Physical Address Lookup
- Enter your street address in any of the above tools
- Use your city's coordinates as approximation (accurate within a few miles is sufficient)

### 📍 Coordinate Format
- **Latitude**: North is positive (+), South is negative (-)
- **Longitude**: East is positive (+), West is negative (-)
- **Precision**: 4 decimal places is sufficient (e.g., `34.0522`)

### 🌍 Example Coordinates
```bash
# North America
Los Angeles, CA:    34.0522, -118.2437  (America/Los_Angeles)
New York, NY:       40.7128, -74.0060   (America/New_York)
Denver, CO:         39.7392, -104.9903  (America/Denver)
Austin, TX:         30.2672, -97.7431   (America/Chicago)
Bee Cave, TX:       30.3077, -97.9475   (America/Chicago)
Phoenix, AZ:        33.4484, -112.0740  (America/Phoenix)
Toronto, Canada:    43.6532, -79.3832   (America/Toronto)

# Europe
London, UK:         51.5074, -0.1278     (Europe/London)
Paris, France:      48.8566, 2.3522     (Europe/Paris)
Berlin, Germany:    52.5200, 13.4050    (Europe/Berlin)

# Asia/Pacific
Tokyo, Japan:       35.6762, 139.6503   (Asia/Tokyo)
Sydney, Australia: -33.8688, 151.2093   (Australia/Sydney)
Seoul, South Korea: 37.5665, 126.9780   (Asia/Seoul)
```

### 4. Test Connection
```bash
# Test telescope connectivity
uv run seestar-mcp --host 192.168.1.100

# Expected output:
# Starting SeestarS50 MCP Server...
# Server running on port 4700...
```

### 5. Start Server
```bash
# Start MCP server
uv run seestar-mcp

# Or with debug logging
LOG_LEVEL=DEBUG uv run seestar-mcp
```

## Claude Desktop Integration

### 1. Install Claude Desktop
Download from [Anthropic's official site](https://claude.ai/download)

### 2. Configure MCP Server
Edit Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "seestar-mcp": {
      "command": "uv",
      "args": ["run", "seestar-mcp"],
      "cwd": "/path/to/seestar-mcp",
      "env": {
        "SEESTAR_HOST": "192.168.1.100",
        "TELESCOPE_LATITUDE": "34.0522",
        "TELESCOPE_LONGITUDE": "-118.2437",
        "TELESCOPE_TIMEZONE": "America/Los_Angeles"
      }
    }
  }
}
```

### 3. Restart Claude Desktop
Completely quit and restart Claude Desktop to load the MCP server.

### 4. Verify Integration
In Claude Desktop, type: "What telescope tools are available?"

You should see output showing 20+ telescope control tools.

## Docker Deployment

### 1. Quick Start with Docker Compose
```bash
# Set environment variables
export SEESTAR_HOST=192.168.1.100
export TELESCOPE_LATITUDE=34.0522
export TELESCOPE_LONGITUDE=-118.2437
export TELESCOPE_TIMEZONE=America/Los_Angeles

# Start container
docker-compose up -d
```

### 2. Manual Docker Build
```bash
# Build image
docker build -t seestar-mcp .

# Run container
docker run -d \
  --name seestar-mcp-server \
  -e SEESTAR_HOST=192.168.1.100 \
  -e TELESCOPE_LATITUDE=34.0522 \
  -e TELESCOPE_LONGITUDE=-118.2437 \
  -e TELESCOPE_TIMEZONE=America/Los_Angeles \
  seestar-mcp
```

### 3. Claude Desktop with Docker
```json
{
  "mcpServers": {
    "seestar-mcp": {
      "command": "docker",
      "args": ["exec", "seestar-mcp-server", "uv", "run", "seestar-mcp"],
      "env": {
        "SEESTAR_HOST": "192.168.1.100",
        "TELESCOPE_LATITUDE": "34.0522",
        "TELESCOPE_LONGITUDE": "-118.2437",
        "TELESCOPE_TIMEZONE": "America/Los_Angeles"
      }
    }
  }
}
```

## Usage Examples

### Basic Telescope Control

**Get telescope status:**
```
"What's the current telescope status?"
```

**Point to astronomical objects:**
```
"Point the telescope to M31"
"Go to the Ring Nebula"
"Slew to Jupiter"
```

**Start imaging:**
```
"Take a 2-minute exposure of M42"
"Start imaging the Orion Nebula for 5 minutes with 10 frames"
"Capture NGC 7000 with 180-second exposures, 15 frames"
```

### Advanced Operations

**Calibration:**
```
"Start auto focus routine"
"Perform plate solving calibration"
"Begin star calibration process"
```

**System Management:**
```
"Check telescope connectivity"
"Get system information"
"Monitor telescope temperature"
```

**Target Planning:**
```
"What objects are visible tonight?"
"Is M81 above the horizon?"
"When will Saturn be visible?"
```

**Mosaic Imaging:**
```
"Create a 2x2 mosaic of M31 with 3-minute exposures"
"Start mosaic imaging of NGC 7000, 3x3 pattern, 180-second subs"
```

## Available MCP Tools

> **📖 Complete Tools Reference**: For the comprehensive list of 20+ MCP tools with detailed descriptions, see the [Main README - Available MCP Tools](../README.md#-available-mcp-tools) section.

### Tool Categories
- **Connection Management**: Connect, disconnect, configure location
- **Status & Information**: Telescope status, system info, device states
- **Target Operations**: Goto, search, and find astronomical objects
- **Imaging Control**: Standard and mosaic imaging with progress monitoring
- **Hardware Control**: Focuser and filter wheel operations
- **Telescope Operations**: Calibration, parking, emergency stop

## Troubleshooting

### Common Issues

**"Connection refused" or "Timeout"**
```bash
# Check telescope IP address
ping 192.168.1.100

# Verify telescope is in Station mode (not AP mode)
# Check telescope WiFi settings in SeeStar app

# Test direct connection
telnet 192.168.1.100 4700
```

**"Target below horizon"**
```bash
# Verify observer location is correctly set
echo $TELESCOPE_LATITUDE $TELESCOPE_LONGITUDE

# Check timezone configuration
echo $TELESCOPE_TIMEZONE

# Verify current time is accurate
date
```

**"Import errors" or "Module not found"**
```bash
# Reinstall dependencies
uv sync --reinstall

# Or with pip
pip install -e . --force-reinstall
```

**Claude Desktop not showing tools**
```bash
# Check Claude Desktop logs (macOS)
tail -f ~/Library/Logs/Claude/mcp.log

# Verify configuration file syntax
python -m json.tool ~/.config/Claude/claude_desktop_config.json

# Restart Claude Desktop completely
```

### Debug Mode

Enable detailed logging:
```bash
# Environment variable
export LOG_LEVEL=DEBUG

# Or inline
LOG_LEVEL=DEBUG uv run seestar-mcp
```

Debug output shows:
```
SENDING: {"id": 1001, "method": "scope_get_equ_coord"}
RECEIVED: {"result": {"ra": 12.88, "dec": -30.13}, "code": 0}
```

### Network Diagnostics

**Check telescope network mode:**
```bash
# Station mode: Connect to your WiFi network
# AP mode: Telescope creates its own network (10.0.0.99)

# For Station mode (recommended):
nmap -p 4700 192.168.1.0/24  # Find telescope IP
```

**Protocol testing:**
```bash
# Test TCP connection via MCP server
uv run seestar-mcp --host 192.168.1.100

# Monitor network traffic
python discovery/analyze_telescope_traffic.py
```

## Configuration Reference

### Environment Variables

**Required:**
- `SEESTAR_HOST` - Telescope IP address
- `TELESCOPE_LATITUDE` - Observer latitude (decimal degrees)
- `TELESCOPE_LONGITUDE` - Observer longitude (decimal degrees)
- `TELESCOPE_TIMEZONE` - IANA timezone (e.g., "America/New_York")

**Optional:**
- `SEESTAR_PORT` - TCP port (default: 4700)
- `SEESTAR_TIMEOUT` - Connection timeout seconds (default: 30.0)
- `TELESCOPE_ELEVATION` - Elevation in meters (default: 0)
- `LOG_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)

### Example Configurations

**Home Observatory (Fixed Location):**
```bash
SEESTAR_HOST=192.168.1.100
TELESCOPE_LATITUDE=40.7128
TELESCOPE_LONGITUDE=-74.0060
TELESCOPE_TIMEZONE=America/New_York
TELESCOPE_ELEVATION=10
```

**Portable Setup (Variable Location):**
```bash
SEESTAR_HOST=192.168.1.100
# Update coordinates for each observing session
TELESCOPE_LATITUDE=34.0522
TELESCOPE_LONGITUDE=-118.2437
TELESCOPE_TIMEZONE=America/Los_Angeles
```

## Performance & Limits

### Typical Performance
- **Target Resolution**: 1-3 seconds (cached: <100ms)
- **TCP Commands**: <1 second response time
- **Memory Usage**: ~50MB base + 10MB per connection
- **Connection Recovery**: Automatic with exponential backoff

### Operational Limits
- **Exposure Time**: 30-600 seconds per frame
- **Frame Count**: 1-100 frames per sequence
- **Mosaic Size**: Up to 5x5 pattern (25 panels)
- **Concurrent Sessions**: Single client recommended
- **Session Duration**: Tested for 24+ hour operations

### Best Practices
- **Use Station Mode**: More reliable than AP mode
- **Stable Network**: Wired connection preferred for telescope
- **Location Accuracy**: Precise coordinates improve targeting
- **Timezone Correctness**: Critical for visibility calculations
- **Regular Updates**: Keep dependencies current for security

## Getting Help

### Documentation
- **Main README**: Overview and quick start
- **DEVELOPMENT.md**: Technical details and architecture
- **Manual Commands**: Direct telescope protocol reference
- **API Reference**: Complete tool documentation

### Community & Support
- **Issues**: Report bugs or request features on GitHub
- **Discussions**: Community support and usage questions
- **Discord**: Real-time chat with other users
- **Email**: Direct support for urgent issues

### Contributing
- **Bug Reports**: Include reproduction steps and logs
- **Feature Requests**: Describe use case and expected behavior
- **Code Contributions**: Follow development guide standards
- **Documentation**: Help improve guides and examples

---

**Ready to explore the cosmos with AI-powered telescope control!** 🔭✨
