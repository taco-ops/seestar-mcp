#!/usr/bin/env node

/**
 * Test Solar System Object Resolution in SeestarS50 MCP Server
 *
 * This test specifically verifies that the MCP server can now resolve
 * solar system objects like the Sun, Moon, and planets.
 */

import { spawn } from 'child_process';

class SolarSystemMCPTester {
    constructor() {
        this.serverProcess = null;
        this.nextId = 1;
    }

    async startServer() {
        console.log('🚀 Starting SeestarS50 MCP Server for solar system testing...');

        this.serverProcess = spawn('uv', ['run', 'python', '-m', 'seestar_mcp'], {
            stdio: ['pipe', 'pipe', 'pipe'],
            env: { ...process.env, SEESTAR_HOST: '127.0.0.1' } // Use localhost to avoid connection issues
        });

        // Log server stderr for debugging
        this.serverProcess.stderr.on('data', (data) => {
            const output = data.toString().trim();
            if (output) {
                console.debug(`Server: ${output}`);
            }
        });

        // Wait for server to start
        await new Promise(resolve => setTimeout(resolve, 2000));

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
            await new Promise(resolve => setTimeout(resolve, 500));
        }
    }

    async sendRequest(method, params = {}) {
        return new Promise((resolve, reject) => {
            const id = this.nextId++;
            const request = {
                jsonrpc: "2.0",
                id: id,
                method: method,
                params: params
            };

            let responseBuffer = '';
            let resolved = false;

            const timeout = setTimeout(() => {
                if (!resolved) {
                    resolved = true;
                    reject(new Error(`Request timeout for ${method}`));
                }
            }, 10000);

            const dataHandler = (data) => {
                responseBuffer += data.toString();
                const lines = responseBuffer.split('\n');
                responseBuffer = lines.pop() || ''; // Keep incomplete line

                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const response = JSON.parse(line.trim());
                            if (response.id === id && !resolved) {
                                resolved = true;
                                clearTimeout(timeout);
                                this.serverProcess.stdout.off('data', dataHandler);
                                resolve(response);
                                return;
                            }
                        } catch (e) {
                            // Ignore parse errors for non-JSON lines
                        }
                    }
                }
            };

            this.serverProcess.stdout.on('data', dataHandler);

            // Send the request
            const requestStr = JSON.stringify(request) + '\n';
            console.debug(`→ ${method}: ${JSON.stringify(params, null, 2)}`);
            this.serverProcess.stdin.write(requestStr);
        });
    }

    async initialize() {
        console.log('\n🔧 Initializing MCP connection...');

        const response = await this.sendRequest('initialize', {
            protocolVersion: "2024-11-05",
            capabilities: {},
            clientInfo: {
                name: "solar-test-client",
                version: "1.0.0"
            }
        });

        if (response.error) {
            throw new Error(`Initialization failed: ${response.error.message}`);
        }

        // Send initialized notification
        const notificationRequest = {
            jsonrpc: "2.0",
            method: "notifications/initialized"
        };
        this.serverProcess.stdin.write(JSON.stringify(notificationRequest) + '\n');

        console.log('✅ MCP connection initialized');
        return response;
    }

    async testSolarSystemObjectResolution(objectName) {
        console.log(`\n🌟 Testing resolution of: ${objectName}`);

        try {
            const response = await this.sendRequest('tools/call', {
                name: 'search_target',
                arguments: {
                    target_name: objectName
                }
            });

            if (response.error) {
                throw new Error(`Tool call failed: ${response.error.message}`);
            }

            // Use the structured content from the MCP response
            const result = response.result.structuredContent;

            console.log(`← Response for ${objectName}:`);
            console.log(`   Found: ${result.found}`);

            if (result.found) {
                const target = result.target;
                console.log(`   Name: ${target.name}`);
                console.log(`   Type: ${target.object_type || 'Unknown'}`);
                console.log(`   RA: ${target.coordinates.ra.toFixed(4)}h`);
                console.log(`   DEC: ${target.coordinates.dec.toFixed(4)}°`);

                if (target.magnitude !== null) {
                    console.log(`   Magnitude: ${target.magnitude}`);
                }

                // Check for solar warning
                if (objectName.toLowerCase() === 'sun' && target.name.includes('SOLAR OBSERVATION')) {
                    console.log('   ✅ Solar safety warning present');
                }

                return { success: true, result };
            } else {
                console.log(`   Alternatives: ${result.alternatives.join(', ')}`);
                return { success: false, result };
            }

        } catch (error) {
            console.error(`❌ Error testing ${objectName}: ${error.message}`);
            return { success: false, error: error.message };
        }
    }

    async runAllTests() {
        const solarSystemObjects = [
            'sun', 'Sun', 'SUN',
            'moon', 'Moon',
            'mars', 'Mars',
            'jupiter', 'Jupiter',
            'venus', 'Venus',
            'saturn', 'Saturn',
            'mercury', 'Mercury'
        ];

        const results = [];
        let successCount = 0;

        for (const obj of solarSystemObjects) {
            const result = await this.testSolarSystemObjectResolution(obj);
            results.push({ object: obj, ...result });

            if (result.success) {
                successCount++;
            }

            // Small delay between tests
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        console.log('\n' + '='.repeat(60));
        console.log('📊 TEST RESULTS SUMMARY');
        console.log('='.repeat(60));
        console.log(`✅ Successful resolutions: ${successCount}/${solarSystemObjects.length}`);
        console.log(`❌ Failed resolutions: ${solarSystemObjects.length - successCount}/${solarSystemObjects.length}`);

        const failedObjects = results.filter(r => !r.success).map(r => r.object);
        if (failedObjects.length > 0) {
            console.log(`Failed objects: ${failedObjects.join(', ')}`);
        }

        return results;
    }
}

async function main() {
    console.log('🌌 Solar System Object Resolution Test for Seestar MCP');
    console.log('='.repeat(60));

    const tester = new SolarSystemMCPTester();

    try {
        // Start server
        const started = await tester.startServer();
        if (!started) {
            console.error('❌ Could not start server, exiting');
            process.exit(1);
        }

        // Initialize MCP connection
        await tester.initialize();

        // Run solar system tests
        const results = await tester.runAllTests();

        // Determine overall success
        const successfulResolutions = results.filter(r => r.success).length;
        const overallSuccess = successfulResolutions >= results.length * 0.8; // 80% success rate

        console.log('\n' + '='.repeat(60));
        if (overallSuccess) {
            console.log('🎉 SOLAR SYSTEM RESOLUTION TEST: PASSED');
            console.log('The Seestar MCP now successfully resolves solar system objects!');
        } else {
            console.log('❌ SOLAR SYSTEM RESOLUTION TEST: FAILED');
            console.log('Some solar system objects could not be resolved.');
        }
        console.log('='.repeat(60));

    } catch (error) {
        console.error(`💥 Test error: ${error.message}`);
        console.error(error.stack);
        process.exit(1);
    } finally {
        await tester.stopServer();
    }
}

// Run the test if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
    main().catch(error => {
        console.error(`Fatal error: ${error.message}`);
        process.exit(1);
    });
}

export { SolarSystemMCPTester };
