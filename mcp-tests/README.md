# MCP Tests

This directory contains JavaScript integration tests for the SeestarS50 MCP Server.

## Test Files

### Integration Tests
- **`test-working-mcp.js`** - Main working integration test (default `npm test`)
- **`test-simple-mcp.js`** - Simple MCP protocol validation test
- **`test-mcp-integration.js`** - Comprehensive integration test suite

### Jest Test Suite
- **`test-mcp-suite.test.js`** - Jest-based test suite for automated testing

### Debug & Development
- **`debug-test.js`** - Debug utility for development and troubleshooting

## Running Tests

### Individual Tests
```bash
# Main working test
npm run test
# or
npm run test:working

# Simple protocol test
npm run test:simple

# Full integration test
npm run test:integration
```

### Jest Test Suite
```bash
# Run Jest tests
npm run test:mcp
```

### All Tests
```bash
# Run Python tests
npm run test:python

# Run JavaScript tests
npm run test:working
npm run test:simple
```

## Test Requirements

- **Node.js 16+**
- **SeestarS50 telescope** connected to network (for integration tests)
- **MCP Server** running (started automatically by tests)
- **Environment variables** configured (SEESTAR_HOST, etc.)

## Test Results

Current status: **11/11 tests passing (100% success rate)**

These tests validate:
- MCP protocol compliance
- Tool discovery and execution
- Error handling and recovery
- End-to-end telescope integration
- Connection state management

## Development

When adding new tests:
1. Follow the existing pattern in `test-working-mcp.js`
2. Include proper error handling and cleanup
3. Add descriptive test names and documentation
4. Update this README if adding new test categories
