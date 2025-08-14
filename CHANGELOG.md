# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Public Beta Status**: Added comprehensive beta warnings and notices across documentation
- **19 MCP Tools**: Complete telescope control suite including:
  - `connect_telescope` / `disconnect_telescope` - Connection management
  - `get_telescope_status` - Real-time status monitoring
  - `goto_target` - Target pointing with astronomical name resolution
  - `start_imaging` / `stop_imaging` / `get_imaging_status` - Imaging control
  - `start_mosaic_imaging` - Multi-panel wide field imaging
  - `start_calibration` / `get_calibration_status` - Telescope calibration
  - `park_telescope` / `unpark_telescope` - Parking controls
  - `open_telescope_arm` / `close_telescope_arm` - Hardware control
  - `check_solar_safety` - Solar collision detection
  - `search_target` - Astronomical catalog search
  - `get_system_info` - System information retrieval
  - `emergency_stop` - Emergency safety function
- **Target Resolution System**: SIMBAD and NED astronomical database integration
- **Location Manager**: Geographic coordinate calculations and horizon visibility
- **Comprehensive Test Suite**: 73 tests with pytest (60 passing, 13 requiring hardware)
- **MCP Integration Tests**: Node.js test suite validating MCP protocol compliance
- **TCP Socket Protocol**: Direct SeestarS50 communication (port 4700)
- **FastMCP 2.10.6 Framework**: Modern MCP server implementation
- **Type Safety**: Full Pydantic V2 models with mypy strict type checking
- **Docker Support**: Multi-stage containerization with health checks
- **GitHub Actions CI/CD**: Automated testing and release pipeline
- **Release Automation**: release-it with conventional changelog generation
- **Code Quality Tools**: Pre-commit hooks (black, isort, flake8, mypy, bandit)
- **UV Package Manager**: Modern Python dependency management

### Changed
- **Development Status**: Updated from Alpha to Beta in package classifiers
- **README**: Replaced "Production Ready" with "Public Beta" notices
- **Server Startup**: Added beta warning banner with issue reporting instructions
- **Package.json**: Fixed missing `release` script for GitHub Actions workflow

### Technical Details
- **Architecture**: FastMCP server ↔ TCP client ↔ SeestarS50 telescope
- **Dependencies**: astropy, pydantic v2, httpx, numpy, pytz, scapy
- **Python Support**: 3.10, 3.11, 3.12
- **Test Coverage**: 49% (targeting 80% for production release)
- **MCP Tools**: 19 tools providing complete telescope control
- **Protocol**: JSON-RPC 2.0 over TCP with `\r\n` message terminators

### Planned for Next Release (0.2.0)
- **Improved Test Coverage**: Target 80%+ test coverage
- **Enhanced Documentation**: More setup guides and troubleshooting
- **Stability Improvements**: Based on community feedback and testing
- **Additional MCP Tools**: Enhanced imaging and calibration features
- **Performance Optimizations**: Faster connection and response times

## [0.1.0] - 2025-08-13

### Added
- **Initial Beta Release**: First public release of SeestarS50 MCP Server
- **Core MCP Framework**: FastMCP 2.10.6 server implementation
- **Telescope Communication**: TCP socket protocol for direct SeestarS50 control
- **Astronomical Integration**: Target resolution via SIMBAD/NED catalogs
- **Essential Telescope Functions**:
  - Connection management and status monitoring
  - Target pointing and goto functionality
  - Basic imaging start/stop controls
  - Parking and unparking operations
  - Emergency safety functions
- **Development Infrastructure**:
  - Python package with UV dependency management
  - Docker containerization support
  - Basic test suite foundation
  - CI/CD pipeline with GitHub Actions
  - Code quality tools and pre-commit hooks

### Notes
- **Beta Software**: This release is intended for testing and feedback
- **Limited Hardware Testing**: Some features require physical telescope for validation
- **Active Development**: Expect frequent updates and improvements
- **Community Feedback Welcome**: Please report issues and suggestions
