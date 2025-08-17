// frontend/js/main.js
// Main application logic for the Mtronaut web interface.

document.addEventListener('DOMContentLoaded', () => {
    const toolSelect = document.getElementById('tool-select');
    const targetInput = document.getElementById('target-input');
    const startButton = document.getElementById('start-button');
    const stopButton = document.getElementById('stop-button');
    const copyButton = document.getElementById('copy-button'); // Get copy button
    const terminalContainer = document.getElementById('terminal-container');

    let terminalManager;
    let websocketClient;

    // Initialize WebSocket and Terminal
    function initializeApp() {
        websocketClient = new WebSocketClient(
            `ws://${window.location.host}/ws`,
            handleWebSocketMessage,
            handleWebSocketOpen,
            handleWebSocketClose,
            handleWebSocketError
        );
        terminalManager = new TerminalManager('terminal-container', websocketClient);
    }

    // Populate tool dropdown
    function populateToolSelect() {
        const tools = listToolNames();
        toolSelect.innerHTML = ''; // Clear existing options
        tools.forEach(toolName => {
            const option = document.createElement('option');
            option.value = toolName;
            option.textContent = toolName;
            toolSelect.appendChild(option);
        });
        // Set default target based on selected tool
        updateTargetPlaceholder();
    }

    // Update target input placeholder based on selected tool
    function updateTargetPlaceholder() {
        const selectedTool = toolSelect.value;
        const config = getToolConfig(selectedTool);
        if (config && config.defaultTarget) {
            targetInput.placeholder = `Enter IP or hostname (e.g., ${config.defaultTarget})`;
            targetInput.value = config.defaultTarget; // Pre-fill with default
        } else {
            targetInput.placeholder = 'Enter IP or hostname';
            targetInput.value = '';
        }
    }

    // Event Listeners
    toolSelect.addEventListener('change', updateTargetPlaceholder);

    startButton.addEventListener('click', () => {
        const tool = toolSelect.value;
        const target = targetInput.value.trim();

        if (!target) {
            alert('Please enter a target IP or hostname.');
            return;
        }

        terminalManager.clear();
        startButton.disabled = true;
        stopButton.disabled = false;
        copyButton.disabled = false; // Enable copy button

        websocketClient.sendJson({
            action: 'start_tool',
            tool: tool,
            target: target,
            term_cols: terminalManager.terminal.cols,
            term_rows: terminalManager.terminal.rows
        });
    });

    stopButton.addEventListener('click', () => {
        websocketClient.sendJson({ action: 'stop_tool' });
        startButton.disabled = false;
        stopButton.disabled = true;
        // copyButton.disabled remains false, allowing copy after stop
    });

    copyButton.addEventListener('click', () => {
        terminalManager.copyOutput();
    });

    // WebSocket Message Handlers
    function handleWebSocketMessage(data) {
        if (typeof data === 'string') {
            // JSON message (status updates)
            const message = JSON.parse(data);
            // console.log('Status message:', message); // Keep commented for cleaner console
            if (message.status === 'stopped') {
                startButton.disabled = false;
                stopButton.disabled = true;
                // copyButton.disabled remains false, allowing copy after stop
            } else if (message.status === 'error') {
                startButton.disabled = false;
                stopButton.disabled = true;
                copyButton.disabled = true; // Disable copy button on error
            }
            terminalManager.write(`\r\n[Server Status]: ${message.message}\r\n`);
        } else {
            // Binary data (terminal output)
            terminalManager.write(data);
        }
    }

    function handleWebSocketOpen() {
        console.log('WebSocket connection established.');
        // Enable start button only after connection is open
        startButton.disabled = false;
    }

    function handleWebSocketClose(event) {
        console.log('WebSocket connection closed.', event);
        startButton.disabled = false;
        stopButton.disabled = true;
        // copyButton.disabled remains enabled
        terminalManager.write('\r\n[Connection Closed]\r\n');
    }

    function handleWebSocketError(event) {
        console.error('WebSocket error occurred.', event);
        startButton.disabled = false;
        stopButton.disabled = true;
        // copyButton.disabled remains enabled
        terminalManager.write('\r\n[Connection Error]\r\n');
    }

    // Initial setup
    populateToolSelect();
    initializeApp();
});