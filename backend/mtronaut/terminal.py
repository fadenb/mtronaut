import asyncio
import os # Added for environment variables
import ptyprocess
import shlex
from typing import Callable, Coroutine, List, Dict, Any, Optional

# A simple type hint for the callback function that handles output
OutputCallback = Callable[[bytes], Coroutine[Any, Any, None]]
CloseCallback = Callable[[], Coroutine[Any, Any, None]]

class TerminalSession:
    """Manages a single pseudo-terminal (PTY) session for running a command."""

    def __init__(
        self,
        cmd: List[str],
        on_output: OutputCallback,
        on_close: CloseCallback,
        loop: asyncio.AbstractEventLoop,
        params: Optional[Dict[str, Any]] = None, # Add params here
        env: Optional[Dict[str, str]] = None # Add env here
    ):
        self._cmd = cmd
        self._on_output = on_output
        self._on_close = on_close
        self._loop = loop
        self._env = env # Store the environment
        self._process: ptyprocess.PtyProcess | None = None
        self._read_task: asyncio.Task | None = None # To manage the async read loop
        self._close_task: asyncio.Task | None = None # To manage the close callback

    def start(self) -> None:
        """Starts the process in a new PTY."""
        if self._process is not None:
            raise RuntimeError("Session has already been started.")

        try:
            # Pass the environment to spawn, defaulting to current environment if not provided
            self._process = ptyprocess.PtyProcess.spawn(self._cmd, echo=False, env=self._env)
            # Start the asynchronous reader loop
            self._read_task = self._loop.create_task(self._read_output_loop())
        except (FileNotFoundError, ptyprocess.PtyProcessError) as e:
            raise

    def stop(self) -> None:
        """Stops the running process."""
        if self._read_task:
            self._read_task.cancel()
            self._read_task = None
        if self._process and self._process.isalive():
            self._process.close() # Use close for more robust termination
        self._process = None
        # Ensure on_close callback is called - cancel any existing task first
        if self._close_task:
            self._close_task.cancel()
            self._close_task = None
        if self._on_close:
            self._close_task = asyncio.create_task(self._on_close())

    def resize(self, cols: int, rows: int) -> None:
        """Resizes the pseudo-terminal window."""
        if self._process:
            self._process.setwinsize(rows, cols)

    async def _read_output_loop(self) -> None:
        """Continuously reads data from the PTY and calls the async output handler."""
        while self._process:
            try:
                output = await asyncio.to_thread(self._process.read, 1024)
                if output:
                    await self._on_output(output)
                else:
                    # If read() returns empty bytes, the process might be idle or finished.
                    # If it's not alive, we can exit the loop.
                    if not self._process.isalive():
                        break
                    await asyncio.sleep(0.01) # Prevent busy-looping when idle
            except EOFError:
                # This is the definitive signal that the process has closed the PTY.
                break
            except asyncio.CancelledError:
                # The task was cancelled, e.g., by stop().
                break
            except Exception:
                # Broad exception to catch other potential I/O errors.
                break
        
        # The read loop is finished, so we can call the close handler.
        await self._on_close()