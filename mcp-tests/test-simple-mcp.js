#!/usr/bin/env node

/**
 * Simple MCP Test Client for SeestarS50 MCP Server
 *
 * This test directly communicates with the MCP server via stdio
 * to test all the tools and functionality.
 */

import { spawn } from 'child_process';
import { createInterface } from 'readline';

class SimpleMCPTester {
    constructor() {
        this.serverProcess = null;
        this.testResults = [];
        this.nextId = 1;
    }

    async startServer() {
        console.log('🚀 Starting SeestarS50 MCP Server...');

        this.serverProcess = spawn('uv', ['run', 'python', '-m', 'seestar_mcp.server'], {
            stdio: ['pipe', 'pipe', 'pipe'],
            env: { ...process.env }
        });

        // Debug: Log server stderr
        this.serverProcess.stderr.on('data', (data) => {
            console.debug(`Server stderr: ${data.toString()}`);
        });

        // Wait for server to start and show banner
        await new Promise(resolve => setTimeout(resolve, 3000));

        if (this.serverProcess && !this.serverProcess.killed) {
            console.log('✅ MCP Server started successfully');
            return true;
        } else {
            console.error('❌ Failed to start MCP Server');
            return false;
        }
    }

    async stopServer() {
        if (this.serverProcess && !this.serverProcess.killed) {
            console.log('🛑 Stopping MCP Server...');
            this.serverProcess.kill('SIGTERM');
            await new Promise(resolve => setTimeout(resolve, 1000));
            console.log('✅ MCP Server stopped');
        }
    }

    async sendRequest(method, params = {}) {
        return new Promise((resolve, reject) => {
            const request = {
                jsonrpc: "2.0",
                id: this.nextId++,
                method: method,
                params: params
            };

            let responseBuffer = '';
            let resolved = false;

            const timeout = setTimeout(() => {
                if (!resolved) {
                    resolved = true;
                    reject(new Error(`Timeout waiting for response to ${method}`));
                }
            }, 15000);

            const onData = (data) => {
                responseBuffer += data.toString();

                // Try to parse complete JSON responses (one per line)
                const lines = responseBuffer.split('\n');
                responseBuffer = lines.pop() || ''; // Keep the incomplete line in buffer

                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const parsed = JSON.parse(line.trim());
                            if (parsed.id === request.id && !resolved) {
                                resolved = true;
                                clearTimeout(timeout);
                                this.serverProcess.stdout.off('data', onData);
                                resolve(parsed);
                                return;
                            }
                        } catch (e) {
                            // Ignore parse errors for non-matching responses
                            console.debug(`Parse error for line: ${line.trim()}`);
                        }
                    }
                }
            };

            this.serverProcess.stdout.on('data', onData);

            this.serverProcess.on('error', (error) => {
                if (!resolved) {
                    resolved = true;
                    clearTimeout(timeout);
                    reject(new Error(`Server process error: ${error.message}`));
                }
            });

            // Send the request
            const requestStr = JSON.stringify(request) + '\n';
            console.debug(`Sending: ${requestStr.trim()}`);
            this.serverProcess.stdin.write(requestStr);
        });
    }

    async runTest(testName, testFn) {
        console.log(`\n🧪 Running test: ${testName}`);

        try {
            const result = await testFn();
            this.testResults.push({ name: testName, status: 'PASS', result });
            console.log(`✅ ${testName}: PASSED`);
            return result;
        } catch (error) {
            this.testResults.push({ name: testName, status: 'FAIL', error: error.message });
            console.error(`❌ ${testName}: FAILED - ${error.message}`);
            throw error;
        }
    }

    async testInitialization() {
        return this.runTest('Server Initialization', async () => {
            const response = await this.sendRequest('initialize', {
                protocolVersion: "2024-11-05",
                capabilities: {},
                clientInfo: {
                    name: "test-client",
                    version: "1.0.0"
                }
            });

            if (response.error) {
                throw new Error(`Initialization failed: ${response.error.message}`);
            }

            // Send the initialized notification (required by MCP protocol)
            const notificationRequest = {
                jsonrpc: "2.0",
                method: "notifications/initialized"
            };

            const notificationStr = JSON.stringify(notificationRequest) + '\n';
            console.log('Sending: notifications/initialized');
            this.serverProcess.stdin.write(notificationStr);

            // Wait for the notification to be processed
            await new Promise(resolve => setTimeout(resolve, 500));

            return { initialized: true, capabilities: response.result };
        });
    }

    async testListTools() {
        return this.runTest('List Tools', async () => {
            const response = await this.sendRequest('tools/list', {});

            if (response.error) {
                throw new Error(`List tools failed: ${response.error.message}`);
            }

            const tools = response.result.tools || [];
            const expectedTools = [
                'connect_telescope',
                'disconnect_telescope',
                'get_telescope_status',
                'goto_target',
                'start_imaging',
                'stop_imaging',
                'get_imaging_status',
                'start_calibration',
                'get_calibration_status',
                'park_telescope',
                'unpark_telescope',
                'search_target',
                'get_system_info',
                'emergency_stop'
            ];

            const toolNames = tools.map(t => t.name);
            const missing = expectedTools.filter(name => !toolNames.includes(name));

            if (missing.length > 0) {
                throw new Error(`Missing tools: ${missing.join(', ')}`);
            }

            return { toolCount: tools.length, tools: toolNames };
        });
    }

    async testSystemInfo() {
        return this.runTest('Get System Info', async () => {
            const response = await this.sendRequest('tools/call', {
                name: 'get_system_info',
                arguments: {}
            });

            if (response.error) {
                throw new Error(`System info failed: ${response.error.message}`);
            }

            const content = response.result.content;
            if (!content || content.length === 0) {
                throw new Error('No content in system info response');
            }

            return { success: true, contentLength: content[0].text.length };
        });
    }

    async testTargetSearch() {
        return this.runTest('Search Target (M31)', async () => {
            const response = await this.sendRequest('tools/call', {
                name: 'search_target',
                arguments: { target_name: 'M31' }
            });

            if (response.error) {
                throw new Error(`Target search failed: ${response.error.message}`);
            }

            const content = response.result.content;
            if (!content || content.length === 0) {
                throw new Error('No content in target search response');
            }

            const text = content[0].text;
            if (!text.includes('coordinates') || !text.includes('ra') || !text.includes('dec')) {
                throw new Error('Target search response missing coordinate information');
            }

            return { success: true, target: 'M31', contentPreview: text.substring(0, 100) };
        });
    }

    async testCalibrationError() {
        return this.runTest('Calibration Error Handling', async () => {
            const response = await this.sendRequest('tools/call', {
                name: 'start_calibration',
                arguments: {}
            });

            // Check if it's an error response
            if (response.error) {
                const errorMessage = response.error.message.toLowerCase();
                if (errorMessage.includes('not connected') || errorMessage.includes('mobile app')) {
                    return { success: true, errorHandled: true, errorType: 'connection' };
                }
                throw new Error(`Unexpected error message: ${response.error.message}`);
            }

            // Check if it's a content response with error message
            if (response.result && response.result.content) {
                const content = response.result.content[0];
                const text = content.text.toLowerCase();

                if (text.includes('not connected') || text.includes('mobile app')) {
                    return { success: true, errorHandled: true, errorType: 'content' };
                }
                throw new Error(`Expected connection error or mobile app requirement. Got: ${content.text}`);
            }

            throw new Error('Expected calibration to fail with error or return error content');
        });
    }

    async testConnectionHandling() {
        return this.runTest('Connection Status (Not Connected)', async () => {
            const response = await this.sendRequest('tools/call', {
                name: 'get_telescope_status',
                arguments: {}
            });

            if (response.error) {
                // This might be expected if not connected
                if (response.error.message.toLowerCase().includes('not connected')) {
                    return { success: true, notConnected: true };
                }
                throw new Error(`Unexpected error: ${response.error.message}`);
            }

            const content = response.result.content;
            if (content && content[0] && content[0].text.toLowerCase().includes('not connected')) {
                return { success: true, notConnected: true };
            }

            return { success: true, statusReceived: true };
        });
    }

    printResults() {
        console.log('\n📊 Test Results Summary:');
        console.log('═'.repeat(50));

        let passed = 0;
        let failed = 0;

        this.testResults.forEach(result => {
            const status = result.status === 'PASS' ? '✅' : '❌';
            console.log(`${status} ${result.name}: ${result.status}`);

            if (result.status === 'PASS') {
                passed++;
            } else {
                failed++;
                console.log(`   Error: ${result.error}`);
            }
        });

        console.log('═'.repeat(50));
        console.log(`Total: ${this.testResults.length}, Passed: ${passed}, Failed: ${failed}`);

        return failed === 0;
    }
}

async function main() {
    console.log('🔬 SeestarS50 MCP Simple Test Suite');
    console.log('═'.repeat(50));

    const tester = new SimpleMCPTester();

    try {
        // Start the MCP server
        console.log('Starting server...');
        const serverStarted = await tester.startServer();

        if (!serverStarted) {
            console.error('❌ Could not start MCP server, exiting');
            process.exit(1);
        }

        console.log('Running tests...');

        // Run all tests
        await tester.testInitialization();
        await tester.testListTools();
        await tester.testSystemInfo();
        await tester.testTargetSearch();
        await tester.testCalibrationError();
        await tester.testConnectionHandling();

        // Print results
        const allPassed = tester.printResults();

        if (allPassed) {
            console.log('\n🎉 All MCP tests passed!');
            process.exit(0);
        } else {
            console.log('\n💥 Some MCP tests failed!');
            process.exit(1);
        }

    } catch (error) {
        console.error(`\n💥 Test suite failed: ${error.message}`);
        console.error(`Stack trace: ${error.stack}`);
        process.exit(1);
    } finally {
        // Clean up
        console.log('Cleaning up...');
        await tester.stopServer();
    }
}

// Handle process signals
process.on('SIGINT', async () => {
    console.log('\n🛑 Received SIGINT, shutting down...');
    process.exit(1);
});

process.on('SIGTERM', async () => {
    console.log('\n🛑 Received SIGTERM, shutting down...');
    process.exit(1);
});

// Run the tests
if (import.meta.url === `file://${process.argv[1]}`) {
    main().catch(error => {
        console.error(`💥 Fatal error: ${error.message}`);
        process.exit(1);
    });
}

export default SimpleMCPTester;
