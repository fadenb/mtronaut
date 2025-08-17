# MTR Default Interactive Mode Behavior Analysis

This document details the terminal output behavior of `mtr` when run in its default interactive mode (e.g., `mtr 8.8.8.8`). This research is based on the analysis of raw PTY output captured using the `script` command.

## Key Findings

1.  **Full-Screen Application**: MTR is not a simple line-scrolling command. It operates as a full-screen terminal application, taking control of the entire terminal window.
2.  **Heavy Use of ANSI Escape Codes**: It relies extensively on standard ANSI escape codes to render its interface. We are not just streaming plain text; we are streaming a series of drawing commands for the terminal.
3.  **Alternate Screen Buffer**: MTR uses the alternate screen buffer (`[?1049h` on entry, `[?1049l` on exit). This is a key behavior of full-screen applications, allowing them to have their own screen space without disrupting the user's shell history. `xterm.js` supports this natively.
4.  **Cursor Positioning**: The interface is built using precise cursor positioning commands (e.g., `[<row>;<col>H`) to place text at specific coordinates on the screen.
5.  **Screen Clearing**: MTR uses screen and line clearing commands (`[2J`, `[1K`) to manage the display and update statistics.
6.  **Text Styling**: It uses styling commands for bold text (`[1m`) and color, which will need to be rendered by `xterm.js`.

## Example Control Sequences Observed

- `[?1049h`: Enter alternate screen buffer.
- `[H[2J`: Home cursor and clear screen (a common initialization pattern).
- `[1;33r`: Set the terminal's scrolling region.
- `[5;159H`: Move cursor to row 5, column 159.
- `[6d`: Move cursor to the beginning of row 6.
- `(B[m`: Reset text attributes.
- `[?1049l`: Exit alternate screen buffer.

## Implications for Implementation

- **PTY is Mandatory**: The backend MUST spawn `mtr` in a pseudo-terminal (`pty`) to ensure `mtr` renders its interactive interface correctly. A standard `subprocess.Pipe` will not work.
- **Raw Stream Forwarding**: The backend's role is to faithfully forward the raw byte stream from the PTY output directly to the frontend via WebSockets. No processing, cleaning, or interpreting of the stream should happen on the backend.
- **Frontend Responsibility**: The frontend, using `xterm.js`, is solely responsible for interpreting the ANSI escape codes and rendering the terminal display.
- **Terminal Size**: The dimensions (rows and columns) of the `xterm.js` terminal must be communicated to the backend so the PTY can be created with the correct size. `mtr` will use this size to format its output.

This analysis confirms our architectural decision to use a PTY on the backend and a capable terminal emulator like `xterm.js` on the frontend. The implementation must focus on creating a transparent, low-latency pipe for the raw terminal data.