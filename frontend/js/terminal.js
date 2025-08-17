// frontend/js/terminal.js
// Handles xterm.js integration and terminal display.

class TerminalManager {
    constructor(containerId, websocketClient) {
        this.terminal = new Terminal({
            cursorBlink: true,
            fontSize: 14,
            fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
            theme: {
                background: '#000',
                foreground: '#d4d4d4',
                cursor: '#d4d4d4',
                selection: 'rgba(255, 255, 255, 0.3)',
                black: '#2e3436',
                red: '#cc0000',
                green: '#4e9a06',
                yellow: '#c4a000',
                blue: '#3465a4',
                magenta: '#75507b',
                cyan: '#06989a',
                white: '#d3d7cf',
                brightBlack: '#555753',
                brightRed: '#ef2929',
                brightGreen: '#8ae234',
                brightYellow: '#fce94f',
                brightBlue: '#729fcf',
                brightMagenta: '#ad7fa8',
                brightCyan: '#34e2e2',
                brightWhite: '#eeeeec'
            }
        });
        this.fitAddon = new FitAddon.FitAddon();
        this.terminal.loadAddon(this.fitAddon);
        this.terminal.open(document.getElementById(containerId));
        this.fitAddon.fit();

        this.websocketClient = websocketClient;

        // Handle terminal resize
        window.addEventListener('resize', () => this.fitAddon.fit());
        this.terminal.onResize(size => {
            if (this.websocketClient) {
                this.websocketClient.sendJson({
                    action: 'resize_terminal',
                    term_cols: size.cols,
                    term_rows: size.rows
                });
            }
        });
    }

    write(data) {
        // xterm.js expects string data, so decode bytes if necessary
        if (data instanceof ArrayBuffer || data instanceof Blob) {
            // Handle Blob directly as well for browser compatibility
            data.arrayBuffer().then(buffer => {
                const text = new TextDecoder().decode(buffer);
                this.terminal.write(text);
            });
        } else if (typeof data === 'string') {
            this.terminal.write(data);
        }
    }

    clear() {
        this.terminal.clear();
    }

    copyOutput() {
        const textarea = document.createElement('textarea');
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        textarea.style.left = '-9999px';
        textarea.style.top = '-9999px';
        document.body.appendChild(textarea);

        const lines = [];
        // Iterate through all lines in the buffer, including scrollback
        for (let i = 0; i < this.terminal.buffer.active.length; i++) {
            // Use translateToString(true) to get the rendered text without padding
            lines.push(this.terminal.buffer.active.getLine(i).translateToString(true));
        }

        // Remove trailing empty lines
        while (lines.length > 0 && lines[lines.length - 1].trim() === '') {
            lines.pop();
        }

        textarea.value = lines.join('\n');
        textarea.select();

        try {
            const successful = document.execCommand('copy');
            const msg = successful ? 'Copied to clipboard!' : 'Failed to copy!';
            alert(msg); // Simple feedback
        } catch (err) {
            alert('Error copying to clipboard: ' + err);
        } finally {
            document.body.removeChild(textarea);
        }
    }
}