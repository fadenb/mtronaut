import asyncio
import anyio
import json
import shlex
from uuid import uuid4
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from mtronaut.terminal import TerminalSession
from mtronaut.tools import build_command, list_tools
from mtronaut.session import SessionManager

from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

# Serve static files from /static
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Serve index.html for the root path
@app.get("/")
async def read_root():
    return FileResponse("frontend/index.html")

# Endpoint to get client IP
@app.get("/api/client-ip")
async def get_client_ip(request: Request):
    # Get the client's IP address from the request
    client_host = request.client.host if request.client else None
    return JSONResponse({"client_ip": client_host})

async def handle_websocket_messages(websocket: WebSocket, queue: asyncio.Queue):
    """Listens for incoming messages and puts them on the queue."""
    try:
        while True:
            message = await websocket.receive_json()
            await queue.put(message)
    except WebSocketDisconnect:
        print("Client disconnected (message handler)")
        await queue.put({"action": "disconnect"})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue()

    # Per-connection session manager (single active session for now, but scalable)
    connection_id = str(uuid4())
    session_manager = SessionManager()
    current_session_id: str | None = None

    # Get client IP for default target
    client_ip = websocket.client.host if websocket.client else "localhost"

    # Start a task to listen for incoming messages
    message_handler_task = asyncio.create_task(
        handle_websocket_messages(websocket, queue)
    )

    async def notify_stopped(session_id: str):
        await websocket.send_json({"status": "stopped", "message": "Process finished.", "session_id": session_id})
        await queue.put({"action": "process_finished", "session_id": session_id})

    try:
        while True:
            message = await queue.get()
            action = message.get("action")

            # Only break the outer loop on explicit disconnect
            if action == "disconnect":
                break

            if action == "start_tool":
                # Enforce at most one active session for back-compat with tests
                if current_session_id is not None:
                    await websocket.send_json({"status": "error", "message": "A session is already running."})
                    continue

                tool = message.get("tool", "ping")
                # Handle target based on presence in message
                if "target" not in message:
                    # No target key provided at all - use client IP
                    target = client_ip
                else:
                    # Target key was provided, even if empty - use the provided value
                    target = message["target"]
                params = message.get("params", {}) # Get parameters

                # Build command via tool configuration with validation
                try:
                    cmd = build_command(tool, target, params) # Pass params to build_command
                except KeyError:
                    await websocket.send_json({
                        "status": "error",
                        "message": f"Tool '{tool}' not allowed. Allowed: {', '.join(list_tools())}"
                    })
                    continue
                except ValueError as ve:
                    # Check if this is a validation error that should fail
                    error_msg = str(ve)
                    if ("Target must be a non-empty string" in error_msg or
                        "Invalid target:" in error_msg or
                        "Unknown parameter:" in error_msg or
                        "Invalid value for parameter" in error_msg):
                        # This is a validation error - send error response
                        await websocket.send_json({"status": "error", "message": error_msg})
                        continue
                    else:
                        # For other ValueError cases, try legacy compatibility
                        try:
                            cmd = shlex.split(f"{tool} {target}")
                        except Exception as ve2:
                            await websocket.send_json({"status": "error", "message": f"Invalid target: {ve2}"})
                            continue

                loop = asyncio.get_running_loop()

                # session_id will be set after creation; callbacks capture it through a holder
                session_id_holder: dict[str, str | None] = {"id": None}

                async def on_output(data: bytes):
                    await websocket.send_bytes(data)

                async def on_close():
                    sid = session_id_holder["id"]
                    if sid is not None:
                        rec = session_manager.get(connection_id, sid)
                        if rec:
                            rec.terminal.stop() # Ensure terminal process is stopped
                        session_manager.remove(connection_id, sid)
                        # Clear current_session_id if this was the active session
                        nonlocal current_session_id
                        if current_session_id == sid:
                            current_session_id = None
                        try:
                            await notify_stopped(sid) # Send status to client
                        except anyio.ClosedResourceError:
                            print(f"Session {sid}: Could not send 'stopped' notification, client disconnected.")


                # Create and start session
                rec = session_manager.create_session(
                    connection_id=connection_id,
                    tool=tool,
                    target=target,
                    cmd=cmd,
                    on_output=on_output,
                    on_close=on_close,
                    loop=loop,
                    params=params, # Pass params to create_session
                )
                session_id_holder["id"] = rec.session_id
                current_session_id = rec.session_id

                try:
                    rec.terminal.start()

                    # Optional resize
                    term_cols = message.get("term_cols", 80)
                    term_rows = message.get("term_rows", 24)
                    rec.terminal.resize(cols=term_cols, rows=term_rows)

                    await websocket.send_json({
                        "status": "running",
                        "message": f"Started {tool} {target}",
                        "session_id": rec.session_id
                    })
                except Exception as e:
                    # Clean up the failed session
                    session_manager.remove(connection_id, rec.session_id)
                    current_session_id = None
                    await websocket.send_json({
                        "status": "error",
                        "message": f"Failed to start process: {str(e)}"
                    })
                    continue

            elif action == "stop_tool":
                # If no id provided, stop the current session for back-compat
                session_id_to_stop = message.get("session_id") or current_session_id
                if session_id_to_stop:
                    rec = session_manager.get(connection_id, session_id_to_stop)
                    if rec:
                        # Stop the process. The on_close callback will handle cleanup.
                        rec.terminal.stop()
                        # If the stopped session was the active one, clear it immediately
                        # so a new one can be started.
                        if current_session_id == session_id_to_stop:
                            current_session_id = None

            elif action == "resize_terminal":
                session_id = message.get("session_id") or current_session_id
                cols = message.get("term_cols", 80)
                rows = message.get("term_rows", 24)
                if session_id:
                    rec = session_manager.get(connection_id, session_id)
                    if rec:
                        rec.terminal.resize(cols=cols, rows=rows)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        message_handler_task.cancel()
        # Cleanup all sessions for this connection
        session_manager.cleanup_connection(connection_id)
        print("WebSocket connection closed.")