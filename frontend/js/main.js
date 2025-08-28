// frontend/js/main.js
// Main application logic for the Mtronaut web interface.

document.addEventListener('DOMContentLoaded', () => {
    const toolSelect = document.getElementById('tool-select');
    const targetInput = document.getElementById('target-input');
    const startButton = document.getElementById('start-button');
    const stopButton = document.getElementById('stop-button');
    const copyButton = document.getElementById('copy-button');
    const terminalContainer = document.getElementById('terminal-container');
    const toolParametersDiv = document.getElementById('tool-parameters');

    let terminalManager;
    let websocketClient;

    // Initialize WebSocket and Terminal
    function initializeApp() {
        websocketClient = new WebSocketClient(
            `ws://${window.location.host}/ws`,
            handleWebSocketMessage,
            handleWebSocketOpen,
            handleWebSocketClose,
            handleWebSocketError,
            handleWebSocketReconnectAttempt
        );
        terminalManager = new TerminalManager('terminal-container', websocketClient);
    }

    // Populate tool dropdown
    function populateToolSelect() {
        const tools = window.listToolNames();
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
        const config = window.getToolConfig(selectedTool);
        if (config && config.defaultTarget) {
            targetInput.placeholder = `Enter IP or hostname (e.g., ${config.defaultTarget})`;
            targetInput.value = config.defaultTarget; // Pre-fill with default
        } else {
            targetInput.placeholder = 'Enter IP or hostname';
            targetInput.value = '';
        }
    }

    function renderToolParameters() {
        const selectedTool = toolSelect.value;
        const toolConfig = window.getToolConfig(selectedTool);
        toolParametersDiv.innerHTML = ''; // Clear previous parameters

        if (toolConfig && toolConfig.parameters) {
            const togglesContainer = document.createElement('div');
            togglesContainer.className = 'param-toggles';

            const inputsContainer = document.createElement('div');
            inputsContainer.className = 'param-inputs';

            toolConfig.parameters.forEach(param => {
                const paramId = `param-${param.name}`;
                const container = document.createElement('div');
                container.classList.add('param-item');

                const label = document.createElement('label');
                label.htmlFor = paramId;
                label.textContent = param.help_text;

                let inputElement;
                if (param.param_type === 'bool') {
                    container.classList.add('input-first');
                    inputElement = document.createElement('input');
                    inputElement.type = 'checkbox';
                    inputElement.id = paramId;
                    inputElement.name = param.name;
                    inputElement.checked = param.default;
                    container.appendChild(inputElement);
                    container.appendChild(label);
                    togglesContainer.appendChild(container);
                } else {
                    if (param.param_type === 'int' || param.param_type === 'float') {
                        container.classList.add('input-first');
                        inputElement = document.createElement('input');
                        inputElement.type = 'number';
                        inputElement.classList.add('input-number'); // Add class for styling
                        if (param.param_type === 'float') {
                            inputElement.step = 'any';
                        }
                        inputElement.id = paramId;
                        inputElement.name = param.name;
                        inputElement.value = param.default || '';
                        container.appendChild(inputElement);
                        container.appendChild(label);
                    } else {
                        inputElement = document.createElement('input');
                        inputElement.type = 'text';
                        inputElement.id = paramId;
                        inputElement.name = param.name;
                        inputElement.value = param.default || '';
                        container.appendChild(label);
                        container.appendChild(inputElement);
                    }
                    inputsContainer.appendChild(container);
                }
            });

            toolParametersDiv.appendChild(togglesContainer);
            toolParametersDiv.appendChild(inputsContainer);
        }
    }

    function isValidTarget(target) {
        // This is a basic check to prevent command injection.
        // The backend has more robust validation.
        const validTargetRegex = /^[a-zA-Z0-9.-_:]+$/;
        return validTargetRegex.test(target);
    }

    // Event Listeners
    toolSelect.addEventListener('change', () => {
        updateTargetPlaceholder();
        renderToolParameters();
    });

    startButton.addEventListener('click', () => {
        const tool = toolSelect.value;
        const target = targetInput.value.trim();

        if (!target) {
            showNotification('Please enter a target IP or hostname.', 'error');
            return;
        }

        if (!isValidTarget(target)) {
            targetInput.style.border = '1px solid red';
            showNotification('Invalid target. Please enter a valid IP address or hostname.', 'error');
            return;
        } else {
            targetInput.style.border = ''; // Reset border
        }

        const params = {};
        const toolConfig = window.getToolConfig(tool);
        if (toolConfig && toolConfig.parameters) {
            toolConfig.parameters.forEach(param => {
                const inputElement = document.getElementById(`param-${param.name}`);
                if (inputElement) {
                    if (param.param_type === 'bool') {
                        params[param.name] = inputElement.checked;
                    } else if (param.param_type === 'int') {
                        params[param.name] = parseInt(inputElement.value);
                    } else if (param.param_type === 'float') {
                        params[param.name] = parseFloat(inputElement.value);
                    } else {
                        params[param.name] = inputElement.value;
                    }
                }
            });
        }

        terminalManager.clear();
        startButton.disabled = true;
        stopButton.disabled = false;
        copyButton.disabled = false;

        websocketClient.sendJson({
            action: 'start_tool',
            tool: tool,
            target: target,
            term_cols: terminalManager.terminal.cols,
            term_rows: terminalManager.terminal.rows,
            params: params
        });
    });

    stopButton.addEventListener('click', () => {
        websocketClient.sendJson({ action: 'stop_tool' });
        startButton.disabled = false;
        stopButton.disabled = true;
    });

    copyButton.addEventListener('click', () => {
        terminalManager.copyOutput();
    });

    // WebSocket Message Handlers
    function handleWebSocketMessage(data) {
        if (typeof data === 'string') {
            const message = JSON.parse(data);
            if (message.status === 'stopped') {
                startButton.disabled = false;
                stopButton.disabled = true;
            } else if (message.status === 'error') {
                startButton.disabled = false;
                stopButton.disabled = true;
                copyButton.disabled = true;
            }
            terminalManager.write(`\r\n[Server Status]: ${message.message}\r\n`);
        } else {
            terminalManager.write(data);
        }
    }

    function handleWebSocketOpen() {
        console.log('WebSocket connection established.');
        startButton.disabled = false;
    }

    function handleWebSocketClose(event, permanent = false) {
        console.log('WebSocket connection closed.', event);
        startButton.disabled = false;
        stopButton.disabled = true;
        if (permanent) {
            terminalManager.write('\r\n[Connection Closed Permanently. Please refresh to reconnect.]\r\n');
        } else {
            terminalManager.write('\r\n[Connection Closed. Attempting to reconnect...]\r\n');
        }
    }

    function handleWebSocketError(event) {
        console.error('WebSocket error occurred.', event);
        startButton.disabled = false;
        stopButton.disabled = true;
        terminalManager.write('\r\n[Connection Error. Attempting to reconnect...]\r\n');
    }

    function handleWebSocketReconnectAttempt(attempt, maxAttempts, delay) {
        terminalManager.write(`\r\n[Reconnecting... Attempt ${attempt}/${maxAttempts}. Next attempt in ${delay / 1000}s]\r\n`);
    }

    // Initial setup
    populateToolSelect();
    renderToolParameters();
    initializeApp();
});