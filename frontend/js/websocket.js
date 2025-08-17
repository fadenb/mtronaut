// frontend/js/websocket.js
// Handles WebSocket connection and message sending/receiving.

class WebSocketClient {
    constructor(url, onMessageCallback, onOpenCallback, onCloseCallback, onErrorCallback, onReconnectAttemptCallback) {
        this.url = url;
        this.ws = null;
        this.onMessageCallback = onMessageCallback;
        this.onOpenCallback = onOpenCallback;
        this.onCloseCallback = onCloseCallback;
        this.onErrorCallback = onErrorCallback;
        this.onReconnectAttemptCallback = onReconnectAttemptCallback; // New callback for reconnection attempts

        this.reconnectInterval = 1000; // Initial reconnect interval in ms
        this.maxReconnectInterval = 30000; // Max reconnect interval
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10; // Max number of reconnection attempts
        this.forcedClose = false; // Flag to indicate if close was intentional

        this.connect();
    }

    connect() {
        this.ws = new WebSocket(this.url);
        this.forcedClose = false; // Reset on new connection attempt

        this.ws.onopen = (event) => {
            console.log('WebSocket opened:', event);
            this.reconnectAttempts = 0; // Reset attempts on successful connection
            this.reconnectInterval = 1000; // Reset interval
            if (this.onOpenCallback) {
                this.onOpenCallback();
            }
        };

        this.ws.onmessage = (event) => {
            if (this.onMessageCallback) {
                this.onMessageCallback(event.data);
            }
        };

        this.ws.onclose = (event) => {
            console.log('WebSocket closed:', event);
            if (this.forcedClose) {
                if (this.onCloseCallback) {
                    this.onCloseCallback(event); // Call original close handler for intentional close
                }
            } else {
                // Attempt to reconnect if not intentionally closed
                this.handleReconnect(event);
            }
        };

        this.ws.onerror = (event) => {
            console.error('WebSocket error:', event);
            if (this.onErrorCallback) {
                this.onErrorCallback(event); // Call original error handler
            }
            // Always attempt to reconnect on error, unless forcedClose is true (which it shouldn't be on error)
            this.handleReconnect(event);
        };
    }

    handleReconnect(event) {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1), this.maxReconnectInterval);
            console.log(`Attempting to reconnect in ${delay / 1000} seconds... (Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            if (this.onReconnectAttemptCallback) {
                this.onReconnectAttemptCallback(this.reconnectAttempts, this.maxReconnectAttempts, delay);
            }
            setTimeout(() => this.connect(), delay);
        } else {
            console.error('Max reconnection attempts reached. Giving up.');
            if (this.onCloseCallback) { // Use onCloseCallback to signal permanent closure
                this.onCloseCallback(event, true); // Pass true to indicate permanent closure
            }
        }
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(message);
        } else {
            console.warn('WebSocket not open. Message not sent:', message);
            // Optionally, queue messages or notify user if connection is down
        }
    }

    sendJson(data) {
        this.send(JSON.stringify(data));
    }

    close() {
        this.forcedClose = true; // Set flag for intentional close
        if (this.ws) {
            this.ws.close();
        }
    }
}