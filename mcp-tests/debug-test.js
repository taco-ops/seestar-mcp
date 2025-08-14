#!/usr/bin/env node

/**
 * Very simple MCP test to debug the issue
 */

console.log('Debug: Starting test script');

try {
    console.log('Debug: About to import modules');

    import('child_process').then(({ spawn }) => {
        console.log('Debug: child_process imported successfully');

        console.log('🔬 Simple MCP Test');

        // Try to start the server
        console.log('Debug: Starting server process');
        const serverProcess = spawn('uv', ['run', 'python', '-m', 'seestar_mcp.server'], {
            stdio: ['pipe', 'pipe', 'pipe']
        });

        console.log('Debug: Server process started');

        serverProcess.stdout.on('data', (data) => {
            console.log('Server stdout:', data.toString());
        });

        serverProcess.stderr.on('data', (data) => {
            console.log('Server stderr:', data.toString());
        });

        serverProcess.on('error', (error) => {
            console.error('Server process error:', error);
        });

        serverProcess.on('close', (code) => {
            console.log('Server process closed with code:', code);
            process.exit(code);
        });

        // Send a simple test after a delay
        setTimeout(() => {
            console.log('Debug: Sending test request');
            const request = JSON.stringify({
                jsonrpc: "2.0",
                id: 1,
                method: "initialize",
                params: {
                    protocolVersion: "2024-11-05",
                    capabilities: {},
                    clientInfo: { name: "test", version: "1.0.0" }
                }
            }) + '\n';

            console.log('Sending:', request.trim());
            serverProcess.stdin.write(request);
        }, 3000);

    }).catch(error => {
        console.error('Debug: Import error:', error);
        process.exit(1);
    });

} catch (error) {
    console.error('Debug: Top-level error:', error);
    process.exit(1);
}

console.log('Debug: Script setup complete');
