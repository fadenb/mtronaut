// frontend/js/websocket.js
// Handles WebSocket connection and message sending/receiving.

class WebSocketClient {
    constructor(url, onMessageCallback, onOpenCallback, onCloseCallback, onErrorCallback) {
        this.url = url;
        this.ws = null;
        this.onMessageCallback = onMessageCallback;
        this.onOpenCallback = onOpenCallback;
        this.onCloseCallback = onCloseCallback;
        this.onErrorCallback = onErrorCallback;
        this.connect();
    }

    connect() {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = (event) => {
            console.log('WebSocket opened:', event);
            if (this.onOpenCallback) {
                this.onOpenCallback();
            }
        };

        this.ws.onmessage = (event) => {
            // console.log('WebSocket message received:', event.data);
            if (this.onMessageCallback) {
                this.onMessageCallback(event.data);
            }
        };

        this.ws.onclose = (event) => {
            console.log('WebSocket closed:', event);
            if (this.onCloseCallback) {
                this.onCloseCallback(event);
            }
        };

        this.ws.onerror = (event) => {
            console.error('WebSocket error:', event);
            if (this.onErrorCallback) {
                this.onErrorCallback(event);
            }
        };
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(message);
        } else {
            console.warn('WebSocket not open. Message not sent:', message);
        }
    }

    sendJson(data) {
        this.send(JSON.stringify(data));
    }

    close() {
        if (this.ws) {
            this.ws.close();
        }
    }
}