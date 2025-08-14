#!/usr/bin/env node

/**
 * Working MCP Test Suite for SeestarS50 MCP Server
 */

import { spawn } from 'child_process';

class WorkingMCPTester {
    constructor() {
        this.serverProcess = null;
        this.testResults = [];
        this.nextId = 1;
    }

    async startServer() {
        console.log('🚀 Starting SeestarS50 MCP Server...');

        this.serverProcess = spawn('uv', ['run', 'python', '-m', 'seestar_mcp.server'], {
            stdio: ['pipe', 'pipe', 'pipe']
        });

        // Wait for server startup
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
            let timeout;

            const cleanup = () => {
                if (timeout) clearTimeout(timeout);
                this.serverProcess.stdout.removeAllListeners('data');
            };

            timeout = setTimeout(() => {
                cleanup();
                reject(new Error(`Timeout waiting for response to ${method}`));
            }, 10000);

            this.serverProcess.stdout.on('data', (data) => {
                responseBuffer += data.toString();

                const lines = responseBuffer.split('\n');
                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const parsed = JSON.parse(line.trim());
                            if (parsed.id === request.id) {
                                cleanup();
                                resolve(parsed);
                                return;
                            }
                        } catch (e) {
                            // Continue looking for valid JSON
                        }
                    }
                }
            });

            const requestStr = JSON.stringify(request) + '\n';
            console.log(`📤 Sending: ${method}`);
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
            return null;
        }
    }

    async testInitialization() {
        return this.runTest('Server Initialization', async () => {
            const response = await this.sendRequest('initialize', {
                protocolVersion: "2024-11-05",
                capabilities: {},
                clientInfo: { name: "test-client", version: "1.0.0" }
            });

            if (response.error) {
                throw new Error(`Initialization failed: ${response.error.message}`);
            }

            // Send the initialized notification
            const notificationRequest = {
                jsonrpc: "2.0",
                method: "notifications/initialized"
            };

            const notificationStr = JSON.stringify(notificationRequest) + '\n';
            console.log('📤 Sending: notifications/initialized');
            this.serverProcess.stdin.write(notificationStr);

            // Wait a moment for the notification to be processed
            await new Promise(resolve => setTimeout(resolve, 500));

            return { initialized: true };
        });
    }

    async testListTools() {
        return this.runTest('List Tools', async () => {
            // MCP tools/list should not have any parameters
            const response = await this.sendRequest('tools/list');

            if (response.error) {
                throw new Error(`List tools failed: ${response.error.message}`);
            }

            const tools = response.result.tools || [];
            const expectedTools = [
                'connect_telescope', 'disconnect_telescope', 'get_telescope_status',
                'goto_target', 'start_imaging', 'stop_imaging', 'get_imaging_status',
                'start_calibration', 'get_calibration_status', 'park_telescope',
                'unpark_telescope', 'search_target', 'get_system_info', 'emergency_stop'
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

            return { success: true };
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
            if (!text.includes('coordinates')) {
                throw new Error('Target search response missing coordinate information');
            }

            return { success: true, target: 'M31' };
        });
    }

    async testCalibrationError() {
        return this.runTest('Calibration Error Handling', async () => {
            const response = await this.sendRequest('tools/call', {
                name: 'start_calibration',
                arguments: {}
            });

            // The tool should return content explaining either that it's not connected
            // or that calibration requires the mobile app
            if (response.result && response.result.content) {
                const content = response.result.content[0];
                const text = content.text.toLowerCase();

                if (text.includes('not connected') || text.includes('mobile app')) {
                    return { success: true, errorHandled: true };
                } else {
                    throw new Error(`Expected connection error or mobile app requirement. Got: ${content.text}`);
                }
            } else if (response.error) {
                const errorMessage = response.error.message.toLowerCase();
                if (errorMessage.includes('not connected') || errorMessage.includes('mobile app')) {
                    return { success: true, errorHandled: true };
                } else {
                    throw new Error(`Expected connection error or mobile app requirement. Got: ${response.error.message}`);
                }
            } else {
                throw new Error('Expected either error or explanatory content');
            }
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
            }
        });

        console.log('═'.repeat(50));
        console.log(`Total: ${this.testResults.length}, Passed: ${passed}, Failed: ${failed}`);

        return failed === 0;
    }
}

async function main() {
    console.log('🔬 SeestarS50 MCP Working Test Suite');
    console.log('═'.repeat(50));

    const tester = new WorkingMCPTester();

    try {
        const serverStarted = await tester.startServer();
        if (!serverStarted) {
            console.error('❌ Could not start MCP server');
            process.exit(1);
        }

        // Run tests
        await tester.testInitialization();
        await tester.testListTools();
        await tester.testSystemInfo();
        await tester.testTargetSearch();
        await tester.testCalibrationError();

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
        process.exit(1);
    } finally {
        await tester.stopServer();
    }
}

// Handle signals
process.on('SIGINT', () => {
    console.log('\n🛑 Received SIGINT, shutting down...');
    process.exit(1);
});

if (import.meta.url === `file://${process.argv[1]}`) {
    main();
}
