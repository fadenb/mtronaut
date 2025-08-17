# PTY/Terminal Emulation Research

## Overview

This document contains research findings for implementing real-time terminal streaming with PTY (pseudo-terminal) support for network analysis tools, particularly focusing on handling curses-based applications like MTR.

## Key Technical Findings

### 1. PTY (Pseudo-Terminal) Implementation

#### Core Python Libraries
- **`pty` module**: Built-in Python library for pseudo-terminal utilities
- **`ptyprocess`**: The recommended third-party library for robust PTY handling
- **`subprocess`**: Standard library for process management (insufficient alone for interactive apps)

#### Why PTY is Essential
From research findings:
- Regular `subprocess.Popen` doesn't allocate a pseudo-terminal
- Many commands behave differently when not running in a real terminal
- Applications may format output differently (e.g., `ls` lists files in columns vs. single column)
- Interactive applications like MTR require a TTY to function properly
- Password prompts and curses applications need PTY to work correctly

#### PTY Implementation Options

**Option 1: Built-in `pty` module (Not Used in This Project)**
```python
import pty
import subprocess

# Basic PTY spawning (example, not used in current implementation)
# pty.spawn(['mtr', '--curses', 'google.com'])
```

**Option 2: `ptyprocess` library (Recommended and Used)**
```python
from ptyprocess import PtyProcess

# Used in TerminalSession for more control over PTY process
# Example: process = PtyProcess.spawn(['mtr', '--curses', 'google.com'], echo=False)
```

### 2. Terminal Control Characters & ANSI Escape Sequences

#### ANSI Escape Sequence Handling
- **Standard**: ANSI escape sequences for cursor control, colors, and formatting
- **Format**: Most sequences start with `\u001b[` (ESC + `[`)
- **Categories**:
  - Cursor positioning: `\u001b[H`, `\u001b[{row};{col}H`
  - Screen clearing: `\u001b[2J`, `\u001b[K`
  - Colors: `\u001b[31m` (red), `\u001b[0m` (reset)
  - Cursor visibility: `\u001b[?25l` (hide), `\u001b[?25h` (show)

#### XTerm Control Sequences
- **Reference**: https://invisible-island.net/xterm/ctlseqs/ctlseqs.html
- **Comprehensive**: Covers all control sequences supported by xterm
- **Critical for MTR**: MTR uses extensive cursor positioning and screen updates

#### Key Challenges
1. **Real-time Processing**: Must handle partial escape sequences
2. **Buffer Management**: Avoid breaking escape sequences across WebSocket messages
3. **Terminal Size**: Need to communicate terminal dimensions to PTY process

### 3. MTR Interactive Mode Specifics

#### MTR Curses Interface Behavior
- **Interactive Mode**: Uses ncurses library for real-time display updates
- **Screen Updates**: Continuously updates statistics in place
- **Cursor Positioning**: Moves cursor to specific positions for updates
- **Colors**: Uses ANSI colors for different statistics (loss, latency)
- **Terminal Size Dependency**: Layout depends on terminal dimensions

#### MTR Command Options
```bash
# Interactive curses mode (what we need)
mtr --curses --interval=1 <target>

# Report mode (not suitable for our use case)
mtr --report --report-cycles=10 <target>
```

#### Technical Requirements for MTR
1. **Full PTY Support**: Must run in pseudo-terminal
2. **Terminal Size**: Must set proper ROWS/COLS environment variables
3. **Signal Handling**: Handle SIGWINCH for terminal resize
4. **Real-time Streaming**: No buffering delays for screen updates

### 4. FastAPI WebSocket Implementation

#### Real-time Streaming Architecture
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
from backend.mtronaut.session import SessionManager
from backend.mtronaut.tools import get_tool_config

app = FastAPI()
session_manager = SessionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = None
    try:
        while True:
            message = await websocket.receive_json()
            action = message.get("action")

            if action == "start_tool":
                tool_name = message.get("tool")
                target = message.get("target")
                term_cols = message.get("term_cols")
                term_rows = message.get("term_rows")

                tool_config = get_tool_config(tool_name)
                if not tool_config:
                    await websocket.send_json({"status": "error", "message": f"Tool '{tool_name}' not found."})
                    continue

                cmd = tool_config["command"](target)
                
                # Start a new session
                session_id = session_manager.start_session(
                    websocket,
                    cmd,
                    term_cols,
                    term_rows
                )
                await websocket.send_json({"status": "started", "session_id": session_id})

            elif action == "stop_tool":
                if session_id:
                    session_manager.stop_session(session_id)
                    await websocket.send_json({"status": "stopped", "message": "Process stopped by user."})
                else:
                    await websocket.send_json({"status": "error", "message": "No active session to stop."})

            elif action == "resize_terminal":
                cols = message.get("term_cols")
                rows = message.get("term_rows")
                if session_id:
                    session_manager.resize_terminal(session_id, cols, rows)
                else:
                    print("Warning: Resize request received without active session.")

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"WebSocket error for session {session_id}: {e}")
        if session_id:
            await websocket.send_json({"status": "error", "message": f"Server error: {e}"})
    finally:
        if session_id:
            session_manager.cleanup_connection(websocket)
```

#### Critical Performance Considerations
1. **Non-blocking I/O**: Use `os.read()` with proper error handling
2. **Async/Await**: Ensure WebSocket operations don't block PTY reading
3. **Buffer Size**: Balance between latency and efficiency (1024-4096 bytes)
4. **Error Handling**: Handle broken pipes, process termination gracefully

### 5. Terminal Size Management

#### Setting Terminal Dimensions
```python
import struct
import fcntl
import termios

def set_terminal_size(fd, rows, cols):
    """Set terminal size for PTY"""
    size = struct.pack('HHHH', rows, cols, 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, size)
```

#### Dynamic Resize Handling
- **SIGWINCH Signal**: Sent when terminal size changes
- **WebSocket Communication**: Frontend must send size updates
- **PTY Update**: Propagate size changes to PTY process

### 6. Session Management & Cleanup

#### Process Lifecycle
```python
from backend.mtronaut.terminal import TerminalSession

# In the actual implementation, TerminalSession.stop() handles this.
# Example of what TerminalSession.stop() does internally:
def stop_terminal_session(session: TerminalSession):
    """Stops the running process and cleans up resources."""
    session.stop()
```

#### WebSocket Disconnect Handling
- **Immediate Cleanup**: Terminate processes when WebSocket disconnects
- **Resource Management**: Close all file descriptors and clean up processes
- **Signal Groups**: Use process groups to ensure all child processes are terminated

### 7. Frontend Integration with xterm.js

#### XTerm.js Configuration
```javascript
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';

const terminal = new Terminal({
    cursorBlink: true,
    fontSize: 14,
    fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
    theme: {
        background: '#1e1e1e',
        foreground: '#d4d4d4'
    }
});

const fitAddon = new FitAddon();
terminal.loadAddon(fitAddon);
```

#### WebSocket Integration
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
    if (event.data instanceof ArrayBuffer) {
        const uint8Array = new Uint8Array(event.data);
        const text = new TextDecoder().decode(uint8Array);
        terminal.write(text);
    }
};

// Send terminal size updates
terminal.onResize(({ cols, rows }) => {
    ws.send(JSON.stringify({
        action: 'resize',
        cols: cols,
        rows: rows
    }));
});
```

### 8. Implementation Challenges & Solutions

#### Challenge 1: Partial ANSI Sequences
**Problem**: WebSocket messages might split ANSI escape sequences
**Solution**: Buffer incomplete sequences and reassemble

```python
class ANSIBuffer:
    def __init__(self):
        self.buffer = b''
    
    def process_data(self, data):
        self.buffer += data
        complete_data = b''
        
        # Process complete sequences
        while b'\x1b[' in self.buffer:
            # Extract complete ANSI sequences
            # Return complete data, keep incomplete in buffer
            pass
        
        return complete_data
```

#### Challenge 2: Real-time Performance
**Problem**: Minimize latency in the streaming pipeline
**Solutions**:
- Use small read buffers (1024 bytes)
- Avoid unnecessary data processing
- Use binary WebSocket messages
- Implement proper async/await patterns

#### Challenge 3: Terminal Compatibility
**Problem**: Different terminals handle control sequences differently
**Solution**: Use xterm.js which provides comprehensive terminal emulation

### 9. Recommended Implementation Stack

#### Backend Dependencies
```toml
[project]
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "websockets>=12.0",
    "ptyprocess>=0.7.0"
]
```

#### Frontend Dependencies
- **xterm.js**: Core terminal emulation
- **xterm-addon-fit**: Terminal sizing
- **xterm-addon-web-links**: URL detection (optional)

### 10. Testing Strategy

#### Unit Tests
- PTY process spawning and cleanup
- ANSI sequence parsing
- WebSocket message handling
- Terminal size management

#### Integration Tests
- End-to-end tool execution (mtr, ping, traceroute, tracepath)
- Real-time streaming performance
- Connection handling and recovery
- Multiple concurrent sessions

#### Manual Testing Scenarios
1. **MTR Interactive Mode**: Verify curses interface works correctly
2. **Long-running Sessions**: Test with extended MTR sessions
3. **Connection Loss**: Verify proper cleanup on disconnect
4. **Multiple Users**: Test concurrent sessions
5. **Terminal Resize**: Verify dynamic size updates work

### 11. Performance Optimization

#### Streaming Optimizations
- **Buffer Management**: Use appropriate buffer sizes (1024-4096 bytes)
- **Async I/O**: Ensure non-blocking operations throughout pipeline
- **Memory Management**: Avoid accumulating large amounts of data
- **Connection Pooling**: Efficient WebSocket connection handling

#### Resource Management
- **Process Limits**: Monitor and limit concurrent processes
- **Memory Usage**: Track memory consumption per session
- **CPU Usage**: Monitor CPU impact of multiple PTY processes
- **File Descriptors**: Ensure proper cleanup to avoid leaks

### 12. Security Considerations

#### Current Scope (No Security)
- Direct command execution with predefined parameters
- No input validation beyond basic format checking
- No authentication or authorization

#### Future Security Enhancements
- Input sanitization for target hostnames/IPs
- Command injection prevention
- Rate limiting per user/IP
- Resource usage quotas
- Audit logging

## Implementation Roadmap

### Phase 1: Basic PTY Implementation
1. Set up FastAPI with WebSocket support
2. Implement basic PTY process spawning
3. Create simple WebSocket streaming
4. Test with basic commands (ping, traceroute)

### Phase 2: Advanced Terminal Support
1. Implement full ANSI sequence handling
2. Add terminal size management
3. Test with MTR interactive mode
4. Optimize streaming performance

### Phase 3: Production Readiness
1. Add comprehensive error handling
2. Implement session management
3. Add monitoring and logging
4. Performance testing and optimization

## Key Takeaways

1. **PTY is Essential**: Regular subprocess won't work for interactive applications
2. **ptyprocess Library**: The chosen library, provides robust control over PTY processes
3. **ANSI Handling**: Must properly handle escape sequences for curses apps
4. **Real-time Performance**: Critical to minimize buffering and latency
5. **Terminal Size**: Must communicate dimensions between frontend and PTY
6. **Cleanup is Critical**: Proper process and resource cleanup on disconnect
7. **xterm.js**: Provides comprehensive terminal emulation for the frontend

This research provides the foundation for implementing a robust real-time terminal streaming system that can handle complex curses-based applications like MTR while maintaining excellent performance and user experience.